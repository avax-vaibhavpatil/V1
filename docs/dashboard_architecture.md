# Dashboard Architecture

## 1. Overview

### Purpose of the Dashboard

The Analytics Dashboard is a **data-driven, config-driven reporting platform** designed to provide comprehensive performance visibility across multiple business dimensions. It enables stakeholders to:

- Monitor sales performance across categories, regions, and entities
- Track KPIs with trend analysis and growth metrics
- Drill down into entity-level details for root cause analysis
- Export data for offline analysis and reporting

### Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Data-Driven** | All UI components render based on data responses, not static layouts |
| **Config-Driven** | Report structure, filters, KPIs, and tables are defined via JSON configuration |
| **Reusable** | Single dashboard codebase supports multiple report types through configuration |
| **Decoupled** | Frontend presentation layer is independent of data source implementation |
| **Stateful** | Filter state is URL-synchronized for shareability and bookmarking |

---

## 2. Data Layers

The dashboard consumes data through a **three-layer architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  (KPI Cards, Data Table, Charts, Drilldown Widgets)            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Formatted Metrics
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   PROCESSED/AGGREGATED LAYER                    │
│  - KPI Aggregations (sum, avg, weighted avg)                   │
│  - Time-based rollups (YTD, QTD, MTD)                          │
│  - Growth calculations (period-over-period)                     │
│  - Contribution percentages                                     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Entity-Level Records
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       RAW DATA LAYER                            │
│  Sources: ERP, CRM, Sales Systems, File Uploads                │
│  Ownership: Sales Operations, Finance, IT Data Team            │
│  Refresh: Daily/Real-time depending on source                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Raw Data Layer

**Sources:**
- Enterprise Resource Planning (ERP) systems
- Customer Relationship Management (CRM)
- Sales transaction databases
- File uploads (CSV/XLSX)

**Ownership:**
- Data Engineering team manages ETL pipelines
- Business Operations defines data quality rules
- IT maintains data security and access controls

**Expected Schema (Minimum Required Fields):**

```typescript
interface RawEntityRecord {
  // Identity
  entityId: string;        // Unique identifier
  entityName: string;      // Display name
  entityCode?: string;     // Optional business code
  entityType: string;      // e.g., "DISTRIBUTOR", "CUSTOMER"
  
  // Hierarchy
  zone: string;            // Geographic zone
  state: string;           // State/Province
  region?: string;         // Optional sub-region
  
  // Segmentation
  channelType: string;     // e.g., "CHANNEL", "INSTITUTIONAL"
  
  // Metrics (per category)
  [category]_actualSales: number;
  [category]_targetSales: number;
  [category]_previousPeriodSales?: number;
  
  // Timestamps
  recordDate: Date;
  lastUpdated: Date;
}
```

### 2.2 Processed/Aggregated Layer

**Transformations Applied:**

| Transformation | Description | Formula |
|----------------|-------------|---------|
| **Growth %** | Period-over-period change | `(current - previous) / previous × 100` |
| **Achievement %** | Target attainment | `actual / target × 100` |
| **Contribution %** | Share of total | `entity_value / total_value × 100` |
| **YTD/QTD/MTD** | Time-based aggregation | Sum of values within time window |
| **Weighted Avg** | Category-weighted metrics | `Σ(value × weight) / Σ(weight)` |

### 2.3 Presentation-Ready Metrics Layer

**Formatting Rules:**

| Format Type | Input | Output Example |
|-------------|-------|----------------|
| `currency` | `1234567.89` | `₹12,34,567.89` |
| `currencyCr` | `1234567.89` | `₹1.23 Cr` |
| `currencyLakh` | `1234567.89` | `₹12.35 L` |
| `percent` | `0.2345` | `23.45%` |
| `integer` | `1234.56` | `1,235` |
| `decimal` | `1234.567` | `1,234.57` |
| `compact` | `1234567` | `1.23M` |

---

## 3. Data Granularity & Dimensions

### 3.1 Time Granularity

The dashboard supports multiple time aggregation levels:

```
┌──────────────────────────────────────────────────────────────┐
│ Aggregation Level │ Use Case                                 │
├──────────────────────────────────────────────────────────────┤
│ YTD (Year-to-Date)│ Annual performance tracking              │
│ QTD (Quarter)     │ Quarterly business reviews               │
│ MTD (Month)       │ Monthly operational monitoring           │
│ Daily             │ Operational dashboards (if enabled)      │
└──────────────────────────────────────────────────────────────┘
```

