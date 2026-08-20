from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.card import Card, Label
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.auth import UserPublic
from app.schemas.board import LabelPublic
from app.schemas.card import CardCreate, CardMove, CardPublic, CardUpdate
from app.schemas.list import ListCreate, ListPublic, ListUpdate
from app.services.board import require_board
from app.services.position import next_position


def _card_to_public(card: Card) -> CardPublic:
    return CardPublic(
        id=card.id,
        list_id=card.list_id,
        title=card.title,
        description=card.description,
        position=card.position,
        due_date=card.due_date,
        assignee_id=card.assignee_id,
        assignee=UserPublic.model_validate(card.assignee) if card.assignee else None,
        labels=[LabelPublic.model_validate(label) for label in card.labels],
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def _load_card(db: Session, card_id: UUID) -> Card | None:
    from sqlalchemy import select

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


def create_list(db: Session, user: User, board_id: UUID, payload: ListCreate) -> ListPublic:
    require_board(db, board_id, user, WorkspaceRole.MEMBER)
    board_list = BoardList(
        board_id=board_id,
        name=payload.name.strip(),
        position=payload.position if payload.position is not None else next_position(db, BoardList, "board_id", board_id),
    )
    db.add(board_list)
    db.commit()
    db.refresh(board_list)
    return ListPublic.model_validate(board_list)


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


def create_card(db: Session, user: User, list_id: UUID, payload: CardCreate) -> CardPublic:
    board_list = require_list(db, list_id, user, WorkspaceRole.MEMBER)
    card = Card(
        list_id=list_id,
        title=payload.title.strip(),
        description=payload.description,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
        position=payload.position if payload.position is not None else next_position(db, Card, "list_id", list_id),
    )
    db.add(card)
    db.flush()
    if payload.label_ids:
        _apply_labels(db, card, board_list.board_id, payload.label_ids)
    db.commit()
    return _card_to_public(_load_card(db, card.id))


def get_card(db: Session, user: User, card_id: UUID) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    require_board(db, card.board_list.board_id, user)
    return _card_to_public(card)


def update_card(db: Session, user: User, card_id: UUID, payload: CardUpdate) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    require_board(db, card.board_list.board_id, user, WorkspaceRole.MEMBER)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        card.title = data["title"].strip()
    if "description" in data:
        card.description = data["description"]
    if "due_date" in data:
        card.due_date = data["due_date"]
    if "assignee_id" in data:
        card.assignee_id = data["assignee_id"]
    if "label_ids" in data and data["label_ids"] is not None:
        _apply_labels(db, card, card.board_list.board_id, data["label_ids"])
    db.commit()
    return _card_to_public(_load_card(db, card.id))


def delete_card(db: Session, user: User, card_id: UUID) -> None:
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    board_list = db.get(BoardList, card.list_id)
    require_board(db, board_list.board_id, user, WorkspaceRole.MEMBER)
    db.delete(card)
    db.commit()


def move_card(db: Session, user: User, card_id: UUID, payload: CardMove) -> CardPublic:
    card = _load_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    source_board_id = card.board_list.board_id
    require_board(db, source_board_id, user, WorkspaceRole.MEMBER)

    target_list = db.get(BoardList, payload.list_id)
    if target_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target list not found")
    if target_list.board_id != source_board_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move card to another board")

    card.list_id = payload.list_id
    card.position = payload.position
    db.commit()
    return _card_to_public(_load_card(db, card.id))
