from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.board import BoardCreate, BoardPublic
from app.schemas.workspace import WorkspaceCreate, WorkspaceDetail, WorkspacePublic, WorkspaceUpdate
from app.services import board as board_service
from app.services import workspace as workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspacePublic])
def list_workspaces(db: DbSession, current_user: CurrentUser) -> list[WorkspacePublic]:
    return workspace_service.list_workspaces(db, current_user)


@router.post("", response_model=WorkspacePublic, status_code=201)
def create_workspace(
    payload: WorkspaceCreate, db: DbSession, current_user: CurrentUser
) -> WorkspacePublic:
    return workspace_service.create_workspace(db, current_user, payload)


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> WorkspaceDetail:
    return workspace_service.get_workspace(db, current_user, workspace_id)


@router.put("/{workspace_id}", response_model=WorkspacePublic)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> WorkspacePublic:
    return workspace_service.update_workspace(db, current_user, workspace_id, payload)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    workspace_service.delete_workspace(db, current_user, workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{workspace_id}/boards", response_model=list[BoardPublic])
def list_boards(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> list[BoardPublic]:
    return board_service.list_boards(db, current_user, workspace_id)


@router.post("/{workspace_id}/boards", response_model=BoardPublic, status_code=201)
def create_board(
    workspace_id: UUID,
    payload: BoardCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> BoardPublic:
    return board_service.create_board(db, current_user, workspace_id, payload)
