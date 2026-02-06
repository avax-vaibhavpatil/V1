# Universal Reporting Dashboard (Frontend) — Build Guide for Cursor
*Generated: 2026-01-27 07:32*

This document is a **shareable build spec** for creating a **config-driven, reusable reporting dashboard UI** (like BI dashboards) that can be used across multiple reports with minimal code changes.

It includes:
1. **Frontend elements + layout** (reusable across reports) and **how configuration works**
2. **Cursor prompts** for each build step
3. **Backend/data integration** details (API contract patterns, auth, pagination, caching)

---

## 0) Goals & Principles

### Goals
- Build a **single dashboard framework** that can host multiple reports (Sales, Inventory, Finance, etc.).
- Ensure the UI is **config-driven**: adding a new report should require mostly **JSON config**, not new components.
- Support common enterprise reporting needs: **filters, KPI tiles, tables, drilldowns, export, states, permissions**.

### Non-goals
- ETL/warehouse modeling
- Business formula correctness (handled by backend or metric-service)
- Admin UI for report creation (can be built later)

---

## 1) Layout & Frontend Elements (Reusable Across Reports)

### 1.1 Global Page Layout
**Sections**
1. **Top Header**
2. **Global Filter Bar**
3. **Segmentation Controls (Tabs/Chips)**
4. **KPI Summary Row (Cards/Tiles)**
5. **Detail Table**
6. **Drilldown Drawer/Page (optional)**

**Universal UX requirements**
- Entire page refreshes on *Apply Filters* (single source-of-truth filter state)
- Supports: Loading, Empty, Error states consistently
- Responsive: desktop-first; tablet mandatory; mobile view-only fallback

---

### 1.2 Top Header (Universal)
**Elements**
- Report Title (from config)
- Optional Subtitle/Description
- “Data Last Updated” timestamp (from backend metadata)
- Optional actions: Export, Share link, Refresh

**Behavior**
- Timestamp tooltip explains freshness and data source
- Refresh triggers refetch (optionally bypass cache)

---

### 1.3 Global Filter Bar (Universal)
**Common selectors**
- Time dimension selector (Financial Year, Month/Quarter, Date range)
- Measure mode selector (Value/Volume/Units) — optional
- Toggle: YTD/QTD/MTD (configurable list)

**Advanced Filter Drawer**
- Opens via funnel icon button
- Contains filters defined by config (multi-select, single-select, range)
- Buttons: **Apply**, **Clear**, **Reset to Defaults**
- “Applied filters” chips row below filter bar (optional)

**Required behaviors**
- Filters support:
  - Single-select / multi-select
  - Search within options (for long lists)
  - Dependent filters (e.g., Zone → State → City)
- Filter changes do not immediately refetch until **Apply** (unless configured as “live”)

---

### 1.4 Segmentation Controls (Universal)
These are quick filters presented as UI-friendly controls:
- **Tabs** (e.g., Channel vs Institutional)
- **Pills/Chips** (e.g., Zone list, State list)
- **Button groups** (e.g., Distributor vs Customer)

**Behavior**
- Config defines:
  - Which segment controls exist
  - Whether single-select or multi-select
  - Dependencies (Zone determines State options)
- Selecting a segment updates the **pending filter state** (or applied state if “live”).

---

### 1.5 KPI Summary Row (Universal KPI Cards)
**Each KPI Card supports**
- Icon (optional)
- Title (e.g., “Project Wires”)
- Primary KPI (e.g., Actual Sales)
- Secondary KPI (Target / Previous Period)
- Contribution / Share %
- Trend indicator (↑/↓) + color semantics
- Tooltip (metric definition)

**Interactions**
- Click KPI card:
  - Option A: Apply a dimension filter (e.g., category=Project Wires)
  - Option B: Highlight related table columns
  - Option C: Open drilldown

Config chooses behavior per KPI card.

---

### 1.6 Detail Table (Universal)
**Structure**
- Sticky header
- Pinned first column(s): entity name, entity code (optional)
- Column groups (e.g., by Category), with subcolumns (Actual, Growth%, Ach%)
- Horizontal scroll (required)

**Capabilities**
- Sorting (single-column, optional multi-sort)
- Search (entity name)
- Pagination OR virtual scrolling (for large datasets)
- Conditional formatting rules from config (positive/negative/zero thresholds)
- Tooltips for abbreviations (Act, %G, %Ach)

**Export**
- Export current view (filtered) as CSV/Excel
- Export should match table columns & metric mode

