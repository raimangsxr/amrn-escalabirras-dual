"""Routes for operator authentication and embed-token redemption."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app import auth
from app.config import get_settings
from app.deps import get_db
from app.errors import ApiError
from app.schemas import (
    EmbedTokenExchangeRequest,
    EmbedTokenExchangeResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
)
from app.security import get_current_session

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    settings = get_settings()
    if not settings.admin_password or not auth.constant_time_compare(
        payload.password, settings.admin_password
    ):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_password",
            detail="invalid password",
        )
    token, expires_at = auth.create_session_token("operator")
    return LoginResponse(session_token=token, expires_at=expires_at)


@router.post("/embed-token", response_model=EmbedTokenExchangeResponse)
def exchange_embed_token(
    payload: EmbedTokenExchangeRequest, db: Session = Depends(get_db)
) -> EmbedTokenExchangeResponse:
    token_row = auth.verify_embed_token(payload.token, db)
    if token_row is None:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_embed_token",
            detail="invalid embed token",
        )
    session_token, expires_at = auth.create_session_token("operator")
    return EmbedTokenExchangeResponse(session_token=session_token, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(_claims: dict = Depends(get_current_session)) -> Response:
    """Stateless no-op for client symmetry."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
def me(claims: dict = Depends(get_current_session)) -> MeResponse:
    return MeResponse(authenticated=True, operator=str(claims.get("sub", "operator")))