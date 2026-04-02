from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
import csv
import io

import logging

from app.core.database import get_db, SessionLocal
from app.core.auth import require_admin
from app.models.backtest import BacktestRun
from app.services.settings_service import get_all_settings, set_many_settings, get_setting_meta, get_setting
from app.services.trading_service import reset_portfolio, get_portfolio, execute_trade
from app.services.price_service import get_latest_price, seed_from_coingecko, prune_old_prices
from app.services.backtest_service import run_backtest
from app.models.price import PricePoint
from app.models.trade import Trade

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    all_settings = get_all_settings(db)
    meta = {m["key"]: m for m in get_setting_meta()}
    return {
        "settings": all_settings,
        "meta": meta,
    }


class SettingsUpdate(BaseModel):
    updates: dict[str, Any]


@router.put("/settings")
async def update_settings(body: SettingsUpdate, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    # Detect if we're switching into live mode (not already live)
    switching_to_live = (
        body.updates.get("trading_mode") == "live"
        and get_setting(db, "trading_mode") != "live"
    )

    try:
        set_many_settings(db, body.updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if switching_to_live:
        # Resolve credentials — may have been included in this same update
        api_key = body.updates.get("kraken_api_key") or get_setting(db, "kraken_api_key")
        api_secret = body.updates.get("kraken_api_secret") or get_setting(db, "kraken_api_secret")
        if api_key and api_secret:
            try:
                from app.services.kraken_service import get_balances
                balances = await get_balances(api_key, api_secret)
                portfolio = get_portfolio(db)
                latest = get_latest_price(db)
                current_price = latest.price if latest else 0.0
                portfolio.usd_balance = balances["usd"]
                portfolio.xrp_balance = balances["xrp"]
                portfolio.starting_budget = portfolio.total_value_usd(current_price)
                portfolio.updated_at = datetime.utcnow()
                db.commit()
                logger.info(
                    "Switched to live trading — synced Kraken balances: USD=%.2f XRP=%.6f, starting_budget=%.2f",
                    balances["usd"], balances["xrp"], portfolio.starting_budget,
                )
            except Exception as exc:
                logger.warning("Failed to sync Kraken balances on switch to live mode: %s", exc)

    return {"ok": True, "updated": list(body.updates.keys())}


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@router.post("/portfolio/reset")
def reset(db: Session = Depends(get_db)):
    portfolio = reset_portfolio(db)
    return portfolio.to_dict()


# ---------------------------------------------------------------------------
# Manual trade
# ---------------------------------------------------------------------------

class ManualTradeBody(BaseModel):
    action: str = Field(..., pattern="^(BUY|SELL)$")
    xrp_amount: float = Field(..., gt=0)
    note: Optional[str] = None


@router.post("/trades")
async def manual_trade(body: ManualTradeBody, db: Session = Depends(get_db)):
    latest = get_latest_price(db)
    if not latest:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No price data available yet.")
    trade, err = await execute_trade(
        db=db,
        action=body.action,
        xrp_amount=body.xrp_amount,
        current_price=latest.price,
        fee_type="maker",
        triggered_by="manual",
        note=body.note,
    )
    if err:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=err)
    return trade.to_dict()


# ---------------------------------------------------------------------------
# Manual AI trigger
# ---------------------------------------------------------------------------

@router.post("/ai/trigger")
async def trigger_ai(db: Session = Depends(get_db)):
    from app.services.ai_service import make_decision
    decision = await make_decision(db, bypass_guards=True)
    if not decision:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=(
                "AI decision could not be made. Check the backend console for the reason. "
                "Common causes: no price data yet, wrong ai_provider_preset (must be 'ollama'), "
                "or Ollama is unreachable at the configured URL."
            ),
        )
    return decision.to_dict(include_raw=True)

@router.post("/seed-history")
async def seed_history(days: int = 30):
    inserted = await seed_from_coingecko(days=days)
    return {"inserted": inserted, "days": days}


@router.post("/prune-history")
async def prune_history():
    deleted = await prune_old_prices()
    return {"deleted": deleted}


@router.delete("/history/prices")
def clear_price_history(db: Session = Depends(get_db)):
    deleted = db.query(PricePoint).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


@router.delete("/history/trades")
def clear_trade_history(db: Session = Depends(get_db)):
    deleted = db.query(Trade).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

@router.get("/export/trades")
def export_trades_csv(db: Session = Depends(get_db)):
    trades = db.query(Trade).order_by(Trade.timestamp.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "timestamp", "action", "xrp_amount", "usd_amount",
        "price_at_trade", "fee_usd", "fee_type", "triggered_by",
        "usd_balance_after", "xrp_balance_after", "ai_decision_id", "note",
        "exchange_order_id",
    ])
    for t in trades:
        writer.writerow([
            t.id, t.timestamp.isoformat(), t.action, t.xrp_amount, t.usd_amount,
            t.price_at_trade, t.fee_usd, t.fee_type, t.triggered_by,
            t.usd_balance_after, t.xrp_balance_after, t.ai_decision_id, t.note,
            t.exchange_order_id,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trades.csv"},
    )


# ---------------------------------------------------------------------------
# Kraken live-mode helpers
# ---------------------------------------------------------------------------

@router.post("/kraken/test-connection")
async def kraken_test_connection(db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.services import kraken_service
    from app.services.settings_service import get_setting

    api_key    = get_setting(db, "kraken_api_key")
    api_secret = get_setting(db, "kraken_api_secret")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Kraken API credentials not configured")
    try:
        balances = await kraken_service.get_balances(api_key, api_secret)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"ok": True, "usd": balances["usd"], "xrp": balances["xrp"]}


@router.post("/kraken/sync-balance")
async def kraken_sync_balance(db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.services import kraken_service
    from app.services.settings_service import get_setting
    from app.services.trading_service import get_portfolio
    from datetime import datetime

    if get_setting(db, "trading_mode") != "live":
        raise HTTPException(status_code=400, detail="Not in live trading mode")
    api_key    = get_setting(db, "kraken_api_key")
    api_secret = get_setting(db, "kraken_api_secret")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Kraken API credentials not configured")
    try:
        balances = await kraken_service.get_balances(api_key, api_secret)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    portfolio = get_portfolio(db)
    portfolio.usd_balance = balances["usd"]
    portfolio.xrp_balance = balances["xrp"]
    portfolio.updated_at  = datetime.utcnow()
    db.commit()
    return {"ok": True, "usd": balances["usd"], "xrp": balances["xrp"]}
