# 📋 Analytics Studio - ACTUAL Technology Stack

> **For Cloud Team** - Only technologies ACTUALLY being used in the codebase (verified)

---

## ⚠️ Important Notes

| Item | Status | Notes |
|------|--------|-------|
| **Redis** | ❌ NOT USED | Package installed but never imported/used |
| **PostgreSQL** | ✅ USED | For sales analytics data (reports, AI chat) |
| **SQLite** | ✅ USED | For app metadata (projects, dashboards) |

### Two Database Architecture:
| Database | Type | Port | Purpose |
|----------|------|------|---------|
| **analytics-llm** | PostgreSQL | 5430 | Sales data, Reports, AI Chat queries |
| **analytics_studio.db** | SQLite | - | App metadata (projects, dashboards, users) |

---

## 🖥️ Runtime Versions (Your System)

| Component | Exact Version |
|-----------|---------------|
| **Python** | 3.12.3 |
| **Node.js** | 22.17.0 |

---

## 🐍 Backend - ACTUALLY USED

### Core Framework

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **fastapi** | 0.128.0 | ✅ Yes |
| **uvicorn** | 0.40.0 | ✅ Yes |
| **pydantic** | 2.12.5 | ✅ Yes |
| **pydantic-settings** | 2.12.0 | ✅ Yes |

### Database & ORM

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **sqlalchemy** | 2.0.46 | ✅ Yes (ORM layer for both databases) |
| **asyncpg** | 0.31.0 | ✅ Yes (PostgreSQL driver for sales data) |
| **aiosqlite** | 0.22.1 | ✅ Yes (SQLite driver for app metadata) |
| **alembic** | 1.18.1 | ✅ Yes (migrations) |

### AI/LLM

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **openai** | 2.17.0 | ✅ Yes |

### Authentication & Security

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **python-jose** | 3.5.0 | ✅ Yes (JWT) |
| **passlib** | 1.7.4 | ✅ Yes (passwords) |

### File Processing

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **python-multipart** | 0.0.21 | ✅ Yes (uploads) |
| **openpyxl** | 3.1.5 | ✅ Yes (Excel files) |

### HTTP Client

| Package | Exact Version | Actually Used? |
|---------|---------------|----------------|
| **httpx** | 0.28.1 | ✅ Yes |

### NOT USED (but installed)

| Package | Exact Version | Status |
|---------|---------------|--------|
| **redis** | 7.1.0 | ❌ NOT IMPORTED ANYWHERE |
| **aiomysql** | 0.3.2 | ❌ Not used |

---

## ⚛️ Frontend - ACTUALLY USED

### Core

| Package | Exact Version |
|---------|---------------|
| **react** | 18.3.1 |
| **react-dom** | 18.3.1 |
| **react-router-dom** | 6.30.3 |
| **typescript** | 5.9.3 |

### Build Tools

| Package | Exact Version |
|---------|---------------|
| **vite** | 5.4.21 |
| **@vitejs/plugin-react** | 4.7.0 |
| **postcss** | 8.5.6 |
| **autoprefixer** | 10.4.23 |

### Styling

| Package | Exact Version |
|---------|---------------|
| **tailwindcss** | 3.4.19 |
| **tailwind-merge** | 2.6.0 |
| **clsx** | 2.1.1 |

### State & Data

| Package | Exact Version |
|---------|---------------|
| **zustand** | 4.5.7 |
| **react-query** | 3.39.3 |
| **axios** | 1.13.2 |

### UI Components

| Package | Exact Version |
|---------|---------------|
| **lucide-react** | 0.294.0 |
| **react-dnd** | 16.0.1 |
| **react-dnd-html5-backend** | 16.0.1 |

### Code Quality

| Package | Exact Version |
|---------|---------------|
| **eslint** | 8.57.1 |
| **@typescript-eslint/eslint-plugin** | 6.21.0 |
| **@typescript-eslint/parser** | 6.21.0 |

---

## 🗄️ Database - CURRENT STATE

### Database 1: Sales Analytics Data (PostgreSQL)
| Property | Value |
|----------|-------|
| **Database** | PostgreSQL |
| **Database Name** | `analytics-llm` |
| **Host** | localhost |
| **Port** | 5430 |
| **Driver** | asyncpg 0.31.0 |
| **Connection URL** | `postgresql+asyncpg://postgres:root@localhost:5430/analytics-llm` |
| **Used For** | Reports, KPIs, Table data, AI Chat queries |

### Database 2: App Metadata (SQLite)
| Property | Value |
|----------|-------|
| **Database** | SQLite |
| **File** | `analytics_studio.db` |
| **Driver** | aiosqlite 0.22.1 |
| **Used For** | Projects, Dashboards, Users, Calculations |

