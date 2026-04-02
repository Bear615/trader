from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.services.trading_service import get_portfolio
from app.services.price_service import get_latest_price

router = APIRouter(prefix="/portfolio", tags=["portfolio"], dependencies=[Depends(require_admin)])


@router.get("")
def get_portfolio_state(db: Session = Depends(get_db)):
    latest = get_latest_price(db)
    current_price = latest.price if latest else None
    portfolio = get_portfolio(db)
    return portfolio.to_dict(current_price)
