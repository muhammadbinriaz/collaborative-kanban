from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.board import Board
from app.models.card import Card, Label
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.auth import UserPublic
from app.schemas.board import LabelPublic
from app.schemas.card import CardCreate, CardMove, CardPublic, CardUpdate
from app.schemas.list import ListCreate, ListPublic, ListUpdate
from app.services.activity import log_activity, publish_board_event
from app.services.board import require_board
from app.services.position import next_position


def _is_done_list(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("done", "complete", "closed", "finished"))


def _card_to_public(card: Card) -> CardPublic:
    return CardPublic(
        id=card.id,
        list_id=card.list_id,
        title=card.title,
        description=card.description,
        position=card.position,
        due_date=card.due_date,
        assignee_id=card.assignee_id,
        estimate_points=card.estimate_points,
        sprint_id=card.sprint_id,
        completed_at=card.completed_at,
        assignee=UserPublic.model_validate(card.assignee) if card.assignee else None,
        labels=[LabelPublic.model_validate(label) for label in card.labels],
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def _load_card(db: Session, card_id: UUID) -> Card | None:
    return db.scalar(
        select(Card)
        .options(selectinload(Card.assignee), selectinload(Card.labels), selectinload(Card.board_list))
        .where(Card.id == card_id)
    )


def require_list(
    db: Session,
    list_id: UUID,
    user: User,
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
) -> BoardList:
    board_list = db.get(BoardList, list_id)
    if board_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    require_board(db, board_list.board_id, user, min_role)
    return board_list


async def create_list(db: Session, user: User, board_id: UUID, payload: ListCreate) -> ListPublic:
    board = require_board(db, board_id, user, WorkspaceRole.MEMBER)
    board_list = BoardList(
        board_id=board_id,
        name=payload.name.strip(),
        position=payload.position if payload.position is not None else next_position(db, BoardList, "board_id", board_id),
    )
    db.add(board_list)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        actor=user,
        action="list.created",
        summary=f'{user.name} created list "{board_list.name}"',
    )
    db.commit()
    db.refresh(board_list)
    public = ListPublic.model_validate(board_list)
    await publish_board_event(board.id, "list.created", public.model_dump(mode="json"))
    return public


def update_list(db: Session, user: User, list_id: UUID, payload: ListUpdate) -> ListPublic:
    board_list = require_list(db, list_id, user, WorkspaceRole.MEMBER)
    if payload.name is not None:
        board_list.name = payload.name.strip()
    if payload.position is not None:
        board_list.position = payload.position
    db.commit()
    db.refresh(board_list)
    return ListPublic.model_validate(board_list)


def delete_list(db: Session, user: User, list_id: UUID) -> None:
    board_list = require_list(db, list_id, user, WorkspaceRole.MEMBER)
    db.delete(board_list)
    db.commit()


def _apply_labels(db: Session, card: Card, board_id: UUID, label_ids: list[UUID]) -> None:
    if not label_ids:
        card.labels = []
        return
    labels = db.scalars(select(Label).where(Label.id.in_(label_ids), Label.board_id == board_id)).all()
    if len(labels) != len(set(label_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more labels are invalid")
    card.labels = labels


async def create_card(db: Session, user: User, list_id: UUID, payload: CardCreate) -> CardPublic:
    board_list = require_list(db, list_id, user, WorkspaceRole.MEMBER)
    board = db.get(Board, board_list.board_id)
    card = Card(
        list_id=list_id,
        title=payload.title.strip(),
        description=payload.description,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
        estimate_points=payload.estimate_points,
        sprint_id=payload.sprint_id,
        position=payload.position if payload.position is not None else next_position(db, Card, "list_id", list_id),
    )
    db.add(card)
    db.flush()
    if payload.label_ids:
        _apply_labels(db, card, board_list.board_id, payload.label_ids)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        card_id=card.id,
        actor=user,
        action="card.created",
        summary=f'{user.name} created "{card.title}"',
    )
    db.commit()
    public = _card_to_public(_load_card(db, card.id))
    await publish_board_event(board.id, "card.created", public.model_dump(mode="json"))
    return public


def get_card(db: Session, user: User, card_id: UUID) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    require_board(db, card.board_list.board_id, user)
    return _card_to_public(card)


async def update_card(db: Session, user: User, card_id: UUID, payload: CardUpdate) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        card.title = data["title"].strip()
    if "description" in data:
        card.description = data["description"]
    if "due_date" in data:
        card.due_date = data["due_date"]
    if "assignee_id" in data:
        card.assignee_id = data["assignee_id"]
    if "estimate_points" in data:
        card.estimate_points = data["estimate_points"]
    if "sprint_id" in data:
        card.sprint_id = data["sprint_id"]
    if "label_ids" in data and data["label_ids"] is not None:
        _apply_labels(db, card, card.board_list.board_id, data["label_ids"])
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        card_id=card.id,
        actor=user,
        action="card.updated",
        summary=f'{user.name} updated "{card.title}"',
    )
    db.commit()
    public = _card_to_public(_load_card(db, card.id))
    await publish_board_event(board.id, "card.updated", public.model_dump(mode="json"))
    return public


async def delete_card(db: Session, user: User, card_id: UUID) -> None:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)
    title = card.title
    list_id = card.list_id
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        card_id=card.id,
        actor=user,
        action="card.deleted",
        summary=f'{user.name} deleted "{title}"',
    )
    db.delete(card)
    db.commit()
    await publish_board_event(
        board.id, "card.deleted", {"id": str(card_id), "list_id": str(list_id)}
    )


async def move_card(db: Session, user: User, card_id: UUID, payload: CardMove) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board = require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)

    target_list = db.get(BoardList, payload.list_id)
    if target_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target list not found")
    if target_list.board_id != board.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move card to another board")

    card.list_id = payload.list_id
    card.position = payload.position
    if _is_done_list(target_list.name):
        card.completed_at = card.completed_at or datetime.now(UTC)
    else:
        card.completed_at = None
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        card_id=card.id,
        actor=user,
        action="card.moved",
        summary=f'{user.name} moved "{card.title}"',
        meta={"list_id": str(payload.list_id), "position": payload.position},
    )
    db.commit()
    public = _card_to_public(_load_card(db, card.id))
    await publish_board_event(board.id, "card.moved", public.model_dump(mode="json"))
    return public
