import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import config

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# In-memory rate limiter  (per-IP, resets after RATE_LIMIT_WINDOW seconds)
# ---------------------------------------------------------------------------
_attempts: dict[str, dict] = defaultdict(lambda: {"count": 0, "window_start": 0.0})

RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 15 * 60  # 15 minutes


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    entry = _attempts[ip]

    # Reset window if enough time has passed
    if now - entry["window_start"] >= RATE_LIMIT_WINDOW:
        entry["count"] = 0
        entry["window_start"] = now

    if entry["count"] >= RATE_LIMIT_MAX:
        retry_after = int(RATE_LIMIT_WINDOW - (now - entry["window_start"]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {max(retry_after // 60, 1)} minute(s).",
            headers={"Retry-After": str(retry_after)},
        )

    entry["count"] += 1


class LoginRequest(BaseModel):
    pin: str


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """
    Verify a PIN and return the session token on success.
    Rate-limited to 5 attempts per IP per 15 minutes.
    Set LOGIN_PIN in .env; falls back to ADMIN_API_KEY if LOGIN_PIN is not set.
    """
    # Resolve the real client IP, accounting for a reverse proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else (request.client.host if request.client else "unknown")
    )

    _check_rate_limit(ip)

    expected = config.login_pin if config.login_pin else config.admin_api_key
    if not secrets.compare_digest(body.pin.strip(), expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect PIN.",
        )

    # Successful login — clear this IP's counter
    _attempts[ip]["count"] = 0

    return {"token": config.admin_api_key}
