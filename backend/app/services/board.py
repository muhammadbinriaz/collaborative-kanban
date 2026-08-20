from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.board import Board
from app.models.card import Label
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.board import BoardCreate, BoardPublic, BoardUpdate, LabelCreate, LabelPublic
from app.schemas.card import BoardDetail, CardPublic, ListWithCards
from app.schemas.auth import UserPublic
from app.services.position import next_position
from app.services.workspace import require_workspace

DEFAULT_LISTS = ("To Do", "In Progress", "Done")
DEFAULT_LABELS = (
    ("Bug", "#ef4444"),
    ("Feature", "#3b82f6"),
    ("Improvement", "#8b5cf6"),
    ("Urgent", "#f97316"),
)


def _load_board(db: Session, board_id: UUID) -> Board | None:
    from app.models.card import Card

    return db.scalar(
        select(Board)
        .options(
            selectinload(Board.labels),
            selectinload(Board.lists).selectinload(BoardList.cards).selectinload(Card.assignee),
            selectinload(Board.lists).selectinload(BoardList.cards).selectinload(Card.labels),
        )
        .where(Board.id == board_id)
    )


def require_board(
    db: Session,
    board_id: UUID,
    user: User,
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
) -> Board:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    require_workspace(db, board.workspace_id, user, min_role)
    return board


def list_boards(db: Session, user: User, workspace_id: UUID) -> list[BoardPublic]:
    require_workspace(db, workspace_id, user)
    boards = db.scalars(
        select(Board).where(Board.workspace_id == workspace_id).order_by(Board.position, Board.created_at)
    ).all()
    return [BoardPublic.model_validate(b) for b in boards]


def create_board(db: Session, user: User, workspace_id: UUID, payload: BoardCreate) -> BoardPublic:
    require_workspace(db, workspace_id, user, WorkspaceRole.MEMBER)
    board = Board(
        workspace_id=workspace_id,
        name=payload.name.strip(),
        description=payload.description,
        position=next_position(db, Board, "workspace_id", workspace_id),
    )
    db.add(board)
    db.flush()
    for index, name in enumerate(DEFAULT_LISTS):
        db.add(BoardList(board_id=board.id, name=name, position=(index + 1) * 65535.0))
    for name, color in DEFAULT_LABELS:
        db.add(Label(board_id=board.id, name=name, color=color))
    db.commit()
    db.refresh(board)
    return BoardPublic.model_validate(board)


def get_board(db: Session, user: User, board_id: UUID) -> BoardDetail:
    from app.services.card import _card_to_public

    require_board(db, board_id, user)
    board = _load_board(db, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    lists = []
    for board_list in sorted(board.lists, key=lambda item: item.position):
        cards = [
            _card_to_public(card)
            for card in sorted(board_list.cards, key=lambda item: item.position)
        ]
        lists.append(
            ListWithCards(
                id=board_list.id,
                board_id=board_list.board_id,
                name=board_list.name,
                position=board_list.position,
                created_at=board_list.created_at,
                updated_at=board_list.updated_at,
                cards=cards,
            )
        )
    return BoardDetail(
        id=board.id,
        workspace_id=board.workspace_id,
        name=board.name,
        description=board.description,
        position=board.position,
        created_at=board.created_at,
        updated_at=board.updated_at,
        lists=lists,
        labels=[LabelPublic.model_validate(label) for label in board.labels],
    )


def update_board(db: Session, user: User, board_id: UUID, payload: BoardUpdate) -> BoardPublic:
    board = require_board(db, board_id, user, WorkspaceRole.MEMBER)
    if payload.name is not None:
        board.name = payload.name.strip()
    if payload.description is not None:
        board.description = payload.description
    if payload.position is not None:
        board.position = payload.position
    db.commit()
    db.refresh(board)
    return BoardPublic.model_validate(board)


def delete_board(db: Session, user: User, board_id: UUID) -> None:
    board = require_board(db, board_id, user, WorkspaceRole.ADMIN)
    db.delete(board)
    db.commit()


def create_label(db: Session, user: User, board_id: UUID, payload: LabelCreate) -> LabelPublic:
    require_board(db, board_id, user, WorkspaceRole.MEMBER)
    label = Label(board_id=board_id, name=payload.name.strip(), color=payload.color)
    db.add(label)
    db.commit()
    db.refresh(label)
    return LabelPublic.model_validate(label)
