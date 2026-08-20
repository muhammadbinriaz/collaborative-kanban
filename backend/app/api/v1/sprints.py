from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.sprint import (
    BoardAnalytics,
    SprintCardAssign,
    SprintCreate,
    SprintPublic,
    SprintUpdate,
)
from app.services import sprint as sprint_service

router = APIRouter(tags=["sprints"])


@router.get("/boards/{board_id}/sprints", response_model=list[SprintPublic])
def list_sprints(board_id: UUID, db: DbSession, current_user: CurrentUser) -> list[SprintPublic]:
    return sprint_service.list_sprints(db, current_user, board_id)


@router.post("/boards/{board_id}/sprints", response_model=SprintPublic, status_code=201)
def create_sprint(
    board_id: UUID, payload: SprintCreate, db: DbSession, current_user: CurrentUser
) -> SprintPublic:
    return sprint_service.create_sprint(db, current_user, board_id, payload)


@router.put("/sprints/{sprint_id}", response_model=SprintPublic)
def update_sprint(
    sprint_id: UUID, payload: SprintUpdate, db: DbSession, current_user: CurrentUser
) -> SprintPublic:
    return sprint_service.update_sprint(db, current_user, sprint_id, payload)


@router.post("/sprints/{sprint_id}/start", response_model=SprintPublic)
def start_sprint(sprint_id: UUID, db: DbSession, current_user: CurrentUser) -> SprintPublic:
    return sprint_service.start_sprint(db, current_user, sprint_id)


@router.post("/sprints/{sprint_id}/complete", response_model=SprintPublic)
def complete_sprint(sprint_id: UUID, db: DbSession, current_user: CurrentUser) -> SprintPublic:
    return sprint_service.complete_sprint(db, current_user, sprint_id)


@router.post("/sprints/{sprint_id}/cards", response_model=SprintPublic)
def assign_cards(
    sprint_id: UUID, payload: SprintCardAssign, db: DbSession, current_user: CurrentUser
) -> SprintPublic:
    return sprint_service.assign_cards(db, current_user, sprint_id, payload)


@router.get("/boards/{board_id}/analytics", response_model=BoardAnalytics)
def board_analytics(board_id: UUID, db: DbSession, current_user: CurrentUser) -> BoardAnalytics:
    return sprint_service.board_analytics(db, current_user, board_id)
