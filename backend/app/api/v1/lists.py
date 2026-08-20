from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.card import CardPublic
from app.schemas.card import CardCreate
from app.schemas.list import ListPublic, ListUpdate
from app.services import card as card_service

router = APIRouter(tags=["lists"])


@router.put("/lists/{list_id}", response_model=ListPublic)
def update_list(
    list_id: UUID, payload: ListUpdate, db: DbSession, current_user: CurrentUser
) -> ListPublic:
    return card_service.update_list(db, current_user, list_id, payload)


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    card_service.delete_list(db, current_user, list_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/lists/{list_id}/cards", response_model=CardPublic, status_code=201)
async def create_card(
    list_id: UUID, payload: CardCreate, db: DbSession, current_user: CurrentUser
) -> CardPublic:
    return await card_service.create_card(db, current_user, list_id, payload)
