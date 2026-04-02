"""
Telegram notification service.

Sends trade and AI decision updates to a configured Telegram chat via
the Bot API. All settings are read from the database at send time so
changes take effect without a restart.

Usage:
    from app.services.telegram_service import notify_trade, notify_decision

Both functions are fire-and-forget coroutines — awaiting them is safe
but failures are logged and never propagate to callers.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx
from sqlalchemy.orm import Session

from app.services.settings_service import get_setting

if TYPE_CHECKING:
    from app.models.trade import Trade
    from app.models.ai_decision import AIDecision

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def _send(token: str, chat_id: str, text: str) -> None:
    url = _TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        if not resp.is_success:
            logger.warning("Telegram send failed (%s): %s", resp.status_code, resp.text[:200])


async def notify_trade(db: Session, trade: "Trade") -> None:
    """Send a trade execution notification if enabled."""
    try:
        if not get_setting(db, "telegram_enabled"):
            return
        if not get_setting(db, "telegram_notify_trades"):
            return
        token = str(get_setting(db, "telegram_bot_token")).strip()
        chat_id = str(get_setting(db, "telegram_chat_id")).strip()
        if not token or not chat_id:
            return

        action = trade.action
        emoji = "🟢" if action == "BUY" else "🔴"
        lines = [
            f"{emoji} <b>{action}</b> executed",
            f"  Amount: <code>{trade.xrp_amount:.4f} XRP</code>",
            f"  Price: <code>${trade.price_at_trade:.6f}</code>",
            f"  Value: <code>${trade.usd_amount:.2f}</code>",
            f"  Fee: <code>${trade.fee_usd:.4f}</code>",
        ]
        if trade.usd_balance_after is not None and trade.xrp_balance_after is not None:
            lines.append(f"  USD after: <code>${trade.usd_balance_after:.2f}</code>")
            lines.append(f"  XRP after: <code>{trade.xrp_balance_after:.4f}</code>")
        await _send(token, chat_id, "\n".join(lines))
    except Exception:
        logger.exception("notify_trade failed")


async def notify_decision(db: Session, decision: "AIDecision") -> None:
    """Send an AI decision notification if enabled."""
    try:
        if not get_setting(db, "telegram_enabled"):
            return
        if not get_setting(db, "telegram_notify_decisions"):
            return
        token = str(get_setting(db, "telegram_bot_token")).strip()
        chat_id = str(get_setting(db, "telegram_chat_id")).strip()
        if not token or not chat_id:
            return

        action = decision.action
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⏸️"}.get(action, "❓")
        conf_pct = int((decision.confidence or 0) * 100)
        lines = [
            f"{emoji} AI decision: <b>{action}</b>",
            f"  Confidence: <code>{conf_pct}%</code>",
        ]
        if decision.xrp_amount:
            lines.append(f"  Amount: <code>{decision.xrp_amount:.4f} XRP</code>")
        if decision.reasoning:
            # Trim long reasoning to avoid hitting Telegram's 4096 char limit
            short = decision.reasoning[:300].replace("<", "&lt;").replace(">", "&gt;")
            if len(decision.reasoning) > 300:
                short += "…"
            lines.append(f"  <i>{short}</i>")
        if decision.execution_error:
            lines.append(f"  ⚠️ Error: <code>{decision.execution_error[:200]}</code>")
        await _send(token, chat_id, "\n".join(lines))
    except Exception:
        logger.exception("notify_decision failed")


async def notify_error(db: Session, message: str) -> None:
    """Send an error notification if enabled."""
    try:
        if not get_setting(db, "telegram_enabled"):
            return
        if not get_setting(db, "telegram_notify_errors"):
            return
        token = str(get_setting(db, "telegram_bot_token")).strip()
        chat_id = str(get_setting(db, "telegram_chat_id")).strip()
        if not token or not chat_id:
            return
        safe = message[:500].replace("<", "&lt;").replace(">", "&gt;")
        await _send(token, chat_id, f"⚠️ <b>Error</b>\n<code>{safe}</code>")
    except Exception:
        logger.exception("notify_error failed")
