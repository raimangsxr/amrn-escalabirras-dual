"""Pytest fixtures.

The tests run against a per-test SQLite in-memory database so they do
not need Docker. The ``app.database.get_db`` dependency is overridden
with the per-test session; the production wiring (``SessionLocal``)
is untouched.

A pre-baked JWT secret and admin password are injected via env vars
before the Settings singleton is touched, so the
``get_current_session`` dependency can be satisfied across tests.
"""

from __future__ import annotations

import os

os.environ.setdefault("ADMIN_PASSWORD", "test-password-1234")
os.environ.setdefault("JWT_SECRET", "test-secret-please-replace-with-32-chars-min-aaaa")

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import database as db_module  # noqa: E402
from app.auth import create_session_token  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def admin_password() -> str:
    return "test-password-1234"


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture()
def db_session(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_token(client: TestClient, admin_password: str) -> str:
    """Return a valid session JWT, logging in via /v1/auth/login."""
    response = client.post("/v1/auth/login", json={"password": admin_password})
    assert response.status_code == 200, response.text
    return response.json()["session_token"]


@pytest.fixture()
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def direct_auth_token() -> str:
    """A token minted without going through /v1/auth/login."""
    token, _ = create_session_token("operator")
    return token