### ORM Layer
| Property | Value |
|----------|-------|
| **ORM** | SQLAlchemy 2.0.46 |
| **Mode** | Async (asyncio) |

### For AWS Production:
| Property | Value |
|----------|-------|
| **Sales Data** | RDS PostgreSQL 15+ |
| **App Metadata** | RDS PostgreSQL 15+ (migrate from SQLite) |
| **AWS Service** | Single RDS instance with 2 databases |

---

## 🤖 External Services - ACTUALLY USED

| Service | Package | Version | Status |
|---------|---------|---------|--------|
| **OpenAI API** | openai | 2.17.0 | ✅ Used in `llm_service.py` |

---

## 🌐 Network Ports

| Service | Port | Status |
|---------|------|--------|
| **Backend API** | 8000 | ✅ Used |
| **Frontend Dev** | 3000 | ✅ Used |
| **PostgreSQL** | 5432 | ⚠️ For production |
| **Redis** | 6379 | ❌ NOT USED |

---

## 📁 File Storage

| Property | Value |
|----------|-------|
| **Upload Directory** | `./uploads/` |
| **Max File Size** | 100 MB |
| **Supported Formats** | .csv, .xlsx, .xls |

---

## 🔧 AWS Services ACTUALLY NEEDED

### Required ✅

| AWS Service | Purpose | Configuration |
|-------------|---------|---------------|
| **ECS Fargate** or **EC2** | Backend hosting | 0.5-1 vCPU, 1-2GB RAM |
| **RDS PostgreSQL** | Database | db.t3.small, PostgreSQL 15+ |
| **S3** | Frontend + Uploads | 2 buckets |
| **CloudFront** | CDN for frontend | Standard |
| **ALB** | Load balancer | HTTPS |
| **ACM** | SSL certificates | Free |
| **Secrets Manager** | API keys | 2-3 secrets |

### NOT Required ❌

| AWS Service | Reason |
|-------------|--------|
| **ElastiCache Redis** | Redis not used in codebase |
| **ElasticSearch** | Not used |
| **Lambda** | Not needed |

---

## 📋 Environment Variables ACTUALLY NEEDED

```env
# Application
ENVIRONMENT=production
DEBUG=false

# Database - Sales Analytics (PostgreSQL) - ALREADY USING
ANALYTICS_DB_URL=postgresql+asyncpg://user:password@rds-endpoint:5432/analytics-llm

# Database - App Metadata (migrate SQLite to PostgreSQL for production)
DATABASE_URL=postgresql+asyncpg://user:password@rds-endpoint:5432/analytics_studio

# OpenAI (REQUIRED - actually used)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=<generate-secure-key>

# Query Limits
MAX_QUERY_ROWS=100000
QUERY_TIMEOUT_SECONDS=300

# Logging
LOG_LEVEL=INFO
```

### NOT NEEDED:
```env
# Redis - NOT USED
# REDIS_URL=...
# REDIS_HOST=...
```

---

## 🐳 Docker Configuration

### Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (for build)

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Output in /app/dist - copy to S3
```

---

## 💰 Simplified AWS Cost Estimate

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| CloudFront | 100GB transfer | $10-15 |
| S3 (2 buckets) | 50GB total | $5-10 |
| ALB | Standard | $20 |
| ECS Fargate | 2 tasks (0.5 vCPU, 1GB) | $35-50 |
| RDS PostgreSQL | db.t3.small | $30-40 |
| Secrets Manager | 3 secrets | $2 |
| **TOTAL** | | **~$100-140/month** |

### Savings vs Original Estimate:
- ❌ No ElastiCache Redis: **Save $15-30/month**

---

## ✅ Summary for Cloud Team

### Deploy These:
1. ✅ **ECS Fargate** with Python 3.12 container
2. ✅ **RDS PostgreSQL 15+** (ALREADY using PostgreSQL for sales data)
3. ✅ **S3** for frontend static files
4. ✅ **S3** for file uploads
5. ✅ **CloudFront** CDN
6. ✅ **ALB** with HTTPS
7. ✅ **Secrets Manager** for OPENAI_API_KEY, DB credentials

### Database Migration Notes:
- **Sales Data**: Already on PostgreSQL (`analytics-llm`) - just point to RDS
- **App Metadata**: Currently SQLite - migrate to RDS PostgreSQL

### Do NOT Deploy:
1. ❌ **ElastiCache Redis** - not used
2. ❌ **MySQL/Aurora MySQL** - using PostgreSQL

---

**Document Version:** 1.0.0  
**Verified Date:** February 2026  
**Verified By:** Codebase analysis

