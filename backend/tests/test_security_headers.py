"""Tests for the production security headers middleware."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_x_content_type_options_present(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_referrer_policy_present(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.headers.get("referrer-policy") == "no-referrer"


def test_hsts_absent_over_http(client: TestClient) -> None:
    response = client.get("/healthz")
    assert "strict-transport-security" not in response.headers


def test_hsts_present_over_https(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Forwarded-Proto": "https"})
    assert (
        response.headers.get("strict-transport-security")
        == "max-age=63072000; includeSubDomains"
    )


def test_hsts_present_with_https_in_forwarded_proto_chain(
    client: TestClient,
) -> None:
    response = client.get("/healthz", headers={"X-Forwarded-Proto": "https, http"})
    assert "strict-transport-security" in response.headers


def test_headers_present_on_error_responses(client: TestClient) -> None:
    response = client.get("/v1/participants/1")
    assert response.status_code == 401
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("referrer-policy") == "no-referrer"