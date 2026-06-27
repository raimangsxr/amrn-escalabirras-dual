"""Tests for participant creation and lookup."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_participant_returns_201_with_zero_crates(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": "Ana"}, headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ana"
    assert body["crates"] == 0
    assert isinstance(body["id"], int) and body["id"] >= 1
    assert "created_at" in body


def test_create_participant_trims_whitespace(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": "  Bea  "}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Bea"


def test_create_participant_rejects_empty_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": ""}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_name"


def test_create_participant_rejects_blank_only_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": "   "}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_name"


def test_create_participant_rejects_too_long_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": "a" * 21}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_name"


def test_get_participant_returns_existing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        "/v1/participants", json={"name": "Cris"}, headers=auth_headers
    ).json()
    response = client.get(f"/v1/participants/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == created


def test_get_participant_returns_404_for_missing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/participants/9999", headers=auth_headers)
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "participant_not_found"
    assert "detail" in body


def test_create_participant_with_exactly_20_chars_succeeds(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants", json={"name": "a" * 20}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "a" * 20