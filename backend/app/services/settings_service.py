"""
Settings service — typed defaults and get/set helpers.

All settings are stored in the `settings` DB table as JSON-serialized values.
On first run, defaults are written. Missing keys fall back to defaults at read time.
"""
from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.models.settings import Setting

# ---------------------------------------------------------------------------
# Default settings schema
# ---------------------------------------------------------------------------
DEFAULTS: dict[str, tuple[Any, str]] = {
    # --- Exchange & Data ---
    "poll_interval_seconds":            (10,    "How often to fetch a new XRP price from DIA (seconds, min 5)"),
    "price_history_retention_days":     (30,    "How many days of price history to keep in the database"),

    # --- Portfolio & Fees ---
    "starting_budget_usd":              (10000.0, "Initial USD balance when the portfolio is reset"),
    "maker_fee_pct":                    (0.1,   "Maker fee percentage (e.g. 0.1 = 0.1%)"),
    "taker_fee_pct":                    (0.1,   "Taker fee percentage (e.g. 0.1 = 0.1%)"),

    # --- AI Provider ---
    "ai_provider_preset":               ("openai", "Provider preset. Options: openai, ollama, groq, together, openrouter, lm-studio, custom"),
    "ai_base_url":                      ("",    "Override the Ollama host URL (e.g. http://192.168.1.50:11434/api) or set a fully custom provider URL. Ignored for non-Ollama presets (use 'custom' preset for those)."),
    "ai_api_key":                       ("",    "API key for the AI provider. Leave blank to use the OPENAI_API_KEY environment variable."),
    "ai_use_tools":                     (True,  "Use function-calling / tools mode. Disable for providers that don't support it (e.g. basic Ollama models)."),
    "ai_ollama_timeout_seconds":        (600,   "Seconds to wait for an Ollama response before timing out. Increase for slow or large models."),
    "ai_ollama_timeout_seconds":        (600,   "Seconds to wait for an Ollama response before giving up. Increase for slow/large models."),

    # --- AI Configuration ---
    "ai_enabled":                       (False, "Master switch — enables automatic AI trading decisions"),
    "ai_model":                         ("gpt-4o", "Model name to use (e.g. gpt-4o, llama3.2, mixtral-8x7b-32768)"),
    "ai_temperature":                   (0.3,   "Temperature for the AI model (0.0 = deterministic, 2.0 = creative)"),
    "ai_decision_interval_seconds":     (300,   "How often the AI evaluates the market and considers a trade (seconds)"),
    "ai_price_window":                  (50,    "Number of recent price points to include in the AI prompt"),
    "ai_max_prompt_tokens":             (0,     "Trim the oldest price history so the prompt stays under this many tokens (0 = no limit). Rough estimate: 1 token ≈ 4 characters."),
    "ai_price_change_threshold_pct":    (1.0,   "Only query the AI when price has moved this % from the last AI-evaluated price (0 = disabled)"),
    "ai_max_trade_pct":                 (10.0,  "Maximum trade size as % of current portfolio value"),
    "ai_system_prompt":                 (
        "You are an expert XRP cryptocurrency trader. Analyse the provided market data "
        "and portfolio state and return a trading decision as valid JSON only. "
        "Consider trend, momentum, risk/reward, and portfolio balance. "
        "Be disciplined — only trade when there is a clear signal.",
        "System prompt sent to the AI model before market data",
    ),

    # --- Risk Management ---
    "risk_stop_loss_pct":               (5.0,   "Auto-sell if XRP drops this % below average buy price"),
    "risk_take_profit_pct":             (10.0,  "Auto-sell if XRP rises this % above average buy price"),
    "risk_max_daily_trades":            (20,    "Maximum number of AI trades allowed per 24-hour period"),
    "risk_max_drawdown_pct":            (20.0,  "Pause AI if portfolio drawdown from peak exceeds this %"),
    "risk_min_trade_usd":               (10.0,  "Minimum trade value in USD — smaller trades are rejected"),
    "risk_max_position_pct":            (80.0,  "Maximum % of portfolio that can be held in XRP at once"),

    # --- Display ---
    "ui_chart_default_timeframe":       ("24h", "Default timeframe shown on the portfolio chart (1h/6h/24h/7d/30d)"),
    "ui_trades_per_page":               (25,    "Number of trades shown per page in the trade history"),
    "ui_price_decimals":                (6,     "Decimal places shown for XRP price"),
    "ui_refresh_interval_seconds":      (5,     "How often the public dashboard refreshes data (seconds)"),

    # --- Live Trading (Kraken) ---
    "trading_mode":                         ("paper", "Trading mode: 'paper' for simulated trading, 'live' for real Kraken orders"),
    "kraken_api_key":                       ("",    "Kraken API key (required for live trading mode)"),
    "kraken_api_secret":                    ("",    "Kraken API secret (required for live trading mode)"),
    "kraken_pair":                          ("XXRPZUSD", "Kraken trading pair symbol (e.g. XXRPZUSD)"),
    "kraken_order_type":                    ("market", "Order type for Kraken trades: 'market' or 'limit'"),
    "kraken_balance_sync_interval_minutes": (20,   "How often (minutes) to reconcile local portfolio balances with Kraken in live mode"),

    # --- Telegram Notifications ---
    "telegram_enabled":                     (False, "Send trade and AI decision notifications to a Telegram chat"),
    "telegram_bot_token":                   ("",    "Telegram bot token from @BotFather (e.g. 123456:ABC-...)"),
    "telegram_chat_id":                     ("",    "Telegram chat ID or @channel_username to send notifications to"),
    "telegram_notify_trades":               (True,  "Send a message when a trade is executed"),
    "telegram_notify_decisions":            (True,  "Send a message when the AI makes a decision (including HOLD)"),
    "telegram_notify_errors":               (False, "Send a message when a trade fails or an error occurs"),
}


def seed_defaults(db: Session) -> None:
    """Write all missing default settings to the DB (idempotent)."""
    for key, (value, description) in DEFAULTS.items():
        if not db.get(Setting, key):
            db.add(Setting.from_value(key, value, description))
    db.commit()


def get_setting(db: Session, key: str) -> Any:
    row = db.get(Setting, key)
    if row is not None:
        return row.get_value()
    if key in DEFAULTS:
        return DEFAULTS[key][0]
    raise KeyError(f"Unknown setting: {key}")


def set_setting(db: Session, key: str, value: Any) -> None:
    row = db.get(Setting, key)
    if row:
        import json
        row.value = json.dumps(value)
    else:
        description = DEFAULTS.get(key, (None, ""))[1]
        db.add(Setting.from_value(key, value, description))
    db.commit()


def get_all_settings(db: Session) -> dict[str, Any]:
    rows = db.query(Setting).all()
    result: dict[str, Any] = {k: v for k, (v, _) in DEFAULTS.items()}
    for row in rows:
        result[row.key] = row.get_value()
    return result


def set_many_settings(db: Session, updates: dict[str, Any]) -> None:
    unknown = [k for k in updates if k not in DEFAULTS]
    if unknown:
        raise ValueError(f"Unknown setting key(s): {', '.join(unknown)}")
    for key, value in updates.items():
        set_setting(db, key, value)


def get_setting_meta() -> list[dict]:
    """Return settings metadata (defaults + descriptions) for the admin UI."""
    return [
        {"key": k, "default": v, "description": d}
        for k, (v, d) in DEFAULTS.items()
    ]
