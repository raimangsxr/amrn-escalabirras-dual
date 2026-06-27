"""Tests for the embed-token lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post("/v1/tokens", json={"name": name}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["token"].startswith("embed_")
    return body["token"]


def test_create_token_returns_plaintext_once(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/tokens", json={"name": "dashboard"}, headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "dashboard"
    assert body["token"].startswith("embed_")
    assert isinstance(body["id"], int) and body["id"] >= 1


def test_list_tokens_does_not_expose_values(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _create(client, auth_headers, "alpha")
    _create(client, auth_headers, "beta")
    response = client.get("/v1/tokens", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    names = [t["name"] for t in body["tokens"]]
    assert names == ["beta", "alpha"]
    for t in body["tokens"]:
        assert "token" not in t
        assert "token_hash" not in t


def test_exchange_valid_token_returns_jwt(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    plaintext = _create(client, auth_headers, "dashboard")
    response = client.post("/v1/auth/embed-token", json={"token": plaintext})
    assert response.status_code == 200
    body = response.json()
    assert body["session_token"].count(".") == 2
    assert "expires_at" in body


def test_exchange_unknown_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/embed-token", json={"token": "embed_definitely-not-real"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_embed_token"


def test_exchange_wrong_prefix_returns_401(client: TestClient) -> None:
    response = client.post("/v1/auth/embed-token", json={"token": "not-an-embed-token"})
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_embed_token"


def test_exchange_updates_last_used_at(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    plaintext = _create(client, auth_headers, "tracked")
    client.post("/v1/auth/embed-token", json={"token": plaintext})
    response = client.get("/v1/tokens", headers=auth_headers)
    tokens = response.json()["tokens"]
    assert tokens[0]["last_used_at"] is not None


def test_revoked_token_cannot_be_exchanged(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    plaintext = _create(client, auth_headers, "doomed")
    list_response = client.get("/v1/tokens", headers=auth_headers)
    token_id = list_response.json()["tokens"][0]["id"]

    delete_response = client.delete(f"/v1/tokens/{token_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    response = client.post("/v1/auth/embed-token", json={"token": plaintext})
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_embed_token"


def test_revoke_unknown_token_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.delete("/v1/tokens/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "token_not_found"


def test_revoke_is_idempotent(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _create(client, auth_headers, "doomed")
    list_response = client.get("/v1/tokens", headers=auth_headers)
    token_id = list_response.json()["tokens"][0]["id"]
    assert client.delete(f"/v1/tokens/{token_id}", headers=auth_headers).status_code == 204
    assert client.delete(f"/v1/tokens/{token_id}", headers=auth_headers).status_code == 204


def test_create_token_requires_bearer(client: TestClient) -> None:
    response = client.post("/v1/tokens", json={"name": "x"})
    assert response.status_code == 401


def test_list_tokens_requires_bearer(client: TestClient) -> None:
    response = client.get("/v1/tokens")
    assert response.status_code == 401


def test_create_token_rejects_empty_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/v1/tokens", json={"name": ""}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"