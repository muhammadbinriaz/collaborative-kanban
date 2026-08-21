from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qs
from uuid import UUID

import socketio
from jwt import InvalidTokenError
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.whiteboard import Whiteboard
from app.models.workspace import WorkspaceMember

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False,
)

# sid -> {user, room_id, color}
_sessions: dict[str, dict[str, Any]] = {}
_room_sids: dict[str, set[str]] = {}


def _user_color(user_id: str) -> str:
    palette = ["#e11d48", "#ea580c", "#ca8a04", "#16a34a", "#0891b2", "#2563eb", "#7c3aed", "#db2777"]
    return palette[sum(ord(ch) for ch in user_id) % len(palette)]


def _token_from_connect(environ: dict[str, Any], auth: dict[str, Any] | None) -> str | None:
    if isinstance(auth, dict) and auth.get("token"):
        return str(auth["token"])
    qs_raw = environ.get("QUERY_STRING") or ""
    if isinstance(qs_raw, bytes):
        qs_raw = qs_raw.decode()
    qs = parse_qs(qs_raw)
    values = qs.get("token") or []
    return values[0] if values else None


def _authenticate(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        return None
    if payload.get("type") != "access" or not payload.get("sub"):
        return None
    db = SessionLocal()
    try:
        user = db.get(User, UUID(payload["sub"]))
        if user is None:
            return None
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "color": _user_color(str(user.id)),
        }
    finally:
        db.close()


def _can_view_whiteboard(user_id: str, whiteboard_id: str) -> bool:
    db = SessionLocal()
    try:
        board = db.get(Whiteboard, UUID(whiteboard_id))
        if board is None:
            return False
        membership = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == board.workspace_id,
                WorkspaceMember.user_id == UUID(user_id),
            )
        )
        return membership is not None
    except (ValueError, TypeError):
        return False
    finally:
        db.close()


def _presence_for(room_id: str) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    for sid in _room_sids.get(room_id, set()):
        session = _sessions.get(sid)
        if not session:
            continue
        users.append({**session["user"], "socket_id": sid, "connection_id": sid})
    return users


@sio.event
async def connect(sid: str, environ: dict[str, Any], auth: dict[str, Any] | None = None) -> bool:
    token = _token_from_connect(environ, auth)
    user = _authenticate(token)
    if user is None:
        logger.warning("excalidraw-room: auth failed sid=%s has_token=%s", sid, bool(token))
        return False
    _sessions[sid] = {"user": user, "room_id": None}
    logger.info("excalidraw-room: connected %s as %s", sid, user["email"])
    await sio.emit("init-room", to=sid)
    return True


@sio.on("join-room")
async def join_room(sid: str, room_id: str) -> None:
    session = _sessions.get(sid)
    if session is None or not room_id:
        return
    if not _can_view_whiteboard(session["user"]["id"], room_id):
        await sio.disconnect(sid)
        return

    await sio.enter_room(sid, room_id)
    session["room_id"] = room_id
    _room_sids.setdefault(room_id, set()).add(sid)

    members = list(_room_sids[room_id])
    if len(members) <= 1:
        await sio.emit("first-in-room", to=sid)
    else:
        await sio.emit("new-user", sid, room=room_id, skip_sid=sid)

    await sio.emit("room-user-change", members, room=room_id)
    await sio.emit("presence", _presence_for(room_id), room=room_id)


@sio.on("server-broadcast")
async def server_broadcast(sid: str, room_id: str, data: Any, iv: Any = None) -> None:
    session = _sessions.get(sid)
    if session is None or session.get("room_id") != room_id:
        return
    await sio.emit("client-broadcast", data, room=room_id, skip_sid=sid)


@sio.on("server-volatile-broadcast")
async def server_volatile_broadcast(sid: str, room_id: str, data: Any, iv: Any = None) -> None:
    session = _sessions.get(sid)
    if session is None or session.get("room_id") != room_id:
        return
    await sio.emit("client-broadcast", data, room=room_id, skip_sid=sid)


@sio.event
async def disconnect(sid: str) -> None:
    session = _sessions.pop(sid, None)
    if not session:
        return
    room_id = session.get("room_id")
    if room_id:
        _room_sids.get(room_id, set()).discard(sid)
        if not _room_sids.get(room_id):
            _room_sids.pop(room_id, None)
        else:
            members = list(_room_sids[room_id])
            await sio.emit("room-user-change", members, room=room_id)
            await sio.emit("presence", _presence_for(room_id), room=room_id)
    logger.info("excalidraw-room: disconnected %s", sid)
