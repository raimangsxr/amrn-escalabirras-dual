"""Routes for the singleton event info (title, subtitle)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.errors import ApiError
from app.models import Event
from app.schemas import EventRead, EventUpdate
from app.security import get_current_session
from fastapi import status

router = APIRouter(prefix="/v1/event", tags=["event"])


@router.get("", response_model=EventRead)
def get_event(
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> EventRead:
    """Return the singleton event row.

    Returns ``404 event_not_found`` if the row does not exist (only
    happens if migration ``0003_add_event`` was never applied or if
    the row was manually deleted). The frontend treats that as
    "no event yet" and renders an empty headline.
    """
    stmt = select(Event).where(Event.id == 1)
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="event_not_found",
            detail="event singleton not found",
        )
    return EventRead.model_validate(row)


@router.put("", response_model=EventRead)
def update_event(
    payload: EventUpdate,
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> EventRead:
    """Upsert the singleton event row.

    Replaces ``title`` and ``subtitle`` in place; ``updated_at`` is
    bumped to ``NOW()``. If the row does not exist yet (only on a
    fresh DB before any successful PUT), it is inserted with
    ``id = 1``. Two operators editing at the same time will
    silently overwrite each other; this is acceptable for v1
    (single operator).
    """
    stmt = select(Event).where(Event.id == 1).with_for_update()
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        row = Event(
            id=1,
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
        )
        db.add(row)
    else:
        row.title = payload.title.strip()
        row.subtitle = payload.subtitle.strip()
    db.commit()
    db.refresh(row)
    return EventRead.model_validate(row)
