# Dashboard Configuration Management

## 1. Why Configuration-Based Dashboards

### Problems with Hardcoded Dashboards

| Problem | Impact |
|---------|--------|
| **Code Duplication** | Creating similar dashboards requires copying entire codebases |
| **Maintenance Overhead** | Bug fixes must be applied to multiple dashboard implementations |
| **Inconsistent UX** | Different dashboards evolve separately, creating inconsistent experiences |
| **Developer Bottleneck** | Every dashboard change requires developer involvement |
| **Slow Time-to-Market** | New reports take weeks/months instead of days |
| **Testing Complexity** | Each dashboard requires separate test suites |
| **Deployment Risk** | Code changes for one dashboard can break others |

### Benefits of Configuration-Driven Design

| Benefit | Description |
|---------|-------------|
| **Single Codebase** | One dashboard engine powers unlimited report types |
| **Rapid Development** | New reports require only config + data adapter |
| **Consistent UX** | All dashboards share the same interaction patterns |
| **Business Empowerment** | Power users can modify configs without code changes |
| **Reduced Testing** | Core engine tested once, configs validated separately |
| **Safe Deployments** | Config changes don't require code deployments |
| **Version Control** | Configs can be tracked, reviewed, and rolled back |

---

## 2. Types of Configuration

### 2.1 Data Configuration

Controls what data is fetched and how it's structured:

```typescript
interface DataConfig {
  // API endpoints
  endpoints: {
    meta: string;      // Report metadata
    kpis: string;      // KPI card data
    table: string;     // Table rows
    drilldown: string; // Entity details
    export?: string;   // Export endpoint
  };
  
  // Data source binding
  dataSource?: {
    type: 'api' | 'sql' | 'file';
    connectionId?: string;
    query?: string;
  };
}
```

### 2.2 UI Configuration

Controls visual presentation without changing data:

```typescript
interface UIConfig {
  // Layout
  layout: {
    showHeader: boolean;
    showFilterBar: boolean;
    showSegmentControls: boolean;
    showKpis: boolean;
    showTable: boolean;
  };
  
  // Theming
  theme?: {
    primaryColor: string;
    accentColor: string;
    fontFamily: string;
  };
  
  // Feature toggles
  features: {
    export: boolean;
    drilldown: boolean;
    share: boolean;
    refresh: boolean;
  };
}
```

### 2.3 Role-Based Configuration

Controls what different users can see:

```typescript
interface RoleConfig {
  // Visibility rules
  visibility: {
    hiddenFilters: string[];      // Filters user cannot see
    hiddenColumns: string[];      // Columns user cannot see
    hiddenKpis: string[];         // KPIs user cannot see
  };
  
  // Data scoping
  dataScope: {
    allowedZones?: string[];      // Geographic restriction
    allowedEntityTypes?: string[];// Entity type restriction
    maxExportRows?: number;       // Export limit
  };
  
  // Actions
  permissions: {
    canExport: boolean;
    canShare: boolean;
    canDrilldown: boolean;
    canRefresh: boolean;
  };
}
```

### 2.4 Time-Based or Business-Rule Configuration

Controls behavior based on business context:

```typescript
interface BusinessRuleConfig {
  // Time-based defaults
  timeDefaults: {
    useFiscalCalendar: boolean;
    fiscalYearStart: number;      // Month (1-12)
    defaultAggregation: 'YTD' | 'QTD' | 'MTD';
    autoSelectCurrentPeriod: boolean;
  };
  
  // Business rules
  rules: {
    // Hide negative growth rows
    hideNegativeGrowth?: boolean;
    
    // Threshold for "good" performance
    goodGrowthThreshold?: number;
    
    // Minimum sales to display
    minimumSalesThreshold?: number;
    
    // Category-specific rules
    categoryRules?: Record<string, {
      weight: number;
      hidden: boolean;
    }>;
  };
}
```

---

## 3. Configuration Structure

### 3.1 Complete Configuration Schema

