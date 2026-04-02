from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, Text
from app.core.database import Base
from datetime import datetime


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    action = Column(String(4), nullable=False)      # "BUY" | "SELL" | "HOLD"
    xrp_amount = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)   # 0.0 – 1.0
    reasoning = Column(Text, nullable=True)
    raw_prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    executed = Column(Boolean, default=False)
    execution_error = Column(Text, nullable=True)
    model_used = Column(String(50), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)

    def to_dict(self, include_raw: bool = False):
        d = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "action": self.action,
            "xrp_amount": self.xrp_amount,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "executed": self.executed,
            "execution_error": self.execution_error,
            "model_used": self.model_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }
        if include_raw:
            d["raw_prompt"] = self.raw_prompt
            d["raw_response"] = self.raw_response
        return d
