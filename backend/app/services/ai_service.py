from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai import prompts
from app.ai.embeddings import cosine, embed_texts
from app.ai.groq_client import GroqError, chat_json, groq_configured
from app.core.config import settings
from app.models.ai import AiJob, CardEmbedding
from app.models.board import Board
from app.models.card import Card
from app.models.collaboration import Activity
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.ai import AiJobPublic, AiStatus
from app.services.board import require_board
from app.services.sprint import board_analytics


def ai_status() -> AiStatus:
    return AiStatus(
        groq_configured=groq_configured(),
        model=settings.GROQ_MODEL,
        embeddings="huggingface" if settings.HF_API_TOKEN else "local-hash",
    )


def _card_payload(card: Card) -> dict:
    return {
        "id": str(card.id),
        "title": card.title,
        "description": (card.description or "")[:300],
        "list": card.board_list.name if card.board_list else None,
        "due_date": card.due_date.isoformat() if card.due_date else None,
        "assignee": card.assignee.name if card.assignee else None,
        "estimate_points": card.estimate_points,
        "completed_at": card.completed_at.isoformat() if card.completed_at else None,
    }


def _load_board_cards(db: Session, board_id: UUID) -> list[Card]:
    lists = db.scalars(
        select(BoardList)
        .options(selectinload(BoardList.cards).selectinload(Card.assignee))
        .where(BoardList.board_id == board_id)
    ).all()
    return [card for board_list in lists for card in board_list.cards]


def _analytics_for_board(db: Session, board_id: UUID):
    board = db.get(Board, board_id)
    member = db.scalar(select(WorkspaceMember).where(WorkspaceMember.workspace_id == board.workspace_id))
    user = db.get(User, member.user_id)
    return board_analytics(db, user, board_id)


def create_job(db: Session, *, board_id: UUID, user: User, job_type: str) -> AiJob:
    require_board(db, board_id, user, WorkspaceRole.MEMBER)
    if job_type != "similar" and not groq_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY is not configured",
        )
    job = AiJob(board_id=board_id, user_id=user.id, job_type=job_type, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, user: User, job_id: UUID) -> AiJobPublic:
    job = db.get(AiJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    require_board(db, job.board_id, user)
    return AiJobPublic.model_validate(job)


async def run_job(
    db: Session,
    job_id: UUID,
    *,
    card_id: UUID | None = None,
    capacity_points: float | None = None,
) -> AiJob:
    job = db.get(AiJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    job.status = "running"
    db.commit()
    try:
        result = await _execute(
            db,
            job.job_type,
            job.board_id,
            card_id=card_id,
            capacity_points=capacity_points,
        )
        job.result = result
        job.status = "completed"
        job.error = None
        job.finished_at = datetime.now(UTC)
    except (GroqError, ValueError) as exc:
        job.status = "failed"
        job.error = str(exc)
        job.finished_at = datetime.now(UTC)
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = str(exc)
        job.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return job


async def _execute(
    db: Session,
    job_type: str,
    board_id: UUID,
    *,
    card_id: UUID | None,
    capacity_points: float | None,
) -> dict:
    cards = _load_board_cards(db, board_id)
    open_cards = [c for c in cards if c.completed_at is None]
    payload_cards = [_card_payload(c) for c in open_cards]
    analytics = _analytics_for_board(db, board_id)

    if job_type == "prioritize":
        return await chat_json(system=prompts.SYSTEM_JSON, user=prompts.prioritize_prompt(payload_cards))

    if job_type == "standup":
        since = datetime.now(UTC) - timedelta(days=1)
        activities = db.scalars(
            select(Activity)
            .where(Activity.board_id == board_id, Activity.created_at >= since)
            .order_by(Activity.created_at.desc())
            .limit(40)
        ).all()
        activity_payload = [
            {"summary": a.summary, "action": a.action, "at": a.created_at.isoformat()} for a in activities
        ]
        return await chat_json(
            system=prompts.SYSTEM_JSON,
            user=prompts.standup_prompt(activity_payload, payload_cards),
        )

    if job_type == "risk":
        bottlenecks = [b.model_dump(mode="json") for b in analytics.bottlenecks]
        return await chat_json(
            system=prompts.SYSTEM_JSON,
            user=prompts.risk_prompt(payload_cards, bottlenecks),
        )

    if job_type == "workload":
        workload = [w.model_dump(mode="json") for w in analytics.workload]
        return await chat_json(
            system=prompts.SYSTEM_JSON,
            user=prompts.workload_prompt(workload, payload_cards),
        )

    if job_type == "sprint-plan":
        velocity = [v.model_dump(mode="json") for v in analytics.velocity]
        capacity = capacity_points
        if capacity is None:
            if analytics.velocity:
                capacity = sum(v.completed_points for v in analytics.velocity) / len(analytics.velocity)
            else:
                capacity = 20.0
        return await chat_json(
            system=prompts.SYSTEM_JSON,
            user=prompts.sprint_plan_prompt(payload_cards, velocity, float(capacity)),
        )

    if job_type == "similar":
        if card_id is None:
            raise ValueError("card_id is required for similar search")
        return await similar_cards(db, board_id, card_id)

    if job_type == "predict":
        velocity = [v.model_dump(mode="json") for v in analytics.velocity]
        return await chat_json(
            system=prompts.SYSTEM_JSON,
            user=prompts.predict_prompt(payload_cards, velocity),
        )

    raise ValueError(f"Unknown job type: {job_type}")


async def similar_cards(db: Session, board_id: UUID, card_id: UUID) -> dict:
    cards = _load_board_cards(db, board_id)
    target = next((c for c in cards if c.id == card_id), None)
    if target is None:
        raise ValueError("Card not found on board")

    await refresh_embeddings(db, cards)
    target_emb = db.get(CardEmbedding, card_id)
    if target_emb is None:
        raise ValueError("Could not embed target card")

    scored: list[tuple[Card, float]] = []
    for card in cards:
        if card.id == card_id:
            continue
        emb = db.get(CardEmbedding, card.id)
        if emb is None:
            continue
        scored.append((card, cosine(list(target_emb.embedding), list(emb.embedding))))
    scored.sort(key=lambda item: item[1], reverse=True)

    matches = [
        {
            "card_id": str(card.id),
            "title": card.title,
            "similarity": round(score, 3),
            "reason": "Embedding similarity",
        }
        for card, score in scored[:5]
        if score >= 0.35
    ]

    if groq_configured() and len(cards) > 1:
        try:
            llm = await chat_json(
                system=prompts.SYSTEM_JSON,
                user=prompts.similar_prompt(
                    _card_payload(target),
                    [_card_payload(c) for c in cards if c.id != card_id][:40],
                ),
            )
            return {"matches": matches, "llm": llm}
        except GroqError:
            pass
    return {"matches": matches}


async def refresh_embeddings(db: Session, cards: list[Card]) -> None:
    if not cards:
        return
    texts = [f"{c.title}\n{c.description or ''}" for c in cards]
    vectors = await embed_texts(texts)
    for card, vector in zip(cards, vectors):
        row = db.get(CardEmbedding, card.id)
        if row is None:
            db.add(CardEmbedding(card_id=card.id, embedding=vector))
        else:
            row.embedding = vector
    db.commit()
