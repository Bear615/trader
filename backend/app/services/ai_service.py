"""
AI service — builds prompts from market data and portfolio state,
calls the configured AI provider, and returns a structured decision.

Supports OpenAI-compatible providers (OpenAI, Groq, Together, OpenRouter,
LM Studio, custom) via AsyncOpenAI, and Ollama's native /api/chat endpoint
directly.  The Ollama host/port is fully configurable via ai_base_url.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.websocket import ws_manager
from app.models.ai_decision import AIDecision
from app.models.price import PricePoint
from app.models.trade import Trade
from app.services.settings_service import get_setting
from app.services.trading_service import (
    get_portfolio,
    execute_trade,
    _daily_trade_count,
    _portfolio_drawdown_pct,
    _avg_buy_price,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider base-URL presets
# ---------------------------------------------------------------------------
PROVIDER_PRESETS: dict[str, str] = {
    "openai":     "",
    "ollama":     "http://localhost:11434/api",   # default; override with ai_base_url
    "groq":       "https://api.groq.com/openai/v1",
    "together":   "https://api.together.xyz/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "lm-studio":  "http://localhost:1234/v1",
    "custom":     "",   # user fills ai_base_url directly
}

# Tracks the price at the last successful AI call. Resets on restart (first call always fires).
_last_ai_price: Optional[float] = None


def _resolve_client_params(db: Session) -> dict:
    """Return kwargs for AsyncOpenAI() based on the current DB settings."""
    from app.core.config import config as app_config

    preset = str(get_setting(db, "ai_provider_preset"))
    base_url = str(get_setting(db, "ai_base_url")).strip()
    api_key = str(get_setting(db, "ai_api_key")).strip()

    # Apply preset URL.
    # For "ollama": ai_base_url (DB) → OLLAMA_BASE_URL (.env) → localhost default.
    # For other non-custom presets: always use the fixed preset URL.
    if preset == "ollama":
        if not base_url:
            base_url = app_config.ollama_base_url or PROVIDER_PRESETS["ollama"]
    elif preset != "custom" and preset in PROVIDER_PRESETS:
        base_url = PROVIDER_PRESETS[preset]

    resolved_key = api_key or app_config.openai_api_key or "none"
    params: dict = {"api_key": resolved_key}
    if base_url:
        params["base_url"] = base_url
    params["_preset"] = preset
    return params


async def _call_ollama_native(
    endpoint: str, model: str, messages: list, temperature: float, timeout: float = 600.0
) -> tuple[dict, str, "int | None", "int | None"]:
    """POST to Ollama's native /api/chat endpoint directly.
    Returns (parsed_args, raw_json_str, prompt_tokens, completion_tokens).
    """
    import httpx
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=timeout) as http:
        resp = await http.post(endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
    raw = json.dumps(data)
    content = data.get("message", {}).get("content", "{}").strip()
    content = content.lstrip("```json").lstrip("```").rstrip("```").strip()
    args = json.loads(content)
    return args, raw, data.get("prompt_eval_count"), data.get("eval_count")

# ---------------------------------------------------------------------------
# Structured output schema for GPT-4o function calling
# ---------------------------------------------------------------------------
DECISION_FUNCTION = {
    "name": "trading_decision",
    "description": "Return a trading decision based on the provided market data.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["BUY", "SELL", "HOLD"],
                "description": "The trading action to take.",
            },
            "xrp_amount": {
                "type": ["number", "null"],
                "description": "Amount of XRP to buy or sell. Null for HOLD.",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence level 0.0 (no confidence) to 1.0 (very high confidence).",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the decision rationale (2-4 sentences).",
            },
        },
        "required": ["action", "confidence", "reasoning"],
    },
}


def _format_price_table(price_points: list[PricePoint]) -> str:
    # Compact: "YYYY-MM-DDTHH:MM price" — no headers, no pipes, no currency symbols
    return "\n".join(
        f"{p.timestamp.strftime('%Y-%m-%dT%H:%M')} {p.price:.6f}"
        for p in price_points
    )


def _format_recent_trades(trades: list[Trade]) -> str:
    if not trades:
        return "none"
    # Compact CSV-style: time action xrp_amount price fee
    return "\n".join(
        f"{t.timestamp.strftime('%Y-%m-%dT%H:%M')} {t.action} {t.xrp_amount:.4f} {t.price_at_trade:.6f} {t.fee_usd:.4f}"
        for t in trades
    )


def build_prompt(db: Session, current_price: float, price_points: list[PricePoint]) -> str:
    portfolio = get_portfolio(db)
    total_value = portfolio.total_value_usd(current_price)
    roi = ((total_value - portfolio.starting_budget) / portfolio.starting_budget * 100) if portfolio.starting_budget else 0

    recent_trades = (
        db.query(Trade)
        .order_by(Trade.timestamp.desc())
        .limit(10)
        .all()
    )

    avg_buy = _avg_buy_price(db)
    drawdown = _portfolio_drawdown_pct(portfolio, current_price)
    daily_trades = _daily_trade_count(db)

    maker_fee = get_setting(db, "maker_fee_pct")
    taker_fee = get_setting(db, "taker_fee_pct")
    max_trade_pct = get_setting(db, "ai_max_trade_pct")
    max_position_pct = get_setting(db, "risk_max_position_pct")
    stop_loss = get_setting(db, "risk_stop_loss_pct")
    take_profit = get_setting(db, "risk_take_profit_pct")
    max_daily = get_setting(db, "risk_max_daily_trades")
    min_trade = get_setting(db, "risk_min_trade_usd")

    max_trade_usd = total_value * (float(max_trade_pct) / 100)
    max_xrp = max_trade_usd / current_price if current_price > 0 else 0

    prompt = f"""MARKET
