import json
import secrets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import ws_manager
from app.core.config import config

router = APIRouter(tags=["websocket"])

VALID_CHANNELS = {"price", "trades", "decisions"}

# Auth timeout: close the connection if the client doesn't send the auth
# message within this many seconds after connecting.
_AUTH_TIMEOUT_SECONDS = 10


@router.websocket("/ws/{channel}")
async def websocket_endpoint(channel: str, websocket: WebSocket):
    """
    WebSocket endpoint with first-message authentication.

    After connecting, the client MUST send:
        {"auth": "<admin_api_key>"}
    within 10 seconds, otherwise the connection is closed with code 4003.

    The admin key is never passed as a URL query parameter to prevent it
    appearing in server logs, proxy logs, and browser history.
    """
    import asyncio

    if channel not in VALID_CHANNELS:
        await websocket.close(code=4004)
        return

    await websocket.accept()

    # ── First-message auth handshake ──────────────────────────────────────
    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=_AUTH_TIMEOUT_SECONDS,
        )
        msg = json.loads(raw)
        provided_key = str(msg.get("auth", ""))
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
        await websocket.close(code=4003)
        return

    if not secrets.compare_digest(provided_key, config.admin_api_key):
        await websocket.close(code=4003)
        return
    # ─────────────────────────────────────────────────────────────────────

    ws_manager.connect_accepted(channel, websocket)
    try:
        while True:
            # Keep connection alive; client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)
