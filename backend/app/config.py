"""Application settings loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default=(
            "postgresql+psycopg://escalabirras:escalabirras@localhost:5432/escalabirras"
        ),
        description="SQLAlchemy database URL.",
    )

    cors_origins: str = Field(
        default="http://localhost:4200",
        description="Comma-separated list of allowed CORS origins.",
    )

    admin_password: str = Field(
        default="",
        description="Operator password. Required at startup.",
    )

    jwt_secret: str = Field(
        default="",
        description="HS256 signing secret. Must be at least 32 chars.",
    )

    jwt_ttl_seconds: int = Field(
        default=86400,
        ge=60,
        description="Session JWT lifetime.",
    )

    frame_ancestors: str = Field(
        default="*",
        description="CSP frame-ancestors / X-Frame-Options value.",
    )

    api_workers: int = Field(
        default=2,
        ge=1,
        le=32,
        description="Number of uvicorn workers (API_WORKERS).",
    )

    api_log_level: str = Field(
        default="info",
        description="Uvicorn log level (API_LOG_LEVEL). Use 'warning' in production.",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_must_be_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters of high-entropy data"
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]