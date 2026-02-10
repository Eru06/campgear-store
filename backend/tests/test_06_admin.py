"""Smoke tests: admin endpoints."""


def test_admin_list_all_orders(client, admin_headers):
    """Admin can list all orders across all users."""
    r = client.get("/admin/orders", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data


def test_admin_get_order_detail(client, admin_headers):
    """Admin can view any order detail."""
    r = client.get("/admin/orders", headers=admin_headers)
    orders = r.json()["data"]["items"]
    if not orders:
        return  # skip if no orders exist yet
    order_id = orders[0]["id"]

    r2 = client.get(f"/admin/orders/{order_id}", headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == order_id


def test_admin_update_order_status(client, admin_headers):
    """Admin can update an order's status."""
    r = client.get("/admin/orders", headers=admin_headers)
    orders = r.json()["data"]["items"]
    if not orders:
        return
    order_id = orders[0]["id"]

    r2 = client.patch(f"/admin/orders/{order_id}/status", headers=admin_headers, json={
        "status": "placed",
    })
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "placed"


def test_admin_audit_logs(client, admin_headers):
    """Admin can list audit logs (should have at least the status change)."""
    r = client.get("/admin/audit-logs", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data


def test_admin_endpoints_forbidden_for_customer(client, customer_headers):
    """Customer cannot access admin endpoints."""
    r1 = client.get("/admin/orders", headers=customer_headers)
    assert r1.status_code == 403

    r2 = client.get("/admin/audit-logs", headers=customer_headers)
    assert r2.status_code == 403


def test_admin_endpoints_forbidden_without_auth(client):
    """Admin endpoints require authentication."""
    r = client.get("/admin/orders")
    assert r.status_code in (401, 403)
