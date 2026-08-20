from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.models.workspace import WorkspaceRole
from app.schemas.collaboration import (
    ActivityPublic,
    CommentCreate,
    CommentPublic,
    InviteAcceptResponse,
    InviteCreate,
    InvitePreview,
    InvitePublic,
    MemberRoleUpdate,
    NotificationPublic,
)
from app.schemas.workspace import MemberPublic
from app.services import comment as comment_service
from app.services import invite as invite_service
from app.services import notification as notification_service

router = APIRouter(tags=["collaboration"])


@router.post("/workspaces/{workspace_id}/invites", response_model=InvitePublic, status_code=201)
def create_invite(
    workspace_id: UUID, payload: InviteCreate, db: DbSession, current_user: CurrentUser
) -> InvitePublic:
    return invite_service.create_invite(db, current_user, workspace_id, payload)


@router.get("/workspaces/{workspace_id}/invites", response_model=list[InvitePublic])
def list_invites(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> list[InvitePublic]:
    return invite_service.list_invites(db, current_user, workspace_id)


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(invite_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    invite_service.revoke_invite(db, current_user, invite_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/invites/{token}", response_model=InvitePreview)
def preview_invite(token: str, db: DbSession) -> InvitePreview:
    return invite_service.preview_invite(db, token)


@router.post("/invites/{token}/accept", response_model=InviteAcceptResponse)
def accept_invite(token: str, db: DbSession, current_user: CurrentUser) -> InviteAcceptResponse:
    return invite_service.accept_invite(db, current_user, token)


@router.patch(
    "/workspaces/{workspace_id}/members/{member_id}",
    response_model=MemberPublic,
)
def update_member_role(
    workspace_id: UUID,
    member_id: UUID,
    payload: MemberRoleUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> MemberPublic:
    return invite_service.update_member_role(db, current_user, workspace_id, member_id, payload.role)


@router.delete(
    "/workspaces/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    workspace_id: UUID, member_id: UUID, db: DbSession, current_user: CurrentUser
) -> Response:
    invite_service.remove_member(db, current_user, workspace_id, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/workspaces/{workspace_id}/activity", response_model=list[ActivityPublic])
def workspace_activity(
    workspace_id: UUID, db: DbSession, current_user: CurrentUser, limit: int = Query(50, ge=1, le=100)
) -> list[ActivityPublic]:
    return notification_service.list_workspace_activity(db, current_user, workspace_id, limit)


@router.get("/boards/{board_id}/activity", response_model=list[ActivityPublic])
def board_activity(
    board_id: UUID, db: DbSession, current_user: CurrentUser, limit: int = Query(50, ge=1, le=100)
) -> list[ActivityPublic]:
    return notification_service.list_board_activity(db, current_user, board_id, limit)


@router.get("/cards/{card_id}/comments", response_model=list[CommentPublic])
def list_comments(card_id: UUID, db: DbSession, current_user: CurrentUser) -> list[CommentPublic]:
    return comment_service.list_comments(db, current_user, card_id)


@router.post("/cards/{card_id}/comments", response_model=CommentPublic, status_code=201)
async def create_comment(
    card_id: UUID, payload: CommentCreate, db: DbSession, current_user: CurrentUser
) -> CommentPublic:
    return await comment_service.create_comment(db, current_user, card_id, payload)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    await comment_service.delete_comment(db, current_user, comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notifications", response_model=list[NotificationPublic])
def list_notifications(
    db: DbSession,
    current_user: CurrentUser,
    unread_only: bool = False,
) -> list[NotificationPublic]:
    return notification_service.list_notifications(db, current_user, unread_only)


@router.post("/notifications/{notification_id}/read", response_model=NotificationPublic)
def mark_read(
    notification_id: UUID, db: DbSession, current_user: CurrentUser
) -> NotificationPublic:
    return notification_service.mark_notification_read(db, current_user, notification_id)


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(db: DbSession, current_user: CurrentUser) -> Response:
    notification_service.mark_all_read(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
