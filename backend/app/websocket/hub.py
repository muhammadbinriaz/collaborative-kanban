from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionHub:
    """In-memory WebSocket rooms for board sync, whiteboards, and presence."""

    def __init__(self) -> None:
        self._board_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._presence: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._whiteboard_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # connection_id -> collaborator payload
        self._whiteboard_presence: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._whiteboard_sockets: dict[str, dict[WebSocket, str]] = defaultdict(dict)
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
        await self._broadcast(self._board_rooms, str(board_id), message, exclude)

    def presence_for(self, board_id: UUID) -> list[dict[str, Any]]:
        return list(self._presence.get(str(board_id), {}).values())

    async def connect_whiteboard(
        self, whiteboard_id: UUID, websocket: WebSocket, user: dict[str, Any], *, already_accepted: bool = False
    ) -> str:
        if not already_accepted:
            await websocket.accept()
        key = str(whiteboard_id)
        connection_id = str(uuid4())
        payload = {**user, "connection_id": connection_id}
        async with self._lock:
            self._whiteboard_rooms[key].add(websocket)
            self._whiteboard_sockets[key][websocket] = connection_id
            self._whiteboard_presence[key][connection_id] = payload
        await self.broadcast_whiteboard(
            whiteboard_id,
            {"type": "presence.updated", "users": list(self._whiteboard_presence[key].values())},
        )
        await websocket.send_json({"type": "connection.hello", "connection_id": connection_id})
        return connection_id

    async def disconnect_whiteboard(
        self, whiteboard_id: UUID, websocket: WebSocket
    ) -> None:
        key = str(whiteboard_id)
        async with self._lock:
            connection_id = self._whiteboard_sockets[key].pop(websocket, None)
            self._whiteboard_rooms[key].discard(websocket)
            if connection_id and connection_id in self._whiteboard_presence[key]:
                del self._whiteboard_presence[key][connection_id]
            if not self._whiteboard_rooms[key]:
                self._whiteboard_rooms.pop(key, None)
                self._whiteboard_presence.pop(key, None)
                self._whiteboard_sockets.pop(key, None)
                return
        await self.broadcast_whiteboard(
            whiteboard_id,
            {
                "type": "presence.updated",
                "users": list(self._whiteboard_presence.get(key, {}).values()),
            },
        )

    async def broadcast_whiteboard(
        self,
        whiteboard_id: UUID,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        await self._broadcast(self._whiteboard_rooms, str(whiteboard_id), message, exclude)

    def whiteboard_presence_for(self, whiteboard_id: UUID) -> list[dict[str, Any]]:
        return list(self._whiteboard_presence.get(str(whiteboard_id), {}).values())

    async def _broadcast(
        self,
        rooms: dict[str, set[WebSocket]],
        key: str,
        message: dict[str, Any],
        exclude: WebSocket | None,
    ) -> None:
        dead: list[WebSocket] = []
        for ws in list(rooms.get(key, set())):
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    rooms[key].discard(ws)


hub = ConnectionHub()
