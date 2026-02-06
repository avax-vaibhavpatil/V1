# Analytics Studio - Architecture Documentation

## Overview

Analytics Studio is a modular, production-grade analytics platform designed for extensibility and maintainability. This document explains the architecture, design decisions, and how new engineers can understand and extend the system.

## Design Principles

1. **Modularity**: Each service is independent and can be tested/modified in isolation
2. **Type Safety**: Comprehensive type hints for better IDE support and fewer bugs
3. **Async First**: All I/O operations are async for better performance
4. **Validation First**: Input validation at API boundaries and service layers
5. **Error Handling**: Custom exceptions with clear error messages
6. **Extensibility**: Easy to add new visual types, calculations, or features

## Architecture Layers

### 1. API Layer (`app/api/`)

**Responsibility**: HTTP request/response handling, input validation, authentication

- **Routes**: Organized by feature (datasets, semantic, calculations, etc.)
- **Pydantic Models**: Request/response validation
- **Dependencies**: Authentication, database sessions, permissions
- **Exception Handlers**: Global error handling

**Key Files**:
- `app/api/v1/datasets.py` - Dataset CRUD operations
- `app/api/v1/query.py` - Query execution endpoint
- `app/api/exception_handlers.py` - Global exception handling

### 2. Service Layer (`app/services/`)

**Responsibility**: Business logic, orchestration, validation

Each service is a stateless class with static methods (can be instantiated if needed for dependency injection).

**Services**:

- **DatasetService**: Dataset lifecycle management
- **SemanticService**: Semantic layer parsing and validation
- **CalculationEngine**: Formula parsing, validation, execution
- **QueryEngine**: SQL generation and execution
- **TimeIntelligenceEngine**: Time-based calculations
- **VisualizationService**: Visual configuration validation
- **DashboardService**: Dashboard composition
- **RBACService**: Permission checking
- **ChangelogService**: Change tracking

### 3. Model Layer (`app/models/`)

**Responsibility**: Database schema, relationships

- SQLAlchemy async models
- Relationships defined for easy querying
- Versioning support for datasets, semantic definitions, measures

**Key Models**:
- `Dataset` - Dataset metadata
- `SemanticDefinition` / `SemanticVersion` - Semantic layer versions
- `CalculatedMeasure` / `MeasureVersion` - Calculated measures with versioning
- `Dashboard` / `DashboardVisual` - Dashboard composition
- `Changelog` - Audit trail
- `User` / `Role` / `Permission` - RBAC

### 4. Core Layer (`app/core/`)

**Responsibility**: Configuration, database, logging, dependencies

- **config.py**: Settings management with Pydantic Settings
- **database.py**: SQLAlchemy async engine and session management
- **exceptions.py**: Custom exception hierarchy
- **logging_config.py**: Structured logging setup
- **dependencies.py**: FastAPI dependencies (auth, DB sessions)

## Data Flow

### Query Execution Flow

```
1. API Request (POST /api/v1/query/execute)
   ↓
2. Pydantic Validation (QueryRequest model)
   ↓
3. DatasetService.get_dataset_or_raise()
   ↓
4. QueryEngine.build_query()
   - Validates against semantic schema
   - Generates SQL
   ↓
5. QueryEngine.optimize_query()
   ↓
6. QueryEngine.execute_query()
   ↓
7. Return results
```

### Dashboard Creation Flow

```
1. API Request (POST /api/v1/dashboards)
   ↓
2. Pydantic Validation (DashboardCreate model)
   ↓
3. DashboardService.create_dashboard()
   ↓
4. For each visual:
   - VisualizationService.validate_visual_config()
   - Validate against semantic schema (if provided)
   ↓
5. Create Dashboard and DashboardVisual records
   ↓
6. ChangelogService.create_changelog_entry()
   ↓
7. Commit transaction
```

## Key Design Patterns

### 1. Service Pattern

Services are stateless classes with static methods. This makes them:
- Easy to test (no state to mock)
- Easy to use (no instantiation needed)
- Thread-safe

