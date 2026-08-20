from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.ai import AiActionRequest, AiJobPublic, AiStatus
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])

JOB_TYPES = {"prioritize", "standup", "risk", "workload", "sprint-plan", "similar", "predict"}


@router.get("/status", response_model=AiStatus)
def status_endpoint() -> AiStatus:
    return ai_service.ai_status()


@router.get("/jobs/{job_id}", response_model=AiJobPublic)
def get_job(job_id: UUID, db: DbSession, current_user: CurrentUser) -> AiJobPublic:
    return ai_service.get_job(db, current_user, job_id)


async def _enqueue_or_run(
    *,
    db: DbSession,
    background: BackgroundTasks,
    board_id: UUID,
    user,
    job_type: str,
    payload: AiActionRequest,
) -> AiJobPublic:
    if job_type not in JOB_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown AI action")
    if job_type == "similar" and payload.card_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="card_id is required")

    job = ai_service.create_job(db, board_id=board_id, user=user, job_type=job_type)

    # Prefer Celery when Redis broker is reachable; otherwise FastAPI BackgroundTasks.
    queued = False
    try:
        from app.tasks.ai_tasks import run_ai_job

        run_ai_job.delay(
            str(job.id),
            str(payload.card_id) if payload.card_id else None,
            payload.capacity_points,
        )
        queued = True
    except Exception:
        queued = False

    if not queued:
        background.add_task(
            _run_in_background,
            str(job.id),
            str(payload.card_id) if payload.card_id else None,
            payload.capacity_points,
        )

    return AiJobPublic.model_validate(job)


def _run_in_background(job_id: str, card_id: str | None, capacity_points: float | None) -> None:
    import asyncio
    from uuid import UUID as _UUID

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        asyncio.run(
            ai_service.run_job(
                db,
                _UUID(job_id),
                card_id=_UUID(card_id) if card_id else None,
                capacity_points=capacity_points,
            )
        )
    finally:
        db.close()


@router.post("/boards/{board_id}/prioritize", response_model=AiJobPublic)
async def prioritize(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="prioritize",
        payload=payload or AiActionRequest(),
    )


@router.post("/boards/{board_id}/standup", response_model=AiJobPublic)
async def standup(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="standup",
        payload=payload or AiActionRequest(),
    )


@router.post("/boards/{board_id}/risk-detection", response_model=AiJobPublic)
async def risk(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="risk",
        payload=payload or AiActionRequest(),
    )


@router.post("/boards/{board_id}/workload-balance", response_model=AiJobPublic)
async def workload(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="workload",
        payload=payload or AiActionRequest(),
    )


@router.post("/boards/{board_id}/sprint-plan", response_model=AiJobPublic)
async def sprint_plan(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="sprint-plan",
        payload=payload or AiActionRequest(),
    )


@router.post("/boards/{board_id}/similar", response_model=AiJobPublic)
async def similar(
    board_id: UUID,
    payload: AiActionRequest,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="similar",
        payload=payload,
    )


@router.post("/boards/{board_id}/predict", response_model=AiJobPublic)
async def predict(
    board_id: UUID,
    background: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    payload: AiActionRequest | None = None,
) -> AiJobPublic:
    return await _enqueue_or_run(
        db=db,
        background=background,
        board_id=board_id,
        user=current_user,
        job_type="predict",
        payload=payload or AiActionRequest(),
    )
