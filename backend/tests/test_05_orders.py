"""Smoke tests: order creation and listing."""


def _get_product_id(client):
    r = client.get("/products", params={"per_page": 1})
    return r.json()["data"]["items"][0]["id"]


def _prepare_cart(client, headers):
    """Clear cart, add one item, return product_id."""
    client.delete("/cart", headers=headers)
    pid = _get_product_id(client)
    client.post("/cart/items", headers=headers, json={
        "product_id": pid, "quantity": 1,
    })
    return pid


def test_create_order(client, customer_headers):
    """Full checkout flow: add to cart → create order."""
    _prepare_cart(client, customer_headers)

    r = client.post("/orders", headers=customer_headers, json={
        "shipping_name": "Happy Camper",
        "shipping_address": "123 Forest Trail",
        "shipping_city": "Portland",
        "shipping_zip": "97201",
        "payment_method": "offline",
        "payment_note": "Pay at pickup",
    })
    assert r.status_code == 201
    order = r.json()["data"]
    assert order["status"] == "pending_payment"
    assert len(order["items"]) >= 1
    assert float(order["total"]) > 0

    # Cart should be empty after order
    r2 = client.get("/cart", headers=customer_headers)
    assert len(r2.json()["data"]["items"]) == 0


def test_create_order_empty_cart(client, customer_headers):
    """Creating order with empty cart should fail."""
    client.delete("/cart", headers=customer_headers)
    r = client.post("/orders", headers=customer_headers, json={
        "shipping_name": "Nobody",
        "shipping_address": "Nowhere",
        "shipping_city": "Void",
        "shipping_zip": "00000",
    })
    assert r.status_code == 400


def test_list_my_orders(client, customer_headers):
    """Customer can list their own orders."""
    r = client.get("/orders", headers=customer_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_order_detail(client, customer_headers):
    """Customer can view their own order detail."""
    # Get first order
    r = client.get("/orders", headers=customer_headers)
    orders = r.json()["data"]["items"]
    assert len(orders) >= 1
    order_id = orders[0]["id"]

    r2 = client.get(f"/orders/{order_id}", headers=customer_headers)
    assert r2.status_code == 200
    detail = r2.json()["data"]
    assert detail["id"] == order_id
    assert len(detail["items"]) >= 1


def test_order_requires_auth(client):
    """Order endpoints require authentication."""
    r = client.get("/orders")
    assert r.status_code in (401, 403)
