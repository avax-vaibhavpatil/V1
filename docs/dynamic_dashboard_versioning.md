# Dynamic Dashboard Versioning from Backend

## 1. Problem Statement

### Why Multiple Dashboard Versions Are Needed

| Scenario | Requirement |
|----------|-------------|
| **Role-Based Views** | Sales managers see regional data; executives see company-wide data |
| **Geographic Customization** | North zone sees different KPIs than South zone |
| **Client White-Labeling** | Same dashboard, different branding per client |
| **A/B Testing** | Test new layouts with subset of users |
| **Seasonal Variants** | Quarterly reports vs annual reports |
| **Historical Snapshots** | View dashboard as it existed last quarter |
| **Progressive Rollout** | New features released to 10% of users first |

### Challenges with Duplicating Dashboards

| Challenge | Impact |
|-----------|--------|
| **Code Proliferation** | 10 user roles × 5 regions = 50 separate dashboards |
| **Maintenance Nightmare** | Bug fix must be applied to all 50 copies |
| **Inconsistent Updates** | Some copies get updates, others don't |
| **Testing Complexity** | Each copy needs separate QA |
| **Deployment Risk** | More code = more potential failures |
| **Storage Overhead** | Duplicate configs waste database space |
| **Cognitive Load** | Developers must track which version is where |

---

## 2. Concept of a Dashboard Template

### Base Dashboard Definition

A **Dashboard Template** is the canonical definition that serves as the foundation for all versions:

```typescript
interface DashboardTemplate {
  // Identity
  templateId: string;           // e.g., "sales-performance"
  templateName: string;         // "Sales Performance Dashboard"
  templateDescription: string;
  
  // Base configuration (complete default)
  baseConfig: ReportConfig;
  
  // Metadata
  createdAt: string;
  createdBy: string;
  lastModified: string;
  
  // Versioning
  schemaVersion: string;        // "2.1.0"
  
  // Status
  status: 'active' | 'deprecated' | 'archived';
}
```

### Reusable Components

Templates are composed of **reusable component definitions**:

```typescript
// Filter presets that can be shared across templates
interface FilterPreset {
  presetId: string;
  presetName: string;
  filters: FilterConfig[];
}

// KPI card sets
interface KpiPreset {
  presetId: string;
  presetName: string;
  cards: KpiCardConfig[];
}

// Table column configurations
interface TablePreset {
  presetId: string;
  presetName: string;
  entityColumn: EntityColumnConfig;
  columnGroups: ColumnGroupConfig[];
}

// Format rule sets
interface FormatPreset {
  presetId: string;
  presetName: string;
  rules: FormatRules;
}
```

**Component Composition:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Template                       │
│  "sales-performance"                                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Filter    │  │    KPI      │  │    Table    │         │
│  │   Preset    │  │   Preset    │  │   Preset    │         │
│  │ "geo-basic" │  │ "category"  │  │ "full-grid" │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   Format    │  │  Drilldown  │                          │
│  │   Preset    │  │   Preset    │                          │
│  │  "indian"   │  │  "standard" │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Backend Architecture

### 3.1 Dashboard Definition Storage

**Database Schema:**

