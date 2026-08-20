from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.board import Board
from app.models.card import Card
from app.models.list import BoardList
from app.models.sprint import Sprint
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.sprint import (
    BoardAnalytics,
    BottleneckInsight,
    BurndownPoint,
    SprintCardAssign,
    SprintCreate,
    SprintPublic,
    SprintUpdate,
    VelocityPoint,
    WorkloadPoint,
)
from app.services.activity import log_activity
from app.services.board import require_board


def _sprint_stats(db: Session, sprint: Sprint) -> SprintPublic:
    cards = db.scalars(select(Card).where(Card.sprint_id == sprint.id)).all()
    total = sum(c.estimate_points or 0 for c in cards)
    completed = sum((c.estimate_points or 0) for c in cards if c.completed_at is not None)
    data = SprintPublic.model_validate(sprint)
    data.total_points = float(total)
    data.completed_points = float(completed)
    data.card_count = len(cards)
    return data


def list_sprints(db: Session, user: User, board_id: UUID) -> list[SprintPublic]:
    require_board(db, board_id, user)
    rows = db.scalars(
        select(Sprint).where(Sprint.board_id == board_id).order_by(Sprint.created_at.desc())
    ).all()
    return [_sprint_stats(db, row) for row in rows]


def create_sprint(db: Session, user: User, board_id: UUID, payload: SprintCreate) -> SprintPublic:
    board = require_board(db, board_id, user, WorkspaceRole.MEMBER)
    sprint = Sprint(
        board_id=board_id,
        name=payload.name.strip(),
        goal=payload.goal,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="planned",
    )
    db.add(sprint)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        actor=user,
        action="sprint.created",
        summary=f'{user.name} created sprint "{sprint.name}"',
    )
    db.commit()
    db.refresh(sprint)
    return _sprint_stats(db, sprint)


def update_sprint(db: Session, user: User, sprint_id: UUID, payload: SprintUpdate) -> SprintPublic:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    require_board(db, sprint.board_id, user, WorkspaceRole.MEMBER)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        sprint.name = data["name"].strip()
    if "goal" in data:
        sprint.goal = data["goal"]
    if "start_date" in data:
        sprint.start_date = data["start_date"]
    if "end_date" in data:
        sprint.end_date = data["end_date"]
    db.commit()
    db.refresh(sprint)
    return _sprint_stats(db, sprint)


def start_sprint(db: Session, user: User, sprint_id: UUID) -> SprintPublic:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    board = require_board(db, sprint.board_id, user, WorkspaceRole.MEMBER)
    active = db.scalar(
        select(Sprint).where(Sprint.board_id == board.id, Sprint.status == "active")
    )
    if active and active.id != sprint.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Another sprint is already active")
    if sprint.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint already completed")
    sprint.status = "active"
    sprint.start_date = sprint.start_date or datetime.now(UTC)
    if sprint.end_date is None:
        sprint.end_date = sprint.start_date + timedelta(days=14)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        actor=user,
        action="sprint.started",
        summary=f'{user.name} started sprint "{sprint.name}"',
    )
    db.commit()
    db.refresh(sprint)
    return _sprint_stats(db, sprint)


def complete_sprint(db: Session, user: User, sprint_id: UUID) -> SprintPublic:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    board = require_board(db, sprint.board_id, user, WorkspaceRole.MEMBER)
    if sprint.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active sprints can be completed")
    sprint.status = "completed"
    sprint.end_date = datetime.now(UTC)
    log_activity(
        db,
        workspace_id=board.workspace_id,
        board_id=board.id,
        actor=user,
        action="sprint.completed",
        summary=f'{user.name} completed sprint "{sprint.name}"',
    )
    db.commit()
    db.refresh(sprint)
    return _sprint_stats(db, sprint)


def assign_cards(db: Session, user: User, sprint_id: UUID, payload: SprintCardAssign) -> SprintPublic:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    require_board(db, sprint.board_id, user, WorkspaceRole.MEMBER)
    cards = db.scalars(select(Card).options(selectinload(Card.board_list)).where(Card.id.in_(payload.card_ids))).all()
    for card in cards:
        if card.board_list.board_id != sprint.board_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Card is not on this board")
        card.sprint_id = sprint.id
    db.commit()
    return _sprint_stats(db, sprint)


def _is_done_list(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("done", "complete", "closed", "finished"))


