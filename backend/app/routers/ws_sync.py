"""
Kestrel Core — Realtime WebSocket Broadcast Manager
Manages real-time streaming connections for the Next.js 16 trading cockpit.
Sub-second delivery of MT5 ticks, equity curves, open positions, and copier events.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/ws", tags=["Realtime WebSocket"])


class ConnectionManager:
    """Manages active browser & client WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast JSON payload to all active UI subscribers."""
        async with self._lock:
            dead_connections = []
            payload_str = json.dumps(message)
            for connection in self.active_connections:
                try:
                    await connection.send_text(payload_str)
                except Exception:
                    dead_connections.append(connection)

            for dead in dead_connections:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)


ws_manager = ConnectionManager()


@router.websocket("/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    """
    Sub-second streaming channel for live account telemetry,
    MT5 heartbeat status, equity updates, and remote execution results.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "server_time": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to Kestrel Institutional Live Feed",
        })
        while True:
            # Client heartbeat ping/pong listener
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING":
                    await websocket.send_json({
                        "type": "PONG",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