time {datetime.utcnow().strftime('%Y-%m-%dT%H:%M')} UTC
price {current_price:.6f}

PRICE HISTORY ({len(price_points)} points, format: datetime price)
{_format_price_table(price_points)}

PORTFOLIO
usd {portfolio.usd_balance:.4f}
xrp {portfolio.xrp_balance:.6f}
total {total_value:.4f}
start {portfolio.starting_budget:.4f}
roi {roi:+.2f}
avg_buy {f'{avg_buy:.6f}' if avg_buy else 'none'}
drawdown {drawdown:.2f}

RECENT TRADES (format: datetime action xrp_amount price fee)
{_format_recent_trades(list(reversed(recent_trades)))}

CONSTRAINTS
taker_fee {taker_fee}
maker_fee {maker_fee}
max_trade_usd {max_trade_usd:.2f}
max_xrp {max_xrp:.4f}
max_position_pct {max_position_pct}
stop_loss_pct {stop_loss}
take_profit_pct {take_profit}
max_daily {max_daily} used {daily_trades}
min_trade_usd {min_trade}

xrp_amount must not exceed {max_xrp:.4f}. If HOLD set xrp_amount null."""

    return prompt


async def make_decision(db: Session, bypass_guards: bool = False) -> Optional[AIDecision]:
    """
    Fetch latest prices, build a prompt, call the configured AI provider,
    persist and (if AI is enabled) execute the resulting trade.

    bypass_guards=True skips the ai_enabled / daily-limit / drawdown guards
    so that manual triggers always attempt a request.
    """
    from app.services.price_service import get_latest_price

    # Guard: check master switch each time (skipped for manual triggers)
    if not bypass_guards and not get_setting(db, "ai_enabled"):
        logger.info("AI disabled — skipping decision (enable via Admin > AI Configuration)")
        return None

    # Guard: max daily trades (skipped for manual triggers)
    daily_trades = _daily_trade_count(db)
    max_daily = int(get_setting(db, "risk_max_daily_trades"))
    if not bypass_guards and daily_trades >= max_daily:
        logger.info("Daily trade limit reached (%d/%d)", daily_trades, max_daily)
        return None

    latest = get_latest_price(db)
    if not latest:
        logger.warning("No price data available for AI decision")
        return None

    current_price = latest.price

    # Guard: max drawdown — pause AI if exceeded
    from app.services.trading_service import get_portfolio, _portfolio_drawdown_pct
    portfolio = get_portfolio(db)
    drawdown = _portfolio_drawdown_pct(portfolio, current_price)
    max_drawdown = float(get_setting(db, "risk_max_drawdown_pct"))
    if not bypass_guards and drawdown >= max_drawdown:
        logger.warning("Max drawdown %.2f%% exceeded (%.2f%%) — AI paused", max_drawdown, drawdown)
        return None

    # Guard: price-change threshold — skip LLM call if price hasn't moved enough
    global _last_ai_price
    threshold = float(get_setting(db, "ai_price_change_threshold_pct"))
    if (
        not bypass_guards
        and threshold > 0
        and _last_ai_price is not None
    ):
        pct_change = abs(current_price - _last_ai_price) / _last_ai_price * 100
        if pct_change < threshold:
            logger.debug(
                "Price moved %.4f%% (threshold %.2f%%) — skipping AI call",
                pct_change, threshold,
            )
            return None

    window = int(get_setting(db, "ai_price_window"))
    price_points = (
        db.query(PricePoint)
        .order_by(PricePoint.timestamp.desc())
        .limit(window)
        .all()
    )
    price_points.reverse()

    system_prompt = str(get_setting(db, "ai_system_prompt"))
    user_prompt = build_prompt(db, current_price, price_points)
    model = str(get_setting(db, "ai_model"))
    temperature = float(get_setting(db, "ai_temperature"))

    # Trim oldest price points if prompt exceeds the configured token budget.
    # Token estimate: 1 token ≈ 4 characters (standard rough approximation).
    max_prompt_tokens = int(get_setting(db, "ai_max_prompt_tokens"))
    if max_prompt_tokens > 0:
        estimated = len(user_prompt) // 4
        if estimated > max_prompt_tokens and len(price_points) > 1:
            keep = max(1, int(len(price_points) * max_prompt_tokens / estimated))
            price_points = price_points[-keep:]  # keep the most recent points
            user_prompt = build_prompt(db, current_price, price_points)
            logger.info(
                "Prompt trimmed to ~%d tokens (%d/%d price points kept)",
                len(user_prompt) // 4, keep, len(price_points) + (len(price_points) - keep),
            )

    # All guards passed — anchor the reference price for the next threshold check
    _last_ai_price = current_price

    try:
        client_params = _resolve_client_params(db)
        preset = client_params.get("_preset", "openai")
        openai_params = {k: v for k, v in client_params.items() if not k.startswith("_")}

        if preset == "ollama":
            from app.core.config import config as app_config
            base_url = openai_params.get("base_url") or app_config.ollama_base_url or PROVIDER_PRESETS["ollama"]
            endpoint = base_url.rstrip("/") + "/chat"
            logger.info("Sending request to Ollama: %s  model=%s", endpoint, model)
            json_system = (
                system_prompt
                + "\n\nRespond ONLY with a valid JSON object with exactly these keys: "
                "action (string: BUY, SELL, or HOLD), "
                "xrp_amount (number or null), "
                "confidence (number 0.0-1.0), "
                "reasoning (string)."
            )
            messages = [
                {"role": "system", "content": json_system},
                {"role": "user", "content": user_prompt},
            ]
            args, raw_response, pt, ct = await _call_ollama_native(
                endpoint, model, messages, temperature,
                timeout=float(get_setting(db, "ai_ollama_timeout_seconds")),
            )
            from types import SimpleNamespace
            usage = SimpleNamespace(prompt_tokens=pt, completion_tokens=ct)
        else:
            from openai import AsyncOpenAI

            if not openai_params.get("api_key") or openai_params["api_key"] == "none":
                logger.error(
                    "No AI API key configured — set OPENAI_API_KEY in .env or ai_api_key in Admin settings. "
                    "If using Ollama, make sure ai_provider_preset is set to 'ollama' in Admin > AI Provider."
                )
                return None
            logger.info("Sending request to provider '%s' base_url=%s  model=%s",
                        preset, openai_params.get("base_url", "(openai default)"), model)

            client = AsyncOpenAI(**openai_params)
            use_tools = bool(get_setting(db, "ai_use_tools"))

            if use_tools:
                response = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    tools=[{"type": "function", "function": DECISION_FUNCTION}],
                    tool_choice={"type": "function", "function": {"name": "trading_decision"}},
                )
                raw_response = response.model_dump_json()
                usage = response.usage
                tool_call = response.choices[0].message.tool_calls[0]
                args = json.loads(tool_call.function.arguments)
            else:
                # JSON-mode fallback for providers that don't support tools
                json_system = (
                    system_prompt
                    + "\n\nRespond ONLY with a valid JSON object with exactly these keys: "
                    "action (string: BUY, SELL, or HOLD), "
                    "xrp_amount (number or null), "
                    "confidence (number 0.0-1.0), "
                    "reasoning (string)."
                )
                response = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": json_system},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw_response = response.model_dump_json()
                usage = response.usage
                content = response.choices[0].message.content or "{}"
                # Strip markdown code fences if present
                content = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                args = json.loads(content)

        action = args["action"].upper()
        xrp_amount_raw = args.get("xrp_amount")
        # Ensure xrp_amount is a float (AI may return string or null)
        try:
            xrp_amount = float(xrp_amount_raw) if xrp_amount_raw is not None else None
        except (ValueError, TypeError):
            xrp_amount = None
        confidence = float(args.get("confidence", 0.5))
        reasoning = args.get("reasoning", "")

        decision = AIDecision(
            timestamp=datetime.utcnow(),
            action=action,
            xrp_amount=xrp_amount,
            confidence=confidence,
            reasoning=reasoning,
            raw_prompt=user_prompt,
            raw_response=raw_response,
            executed=False,
            model_used=model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)

        # Execute the trade if action is not HOLD
        if action in ("BUY", "SELL") and xrp_amount and xrp_amount > 0:
            _, err = await execute_trade(
                db=db,
                action=action,
                xrp_amount=float(xrp_amount),
                current_price=current_price,
                fee_type="taker",
                ai_decision_id=decision.id,
                triggered_by="ai",
            )
            decision.executed = err is None
            decision.execution_error = err
            db.commit()

        await ws_manager.broadcast("decisions", decision.to_dict(include_raw=True))

        logger.info(
            "AI decision: %s %.4f XRP (conf=%.2f) — %s",
            action, xrp_amount or 0, confidence, reasoning[:60],
        )
        return decision

    except Exception as exc:
        logger.error("AI decision failed: %s", exc)
        return None