def board_analytics(db: Session, user: User, board_id: UUID) -> BoardAnalytics:
    board = require_board(db, board_id, user)
    sprints = db.scalars(
        select(Sprint).where(Sprint.board_id == board_id).order_by(Sprint.created_at.asc())
    ).all()
    active = next((s for s in sprints if s.status == "active"), None)

    burndown: list[BurndownPoint] = []
    if active and active.start_date and active.end_date:
        cards = db.scalars(select(Card).where(Card.sprint_id == active.id)).all()
        total = float(sum(c.estimate_points or 1 for c in cards) or 0)
        start = active.start_date if active.start_date.tzinfo else active.start_date.replace(tzinfo=UTC)
        end = active.end_date if active.end_date.tzinfo else active.end_date.replace(tzinfo=UTC)
        days = max(1, (end.date() - start.date()).days)
        today = datetime.now(UTC).date()
        for offset in range(days + 1):
            day = start.date() + timedelta(days=offset)
            ideal = total - (total * offset / days)
            actual = None
            if day <= today:
                completed = sum(
                    (c.estimate_points or 1)
                    for c in cards
                    if c.completed_at
                    and (c.completed_at if c.completed_at.tzinfo else c.completed_at.replace(tzinfo=UTC)).date()
                    <= day
                )
                actual = max(0.0, total - completed)
            burndown.append(
                BurndownPoint(
                    date=day.isoformat(),
                    ideal_remaining=round(ideal, 2),
                    actual_remaining=None if actual is None else round(actual, 2),
                )
            )

    velocity: list[VelocityPoint] = []
    for sprint in [s for s in sprints if s.status == "completed"][-8:]:
        stats = _sprint_stats(db, sprint)
        velocity.append(
            VelocityPoint(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                completed_points=stats.completed_points,
                committed_points=stats.total_points,
            )
        )

    lists = db.scalars(
        select(BoardList).options(selectinload(BoardList.cards).selectinload(Card.assignee)).where(BoardList.board_id == board_id)
    ).all()
    workload_map: dict[str | None, WorkloadPoint] = {}
    for board_list in lists:
        for card in board_list.cards:
            key = str(card.assignee_id) if card.assignee_id else None
            if key not in workload_map:
                workload_map[key] = WorkloadPoint(
                    user_id=card.assignee_id,
                    user_name=card.assignee.name if card.assignee else "Unassigned",
                    card_count=0,
                    estimate_points=0,
                )
            workload_map[key].card_count += 1
            workload_map[key].estimate_points += float(card.estimate_points or 0)

    bottlenecks: list[BottleneckInsight] = []
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(days=7)
    for board_list in lists:
        if len(board_list.cards) >= 8 and not _is_done_list(board_list.name):
            bottlenecks.append(
                BottleneckInsight(
                    type="list_congestion",
                    title=f'"{board_list.name}" is congested',
                    detail=f"{len(board_list.cards)} cards sitting in this list",
                    severity="medium",
                    meta={"list_id": str(board_list.id), "count": len(board_list.cards)},
                )
            )
        for card in board_list.cards:
            updated = card.updated_at if card.updated_at.tzinfo else card.updated_at.replace(tzinfo=UTC)
            if not _is_done_list(board_list.name) and updated < stale_cutoff:
                bottlenecks.append(
                    BottleneckInsight(
                        type="stale_card",
                        title=f'Stale: "{card.title}"',
                        detail=f'No updates for {(now - updated).days} days in "{board_list.name}"',
                        severity="low",
                        meta={"card_id": str(card.id)},
                    )
                )
            if card.due_date:
                due = card.due_date if card.due_date.tzinfo else card.due_date.replace(tzinfo=UTC)
                if due < now and not _is_done_list(board_list.name):
                    bottlenecks.append(
                        BottleneckInsight(
                            type="overdue",
                            title=f'Overdue: "{card.title}"',
                            detail=f"Due {due.date().isoformat()}",
                            severity="high",
                            meta={"card_id": str(card.id)},
                        )
                    )

    bottlenecks = sorted(bottlenecks, key=lambda b: {"high": 0, "medium": 1, "low": 2}[b.severity])[:12]

    return BoardAnalytics(
        burndown=burndown,
        velocity=velocity,
        workload=list(workload_map.values()),
        bottlenecks=bottlenecks,
        active_sprint=_sprint_stats(db, active) if active else None,
    )
