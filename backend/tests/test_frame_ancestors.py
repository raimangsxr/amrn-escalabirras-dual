"""Tests for the frame-ancestors middleware."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_csp_frame_ancestors_header_present(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.headers.get("content-security-policy", "").startswith("frame-ancestors")


def test_x_frame_options_header_present(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.headers.get("x-frame-options", "").startswith("ALLOW-FROM")


def test_headers_present_on_error_responses(client: TestClient) -> None:
    response = client.get("/v1/participants/1")
    assert response.status_code == 401
    assert response.headers.get("content-security-policy", "").startswith("frame-ancestors")
    assert response.headers.get("x-frame-options", "").startswith("ALLOW-FROM")