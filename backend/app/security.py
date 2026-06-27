"""FastAPI security dependencies."""

from __future__ import annotations

import jwt
from fastapi import Depends, Request, status

from app.auth import decode_session_token
from app.errors import ApiError


def get_current_session(request: Request) -> dict:
    """Read ``Authorization: Bearer <jwt>`` and return the decoded claims.

    Raises ``401 unauthorized`` when the header is missing, malformed,
    or the JWT fails any validation step.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            detail="missing or malformed Authorization header",
        )
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        claims = decode_session_token(token)
    except jwt.ExpiredSignatureError:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            detail="token expired",
        ) from None
    except jwt.InvalidTokenError:
        # Do not leak PyJWT's internal message ("Not enough segments",
        # "Signature verification failed", etc.) to the client.
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            detail="invalid token",
        ) from None
    return claims


CurrentSession = Depends(get_current_session)