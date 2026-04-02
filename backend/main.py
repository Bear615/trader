from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import config
from app.core.database import init_db, SessionLocal
from app.services.settings_service import seed_defaults, get_setting

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scheduler state (module-level so it survives reference)
# ---------------------------------------------------------------------------
_scheduler = None


async def _price_poll_job():
    from app.services.price_service import fetch_and_store_price
    await fetch_and_store_price()


async def _ai_decision_job():
    db = SessionLocal()
    try:
        from app.services.ai_service import make_decision
        await make_decision(db)
    finally:
        db.close()


async def _kraken_balance_sync_job():
    db = SessionLocal()
    try:
        from app.services.settings_service import get_setting
        from app.services.kraken_service import get_balances
        from app.services.trading_service import get_portfolio
        from datetime import datetime

        if get_setting(db, "trading_mode") != "live":
            return
        api_key    = get_setting(db, "kraken_api_key")
        api_secret = get_setting(db, "kraken_api_secret")
        if not api_key or not api_secret:
            return

        balances  = await get_balances(api_key, api_secret)
        portfolio = get_portfolio(db)
        portfolio.usd_balance = balances["usd"]
        portfolio.xrp_balance = balances["xrp"]
        portfolio.updated_at  = datetime.utcnow()
        db.commit()
        logger.info(
            "Kraken balance sync: USD=%.2f XRP=%.6f",
            balances["usd"], balances["xrp"],
        )
    except Exception as exc:
        logger.warning("Kraken balance sync failed: %s", exc)
    finally:
        db.close()


def _setup_scheduler(poll_interval: int, ai_interval: int, kraken_sync_minutes: int):
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _price_poll_job,
        "interval",
        seconds=max(poll_interval, 5),
        id="price_poll",
        replace_existing=True,
    )
    _scheduler.add_job(
        _ai_decision_job,
        "interval",
        seconds=max(ai_interval, 30),
        id="ai_decision",
        replace_existing=True,
    )
    _scheduler.add_job(
        _kraken_balance_sync_job,
        "interval",
        seconds=max(kraken_sync_minutes * 60, 60),
        id="kraken_balance_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — price poll every %ds, AI every %ds, Kraken sync every %dm",
        poll_interval, ai_interval, kraken_sync_minutes,
    )
    return _scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    init_db()
    db = SessionLocal()
    try:
        seed_defaults(db)
        poll_interval = int(get_setting(db, "poll_interval_seconds"))
        ai_interval = int(get_setting(db, "ai_decision_interval_seconds"))
        kraken_sync_minutes = int(get_setting(db, "kraken_balance_sync_interval_minutes"))
    finally:
        db.close()

    _setup_scheduler(poll_interval, ai_interval, kraken_sync_minutes)
    logger.info("XRP AI Trader backend started")

    yield

    # ---- Shutdown ----
    if _scheduler:
        _scheduler.shutdown(wait=False)
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="XRP AI Trading Tester",
        version="1.0.0",
        description="Paper-trade XRP with GPT-4o using real-time DIA price data.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security response headers
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            # Only set CSP for non-WebSocket responses
            if not request.url.path.startswith("/ws"):
                response.headers["Content-Security-Policy"] = (
                    "default-src 'none'; frame-ancestors 'none'"
                )
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Mount routers
    from app.api.routes import (
        prices, portfolio, trades, ai, metrics, admin, backtest, websocket_routes, auth
    )
    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)   # unauthenticated — must come first
    app.include_router(prices.router, prefix=prefix)
    app.include_router(portfolio.router, prefix=prefix)
    app.include_router(trades.router, prefix=prefix)
    app.include_router(ai.router, prefix=prefix)
    app.include_router(metrics.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    app.include_router(backtest.router, prefix=prefix)
    app.include_router(websocket_routes.router)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "xrp-ai-trader"}

    return app


app = create_app()
