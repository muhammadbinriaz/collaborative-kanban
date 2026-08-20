from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.collaboration import Activity, Notification
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.auth import UserPublic
from app.schemas.collaboration import ActivityPublic, NotificationPublic
from app.services.board import require_board
from app.services.workspace import require_workspace


def list_board_activity(db: Session, user: User, board_id: UUID, limit: int = 50) -> list[ActivityPublic]:
    board = require_board(db, board_id, user)
    rows = db.scalars(
        select(Activity)
        .options(selectinload(Activity.actor))
        .where(Activity.board_id == board.id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
    ).all()
    return [
        ActivityPublic(
            id=row.id,
            workspace_id=row.workspace_id,
            board_id=row.board_id,
            card_id=row.card_id,
            actor_id=row.actor_id,
            actor=UserPublic.model_validate(row.actor),
            action=row.action,
            summary=row.summary,
            meta=row.meta,
            created_at=row.created_at,
        )
        for row in rows
    ]


def list_workspace_activity(
    db: Session, user: User, workspace_id: UUID, limit: int = 50
) -> list[ActivityPublic]:
    require_workspace(db, workspace_id, user, WorkspaceRole.VIEWER)
    rows = db.scalars(
        select(Activity)
        .options(selectinload(Activity.actor))
        .where(Activity.workspace_id == workspace_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
    ).all()
    return [
        ActivityPublic(
            id=row.id,
            workspace_id=row.workspace_id,
            board_id=row.board_id,
            card_id=row.card_id,
            actor_id=row.actor_id,
            actor=UserPublic.model_validate(row.actor),
            action=row.action,
            summary=row.summary,
            meta=row.meta,
            created_at=row.created_at,
        )
        for row in rows
    ]


def list_notifications(db: Session, user: User, unread_only: bool = False) -> list[NotificationPublic]:
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    rows = db.scalars(query.order_by(Notification.created_at.desc()).limit(50)).all()
    return [NotificationPublic.model_validate(row) for row in rows]


def mark_notification_read(db: Session, user: User, notification_id: UUID) -> NotificationPublic:
    note = db.get(Notification, notification_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    note.read_at = datetime.now(UTC)
    db.commit()
    db.refresh(note)
    return NotificationPublic.model_validate(note)


def mark_all_read(db: Session, user: User) -> None:
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ).all()
    now = datetime.now(UTC)
    for row in rows:
        row.read_at = now
    db.commit()
