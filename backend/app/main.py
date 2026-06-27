"""FastAPI application entry point."""

from __future__ import annotations

from typing import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.errors import ApiError
from app.middleware.frame_ancestors import FrameAncestorsMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import auth as auth_router
from app.routers import leaderboard, participants, tokens as tokens_router
from app.schemas import ErrorBody, HealthResponse

settings = get_settings()

app = FastAPI(
    title="Escalabirras API",
    version="0.1.0",
    description="Backend for the escalabirras tournament app.",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(FrameAncestorsMiddleware, frame_ancestors=settings.frame_ancestors)


def _build_error(status_code: int, code: str, detail: str) -> JSONResponse:
    body = ErrorBody(detail=detail, code=code).model_dump()
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, Mapping) and "code" in exc.detail:
        code = str(exc.detail["code"])
        message = str(exc.detail.get("message", ""))
    else:
        code = _default_code_for_status(exc.status_code)
        message = str(exc.detail)
    return _build_error(exc.status_code, code, message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    is_participant_name = (
        request.url.path.rstrip("/").endswith("/v1/participants")
        and any(err.get("loc", ())[:2] == ("body", "name") for err in errors)
    )
    if is_participant_name:
        return _build_error(422, "invalid_name", "name must be 1-20 characters")
    return _build_error(422, "validation_error", "request validation failed")


def _default_code_for_status(status_code: int) -> str:
    return {
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        500: "internal_error",
    }.get(status_code, "http_error")


app.include_router(auth_router.router)
app.include_router(tokens_router.router)
app.include_router(participants.router)
app.include_router(leaderboard.router)


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")