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
from app.services.settings_service import (
    MASKED_SECRET,
    SECRET_SETTING_KEYS,
    get_all_settings,
    set_many_settings,
    get_setting_meta,
    get_setting,
)
from app.services.trading_service import reset_portfolio, reset_roi, get_portfolio, execute_trade, _avg_buy_price
from app.services.pnl_service import compute_pnl_snapshot
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
    for key in SECRET_SETTING_KEYS:
        if all_settings.get(key):
            all_settings[key] = MASKED_SECRET
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

    updates = {
        key: value
        for key, value in body.updates.items()
        if not (key in SECRET_SETTING_KEYS and value == MASKED_SECRET)
    }
    if "quote_currency" in updates or "kraken_pair" in updates:
        from app.services.kraken_service import normalize_xrp_pair_for_quote
        quote_currency = str(updates.get("quote_currency") or get_setting(db, "quote_currency")).upper()
        pair = updates.get("kraken_pair") or get_setting(db, "kraken_pair")
        updates["kraken_pair"] = normalize_xrp_pair_for_quote(pair, quote_currency)

    # Detect if we're switching into live mode (not already live)
    switching_to_live = (
        updates.get("trading_mode") == "live"
        and get_setting(db, "trading_mode") != "live"
    )

    try:
        set_many_settings(db, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if switching_to_live:
        # Resolve credentials — may have been included in this same update
        api_key = updates.get("kraken_api_key") or get_setting(db, "kraken_api_key")
        api_secret = updates.get("kraken_api_secret") or get_setting(db, "kraken_api_secret")
        if api_key and api_secret:
            try:
                from app.services.kraken_service import get_balances
                quote_currency = str(get_setting(db, "quote_currency")).upper()
                pair = str(get_setting(db, "kraken_pair"))
                balances = await get_balances(api_key, api_secret, quote_currency, pair)
                portfolio = get_portfolio(db)
                latest = get_latest_price(db)
                current_price = latest.price if latest else 0.0
                portfolio.usd_balance = balances["usd"]
                portfolio.xrp_balance = balances["xrp"]
                portfolio.starting_budget = portfolio.total_value_usd(current_price)
                portfolio.updated_at = datetime.utcnow()
                db.commit()
                logger.info(
                    "Switched to live trading - synced Kraken balances: %s=%.2f XRP=%.6f, starting_budget=%.2f",
                    balances["quote_currency"], balances["usd"], balances["xrp"], portfolio.starting_budget,
                )
            except Exception as exc:
                logger.warning("Failed to sync Kraken balances on switch to live mode: %s", exc)

    return {"ok": True, "updated": list(updates.keys())}


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@router.post("/portfolio/reset")
def reset(db: Session = Depends(get_db)):
    portfolio = reset_portfolio(db)
    latest = get_latest_price(db)
    current_price = latest.price if latest else None
    return portfolio.to_dict(current_price, str(get_setting(db, "quote_currency")).upper(), _avg_buy_price(db))


@router.post("/portfolio/reset-roi")
def reset_roi_endpoint(db: Session = Depends(get_db)):
    portfolio = reset_roi(db)
    latest = get_latest_price(db)
    current_price = latest.price if latest else None
    return portfolio.to_dict(current_price, str(get_setting(db, "quote_currency")).upper(), _avg_buy_price(db))




class BalanceAdjustmentBody(BaseModel):
    amount: float = Field(..., description="Positive for deposit, negative for withdrawal")
    note: Optional[str] = None


@router.post("/portfolio/record-balance-change")
def record_balance_change(body: BalanceAdjustmentBody, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from datetime import datetime

    if body.amount == 0:
        raise HTTPException(status_code=400, detail="Amount must be non-zero")

    portfolio = get_portfolio(db)
    new_balance = portfolio.usd_balance + body.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Balance cannot go negative")

    portfolio.usd_balance = new_balance
    portfolio.updated_at = datetime.utcnow()

    direction = "deposit" if body.amount > 0 else "withdrawal"
    note = (body.note or "").strip()
    trade = Trade(
        timestamp=datetime.utcnow(),
        action="BUY" if body.amount > 0 else "SELL",
        xrp_amount=0.0,
        usd_amount=abs(body.amount),
        price_at_trade=0.0,
        fee_usd=0.0,
        fee_type="maker",
        usd_balance_after=portfolio.usd_balance,
        xrp_balance_after=portfolio.xrp_balance,
        triggered_by="manual",
        note=f"Manual {direction}: {note}" if note else f"Manual {direction}",
    )
    db.add(trade)
    db.commit()

    return {
        "ok": True,
        "change": body.amount,
        "usd_balance": portfolio.usd_balance,
        "xrp_balance": portfolio.xrp_balance,
    }


@router.post("/kraken/check-unexpected-balance-change")
async def kraken_check_unexpected_balance_change(db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.services import kraken_service
    from app.services.settings_service import get_setting
    from app.services.trading_service import get_portfolio
    from datetime import datetime

    api_key = get_setting(db, "kraken_api_key")
    api_secret = get_setting(db, "kraken_api_secret")
    pair = get_setting(db, "kraken_pair")
    threshold = float(get_setting(db, "kraken_balance_delta_warn_threshold") or 0.01)
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Kraken API credentials not configured")

    try:
        quote_currency = str(get_setting(db, "quote_currency")).upper()
        balances = await kraken_service.get_balances(api_key, api_secret, quote_currency, pair)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    portfolio = get_portfolio(db)
    usd_delta = balances["usd"] - portfolio.usd_balance
    xrp_delta = balances["xrp"] - portfolio.xrp_balance

    unexpected_quote_change = abs(usd_delta) >= threshold
    unexpected_xrp_change = abs(xrp_delta) >= 0.000001

    if unexpected_quote_change or unexpected_xrp_change:
        portfolio.usd_balance = balances["usd"]
        portfolio.xrp_balance = balances["xrp"]
        portfolio.updated_at = datetime.utcnow()

        direction = "deposit" if usd_delta > 0 else "withdrawal"
        trade = Trade(
            timestamp=datetime.utcnow(),
            action="BUY" if usd_delta >= 0 else "SELL",
            xrp_amount=0.0,
            usd_amount=abs(usd_delta),
            price_at_trade=0.0,
            fee_usd=0.0,
            fee_type="maker",
            usd_balance_after=portfolio.usd_balance,
            xrp_balance_after=portfolio.xrp_balance,
            triggered_by="manual",
            note=(
                f"Auto-detected Kraken {direction} ({balances['quote_currency']}): {usd_delta:+.2f}; "
                f"XRP delta: {xrp_delta:+.6f}"
            ),
        )
        db.add(trade)
        db.commit()

    return {
        "ok": True,
        "unexpected_quote_change": unexpected_quote_change,
        "unexpected_xrp_change": unexpected_xrp_change,
        "usd_delta": usd_delta,
        "xrp_delta": xrp_delta,
        "quote_currency": balances["quote_currency"],
        "kraken_usd": balances["usd"],
        "kraken_xrp": balances["xrp"],
        "local_usd": portfolio.usd_balance,
        "local_xrp": portfolio.xrp_balance,
    }
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
    trades = db.query(Trade).order_by(Trade.timestamp.asc()).all()
    pnl = compute_pnl_snapshot(trades)
    return trade.to_dict(pnl.per_trade_pnl.get(trade.id))


# ---------------------------------------------------------------------------
# Manual AI trigger
# ---------------------------------------------------------------------------

@router.post("/ai/trigger")
async def trigger_ai(db: Session = Depends(get_db)):
    from app.services.ai_service import make_decision, get_last_ai_error
    decision = await make_decision(db, bypass_guards=True)
    if not decision:
        from fastapi import HTTPException
        detail = get_last_ai_error() or (
            "AI decision could not be made. Check AI provider settings and backend logs."
        )
        raise HTTPException(
            status_code=400,
            detail=detail,
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
    quote_currency = str(get_setting(db, "quote_currency")).upper()
    quote_currency_lower = quote_currency.lower()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["report", "xrp_trades_export"])
    writer.writerow(["generated_at_utc", datetime.utcnow().isoformat() + "Z"])
    writer.writerow(["quote_currency", quote_currency])
    writer.writerow(["total_rows", len(trades)])
    writer.writerow([])
    writer.writerow([
        "id", "timestamp_utc", "action", "xrp_amount", f"{quote_currency_lower}_gross_amount",
        f"{quote_currency_lower}_net_amount", "price_at_trade", f"fee_{quote_currency_lower}", "fee_type", "triggered_by",
        f"{quote_currency_lower}_balance_after", "xrp_balance_after", f"running_{quote_currency_lower}_fees",
        f"running_realized_{quote_currency_lower}_pnl", "avg_entry_price_reference",
        "ai_decision_id", "note", "exchange_order_id",
    ])
    running_fees = 0.0
    running_realized_pnl = 0.0
    pnl_snapshot = compute_pnl_snapshot(trades)
    for t in trades:
        net_amount = t.usd_amount - t.fee_usd if t.action == "SELL" else t.usd_amount + t.fee_usd
        pnl = pnl_snapshot.per_trade_pnl.get(t.id)
        running_fees += t.fee_usd
        if pnl is not None:
            running_realized_pnl += pnl
        writer.writerow([
            t.id, t.timestamp.isoformat(), t.action, t.xrp_amount, t.usd_amount,
            net_amount, t.price_at_trade, t.fee_usd, t.fee_type, t.triggered_by,
            t.usd_balance_after, t.xrp_balance_after, running_fees, running_realized_pnl,
            pnl_snapshot.avg_entry_price, t.ai_decision_id, t.note,
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
    pair       = get_setting(db, "kraken_pair")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Kraken API credentials not configured")
    try:
        quote_currency = str(get_setting(db, "quote_currency")).upper()
        balances = await kraken_service.get_balances(api_key, api_secret, quote_currency, pair)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"ok": True, "usd": balances["usd"], "quote_currency": balances["quote_currency"], "xrp": balances["xrp"]}


@router.post("/kraken/sync-balance")
async def kraken_sync_balance(db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.services import kraken_service
    from app.services.settings_service import get_setting
    from app.services.trading_service import get_portfolio
    from datetime import datetime

    api_key    = get_setting(db, "kraken_api_key")
    api_secret = get_setting(db, "kraken_api_secret")
    pair       = get_setting(db, "kraken_pair")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Kraken API credentials not configured")
    try:
        quote_currency = str(get_setting(db, "quote_currency")).upper()
        balances = await kraken_service.get_balances(api_key, api_secret, quote_currency, pair)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    portfolio = get_portfolio(db)
    portfolio.usd_balance = balances["usd"]
    portfolio.xrp_balance = balances["xrp"]
    portfolio.updated_at  = datetime.utcnow()
    db.commit()
    return {"ok": True, "usd": balances["usd"], "quote_currency": balances["quote_currency"], "xrp": balances["xrp"]}
