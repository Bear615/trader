import secrets
import time

from fastapi import Cookie, Header, HTTPException, status
from app.core.config import config

SESSION_COOKIE_NAME = "trader_admin_session"
SESSION_TTL_SECONDS = 8 * 60 * 60

_sessions: dict[str, float] = {}


def create_admin_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + SESSION_TTL_SECONDS
    return token


def revoke_admin_session(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def validate_admin_session(token: str | None) -> bool:
    if not token:
        return False
    expires_at = _sessions.get(token)
    if expires_at is None:
        return False
    if expires_at <= time.time():
        _sessions.pop(token, None)
        return False
    return True


async def require_admin(
    x_admin_key: str | None = Header(default=None),
    trader_admin_session: str | None = Cookie(default=None),
):
    if validate_admin_session(trader_admin_session):
        return
    # Keep the header path for local scripts and non-browser clients.
    if x_admin_key and secrets.compare_digest(x_admin_key, config.admin_api_key):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid admin credentials.",
    )