```sql
-- Dashboard Templates (canonical definitions)
CREATE TABLE dashboard_templates (
  template_id VARCHAR(64) PRIMARY KEY,
  template_name VARCHAR(255) NOT NULL,
  description TEXT,
  base_config JSONB NOT NULL,
  schema_version VARCHAR(20) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(64),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard Versions (published snapshots)
CREATE TABLE dashboard_versions (
  version_id SERIAL PRIMARY KEY,
  template_id VARCHAR(64) REFERENCES dashboard_templates(template_id),
  version_number VARCHAR(20) NOT NULL,
  config_snapshot JSONB NOT NULL,
  changelog TEXT[],
  status VARCHAR(20) DEFAULT 'draft',
  published_at TIMESTAMP,
  published_by VARCHAR(64),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(template_id, version_number)
);

-- Dashboard Overrides (user/role/tenant specific)
CREATE TABLE dashboard_overrides (
  override_id SERIAL PRIMARY KEY,
  template_id VARCHAR(64) REFERENCES dashboard_templates(template_id),
  scope_type VARCHAR(20) NOT NULL,  -- 'user', 'role', 'tenant', 'zone'
  scope_value VARCHAR(64) NOT NULL,
  override_config JSONB NOT NULL,   -- Partial config to merge
  priority INTEGER DEFAULT 0,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(template_id, scope_type, scope_value)
);

-- Reusable presets
CREATE TABLE config_presets (
  preset_id VARCHAR(64) PRIMARY KEY,
  preset_type VARCHAR(20) NOT NULL,  -- 'filter', 'kpi', 'table', 'format'
  preset_name VARCHAR(255) NOT NULL,
  preset_config JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Configuration Resolution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Configuration Resolution                       │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. FETCH BASE CONFIG                                             │
│    SELECT base_config FROM dashboard_templates                   │
│    WHERE template_id = :templateId AND status = 'active'         │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. FETCH APPLICABLE OVERRIDES                                    │
│    SELECT * FROM dashboard_overrides                             │
│    WHERE template_id = :templateId                               │
│      AND active = TRUE                                           │
│      AND (                                                       │
│        (scope_type = 'tenant' AND scope_value = :tenantId) OR    │
│        (scope_type = 'role' AND scope_value = :userRole) OR      │
│        (scope_type = 'user' AND scope_value = :userId) OR        │
│        (scope_type = 'zone' AND scope_value = :userZone)         │
│      )                                                           │
│    ORDER BY priority ASC                                         │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. MERGE CONFIGS (in priority order)                             │
│    finalConfig = deepMerge(baseConfig, ...overrides)             │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. APPLY PERMISSION FILTERS                                      │
│    - Remove filters user cannot access                           │
│    - Remove columns user cannot see                              │
│    - Disable features user doesn't have permission for           │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. RETURN RESOLVED CONFIG                                        │
│    { config: resolvedConfig, meta: { version, appliedOverrides }}│
└──────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import json

@dataclass
class ResolutionContext:
    template_id: str
    user_id: str
    user_role: str
    tenant_id: str
    user_zone: Optional[str] = None

async def resolve_dashboard_config(
    ctx: ResolutionContext,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Resolve the final dashboard configuration for a specific user context.
    """
    # 1. Fetch base config
    template = await db.execute(
        select(DashboardTemplate)
        .where(DashboardTemplate.template_id == ctx.template_id)
        .where(DashboardTemplate.status == 'active')
    )
    base_config = template.scalar_one().base_config
    
    # 2. Fetch applicable overrides
    overrides = await db.execute(
        select(DashboardOverride)
        .where(DashboardOverride.template_id == ctx.template_id)
        .where(DashboardOverride.active == True)
        .where(
            or_(
                and_(DashboardOverride.scope_type == 'tenant', 
                     DashboardOverride.scope_value == ctx.tenant_id),
                and_(DashboardOverride.scope_type == 'role', 
                     DashboardOverride.scope_value == ctx.user_role),
                and_(DashboardOverride.scope_type == 'user', 
                     DashboardOverride.scope_value == ctx.user_id),
                and_(DashboardOverride.scope_type == 'zone', 
                     DashboardOverride.scope_value == ctx.user_zone),
            )
        )
        .order_by(DashboardOverride.priority.asc())
    )
    
    # 3. Merge configs
    final_config = deep_merge(base_config, *[o.override_config for o in overrides])
    
    # 4. Apply permission filters
    final_config = apply_permission_filters(final_config, ctx)
    
    # 5. Return with metadata
    return {
        "config": final_config,
        "meta": {
            "templateId": ctx.template_id,
            "resolvedAt": datetime.utcnow().isoformat(),
            "appliedOverrides": [o.override_id for o in overrides],
        }
    }

def deep_merge(base: Dict, *overrides: Dict) -> Dict:
    """Recursively merge override configs into base."""
    result = copy.deepcopy(base)
    for override in overrides:
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
    return result
```

