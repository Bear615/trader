from sqlalchemy import Column, Integer, Float, DateTime
from app.core.database import Base
from datetime import datetime


class PricePoint(Base):
    __tablename__ = "price_points"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    price_yesterday = Column(Float, nullable=True)
    volume_usd = Column(Float, nullable=True)
    source = Column(Integer, nullable=True)  # reserved for future multi-source support

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "price": self.price,
            "price_yesterday": self.price_yesterday,
            "volume_usd": self.volume_usd,
        }
