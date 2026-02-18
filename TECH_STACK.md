# 📋 Analytics Studio - Technology Stack & AWS Requirements

> **For Cloud Team** - Complete list of technologies, versions, and configurations required for AWS deployment

---

## 🎯 Project Overview

| Property | Value |
|----------|-------|
| **Project Name** | Analytics Studio |
| **Version** | 0.1.0 |
| **Type** | Full-Stack Analytics Platform |
| **Architecture** | Monorepo (Backend + Frontend) |

---

## 🐍 Backend Stack

### Python Runtime

| Component | Version | Notes |
|-----------|---------|-------|
| **Python** | **>=3.11** | Required (uses modern type hints) |
| **Package Manager** | uv | Alternative: pip |

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | 0.128.0 | Web framework (async) |
| **Uvicorn** | 0.24.0+ | ASGI server |
| **Starlette** | 0.50.0 | ASGI toolkit (FastAPI dependency) |
| **Pydantic** | 2.12.5 | Data validation |
| **Pydantic-Settings** | 2.12.0 | Environment configuration |

### Database & ORM

| Package | Version | Purpose |
|---------|---------|---------|
| **SQLAlchemy** | 2.0.46 | ORM (async mode) |
| **Alembic** | 1.18.1 | Database migrations |
| **asyncpg** | 0.31.0 | PostgreSQL async driver |
| **aiosqlite** | 0.22.1 | SQLite async driver (dev) |
| **aiomysql** | 0.3.2 | MySQL async driver (optional) |
| **psycopg2-binary** | 2.9.11 | PostgreSQL sync driver |

### Caching

| Package | Version | Purpose |
|---------|---------|---------|
| **Redis** | 7.1.0 | Cache client library |

### Authentication & Security

| Package | Version | Purpose |
|---------|---------|---------|
| **python-jose** | 3.5.0 | JWT tokens |
| **passlib** | 1.7.4 | Password hashing |
| **bcrypt** | 5.0.0 | Bcrypt algorithm |
| **cryptography** | 46.0.3 | Cryptographic operations |

### File Processing

| Package | Version | Purpose |
|---------|---------|---------|
| **python-multipart** | 0.0.21 | File uploads |
| **openpyxl** | 3.1.5 | Excel file processing |

### AI/LLM Integration

| Package | Version | Purpose |
|---------|---------|---------|
| **OpenAI** | 2.17.0 | OpenAI API client |

### Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| **python-dotenv** | 1.2.1 | Environment variables |
| **httpx** | 0.28.1 | HTTP client |
| **PyYAML** | 6.0.3 | YAML parsing |
| **tqdm** | 4.67.3 | Progress bars |

---

## ⚛️ Frontend Stack

### Node.js Runtime

| Component | Version | Notes |
|-----------|---------|-------|
| **Node.js** | **>=18.x** | LTS recommended (20.x preferred) |
| **npm** | >=9.x | Package manager |

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| **React** | 18.2.0 | UI framework |
| **React DOM** | 18.2.0 | React DOM renderer |
| **React Router DOM** | 6.20.0 | Client-side routing |
| **TypeScript** | 5.2.2 | Type safety |

### Build Tools

| Package | Version | Purpose |
|---------|---------|---------|
| **Vite** | 5.0.8 | Build tool & dev server |
| **@vitejs/plugin-react** | 4.2.1 | React plugin for Vite |
| **PostCSS** | 8.4.32 | CSS processing |
| **Autoprefixer** | 10.4.16 | CSS vendor prefixes |

### Styling

| Package | Version | Purpose |
|---------|---------|---------|
| **TailwindCSS** | 3.3.6 | Utility-first CSS |
| **tailwind-merge** | 2.1.0 | Tailwind class merging |
| **clsx** | 2.0.0 | Conditional classes |

### State Management & Data Fetching

| Package | Version | Purpose |
|---------|---------|---------|
| **Zustand** | 4.4.7 | State management |
| **React Query** | 3.39.3 | Server state management |
| **Axios** | 1.6.2 | HTTP client |

### UI Components

| Package | Version | Purpose |
|---------|---------|---------|
| **Lucide React** | 0.294.0 | Icons |
| **React DnD** | 16.0.1 | Drag and drop |
| **React DnD HTML5 Backend** | 16.0.1 | DnD HTML5 backend |

### Code Quality

| Package | Version | Purpose |
|---------|---------|---------|
| **ESLint** | 8.55.0 | Linting |
| **@typescript-eslint/eslint-plugin** | 6.14.0 | TypeScript ESLint |
| **@typescript-eslint/parser** | 6.14.0 | TypeScript parser |

---

## 🗄️ Database Requirements

### Primary Database (Production)

| Component | Version | Notes |
|-----------|---------|-------|
| **PostgreSQL** | **12+** | Recommended: 15+ |
| **Connection** | asyncpg | Async driver |
| **Default Port** | 5432 | |

### Development Database

| Component | Version | Notes |
|-----------|---------|-------|
| **SQLite** | 3.x | For local development |

