"""Smoke tests: authentication flow."""

import uuid


def test_register_new_user(client):
    """Register a unique test user."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/auth/register", json={
        "email": email,
        "password": "TestPass1",
        "full_name": "Test User",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["email"] == email
    assert data["role"] == "customer"


def test_register_duplicate_email(client):
    """Duplicate email should return 409."""
    r = client.post("/auth/register", json={
        "email": "admin@campgear.com",
        "password": "TestPass1",
        "full_name": "Dup User",
    })
    assert r.status_code == 409


def test_register_weak_password(client):
    """Weak password should return 422."""
    r = client.post("/auth/register", json={
        "email": f"weak-{uuid.uuid4().hex[:8]}@example.com",
        "password": "short",
        "full_name": "Weak User",
    })
    assert r.status_code == 422


def test_login_valid(client):
    """Login with seeded admin credentials."""
    r = client.post("/auth/login", json={
        "email": "admin@campgear.com",
        "password": "Admin123!",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    """Wrong password should return 401."""
    r = client.post("/auth/login", json={
        "email": "admin@campgear.com",
        "password": "WrongPass1",
    })
    assert r.status_code == 401


def test_login_nonexistent_email(client):
    """Non-existent email should return 401."""
    r = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "Whatever1",
    })
    assert r.status_code == 401


def test_me_with_token(client, admin_headers):
    """GET /auth/me with valid token returns user info."""
    r = client.get("/auth/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["email"] == "admin@campgear.com"
    assert data["role"] == "admin"


def test_me_without_token(client):
    """GET /auth/me without token returns 401 (no credentials)."""
    r = client.get("/auth/me")
    assert r.status_code in (401, 403)


def test_refresh_token_flow(client):
    """Login → refresh → new tokens."""
    # Login
    r = client.post("/auth/login", json={
        "email": "camper@example.com",
        "password": "Camper123!",
    })
    assert r.status_code == 200
    refresh_token = r.json()["data"]["refresh_token"]

    # Refresh
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    new_data = r2.json()["data"]
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # Old refresh token should be revoked
    r3 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r3.status_code == 401


def test_logout(client):
    """Login → logout → refresh should fail."""
    # Login
    r = client.post("/auth/login", json={
        "email": "camper@example.com",
        "password": "Camper123!",
    })
    assert r.status_code == 200
    tokens = r.json()["data"]

    # Logout
    r2 = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r2.status_code == 200

    # Refresh should fail
    r3 = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 401
