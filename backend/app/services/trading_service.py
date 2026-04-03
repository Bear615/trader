"""
Trading service — executes paper trades and updates portfolio state.
Handles fee calculation, balance validation, risk checks, and P&L tracking.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.websocket import ws_manager
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.models.ai_decision import AIDecision
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Portfolio helpers
# ---------------------------------------------------------------------------

def get_portfolio(db: Session) -> Portfolio:
    """Return the active portfolio, creating it with defaults if needed."""
    portfolio = db.query(Portfolio).filter(Portfolio.is_active == True).first()
    if not portfolio:
        starting = get_setting(db, "starting_budget_usd")
        portfolio = Portfolio(
            id=1,
            usd_balance=float(starting),
            xrp_balance=0.0,
            starting_budget=float(starting),
            is_active=True,
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def reset_portfolio(db: Session) -> Portfolio:
    """Reset the active portfolio to its starting budget."""
    portfolio = get_portfolio(db)
    starting = get_setting(db, "starting_budget_usd")
    portfolio.usd_balance = float(starting)
    portfolio.xrp_balance = 0.0
    portfolio.starting_budget = float(starting)
    portfolio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(portfolio)
    logger.info("Portfolio reset to $%.2f", portfolio.starting_budget)
    return portfolio


def reset_roi(db: Session) -> Portfolio:
    """Reset ROI baseline to the current portfolio value without touching balances."""
    from app.services.price_service import get_latest_price
    portfolio = get_portfolio(db)
    latest = get_latest_price(db)
    current_price = latest.price if latest else 0.0
    portfolio.starting_budget = portfolio.total_value_usd(current_price)
    portfolio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(portfolio)
    logger.info("ROI reset — new baseline $%.2f", portfolio.starting_budget)
    return portfolio


# ---------------------------------------------------------------------------
# Risk checks
# ---------------------------------------------------------------------------

def _daily_trade_count(db: Session) -> int:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    return db.query(Trade).filter(Trade.timestamp >= cutoff).count()


def _portfolio_drawdown_pct(portfolio: Portfolio, current_price: float) -> float:
    """Rough max-drawdown approximation based on peak vs current value."""
    # We use starting_budget as baseline peak; would need a peaks table for true max-DD
    total = portfolio.total_value_usd(current_price)
    if portfolio.starting_budget == 0:
        return 0.0
    return max(0.0, (portfolio.starting_budget - total) / portfolio.starting_budget * 100)


def _avg_buy_price(db: Session) -> Optional[float]:
    """Compute volume-weighted average buy price from trade history."""
    buys = db.query(Trade).filter(Trade.action == "BUY").all()
    if not buys:
        return None
    total_xrp = sum(t.xrp_amount for t in buys)
    if total_xrp == 0:
        return None
    return sum(t.xrp_amount * t.price_at_trade for t in buys) / total_xrp


# ---------------------------------------------------------------------------
# Core trade execution
# ---------------------------------------------------------------------------

async def execute_trade(
    db: Session,
    action: str,  # "BUY" | "SELL"
    xrp_amount: float,
    current_price: float,
    fee_type: str = "taker",
    ai_decision_id: Optional[int] = None,
    triggered_by: str = "ai",
    note: Optional[str] = None,
) -> tuple[Trade, str | None]:
    """
    Execute a trade — paper or live Kraken depending on trading_mode.
    Returns (Trade, error_message). error_message is None on success.
    """
    action = action.upper()
    if action not in ("BUY", "SELL"):
        return None, f"Invalid action: {action}"

    trading_mode = get_setting(db, "trading_mode")

    if trading_mode == "live":
        return await _execute_live_trade(
            db, action, xrp_amount, current_price, fee_type,
            ai_decision_id, triggered_by, note,
        )
    return await _execute_paper_trade(
        db, action, xrp_amount, current_price, fee_type,
        ai_decision_id, triggered_by, note,
    )


async def _execute_paper_trade(
    db: Session,
    action: str,
    xrp_amount: float,
    current_price: float,
    fee_type: str = "taker",
    ai_decision_id: Optional[int] = None,
    triggered_by: str = "ai",
    note: Optional[str] = None,
) -> tuple[Trade, str | None]:
    """Original paper-trade logic, unchanged."""
    portfolio = get_portfolio(db)

    fee_pct = get_setting(db, f"{fee_type}_fee_pct") / 100.0
    usd_amount = xrp_amount * current_price
    fee_usd = usd_amount * fee_pct
    min_trade = get_setting(db, "risk_min_trade_usd")

    if usd_amount < float(min_trade):
        return None, f"Trade too small: ${usd_amount:.2f} < min ${min_trade}"

    if action == "BUY":
        total_cost = usd_amount + fee_usd
        if portfolio.usd_balance < total_cost:
            return None, f"Insufficient USD balance: ${portfolio.usd_balance:.2f} < ${total_cost:.2f}"

        # Max position check
        max_pct = get_setting(db, "risk_max_position_pct")
        total_value = portfolio.total_value_usd(current_price)
        new_xrp_value = (portfolio.xrp_balance + xrp_amount) * current_price
        if total_value > 0 and (new_xrp_value / total_value * 100) > float(max_pct):
            return None, f"Would exceed max XRP position of {max_pct}%"

        portfolio.usd_balance -= total_cost
        portfolio.xrp_balance += xrp_amount

    elif action == "SELL":
        if portfolio.xrp_balance < xrp_amount:
            return None, f"Insufficient XRP balance: {portfolio.xrp_balance:.6f} < {xrp_amount:.6f}"

        net_usd = usd_amount - fee_usd
        portfolio.xrp_balance -= xrp_amount
        portfolio.usd_balance += net_usd

    portfolio.updated_at = datetime.utcnow()
    db.flush()

    trade = Trade(
        timestamp=datetime.utcnow(),
        action=action,
        xrp_amount=xrp_amount,
        usd_amount=usd_amount,
        price_at_trade=current_price,
        fee_usd=fee_usd,
        fee_type=fee_type,
        usd_balance_after=portfolio.usd_balance,
        xrp_balance_after=portfolio.xrp_balance,
        ai_decision_id=ai_decision_id,
        triggered_by=triggered_by,
        note=note,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    # Broadcast trade + portfolio update
    avg_buy = _avg_buy_price(db)
    await ws_manager.broadcast("trades", trade.to_dict(avg_buy))

    from app.services.telegram_service import notify_trade
    await notify_trade(db, trade)

    logger.info(
        "Trade executed: %s %.6f XRP @ $%.6f (fee $%.4f)",
        action, xrp_amount, current_price, fee_usd,
    )
    return trade, None


async def _execute_live_trade(
    db: Session,
    action: str,
    xrp_amount: float,
    current_price: float,
    fee_type: str = "taker",
    ai_decision_id: Optional[int] = None,
    triggered_by: str = "ai",
    note: Optional[str] = None,
) -> tuple[Trade, str | None]:
    """Place a real order on Kraken and record it in the local portfolio."""
    from app.services import kraken_service

    api_key    = get_setting(db, "kraken_api_key")
    api_secret = get_setting(db, "kraken_api_secret")
    pair       = get_setting(db, "kraken_pair")
    order_type = get_setting(db, "kraken_order_type")

    if not api_key or not api_secret:
        return None, "Kraken API credentials not configured"

    # --- Risk / size checks (same gates as paper mode) ---
    portfolio = get_portfolio(db)
    fee_pct   = get_setting(db, f"{fee_type}_fee_pct") / 100.0
    usd_amount = xrp_amount * current_price
    fee_usd    = usd_amount * fee_pct
    min_trade  = get_setting(db, "risk_min_trade_usd")

    if usd_amount < float(min_trade):
        return None, f"Trade too small: ${usd_amount:.2f} < min ${min_trade}"

    if action == "BUY":
        total_cost = usd_amount + fee_usd
        if portfolio.usd_balance < total_cost:
            return None, f"Insufficient USD balance: ${portfolio.usd_balance:.2f} < ${total_cost:.2f}"
        max_pct = get_setting(db, "risk_max_position_pct")
        total_value = portfolio.total_value_usd(current_price)
        new_xrp_value = (portfolio.xrp_balance + xrp_amount) * current_price
        if total_value > 0 and (new_xrp_value / total_value * 100) > float(max_pct):
            return None, f"Would exceed max XRP position of {max_pct}%"
    elif action == "SELL":
        if portfolio.xrp_balance < xrp_amount:
            return None, f"Insufficient XRP balance: {portfolio.xrp_balance:.6f} < {xrp_amount:.6f}"

    # --- Place order on Kraken ---
    try:
        kraken_result = await kraken_service.place_order(
            pair=pair,
            side=action.lower(),
            volume=xrp_amount,
            order_type=order_type,
            api_key=api_key,
            api_secret=api_secret,
            limit_price=current_price if order_type == "limit" else None,
        )
    except Exception as exc:
        logger.error("Kraken order failed: %s", exc)
        return None, f"Kraken order failed: {exc}"

    filled_price = kraken_result.get("filled_price", current_price)
    order_id     = kraken_result.get("order_id")

    # Recalculate with actual filled price
    usd_amount  = xrp_amount * filled_price
    fee_usd     = usd_amount * fee_pct

    # --- Update local portfolio ---
    if action == "BUY":
        portfolio.usd_balance -= usd_amount + fee_usd
        portfolio.xrp_balance += xrp_amount
    else:
        portfolio.xrp_balance -= xrp_amount
        portfolio.usd_balance += usd_amount - fee_usd

    portfolio.updated_at = datetime.utcnow()
    db.flush()

    trade = Trade(
        timestamp=datetime.utcnow(),
        action=action,
        xrp_amount=xrp_amount,
        usd_amount=usd_amount,
        price_at_trade=filled_price,
        fee_usd=fee_usd,
        fee_type=fee_type,
        usd_balance_after=portfolio.usd_balance,
        xrp_balance_after=portfolio.xrp_balance,
        ai_decision_id=ai_decision_id,
        triggered_by=triggered_by,
        note=note,
        exchange_order_id=order_id,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    avg_buy = _avg_buy_price(db)
    await ws_manager.broadcast("trades", trade.to_dict(avg_buy))

    from app.services.telegram_service import notify_trade
    await notify_trade(db, trade)

    logger.info(
        "Live trade executed: %s %.6f XRP @ $%.6f via Kraken (order %s)",
        action, xrp_amount, filled_price, order_id,
    )
    return trade, None