### Optional Databases

| Component | Version | Notes |
|-----------|---------|-------|
| **MySQL** | 8.0+ | Supported via aiomysql |

---

## 🔴 Cache Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Redis** | **6.x+** | Recommended: 7.x |
| **Default Port** | 6379 | |
| **Purpose** | Query caching, session storage |

---

## 🤖 External Services

### OpenAI API

| Component | Details |
|-----------|---------|
| **Service** | OpenAI API |
| **Models Used** | gpt-4o-mini (default), gpt-4o |
| **Purpose** | SQL generation, answer formatting |
| **Required** | OPENAI_API_KEY environment variable |

---

## 🌐 Network & Ports

| Service | Port | Protocol |
|---------|------|----------|
| **Backend API** | 8000 | HTTP/HTTPS |
| **Frontend Dev Server** | 3000 | HTTP |
| **PostgreSQL** | 5432 | TCP |
| **Redis** | 6379 | TCP |

---

## 📁 File Storage

| Requirement | Details |
|-------------|---------|
| **Upload Directory** | `/uploads/` |
| **Max File Size** | 100 MB |
| **Allowed Types** | .csv, .xlsx, .xls |
| **AWS Service** | S3 (recommended) |

---

## 🔧 AWS Service Requirements

### Compute

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **ECS Fargate** | 0.5 vCPU, 1GB RAM per task | Backend containers |
| **OR EC2** | t3.small/medium | Alternative to Fargate |

### Database

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **RDS PostgreSQL** | db.t3.small, 20GB GP3 | Primary database |
| **Version** | PostgreSQL 15+ | |

### Caching

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **ElastiCache Redis** | cache.t3.micro | Query caching |
| **Version** | Redis 7.x | |

### Storage

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **S3** | Standard storage | Frontend hosting + file uploads |
| **Buckets** | 2 buckets | `*-frontend`, `*-uploads` |

### Networking

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **ALB** | Application Load Balancer | API traffic |
| **CloudFront** | CDN distribution | Frontend delivery |
| **Route 53** | DNS | Domain management |
| **ACM** | SSL/TLS certificates | HTTPS |

### Security

| AWS Service | Configuration | Purpose |
|-------------|---------------|---------|
| **Secrets Manager** | 4+ secrets | API keys, DB credentials |
| **WAF** | Optional | Web application firewall |
| **VPC** | Private subnets | Network isolation |

---

## 📋 Environment Variables

### Required Variables

```env
# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=Analytics Studio
APP_VERSION=0.1.0

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/analytics_studio
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://host:6379/0
CACHE_TTL=3600

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Query Limits
MAX_QUERY_ROWS=100000
QUERY_TIMEOUT_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 🐳 Docker Requirements

### Base Images

| Image | Version | Purpose |
|-------|---------|---------|
| **python** | 3.11-slim | Backend container |
| **node** | 20-alpine | Frontend build |

### Sample Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📊 Resource Recommendations

### Development Environment

| Resource | Specification |
|----------|---------------|
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Storage** | 20 GB |

### Production Environment (Small)

| Resource | Specification |
|----------|---------------|
| **Backend (per task)** | 0.5 vCPU, 1 GB RAM |
| **Tasks** | 2-4 |
| **Database** | db.t3.small (2 vCPU, 2GB RAM) |
| **Redis** | cache.t3.micro |

### Production Environment (Medium)

| Resource | Specification |
|----------|---------------|
| **Backend (per task)** | 1 vCPU, 2 GB RAM |
| **Tasks** | 4-8 |
| **Database** | db.t3.medium (2 vCPU, 4GB RAM) |
| **Redis** | cache.t3.small |

---

## ✅ Pre-Deployment Checklist

### Infrastructure
- [ ] VPC with public/private subnets created
- [ ] Security groups configured
- [ ] RDS PostgreSQL instance running
- [ ] ElastiCache Redis cluster running
- [ ] S3 buckets created (frontend + uploads)
- [ ] ECR repository created
- [ ] ALB configured with HTTPS
- [ ] CloudFront distribution created
- [ ] Route 53 DNS configured
- [ ] ACM certificates issued

### Secrets
- [ ] Database URL stored in Secrets Manager
- [ ] OpenAI API key stored in Secrets Manager
- [ ] JWT secret key generated and stored
- [ ] Redis URL configured

### Application
- [ ] Docker image built and pushed to ECR
- [ ] ECS task definition created
- [ ] ECS service running
- [ ] Frontend built and uploaded to S3
- [ ] CloudFront cache invalidated

### Verification
- [ ] Health check endpoint responding (`/health`)
- [ ] API docs accessible (`/docs`)
- [ ] Frontend loading correctly
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] OpenAI integration working

---

## 📞 Support Contacts

| Role | Contact |
|------|---------|
| **Development Team** | [Your team contact] |
| **DevOps/Cloud Team** | [Cloud team contact] |

---

**Document Version:** 1.0.0  
**Last Updated:** February 2026  
**Project Repository:** [Your repo URL]

