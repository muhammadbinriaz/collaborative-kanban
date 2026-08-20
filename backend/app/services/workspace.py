import re
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.workspace import ROLE_RANK, Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import (
    MemberPublic,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspacePublic,
    WorkspaceUpdate,
)


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "workspace"
    return f"{base}-{uuid4().hex[:8]}"


def _to_public(workspace: Workspace, role: WorkspaceRole) -> WorkspacePublic:
    data = WorkspacePublic.model_validate(workspace)
    data.role = role
    return data


def _member_public(member: WorkspaceMember) -> MemberPublic:
    return MemberPublic(
        id=member.id,
        user_id=member.user_id,
        role=WorkspaceRole(member.role),
        name=member.user.name,
        email=member.user.email,
    )


def get_membership(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
    return db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )


def require_workspace(
    db: Session,
    workspace_id: UUID,
    user: User,
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
) -> tuple[Workspace, WorkspaceMember]:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    membership = get_membership(db, workspace_id, user.id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this workspace")

    role = WorkspaceRole(membership.role)
    if ROLE_RANK[role] < ROLE_RANK[min_role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace permissions")
    return workspace, membership


def list_workspaces(db: Session, user: User) -> list[WorkspacePublic]:
    rows = db.scalars(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(WorkspaceMember.user_id == user.id)
    ).all()
    return [_to_public(row.workspace, WorkspaceRole(row.role)) for row in rows]


def create_workspace(db: Session, user: User, payload: WorkspaceCreate) -> WorkspacePublic:
    workspace = Workspace(name=payload.name.strip(), slug=_slugify(payload.name), owner_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER.value,
        )
    )
    db.commit()
    db.refresh(workspace)
    return _to_public(workspace, WorkspaceRole.OWNER)


def get_workspace(db: Session, user: User, workspace_id: UUID) -> WorkspaceDetail:
    workspace, membership = require_workspace(db, workspace_id, user)
    workspace = db.scalar(
        select(Workspace)
        .options(selectinload(Workspace.members).selectinload(WorkspaceMember.user))
        .where(Workspace.id == workspace.id)
    )
    return WorkspaceDetail(
        **_to_public(workspace, WorkspaceRole(membership.role)).model_dump(),
        members=[_member_public(m) for m in workspace.members],
    )


def update_workspace(
    db: Session, user: User, workspace_id: UUID, payload: WorkspaceUpdate
) -> WorkspacePublic:
    workspace, membership = require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    if payload.name is not None:
        workspace.name = payload.name.strip()
    db.commit()
    db.refresh(workspace)
    return _to_public(workspace, WorkspaceRole(membership.role))


def delete_workspace(db: Session, user: User, workspace_id: UUID) -> None:
    workspace, _ = require_workspace(db, workspace_id, user, WorkspaceRole.OWNER)
    db.delete(workspace)
    db.commit()
