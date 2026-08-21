from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.whiteboard import WhiteboardCreate, WhiteboardPublic, WhiteboardSummary, WhiteboardUpdate
from app.services import whiteboard as whiteboard_service

router = APIRouter(tags=["whiteboards"])


@router.get("/workspaces/{workspace_id}/whiteboards", response_model=list[WhiteboardSummary])
def list_whiteboards(
    workspace_id: UUID, db: DbSession, current_user: CurrentUser
) -> list[WhiteboardSummary]:
    return whiteboard_service.list_whiteboards(db, current_user, workspace_id)


@router.post(
    "/workspaces/{workspace_id}/whiteboards",
    response_model=WhiteboardPublic,
    status_code=201,
)
def create_whiteboard(
    workspace_id: UUID,
    payload: WhiteboardCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> WhiteboardPublic:
    return whiteboard_service.create_whiteboard(db, current_user, workspace_id, payload)


@router.get("/whiteboards/{whiteboard_id}", response_model=WhiteboardPublic)
def get_whiteboard(
    whiteboard_id: UUID, db: DbSession, current_user: CurrentUser, response: Response
) -> WhiteboardPublic:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return whiteboard_service.get_whiteboard(db, current_user, whiteboard_id)


@router.put("/whiteboards/{whiteboard_id}", response_model=WhiteboardPublic)
def update_whiteboard(
    whiteboard_id: UUID,
    payload: WhiteboardUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> WhiteboardPublic:
    return whiteboard_service.update_whiteboard(db, current_user, whiteboard_id, payload)


@router.delete("/whiteboards/{whiteboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_whiteboard(whiteboard_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    whiteboard_service.delete_whiteboard(db, current_user, whiteboard_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
