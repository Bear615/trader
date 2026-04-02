from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.services.price_service import get_latest_price
from app.services.backtest_service import _compute_live_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"], dependencies=[Depends(require_admin)])


@router.get("")
def get_metrics(db: Session = Depends(get_db)):
    latest = get_latest_price(db)
    current_price = latest.price if latest else 0.0
    return _compute_live_metrics(db, current_price)
