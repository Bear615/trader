from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import require_admin
from app.models.trade import Trade
from app.services.pnl_service import compute_pnl_snapshot, get_pnl_reset_state

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
    all_trades = db.query(Trade).order_by(Trade.timestamp.asc()).all()
    pnl = compute_pnl_snapshot(all_trades, reset_state=get_pnl_reset_state(db))
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [t.to_dict(pnl.per_trade_pnl.get(t.id)) for t in trades],
    }


@router.get("/pnl-report")
def pnl_report(db: Session = Depends(get_db)):
    all_trades = db.query(Trade).order_by(Trade.timestamp.asc(), Trade.id.asc()).all()
    reset_state = get_pnl_reset_state(db)
    pnl = compute_pnl_snapshot(all_trades, reset_state=reset_state)
    profitable = []
    losing = []
    rows = []
    for trade in all_trades:
        trade_pnl = pnl.per_trade_pnl.get(trade.id)
        if trade_pnl is None:
            continue
        row = trade.to_dict(trade_pnl)
        rows.append(row)
        if trade_pnl >= 0:
            profitable.append(trade_pnl)
        else:
            losing.append(trade_pnl)

    return {
        "reset_at": pnl.reset_at.isoformat() + "Z" if pnl.reset_at else None,
        "reset_trade_id": pnl.reset_trade_id,
        "realized_pnl_usd": round(pnl.realized_pnl, 4),
        "winning_pnl_usd": round(sum(profitable), 4),
        "losing_pnl_usd": round(sum(losing), 4),
        "trade_count": len(rows),
        "win_count": len(profitable),
        "loss_count": len(losing),
        "items": list(reversed(rows)),
    }


@router.get("/{trade_id}")
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if not trade:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trade not found")
    all_trades = db.query(Trade).order_by(Trade.timestamp.asc()).all()
    pnl = compute_pnl_snapshot(all_trades, reset_state=get_pnl_reset_state(db))
    return trade.to_dict(pnl.per_trade_pnl.get(trade.id))