### 3.3 Data Query Generation Logic

The backend generates data queries based on the resolved config:

```python
async def generate_data_query(
    config: Dict[str, Any],
    filters: Dict[str, Any],
    pagination: Dict[str, int],
    ctx: ResolutionContext
) -> str:
    """
    Generate SQL/API query based on dashboard config and user filters.
    """
    # Extract required columns from config
    required_columns = extract_required_columns(config)
    
    # Build base query
    query_builder = QueryBuilder()
    query_builder.select(required_columns)
    query_builder.from_table(config['data']['sourceTable'])
    
    # Apply user filters
    for filter_key, filter_value in filters.items():
        filter_config = get_filter_config(config, filter_key)
        if filter_config:
            query_builder.add_filter(filter_key, filter_value, filter_config['type'])
    
    # Apply permission-based data scoping
    if ctx.user_zone:
        query_builder.add_filter('zone', ctx.user_zone, 'equals')
    
    # Apply aggregation based on toggle state
    if filters.get('aggregation') == 'YTD':
        query_builder.add_date_filter('record_date', 'ytd')
    elif filters.get('aggregation') == 'QTD':
        query_builder.add_date_filter('record_date', 'qtd')
    
    # Add pagination
    query_builder.paginate(pagination['page'], pagination['pageSize'])
    
    return query_builder.build()
```

---

## 4. Versioning Strategy

### 4.1 Version Identifiers

**Semantic Versioning:**

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug fixes, text changes (backward compatible)
  │     └──────── New features, new columns (backward compatible)
  └────────────── Breaking changes, removed features
```

**Examples:**

| Version | Change Type | Example |
|---------|-------------|---------|
| `1.0.0` → `1.0.1` | Patch | Fixed typo in column label |
| `1.0.0` → `1.1.0` | Minor | Added new KPI card |
| `1.0.0` → `2.0.0` | Major | Removed deprecated filter, changed data schema |

### 4.2 Draft vs Published Dashboards

**Lifecycle States:**

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌───────────┐
│  Draft  │ ──▶ │ Review  │ ──▶ │ Published│ ──▶ │Deprecated │
└─────────┘     └─────────┘     └──────────┘     └───────────┘
     │               │               │                │
     │               │               │                │
     ▼               ▼               ▼                ▼
 Editable       Locked for      Active for       Hidden from
 by author      review          all users        new users
```

**State Transitions:**

```python
class DashboardVersionState(Enum):
    DRAFT = "draft"           # Work in progress
    REVIEW = "review"         # Awaiting approval
    PUBLISHED = "published"   # Live for users
    DEPRECATED = "deprecated" # Marked for removal
    ARCHIVED = "archived"     # Removed from production

VALID_TRANSITIONS = {
    DashboardVersionState.DRAFT: [DashboardVersionState.REVIEW],
    DashboardVersionState.REVIEW: [DashboardVersionState.DRAFT, DashboardVersionState.PUBLISHED],
    DashboardVersionState.PUBLISHED: [DashboardVersionState.DEPRECATED],
    DashboardVersionState.DEPRECATED: [DashboardVersionState.ARCHIVED, DashboardVersionState.PUBLISHED],
    DashboardVersionState.ARCHIVED: [],  # Terminal state
}
```

### 4.3 Backward Compatibility

**Compatibility Rules:**

| Rule | Description |
|------|-------------|
| **Additive Changes** | Adding new filters, columns, KPIs is always safe |
| **Deprecation Period** | Features must be deprecated for 30 days before removal |
| **Default Values** | New required fields must have sensible defaults |
| **Schema Migration** | Data schema changes require migration scripts |
| **Client Notification** | Breaking changes trigger user notifications |

