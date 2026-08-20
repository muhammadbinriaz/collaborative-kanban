from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.card import Card
from app.models.collaboration import Comment, CommentMention
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.auth import UserPublic
from app.schemas.collaboration import CommentCreate, CommentPublic
from app.services.activity import create_notification, log_activity, publish_board_event
from app.services.board import require_board
from app.services.card import _load_card

MENTION_RE = re.compile(r"@([\w.\-]+)")


def _comment_public(comment: Comment) -> CommentPublic:
    return CommentPublic(
        id=comment.id,
        card_id=comment.card_id,
        author_id=comment.author_id,
        author=UserPublic.model_validate(comment.author),
        body=comment.body,
        mentioned_user_ids=[m.user_id for m in comment.mentions],
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def list_comments(db: Session, user: User, card_id: UUID) -> list[CommentPublic]:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    require_board(db, card.board_list.board_id, user)
    rows = db.scalars(
        select(Comment)
        .options(selectinload(Comment.author), selectinload(Comment.mentions))
        .where(Comment.card_id == card_id)
        .order_by(Comment.created_at.asc())
    ).all()
    return [_comment_public(row) for row in rows]


async def create_comment(
    db: Session, user: User, card_id: UUID, payload: CommentCreate
) -> CommentPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)
    body = payload.body.strip()
    comment = Comment(card_id=card_id, author_id=user.id, body=body)
    db.add(comment)
    db.flush()

    handles = {m.lower() for m in MENTION_RE.findall(body)}
    mentioned_users: list[User] = []
    if handles:
        members = db.scalars(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == board.workspace_id)
        ).all()
        for member in members:
            candidate = member.user
            name_key = candidate.name.lower().replace(" ", "")
            email_key = candidate.email.split("@")[0].lower()
            if candidate.name.lower() in handles or name_key in handles or email_key in handles:
                if candidate.id == user.id:
                    continue
                mentioned_users.append(candidate)
                db.add(CommentMention(comment_id=comment.id, user_id=candidate.id))

    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        card_id=card.id,
        actor=user,
        action="comment.created",
        summary=f'{user.name} commented on "{card.title}"',
    )
    for mentioned in mentioned_users:
        create_notification(
            db,
            user_id=mentioned.id,
            type="mention",
            title=f"{user.name} mentioned you",
            body=body[:180],
            link=f"/boards/{board.id}?card={card.id}",
            meta={"card_id": str(card.id), "comment_id": str(comment.id)},
        )

    db.commit()
    comment = db.scalar(
        select(Comment)
        .options(selectinload(Comment.author), selectinload(Comment.mentions))
        .where(Comment.id == comment.id)
    )
    public = _comment_public(comment)
    await publish_board_event(
        board.id,
        "comment.created",
        {"card_id": str(card.id), "comment": public.model_dump(mode="json")},
    )
    return public


async def delete_comment(db: Session, user: User, comment_id: UUID) -> None:
    comment = db.scalar(
        select(Comment)
        .options(selectinload(Comment.card).selectinload(Card.board_list))
        .where(Comment.id == comment_id)
    )
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    board_id = comment.card.board_list.board_id
    board = require_board(db, board_id, user, WorkspaceRole.MEMBER)
    if comment.author_id != user.id:
        require_board(db, board_id, user, WorkspaceRole.ADMIN)
    card_id = comment.card_id
    db.delete(comment)
    db.commit()
    await publish_board_event(
        board.id,
        "comment.deleted",
        {"card_id": str(card_id), "comment_id": str(comment_id)},
    )