---

### 1.7 Drilldown (Universal)
**Trigger**
- Clicking a row (entity), a KPI card, or an action button

**Presentation**
- Right-side drawer (recommended) OR dedicated page route

**Contents (config-driven)**
- Entity summary KPIs
- Trend chart (time series)
- Breakdowns by dimension (top products, top customers)
- Related transactions list (optional)

---

### 1.8 States (Universal)
- **Loading**: skeleton for KPI cards + table rows
- **Empty**: “No data for selection” with reset/clear suggestions
- **Error**: message + retry; include request id/correlation id (if provided)

---

### 1.9 Permissions / Role-based Rendering (Universal)
- Backend provides permissions (or role) and allowed filter values
- Frontend:
  - Hides/disabled controls not allowed
  - Prevents export if not permitted
  - Ensures UI never assumes access to data

---

## 2) Configuration-Driven Architecture (How Config Works)

### 2.1 Core Idea
All reports use the same components:
- `ReportShell`
- `FilterBar`
- `SegmentControls`
- `KpiGrid`
- `DataTable`
- `DrilldownDrawer`

A report is defined by a **Report Config JSON** that describes:
- Data endpoints
- Filters & dependencies
- KPI cards
- Table column groups
- Drilldowns
- Formatting rules

---

### 2.2 Suggested Folder Structure (React/Next example)
```
src/
  reports/
    configs/
      salesDistributor.json
      stockPlanning.json
  dashboard/
    ReportShell.tsx
    filter/
      FilterBar.tsx
      AdvancedFilterDrawer.tsx
      filterTypes.ts
      useFilterState.ts
    kpi/
      KpiGrid.tsx
      KpiCard.tsx
    table/
      DataTable.tsx
      columnBuilder.ts
      formatters.ts
    drilldown/
      DrilldownDrawer.tsx
      widgets/
        TrendChart.tsx
        BreakdownTable.tsx
  api/
    client.ts
    reportApi.ts
  state/
    queryKeys.ts
```

---

### 2.3 Report Config Schema (Practical)
Below is a *minimum viable* schema. Adjust as needed.

```json
{
  "reportId": "primary-distributor-sales",
  "title": "Primary Distributor Sales Dashboard",
  "description": "Performance by category and distributor/customer.",
  "defaults": {
    "time": { "fiscalYear": "2025-2026", "period": "Dec" },
    "toggles": { "aggregation": "YTD", "metricMode": "VALUE" },
    "segments": { "channelType": "CHANNEL", "entityType": "DISTRIBUTOR" }
  },
  "data": {
    "endpoints": {
      "meta": "/api/reports/{reportId}/meta",
      "kpis": "/api/reports/{reportId}/kpis",
      "table": "/api/reports/{reportId}/table",
      "drilldown": "/api/reports/{reportId}/drilldown"
    }
  },
  "filters": [
    {
      "key": "channelType",
      "label": "Channel Type",
      "type": "single",
      "ui": "tabs",
      "optionsSource": "static",
      "options": [
        { "label": "Channel", "value": "CHANNEL" },
        { "label": "Institutional", "value": "INSTITUTIONAL" }
      ]
    },
    {
      "key": "zone",
      "label": "Zone",
      "type": "single",
      "ui": "chips",
      "optionsSource": "api",
      "endpoint": "/api/dimensions/zones"
    },
    {
      "key": "state",
      "label": "State",
      "type": "multi",
      "ui": "chips",
      "dependsOn": ["zone"],
      "optionsSource": "api",
      "endpoint": "/api/dimensions/states?zone={zone}"
    }
  ],
  "kpis": {
    "cards": [
      {
        "id": "project-wires",
        "title": "Project Wires",
        "primaryMetric": "actualSales",
        "secondaryMetric": "targetSales",
        "shareMetric": "contributionPct",
        "trendMetric": "growthPct",
        "onClick": { "type": "filter", "filterKey": "category", "value": "PROJECT_WIRES" }
      }
    ]
  },
  "table": {
    "entityColumn": { "key": "entityName", "label": "Distributor/Customer", "pinned": true },
    "columnGroups": [
      {
        "groupLabel": "Project Wires",
        "groupKey": "PROJECT_WIRES",
        "columns": [
          { "key": "projectWires_actualSales", "label": "Act", "format": "currencyCr" },
          { "key": "projectWires_growthPct", "label": "%G", "format": "percent", "conditional": "posNeg" }
        ]
      }
    ]
  },
  "formatRules": {
    "conditionalStyles": {
      "posNeg": {
        "positive": { "icon": "arrowUp" },
        "negative": { "icon": "arrowDown" },
        "zero": { "icon": "dash" }
      }
    }
  },
  "drilldown": {
    "enabled": true,
    "widgets": ["entitySummary", "trendChart", "breakdownByCategory"]
  }
}
```

