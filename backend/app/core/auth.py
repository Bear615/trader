import secrets

from fastapi import Header, HTTPException, status
from app.core.config import config


async def require_admin(x_admin_key: str = Header(...)):
    # Use secrets.compare_digest to prevent timing-based key enumeration
    if not secrets.compare_digest(x_admin_key, config.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key.",
        )