**Fiscal Calendar Support:**
- Configurable fiscal year start (default: April)
- Period selection: APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC, JAN, FEB, MAR

### 3.2 Organizational Hierarchy

```
                    ┌─────────────┐
                    │   Company   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      ┌────────┐      ┌────────┐      ┌────────┐
      │  Zone  │      │  Zone  │      │  Zone  │
      │ (North)│      │(South) │      │ (West) │
      └───┬────┘      └────────┘      └────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌───────┐  ┌───────┐
│ State │  │ State │
│  (UP) │  │ (DL)  │
└───┬───┘  └───────┘
    │
    ▼
┌─────────────┐
│   Region    │
│   (UP-1)    │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Distributor/ │
│   Customer   │
└──────────────┘
```

**Filterable Dimensions:**
- Zone (North, South, East, West, Central)
- State (dependent on Zone selection)
- Channel Type (Channel, Institutional)
- Entity Type (Distributor, Customer)

### 3.3 Product/Category Dimensions

**Default Categories (configurable):**

| Category Key | Display Label | Description |
|--------------|---------------|-------------|
| `projectWires` | Project Wires | Industrial cables |
| `flexibles` | Flexibles | Flexible wiring |
| `hdc` | HDC | Heavy Duty Cables |
| `dowells` | Dowells | Cable connectors |
| `fmeg` | FMEG | Fans, Motors, Electrical Goods |
| `lumes` | Lumes | Lighting products |

---

## 4. Metrics & KPIs

### 4.1 Types of Metrics

| Type | Examples | Calculation |
|------|----------|-------------|
| **Counts** | Total entities, active customers | `COUNT(*)` |
| **Sums** | Total sales, total target | `SUM(value)` |
| **Ratios** | Achievement %, contribution % | `value_a / value_b × 100` |
| **Trends** | Growth %, period comparison | `(current - previous) / previous × 100` |
| **Weighted Averages** | Avg growth weighted by sales | `Σ(growth × sales) / Σ(sales)` |

### 4.2 Mandatory vs Optional Metrics

**Mandatory (Required for dashboard to function):**

```typescript
interface MandatoryMetrics {
  entityId: string;         // Row identifier
  entityName: string;       // Display name
  actualSales: number;      // Primary metric (at least one category)
}
```

**Optional (Enhances functionality):**

```typescript
interface OptionalMetrics {
  targetSales?: number;      // Enables achievement %
  previousPeriodSales?: number; // Enables growth %
  entityCode?: string;       // Secondary identifier
  zone?: string;             // Enables geographic filtering
  state?: string;            // Enables state filtering
}
```

### 4.3 Derived vs Raw Metrics

| Derived Metric | Formula | Dependencies |
|----------------|---------|--------------|
| `growthPct` | `(actual - previous) / previous × 100` | `actualSales`, `previousPeriodSales` |
| `achievementPct` | `actual / target × 100` | `actualSales`, `targetSales` |
| `contributionPct` | `entityActual / totalActual × 100` | `actualSales` (all entities) |
| `overall_actualSales` | `Σ(category_actualSales)` | All category actuals |
| `overall_growthPct` | `Σ(actual × growth) / Σ(actual)` | All category sales & growth |

---

## 5. Dashboard Components

### 5.1 Component Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        ReportHeader                            │
│  [Title] [Last Updated] [Refresh] [Export] [Share]            │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│                        FilterBar                               │
│  [FY Selector] [Period] [Aggregation Toggle] [Advanced]       │
│  [Apply] [Clear] [Reset]                                       │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│                     SegmentControls                            │
│  [Channel | Institutional]  [Distributor | Customer]          │
│  [North] [South] [East] [West] [Central]                      │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│                        KPI Grid                                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│  │ KPI1 │ │ KPI2 │ │ KPI3 │ │ KPI4 │ │ KPI5 │ │ KPI6 │       │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘       │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│                       DataTable                                │
│  [Search] [Page Info]                                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Entity │ Cat1 Act/%G/%A │ Cat2 Act/%G/%A │ ... │ Total │  │
│  │--------|----------------|----------------|-----|-------|  │
│  │ Row 1  │ ₹1.23Cr │ +5% │ ₹0.45Cr │ -2% │ ... │ ₹5.6Cr│  │
│  │ Row 2  │ ...            │ ...            │ ... │ ...   │  │
│  └─────────────────────────────────────────────────────────┘  │
│  [< Prev] [1] [2] [3] ... [Next >]                            │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│                    DrilldownDrawer (Side Panel)                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Entity: MULTICAB ENTERPRISES                             │ │
│  │ Summary: ₹12.5 Cr | +15% Growth                          │ │
│  │ ┌────────────────────────────────────────────────────┐   │ │
│  │ │ Trend Chart (12 months)                            │   │ │
│  │ └────────────────────────────────────────────────────┘   │ │
│  │ ┌────────────────────────────────────────────────────┐   │ │
│  │ │ Breakdown by Category                              │   │ │
│  │ └────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Component-to-Data Mapping

