# CampGear Store — API Design (v1)

Base path: `/api/v1`

All responses use a consistent envelope:
```json
{
  "data": { ... },       // or list
  "message": "ok",       // human-readable
  "errors": []           // validation / business errors
}
```

Error responses:
```json
{
  "data": null,
  "message": "Validation failed",
  "errors": [
    {"field": "email", "detail": "Already registered"}
  ]
}
```

## Authentication

| Method | Endpoint                  | Auth   | Role | Description                     |
|--------|---------------------------|--------|------|---------------------------------|
| POST   | `/auth/register`          | No     | —    | Create new customer account     |
| POST   | `/auth/login`             | No     | —    | Get access + refresh tokens     |
| POST   | `/auth/refresh`           | No*    | —    | Exchange refresh token for new pair |
| POST   | `/auth/logout`            | Bearer | Any  | Revoke refresh token            |
| GET    | `/auth/me`                | Bearer | Any  | Get current user profile        |

*Refresh endpoint receives the refresh token in body, not in Authorization header.

### Register
```
POST /api/v1/auth/register
Body: { "email": "alice@example.com", "password": "Str0ng!Pass", "full_name": "Alice Smith" }
→ 201 { "data": { "id": "uuid", "email": "...", "full_name": "...", "role": "customer" } }
```

### Login
```
POST /api/v1/auth/login
Body: { "email": "alice@example.com", "password": "Str0ng!Pass" }
→ 200 { "data": { "access_token": "...", "refresh_token": "...", "token_type": "bearer" } }
```

## Categories

| Method | Endpoint                  | Auth   | Role  | Description             |
|--------|---------------------------|--------|-------|-------------------------|
| GET    | `/categories`             | No     | —     | List all categories     |
| GET    | `/categories/{slug}`      | No     | —     | Get category detail     |
| POST   | `/categories`             | Bearer | Admin | Create category         |
| PUT    | `/categories/{id}`        | Bearer | Admin | Update category         |
| DELETE | `/categories/{id}`        | Bearer | Admin | Delete category         |

## Products

| Method | Endpoint                          | Auth   | Role  | Description                   |
|--------|-----------------------------------|--------|-------|-------------------------------|
| GET    | `/products`                       | No     | —     | List products (paginated)     |
| GET    | `/products/{slug}`                | No     | —     | Product detail                |
| POST   | `/products`                       | Bearer | Admin | Create product                |
| PUT    | `/products/{id}`                  | Bearer | Admin | Update product                |
| DELETE | `/products/{id}`                  | Bearer | Admin | Soft-delete (set inactive)    |
| POST   | `/products/{id}/images`           | Bearer | Admin | Upload product image          |
| DELETE | `/products/{id}/images/{img_id}`  | Bearer | Admin | Remove product image          |

### List Products — Query Parameters
| Param      | Type    | Description                          |
|------------|---------|--------------------------------------|
| `q`        | string  | Search name/description (ILIKE)      |
| `category` | string  | Filter by category slug              |
| `min_price`| decimal | Minimum price filter                 |
| `max_price`| decimal | Maximum price filter                 |
| `in_stock` | bool    | Only show items with stock > 0       |
| `page`     | int     | Page number (default 1)              |
| `per_page` | int     | Items per page (default 20, max 100) |
| `sort`     | string  | `price_asc`, `price_desc`, `newest`  |

### List Products Response
```json
{
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "4-Person Camping Tent",
        "slug": "4-person-camping-tent",
        "price": "149.99",
        "stock": 25,
        "category": { "name": "Tents", "slug": "tents" },
        "thumbnail": "https://.../thumb.jpg"
      }
    ],
    "total": 42,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

## Cart

One cart per user, created lazily on first add.

| Method | Endpoint                    | Auth   | Role     | Description              |
|--------|-----------------------------|--------|----------|--------------------------|
| GET    | `/cart`                     | Bearer | Customer | Get current cart          |
| POST   | `/cart/items`               | Bearer | Customer | Add item to cart          |
| PUT    | `/cart/items/{item_id}`     | Bearer | Customer | Update item quantity      |
| DELETE | `/cart/items/{item_id}`     | Bearer | Customer | Remove item from cart     |
| DELETE | `/cart`                     | Bearer | Customer | Clear entire cart         |

### Add to Cart
```
POST /api/v1/cart/items
Body: { "product_id": "uuid", "quantity": 2 }
→ 201 { "data": { cart object with items } }
```

## Orders

| Method | Endpoint                    | Auth   | Role     | Description                    |
|--------|-----------------------------|--------|----------|--------------------------------|
| POST   | `/orders`                   | Bearer | Customer | Create order from cart          |
| GET    | `/orders`                   | Bearer | Customer | List my orders (paginated)      |
| GET    | `/orders/{id}`              | Bearer | Customer | Get order detail                |

### Create Order (checkout)
```
POST /api/v1/orders
Body: {
  "shipping_name": "Alice Smith",
  "shipping_address": "123 Trail Rd",
  "shipping_city": "Portland",
  "shipping_zip": "97201",
  "payment_method": "offline",
  "payment_note": "Will pay at pickup"
}
→ 201 { "data": { order object with items, status: "pending_payment" } }
```

This endpoint:
1. Validates all cart items are still in stock
2. Decrements product stock (atomic)
3. Creates order + order_items with price snapshots
4. Clears the user's cart
5. Queues a background task for mock "order confirmation email"

## Admin — Orders

| Method | Endpoint                           | Auth   | Role  | Description              |
|--------|------------------------------------|--------|-------|--------------------------|
| GET    | `/admin/orders`                    | Bearer | Admin | List all orders          |
| GET    | `/admin/orders/{id}`               | Bearer | Admin | Get any order detail     |
| PATCH  | `/admin/orders/{id}/status`        | Bearer | Admin | Update order status      |

### Update Order Status
```
PATCH /api/v1/admin/orders/{id}/status
Body: { "status": "placed" }
→ 200 { "data": { updated order } }
```

## Admin — Audit Logs

| Method | Endpoint              | Auth   | Role  | Description                |
|--------|-----------------------|--------|-------|----------------------------|
| GET    | `/admin/audit-logs`   | Bearer | Admin | List audit log entries     |

## Authorization Rules Summary

- **Public**: product browsing, categories, register, login
- **Customer (authenticated)**: cart operations, create orders, view own orders, profile
- **Admin**: all product/category CRUD, all order management, audit logs, everything customer can do

## Input Validation

- Email: valid format, max 320 chars
- Password: min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit
- Product name: max 200 chars
- Price: decimal, >= 0, max 2 decimal places
- Quantity: integer, > 0
- Pagination: page >= 1, per_page 1..100

All validation handled by Pydantic schemas. Invalid input returns 422 with field-level errors.
