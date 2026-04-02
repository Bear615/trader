from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import require_admin
from app.models.trade import Trade
from app.services.trading_service import _avg_buy_price

router = APIRouter(prefix="/trades", tags=["trades"], dependencies=[Depends(require_admin)])


@router.get("")
def list_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    action: Optional[str] = Query(None, regex="^(BUY|SELL)$"),
    db: Session = Depends(get_db),
):
    q = db.query(Trade).order_by(Trade.timestamp.desc())
    if action:
        q = q.filter(Trade.action == action.upper())
    total = q.count()
    trades = q.offset((page - 1) * per_page).limit(per_page).all()
    avg_buy = _avg_buy_price(db)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [t.to_dict(avg_buy) for t in trades],
    }


@router.get("/{trade_id}")
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if not trade:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trade not found")
    avg_buy = _avg_buy_price(db)
    return trade.to_dict(avg_buy)