---

### 2.4 Config-Driven Rendering Rules
- UI components read config and render controls dynamically
- Column builder converts `columnGroups` into table columns
- Filter system uses config to:
  - Build form fields
  - Validate dependencies
  - Fetch options lists

---

### 2.5 Reusability Checklist
To add a new report you should only need to:
- Create a new config file
- Ensure backend supports the `reportId`
- Register route: `/reports/:reportId`

No new UI components should be required unless new visualization type is needed.

---

## 3) Cursor Prompts (Step-by-Step)

> Use these prompts sequentially in Cursor. Replace `[STACK]` if needed (React/Next suggested).

### Prompt 1 — Scaffold the dashboard framework
**Goal:** Create base components and routing.

**Prompt:**
> Build a config-driven reporting dashboard in [STACK] with these components: ReportShell, FilterBar, AdvancedFilterDrawer, SegmentControls, KpiGrid/KpiCard, DataTable, DrilldownDrawer. Use TypeScript, React Query for data fetching, and a central ReportConfig type. Provide minimal styling with CSS modules or Tailwind. Include a sample config JSON and a demo page rendering it.

---

### Prompt 2 — Implement filter state model
**Goal:** Pending vs Applied state, Apply/Clear/Reset.

**Prompt:**
> Implement a filter state system with pending and applied states. Pending changes do not refetch until Apply. Add Clear (clears pending), Reset to Defaults (restore config defaults). Sync applied filters to URL query params. Provide hooks: useReportFilters(reportConfig).

---

### Prompt 3 — Dependent filters + option fetching
**Goal:** Zone → State and similar dependencies.

**Prompt:**
> Add support for dependent filters defined in config (dependsOn). When parent filter changes, refresh child options and clear invalid selections. Implement options fetching from endpoint templates with tokens like {zone}. Add search within options for long lists.

---

### Prompt 4 — KPI cards rendering + interactions
**Prompt:**
> Implement KpiGrid rendering KPI cards from config. Each card shows icon, title, primary metric, secondary metric, share %, growth %, and trend arrow. Add onClick actions: apply filter, highlight table group, or open drilldown. Metrics come from /kpis endpoint.

---

### Prompt 5 — Table column builder from config
**Prompt:**
> Implement DataTable with column groups generated from config.table.columnGroups. Support pinned entity column, sticky headers, horizontal scroll, sorting, table search, pagination/virtual scroll toggle. Apply formatters and conditional style rules from config.

---

### Prompt 6 — Export current view
**Prompt:**
> Add export functionality: export filtered table data to CSV and Excel. Export should use current applied filters and visible columns. Provide UI button in header; disable if backend says export not allowed.

---

### Prompt 7 — Drilldown drawer
**Prompt:**
> Implement DrilldownDrawer that opens when clicking a table row. Fetch /drilldown endpoint with entityId and applied filters. Render widgets based on config: entity summary KPIs, trend chart, and breakdown table. Provide loading/error/empty states.

---

### Prompt 8 — System states & UX polish
**Prompt:**
> Add skeleton loading states for KPI cards and table rows, empty states with reset CTA, error states with retry. Add tooltips for abbreviations like Act, %G, %Ach. Ensure responsive behavior: desktop + tablet; mobile fallback scroll.

---

### Prompt 9 — Permissions-driven UI
**Prompt:**
> Add permissions support: backend returns allowed zones/states/categories and feature flags (export allowed, drilldown allowed). Hide/disable UI elements accordingly. Ensure frontend never shows options outside allowed sets.

---

## 4) Backend/Data Connection (How to Integrate)

### 4.1 Integration Model
Frontend calls backend endpoints for:
- Metadata (timestamp, allowed filters, feature flags)
- KPI metrics
- Table dataset (paginated)
- Drilldown data
- Export (server-side export preferred)

Use a consistent `reportId` so the same UI can support multiple reports.

---

### 4.2 Recommended API Endpoints
#### 1) Meta
`GET /api/reports/:reportId/meta?filters=...`

Returns:
- lastUpdatedAt
- allowedValues per filter (optional but recommended)
- feature flags (export/drilldown)
- column overrides (optional)

