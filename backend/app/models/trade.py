from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from app.core.database import Base
from datetime import datetime


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    action = Column(String(4), nullable=False)          # "BUY" | "SELL"
    xrp_amount = Column(Float, nullable=False)
    usd_amount = Column(Float, nullable=False)          # gross selected quote-currency value of trade
    price_at_trade = Column(Float, nullable=False)
    fee_usd = Column(Float, nullable=False, default=0.0)
    fee_type = Column(String(6), nullable=False, default="taker")  # "maker" | "taker"
    usd_balance_after = Column(Float, nullable=True)
    xrp_balance_after = Column(Float, nullable=True)
    ai_decision_id = Column(Integer, ForeignKey("ai_decisions.id"), nullable=True)
    triggered_by = Column(String(10), nullable=False, default="ai")  # "ai" | "manual"
    note = Column(String, nullable=True)
    exchange_order_id = Column(String, nullable=True)  # Kraken txid when trading_mode == 'live'

    def pnl(self, realized_pnl: float | None = None) -> float | None:
        """Return precomputed realized P&L for SELL trades."""
        return realized_pnl if self.action == "SELL" else None

    def to_dict(self, realized_pnl: float | None = None):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "action": self.action,
            "xrp_amount": self.xrp_amount,
            "usd_amount": self.usd_amount,
            "price_at_trade": self.price_at_trade,
            "fee_usd": self.fee_usd,
            "fee_type": self.fee_type,
            "usd_balance_after": self.usd_balance_after,
            "xrp_balance_after": self.xrp_balance_after,
            "ai_decision_id": self.ai_decision_id,
            "triggered_by": self.triggered_by,
            "pnl": self.pnl(realized_pnl),
            "note": self.note,
            "exchange_order_id": self.exchange_order_id,
        }
