from __future__ import annotations

import asyncio
from uuid import UUID

from app.db.session import SessionLocal
from app.services import ai_service
from app.tasks.celery_app import celery_app


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="ai.run_job")
def run_ai_job(job_id: str, card_id: str | None = None, capacity_points: float | None = None) -> dict:
    db = SessionLocal()
    try:
        job = _run_async(
            ai_service.run_job(
                db,
                UUID(job_id),
                card_id=UUID(card_id) if card_id else None,
                capacity_points=capacity_points,
            )
        )
        return {"id": str(job.id), "status": job.status}
    finally:
        db.close()
