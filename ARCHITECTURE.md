# CampGear Store — Architecture Overview

## Network Topology (Based on Network Diagram v3 — Team D)

```
                         ┌──────────────┐
                         │   INTERNET   │
                         └──────┬───────┘
                                │
                    NAT/PAT (172.31.26.186/29)
                    172.31.26.187:80,443 → 192.168.2.10:80,443
                                │
┌───────────────────────────────┼──────────────────────────────────────┐
│                        Proxmox PVE Host                              │
│                     (Mgmt: 192.168.3.101)                            │
│                                                                      │
│   ┌────────────────────────────────────────────────────────────┐     │
│   │              Palo Alto Firewall                             │     │
│   │  Outside: 172.31.26.186/29                                  │     │
│   │  Inside:  192.168.1.1/24                                    │     │
│   │  DMZ:     192.168.2.1/24                                    │     │
│   │  Mgmt:    192.168.3.1/24                                    │     │
│   └──────┬──────────────────────────┬──────────────────────────┘     │
│          │ Inside                   │ DMZ                            │
│          ▼                          ▼                                │
│   ┌──────────────────┐    ┌──────────────────────────────┐          │
│   │ INSIDE ZONE       │    │ DMZ ZONE                     │          │
│   │ 192.168.1.0/24    │    │ 192.168.2.0/24               │          │
│   │                   │    │                              │          │
│   │ ┌───────────────┐│    │ ┌──────────────────────────┐ │          │
│   │ │E-commerce     ││    │ │E-commerce Web            │ │          │
│   │ │App/DB         ││    │ │192.168.2.10              │ │          │
│   │ │192.168.1.30   ││    │ │                          │ │          │
│   │ │               ││    │ │  Nginx + React SPA       │ │          │
│   │ │ FastAPI :8000 ◄├────┤─│  /api/* → 192.168.1.30   │ │          │
│   │ │ PostgreSQL    ││    │ │  :8000 (via Palo Alto)   │ │          │
│   │ │  :5432        ││    │ │                          │ │          │
│   │ └───────────────┘│    │ └──────────────────────────┘ │          │
│   │                   │    │                              │          │
│   │ Other servers:    │    │ Other servers:               │          │
│   │  DC/DNS .1.10    │    │  Email GW   .2.20           │          │
│   │  Mail   .1.20    │    │  Public DNS .2.30           │          │
│   │  SecOnion .1.40  │    │  SecOnion   .2.40           │          │
│   │  Wazuh  .1.50    │    │                              │          │
│   └──────────────────┘    └──────────────────────────────┘          │
│                                                                      │
│   ┌──────────────────────────────────────────────┐                   │
│   │ MANAGEMENT ZONE (192.168.3.0/24)              │                   │
│   │  Proxmox Mgmt  .3.101                         │                   │
│   │  IAM Server    .3.11                           │                   │
│   │  Palo Alto Mgmt .3.1                           │                   │
│   └──────────────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

## IP Address Summary

| Host                  | Zone       | IP Address      | Purpose                  |
|-----------------------|------------|-----------------|--------------------------|
| E-commerce Web        | DMZ        | 192.168.2.10    | Nginx + React frontend   |
| E-commerce App/DB     | Inside     | 192.168.1.30    | FastAPI + PostgreSQL     |
| Palo Alto FW (DMZ)    | —          | 192.168.2.1     | Gateway for DMZ zone     |
| Palo Alto FW (Inside) | —          | 192.168.1.1     | Gateway for Inside zone  |
| Palo Alto FW (Outside)| —          | 172.31.26.186   | Internet-facing          |
| Proxmox Host Mgmt     | Management | 192.168.3.101   | Hypervisor management    |
| Domain Controller/DNS | Inside     | 192.168.1.10    | AD + Internal DNS        |
| Mail Server           | Inside     | 192.168.1.20    | Mailbox/IMAP             |
| Security Onion        | Inside     | 192.168.1.40    | IDS/IPS management       |
| Wazuh Server          | Inside     | 192.168.1.50    | HIDS/SIEM               |
| Email Gateway         | DMZ        | 192.168.2.20    | SMTP relay               |
| Public DNS            | DMZ        | 192.168.2.30    | External DNS             |
| Security Onion Sensor | DMZ        | 192.168.2.40    | Network sensor           |

## NAT/PAT Rules (Palo Alto)

| Public IP:Port              | Direction | Internal IP:Port     | Service         |
|-----------------------------|-----------|----------------------|-----------------|
| 172.31.26.187:80,443        | Inbound   | 192.168.2.10:80,443  | E-commerce Web  |
| 172.31.26.188:25,587        | Inbound   | 192.168.2.20:25,587  | Email Gateway   |
| 172.31.26.189:53 TCP/UDP    | Inbound   | 192.168.2.30:53      | Public DNS      |
| Inside/DMZ → 172.31.26.186  | Outbound  | —                    | Outbound NAT    |

## Services Summary

| Service        | Zone     | VM IP           | Container  | Port  | Exposed To         |
|----------------|----------|-----------------|------------|-------|--------------------|
| Nginx + React  | DMZ      | 192.168.2.10    | `frontend` | 80/443| Internet (via NAT) |
| FastAPI API    | Inside   | 192.168.1.30    | `backend`  | 8000  | DMZ (Nginx only)   |
| PostgreSQL     | Inside   | 192.168.1.30    | `db`       | 5432  | Backend only       |

## Firewall Rules (Palo Alto — CampGear Specific)

| # | Source            | Destination         | Port  | Protocol | Action  | Notes                       |
|---|-------------------|---------------------|-------|----------|---------|-----------------------------|
| 1 | Internet          | 192.168.2.10        | 80,443| TCP      | ALLOW   | NAT to DMZ web server       |
| 2 | 192.168.2.10      | 192.168.1.30        | 8000  | TCP      | ALLOW   | Nginx → Backend API         |
| 3 | 192.168.1.30      | (Docker internal)   | 5432  | TCP      | ALLOW   | Backend → DB (Docker net)   |
| 4 | Internet          | 192.168.1.0/24      | *     | *        | **DENY**| No direct access to Inside  |
| 5 | 192.168.2.0/24    | 192.168.1.30        | 5432  | TCP      | **DENY**| DB never reachable from DMZ |
| 6 | 192.168.2.0/24    | 192.168.1.0/24      | *     | *        | **DENY**| Block all except rule #2    |

Key principle: **The database is never reachable from DMZ or Internet.** Only the FastAPI container communicates with PostgreSQL via Docker's internal bridge network on 192.168.1.30.

## Docker Compose Strategy

We use **two separate docker-compose files**, one per VM:

### VM: 192.168.2.10 (DMZ) — `deploy/dmz/docker-compose.yml`
- `frontend` container: Nginx serving React static build + reverse proxy to 192.168.1.30:8000
- TLS certs mounted from `deploy/dmz/certs/`

### VM: 192.168.1.30 (Inside) — `deploy/internal/docker-compose.yml`
- `backend` container: FastAPI + Uvicorn on port 8000
- `db` container: PostgreSQL 16 with persistent volume
- Environment from `deploy/internal/.env`

### Local Development — `docker-compose.yml` (project root)
- Runs all three containers on one machine with Docker bridge network
- API available at `http://localhost:8000`
- Frontend at `http://localhost:3000`
- PostgreSQL at `localhost:5432` (for tooling only)

