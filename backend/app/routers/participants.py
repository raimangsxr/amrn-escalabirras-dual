"""Routes for participant creation and crate adjustments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_db
from app.errors import ApiError
from app.schemas import CratesAdjustResponse, ParticipantCreate, ParticipantRead
from app.security import get_current_session

router = APIRouter(prefix="/v1/participants", tags=["participants"])


@router.post(
    "",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        422: {"description": "Invalid name (empty or longer than 20 chars)."},
    },
)
def create_participant(
    payload: ParticipantCreate,
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> ParticipantRead:
    name = payload.name.strip()
    if not name or len(name) > 20:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_name",
            detail="name must be 1-20 characters after trimming",
        )
    participant = crud.create_participant(db, name=name)
    return ParticipantRead.model_validate(participant)


@router.get(
    "/{participant_id}",
    response_model=ParticipantRead,
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        404: {"description": "Participant not found."},
    },
)
def get_participant(
    participant_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> ParticipantRead:
    try:
        participant = crud.get_participant(db, participant_id)
    except crud.ParticipantNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="participant_not_found",
            detail=str(exc),
        ) from exc
    return ParticipantRead.model_validate(participant)


@router.post(
    "/{participant_id}/crates/increment",
    response_model=CratesAdjustResponse,
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        404: {"description": "Participant not found."},
    },
)
def increment_crates(
    participant_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> CratesAdjustResponse:
    try:
        participant, is_new_record = crud.adjust_crates(db, participant_id, delta=1)
    except crud.ParticipantNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="participant_not_found",
            detail=str(exc),
        ) from exc
    return CratesAdjustResponse(
        participant=ParticipantRead.model_validate(participant),
        is_new_record=is_new_record,
    )


@router.post(
    "/{participant_id}/crates/decrement",
    response_model=CratesAdjustResponse,
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        404: {"description": "Participant not found."},
        409: {"description": "Decrement would drive crates below zero."},
    },
)
def decrement_crates(
    participant_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> CratesAdjustResponse:
    try:
        participant, _ = crud.adjust_crates(db, participant_id, delta=-1)
    except crud.ParticipantNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="participant_not_found",
            detail=str(exc),
        ) from exc
    except crud.CratesUnderflowError as exc:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="crates_underflow",
            detail=str(exc),
        ) from exc
    return CratesAdjustResponse(
        participant=ParticipantRead.model_validate(participant),
        is_new_record=False,
    )