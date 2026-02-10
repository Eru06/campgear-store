"""Shared fixtures for smoke tests.

These tests run against a LIVE server (default http://localhost:8000).
Start the server + DB before running: docker compose up -d && uvicorn app.main:app
"""

import os

import httpx
import pytest


BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def api_url():
    return API


@pytest.fixture(scope="session")
def client():
    """Shared httpx client for the entire test session."""
    with httpx.Client(base_url=API, timeout=10.0) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    """Login as admin and return the access token."""
    r = client.post("/auth/login", json={
        "email": "admin@campgear.com",
        "password": "Admin123!",
    })
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["data"]["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def customer_token(client):
    """Login as customer and return the access token."""
    r = client.post("/auth/login", json={
        "email": "camper@example.com",
        "password": "Camper123!",
    })
    assert r.status_code == 200, f"Customer login failed: {r.text}"
    return r.json()["data"]["access_token"]


@pytest.fixture(scope="session")
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}
