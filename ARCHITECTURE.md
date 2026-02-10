# CampGear Store — Architecture Overview

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS :443
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  DMZ ZONE  (Proxmox VM 1 — 10.10.1.0/24)                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Nginx Reverse Proxy  (:443 → :80 internal)              │    │
│  │  ┌─────────────────┐   ┌──────────────────────────┐     │    │
│  │  │  React SPA       │   │  /api/* → backend:8000   │     │    │
│  │  │  (static files)  │   │  (proxy_pass)            │     │    │
│  │  └─────────────────┘   └──────────────────────────┘     │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP :8000 (internal only)
                           │ firewall: DMZ→Internal on port 8000 only
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  INTERNAL ZONE  (Proxmox VM 2 — 10.10.2.0/24)                   │
│                                                                  │
│  ┌────────────────────────┐    ┌─────────────────────────┐      │
│  │  FastAPI Backend       │    │  PostgreSQL 16           │      │
│  │  (Uvicorn :8000)       │◄──►│  (:5432, listen on      │      │
│  │                        │    │   10.10.2.x only)        │      │
│  │  - REST API            │    └─────────────────────────┘      │
│  │  - JWT auth            │                                      │
│  │  - Background tasks    │    ┌─────────────────────────┐      │
│  │  - Alembic migrations  │    │  Uploaded files volume   │      │
│  └────────────────────────┘    │  /data/uploads           │      │
│                                └─────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

## Services Summary

| Service        | Zone     | Container        | Port  | Exposed To       |
|----------------|----------|------------------|-------|------------------|
| Nginx + React  | DMZ      | `frontend`       | 443/80| Internet         |
| FastAPI API    | Internal | `backend`        | 8000  | DMZ (Nginx only) |
| PostgreSQL     | Internal | `db`             | 5432  | Backend only     |

## Network / Firewall Rules

| Source          | Destination      | Port  | Protocol | Allow  |
|-----------------|-----------------|-------|----------|--------|
| Internet        | DMZ Nginx       | 443   | TCP      | YES    |
| DMZ Nginx       | Internal Backend| 8000  | TCP      | YES    |
| Internal Backend| Internal DB     | 5432  | TCP      | YES    |
| Internet        | Internal *      | *     | *        | **NO** |
| DMZ             | Internal DB     | 5432  | *        | **NO** |

Key principle: **The database is never reachable from DMZ or Internet.**

## Docker Compose Strategy

We use **two separate docker-compose files**, one per VM:

### VM 1 (DMZ) — `deploy/dmz/docker-compose.yml`
- `frontend` container: Nginx serving React static build + reverse proxy to backend

### VM 2 (Internal) — `deploy/internal/docker-compose.yml`
- `backend` container: FastAPI + Uvicorn
- `db` container: PostgreSQL 16 with persistent volume

### Local Development — `docker-compose.yml` (project root)
- Runs all three containers on one machine with a bridge network
- API available at `http://localhost:8000`
- Frontend at `http://localhost:3000` (dev server) or `http://localhost:80` (Nginx)
- PostgreSQL at `localhost:5432` (for tooling only)

## Data Flow

```
Browser → Nginx (TLS termination)
  → GET /              → serve React SPA (index.html + JS bundle)
  → GET /api/products  → proxy_pass http://backend:8000/api/v1/products
  → POST /api/auth/login → proxy_pass http://backend:8000/api/v1/auth/login

Backend → PostgreSQL (SQLAlchemy async, connection pool)
Backend → local filesystem /data/uploads (product images)
```

## Authentication Flow

```
1. POST /api/v1/auth/register  → create user, return access + refresh tokens
2. POST /api/v1/auth/login     → verify credentials, return tokens
3. All protected requests      → Authorization: Bearer <access_token>
4. POST /api/v1/auth/refresh   → exchange refresh token for new access token
5. POST /api/v1/auth/logout    → blacklist refresh token (in-memory set or DB)
```

JWT chosen over session cookies because:
- Stateless: no server-side session store needed (no Redis dependency)
- Works cleanly with SPA + API architecture
- Easy to pass across the Nginx proxy boundary
- Refresh tokens provide security rotation without forcing re-login

## Security Assumptions

- TLS terminates at Nginx in DMZ (self-signed cert fine for school demo)
- JWT secret stored as environment variable, never in code
- Database credentials in env vars, not in compose files committed to git
- `.env` files are in `.gitignore`
- DB user has limited privileges (no SUPERUSER, no CREATE DATABASE)
- CORS allows only the DMZ frontend origin
- All user input validated via Pydantic models
- Passwords hashed with bcrypt (via passlib)
- Access tokens: short-lived (30 min)
- Refresh tokens: longer-lived (7 days), stored in DB for revocation
