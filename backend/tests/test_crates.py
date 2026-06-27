"""Tests for crate increment/decrement and new-record detection."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create(client: TestClient, headers: dict[str, str], name: str) -> dict:
    response = client.post("/v1/participants", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_increment_first_run_is_a_new_record(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    p = _create(client, auth_headers, "Ana")
    response = client.post(
        f"/v1/participants/{p['id']}/crates/increment", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["participant"]["crates"] == 1
    assert body["is_new_record"] is True


def test_increment_second_run_does_not_surpass(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    p1 = _create(client, auth_headers, "Ana")
    p2 = _create(client, auth_headers, "Bea")
    client.post(f"/v1/participants/{p1['id']}/crates/increment", headers=auth_headers)
    client.post(f"/v1/participants/{p1['id']}/crates/increment", headers=auth_headers)
    response = client.post(
        f"/v1/participants/{p2['id']}/crates/increment", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["participant"]["crates"] == 1
    assert body["is_new_record"] is False


def test_increment_overtaking_returns_new_record(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    p1 = _create(client, auth_headers, "Ana")
    p2 = _create(client, auth_headers, "Bea")
    client.post(f"/v1/participants/{p1['id']}/crates/increment", headers=auth_headers)
    client.post(f"/v1/participants/{p1['id']}/crates/increment", headers=auth_headers)
    client.post(f"/v1/participants/{p2['id']}/crates/increment", headers=auth_headers)
    client.post(f"/v1/participants/{p2['id']}/crates/increment", headers=auth_headers)
    overtaking = client.post(
        f"/v1/participants/{p2['id']}/crates/increment", headers=auth_headers
    )
    assert overtaking.status_code == 200
    assert overtaking.json()["is_new_record"] is True
    assert overtaking.json()["participant"]["crates"] == 3


def test_increment_returns_404_for_missing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants/9999/crates/increment", headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["code"] == "participant_not_found"


def test_decrement_decreases_crates(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    p = _create(client, auth_headers, "Ana")
    client.post(f"/v1/participants/{p['id']}/crates/increment", headers=auth_headers)
    client.post(f"/v1/participants/{p['id']}/crates/increment", headers=auth_headers)
    response = client.post(
        f"/v1/participants/{p['id']}/crates/decrement", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["participant"]["crates"] == 1
    assert body["is_new_record"] is False


def test_decrement_at_zero_returns_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    p = _create(client, auth_headers, "Ana")
    response = client.post(
        f"/v1/participants/{p['id']}/crates/decrement", headers=auth_headers
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "crates_underflow"
    get_after = client.get(f"/v1/participants/{p['id']}", headers=auth_headers)
    assert get_after.json()["crates"] == 0


def test_decrement_returns_404_for_missing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/participants/9999/crates/decrement", headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["code"] == "participant_not_found"