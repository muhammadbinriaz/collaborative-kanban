from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.board import BoardPublic, BoardUpdate, LabelCreate, LabelPublic
from app.schemas.card import BoardDetail
from app.schemas.list import ListCreate, ListPublic
from app.services import board as board_service
from app.services import card as card_service

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/{board_id}", response_model=BoardDetail)
def get_board(board_id: UUID, db: DbSession, current_user: CurrentUser) -> BoardDetail:
    return board_service.get_board(db, current_user, board_id)


@router.put("/{board_id}", response_model=BoardPublic)
def update_board(
    board_id: UUID, payload: BoardUpdate, db: DbSession, current_user: CurrentUser
) -> BoardPublic:
    return board_service.update_board(db, current_user, board_id, payload)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    board_service.delete_board(db, current_user, board_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{board_id}/lists", response_model=ListPublic, status_code=201)
async def create_list(
    board_id: UUID, payload: ListCreate, db: DbSession, current_user: CurrentUser
) -> ListPublic:
    return await card_service.create_list(db, current_user, board_id, payload)


@router.post("/{board_id}/labels", response_model=LabelPublic, status_code=201)
def create_label(
    board_id: UUID, payload: LabelCreate, db: DbSession, current_user: CurrentUser
) -> LabelPublic:
    return board_service.create_label(db, current_user, board_id, payload)
