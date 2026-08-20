from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.collaboration import WorkspaceInvite
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.collaboration import InviteAcceptResponse, InviteCreate, InvitePreview, InvitePublic
from app.schemas.workspace import MemberPublic
from app.services.activity import create_notification, log_activity
from app.services.workspace import _member_public, require_workspace


def create_invite(db: Session, user: User, workspace_id: UUID, payload: InviteCreate) -> InvitePublic:
    if payload.role == WorkspaceRole.OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite as owner")
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    invite = WorkspaceInvite(
        workspace_id=workspace_id,
        token=secrets.token_urlsafe(24),
        role=payload.role.value,
        created_by_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=payload.expires_in_hours),
    )
    db.add(invite)
    log_activity(
        db,
        workspace_id=workspace_id,
        actor=user,
        action="invite.created",
        summary=f"{user.name} created a {payload.role.value} invite link",
    )
    db.commit()
    db.refresh(invite)
    return _invite_public(invite)


def list_invites(db: Session, user: User, workspace_id: UUID) -> list[InvitePublic]:
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    rows = db.scalars(
        select(WorkspaceInvite)
        .where(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.revoked_at.is_(None),
            WorkspaceInvite.expires_at > datetime.now(UTC),
        )
        .order_by(WorkspaceInvite.created_at.desc())
    ).all()
    return [_invite_public(row) for row in rows]


def revoke_invite(db: Session, user: User, invite_id: UUID) -> None:
    invite = db.get(WorkspaceInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    require_workspace(db, invite.workspace_id, user, WorkspaceRole.ADMIN)
    invite.revoked_at = datetime.now(UTC)
    db.commit()


def preview_invite(db: Session, token: str) -> InvitePreview:
    invite = _valid_invite(db, token)
    workspace = db.get(Workspace, invite.workspace_id)
    return InvitePreview(
        workspace_id=invite.workspace_id,
        workspace_name=workspace.name if workspace else "Workspace",
        role=WorkspaceRole(invite.role),
        expires_at=invite.expires_at,
    )


def accept_invite(db: Session, user: User, token: str) -> InviteAcceptResponse:
    invite = _valid_invite(db, token)
    existing = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == invite.workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if existing:
        return InviteAcceptResponse(workspace_id=invite.workspace_id, role=WorkspaceRole(existing.role))

    member = WorkspaceMember(
        workspace_id=invite.workspace_id,
        user_id=user.id,
        role=invite.role,
    )
    db.add(member)
    log_activity(
        db,
        workspace_id=invite.workspace_id,
        actor=user,
        action="member.joined",
        summary=f"{user.name} joined via invite",
    )
    workspace = db.get(Workspace, invite.workspace_id)
    create_notification(
        db,
        user_id=invite.created_by_id,
        type="member.joined",
        title="Someone joined your workspace",
        body=f"{user.name} joined {workspace.name if workspace else 'the workspace'}",
        link=f"/workspaces/{invite.workspace_id}",
    )
    db.commit()
    return InviteAcceptResponse(workspace_id=invite.workspace_id, role=WorkspaceRole(invite.role))


def update_member_role(
    db: Session, user: User, workspace_id: UUID, member_id: UUID, role: WorkspaceRole
) -> MemberPublic:
    if role == WorkspaceRole.OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use ownership transfer instead")
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    member = db.scalar(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == workspace_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change owner role")
    member.role = role.value
    db.commit()
    db.refresh(member)
    return _member_public(member)


def remove_member(db: Session, user: User, workspace_id: UUID, member_id: UUID) -> None:
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    member = db.get(WorkspaceMember, member_id)
    if member is None or member.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove owner")
    db.delete(member)
    db.commit()


def _valid_invite(db: Session, token: str) -> WorkspaceInvite:
    invite = db.scalar(select(WorkspaceInvite).where(WorkspaceInvite.token == token))
    if invite is None or invite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    expires = invite.expires_at if invite.expires_at.tzinfo else invite.expires_at.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite expired")
    return invite


def _invite_public(invite: WorkspaceInvite) -> InvitePublic:
    data = InvitePublic.model_validate(invite)
    data.role = WorkspaceRole(invite.role)
    data.invite_url = f"{settings.FRONTEND_URL}/invite/{invite.token}"
    return data
