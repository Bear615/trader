from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean
from app.core.database import Base
from datetime import datetime


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, default=1)
    usd_balance = Column(Float, nullable=False, default=10000.0)
    xrp_balance = Column(Float, nullable=False, default=0.0)
    starting_budget = Column(Float, nullable=False, default=10000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    note = Column(String, nullable=True)

    def total_value_usd(self, current_price: float) -> float:
        return self.usd_balance + (self.xrp_balance * current_price)

    def xrp_value_quote(self, current_price: float) -> float:
        return self.xrp_balance * current_price

    def to_dict(
        self,
        current_price: float | None = None,
        quote_currency: str = "USD",
        avg_buy_price: float | None = None,
    ):
        xrp_value = self.xrp_value_quote(current_price) if current_price is not None else None
        total = self.total_value_usd(current_price) if current_price is not None else None
        roi = None
        if total is not None and self.starting_budget > 0:
            roi = ((total - self.starting_budget) / self.starting_budget) * 100
        return {
            "id": self.id,
            "usd_balance": self.usd_balance,
            "xrp_balance": self.xrp_balance,
            "starting_budget": self.starting_budget,
            "total_value_usd": total,
            "xrp_value_quote": xrp_value,
            "quote_currency": quote_currency,
            "roi_pct": roi,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
