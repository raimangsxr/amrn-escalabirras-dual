"""Authentication helpers: JWT sign/verify, embed-token hash/verify."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import EmbedToken

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "escalabirras"
JWT_AUDIENCE = "escalabirras-web"

EMBED_TOKEN_PREFIX = "embed_"


def create_session_token(subject: str = "operator") -> tuple[str, datetime]:
    """Return ``(token, expires_at)`` for a freshly issued session JWT."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.jwt_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_session_token(token: str) -> dict[str, Any]:
    """Decode and validate a session JWT.

    Raises ``jwt.InvalidTokenError`` on any failure (signature, expiry,
    audience, issuer, or algorithm). Signature verification is
    explicitly enabled (PyJWT 2.x default, but pinned for clarity and
    to survive option-key changes in future PyJWT versions).
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[JWT_ALGORITHM],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
            "require": ["exp", "iat", "sub", "iss", "aud"],
        },
        leeway=30,
    )


def generate_embed_token() -> str:
    """Return a fresh plaintext embed token of the form ``embed_<random>``."""
    return EMBED_TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_embed_token(plaintext: str) -> str:
    """Return the sha256 hex digest of an embed token's full string."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def verify_embed_token(plaintext: str, db: Session) -> EmbedToken | None:
    """Return the matching active EmbedToken row, or None.

    A token is "active" when ``revoked_at IS NULL``. On a successful
    match, ``last_used_at`` is updated to ``NOW()`` and the session
    is committed.
    """
    if not plaintext.startswith(EMBED_TOKEN_PREFIX):
        return None
    token_hash = hash_embed_token(plaintext)
    stmt = select(EmbedToken).where(
        EmbedToken.token_hash == token_hash,
        EmbedToken.revoked_at.is_(None),
    )
    token = db.execute(stmt).scalar_one_or_none()
    if token is None:
        return None
    token.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(token)
    return token


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))