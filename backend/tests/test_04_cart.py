"""Smoke tests: cart operations."""


def _get_product_id(client):
    """Helper: get the first product ID from listing."""
    r = client.get("/products", params={"per_page": 1})
    return r.json()["data"]["items"][0]["id"]


def test_get_empty_cart(client, customer_headers):
    """GET /cart returns a cart (empty or not)."""
    # Clear first to ensure clean state
    client.delete("/cart", headers=customer_headers)
    r = client.get("/cart", headers=customer_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data


def test_add_item_to_cart(client, customer_headers):
    """Add a product to the cart."""
    # Clear cart first
    client.delete("/cart", headers=customer_headers)

    pid = _get_product_id(client)
    r = client.post("/cart/items", headers=customer_headers, json={
        "product_id": pid,
        "quantity": 2,
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert len(data["items"]) >= 1
    added = [i for i in data["items"] if i["product_id"] == pid]
    assert len(added) == 1
    assert added[0]["quantity"] == 2


def test_update_cart_item_quantity(client, customer_headers):
    """Update quantity of a cart item."""
    r = client.get("/cart", headers=customer_headers)
    items = r.json()["data"]["items"]
    if not items:
        # Add an item first
        pid = _get_product_id(client)
        client.post("/cart/items", headers=customer_headers, json={
            "product_id": pid, "quantity": 2,
        })
        r = client.get("/cart", headers=customer_headers)
        items = r.json()["data"]["items"]

    item_id = items[0]["id"]

    r2 = client.put(f"/cart/items/{item_id}", headers=customer_headers, json={
        "quantity": 1,
    })
    assert r2.status_code == 200
    updated = [i for i in r2.json()["data"]["items"] if i["id"] == item_id]
    assert updated[0]["quantity"] == 1


def test_remove_cart_item(client, customer_headers):
    """Remove an item from the cart."""
    # Ensure clean state: clear and add exactly one item
    client.delete("/cart", headers=customer_headers)
    pid = _get_product_id(client)
    client.post("/cart/items", headers=customer_headers, json={
        "product_id": pid, "quantity": 1,
    })

    r = client.get("/cart", headers=customer_headers)
    items = r.json()["data"]["items"]
    assert len(items) == 1
    item_id = items[0]["id"]

    r2 = client.delete(f"/cart/items/{item_id}", headers=customer_headers)
    assert r2.status_code == 200
    assert len(r2.json()["data"]["items"]) == 0


def test_clear_cart(client, customer_headers):
    """Clear the entire cart."""
    pid = _get_product_id(client)
    client.post("/cart/items", headers=customer_headers, json={
        "product_id": pid, "quantity": 1,
    })

    r = client.delete("/cart", headers=customer_headers)
    assert r.status_code == 200

    # Verify empty
    r2 = client.get("/cart", headers=customer_headers)
    assert len(r2.json()["data"]["items"]) == 0


def test_add_insufficient_stock(client, customer_headers):
    """Adding more than available stock should fail."""
    pid = _get_product_id(client)
    r = client.post("/cart/items", headers=customer_headers, json={
        "product_id": pid,
        "quantity": 999999,
    })
    assert r.status_code == 400
    assert "stock" in r.json()["detail"].lower()


def test_cart_requires_auth(client):
    """Cart endpoints require authentication."""
    r = client.get("/cart")
    assert r.status_code in (401, 403)
