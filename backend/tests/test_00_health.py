"""Smoke test: health endpoint and OpenAPI docs."""

import httpx

from tests.conftest import BASE_URL


def test_health():
    r = httpx.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_docs_accessible():
    r = httpx.get(f"{BASE_URL}/api/docs")
    assert r.status_code == 200
