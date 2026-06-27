"""Tests for the top-N leaderboard endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create(client: TestClient, headers: dict[str, str], name: str) -> dict:
    response = client.post("/v1/participants", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()


def _bump(client: TestClient, headers: dict[str, str], participant_id: int, times: int) -> None:
    for _ in range(times):
        r = client.post(
            f"/v1/participants/{participant_id}/crates/increment", headers=headers
        )
        assert r.status_code == 200


def test_leaderboard_orders_by_crates_descending(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    a = _create(client, auth_headers, "Ana")
    b = _create(client, auth_headers, "Bea")
    c = _create(client, auth_headers, "Cris")
    _bump(client, auth_headers, a["id"], 5)
    _bump(client, auth_headers, b["id"], 2)
    _bump(client, auth_headers, c["id"], 4)
    response = client.get("/v1/leaderboard/top?limit=3", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert [p["name"] for p in body] == ["Ana", "Cris", "Bea"]
    assert [p["crates"] for p in body] == [5, 4, 2]


def test_leaderboard_empty_returns_empty_list(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/leaderboard/top?limit=3", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_leaderboard_breaks_ties_by_created_at_ascending(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """When two participants tie on crates, the older one wins."""
    a = _create(client, auth_headers, "Ana")
    b = _create(client, auth_headers, "Bea")
    c = _create(client, auth_headers, "Cris")
    _bump(client, auth_headers, a["id"], 3)
    _bump(client, auth_headers, b["id"], 3)
    _bump(client, auth_headers, c["id"], 3)
    response = client.get("/v1/leaderboard/top?limit=3", headers=auth_headers)
    body = response.json()
    assert [p["name"] for p in body] == ["Ana", "Bea", "Cris"]


def test_leaderboard_clamps_limit_to_max(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/leaderboard/top?limit=500", headers=auth_headers)
    assert response.status_code == 422


def test_leaderboard_rejects_zero_limit(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/leaderboard/top?limit=0", headers=auth_headers)
    assert response.status_code == 422


def test_leaderboard_default_limit_is_three(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for name in ["A", "B", "C", "D", "E"]:
        _create(client, auth_headers, name)
    response = client.get("/v1/leaderboard/top", headers=auth_headers)
    body = response.json()
    assert len(body) == 3