```typescript
interface ReportConfig {
  // ========================================
  // IDENTITY
  // ========================================
  reportId: string;                    // Unique identifier
  title: string;                       // Display title
  description?: string;                // Report description
  version?: string;                    // Config version
  
  // ========================================
  // DEFAULTS
  // ========================================
  defaults: {
    time: {
      fiscalYear: string;              // e.g., "2025-2026"
      period: string;                  // e.g., "DEC"
    };
    toggles: {
      aggregation: 'YTD' | 'QTD' | 'MTD';
      metricMode: 'VALUE' | 'VOLUME' | 'UNITS';
    };
    segments: Record<string, string>;  // Default segment values
  };
  
  // ========================================
  // DATA ENDPOINTS
  // ========================================
  data: {
    endpoints: {
      meta: string;
      kpis: string;
      table: string;
      drilldown: string;
      export?: string;
    };
  };
  
  // ========================================
  // FILTERS
  // ========================================
  filters: FilterConfig[];
  
  // ========================================
  // KPI CARDS
  // ========================================
  kpis: {
    cards: KpiCardConfig[];
  };
  
  // ========================================
  // DATA TABLE
  // ========================================
  table: {
    entityColumn: EntityColumnConfig;
    columnGroups: ColumnGroupConfig[];
    defaultSort?: { key: string; direction: 'asc' | 'desc' };
    pageSize?: number;
    virtualScroll?: boolean;
  };
  
  // ========================================
  // FORMATTING
  // ========================================
  formatRules: {
    conditionalStyles: {
      posNeg?: ConditionalStyleRule;
      heatmap?: ThresholdRule;
    };
    currency?: {
      symbol: string;
      scale: 'Cr' | 'Lakh' | 'K' | 'M';
    };
  };
  
  // ========================================
  // DRILLDOWN
  // ========================================
  drilldown: {
    enabled: boolean;
    widgets: DrilldownWidget[];
  };
  
  // ========================================
  // FEATURES
  // ========================================
  features?: {
    export?: boolean;
    drilldown?: boolean;
    share?: boolean;
    refresh?: boolean;
  };
}
```

### 3.2 Filter Configuration

```typescript
interface FilterConfig {
  key: string;                         // Filter identifier
  label: string;                       // Display label
  type: 'single' | 'multi';            // Selection mode
  ui: 'tabs' | 'chips' | 'select' | 'multiselect' | 'daterange';
  optionsSource: 'static' | 'api';     // Where options come from
  options?: FilterOption[];            // Static options
  endpoint?: string;                   // API endpoint for dynamic options
  dependsOn?: string[];                // Dependent filters
  defaultValue?: string | string[];    // Default selection
  searchable?: boolean;                // Enable search
  placeholder?: string;                // Placeholder text
}
```

### 3.3 KPI Card Configuration

```typescript
interface KpiCardConfig {
  id: string;                          // Card identifier
  title: string;                       // Display title
  icon?: string;                       // Optional icon
  primaryMetric: string;               // Main metric key
  secondaryMetric?: string;            // Secondary metric key
  shareMetric?: string;                // Contribution % key
  trendMetric?: string;                // Growth % key
  onClick?: {
    type: 'filter' | 'highlight' | 'drilldown';
    filterKey?: string;
    value?: string;
    groupKey?: string;
  };
  tooltip?: string;                    // Hover tooltip
}
```

### 3.4 Table Column Configuration

```typescript
interface ColumnConfig {
  key: string;                         // Data key
  label: string;                       // Column header
  format?: 'currency' | 'currencyCr' | 'percent' | 'integer' | 'decimal';
  conditional?: 'posNeg' | 'heatmap' | 'threshold';
  width?: number;                      // Column width
  sortable?: boolean;                  // Enable sorting
  align?: 'left' | 'center' | 'right';
  tooltip?: string;
}

interface ColumnGroupConfig {
  groupLabel: string;                  // Group header
  groupKey: string;                    // Group identifier
  columns: ColumnConfig[];             // Columns in group
}
```

---

## 4. Examples

### 4.1 Example 1: Sales Manager Dashboard

**Use Case:** Regional sales managers need to track their team's performance.

