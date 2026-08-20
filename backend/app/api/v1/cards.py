from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.card import CardMove, CardPublic, CardUpdate
from app.services import card as card_service

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/{card_id}", response_model=CardPublic)
def get_card(card_id: UUID, db: DbSession, current_user: CurrentUser) -> CardPublic:
    return card_service.get_card(db, current_user, card_id)


@router.put("/{card_id}", response_model=CardPublic)
def update_card(
    card_id: UUID, payload: CardUpdate, db: DbSession, current_user: CurrentUser
) -> CardPublic:
    return card_service.update_card(db, current_user, card_id, payload)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    card_service.delete_card(db, current_user, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{card_id}/move", response_model=CardPublic)
def move_card(card_id: UUID, payload: CardMove, db: DbSession, current_user: CurrentUser) -> CardPublic:
    return card_service.move_card(db, current_user, card_id, payload)