**Compatibility Check:**

```python
def check_backward_compatibility(
    old_config: Dict,
    new_config: Dict
) -> CompatibilityReport:
    """Check if new config is backward compatible with old."""
    issues = []
    
    # Check for removed filters
    old_filter_keys = {f['key'] for f in old_config['filters']}
    new_filter_keys = {f['key'] for f in new_config['filters']}
    removed_filters = old_filter_keys - new_filter_keys
    if removed_filters:
        issues.append(BreakingChange(
            type='removed_filter',
            details=f"Filters removed: {removed_filters}"
        ))
    
    # Check for removed columns
    old_columns = extract_column_keys(old_config)
    new_columns = extract_column_keys(new_config)
    removed_columns = old_columns - new_columns
    if removed_columns:
        issues.append(BreakingChange(
            type='removed_column',
            details=f"Columns removed: {removed_columns}"
        ))
    
    # Check for changed data endpoints
    if old_config['data']['endpoints'] != new_config['data']['endpoints']:
        issues.append(Warning(
            type='endpoint_change',
            details="Data endpoints changed - verify API compatibility"
        ))
    
    return CompatibilityReport(
        is_compatible=len([i for i in issues if isinstance(i, BreakingChange)]) == 0,
        issues=issues
    )
```

---

## 5. Runtime Flow

