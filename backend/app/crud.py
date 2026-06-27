"""Data-access functions for participants."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Participant
from app.services.records import compute_is_new_record


class CratesUnderflowError(Exception):
    """Raised when a decrement would drive ``crates`` below zero."""


class ParticipantNotFoundError(Exception):
    """Raised when ``participant_id`` does not exist."""


def create_participant(db: Session, *, name: str) -> Participant:
    participant = Participant(name=name, crates=0)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def get_participant(db: Session, participant_id: int) -> Participant:
    participant = db.get(Participant, participant_id)
    if participant is None:
        raise ParticipantNotFoundError(f"participant {participant_id} not found")
    return participant


def _other_max_crates(db: Session, participant_id: int) -> int | None:
    stmt = select(func.max(Participant.crates)).where(Participant.id != participant_id)
    return db.execute(stmt).scalar_one_or_none()


def adjust_crates(
    db: Session, participant_id: int, *, delta: int
) -> tuple[Participant, bool]:
    """Atomically adjust ``crates`` for one participant.

    Returns the refreshed participant and an ``is_new_record`` flag.

    On Postgres the row is locked with ``SELECT ... FOR UPDATE`` to
    serialize concurrent mutations; the lock is a no-op on SQLite so
    tests can run without Postgres.
    """
    if delta not in (-1, 1):
        raise ValueError(f"delta must be -1 or +1, got {delta!r}")

    stmt = select(Participant).where(Participant.id == participant_id).with_for_update()
    participant = db.execute(stmt).scalar_one_or_none()
    if participant is None:
        raise ParticipantNotFoundError(f"participant {participant_id} not found")

    new_crates = participant.crates + delta
    if new_crates < 0:
        raise CratesUnderflowError(
            f"participant {participant_id} already has crates={participant.crates}"
        )
    participant.crates = new_crates

    previous_max = _other_max_crates(db, participant_id)
    is_new_record = compute_is_new_record(new_crates, previous_max) if delta == 1 else False

    db.commit()
    db.refresh(participant)
    return participant, is_new_record


def list_top(db: Session, *, limit: int) -> list[Participant]:
    stmt = (
        select(Participant)
        .order_by(Participant.crates.desc(), Participant.created_at.asc(), Participant.id.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def list_history(db: Session, *, limit: int, offset: int) -> list[Participant]:
    stmt = (
        select(Participant)
        .order_by(Participant.created_at.desc(), Participant.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())