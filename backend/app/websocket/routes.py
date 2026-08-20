from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.board import Board
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.websocket.hub import hub
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def _authenticate_ws(token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        return None
    if payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.get(User, UUID(user_id))
    finally:
        db.close()


def _can_view_board(user: User, board_id: UUID) -> bool:
    db = SessionLocal()
    try:
        board = db.get(Board, board_id)
        if board is None:
            return False
        membership = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == board.workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
        return membership is not None
    finally:
        db.close()


@router.websocket("/ws/boards/{board_id}")
async def board_ws(websocket: WebSocket, board_id: UUID, token: str | None = Query(default=None)) -> None:
    user = _authenticate_ws(token)
    if user is None or not _can_view_board(user, board_id):
        await websocket.close(code=4401)
        return

    user_payload = {"id": str(user.id), "name": user.name, "email": user.email}
    await hub.connect_board(board_id, websocket, user_payload)
    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "presence.ping":
                await websocket.send_json(
                    {"type": "presence.updated", "users": hub.presence_for(board_id)}
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Board websocket error")
    finally:
        await hub.disconnect_board(board_id, websocket, str(user.id))


@router.websocket("/ws/presence")
async def presence_ws(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    """Lightweight global presence ping channel (authenticated)."""
    user = _authenticate_ws(token)
    if user is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        await websocket.send_json(
            {"type": "presence.hello", "user": {"id": str(user.id), "name": user.name}}
        )
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Presence websocket error")
