from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.auth import require_admin
from app.services.price_service import get_latest_price, get_price_history

router = APIRouter(prefix="/prices", tags=["prices"], dependencies=[Depends(require_admin)])


@router.get("/current")
def current_price(db: Session = Depends(get_db)):
    point = get_latest_price(db)
    if not point:
        return {"price": None, "message": "No price data yet. Waiting for first poll."}
    return point.to_dict()


@router.get("/history")
def price_history(
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=5000),
    timeframe: Optional[str] = Query(None, description="Shorthand: 1h, 6h, 24h, 7d, 30d"),
    db: Session = Depends(get_db),
):
    if timeframe and not from_dt:
        mapping = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}
        hours = mapping.get(timeframe, 24)
        from_dt = datetime.utcnow() - timedelta(hours=hours)

    points = get_price_history(db, from_dt=from_dt, to_dt=to_dt, limit=limit)
    # Return in ascending order for charting
    return [p.to_dict() for p in reversed(points)]
