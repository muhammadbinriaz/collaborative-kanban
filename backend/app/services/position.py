from sqlalchemy import func, select
from sqlalchemy.orm import Session

POSITION_GAP = 65535.0


def next_position(db: Session, model, parent_field: str, parent_id) -> float:
    current_max = db.scalar(
        select(func.max(model.position)).where(getattr(model, parent_field) == parent_id)
    )
    if current_max is None:
        return POSITION_GAP
    return float(current_max) + POSITION_GAP
