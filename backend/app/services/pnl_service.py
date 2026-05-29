"""Portfolio P&L helpers based on chronological trade history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass
class PnLSnapshot:
    """Running average-cost P&L state for a list of trades."""

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    avg_entry_price: float | None = None
    remaining_cost_basis: float = 0.0
    per_trade_pnl: dict[int, float | None] = field(default_factory=dict)


def _is_xrp_trade(trade: Any) -> bool:
    """Return true for actual XRP trades, not cash-only balance adjustments."""
    return trade.xrp_amount > 0 and trade.price_at_trade > 0


def compute_pnl_snapshot(trades: Iterable[Any], current_price: float | None = None) -> PnLSnapshot:
    """
    Compute realized/unrealized P&L using average cost accounting.

    BUY fees are capitalized into cost basis. SELL fees reduce proceeds.
    Cash-only balance adjustments (stored as zero-XRP trades) are ignored so
    deposits/withdrawals do not corrupt entry price or realized P&L.
    """
    snapshot = PnLSnapshot()
    open_xrp = 0.0
    cost_basis = 0.0

    for trade in sorted(trades, key=lambda t: (t.timestamp, t.id or 0)):
        snapshot.per_trade_pnl[trade.id] = None
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


def total_return_pct(total_value: float | None, starting_budget: float | None) -> float | None:
    """Return total portfolio ROI percentage against the resettable baseline."""
    if total_value is None or not starting_budget or starting_budget <= 0:
        return None
    return ((total_value - starting_budget) / starting_budget) * 100
