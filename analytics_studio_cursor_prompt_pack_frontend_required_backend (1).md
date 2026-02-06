# Analytics Studio – Cursor Prompt Pack (Frontend + Required Backend)

> **Purpose**  
This document contains **copy-paste ready Cursor prompts** to generate the **Analytics Studio frontend** along with **all supporting backend APIs required for it to function**.

It is aligned with:
- Approved PRD + FRD
- Existing analytics backend (semantic layer, calculation engine)
- Two data ingestion modes (SQL + CSV)
- Project-based workspace model

This file is intended to be **downloaded and used directly by developers**.

---

## HOW TO USE THIS FILE (IMPORTANT)

- Run **one prompt at a time** in Cursor
- Always run prompts inside the **relevant folder** (frontend / backend)
- Prefer "extend existing codebase" instead of regenerate
- After generation, manually review types and API contracts

---

# SECTION A — FULL SYSTEM SCAFFOLD

## A1. Monorepo Scaffold (Frontend + Backend)

**Cursor Prompt**
```
You are creating an Analytics Studio platform.

Task:
1. Scaffold a monorepo with:
   - frontend/ (React + TypeScript)
   - backend/ (FastAPI or Node.js – keep modular)
2. Shared contracts for:
   - Dataset
   - Semantic definitions
   - Visual config

Constraints:
- Frontend must be fully decoupled
- Backend must be API-first
- Avoid tight coupling between SQL and UI

Output:
- Folder structure
- README per service
```

---

# SECTION B — BACKEND PROMPTS (REQUIRED FOR FRONTEND)

## B1. Project Management APIs

**Cursor Prompt**
```
Build backend APIs for a project-based analytics studio.

Requirements:
- Create project
- List projects
- Update project metadata
- Delete project

Each project should:
- Own uploaded datasets
- Own dashboards
- Be isolated from others

Deliver:
- DB schema
- REST APIs
- Access control checks
```

---

## B2. SQL Database Connection Manager

**Cursor Prompt**
```
Implement a SQL database connection manager.

Requirements:
- Support PostgreSQL, MySQL
- Read-only connections
- Environment based configs (dev/uat/prod)
- Connection pooling

Expose APIs:
- Create connection (admin only)
- Test connection
- List available datasets (tables/views)

Security:
- No credentials exposed to frontend
```

---

## B3. File Upload & Storage Service

**Cursor Prompt**
```
Implement file upload service for analytics studio.

Requirements:
- Accept CSV and XLSX
- Store files per project
- Persist metadata in DB
- Validate file size & format

Deliver:
- Upload API
- Storage abstraction (local/S3)
- File metadata schema
```

---

## B4. Dataset Registry & Semantic Binding

**Cursor Prompt**
```
Build dataset registry APIs.

Responsibilities:
- Register SQL datasets
- Register uploaded file datasets
- Bind semantic JSON
- Version semantic definitions

Expose:
- List datasets per project
- Get dataset schema
- Update semantic version
```

---

## B5. Query Execution API (Studio Runtime)

**Cursor Prompt**
```
Implement query execution API for Studio.

Input:
- Dataset ID
- Visual config JSON
- Filters
- Time range

Behavior:
- Enforce semantic rules
- Delegate calculations to calculation engine
- Return visualization-ready data

Deliver:
- Request/response schema
- Validation rules
```

---

# SECTION C — FRONTEND PROMPTS (REACT)

## C1. Frontend Base Setup

**Cursor Prompt**
```
Set up a React + TypeScript frontend for Analytics Studio.

Requirements:
- Modern folder structure
- API service layer
- Global state management
- Role-based access handling

Deliver:
- Project structure
- Base layout
- Auth-ready routing
```

---

## C2. Project Workspace UI

**Cursor Prompt**
```
Build Project Workspace UI.

Features:
- Create project
- List projects
- Select active project

Behavior:
- Project selection scopes all data

Deliver:
- React components
- API integration
```

---

## C3. Dataset Explorer UI

**Cursor Prompt**
```
Build Dataset Explorer UI.

Features:
- List datasets (SQL + uploaded)
- Preview dataset rows
- Show semantic schema

Constraints:
- No raw SQL shown
- Semantic fields only

Deliver:
- Dataset sidebar
- Dataset preview panel
```

---

## C4. File Upload UI (CSV / Spreadsheet)

**Cursor Prompt**
```
Build file upload UI for analytics studio.

Flow:
- Select project
- Upload CSV/XLSX
- Show profiling summary
- Confirm dataset creation

Deliver:
- Upload component
- Progress handling
- Error states
```

---

## C5. Visual Builder UI (Core)

**Cursor Prompt**
```
Build Visual Builder UI similar to Power BI (simplified).

Features:
- Visual type selector
- Dimension picker
- Measure picker
- Time grain selector
- Filter controls

Deliver:
- Visual config state model
- UI components
- Validation feedback
```

---

## C6. Calculation Builder UI

**Cursor Prompt**
```
Build Calculation Builder UI.

Features:
- Formula editor
- Semantic field picker
- Live validation
- Preview results

Constraints:
- No free SQL
- Human-readable formulas only
```

---

## C7. Dashboard Canvas UI

**Cursor Prompt**
```
Build Dashboard Canvas UI.

Features:
- Drag & drop visuals
- Grid-based layout
- Cross-filtering
- Time drill-down

Deliver:
- Canvas component
- Visual containers
```

---

# SECTION D — SAMPLE DATA & DEMO SUPPORT

## D1. Sample Dataset Generator (Backend)

**Cursor Prompt**
```
Implement sample dataset generator for Analytics Studio.

Requirements:
- Generate sales-like data
- Include time, numeric, categorical columns
- Configurable size

Use cases:
- UI demo
- Testing
```

---

## D2. Sample Dashboard Seeder

**Cursor Prompt**
```
Create sample dashboards programmatically.

Dashboards should include:
- KPI cards
- Line chart
- Bar chart
- % contribution

Deliver:
- Seed scripts
- Sample configs
```

---

# SECTION E — GOVERNANCE, CHANGELOG & SAFETY

## E1. Changelog System

**Cursor Prompt**
```
Implement changelog tracking for Analytics Studio.

Track changes for:
- Projects
- Datasets
- Calculations
- Dashboards

Each entry must store:
- User
- Timestamp
- Change summary
```

---

## E2. Dependency Safety Checks

**Cursor Prompt**
```
Implement dependency safety checks.

Rules:
- Prevent deleting datasets used in dashboards
- Warn on semantic changes

Deliver:
- Validation logic
- Error messages
```

---

# FINAL NOTES FOR DEVELOPERS

- Frontend must be thin
- Backend owns all logic
- Semantic layer is mandatory
- Projects are isolation boundaries

This prompt pack is the **official implementation guide** for Analytics Studio frontend + required backend.
Any new feature must add a new prompt here.

