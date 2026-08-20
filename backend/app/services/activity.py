from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.collaboration import Activity, Notification
from app.models.user import User
from app.websocket.hub import hub


def log_activity(
    db: Session,
    *,
    workspace_id: UUID,
    actor: User,
    action: str,
    summary: str,
    board_id: UUID | None = None,
    card_id: UUID | None = None,
    meta: dict[str, Any] | None = None,
) -> Activity:
    activity = Activity(
        workspace_id=workspace_id,
        board_id=board_id,
        card_id=card_id,
        actor_id=actor.id,
        action=action,
        summary=summary,
        meta=meta,
    )
    db.add(activity)
    db.flush()
    return activity


def create_notification(
    db: Session,
    *,
    user_id: UUID,
    type: str,
    title: str,
    body: str,
    link: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Notification:
    note = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        link=link,
        meta=meta,
    )
    db.add(note)
    db.flush()
    return note


async def publish_board_event(board_id: UUID, event_type: str, payload: dict[str, Any]) -> None:
    await hub.broadcast_board(board_id, {"type": event_type, "payload": payload, "at": datetime.now(UTC).isoformat()})
