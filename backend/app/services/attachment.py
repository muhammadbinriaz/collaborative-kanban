from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.attachment import AttachmentPublic
from app.services import storage
from app.services.activity import log_activity, publish_board_event
from app.services.board import require_board
from app.services.card import _load_card

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
SAFE_NAME = re.compile(r"[^A-Za-z0-9._\-]+")


def _public(row: Attachment, *, include_url: bool = True) -> AttachmentPublic:
    return AttachmentPublic(
        id=row.id,
        card_id=row.card_id,
        uploaded_by_id=row.uploaded_by_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        created_at=row.created_at,
        download_url=storage.presigned_get_url(row.object_key) if include_url else None,
    )


def list_attachments(db: Session, user: User, card_id: UUID) -> list[AttachmentPublic]:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    require_board(db, card.board_list.board_id, user)
    rows = db.scalars(
        select(Attachment).where(Attachment.card_id == card_id).order_by(Attachment.created_at.desc())
    ).all()
    return [_public(row) for row in rows]


async def upload_attachment(
    db: Session, user: User, card_id: UUID, file: UploadFile
) -> AttachmentPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)

    filename = (file.filename or "upload.bin").strip() or "upload.bin"
    content_type = file.content_type or "application/octet-stream"
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 25MB limit")

    safe = SAFE_NAME.sub("_", filename)[:180]
    key = f"boards/{board.id}/cards/{card_id}/{uuid4().hex}_{safe}"
    storage.upload_bytes(key=key, body=data, content_type=content_type)

    row = Attachment(
        card_id=card_id,
        uploaded_by_id=user.id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        object_key=key,
    )
    db.add(row)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        actor=user,
        action="attachment.created",
        summary=f'{user.name} attached "{filename}"',
        board_id=board.id,
        card_id=card_id,
        meta={"filename": filename, "size_bytes": len(data)},
    )
    db.commit()
    db.refresh(row)
    public = _public(row)
    await publish_board_event(board.id, "attachment.created", {"card_id": str(card_id), "id": str(row.id)})
    return public


async def delete_attachment(db: Session, user: User, attachment_id: UUID) -> None:
    row = db.get(Attachment, attachment_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    card = _load_card(db, row.card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)
    storage.delete_object(row.object_key)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        actor=user,
        action="attachment.deleted",
        summary=f'{user.name} removed attachment "{row.filename}"',
        board_id=board.id,
        card_id=row.card_id,
        meta={"filename": row.filename},
    )
    db.delete(row)
    db.commit()
    await publish_board_event(
        board.id, "attachment.deleted", {"card_id": str(card.id), "id": str(attachment_id)}
    )
