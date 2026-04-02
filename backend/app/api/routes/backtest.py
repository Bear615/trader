from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.core.database import get_db, SessionLocal
from app.core.auth import require_admin
from app.models.backtest import BacktestRun
from app.services.backtest_service import run_backtest

router = APIRouter(prefix="/admin/backtest", tags=["backtest"], dependencies=[Depends(require_admin)])


class BacktestRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=10000.0, gt=0)
    maker_fee_pct: float = Field(default=0.1, ge=0)
    taker_fee_pct: float = Field(default=0.1, ge=0)
    decisions_per_hour: int = Field(default=12, ge=1, le=60)
    ai_price_window: int = Field(default=50, ge=5, le=500)
    ai_model: Optional[str] = Field(
        default="random",
        description="Model name for AI strategy, or 'random' for random decisions",
    )


@router.post("")
async def start_backtest(
    body: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if body.end_date <= body.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    run = BacktestRun(
        start_date=body.start_date,
        end_date=body.end_date,
        initial_capital=body.initial_capital,
        maker_fee_pct=body.maker_fee_pct,
        taker_fee_pct=body.taker_fee_pct,
        decisions_per_hour=body.decisions_per_hour,
        ai_price_window=body.ai_price_window,
        ai_model=body.ai_model,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(run_backtest, run.id, SessionLocal)
    return {"run_id": run.id, "status": "pending"}


@router.get("")
def list_backtests(db: Session = Depends(get_db)):
    runs = db.query(BacktestRun).order_by(BacktestRun.created_at.desc()).all()
    return [r.to_dict() for r in runs]


@router.get("/{run_id}")
def get_backtest(run_id: int, db: Session = Depends(get_db)):
    run = db.get(BacktestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run.to_dict()
