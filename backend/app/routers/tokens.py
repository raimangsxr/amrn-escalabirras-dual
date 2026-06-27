"""Routes for managing embed tokens (CRUD)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import auth
from app.deps import get_db
from app.errors import ApiError
from app.models import EmbedToken
from app.schemas import (
    CreateEmbedTokenRequest,
    EmbedTokenCreatedResponse,
    EmbedTokenListItem,
    EmbedTokenListResponse,
)
from app.security import get_current_session

router = APIRouter(prefix="/v1/tokens", tags=["tokens"])


@router.post("", response_model=EmbedTokenCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_embed_token(
    payload: CreateEmbedTokenRequest,
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> EmbedTokenCreatedResponse:
    plaintext = auth.generate_embed_token()
    token_hash = auth.hash_embed_token(plaintext)
    row = EmbedToken(name=payload.name.strip(), token_hash=token_hash)
    db.add(row)
    db.commit()
    db.refresh(row)
    return EmbedTokenCreatedResponse(
        id=row.id,
        name=row.name,
        token=plaintext,
        created_at=row.created_at,
    )


@router.get("", response_model=EmbedTokenListResponse)
def list_embed_tokens(
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> EmbedTokenListResponse:
    stmt = select(EmbedToken).order_by(EmbedToken.id.desc())
    rows = list(db.execute(stmt).scalars().all())
    return EmbedTokenListResponse(
        tokens=[EmbedTokenListItem.model_validate(r) for r in rows]
    )


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def revoke_embed_token(
    token_id: int,
    db: Session = Depends(get_db),
    _claims: dict = Depends(get_current_session),
) -> Response:
    row = db.get(EmbedToken, token_id)
    if row is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="token_not_found",
            detail=f"token {token_id} not found",
        )
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)