Example response:
```json
{
  "lastUpdatedAt": "2025-12-31T11:05:00Z",
  "features": { "export": true, "drilldown": true },
  "allowed": {
    "zone": ["NORTH","WEST","SOUTH"],
    "state": ["DL","HR","MH"]
  }
}
```

#### 2) KPI Cards
`POST /api/reports/:reportId/kpis`

Body:
```json
{
  "filters": {},
  "toggles": { "aggregation": "YTD", "metricMode": "VALUE" },
  "time": { "fiscalYear": "2025-2026", "period": "DEC" }
}
```

Response:
```json
{
  "cards": [
    {
      "id": "project-wires",
      "actualSales": 430.5,
      "targetSales": 0.0,
      "contributionPct": 51,
      "growthPct": 0
    }
  ]
}
```

#### 3) Table Data
`POST /api/reports/:reportId/table`

Body:
```json
{
  "filters": {},
  "toggles": {},
  "time": {},
  "pagination": { "page": 1, "pageSize": 50 },
  "sort": { "key": "overall_actualSales", "dir": "desc" },
  "search": "prabhat"
}
```

Response:
```json
{
  "rows": [
    {
      "entityId": "D123",
      "entityName": "MULTICAB CORPORATION",
      "projectWires_actualSales": 50.7,
      "projectWires_growthPct": 125
    }
  ],
  "page": 1,
  "pageSize": 50,
  "total": 2380
}
```

#### 4) Drilldown
`POST /api/reports/:reportId/drilldown`

Body includes `entityId` + applied filters/toggles/time.

Response contains:
- entity summary
- time series points
- breakdown lists

#### 5) Export
Option A (server-side):
- `POST /api/reports/:reportId/export` → returns file URL/token

Option B (client-side):
- Use `/table` with large pageSize and generate CSV locally (only for small datasets)

---

### 4.3 Authentication & Headers
Frontend should send:
- `Authorization: Bearer <token>` OR session cookie
- `X-Request-Id` (generated client-side) for tracing
- `X-Report-Id` optional

Backend should respond with:
- correlation id in error payload
- consistent error shape:
```json
{ "error": { "message": "…", "code": "…", "requestId": "…" } }
```

---

### 4.4 Caching & Performance
Recommended approach:
- React Query caching keyed by:
  - reportId
  - appliedFilters
  - toggles
  - time selectors
  - pagination/sort/search
- Debounce search input (300ms)
- Use server pagination for large tables
- Use option list caching for dimension endpoints

---

### 4.5 Formatting Rules
Backend returns raw numbers; frontend formats via config:
- currencyCr (crores)
- percent
- integer
- compact notation

If currency units vary per report, include in meta:
- currency symbol
- scaling unit (Cr/Lakh/Thousands)

---

### 4.6 Configuration Delivery Options
**Option 1: Config in code repo**
- `reports/configs/*.json`
- Best for versioning and controlled releases

**Option 2: Config from backend**
- `GET /api/reports/:reportId/config`
- Best for dynamic updates (requires robust validation)

Recommendation: Start with **Option 1**, later move to **Option 2** if needed.

---

## 5) Acceptance Criteria (Minimum)
A build is acceptable when:
- User can load report, see last updated timestamp
- User can apply filters (including dependent filters) and see KPIs + table update
- User can switch toggles (YTD/QTD, metric mode) and view updates
- Table supports sorting, search, pagination/virtual scroll, horizontal scroll
- KPI cards display and click actions work
- Drilldown opens for entity and displays data
- Export works and respects filters
- Loading/empty/error states are implemented

---

## 6) Developer Handoff Notes (Practical)
- Prefer **config-driven** over hardcoded columns.
- Keep **single filter state hook**; do not let each component manage its own state.
- Ensure URL sync for shareable links.
- Use typed interfaces for config + API responses.

---

## Appendix A — Example “Filter Endpoint Template” Tokens
Supported template tokens:
- `{zone}`, `{state}`, `{channelType}`, `{entityType}`
- `{fiscalYear}`, `{period}`, `{aggregation}`, `{metricMode}`

Template replacement should:
- URL encode values
- Handle arrays (comma-separated or repeated params) consistently

---

## Appendix B — Suggested Libraries (Optional)
- React Query (TanStack Query)
- TanStack Table (for table rendering)
- Zod (config + response validation)
- Date library: dayjs or date-fns
- Tooltip component library of your choice

---

*End of document.*
