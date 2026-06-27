"""Tests for /v1/auth/login, /me, /logout, and the auth dependency."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth import create_session_token
from app.config import get_settings


def test_login_with_correct_password_returns_jwt(
    client: TestClient, admin_password: str
) -> None:
    response = client.post("/v1/auth/login", json={"password": admin_password})
    assert response.status_code == 200
    body = response.json()
    assert body["session_token"].count(".") == 2
    assert "expires_at" in body


def test_login_with_wrong_password_returns_401(
    client: TestClient, admin_password: str
) -> None:
    response = client.post("/v1/auth/login", json={"password": "definitely-not-it"})
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "invalid_password"


def test_login_with_empty_password_returns_422(client: TestClient) -> None:
    response = client.post("/v1/auth/login", json={"password": ""})
    assert response.status_code == 422


def test_me_returns_authenticated_with_valid_jwt(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["operator"] == "operator"


def test_me_returns_401_without_jwt(client: TestClient) -> None:
    response = client.get("/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_me_returns_401_with_garbage_jwt(client: TestClient) -> None:
    response = client.get("/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_logout_returns_204_with_valid_jwt(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 204


def test_logout_returns_401_without_jwt(client: TestClient) -> None:
    response = client.post("/v1/auth/logout")
    assert response.status_code == 401


def test_jwt_with_different_secret_is_rejected(client: TestClient) -> None:
    """A token signed with a different secret must be rejected."""
    token, _ = create_session_token("operator")
    # Mutate the cached Settings.jwt_secret to something different.
    settings = get_settings()
    original = settings.jwt_secret
    object.__setattr__(settings, "jwt_secret", "different-secret-but-also-32-chars-long-aaaa")
    try:
        response = client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
    finally:
        object.__setattr__(settings, "jwt_secret", original)