## Data Flow

```
Browser → Internet → Palo Alto NAT (172.31.26.187)
  → 192.168.2.10:80 Nginx (TLS termination)
    → GET /              → serve React SPA (index.html + JS bundle)
    → GET /api/products  → proxy_pass → Palo Alto FW → 192.168.1.30:8000
    → POST /api/auth/login → proxy_pass → 192.168.1.30:8000

192.168.1.30 Backend → PostgreSQL (Docker internal network, :5432)
192.168.1.30 Backend → local filesystem /data/uploads (product images)
```

## Authentication Flow

```
1. POST /api/v1/auth/register  → create user, return access + refresh tokens
2. POST /api/v1/auth/login     → verify credentials, return tokens
3. All protected requests      → Authorization: Bearer <access_token>
4. POST /api/v1/auth/refresh   → exchange refresh token for new access token
5. POST /api/v1/auth/logout    → blacklist refresh token (in DB)
```

JWT chosen over session cookies because:
- Stateless: no server-side session store needed (no Redis dependency)
- Works cleanly with SPA + API architecture
- Easy to pass across the Nginx proxy boundary via Palo Alto FW
- Refresh tokens provide security rotation without forcing re-login

## Security Assumptions

- TLS terminates at Nginx on 192.168.2.10 (self-signed cert fine for school demo)
- Palo Alto FW enforces zone segmentation (DMZ ↔ Inside)
- JWT secret stored as environment variable, never in code
- Database credentials in `.env` files, not committed to git
- DB user has limited privileges (no SUPERUSER, no CREATE DATABASE)
- CORS allows only `http://192.168.2.10` and `https://192.168.2.10`
- All user input validated via Pydantic models
- Passwords hashed with bcrypt (via passlib)
- Access tokens: short-lived (30 min)
- Refresh tokens: longer-lived (7 days), stored in DB for revocation
- Security monitoring: Wazuh (192.168.1.50) + Security Onion (192.168.1.40 / 192.168.2.40)
