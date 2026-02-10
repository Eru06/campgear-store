"""Smoke tests: product endpoints."""

import uuid


def test_list_products(client):
    """Public endpoint — list seeded products."""
    r = client.get("/products")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 14
    assert len(data["items"]) > 0
    assert data["page"] == 1


def test_list_products_pagination(client):
    """Pagination params work."""
    r = client.get("/products", params={"page": 1, "per_page": 3})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["items"]) <= 3
    assert data["per_page"] == 3


def test_list_products_filter_by_category(client):
    """Filter products by category slug."""
    r = client.get("/products", params={"category": "tents"})
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) >= 3
    for item in items:
        assert item["category"]["slug"] == "tents"


def test_list_products_search(client):
    """Search products by name."""
    r = client.get("/products", params={"q": "hammock"})
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) >= 1
    assert any("Hammock" in i["name"] for i in items)


def test_list_products_price_filter(client):
    """Filter by price range."""
    r = client.get("/products", params={"min_price": 100, "max_price": 200})
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    for item in items:
        price = float(item["price"])
        assert 100 <= price <= 200


def test_list_products_sort_price_asc(client):
    """Sort by price ascending."""
    r = client.get("/products", params={"sort": "price_asc", "per_page": 100})
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    prices = [float(i["price"]) for i in items]
    assert prices == sorted(prices)


def test_get_product_by_slug(client):
    """Get product detail by slug."""
    r = client.get("/products/trailmaster-2-person-tent")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "TrailMaster 2-Person Tent"
    assert "price" in data
    assert "stock" in data
    assert "category" in data
    assert "images" in data


def test_get_product_not_found(client):
    r = client.get("/products/nonexistent-product-slug")
    assert r.status_code == 404


def test_create_product_as_admin(client, admin_headers):
    """Admin can create a product."""
    # Get a category ID
    cats = client.get("/categories").json()["data"]
    cat_id = cats[0]["id"]

    slug = f"test-prod-{uuid.uuid4().hex[:6]}"
    r = client.post("/products", headers=admin_headers, json={
        "name": f"Test Product {slug}",
        "slug": slug,
        "description": "Smoke test product",
        "price": "49.99",
        "stock": 10,
        "category_id": cat_id,
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["slug"] == slug
    assert float(data["price"]) == 49.99


def test_create_product_as_customer_forbidden(client, customer_headers):
    """Customer cannot create a product."""
    r = client.post("/products", headers=customer_headers, json={
        "name": "Nope",
        "slug": "nope",
        "price": "9.99",
        "stock": 1,
        "category_id": "00000000-0000-0000-0000-000000000000",
    })
    assert r.status_code == 403


def test_update_product_as_admin(client, admin_headers):
    """Admin can update a product."""
    # Create first
    cats = client.get("/categories").json()["data"]
    slug = f"upd-prod-{uuid.uuid4().hex[:6]}"
    r = client.post("/products", headers=admin_headers, json={
        "name": f"Updatable {slug}",
        "slug": slug,
        "price": "19.99",
        "stock": 5,
        "category_id": cats[0]["id"],
    })
    prod_id = r.json()["data"]["id"]

    r2 = client.put(f"/products/{prod_id}", headers=admin_headers, json={
        "price": "29.99",
        "stock": 20,
    })
    assert r2.status_code == 200
    assert float(r2.json()["data"]["price"]) == 29.99
    assert r2.json()["data"]["stock"] == 20


def test_soft_delete_product(client, admin_headers):
    """DELETE product sets is_active=false (soft delete)."""
    cats = client.get("/categories").json()["data"]
    slug = f"del-prod-{uuid.uuid4().hex[:6]}"
    r = client.post("/products", headers=admin_headers, json={
        "name": f"Deletable {slug}",
        "slug": slug,
        "price": "9.99",
        "stock": 1,
        "category_id": cats[0]["id"],
    })
    prod_id = r.json()["data"]["id"]

    # Soft delete
    r2 = client.delete(f"/products/{prod_id}", headers=admin_headers)
    assert r2.status_code == 200

    # Product detail should still resolve by slug (is_active check is on listing)
    # But listing should NOT include it
    r3 = client.get("/products", params={"q": slug})
    items = r3.json()["data"]["items"]
    assert all(i["slug"] != slug for i in items)
