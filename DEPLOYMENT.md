# CampGear Store — Proxmox Deployment Guide

## Prerequisites

- Proxmox PVE host at 192.168.3.101
- Two VMs created with Docker + Docker Compose installed:
  - **DMZ VM**: 192.168.2.10 (gateway 192.168.2.1)
  - **Internal VM**: 192.168.1.30 (gateway 192.168.1.1)
- Palo Alto FW configured with zones (Outside, DMZ, Inside, Mgmt)
- SSH access to both VMs from management network (192.168.3.0/24)

## Network Overview

```
Internet → 172.31.26.187:80,443
  → Palo Alto NAT → 192.168.2.10:80,443 (DMZ - Nginx + React)
    → Palo Alto FW rule → 192.168.1.30:8000 (Inside - FastAPI + PostgreSQL)
```

See `ARCHITECTURE.md` for full topology and firewall rules.

---

## Step 1: Palo Alto Firewall Rules

Configure these rules on the Palo Alto FW before deploying:

### NAT Rules
```
# Inbound NAT for web traffic
Source: any  →  Dest: 172.31.26.187:80,443  →  Translate to: 192.168.2.10:80,443

# Outbound NAT for DMZ/Inside internet access (package downloads)
Source: 192.168.1.0/24, 192.168.2.0/24  →  Translate to: 172.31.26.186
```

### Security Rules
```
# Allow internet → DMZ web server
Rule 1: any → 192.168.2.10 | TCP 80,443 | ALLOW

# Allow DMZ web → Inside backend API
Rule 2: 192.168.2.10 → 192.168.1.30 | TCP 8000 | ALLOW

# Deny DMZ → Inside (everything else)
Rule 3: 192.168.2.0/24 → 192.168.1.0/24 | any | DENY

# Deny internet → Inside (direct)
Rule 4: any → 192.168.1.0/24 | any | DENY
```

---

## Step 2: Deploy Internal VM (192.168.1.30)

### 2.1 Copy files to the VM

```bash
# From your workstation (on management network)
scp -r backend/ user@192.168.1.30:~/campgear/backend/
scp deploy/internal/docker-compose.yml user@192.168.1.30:~/campgear/
scp deploy/internal/.env.example user@192.168.1.30:~/campgear/.env.example
scp deploy/db/init.sql user@192.168.1.30:~/campgear/init.sql
```

### 2.2 Create production .env

```bash
ssh user@192.168.1.30
cd ~/campgear
cp .env.example .env
```

Edit `.env` with production values:
```bash
# Generate a strong DB password
DB_PASSWORD=$(openssl rand -hex 16)

# Generate JWT secret
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# CORS — only allow the DMZ frontend
CORS_ORIGINS=http://192.168.2.10,https://192.168.2.10
```

### 2.3 Build and start

```bash
cd ~/campgear
docker compose up -d --build
```

### 2.4 Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 2.5 Seed demo data

```bash
docker compose exec backend python -m app.seed
```

### 2.6 Verify

```bash
# Check containers are running
docker compose ps

# Test API locally
curl http://localhost:8000/api/v1/categories
# Should return JSON with categories
```

---

## Step 3: Deploy DMZ VM (192.168.2.10)

### 3.1 Copy files to the VM

```bash
# From your workstation
scp -r frontend/ user@192.168.2.10:~/campgear/frontend/
scp deploy/dmz/docker-compose.yml user@192.168.2.10:~/campgear/
scp deploy/dmz/nginx.conf user@192.168.2.10:~/campgear/nginx.conf
```

### 3.2 (Optional) Generate self-signed TLS certificate

```bash
ssh user@192.168.2.10
mkdir -p ~/campgear/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ~/campgear/certs/campgear.key \
  -out ~/campgear/certs/campgear.crt \
  -subj "/CN=campgear.local/O=TeamD"
```

If using HTTPS, uncomment the HTTPS server block in `nginx.conf`.

### 3.3 Build and start

```bash
cd ~/campgear
docker compose up -d --build
```

### 3.4 Verify

```bash
# Check container is running
docker compose ps

# Test locally on DMZ VM
curl http://localhost/
# Should return HTML (React index.html)

# Test API proxy through to internal zone
curl http://localhost/api/v1/categories
# Should return JSON from backend at 192.168.1.30
```

---

## Step 4: End-to-End Verification

### From External Pen-Test Machine (172.31.26.190) or any external host:

```bash
# 1. Load the web frontend
curl http://172.31.26.187/
# Should return React SPA HTML

# 2. API call through the full chain
curl http://172.31.26.187/api/v1/products
# Should return product JSON

# 3. Register a user
curl -X POST http://172.31.26.187/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!","full_name":"Test User"}'

# 4. Login
curl -X POST http://172.31.26.187/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
# Should return access_token + refresh_token
```

### From a browser:
1. Open `http://172.31.26.187` (or the DNS name if configured)
2. Register a new user
3. Browse products, add to cart, checkout
4. Login as admin: `admin@campgear.com` / `Admin123!`
5. Manage products, orders, categories

---

## Step 5: Security Verification

```bash
# Verify DB is NOT reachable from DMZ
ssh user@192.168.2.10
nc -zv 192.168.1.30 5432    # Should FAIL (blocked by Palo Alto)
nc -zv 192.168.1.30 8000    # Should SUCCEED (allowed by rule #2)

# Verify DB is NOT reachable from internet
# From 172.31.26.190:
nc -zv 172.31.26.187 5432   # Should FAIL (no NAT rule)
nc -zv 192.168.1.30 5432    # Should FAIL (not routable)
```

---

## Directory Structure on Each VM

### DMZ VM (192.168.2.10): ~/campgear/
```
├── docker-compose.yml     # from deploy/dmz/
├── nginx.conf             # from deploy/dmz/ (backend IP = 192.168.1.30)
├── certs/                 # TLS certs (optional)
│   ├── campgear.crt
│   └── campgear.key
└── frontend/              # React app source + Dockerfile
    ├── frontend.Dockerfile
    ├── package.json
    └── src/
```

### Internal VM (192.168.1.30): ~/campgear/
```
├── docker-compose.yml     # from deploy/internal/
├── .env                   # production secrets (not in git)
├── init.sql               # from deploy/db/
└── backend/               # FastAPI source + Dockerfile
    ├── Dockerfile
    ├── pyproject.toml
    └── app/
```

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Frontend loads but API calls fail | Palo Alto rule #2 (DMZ→Inside:8000) missing |
| `502 Bad Gateway` from Nginx | Backend not running on 192.168.1.30, or wrong IP in nginx.conf |
| DB connection refused | Check `DB_PASSWORD` matches in `.env`, run `docker compose logs db` |
| CORS errors in browser | Check `CORS_ORIGINS` in Internal `.env` includes `http://192.168.2.10` |
| Can't reach site from internet | Palo Alto NAT rule missing: 172.31.26.187 → 192.168.2.10 |
| Migration fails | Run `docker compose exec backend alembic upgrade head` on Internal VM |

---

## Maintenance

```bash
# View logs
docker compose logs -f backend    # on Internal VM
docker compose logs -f frontend   # on DMZ VM

# Restart services
docker compose restart

# Update and rebuild
docker compose down
docker compose up -d --build

# Backup database
docker compose exec db pg_dump -U campgear campgear > backup_$(date +%Y%m%d).sql
```