### 5.1 Request → Config Resolution → Data Fetch → Response

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                           │
│  GET /api/dashboards/sales-performance                          │
│  Headers: Authorization: Bearer <token>                          │
│  Query: ?fy=2025-2026&period=DEC&zone=NORTH                     │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. AUTHENTICATION & AUTHORIZATION                                │
│    - Validate JWT token                                          │
│    - Extract user_id, role, tenant_id, permissions               │
│    - Check dashboard access permission                           │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. CONFIG RESOLUTION                                             │
│    - Fetch base template                                         │
│    - Apply role/user/tenant overrides                            │
│    - Apply permission filters                                    │
│    - Return resolved config                                      │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. PARALLEL DATA FETCHING                                        │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│    │ /meta    │  │ /kpis    │  │ /table   │                     │
│    └──────────┘  └──────────┘  └──────────┘                     │
│         │             │             │                            │
│         ▼             ▼             ▼                            │
│    ┌─────────────────────────────────────┐                      │
│    │    Query Generation & Execution      │                      │
│    │    (based on resolved config)        │                      │
│    └─────────────────────────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. RESPONSE ASSEMBLY                                             │
│    {                                                             │
│      "config": { ...resolved config... },                        │
│      "data": {                                                   │
│        "meta": { lastUpdatedAt, features },                      │
│        "kpis": { cards: [...] },                                 │
│        "table": { rows: [...], total, page }                     │
│      },                                                          │
│      "version": {                                                │
│        "templateId": "sales-performance",                        │
│        "version": "2.1.0",                                       │
│        "appliedOverrides": ["role-manager", "zone-north"]        │
│      }                                                           │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 How Different Users Get Different Versions

**User Context Examples:**

```
┌─────────────────────────────────────────────────────────────────┐
│ USER A: Sales Manager, North Zone                               │
├─────────────────────────────────────────────────────────────────┤
│ Context:                                                        │
│   user_id: "user-123"                                           │
│   role: "sales_manager"                                         │
│   zone: "NORTH"                                                 │
│   tenant: "acme-corp"                                           │
│                                                                 │
│ Applied Overrides:                                              │
│   1. tenant:acme-corp → Custom branding, currency: USD          │
│   2. role:sales_manager → Hide executive-only KPIs              │
│   3. zone:NORTH → Pre-filter to North zone data                 │
│                                                                 │
│ Result: Dashboard shows North zone data, manager-level metrics  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ USER B: Executive, Company-wide                                 │
├─────────────────────────────────────────────────────────────────┤
│ Context:                                                        │
│   user_id: "user-456"                                           │
│   role: "executive"                                             │
│   zone: null (all zones)                                        │
│   tenant: "acme-corp"                                           │
│                                                                 │
│ Applied Overrides:                                              │
│   1. tenant:acme-corp → Custom branding, currency: USD          │
│   2. role:executive → Add strategic KPIs, enable all exports    │
│                                                                 │
│ Result: Dashboard shows all zones, executive-level metrics      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Performance & Caching Considerations

### 6.1 Query Reuse

**Caching Layers:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Caching Architecture                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Browser Cache   │     │   CDN/Edge       │     │   App Cache  │
│  (Config: 5min)  │     │  (Static: 1hr)   │     │  (Redis)     │
└──────────────────┘     └──────────────────┘     └──────────────┘
                                                         │
                              ┌───────────────────────────┴───────┐
                              │                                   │
                    ┌─────────▼─────────┐           ┌─────────────▼─────────┐
                    │   Config Cache    │           │     Data Cache        │
                    │  (TTL: 5min)      │           │  (TTL: varies)        │
                    │                   │           │                       │
                    │ Key: template_id  │           │ Key: query_hash       │
                    │ + user_context    │           │ + filter_params       │
                    └───────────────────┘           └───────────────────────┘
```

**Cache Key Generation:**

```python
def generate_config_cache_key(ctx: ResolutionContext) -> str:
    """Generate cache key for resolved config."""
    return f"config:{ctx.template_id}:{ctx.tenant_id}:{ctx.user_role}"

def generate_data_cache_key(
    template_id: str,
    filters: Dict,
    pagination: Dict
) -> str:
    """Generate cache key for data query results."""
    filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
    return f"data:{template_id}:{filter_hash}:p{pagination['page']}"
```

### 6.2 Pre-Aggregation Strategies

**Materialized Views:**

```sql
-- Pre-aggregate daily data to improve query performance
CREATE MATERIALIZED VIEW mv_daily_sales_by_entity AS
SELECT 
  entity_id,
  entity_name,
  entity_type,
  zone,
  state,
  channel_type,
  DATE_TRUNC('day', record_date) as sales_date,
  SUM(project_wires_actual) as project_wires_actual,
  SUM(project_wires_target) as project_wires_target,
  -- ... other category aggregates
  SUM(overall_actual) as overall_actual
FROM raw_sales_transactions
GROUP BY 1, 2, 3, 4, 5, 6, 7;

-- Refresh daily
CREATE INDEX idx_mv_daily_entity ON mv_daily_sales_by_entity(entity_id, sales_date);
```

**Pre-computed KPI Tables:**

```sql
-- Pre-compute KPIs for common filter combinations
CREATE TABLE precomputed_kpis (
  computation_id SERIAL PRIMARY KEY,
  template_id VARCHAR(64),
  filter_hash VARCHAR(64),
  aggregation VARCHAR(10),
  fiscal_year VARCHAR(10),
  period VARCHAR(10),
  kpi_data JSONB,
  computed_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  UNIQUE(template_id, filter_hash, aggregation, fiscal_year, period)
);
```

---

## 7. Risks & Trade-offs

### 7.1 Complexity vs Flexibility

| Aspect | Simple Approach | Dynamic Versioning |
|--------|-----------------|-------------------|
| **Implementation Effort** | Low | High |
| **Maintenance** | Per-dashboard | Centralized |
| **Flexibility** | Limited | High |
| **Performance** | Direct queries | Needs caching layer |
| **Debugging** | Straightforward | Complex (override chains) |
| **Testing** | Per-dashboard tests | Config validation + integration |

### 7.2 Debugging and Observability

**Debug Mode Response:**

```json
{
  "config": { /* resolved config */ },
  "data": { /* dashboard data */ },
  "_debug": {
    "resolution": {
      "baseTemplate": "sales-performance",
      "baseVersion": "2.1.0",
      "appliedOverrides": [
        {
          "id": "override-123",
          "scope": "role:sales_manager",
          "priority": 10,
          "changes": ["filters.zone.hidden=true", "kpis.cards[5].visible=false"]
        },
        {
          "id": "override-456",
          "scope": "tenant:acme-corp",
          "priority": 5,
          "changes": ["formatRules.currency.symbol=$"]
        }
      ],
      "permissionFilters": {
        "hiddenFilters": [],
        "hiddenColumns": ["margin_pct"],
        "disabledFeatures": ["export_xlsx"]
      },
      "resolvedAt": "2026-01-28T10:30:00Z",
      "resolutionTimeMs": 45
    },
    "queries": {
      "kpis": {
        "sql": "SELECT ...",
        "params": {...},
        "executionTimeMs": 120,
        "cacheHit": false
      },
      "table": {
        "sql": "SELECT ...",
        "params": {...},
        "executionTimeMs": 250,
        "cacheHit": true
      }
    }
  }
}
```

**Logging Strategy:**

```python
import structlog

logger = structlog.get_logger()

async def resolve_config_with_logging(ctx: ResolutionContext):
    with logger.bind(
        template_id=ctx.template_id,
        user_id=ctx.user_id,
        user_role=ctx.user_role
    ):
        logger.info("config_resolution_started")
        
        try:
            result = await resolve_dashboard_config(ctx)
            logger.info(
                "config_resolution_completed",
                applied_overrides=result['meta']['appliedOverrides'],
                resolution_time_ms=result['meta']['resolutionTimeMs']
            )
            return result
        except Exception as e:
            logger.error("config_resolution_failed", error=str(e))
            raise
```

---

## 8. Final Recommendation

### Best Practices for Implementing Dynamic Dashboard Versioning

| Practice | Description |
|----------|-------------|
| **Start Simple** | Begin with base templates + role-based overrides only |
| **Limit Override Depth** | Max 3-4 override layers to keep debugging manageable |
| **Cache Aggressively** | Config resolution should be cached; invalidate on change |
| **Version Everything** | Every config change should increment version |
| **Test Override Chains** | Automated tests for common user context combinations |
| **Monitor Resolution Time** | Alert if config resolution exceeds 100ms |
| **Provide Debug Mode** | Include `?debug=true` option for troubleshooting |
| **Document Overrides** | Every override must have a reason documented |
| **Audit Trail** | Log all config changes with who/when/why |
| **Gradual Rollout** | Use feature flags for new override types |

### Implementation Phases

**Phase 1: Foundation**
- Base template storage
- Single-version publishing
- Role-based overrides (3-5 roles)

**Phase 2: Enhancement**
- Multi-tenant support
- Geographic overrides
- Caching layer
- Debug mode

**Phase 3: Advanced**
- A/B testing support
- Historical snapshots
- Self-service override creation
- Advanced observability

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recommended Architecture                      │
└─────────────────────────────────────────────────────────────────┘

                        ┌─────────────────┐
                        │   API Gateway   │
                        │   (Auth + Rate  │
                        │    Limiting)    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Dashboard       │
                        │ Service         │
                        │ (Config         │
                        │  Resolution)    │
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼──────┐  ┌───────▼───────┐
     │  Config Store   │ │   Cache     │  │  Data Service │
     │  (PostgreSQL)   │ │   (Redis)   │  │  (Query Gen)  │
     └─────────────────┘ └─────────────┘  └───────────────┘
              │                                     │
              │                            ┌───────▼───────┐
              │                            │  Data Store   │
              │                            │  (Analytics   │
              │                            │   Database)   │
              └────────────────────────────┴───────────────┘
```

This architecture enables:
- ✅ Single codebase for all dashboard variants
- ✅ Role/tenant/user-specific customization
- ✅ Safe versioning and rollback
- ✅ Performance through caching
- ✅ Observability for debugging
- ✅ Governance through approval workflows