```typescript
const salesManagerConfig: ReportConfig = {
  reportId: 'sales-manager-dashboard',
  title: 'Regional Sales Performance',
  
  defaults: {
    time: { fiscalYear: '2025-2026', period: 'DEC' },
    toggles: { aggregation: 'MTD', metricMode: 'VALUE' },
    segments: { entityType: 'DISTRIBUTOR' },
  },
  
  filters: [
    {
      key: 'entityType',
      label: 'Entity Type',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      options: [
        { label: 'Distributors', value: 'DISTRIBUTOR' },
        { label: 'Customers', value: 'CUSTOMER' },
      ],
    },
    {
      key: 'state',
      label: 'State',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'api',
      endpoint: '/api/dimensions/states',
      searchable: true,
    },
  ],
  
  kpis: {
    cards: [
      {
        id: 'totalSales',
        title: 'Total Sales',
        primaryMetric: 'actualSales',
        trendMetric: 'growthPct',
      },
      {
        id: 'target',
        title: 'Target Achievement',
        primaryMetric: 'achievementPct',
      },
      {
        id: 'activeEntities',
        title: 'Active Entities',
        primaryMetric: 'activeCount',
      },
    ],
  },
  
  table: {
    entityColumn: { key: 'entityName', label: 'Name', pinned: true },
    columnGroups: [
      {
        groupLabel: 'Performance',
        groupKey: 'performance',
        columns: [
          { key: 'actualSales', label: 'Sales', format: 'currencyCr', sortable: true },
          { key: 'targetSales', label: 'Target', format: 'currencyCr' },
          { key: 'growthPct', label: 'Growth', format: 'percent', conditional: 'posNeg' },
        ],
      },
    ],
    pageSize: 25,
  },
  
  drilldown: { enabled: true, widgets: ['entitySummary', 'trendChart'] },
  features: { export: true, drilldown: true, share: false, refresh: true },
};
```

### 4.2 Example 2: Executive Summary Dashboard

**Use Case:** C-level executives need high-level overview across all categories.

```typescript
const executiveSummaryConfig: ReportConfig = {
  reportId: 'executive-summary',
  title: 'Executive Performance Summary',
  
  defaults: {
    time: { fiscalYear: '2025-2026', period: 'DEC' },
    toggles: { aggregation: 'YTD', metricMode: 'VALUE' },
    segments: {},
  },
  
  filters: [
    {
      key: 'zone',
      label: 'Zone',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: '' },
        { label: 'North', value: 'NORTH' },
        { label: 'South', value: 'SOUTH' },
        { label: 'East', value: 'EAST' },
        { label: 'West', value: 'WEST' },
      ],
    },
  ],
  
  kpis: {
    cards: [
      // All categories as separate KPI cards
      { id: 'projectWires', title: 'Project Wires', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
      { id: 'flexibles', title: 'Flexibles', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
      { id: 'hdc', title: 'HDC', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
      { id: 'dowells', title: 'Dowells', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
      { id: 'fmeg', title: 'FMEG', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
      { id: 'lumes', title: 'Lumes', primaryMetric: 'actualSales', trendMetric: 'growthPct' },
    ],
  },
  
  table: {
    entityColumn: { key: 'zoneName', label: 'Zone', pinned: true },
    columnGroups: [
      {
        groupLabel: 'Revenue',
        groupKey: 'revenue',
        columns: [
          { key: 'totalSales', label: 'Total', format: 'currencyCr', sortable: true },
          { key: 'growthPct', label: 'YoY Growth', format: 'percent', conditional: 'posNeg' },
        ],
      },
      {
        groupLabel: 'Market Share',
        groupKey: 'marketShare',
        columns: [
          { key: 'marketSharePct', label: 'Share %', format: 'percent' },
        ],
      },
    ],
    pageSize: 10,
  },
  
  drilldown: { enabled: false, widgets: [] },
  features: { export: true, drilldown: false, share: true, refresh: true },
};
```

### 4.3 Example 3: Product-wise Performance Dashboard

**Use Case:** Product managers need category-specific insights.

