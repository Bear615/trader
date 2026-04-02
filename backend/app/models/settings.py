from sqlalchemy import Column, String, Text
from app.core.database import Base
import json


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    def get_value(self):
        return json.loads(self.value)

    @staticmethod
    def from_value(key: str, value, description: str = "") -> "Setting":
        return Setting(key=key, value=json.dumps(value), description=description)
