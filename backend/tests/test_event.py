"""Tests for the singleton event info (title, subtitle)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Event


def _seed_event(session: Session) -> Event:
    row = Event(id=1, title="Initial title", subtitle="Initial subtitle")
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_get_event_requires_bearer(client: TestClient) -> None:
    response = client.get("/v1/event")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_get_event_returns_404_when_singleton_missing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/v1/event", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "event_not_found"


def test_get_event_returns_seeded_row(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    _seed_event(db_session)
    response = client.get("/v1/event", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Initial title"
    assert body["subtitle"] == "Initial subtitle"
    assert "updated_at" in body


def test_put_event_requires_bearer(client: TestClient) -> None:
    response = client.put("/v1/event", json={"title": "a", "subtitle": "b"})
    assert response.status_code == 401


def test_put_event_creates_singleton_when_missing(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    response = client.put(
        "/v1/event",
        json={"title": "  Demo title  ", "subtitle": "Demo subtitle"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Demo title"
    assert body["subtitle"] == "Demo subtitle"

    stored = db_session.get(Event, 1)
    assert stored is not None
    assert stored.title == "Demo title"
    assert stored.subtitle == "Demo subtitle"


def test_put_event_updates_existing_row(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    _seed_event(db_session)
    response = client.put(
        "/v1/event",
        json={"title": "New title", "subtitle": "New subtitle"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["subtitle"] == "New subtitle"

    db_session.expire_all()
    stored = db_session.get(Event, 1)
    assert stored is not None
    assert stored.title == "New title"


def test_put_event_rejects_empty_title(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(
        "/v1/event",
        json={"title": "", "subtitle": "ok"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_event"


def test_put_event_rejects_empty_subtitle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(
        "/v1/event",
        json={"title": "ok", "subtitle": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_event"


def test_put_event_rejects_overlong_title(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(
        "/v1/event",
        json={"title": "x" * 81, "subtitle": "ok"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_event"


def test_put_event_accepts_max_length(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(
        "/v1/event",
        json={"title": "x" * 80, "subtitle": "y" * 80},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "ok"},
        {"subtitle": "ok"},
        {},
    ],
)
def test_put_event_rejects_missing_fields(
    client: TestClient, auth_headers: dict[str, str], payload: dict[str, str]
) -> None:
    response = client.put("/v1/event", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_event"
