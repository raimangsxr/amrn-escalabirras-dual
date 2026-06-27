"""Tests for the history endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_history_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_history_returns_recent_first(client: TestClient, auth_headers: dict[str, str]) -> None:
    names = ["A", "B", "C", "D"]
    ids: list[int] = []
    for name in names:
        r = client.post("/v1/participants", json={"name": name}, headers=auth_headers)
        ids.append(r.json()["id"])
    response = client.get("/v1/history", headers=auth_headers)
    body = response.json()
    assert [p["name"] for p in body] == list(reversed(names))
    assert [p["id"] for p in body] == list(reversed(ids))


def test_history_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    for name in ["A", "B", "C", "D", "E"]:
        client.post("/v1/participants", json={"name": name}, headers=auth_headers)
    first = client.get("/v1/history?limit=2&offset=0", headers=auth_headers).json()
    second = client.get("/v1/history?limit=2&offset=2", headers=auth_headers).json()
    third = client.get("/v1/history?limit=2&offset=4", headers=auth_headers).json()
    assert len(first) == 2
    assert len(second) == 2
    assert len(third) == 1
    seen_ids = {p["id"] for p in first} | {p["id"] for p in second} | {p["id"] for p in third}
    assert len(seen_ids) == 5


def test_history_rejects_negative_offset(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/history?offset=-1", headers=auth_headers)
    assert response.status_code == 422