```typescript
const productPerformanceConfig: ReportConfig = {
  reportId: 'product-performance',
  title: 'Product Category Analysis',
  
  defaults: {
    time: { fiscalYear: '2025-2026', period: 'DEC' },
    toggles: { aggregation: 'QTD', metricMode: 'VOLUME' },
    segments: { category: 'projectWires' },
  },
  
  filters: [
    {
      key: 'category',
      label: 'Product Category',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      options: [
        { label: 'Project Wires', value: 'projectWires' },
        { label: 'Flexibles', value: 'flexibles' },
        { label: 'HDC', value: 'hdc' },
        { label: 'Dowells', value: 'dowells' },
        { label: 'FMEG', value: 'fmeg' },
        { label: 'Lumes', value: 'lumes' },
      ],
    },
    {
      key: 'zone',
      label: 'Zone',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'static',
      options: [
        { label: 'North', value: 'NORTH' },
        { label: 'South', value: 'SOUTH' },
        { label: 'East', value: 'EAST' },
        { label: 'West', value: 'WEST' },
        { label: 'Central', value: 'CENTRAL' },
      ],
    },
  ],
  
  kpis: {
    cards: [
      { id: 'volume', title: 'Total Volume', primaryMetric: 'totalVolume', trendMetric: 'volumeGrowth' },
      { id: 'revenue', title: 'Revenue', primaryMetric: 'totalRevenue', trendMetric: 'revenueGrowth' },
      { id: 'avgPrice', title: 'Avg Price', primaryMetric: 'averagePrice', trendMetric: 'priceChange' },
      { id: 'topSku', title: 'Top SKU', primaryMetric: 'topSkuName' },
    ],
  },
  
  table: {
    entityColumn: { key: 'skuName', label: 'SKU', pinned: true, secondaryKey: 'skuCode' },
    columnGroups: [
      {
        groupLabel: 'Volume',
        groupKey: 'volume',
        columns: [
          { key: 'unitsSold', label: 'Units', format: 'integer', sortable: true },
          { key: 'volumeGrowth', label: 'Growth', format: 'percent', conditional: 'posNeg' },
        ],
      },
      {
        groupLabel: 'Revenue',
        groupKey: 'revenue',
        columns: [
          { key: 'revenue', label: 'Value', format: 'currencyLakh', sortable: true },
          { key: 'revenueShare', label: 'Share', format: 'percent' },
        ],
      },
    ],
    pageSize: 50,
  },
  
  drilldown: {
    enabled: true,
    widgets: ['entitySummary', 'trendChart', 'breakdownByProduct'],
  },
  features: { export: true, drilldown: true, share: true, refresh: true },
};
```

---

## 5. Config vs Code Boundaries

### 5.1 What Should Be Configurable

| Aspect | Config Ownership | Rationale |
|--------|------------------|-----------|
| **Report title, description** | ✅ Config | Text changes shouldn't need deploys |
| **Filter definitions** | ✅ Config | Business defines what's filterable |
| **KPI card definitions** | ✅ Config | Metrics change per report |
| **Table columns** | ✅ Config | Different reports need different views |
| **Column formatting** | ✅ Config | Display preferences are contextual |
| **Default values** | ✅ Config | Defaults are business decisions |
| **Feature toggles** | ✅ Config | Features vary by report/user |
| **Conditional styling rules** | ✅ Config | Business defines "good" vs "bad" |
| **Drilldown widgets** | ✅ Config | Detail level varies by report |

### 5.2 What Should Remain Fixed in Code

| Aspect | Code Ownership | Rationale |
|--------|----------------|-----------|
| **Component architecture** | ❌ Code | Core UI behavior is stable |
| **Data fetching logic** | ❌ Code | API contracts are standardized |
| **State management** | ❌ Code | Filter/apply pattern is consistent |
| **URL synchronization** | ❌ Code | Deep linking is a core feature |
| **Error handling** | ❌ Code | Failure modes are predictable |
| **Loading states** | ❌ Code | UX consistency matters |
| **Accessibility** | ❌ Code | A11y is non-negotiable |
| **Security checks** | ❌ Code | Auth/authz in code, not config |
| **Aggregation logic** | ❌ Code | Math should be tested, not configured |

### 5.3 Gray Areas (Case-by-Case)

| Aspect | Recommendation |
|--------|----------------|
| **Custom calculations** | Config for simple formulas; code for complex logic |
| **Validation rules** | Config for thresholds; code for data integrity |
| **Caching policies** | Config for TTLs; code for invalidation logic |
| **Rate limiting** | Config for limits; code for enforcement |

---

## 6. Governance & Versioning

### 6.1 Config Validation

**Schema Validation:**

