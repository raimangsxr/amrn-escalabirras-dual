"""Tests for the health check endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_returns_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_is_served(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_openapi_schema_includes_v1_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]
    expected = {
        "/v1/participants",
        "/v1/participants/{participant_id}",
        "/v1/participants/{participant_id}/crates/increment",
        "/v1/participants/{participant_id}/crates/decrement",
        "/v1/leaderboard/top",
        "/v1/history",
        "/healthz",
    }
    assert expected.issubset(set(paths.keys()))