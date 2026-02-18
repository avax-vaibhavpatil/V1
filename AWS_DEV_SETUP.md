# AWS Dev Environment – Analytics Studio

## Architecture

```
EC2 (App Server) ──→ RDS PostgreSQL (Sales Data)
       │
       ├──→ SQLite (App Metadata - local file)
       │
       └──→ OpenAI API (External)
```

---

## 1. EC2 – Application Server

| Property | Value |
|----------|-------|
| Instance | t3.large (2 vCPU, 8 GB RAM) |
| OS | Ubuntu 22.04 LTS |
| Storage | 50 GB gp3 |

### Runtime Versions

| Component | Version |
|-----------|---------|
| Python | 3.12.3 |
| Node.js | 22.17.0 |
| npm | 10.x |

### Backend Dependencies (Python)

| Package | Version |
|---------|---------|
| fastapi | 0.128.0 |
| uvicorn | 0.40.0 |
| gunicorn | latest |
| sqlalchemy | 2.0.46 |
| asyncpg | 0.31.0 |
| aiosqlite | 0.22.1 |
| pydantic | 2.12.5 |
| pydantic-settings | 2.12.0 |
| openai | 2.17.0 |
| alembic | 1.18.1 |
| python-jose | 3.5.0 |
| passlib | 1.7.4 |
| openpyxl | 3.1.5 |
| python-multipart | 0.0.21 |
| httpx | 0.28.1 |

### Frontend Dependencies (Node.js)

| Package | Version |
|---------|---------|
| react | 18.3.1 |
| react-dom | 18.3.1 |
| typescript | 5.9.3 |
| vite | 5.4.21 |
| tailwindcss | 3.4.19 |
| axios | 1.13.2 |

### Application Server

| Property | Value |
|----------|-------|
| Server | Gunicorn + Uvicorn |
| Workers | 1 (SQLite limitation) |
| Port | 8000 |
| Command | `gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` |

---

## 2. RDS – PostgreSQL

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 15 |
| Instance | db.t3.medium (2 vCPU, 4 GB RAM) |
| Storage | 100 GB gp3 (auto-scaling) |
| Multi-AZ | No |
| Database Name | analytics_llm |
| Port | 5432 |
| Purpose | Sales data, reports, AI chat |

---

## 3. SQLite (Local on EC2)

| Property | Value |
|----------|-------|
| File | analytics_studio.db |
| Driver | aiosqlite 0.22.1 |
| Purpose | App metadata (projects, dashboards) |

---

## 4. Security Groups

### EC2 – Inbound

| Port | Source | Purpose |
|------|--------|---------|
| 22 | Office IP | SSH |
| 8000 | Office IP / VPC | FastAPI |
| 80 | Office IP / VPC | Nginx (optional) |

### EC2 – Outbound

| Port | Destination | Purpose |
|------|-------------|---------|
| 443 | 0.0.0.0/0 | OpenAI API |
| 5432 | RDS | PostgreSQL |

### RDS – Inbound

| Port | Source | Purpose |
|------|--------|---------|
| 5432 | EC2 SG | PostgreSQL |

---

## 5. Environment Variables

```env
ENVIRONMENT=development
DEBUG=true

# PostgreSQL (RDS) - Sales Data
ANALYTICS_DB_URL=postgresql+asyncpg://postgres:PASSWORD@RDS_ENDPOINT:5432/analytics_llm

# SQLite - App Metadata
DATABASE_URL=sqlite+aiosqlite:///./analytics_studio.db

# OpenAI (Required)
OPENAI_API_KEY=sk-xxxxx

# Security
SECRET_KEY=<random-64-char-string>
```

---

## 6. IAM Role (EC2)

- CloudWatch Logs: Read/Write
- S3: Read/Write (optional, for uploads)

---

## 8. Summary

| Component | AWS Service | Spec |
|-----------|-------------|------|
| App Server | EC2 t3.large | Python 3.12, Node 22, Port 8000 |
| Sales DB | RDS PostgreSQL 15 | db.t3.medium, 100GB |
| App DB | SQLite | Local file on EC2 |
| External | OpenAI API | Outbound HTTPS |

