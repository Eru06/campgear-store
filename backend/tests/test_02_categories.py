"""Smoke tests: category endpoints."""

import uuid


def test_list_categories(client):
    """Public endpoint — list all seeded categories."""
    r = client.get("/categories")
    assert r.status_code == 200
    cats = r.json()["data"]
    assert isinstance(cats, list)
    assert len(cats) >= 6
    slugs = {c["slug"] for c in cats}
    assert "tents" in slugs
    assert "cooking" in slugs


def test_get_category_by_slug(client):
    """Get a single category by slug."""
    r = client.get("/categories/tents")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "Tents"
    assert data["slug"] == "tents"


def test_get_category_not_found(client):
    r = client.get("/categories/nonexistent-slug")
    assert r.status_code == 404


def test_create_category_as_admin(client, admin_headers):
    """Admin can create a new category."""
    slug = f"test-cat-{uuid.uuid4().hex[:6]}"
    r = client.post("/categories", headers=admin_headers, json={
        "name": f"Test Category {slug}",
        "slug": slug,
        "description": "Smoke test category",
    })
    assert r.status_code == 201
    assert r.json()["data"]["slug"] == slug


def test_create_category_as_customer_forbidden(client, customer_headers):
    """Customer cannot create a category."""
    slug = f"nope-{uuid.uuid4().hex[:6]}"
    r = client.post("/categories", headers=customer_headers, json={
        "name": f"Nope {slug}",
        "slug": slug,
    })
    assert r.status_code == 403


def test_update_category_as_admin(client, admin_headers):
    """Admin can update a category."""
    # Create one first
    slug = f"upd-{uuid.uuid4().hex[:6]}"
    r = client.post("/categories", headers=admin_headers, json={
        "name": f"Updatable {slug}",
        "slug": slug,
    })
    cat_id = r.json()["data"]["id"]

    # Update
    r2 = client.put(f"/categories/{cat_id}", headers=admin_headers, json={
        "description": "Updated description",
    })
    assert r2.status_code == 200
    assert r2.json()["data"]["description"] == "Updated description"


def test_delete_category_as_admin(client, admin_headers):
    """Admin can delete a category."""
    slug = f"del-{uuid.uuid4().hex[:6]}"
    r = client.post("/categories", headers=admin_headers, json={
        "name": f"Deletable {slug}",
        "slug": slug,
    })
    cat_id = r.json()["data"]["id"]

    r2 = client.delete(f"/categories/{cat_id}", headers=admin_headers)
    assert r2.status_code == 200

    # Verify gone
    r3 = client.get(f"/categories/{slug}")
    assert r3.status_code == 404
