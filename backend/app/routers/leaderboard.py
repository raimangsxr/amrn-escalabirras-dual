"""Routes for leaderboard and history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_db
from app.schemas import ParticipantRead
from app.security import get_current_session

router = APIRouter(prefix="/v1", tags=["leaderboard"])


@router.get(
    "/leaderboard/top",
    response_model=list[ParticipantRead],
    responses={401: {"description": "Missing or invalid Bearer token."}},
)
def leaderboard_top(
    limit: int = Query(default=3, ge=1, le=100),
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> list[ParticipantRead]:
    return [ParticipantRead.model_validate(p) for p in crud.list_top(db, limit=limit)]


@router.get(
    "/history",
    response_model=list[ParticipantRead],
    responses={401: {"description": "Missing or invalid Bearer token."}},
)
def history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> list[ParticipantRead]:
    return [
        ParticipantRead.model_validate(p) for p in crud.list_history(db, limit=limit, offset=offset)
    ]