| Component | API Endpoint | Data Requirements |
|-----------|--------------|-------------------|
| **ReportHeader** | `/meta` | `lastUpdatedAt`, `features` |
| **FilterBar** | `/meta` (allowed values) | Filter options, defaults |
| **SegmentControls** | Config-defined | Static options or `/dimensions/*` |
| **KpiGrid** | `/kpis` | Aggregated metrics per category |
| **DataTable** | `/table` | Paginated entity rows |
| **DrilldownDrawer** | `/drilldown` | Entity summary, trends, breakdown |

---

## 6. Data Validation & Assumptions

### 6.1 Minimum Data Required

| Requirement | Validation |
|-------------|------------|
| At least 1 entity row | `rows.length >= 1` |
| Entity identifier present | `entityId !== null` |
| At least one numeric metric | `actualSales !== undefined` |
| Consistent category keys | All rows have same category structure |

### 6.2 Fallbacks When Data is Missing

| Scenario | Fallback Behavior |
|----------|-------------------|
| No `targetSales` | Achievement % shows "N/A" or hidden |
| No `previousPeriodSales` | Growth % shows "0%" or "N/A" |
| Empty table response | Show empty state with message |
| API error | Show error state with retry button |
| Missing zone/state | Entity excluded from geographic filters |
| Zero actual sales | Show "₹0" with neutral styling |

### 6.3 Data Quality Assumptions

```typescript
// Assumptions made by the dashboard:
const assumptions = {
  // Numeric fields are always numbers (not strings)
  numericFieldsAreNumbers: true,
  
  // Entity IDs are unique within the dataset
  uniqueEntityIds: true,
  
  // Category keys are consistent across all entities
  consistentCategoryKeys: true,
  
  // Time periods follow fiscal calendar
  fiscalCalendarCompliance: true,
  
  // Negative growth is possible and valid
  negativeGrowthAllowed: true,
  
  // Zero values are valid (not nulls)
  zeroValuesValid: true,
};
```

---

## 7. Summary

### Data Maturity Requirements

| Level | Requirement | Dashboard Features Available |
|-------|-------------|------------------------------|
| **Basic** | Entity ID, Name, Sales (1 metric) | Table only, no KPIs |
| **Standard** | + Categories, Targets, Geography | Full KPIs, filtering, basic drilldown |
| **Advanced** | + Historical data, multiple periods | Growth trends, YTD/QTD, full drilldown |
| **Enterprise** | + Real-time updates, full hierarchy | All features + refresh, advanced analytics |

### Key Takeaways

1. **Data must be entity-level** - Each row represents one distributor/customer
2. **Categories must be consistent** - All entities report on same category structure
3. **Metrics enable features** - More metrics unlock more dashboard capabilities
4. **Config adapts presentation** - Same data can power multiple report views
5. **Filters reduce scope** - Data layer must support filter parameters

### Data Contract Summary

```typescript
// Minimum viable data contract
interface MinimumDataContract {
  // Meta endpoint
  meta: {
    lastUpdatedAt: string;
  };
  
  // KPIs endpoint
  kpis: {
    cards: Array<{
      id: string;
      actualSales: number;
    }>;
  };
  
  // Table endpoint
  table: {
    rows: Array<{
      entityId: string;
      entityName: string;
      [categoryKey: string]: number;
    }>;
    total: number;
  };
}
```

This architecture enables a single dashboard implementation to serve multiple business domains by simply changing the configuration and ensuring data conforms to the expected contract.

