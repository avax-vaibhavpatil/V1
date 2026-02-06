# Analytics Dashboard - Changelog

All notable changes to the Analytics Dashboard module will be documented in this file.

---

## [1.1.0] - 2026-01-29

### Added

#### AI Data Assistant (`frontend/src/analytics/components/ReportAIChat.tsx`)
- **Natural Language Queries**: Ask questions about your report data in plain English
- **Floating Chat Interface**: Sleek floating button that expands to full chat panel
- **Smart Data Analysis**: Analyzes current filtered data and provides insights
- **Suggested Questions**: Pre-built questions for quick insights
- **Confidence Indicators**: Shows confidence level for each response
- **Markdown Support**: Rich formatted responses with tables, lists, and highlights

#### Data Analyzer Engine (`frontend/src/analytics/utils/dataAnalyzer.ts`)
- Pattern-based question recognition for:
  - Top/Bottom performers analysis
  - Category-specific insights
  - Category comparisons (e.g., "Compare HDC vs Flexibles")
  - Growth analysis (trending up/down entities)
  - Achievement analysis (target vs actual)
  - Zone-wise breakdown
  - Entity counts and averages
  - Report summaries
- Context-aware analysis using current filters and aggregation
- Currency and percentage formatting in responses

#### Supported Questions
- "Who are the top 5 performers?"
- "Show me bottom performers"
- "What are the total sales?"
- "How is Project Wires performing?"
- "Compare HDC vs Flexibles"
- "Show growth analysis"
- "Target achievement summary"
- "Zone-wise breakdown"
- "How many distributors?"
- "Give me a summary"

### UI/UX
- Purple gradient theme matching dashboard design
- Typing animation with bouncing dots
- Smooth slide-in/out transitions
- Minimizable chat window
- Clear chat functionality
- Message history during session
- Mobile-responsive design

---

## [1.0.1] - 2026-01-29

### Fixed
- Fixed invisible text in ACT and %ACH columns by adding default `text-gray-700` color
- Columns without conditional formatting now display correctly

---

## [1.0.0] - 2026-01-27

### Added

#### Core Architecture
- **Config-Driven Design**: All reports are defined via TypeScript/JSON configuration
- **Data Adapter Pattern**: Mock data layer mirrors real API contract for easy swap to production APIs
- **URL State Sync**: Applied filters sync to URL query params for shareable links
- **Pending/Applied Filter Model**: Changes don't trigger refetch until "Apply" is clicked

#### Mock Data Generator (`frontend/src/analytics/data/mockDataGenerator.ts`)
- Generates 1,200+ rows of realistic sales data
- Includes distributors (60%) and customers (40%)
- 5 zones with realistic state mappings (NORTH, SOUTH, EAST, WEST, CENTRAL)
- 6 product categories: Project Wires, Flexibles, HDC, Dowells, FMEG, Lumes
- Metrics: Actual Sales, Target Sales, Growth %, Achievement %, Contribution %
- Mix of positive (65%), negative (20%), and zero (15%) growth cases
- Trend data generation for 12-month time series
- Breakdown data by category and product

#### Data Adapter (`frontend/src/analytics/data/dataAdapter.ts`)
- Simulates API endpoints: `/meta`, `/kpis`, `/table`, `/drilldown`
- Implements filtering by zone, state, channel type, entity type, category
- Supports sorting on any column
- Full-text search on entity name and code
- Server-side pagination simulation
- Aggregation modes: YTD, QTD, MTD
- CSV export functionality

#### Filter State Management (`frontend/src/analytics/hooks/useReportFilters.ts`)
- Pending vs Applied state pattern
- URL synchronization for shareable links
- Apply/Clear/Reset actions
- Dependent filter support (Zone → State)
- Filter count tracking

#### Components

##### ReportHeader (`frontend/src/analytics/components/ReportHeader.tsx`)
- Report title and description
- Last updated timestamp with relative time
- Action buttons: Refresh, Share, Export
- Export dropdown (CSV/Excel)

