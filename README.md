# Analytics Studio

> **Production-grade Analytics Platform** - A modular, extensible analytics platform inspired by Power BI but simplified.

Built with FastAPI, SQLAlchemy, and modern Python best practices. Designed for teams who need a powerful, maintainable analytics solution.

## 🎯 Features

- **Semantic Layer**: Column-centric JSON definitions for dimensions, measures, and aggregations
- **Dataset Management**: Register and version datasets with metadata tracking
- **Calculation Engine**: DSL-based calculated measures with validation
- **Query Engine**: Automatic SQL generation with optimization
- **Time Intelligence**: Period comparisons, rolling windows, YTD/MTD calculations
- **Visualization Layer**: Support for KPI cards, charts, tables with validation
- **Dashboard Composition**: Grid-based layouts with cross-filtering
- **RBAC**: Role-based access control with granular permissions
- **Changelog**: Complete audit trail for all changes
- **Production Ready**: Error handling, logging, database migrations, type hints

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 12+ (for production)
- `uv` package manager (recommended) or `pip`

### Install uv

```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
```

### 2. Database Setup

```bash
# Create database
createdb analytics_studio

# Run migrations (after setting up Alembic)
alembic upgrade head
```

### 3. Run the Application

```bash
# Development mode
uv run uvicorn main:app --reload

# Production mode
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API**: http://127.0.0.1:8000
- **Interactive API Docs (Swagger UI)**: http://127.0.0.1:8000/docs
- **Alternative API Docs (ReDoc)**: http://127.0.0.1:8000/redoc

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── api/                    # API routes
│   │   ├── v1/                 # API v1 endpoints
│   │   │   ├── datasets.py     # Dataset management
│   │   │   ├── semantic.py     # Semantic layer
│   │   │   ├── calculations.py # Calculation engine
│   │   │   ├── dashboards.py   # Dashboard management
│   │   │   ├── query.py        # Query execution
│   │   │   └── changelog.py    # Changelog API
│   │   └── exception_handlers.py
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Settings management
│   │   ├── database.py        # Database connection
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── logging_config.py  # Logging setup
│   │   └── dependencies.py    # FastAPI dependencies
│   ├── models/                 # Database models
│   │   ├── dataset.py         # Dataset models
│   │   ├── semantic.py        # Semantic layer models
│   │   ├── calculation.py     # Calculation models
│   │   ├── dashboard.py       # Dashboard models
│   │   ├── changelog.py       # Changelog model
│   │   └── user.py            # User/Role/Permission models
│   └── services/               # Business logic
│       ├── dataset_service.py
│       ├── semantic_service.py
│       ├── calculation_engine.py
│       ├── query_engine.py
│       ├── time_intelligence.py
│       ├── visualization_service.py
│       ├── dashboard_service.py
│       ├── rbac_service.py
│       └── changelog_service.py
├── alembic/                    # Database migrations
├── main.py                     # FastAPI application entry point
├── pyproject.toml             # Dependencies and project config
├── alembic.ini                # Alembic configuration
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🏗️ Architecture

### Core Modules

1. **Dataset Service** (`app/services/dataset_service.py`)
   - Register and manage datasets
   - Version tracking
   - Metadata management

2. **Semantic Service** (`app/services/semantic_service.py`)
   - Parse and validate semantic JSON
   - Convert to UI-selectable fields
   - Field usage validation

3. **Calculation Engine** (`app/services/calculation_engine.py`)
   - DSL formula parsing
   - Validation (prevents nested aggregations)
   - Execution with error handling

4. **Query Engine** (`app/services/query_engine.py`)
   - SQL generation from visual configs
   - Query optimization
   - Safe execution with timeouts

5. **Time Intelligence** (`app/services/time_intelligence.py`)
   - Period comparisons (previous period, same period last year)
   - Rolling windows (7, 30, 90 days)
   - YTD/MTD calculations

6. **Visualization Service** (`app/services/visualization_service.py`)
   - Visual configuration validation
   - Support for KPI, charts, tables

7. **Dashboard Service** (`app/services/dashboard_service.py`)
   - Dashboard composition
   - Grid-based layouts
   - Visual management

8. **RBAC Service** (`app/services/rbac_service.py`)
   - Role-based permissions
   - Resource access control

9. **Changelog Service** (`app/services/changelog_service.py`)
   - Change tracking
   - Entity history

## 📚 API Endpoints

### Datasets
- `GET /api/v1/datasets` - List datasets
- `GET /api/v1/datasets/{id}` - Get dataset
- `POST /api/v1/datasets` - Create dataset
- `PATCH /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Deprecate dataset

