from sqlalchemy import Column, Integer, Float, DateTime, String, Text
from app.core.database import Base
from datetime import datetime
import json


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(10), default="pending")  # pending | running | done | error
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False, default=10000.0)
    maker_fee_pct = Column(Float, nullable=False, default=0.1)
    taker_fee_pct = Column(Float, nullable=False, default=0.1)
    decisions_per_hour = Column(Integer, default=12)
    ai_price_window = Column(Integer, default=50)
    ai_model = Column(String(50), nullable=True)
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    def result(self):
        if self.result_json:
            return json.loads(self.result_json)
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "status": self.status,
            "start_date": self.start_date.isoformat() + "Z" if self.start_date else None,
            "end_date": self.end_date.isoformat() + "Z" if self.end_date else None,
            "initial_capital": self.initial_capital,
            "maker_fee_pct": self.maker_fee_pct,
            "taker_fee_pct": self.taker_fee_pct,
            "decisions_per_hour": self.decisions_per_hour,
            "ai_price_window": self.ai_price_window,
            "ai_model": self.ai_model,
            "result": self.result(),
            "error_message": self.error_message,
        }
