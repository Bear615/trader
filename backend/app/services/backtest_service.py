"""
Backtest service — replays stored/seeded price history through the AI
and computes performance metrics.

Modes:
  ai     — calls GPT-4o for every decision interval (slow, costs tokens)
  random — random buy/sell/hold (free, use for engine testing)
"""
from __future__ import annotations

import json
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.backtest import BacktestRun
from app.models.price import PricePoint
from app.services.ai_service import build_prompt, DECISION_FUNCTION

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _sharpe(returns: list[float], risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    std = math.sqrt(variance) if variance > 0 else 0.0
    if std == 0:
        return 0.0
    annualized = math.sqrt(252)  # daily returns approximation
    return (mean - risk_free) / std * annualized


def _max_drawdown(equity_curve: list[float]) -> float:
    """Return max peak-to-trough drawdown as a positive percentage."""
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _compute_metrics(
    equity_curve: list[dict],
    initial_capital: float,
    trades: list[dict],
) -> dict[str, Any]:
    values = [e["value"] for e in equity_curve]
    final_value = values[-1] if values else initial_capital
    total_return_pct = (final_value - initial_capital) / initial_capital * 100

    daily_returns: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            daily_returns.append((values[i] - values[i - 1]) / values[i - 1])

    buy_trades = [t for t in trades if t["action"] == "BUY"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    profitable_sells = sum(1 for t in sell_trades if (t.get("pnl") or 0) > 0)
    win_rate = (profitable_sells / len(sell_trades) * 100) if sell_trades else 0.0

    return {
        "initial_capital": initial_capital,
        "final_value": final_value,
        "total_return_pct": round(total_return_pct, 4),
        "sharpe_ratio": round(_sharpe(daily_returns), 4),
        "max_drawdown_pct": round(_max_drawdown(values), 4),
        "win_rate_pct": round(win_rate, 2),
        "total_trades": len(trades),
        "buy_count": len(buy_trades),
        "sell_count": len(sell_trades),
        "equity_curve": equity_curve,
        "trades": trades,
    }


# ---------------------------------------------------------------------------
# Paper simulation helpers (no DB side effects)
# ---------------------------------------------------------------------------

class SimPortfolio:
    def __init__(self, capital: float, maker_fee: float, taker_fee: float):
        self.usd = capital
        self.xrp = 0.0
        self.starting = capital
        self.maker_fee = maker_fee / 100.0
        self.taker_fee = taker_fee / 100.0
        self.trades: list[dict] = []

    def buy(self, xrp_amount: float, price: float, ts: datetime) -> bool:
        cost = xrp_amount * price
        fee = cost * self.taker_fee
        total = cost + fee
        if self.usd < total or cost < 1.0:
            return False
        self.usd -= total
        self.xrp += xrp_amount
        self.trades.append({
            "timestamp": ts.isoformat() + "Z",
            "action": "BUY",
            "xrp_amount": xrp_amount,
            "usd_amount": cost,
            "price_at_trade": price,
            "fee_usd": fee,
            "pnl": None,
        })
        return True

    def sell(self, xrp_amount: float, price: float, ts: datetime, avg_buy: float | None) -> bool:
        if self.xrp < xrp_amount or xrp_amount * price < 1.0:
            return False
        gross = xrp_amount * price
        fee = gross * self.taker_fee
        net = gross - fee
        pnl = ((price - avg_buy) * xrp_amount - fee) if avg_buy else None
        self.xrp -= xrp_amount
        self.usd += net
        self.trades.append({
            "timestamp": ts.isoformat() + "Z",
            "action": "SELL",
            "xrp_amount": xrp_amount,
            "usd_amount": gross,
            "price_at_trade": price,
            "fee_usd": fee,
            "pnl": pnl,
        })
        return True

    def total_value(self, price: float) -> float:
        return self.usd + self.xrp * price

    def avg_buy_price(self) -> float | None:
        buys = [t for t in self.trades if t["action"] == "BUY"]
        if not buys:
            return None
        total_xrp = sum(t["xrp_amount"] for t in buys)
        if total_xrp == 0:
            return None
        return sum(t["xrp_amount"] * t["price_at_trade"] for t in buys) / total_xrp


# ---------------------------------------------------------------------------
# Random strategy (for quick testing without AI cost)
# ---------------------------------------------------------------------------

def _random_decision(portfolio: SimPortfolio, price: float, max_trade_pct: float = 10.0):
    action = random.choice(["BUY", "SELL", "HOLD"])
    xrp_amount = None
    if action == "BUY" and portfolio.usd > 1:
        trade_usd = portfolio.total_value(price) * (max_trade_pct / 100.0)
        trade_usd = min(trade_usd, portfolio.usd * 0.95)
        xrp_amount = trade_usd / price if price > 0 else 0
    elif action == "SELL" and portfolio.xrp > 0:
        xrp_amount = portfolio.xrp * (max_trade_pct / 100.0)
    return action, xrp_amount


# ---------------------------------------------------------------------------
# AI strategy call (real GPT-4o via mock DB proxy)
# ---------------------------------------------------------------------------

async def _ai_decision_for_backtest(
    price_points: list[PricePoint],
    portfolio: SimPortfolio,
    current_price: float,
    model: str,
    temperature: float,
    system_prompt: str,
    max_trade_pct: float,
    client_params: dict,
    use_tools: bool,
):
    """Standalone AI decision without DB side effects."""
    try:
        from app.services.ai_service import _call_ollama_native, PROVIDER_PRESETS
        preset = client_params.get("_preset", "openai")
        openai_params = {k: v for k, v in client_params.items() if not k.startswith("_")}

        total_value = portfolio.total_value(current_price)
        max_trade_usd = total_value * (max_trade_pct / 100)
        max_xrp = max_trade_usd / current_price if current_price > 0 else 0

        rows = "\n".join(
            f"{p.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {p.price:.6f}"
            for p in price_points
        )
        avg_buy = portfolio.avg_buy_price()
        user_msg = f"""Current XRP price: ${current_price:.6f}
USD balance: ${portfolio.usd:.4f}
XRP balance: {portfolio.xrp:.6f}
Total value: ${total_value:.4f}
Avg buy price: {'$' + f'{avg_buy:.6f}' if avg_buy else 'N/A'}
Recent prices:\n{rows}
Max trade: {max_xrp:.4f} XRP (${max_trade_usd:.2f})"""

        if preset == "ollama":
            base_url = openai_params.get("base_url") or PROVIDER_PRESETS["ollama"]
            endpoint = base_url.rstrip("/") + "/chat"
            json_sys = (
                system_prompt
                + "\n\nReturn ONLY a JSON object with keys: "
                "action (BUY/SELL/HOLD), xrp_amount (number or null), "
                "confidence (0.0-1.0), reasoning (string)."
            )
            messages = [
                {"role": "system", "content": json_sys},
                {"role": "user", "content": user_msg},
            ]
            args, _, _, _ = await _call_ollama_native(endpoint, model, messages, temperature)
        elif use_tools:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(**openai_params)
            response = await client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                tools=[{"type": "function", "function": DECISION_FUNCTION}],
                tool_choice={"type": "function", "function": {"name": "trading_decision"}},
            )
            args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        else:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(**openai_params)
            json_sys = (
                system_prompt
                + "\n\nReturn ONLY a JSON object with keys: "
                "action (BUY/SELL/HOLD), xrp_amount (number or null), "
                "confidence (0.0-1.0), reasoning (string)."
            )
            response = await client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": json_sys},
                    {"role": "user", "content": user_msg},
                ],
            )
            content = (response.choices[0].message.content or "{}").strip()
            content = content.lstrip("```json").lstrip("```").rstrip("```").strip()
            args = json.loads(content)

        return args.get("action", "HOLD"), args.get("xrp_amount")
    except Exception as exc:
        logger.warning("Backtest AI call failed: %s", exc)
        return "HOLD", None