```typescript
import { z } from 'zod';

const ReportConfigSchema = z.object({
  reportId: z.string().min(1).regex(/^[a-z0-9-]+$/),
  title: z.string().min(1).max(100),
  defaults: z.object({
    time: z.object({
      fiscalYear: z.string().regex(/^\d{4}-\d{4}$/),
      period: z.enum(['APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR']),
    }),
    toggles: z.object({
      aggregation: z.enum(['YTD', 'QTD', 'MTD']),
      metricMode: z.enum(['VALUE', 'VOLUME', 'UNITS']),
    }),
    segments: z.record(z.string()),
  }),
  filters: z.array(FilterConfigSchema),
  kpis: z.object({ cards: z.array(KpiCardConfigSchema) }),
  table: TableConfigSchema,
  drilldown: DrilldownConfigSchema,
  features: FeaturesConfigSchema.optional(),
});

// Validate before deploying
function validateConfig(config: unknown): ReportConfig {
  return ReportConfigSchema.parse(config);
}
```

**Runtime Validation:**

```typescript
function validateConfigAtRuntime(config: ReportConfig): ValidationResult {
  const errors: string[] = [];
  
  // Check for duplicate filter keys
  const filterKeys = config.filters.map(f => f.key);
  const duplicates = filterKeys.filter((k, i) => filterKeys.indexOf(k) !== i);
  if (duplicates.length > 0) {
    errors.push(`Duplicate filter keys: ${duplicates.join(', ')}`);
  }
  
  // Check column keys match data contract
  const allColumnKeys = config.table.columnGroups.flatMap(g => g.columns.map(c => c.key));
  // Validate against expected data schema...
  
  // Check KPI metric references
  config.kpis.cards.forEach(kpi => {
    if (!isValidMetricKey(kpi.primaryMetric)) {
      errors.push(`Invalid metric key in KPI ${kpi.id}: ${kpi.primaryMetric}`);
    }
  });
  
  return { valid: errors.length === 0, errors };
}
```

### 6.2 Change Management and Approvals

**Config Lifecycle:**

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌───────────┐
│  Draft  │ ──▶ │ Review  │ ──▶ │ Staging │ ──▶ │Production │
└─────────┘     └─────────┘     └─────────┘     └───────────┘
     │               │               │                │
     │               │               │                │
     ▼               ▼               ▼                ▼
  Author          Reviewer        QA Test         Live Users
```

**Approval Requirements:**

| Change Type | Approval Level |
|-------------|----------------|
| New report config | Product Owner + Tech Lead |
| Modify existing filters | Product Owner |
| Add/remove columns | Product Owner |
| Change formatting rules | Self-approve (minor) |
| Modify features/permissions | Product Owner + Security |
| Change data endpoints | Tech Lead + Data Owner |

**Versioning Strategy:**

```typescript
interface VersionedConfig {
  reportId: string;
  version: string;          // Semantic versioning: "1.2.3"
  previousVersion?: string; // Reference to prior version
  changelog: string[];      // List of changes
  createdAt: string;
  createdBy: string;
  approvedBy?: string;
  approvedAt?: string;
  status: 'draft' | 'review' | 'staging' | 'published' | 'deprecated';
}
```

**Rollback Procedure:**

```typescript
async function rollbackConfig(reportId: string, targetVersion: string): Promise<void> {
  // 1. Fetch target version from history
  const historicalConfig = await configStore.getVersion(reportId, targetVersion);
  
  // 2. Validate it still works with current data contract
  const validation = await validateConfigAgainstDataContract(historicalConfig);
  if (!validation.valid) {
    throw new Error(`Cannot rollback: ${validation.errors.join(', ')}`);
  }
  
  // 3. Create new version with rollback marker
  const rollbackConfig = {
    ...historicalConfig,
    version: incrementVersion(getCurrentVersion(reportId)),
    changelog: [`Rollback to version ${targetVersion}`],
    status: 'published',
  };
  
  // 4. Deploy
  await deployConfig(rollbackConfig);
  
  // 5. Notify stakeholders
  await notifyRollback(reportId, targetVersion);
}
```

---

## Summary

Configuration-driven dashboards enable:

1. **Rapid Report Development** - New reports in hours, not weeks
2. **Consistent User Experience** - Same engine, different views
3. **Business Empowerment** - Less dependency on engineering
4. **Safe Evolution** - Configs can be versioned and rolled back
5. **Clear Boundaries** - Config for "what", code for "how"

The key is defining clear contracts between configuration and code, with proper validation and governance to ensure production stability.