##### FilterBar (`frontend/src/analytics/components/FilterBar.tsx`)
- Fiscal year and period selectors
- Aggregation toggle (YTD/QTD/MTD)
- Metric mode selector (Value/Volume/Units)
- Advanced filter drawer
- Applied filters chip display
- Dependent filter cascading

##### SegmentControls (`frontend/src/analytics/components/SegmentControls.tsx`)
- Tab-based controls for quick filtering
- Chip-based multi-select controls
- Auto-apply on segment change

##### KpiCard (`frontend/src/analytics/components/KpiCard.tsx`)
- Icon with category indicator
- Primary metric (actual sales)
- Secondary metric (target)
- Contribution percentage badge
- Trend indicator with conditional coloring
- Click actions: filter, highlight column group
- Skeleton loading state

##### DataTable (`frontend/src/analytics/components/DataTable.tsx`)
- Sticky header with column groups
- Pinned entity column
- Horizontal scroll with custom scrollbar
- Sortable columns with visual indicators
- Search functionality
- Pagination with page number display
- Conditional formatting (positive/negative colors)
- Row click for drilldown
- Empty state with helpful message
- Skeleton loading state

##### DrilldownDrawer (`frontend/src/analytics/components/DrilldownDrawer.tsx`)
- Right-side drawer with slide-in animation
- Entity summary with gradient header
- Monthly trend bar chart
- Category breakdown with progress bars
- Product breakdown with growth indicators
- Loading and error states

##### ReportShell (`frontend/src/analytics/components/ReportShell.tsx`)
- Main orchestration component
- Manages all data fetching
- Coordinates filter state
- Handles KPI click actions
- Manages drilldown state

#### Sample Configuration (`frontend/src/analytics/config/primaryDistributorSales.ts`)
- Complete report configuration for Primary Distributor Sales
- 6 KPI cards with click actions
- 7 column groups with 3 columns each
- Full filter configuration
- Drilldown widget configuration

#### Routing
- `/analytics` - Default analytics dashboard
- `/analytics/:reportId` - Dynamic report loading
- Sidebar link to Sales Dashboard

#### Styling
- Slide-in animation for drilldown drawer
- Custom scrollbar for horizontal scroll
- Responsive design (desktop + tablet)
- Tailwind CSS for all styling

### Architectural Decisions

1. **TypeScript-First**: All configs and data structures are fully typed
2. **No External BI Tools**: Built entirely with React + Tailwind
3. **Component Composition**: Small, focused components composed into larger ones
4. **Hook-Based State**: Custom hooks for filter management and data fetching
5. **Mock-First Development**: Data adapter can be swapped with real APIs
6. **URL as Source of Truth**: Filters sync to URL for bookmarkable views

### File Structure

```
frontend/src/analytics/
├── components/
│   ├── DataTable.tsx
│   ├── DrilldownDrawer.tsx
│   ├── FilterBar.tsx
│   ├── KpiCard.tsx
│   ├── ReportAIChat.tsx      # NEW - AI Chat Assistant
│   ├── ReportHeader.tsx
│   ├── ReportShell.tsx
│   ├── SegmentControls.tsx
│   └── index.ts
├── config/
│   ├── primaryDistributorSales.ts
│   └── index.ts
├── data/
│   ├── dataAdapter.ts
│   ├── mockDataGenerator.ts
│   └── index.ts
├── hooks/
│   ├── useReportFilters.ts
│   └── index.ts
├── types/
│   ├── config.ts
│   └── index.ts
├── utils/
│   ├── dataAnalyzer.ts       # NEW - AI Analysis Engine
│   ├── formatters.ts
│   └── index.ts
└── index.ts
```

### Breaking Changes
- None (new module)

---

## [0.1.0] - 2026-01-27

### Added
- Initial project setup
- Analytics Studio backend with FastAPI
- Frontend with React + TypeScript + Vite
- Basic project, dataset, and dashboard management

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles.*