Example:
```python
dataset = await DatasetService.get_dataset(session, dataset_id)
```

### 2. Repository Pattern (via Services)

Services act as repositories, abstracting database access:
- `get_dataset()` - Find by ID
- `list_datasets()` - Query with filters
- `create_dataset()` - Create with validation

### 3. Validation Chain

Validation happens at multiple levels:
1. **API**: Pydantic models validate request structure
2. **Service**: Business logic validation (e.g., semantic schema validation)
3. **Database**: Constraints and foreign keys

### 4. Error Handling

Custom exception hierarchy:
- `AnalyticsStudioException` - Base exception
- `ValidationError` - Input validation failures
- `DatasetNotFoundError` - Resource not found
- `CalculationError` - Formula errors
- `QueryExecutionError` - Query failures

All exceptions are caught by global handlers and return consistent JSON responses.

## Extending the System

### Adding a New Visual Type

1. **Update VisualizationService**:
   ```python
   VALID_VISUAL_TYPES = ["kpi", "line", "bar", "new_type"]
   ```

2. **Add validation logic** in `validate_visual_config()`

3. **Update QueryEngine** if new visual requires special SQL generation

### Adding a New Calculation Function

1. **Update CalculationEngine**:
   ```python
   FUNCTIONS = ["SUM", "AVG", "COUNT", "NEW_FUNCTION"]
   ```

2. **Add parsing logic** in `parse_formula()`

3. **Add execution logic** in `execute_calculation()`

### Adding a New Time Comparison

1. **Update TimeComparison enum**:
   ```python
   class TimeComparison(str, Enum):
       NEW_COMPARISON = "new_comparison"
   ```

2. **Implement logic** in `calculate_time_range()`

3. **Update query generation** if needed

## Database Design

### Versioning Strategy

- **Datasets**: Tracked via `DatasetVersion` table
- **Semantic Definitions**: Versioned in `SemanticVersion` with JSON schema
- **Calculated Measures**: Versioned in `MeasureVersion` with formula history

### Relationships

- Dataset → SemanticDefinition (one-to-many)
- Dataset → CalculatedMeasure (one-to-many)
- Dashboard → DashboardVisual (one-to-many)
- User → Role (many-to-many)
- Role → Permission (many-to-many)

### Soft Deletes

Most entities use `is_active` flag for soft deletes, preserving history.

## Security Considerations

1. **Input Validation**: All inputs validated via Pydantic
2. **SQL Injection**: Prevented by SQLAlchemy parameterized queries
3. **Authorization**: RBAC enforced at API and service layers
4. **Error Messages**: No sensitive data exposed in errors

## Performance Considerations

1. **Connection Pooling**: Configured in `database.py`
2. **Query Optimization**: Basic optimization in `QueryEngine.optimize_query()`
3. **Async Operations**: All database operations are async
4. **Caching**: Redis support configured (optional)

## Testing Strategy (To Be Implemented)

1. **Unit Tests**: Test services in isolation
2. **Integration Tests**: Test API endpoints with test database
3. **Calculation Tests**: Validate formula parsing and execution
4. **Query Tests**: Verify SQL generation correctness

## Migration Path

When adding new features:

1. Create database migration (Alembic)
2. Update models if needed
3. Add service methods
4. Add API endpoints
5. Update documentation
6. Add tests

## Common Tasks for New Engineers

### Understanding a Feature

1. Start with the API endpoint (`app/api/v1/`)
2. Follow to the service (`app/services/`)
3. Check the models (`app/models/`)
4. Review tests (when available)

### Adding a Feature

1. Design the data model
2. Create migration
3. Add service methods
4. Add API endpoint
5. Test manually via `/docs`
6. Write tests

### Debugging

1. Check logs (structured JSON in production)
2. Use API docs to test endpoints
3. Check database state
4. Review changelog for recent changes

## Questions?

- Check API docs at `/docs`
- Review service docstrings
- Check `analytics-studio-cursor-prompts.md` for architecture prompts