# ---------------------------------------------------------------------------
# Main backtest runner
# ---------------------------------------------------------------------------

async def run_backtest(run_id: int, db_factory) -> None:
    """
    Run a backtest in the background.
    db_factory is a callable returning a new Session (avoids shared sessions in threads).
    """
    db: Session = db_factory()
    try:
        run: BacktestRun = db.get(BacktestRun, run_id)
        if not run:
            return

        run.status = "running"
        db.commit()

        price_points: list[PricePoint] = (
            db.query(PricePoint)
            .filter(
                PricePoint.timestamp >= run.start_date,
                PricePoint.timestamp <= run.end_date,
            )
            .order_by(PricePoint.timestamp.asc())
            .all()
        )

        if len(price_points) < 2:
            run.status = "error"
            run.error_message = "Not enough price data in the selected date range. Try seeding history first."
            db.commit()
            return

        decision_interval = timedelta(seconds=3600 / max(1, run.decisions_per_hour))

        portfolio = SimPortfolio(
            capital=run.initial_capital,
            maker_fee=run.maker_fee_pct,
            taker_fee=run.taker_fee_pct,
        )

        equity_curve = []
        last_decision_time = None
        window = run.ai_price_window

        use_ai = run.ai_model is not None and run.ai_model != "random"
        from app.services.settings_service import get_setting
        from app.services.ai_service import _resolve_client_params
        system_prompt = str(get_setting(db, "ai_system_prompt"))
        max_trade_pct = float(get_setting(db, "ai_max_trade_pct"))
        client_params = _resolve_client_params(db)
        use_tools = bool(get_setting(db, "ai_use_tools"))

        for i, point in enumerate(price_points):
            price = point.price
            total = portfolio.total_value(price)
            equity_curve.append({"timestamp": point.timestamp.isoformat() + "Z", "value": total})

            should_decide = (
                last_decision_time is None
                or (point.timestamp - last_decision_time) >= decision_interval
            )

            if not should_decide:
                continue

            last_decision_time = point.timestamp

            if use_ai:
                history_slice = price_points[max(0, i - window): i + 1]
                action, xrp_amount = await _ai_decision_for_backtest(
                    price_points=history_slice,
                    portfolio=portfolio,
                    current_price=price,
                    model=run.ai_model,
                    temperature=0.3,
                    system_prompt=system_prompt,
                    max_trade_pct=max_trade_pct,
                    client_params=client_params,
                    use_tools=use_tools,
                )
            else:
                action, xrp_amount = _random_decision(portfolio, price, max_trade_pct)

            if action == "BUY" and xrp_amount and xrp_amount > 0:
                portfolio.buy(float(xrp_amount), price, point.timestamp)
            elif action == "SELL" and xrp_amount and xrp_amount > 0:
                portfolio.sell(float(xrp_amount), price, point.timestamp, portfolio.avg_buy_price())

        metrics = _compute_metrics(equity_curve, run.initial_capital, portfolio.trades)

        run.result_json = json.dumps(metrics)
        run.status = "done"
        db.commit()
        logger.info("Backtest %d complete — return %.2f%%", run_id, metrics["total_return_pct"])

    except Exception as exc:
        logger.error("Backtest %d failed: %s", run_id, exc)
        run = db.get(BacktestRun, run_id)
        if run:
            run.status = "error"
            run.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def _compute_live_metrics(db: Session, current_price: float) -> dict[str, Any]:
    """Compute live portfolio metrics for the /api/v1/metrics endpoint."""
    from app.services.trading_service import get_portfolio
    from app.models.trade import Trade

    portfolio = get_portfolio(db)
    total_value = portfolio.total_value_usd(current_price)
    roi = ((total_value - portfolio.starting_budget) / portfolio.starting_budget * 100) if portfolio.starting_budget else 0

    all_trades = db.query(Trade).order_by(Trade.timestamp.asc()).all()

    buy_trades = [t for t in all_trades if t.action == "BUY"]
    sell_trades = [t for t in all_trades if t.action == "SELL"]

    # Simple win rate: sells above their avg cost
    total_xrp_bought = 0.0
    total_usd_spent = 0.0
    profitable_sells = 0
    for t in all_trades:
        if t.action == "BUY":
            total_xrp_bought += t.xrp_amount
            total_usd_spent += t.usd_amount
    avg_cost = (total_usd_spent / total_xrp_bought) if total_xrp_bought > 0 else 0
    for t in sell_trades:
        if t.price_at_trade > avg_cost:
            profitable_sells += 1
    win_rate = (profitable_sells / len(sell_trades) * 100) if sell_trades else 0.0

    total_fees = sum(t.fee_usd for t in all_trades)

    return {
        "total_value_usd": total_value,
        "roi_pct": round(roi, 4),
        "total_trades": len(all_trades),
        "buy_count": len(buy_trades),
        "sell_count": len(sell_trades),
        "win_rate_pct": round(win_rate, 2),
        "avg_buy_price": round(avg_cost, 6) if avg_cost else None,
        "total_fees_usd": round(total_fees, 4),
        "xrp_balance": portfolio.xrp_balance,
        "usd_balance": portfolio.usd_balance,
        "starting_budget": portfolio.starting_budget,
        "current_price": current_price,
    }