### Semantic Layer
- `POST /api/v1/semantic/validate` - Validate semantic schema
- `POST /api/v1/semantic/parse` - Parse semantic to UI fields
- `POST /api/v1/semantic/validate-field` - Validate field usage

### Calculations
- `POST /api/v1/calculations/validate` - Validate formula
- `POST /api/v1/calculations/parse` - Parse formula
- `POST /api/v1/calculations/check-division-by-zero` - Check for division by zero

### Dashboards
- `GET /api/v1/dashboards` - List dashboards
- `GET /api/v1/dashboards/{id}` - Get dashboard
- `POST /api/v1/dashboards` - Create dashboard
- `PATCH /api/v1/dashboards/{id}` - Update dashboard

### Query Execution
- `POST /api/v1/query/execute` - Execute analytics query

### Changelog
- `GET /api/v1/changelog` - Get changelog entries
- `GET /api/v1/changelog/entity/{type}/{id}` - Get entity history

## 🔧 Configuration

Configuration is managed through environment variables (see `.env.example`):

- **Database**: PostgreSQL connection settings
- **Security**: JWT secret key, token expiration
- **Caching**: Redis configuration (optional)
- **Query Limits**: Max rows, timeout settings
- **Logging**: Log level and format

## 🧪 Development

### Adding Dependencies

```bash
uv add <package-name>
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

The project follows Python best practices:
- Type hints throughout
- Pydantic models for validation
- Async/await for database operations
- Comprehensive error handling
- Structured logging

## 🔒 Security

- **Authentication**: JWT-based (to be implemented)
- **Authorization**: RBAC with role-based permissions
- **Input Validation**: Pydantic models and custom validators
- **SQL Injection**: Parameterized queries via SQLAlchemy
- **Error Handling**: No sensitive data in error messages

## 📝 Semantic Layer Schema

Example semantic layer JSON:

```json
{
  "grain": "daily",
  "time_columns": ["date", "created_at"],
  "dimensions": [
    {
      "name": "region",
      "column": "region_name",
      "type": "string",
      "description": "Geographic region"
    }
  ],
  "measures": [
    {
      "name": "revenue",
      "column": "amount",
      "type": "numeric",
      "aggregations": ["SUM", "AVG", "MIN", "MAX"],
      "format": "currency"
    }
  ]
}
```

## 🚦 Status

This is a **production-ready foundation** with:
- ✅ Complete modular architecture
- ✅ All core services implemented
- ✅ Database models and migrations
- ✅ API endpoints
- ✅ Error handling and logging
- ⚠️ Authentication (mock implementation - needs JWT)
- ⚠️ Redis caching (optional - not required)
- ⚠️ Tests (to be added)

## 📖 Documentation

- **API Documentation**: Available at `/docs` when running
- **Architecture**: See `analytics-studio-cursor-prompts.md` for detailed architecture prompts
- **Code**: Comprehensive docstrings and type hints

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Include docstrings
4. Update changelog for significant changes
5. Test your changes

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

Built following best practices from:
- FastAPI documentation
- SQLAlchemy async patterns
- Domain-driven design principles

---

**Built with ❤️ for teams who need powerful, maintainable analytics**







task 1 : make filters working
2 : take flate table cvs format from database 
3 : configure it in dashboard project
4 : apply llm model on that dasboard where we can query and get live data info





cd /home/avaxpro16/Desktop/V1 && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

npm run dev




cd /home/avaxpro16/Desktop/V1 && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000




$ cd /home/avaxpro16/Desktop/V1 && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000






   

def merge_sorted_array(a, b):
   i,j=0,0
   result = []

   while i < len(a) and j < len(b):
      if a[i] <= b[j]:
         result.append(a[i])
         i+=1
      else:
         result.append(b[j])
         j+=1

   while i < len(a):
      result.append(a[i])

   while j < len(b):
      result.append(b[j])

   return result

   🐍 Backend Requirements
Component	Version
Python	>=3.11
FastAPI	0.128.0
SQLAlchemy	2.0.46
Uvicorn	0.24.0+


⚛️ Frontend Requirements
Component	Version
Node.js	>=18.x (20.x preferred)
React	18.2.0
TypeScript	5.2.2
Vite	5.0.8
TailwindCSS	3.3.6

🗄️ Database & Cache
Component	Version
PostgreSQL	12+ (15+ recommended)
Redis	6.x+ (7.x recommended)

🤖 External Services
Service	Details
OpenAI API	gpt-4o-mini model

🌐 Ports
Service	Port
Backend API	8000
Frontend Dev	3000
PostgreSQL	5432
Redis	6379

🐳 Docker Base Images
Purpose	Image
Backend	python:3.11-slim
Frontend Build	node:20-alpine

//
