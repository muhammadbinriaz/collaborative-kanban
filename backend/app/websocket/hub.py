from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionHub:
    """In-memory WebSocket rooms for board sync and presence."""

    def __init__(self) -> None:
        self._board_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._presence: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def connect_board(self, board_id: UUID, websocket: WebSocket, user: dict[str, Any]) -> None:
        await websocket.accept()
        key = str(board_id)
        async with self._lock:
            self._board_rooms[key].add(websocket)
            self._presence[key][str(user["id"])] = user
        await self.broadcast_board(
            board_id,
            {"type": "presence.updated", "users": list(self._presence[key].values())},
            exclude=None,
        )

    async def disconnect_board(self, board_id: UUID, websocket: WebSocket, user_id: str | None) -> None:
        key = str(board_id)
        async with self._lock:
            self._board_rooms[key].discard(websocket)
            if user_id and user_id in self._presence[key]:
                del self._presence[key][user_id]
            if not self._board_rooms[key]:
                self._board_rooms.pop(key, None)
                self._presence.pop(key, None)
                return
        await self.broadcast_board(
            board_id,
            {"type": "presence.updated", "users": list(self._presence.get(key, {}).values())},
        )

    async def broadcast_board(
        self,
        board_id: UUID,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        key = str(board_id)
        dead: list[WebSocket] = []
        for ws in list(self._board_rooms.get(key, set())):
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._board_rooms[key].discard(ws)

    def presence_for(self, board_id: UUID) -> list[dict[str, Any]]:
        return list(self._presence.get(str(board_id), {}).values())


hub = ConnectionHub()
