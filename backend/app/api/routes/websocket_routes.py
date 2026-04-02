import secrets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import ws_manager
from app.core.config import config

router = APIRouter(tags=["websocket"])

VALID_CHANNELS = {"price", "trades", "decisions"}


@router.websocket("/ws/{channel}")
async def websocket_endpoint(channel: str, websocket: WebSocket, key: str = ""):
    if not secrets.compare_digest(key, config.admin_api_key):
        await websocket.close(code=4003)
        return

    if channel not in VALID_CHANNELS:
        await websocket.close(code=4004)
        return

    await ws_manager.connect(channel, websocket)
    try:
        while True:
            # Keep connection alive; client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)
