"""Smoke tests: every previously-open endpoint now requires Bearer."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _open(client: TestClient, method: str, path: str, **kwargs) -> int:
    response = client.request(method, path, **kwargs)
    return response.status_code


def test_participants_require_bearer(client: TestClient) -> None:
    assert _open(client, "POST", "/v1/participants", json={"name": "x"}) == 401
    assert _open(client, "GET", "/v1/participants/1") == 401
    assert _open(client, "POST", "/v1/participants/1/crates/increment") == 401
    assert _open(client, "POST", "/v1/participants/1/crates/decrement") == 401


def test_leaderboard_requires_bearer(client: TestClient) -> None:
    assert _open(client, "GET", "/v1/leaderboard/top") == 401
    assert _open(client, "GET", "/v1/history") == 401


def test_healthz_is_open(client: TestClient) -> None:
    assert _open(client, "GET", "/healthz") == 200


def test_login_is_open(client: TestClient) -> None:
    assert _open(client, "POST", "/v1/auth/login", json={"password": "x"}) == 401
    # 401 because the password is wrong, not because auth is required.
    assert _open(client, "POST", "/v1/auth/login", json={"password": ""}) == 422


def test_embed_token_endpoint_is_open(client: TestClient) -> None:
    assert _open(client, "POST", "/v1/auth/embed-token", json={"token": "x"}) == 401
    # 401 because the token is wrong, not because auth is required.


def test_protected_endpoints_with_bearer_respond_normally(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # Without bearer: 401
    assert _open(client, "POST", "/v1/participants", json={"name": "x"}) == 401
    # With bearer: 201
    assert (
        _open(client, "POST", "/v1/participants", json={"name": "x"}, headers=auth_headers)
        == 201
    )