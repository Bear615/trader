"""Portfolio P&L helpers based on chronological trade history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session


@dataclass
class PnLResetState:
    """Optional baseline used to restart P&L accounting from a chosen moment."""

    reset_at: datetime | None = None
    reset_trade_id: int | None = None
    open_xrp: float = 0.0
    cost_basis: float = 0.0
    price: float | None = None


@dataclass
class PnLSnapshot:
    """Running average-cost P&L state for a list of trades."""

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    avg_entry_price: float | None = None
    remaining_cost_basis: float = 0.0
    per_trade_pnl: dict[int, float | None] = field(default_factory=dict)
    reset_at: datetime | None = None
    reset_trade_id: int | None = None


def _is_xrp_trade(trade: Any) -> bool:
    """Return true for actual XRP trades, not cash-only balance adjustments."""
    return trade.xrp_amount > 0 and trade.price_at_trade > 0


def _is_after_reset(trade: Any, reset_state: PnLResetState | None) -> bool:
    if reset_state is None:
        return True
    if reset_state.reset_trade_id is not None and trade.id is not None:
        return trade.id > reset_state.reset_trade_id
    if reset_state.reset_at is not None:
        return trade.timestamp > reset_state.reset_at
    return True


def compute_pnl_snapshot(
    trades: Iterable[Any],
    current_price: float | None = None,
    reset_state: PnLResetState | None = None,
) -> PnLSnapshot:
    """
    Compute realized/unrealized P&L using average cost accounting.

    BUY fees are capitalized into cost basis. SELL fees reduce proceeds.
    Cash-only balance adjustments (stored as zero-XRP trades) are ignored so
    deposits/withdrawals do not corrupt entry price or realized P&L.

    When ``reset_state`` is provided, historical trades are retained in the
    response with null per-trade P&L, while realized/open P&L is calculated from
    the reset baseline forward.
    """
    snapshot = PnLSnapshot(
        reset_at=reset_state.reset_at if reset_state else None,
        reset_trade_id=reset_state.reset_trade_id if reset_state else None,
    )
    open_xrp = max(0.0, reset_state.open_xrp) if reset_state else 0.0
    cost_basis = max(0.0, reset_state.cost_basis) if reset_state else 0.0

    for trade in sorted(trades, key=lambda t: (t.timestamp, t.id or 0)):
        snapshot.per_trade_pnl[trade.id] = None
        if not _is_after_reset(trade, reset_state):
            continue
        if not _is_xrp_trade(trade):
            continue

        if trade.action == "BUY":
            open_xrp += trade.xrp_amount
            cost_basis += trade.usd_amount + trade.fee_usd
            continue

        if trade.action != "SELL" or open_xrp <= 0 or cost_basis <= 0:
            continue

        avg_cost = cost_basis / open_xrp
        sold_xrp = min(trade.xrp_amount, open_xrp)
        sold_cost_basis = avg_cost * sold_xrp
        proceeds = trade.usd_amount - trade.fee_usd
        pnl = proceeds - sold_cost_basis

        snapshot.per_trade_pnl[trade.id] = pnl
        snapshot.realized_pnl += pnl
        open_xrp -= sold_xrp
        cost_basis = max(0.0, cost_basis - sold_cost_basis)

        if open_xrp <= 1e-12:
            open_xrp = 0.0
            cost_basis = 0.0

    snapshot.remaining_cost_basis = cost_basis
    snapshot.avg_entry_price = (cost_basis / open_xrp) if open_xrp > 0 and cost_basis > 0 else None

    if current_price is not None and open_xrp > 0:
        snapshot.unrealized_pnl = (open_xrp * current_price) - cost_basis

    return snapshot


def _parse_reset_at(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", ""))
    return None


def get_pnl_reset_state(db: Session) -> PnLResetState | None:
    """Read the optional persisted P&L reset baseline from settings."""
    from app.services.settings_service import get_setting

    reset_at = _parse_reset_at(get_setting(db, "pnl_reset_at"))
    if reset_at is None:
        return None
    reset_trade_id_raw = get_setting(db, "pnl_reset_trade_id")
    reset_trade_id = int(reset_trade_id_raw) if reset_trade_id_raw is not None else None
    open_xrp = float(get_setting(db, "pnl_reset_open_xrp") or 0.0)
    cost_basis = float(get_setting(db, "pnl_reset_cost_basis_usd") or 0.0)
    price_raw = get_setting(db, "pnl_reset_price")
    price = float(price_raw) if price_raw is not None else None
    return PnLResetState(
        reset_at=reset_at,
        reset_trade_id=reset_trade_id,
        open_xrp=open_xrp,
        cost_basis=cost_basis,
        price=price,
    )


def reset_pnl_baseline(db: Session, current_price: float | None = None) -> PnLResetState:
    """Persist a new P&L baseline using current holdings valued at current price."""
    from app.models.trade import Trade
    from app.services.settings_service import set_setting
    from app.services.trading_service import get_portfolio

    now = datetime.utcnow()
    trades = db.query(Trade).order_by(Trade.timestamp.asc(), Trade.id.asc()).all()
    latest_trade = trades[-1] if trades else None
    portfolio = get_portfolio(db)
    price = float(current_price or 0.0)
    open_xrp = float(portfolio.xrp_balance or 0.0)
    previous_snapshot = compute_pnl_snapshot(trades)
    cost_basis = (
        open_xrp * price
        if open_xrp > 0 and price > 0
        else previous_snapshot.remaining_cost_basis
    )

    set_setting(db, "pnl_reset_at", now.isoformat() + "Z")
    set_setting(db, "pnl_reset_trade_id", latest_trade.id if latest_trade else None)
    set_setting(db, "pnl_reset_open_xrp", open_xrp)
    set_setting(db, "pnl_reset_cost_basis_usd", cost_basis)
    set_setting(db, "pnl_reset_price", price if price > 0 else None)

    return PnLResetState(
        reset_at=now,
        reset_trade_id=latest_trade.id if latest_trade else None,
        open_xrp=open_xrp,
        cost_basis=cost_basis,
        price=price if price > 0 else None,
    )


def total_return_pct(total_value: float | None, starting_budget: float | None) -> float | None:
    """Return total portfolio ROI percentage against the resettable baseline."""
    if total_value is None or not starting_budget or starting_budget <= 0:
        return None
    return ((total_value - starting_budget) / starting_budget) * 100
