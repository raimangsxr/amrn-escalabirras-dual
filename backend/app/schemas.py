"""Pydantic DTOs for the public API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParticipantCreate(BaseModel):
    """Request body for ``POST /v1/participants``."""

    name: str = Field(min_length=1, max_length=20)


class ParticipantRead(BaseModel):
    """Response body for any endpoint returning a single participant."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    crates: int
    created_at: datetime


class CratesAdjustResponse(BaseModel):
    """Response body for increment / decrement endpoints."""

    participant: ParticipantRead
    is_new_record: bool = False


class ErrorBody(BaseModel):
    """Response body for any non-2xx response."""

    detail: str
    code: str


class HealthResponse(BaseModel):
    status: str = "ok"


# Auth DTOs


class LoginRequest(BaseModel):
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    session_token: str
    expires_at: datetime


class EmbedTokenExchangeRequest(BaseModel):
    token: str = Field(min_length=1)


class EmbedTokenExchangeResponse(BaseModel):
    session_token: str
    expires_at: datetime


class MeResponse(BaseModel):
    authenticated: bool = True
    operator: str


# Token DTOs


class CreateEmbedTokenRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class EmbedTokenCreatedResponse(BaseModel):
    id: int
    name: str
    token: str
    created_at: datetime


class EmbedTokenListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class EmbedTokenListResponse(BaseModel):
    tokens: list[EmbedTokenListItem]


# Event DTOs


class EventRead(BaseModel):
    """Response body for ``GET /v1/event`` and the success side of ``PUT /v1/event``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    subtitle: str
    updated_at: datetime


class EventUpdate(BaseModel):
    """Request body for ``PUT /v1/event``.

    Mirrors the validation in
    ``specs/contracts/persistence-postgres/contract.md``: each
    field is trimmed and must be 1 to 80 characters. Empty or
    over-long values raise the FastAPI validation error, which the
    global handler in ``app.main`` turns into ``422 invalid_event``.
    """

    title: str = Field(min_length=1, max_length=80)
    subtitle: str = Field(min_length=1, max_length=80)