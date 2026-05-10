"""
WebSocket connection manager.
Tracks active connections per match_id and broadcasts prediction payloads.
"""
import asyncio
import json
from collections import defaultdict
from typing import DefaultDict

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        # match_id → list of active WebSocket connections
        self._connections: DefaultDict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, match_id: int, ws: WebSocket):
        await ws.accept()
        self._connections[match_id].append(ws)
        logger.info(f"WS connected: match={match_id}, total={len(self._connections[match_id])}")

    def disconnect(self, match_id: int, ws: WebSocket):
        conns = self._connections.get(match_id, [])
        if ws in conns:
            conns.remove(ws)
        logger.info(f"WS disconnected: match={match_id}, remaining={len(conns)}")

    async def broadcast(self, match_id: int, payload: dict):
        """Send payload JSON to all connections watching this match."""
        conns = self._connections.get(match_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(match_id, ws)

    def active_connections(self, match_id: int) -> int:
        return len(self._connections.get(match_id, []))

    def total_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Singleton used across the app
manager = ConnectionManager()
