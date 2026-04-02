from fastapi import WebSocket
from typing import Dict, List
import asyncio
import json


class ConnectionManager:
    """Manages WebSocket connections grouped by channel."""

    def __init__(self):
        self._channels: Dict[str, List[WebSocket]] = {}

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        self._channels.setdefault(channel, []).append(websocket)

    def disconnect(self, channel: str, websocket: WebSocket):
        if channel in self._channels:
            self._channels[channel] = [
                ws for ws in self._channels[channel] if ws is not websocket
            ]

    async def broadcast(self, channel: str, data: dict):
        payload = json.dumps(data)
        dead: List[WebSocket] = []
        for ws in self._channels.get(channel, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(channel, ws)

    def connection_count(self, channel: str) -> int:
        return len(self._channels.get(channel, []))


ws_manager = ConnectionManager()
