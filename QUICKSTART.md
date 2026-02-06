# Quick Start Guide for New Engineers

Welcome to Analytics Studio! This guide will help you get up and running quickly.

## 🎯 What is Analytics Studio?

Analytics Studio is a production-grade analytics platform that allows users to:
- Register datasets (wide analytics tables)
- Define semantic layers (dimensions, measures, aggregations)
- Create calculated measures using a DSL
- Build dashboards with various visualizations
- Execute queries without writing SQL

## 🏗️ Architecture Overview

The system is organized into clear layers:

```
API Layer (app/api/)          → HTTP endpoints, validation
    ↓
Service Layer (app/services/) → Business logic
    ↓
Model Layer (app/models/)      → Database models
    ↓
Core Layer (app/core/)        → Configuration, database, logging
```

## 📝 Key Concepts

### 1. Datasets
A dataset represents a table in your database. It has:
- Metadata (name, description, grain)
- Versioning
- Linked semantic definitions

### 2. Semantic Layer
A JSON schema that defines:
- **Dimensions**: Categorical fields (e.g., region, product)
- **Measures**: Numeric fields with allowed aggregations (e.g., SUM, AVG)
- **Time columns**: Date/time fields for time intelligence
- **Grain**: Data granularity (daily, hourly, etc.)

### 3. Calculated Measures
User-defined formulas using a DSL:
- Supports arithmetic: `revenue - cost`
- Supports aggregations: `SUM(revenue)`
- Supports conditionals: `IF(region = 'US', revenue, 0)`

### 4. Dashboards
Compositions of visuals:
- KPI cards
- Charts (line, bar, column)
- Tables
- Grid-based layouts

## 🚀 Getting Started

### Step 1: Setup Environment

```bash
# Install dependencies
uv sync

# Copy and edit environment file
cp .env.example .env
# Edit .env with your database credentials
```

### Step 2: Database Setup

```bash
# Create database
createdb analytics_studio

# Run migrations
alembic upgrade head
```

### Step 3: Run the Application

```bash
uv run uvicorn main:app --reload
```

Visit http://localhost:8000/docs to see the API documentation.

## 📚 Common Tasks

### Task 1: Register a Dataset

```python
# Via API (POST /api/v1/datasets)
{
  "id": "sales_data",
  "name": "Sales Data",
  "table_name": "sales_fact",
  "grain": "daily",
  "description": "Daily sales transactions"
}
```

### Task 2: Define Semantic Layer

```python
# Via API (POST /api/v1/semantic/validate)
{
  "schema_json": {
    "grain": "daily",
    "time_columns": ["sale_date"],
    "dimensions": [
      {
        "name": "region",
        "column": "region_name",
        "type": "string"
      }
    ],
    "measures": [
      {
        "name": "revenue",
        "column": "amount",
        "type": "numeric",
        "aggregations": ["SUM", "AVG", "MIN", "MAX"]
      }
    ]
  }
}
```

### Task 3: Execute a Query

```python
# Via API (POST /api/v1/query/execute)
{
  "dataset_id": "sales_data",
  "dimensions": ["region"],
  "measures": [
    {
      "name": "revenue",
      "column": "amount",
      "aggregation": "SUM",
      "alias": "total_revenue"
    }
  ],
  "filters": [
    {
      "column": "region",
      "operator": "=",
      "value": "North America"
    }
  ],
  "limit": 100
}
```

## 🔍 Understanding the Codebase

### Where to Start?

1. **API Endpoints**: `app/api/v1/` - See what the system can do
2. **Services**: `app/services/` - Understand business logic
3. **Models**: `app/models/` - Understand data structure
4. **Core**: `app/core/` - Configuration and setup

### Reading Code Flow

Example: Understanding how a query is executed

1. **API Entry**: `app/api/v1/query.py` → `execute_query()`
2. **Service**: `app/services/query_engine.py` → `build_query()`, `execute_query()`
3. **Validation**: `app/services/semantic_service.py` → `validate_field_usage()`
4. **Database**: `app/core/database.py` → `get_db()`

### Adding a Feature

Example: Adding a new visual type "heatmap"

1. **Update Service**: `app/services/visualization_service.py`
   ```python
   VALID_VISUAL_TYPES = ["kpi", "line", "bar", "heatmap"]
   ```

2. **Add Validation**: Update `validate_visual_config()`

3. **Update Query Engine**: If heatmap needs special SQL

4. **Test**: Use `/docs` to test the new visual type

## 🐛 Debugging

### Check Logs
Logs are structured JSON in production. Look for:
- Error codes
- Stack traces
- Request IDs

### Use API Docs
The `/docs` endpoint is your best friend:
- Test endpoints interactively
- See request/response schemas
- Understand validation rules

### Database State
```python
# In Python shell
from app.core.database import AsyncSessionLocal
from app.models.dataset import Dataset

async with AsyncSessionLocal() as session:
    datasets = await session.execute(select(Dataset))
    print(datasets.scalars().all())
```

## 📖 Key Files to Understand

1. **`main.py`**: Application entry point, middleware setup
2. **`app/core/config.py`**: All configuration options
3. **`app/services/query_engine.py`**: How SQL is generated
4. **`app/services/calculation_engine.py`**: How formulas are parsed
5. **`app/models/dataset.py`**: Dataset data model

## 🎓 Learning Path

### Week 1: Understanding
- Read `ARCHITECTURE.md`
- Explore API docs
- Review service implementations

### Week 2: Making Changes
- Fix a small bug
- Add a validation rule
- Extend a service method

### Week 3: Adding Features
- Add a new visual type
- Implement a new calculation function
- Add a new time comparison

## 💡 Tips

1. **Type Hints**: Use them! They help IDE autocomplete
2. **Docstrings**: Read them for function documentation
3. **Pydantic Models**: They define API contracts
4. **Service Pattern**: Services are stateless, easy to test
5. **Error Handling**: Check `app/core/exceptions.py` for error types

## ❓ Common Questions

**Q: Where do I add business logic?**
A: In `app/services/` - each service handles one domain

**Q: How do I add a new API endpoint?**
A: Add route in `app/api/v1/`, add service method if needed

**Q: How do I change the database schema?**
A: Create Alembic migration: `alembic revision --autogenerate -m "description"`

**Q: How do I add authentication?**
A: Update `app/core/dependencies.py` → `get_current_user()`

**Q: Where are tests?**
A: To be added - follow FastAPI testing patterns

## 🚨 Important Notes

- **Never write raw SQL** - Use SQLAlchemy or QueryEngine
- **Always validate inputs** - Use Pydantic models
- **Handle errors gracefully** - Use custom exceptions
- **Log important events** - Use structured logging
- **Follow type hints** - They catch bugs early

## 📚 Additional Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Pydantic: https://docs.pydantic.dev

---

**Happy coding! 🎉**


