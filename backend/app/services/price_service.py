"""
Price service — polls DIA API for live XRP price and stores PricePoints.
Also handles pruning stale history and seeding from CoinGecko.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.websocket import ws_manager
from app.models.price import PricePoint
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)

DIA_URL = (
    "https://api.diadata.org/v1/assetQuotation/"
    "XRPL/0x0000000000000000000000000000000000000000"
)
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    "?vs_currency=usd&days={days}&interval=daily"
)


async def fetch_and_store_price() -> Optional[PricePoint]:
    """Fetch the current XRP price (Kraken in live mode, DIA otherwise) and persist it."""
    db: Session = SessionLocal()
    try:
        mode = get_setting(db, "trading_mode")
    finally:
        db.close()

    if mode == "live":
        return await _fetch_from_kraken()
    return await _fetch_from_dia()


async def _fetch_from_kraken() -> Optional[PricePoint]:
    """Fetch price from Kraken public ticker API."""
    try:
        from app.services.kraken_service import get_ticker
        from app.core.database import SessionLocal as _SL

        db: Session = _SL()
        try:
            pair = get_setting(db, "kraken_pair")
        finally:
            db.close()

        ticker = await get_ticker(pair)
        price = ticker["price"]
        volume_usd = ticker["volume_24h"] * price
        ts = datetime.utcnow()

        db = SessionLocal()
        try:
            existing = (
                db.query(PricePoint)
                .filter(PricePoint.timestamp == ts)
                .first()
            )
            if existing:
                return existing

            point = PricePoint(
                timestamp=ts,
                price=price,
                price_yesterday=0.0,
                volume_usd=volume_usd,
            )
            db.add(point)
            db.commit()
            db.refresh(point)
            await ws_manager.broadcast("price", point.to_dict())
            return point
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Kraken price fetch failed: %s", exc)
        return None


async def _fetch_from_dia() -> Optional[PricePoint]:
    """Fetch the current XRP price from DIA and persist it."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(DIA_URL)
            resp.raise_for_status()
            data = resp.json()

        price = float(data["Price"])
        price_yesterday = float(data.get("PriceYesterday", 0) or 0)
        volume_usd = float(data.get("VolumeYesterdayUSD", 0) or 0)
        # Parse the timestamp from the DIA response
        raw_time = data.get("Time")
        if raw_time:
            ts = datetime.fromisoformat(raw_time.replace("Z", "+00:00")).replace(tzinfo=None)
        else:
            ts = datetime.utcnow()

        db: Session = SessionLocal()
        try:
            # DIA returns the same timestamp when price hasn't updated — skip duplicates
            existing = (
                db.query(PricePoint)
                .filter(PricePoint.timestamp == ts)
                .first()
            )
            if existing:
                return existing

            point = PricePoint(
                timestamp=ts,
                price=price,
                price_yesterday=price_yesterday,
                volume_usd=volume_usd,
            )
            db.add(point)
            db.commit()
            db.refresh(point)

            # Broadcast to WebSocket subscribers
            await ws_manager.broadcast("price", point.to_dict())

            return point
        finally:
            db.close()

    except Exception as exc:
        logger.warning("Price fetch failed: %s", exc)
        return None


async def prune_old_prices() -> int:
    """Delete price points older than retention setting. Returns rows deleted."""
    db: Session = SessionLocal()
    try:
        retention_days = get_setting(db, "price_history_retention_days")
        cutoff = datetime.utcnow() - timedelta(days=int(retention_days))
        deleted = (
            db.query(PricePoint)
            .filter(PricePoint.timestamp < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted
    finally:
        db.close()


async def seed_from_coingecko(days: int = 30) -> int:
    """
    Seed historical XRP daily prices from CoinGecko into the DB.
    Skips dates that already have a price point within ±12 hours.
    Returns number of rows inserted.
    """
    try:
        url = COINGECKO_URL.format(days=days)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            market_data = resp.json()

        prices = market_data.get("prices", [])  # [[timestamp_ms, price], ...]
        volumes = {int(v[0]): v[1] for v in market_data.get("total_volumes", [])}

        db: Session = SessionLocal()
        try:
            inserted = 0
            for ts_ms, price in prices:
                ts = datetime.utcfromtimestamp(ts_ms / 1000)
                lower = ts - timedelta(hours=12)
                upper = ts + timedelta(hours=12)
                exists = (
                    db.query(PricePoint.id)
                    .filter(PricePoint.timestamp >= lower, PricePoint.timestamp <= upper)
                    .first()
                )
                if exists:
                    continue
                vol = volumes.get(ts_ms, 0)
                db.add(PricePoint(timestamp=ts, price=float(price), volume_usd=float(vol)))
                inserted += 1
            db.commit()
            return inserted
        finally:
            db.close()

    except Exception as exc:
        logger.error("CoinGecko seed failed: %s", exc)
        return 0


def get_latest_price(db: Session) -> Optional[PricePoint]:
    return (
        db.query(PricePoint)
        .order_by(PricePoint.timestamp.desc())
        .first()
    )


def get_price_history(
    db: Session,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    limit: int = 500,
) -> list[PricePoint]:
    q = db.query(PricePoint).order_by(PricePoint.timestamp.desc())
    if from_dt:
        q = q.filter(PricePoint.timestamp >= from_dt)
    if to_dt:
        q = q.filter(PricePoint.timestamp <= to_dt)
    return q.limit(limit).all()
