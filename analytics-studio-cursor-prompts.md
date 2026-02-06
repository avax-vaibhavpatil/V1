# Analytics Studio – Cursor Prompt Pack

> **Purpose**: This document contains **ready-to-use prompts** for building the Analytics Studio using **Cursor**.  
> Each prompt is written so developers can paste it directly into Cursor to generate code, refactors, documentation, or architecture safely and consistently.

This file is meant to be **downloadable and reusable** across teams.

---

## 0. How to Use This File (Important)

- Use **one prompt at a time** in Cursor
- Always mention:
  - Existing codebase context
  - Tech stack (Frontend / Backend / DB)
- Prefer **"extend existing code"** over regenerate

---

# SECTION A — SYSTEM & ARCHITECTURE PROMPTS

## A1. Studio Architecture Scaffold

**Prompt**
```
You are building an Analytics Studio inspired by Power BI but simplified.

Context:
- Data source: Wide analytics tables (daily grain)
- Semantic layer: Column-centric JSON defining dimensions, measures, aggregations
- Users must not write SQL

Task:
1. Propose a clean modular architecture for:
   - Dataset service
   - Semantic service
   - Calculation engine
   - Query engine
   - Visualization config layer
2. Explain responsibilities of each module
3. Suggest folder structure

Constraints:
- Must be extensible
- Must enforce semantic rules
- Avoid overengineering
```

---

## A2. Semantic Layer → Studio Mapping

**Prompt**
```
Given a semantic layer JSON that defines:
- dataset grain
- time columns
- dimensions
- measures with allowed aggregations

Task:
1. Design a parser that converts semantic JSON into:
   - UI-selectable fields
   - Validation rules
   - Query-safe expressions
2. Show example input/output structures
3. Highlight validation edge cases
```

---

# SECTION B — DATASET & DB MANAGEMENT PROMPTS

## B1. Database Connection Manager

**Prompt**
```
Design a database connection manager for an analytics platform.

Requirements:
- Support multiple environments (dev / uat / prod)
- Read credentials securely (env / secrets manager)
- Support read-only analytics users
- Connection pooling
- Graceful failure handling

Deliver:
- Connection lifecycle design
- Example implementation
- Best practices
```

---

## B2. Dataset Registration & Metadata Sync

**Prompt**
```
We need a dataset registration system for Analytics Studio.

Context:
- Datasets are wide tables
- Each dataset must be linked to a semantic JSON

Task:
1. Design DB tables to store:
   - Dataset metadata
   - Semantic file reference
   - Versioning
2. Provide APIs for:
   - Register dataset
   - Update semantic version
   - Deprecate dataset

Include validation rules.
```

---

# SECTION C — CALCULATION ENGINE PROMPTS

## C1. Calculation DSL Design

**Prompt**
```
Design a calculation DSL for an analytics studio.

Requirements:
- Support arithmetic operations
- Support SUM, AVG, COUNT
- Support IF / CASE
- Prevent nested aggregations
- Must be human-readable

Deliver:
- DSL syntax examples
- Validation rules
- Error messages for invalid formulas
```

---

## C2. Measure Execution Engine

**Prompt**
```
Build a measure execution engine.

Context:
- Input: user-defined calculated measure
- Data: aggregated wide table data

Task:
1. Convert validated formulas into executable query logic
2. Handle division by zero
3. Ensure aggregation correctness
4. Support time-based offsets

Output:
- Pseudocode
- Execution flow
```

---

# SECTION D — TIME INTELLIGENCE PROMPTS

## D1. Time Comparison Engine

**Prompt**
```
Design a time intelligence engine for analytics.

Supported comparisons:
- Previous period
- Same period last year
- Rolling window (7, 30, 90 days)

Rules:
- Must respect dataset grain
- Must use semantic time column

Provide:
- Logic per comparison
- Query generation examples
- Edge cases
```

---

# SECTION E — VISUALIZATION PROMPTS

## E1. Visual Configuration Schema

**Prompt**
```
Design a JSON schema for visual configuration in Analytics Studio.

Visuals:
- KPI Card
- Line Chart
- Bar / Column
- Stacked Bar
- Table

Each visual must define:
- Dimensions
- Measures
- Filters
- Sorting
- Time grain

Provide examples for each visual.
```

---

## E2. Percentage & Contribution Logic

**Prompt**
```
Implement percentage-based analytics logic.

Types:
1. % of total
2. % change over time

Task:
- Define backend computation logic
- Ensure accuracy across filters
- Provide test cases
```

---

# SECTION F — DASHBOARD & UX PROMPTS

## F1. Dashboard Composition Engine

**Prompt**
```
Design a dashboard composition system.

Requirements:
- Multiple visuals per dashboard
- Grid-based layout
- Cross-filtering
- Drill-down by time

Deliver:
- Dashboard schema
- Interaction flow
- State management approach
```

---

## F2. UX Error Handling

**Prompt**
```
Design UX error handling for Analytics Studio.

Rules:
- Errors must be human-readable
- Prevent invalid configurations

Provide:
- Error taxonomy
- Sample messages
- UI behavior
```

---

# SECTION G — GOVERNANCE & SECURITY PROMPTS

## G1. Role-Based Access Control

**Prompt**
```
Design RBAC for Analytics Studio.

Roles:
- Viewer
- Editor
- Analyst
- Admin

Task:
- Define permissions per role
- Enforce at API and UI level
- Provide schema and middleware examples
```

---

# SECTION H — CHANGELOG & VERSIONING PROMPTS

## H1. Changelog System Design

**Prompt**
```
Design a changelog system for Analytics Studio.

Track changes for:
- Calculations
- Semantic definitions
- Dashboards

Each change must record:
- Who
- What
- When
- Impacted assets

Deliver:
- DB schema
- API design
- Example changelog entries
```

---

## H2. Calculation Versioning & Rollback

**Prompt**
```
Implement versioning for calculated measures.

Requirements:
- Maintain history
- Allow rollback
- Prevent breaking dashboards

Provide:
- Versioning strategy
- Dependency tracking
- Rollback flow
```

---

# SECTION I — PERFORMANCE & SCALING PROMPTS

## I1. Query Optimization Strategy

**Prompt**
```
Optimize analytics queries for wide tables.

Context:
- Daily incremental data
- Large volumes

Task:
- Partition strategy
- Caching layers
- Query limits
- Cost control
```

---

# SECTION J — TESTING & QUALITY PROMPTS

## J1. Analytics Studio Test Plan

**Prompt**
```
Create a test strategy for Analytics Studio.

Include:
- Unit tests for calculations
- Integration tests for queries
- Performance tests
- Data accuracy validation
```

---

# FINAL NOTE

This prompt pack is designed to:
- Prevent architectural drift
- Maintain semantic consistency
- Enable fast, safe development in Cursor

Treat this file as a **living document**. Any new Studio feature must add a new prompt here.


