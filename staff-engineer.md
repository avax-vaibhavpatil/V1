# NL → SQL Analytics Engine — Complete System Design
## Step-by-Step Execution Guide with Examples

> **Target:** 500+ tables · 200k QPS · Sub-second SLA · Multi-tenant · RBAC · Defense-in-depth security

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Control Plane — Startup & Background Services](#2-control-plane--startup--background-services)
   - 2.1 Schema Registry Service
   - 2.2 Embedding Manager
   - 2.3 Governance & Audit Service
3. [Query Planning Plane — Per-Request Flow](#3-query-planning-plane--per-request-flow)
   - 3.1 API Gateway
   - 3.2 Authentication & Tenant Extraction
   - 3.3 Early Cache Lookup *(Critical Position)*
   - 3.4 LLM Orchestrator
   - 3.5 Table Identification
   - 3.6 Intent Extraction
   - 3.7 Join Planner
   - 3.8 Analytical Engine
   - 3.9 SQL Builder
   - 3.10 SQL Validator
4. [Execution Plane — DB & Response](#4-execution-plane--db--response)
   - 4.1 RBAC Enforcement
   - 4.2 Multi-Tenant RLS Enforcement
   - 4.3 Query Cost Estimator
   - 4.4 Execute Query
   - 4.5 Result Cache
   - 4.6 Format Result
   - 4.7 Store Template Cache
   - 4.8 Observability & Metrics
5. [Complete End-to-End Walkthrough](#5-complete-end-to-end-walkthrough)
6. [Cache Key Architecture](#6-cache-key-architecture)
7. [Security Layers — Defense in Depth](#7-security-layers--defense-in-depth)
8. [Scalability Design Decisions](#8-scalability-design-decisions)
9. [Data Contracts — Interfaces Between Components](#9-data-contracts--interfaces-between-components)
10. [What Goes Wrong Without Each Component](#10-what-goes-wrong-without-each-component)

---

## 1. System Architecture Overview

The system is divided into **3 planes**, each with distinct responsibilities, scaling characteristics, and failure modes.

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTROL PLANE  (Stable · Low QPS · Versioned)                 │
│  Schema Registry ──► Embedding Manager ──► Audit Service       │
└─────────────────────────────────────────────────────────────────┘
                              │ feeds metadata into ▼
┌─────────────────────────────────────────────────────────────────┐
│  QUERY PLANNING PLANE  (High QPS · Stateless · Scalable)       │
│  API GW → Auth → Cache → Orchestrator → Table ID               │
│  → Intent (LLM) → Join Planner → Analytical Engine → SQL Build │
│  → SQL Validate                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │ validated SQL ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXECUTION PLANE  (High Load · Optimized · Observable)         │
│  RBAC → RLS → Cost Estimator → Execute → Result Cache          │
│  → Format → Store Template Cache → Observability               │
└─────────────────────────────────────────────────────────────────┘
```

**The core rule of this architecture:**

> The LLM **never generates SQL**. It only produces a structured JSON intent. All SQL is built deterministically by the SQL Builder. This prevents prompt injection from producing executable SQL.

---

## 2. Control Plane — Startup & Background Services

These components run **once at startup** and refresh on schema change. They do not participate in the per-request hot path.

---

### 2.1 Schema Registry Service

**Purpose:** Discover and maintain a live model of the entire database schema — tables, columns, foreign keys, indexes, and row counts. Build and maintain the join graph that the Join Planner will use.

**When it runs:** At application startup. Re-runs on schema change notification (DB event or polling interval).

**Execution steps:**

**Step 1 — Fetch schema from information_schema**

Query PostgreSQL's metadata tables to get the full picture of the database.

```sql
-- What you query:
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public';

SELECT tc.table_name, kcu.column_name,
       ccu.table_name AS foreign_table,
       ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ...
JOIN information_schema.constraint_column_usage ccu ...
WHERE tc.constraint_type = 'FOREIGN KEY';
```

**Step 2 — Fetch table statistics**

```sql
-- Row counts and sizes from pg_class
SELECT relname AS table_name,
       reltuples::bigint AS estimated_row_count,
       pg_size_pretty(pg_total_relation_size(oid)) AS total_size
FROM pg_class
WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace;
```

**Step 3 — Build the join graph**

The join graph is a directed graph where:
- Nodes = tables
- Edges = foreign key relationships

```
Example graph for e-commerce schema:

  orders ──────► customers
    │
    ▼
 order_items ──► products ──► categories
    │               │
    ▼               ▼
 discounts       suppliers
```

**Step 4 — Compute schema_version**

```python
# Hash of the entire schema snapshot
# Any column rename, new table, or FK change produces a new version
schema_version = sha256(json.dumps(schema_dict, sort_keys=True))
# Example: "a3f9b2c1d8e7..."
```

**Step 5 — Store in 3 locations**

| Location | Purpose |
|---|---|
| PostgreSQL metadata table | Persistent source of truth |
| S3 (JSON file) | Cross-instance bootstrap |
| In-memory (each instance) | Zero-latency access during requests |

**Output object:**

```json
{
  "schema_version": "a3f9b2c1d8e7...",
  "tables": {
    "sales": {
      "columns": ["id","product_id","category_id","amount","date","tenant_id"],
      "indexed_columns": ["product_id", "date", "tenant_id"],
      "row_count": 45000000
    },
    "product": {
      "columns": ["id","name","category_id","supplier_id"],
      "indexed_columns": ["id","category_id"],
      "row_count": 8500
    }
  },
  "join_graph": {
    "sales": ["product", "category"],
    "product": ["category", "supplier"],
    "order_items": ["sales", "product"]
  },
  "foreign_keys": [
    { "from": "sales.product_id", "to": "product.id" },
    { "from": "sales.category_id", "to": "category.id" }
  ]
}
```

---

### 2.2 Embedding Manager

**Purpose:** Precompute semantic vector embeddings for every table name, column name, and table description. Version them so cache invalidation works correctly across schema changes.

**When it runs:** At startup; re-runs when `schema_version` changes.

**Execution steps:**

**Step 1 — Generate embeddings for each table and column**

For each table, create a rich text description and embed it:

```
Input text for embedding:
"table: sales | columns: id, product_id, category_id, amount, date, tenant_id | 
description: transaction records with revenue amount per product and category"

Input text for embedding:
"table: product | columns: id, name, category_id, supplier_id | 
description: product catalog with name and categorization"
```

You embed these strings using a model like `text-embedding-3-large`. The output is a 1536-dimensional float vector per table.

**Step 2 — Store to S3 with version metadata**

```
s3://your-bucket/embeddings/
  v3.1/
    embeddings.npy       ← numpy array of all vectors [N_tables × 1536]
    table_index.json     ← maps vector index → table name
    metadata.json        ← version info
```

Metadata file:

```json
{
  "embedding_version": "v3.1",
  "embedding_model": "text-embedding-3-large",
  "schema_version": "a3f9b2c1d8e7...",
  "table_count": 500,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Step 3 — Load into memory per instance**

Each service instance loads the full embedding matrix into RAM at startup. For 500 tables × 1536 dimensions × float32 = ~3MB. This is trivial.

**Step 4 — Atomic swap on schema change**

When a new schema_version is detected:
1. Download new embeddings from S3 in background
2. Prepare new in-memory matrix
3. Atomic swap (swap pointer, not rebuild in place)
4. No request interruption, no downtime

---

### 2.3 Governance & Audit Service

**Purpose:** Record every query execution for compliance, debugging, billing, and security auditing. This is an enterprise requirement — every SQL query ever generated must be traceable.

**When it runs:** Asynchronously, after every query execution. Never on the critical path.

**What it records:**

```json
{
  "audit_id": "uuid-v4",
  "tenant_id": 42,
  "user_id": "user_881",
  "role": "analyst",
  "original_nl_query": "show top 3 products by revenue per category last month",
  "generated_sql": "SELECT * FROM (...) WHERE rnk <= 3",
  "tables_accessed": ["sales", "product", "category"],
  "sensitive_columns_accessed": [],
  "execution_time_ms": 187,
  "rows_returned": 9,
  "cache_hit": false,
  "llm_model_used": "gpt-4o-mini",
  "llm_latency_ms": 312,
  "timestamp": "2024-01-15T14:22:05Z",
  "schema_version": "a3f9b2c1d8e7...",
  "status": "success"
}
```

**Why sensitive_columns_accessed matters:** If a column like `salary`, `ssn`, or `credit_card_number` is accessed, it gets flagged here, enabling compliance review.

---

## 3. Query Planning Plane — Per-Request Flow

This is the hot path. Every incoming request flows through these components in strict order. All components are **stateless** — they read from shared memory/cache/DB but hold no per-instance state.

**The example query we'll trace through all steps:**

> User types: *"Show me top 3 products by revenue per category for last month"*

---

### 3.1 API Gateway

**Purpose:** The single entry point for all traffic. Handles cross-cutting concerns before any business logic runs.

**Responsibilities:**
- TLS termination
- Rate limiting (per tenant, per user)
- Request ID generation (for distributed tracing)
- Basic auth token presence check (not decoding — that's next step)
- Request/response logging
- Load balancing across planning plane instances

**What it passes downstream:**

```
Headers added to internal request:
  X-Request-ID: "req_a1b2c3d4"
  X-Forwarded-For: "client IP"
  X-Rate-Limit-Remaining: "847"

Body passed unchanged:
  { "query": "Show me top 3 products by revenue per category for last month",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9..." }
```

**Implementation choices:** Nginx, AWS API Gateway, Kong, or a FastAPI middleware layer.

---

### 3.2 Authentication & Tenant Extraction

**Purpose:** Decode the JWT and attach tenant context to every downstream operation. Everything from here on knows who is asking and what they're allowed to see.

**Execution steps:**

**Step 1 — Decode the JWT**

```
JWT payload after decoding:
{
  "sub": "user_881",
  "tenant_id": 42,
  "role": "analyst",
  "allowed_tables": ["sales", "product", "category", "orders"],
  "allowed_columns": {
    "sales": ["id", "amount", "date", "product_id", "category_id"],
    "product": ["id", "name", "category_id"]
    // Note: sales.cost, sales.margin NOT in allowed_columns for this role
  },
  "exp": 1705329600
}
```

**Step 2 — Build request context object**

```python
# This object travels with the request through every component
RequestContext = {
    "request_id": "req_a1b2c3d4",
    "tenant_id": 42,
    "user_id": "user_881",
    "role": "analyst",
    "allowed_tables": ["sales", "product", "category", "orders"],
    "allowed_columns": { ... },
    "schema_version": "a3f9b2c1d8e7...",   # loaded from registry
    "embedding_version": "v3.1",           # loaded from registry
    "timestamp": "2024-01-15T14:22:05Z"
}
```

**Why tenant_id here and not later:** Every downstream component — cache key, SQL validator, DB execution — needs tenant_id. Extracting it once here prevents repeated JWT decoding.

---

### 3.3 Early Cache Lookup — CRITICAL POSITION

**Purpose:** Before doing ANY expensive work (LLM call, embedding search, join planning), check if we've already answered this exact question for this role. If yes, skip the entire planning pipeline.

**Why position matters:** In the original design, cache lookup appeared AFTER table identification. That means even on cache hits, you'd still be burning time on embedding searches and rule-based filtering. The correct position is immediately after auth — the very next step.

**Execution steps:**

**Step 1 — Normalize the query**

```python
original:    "Show me top 3 products by revenue per category for last month"
normalized:  "show top 3 products revenue category last month"

# Normalization rules:
# - lowercase
# - remove stop words (me, by, for, the, a, an)
# - strip extra whitespace
# - sort synonyms to canonical form ("revenue" → "revenue", "sales" → "revenue" only if synonym map exists)
```

**Step 2 — Build the cache key**

```python
cache_key = sha256(
    normalized_query       +  # semantic identity
    role_signature         +  # RBAC scope
    schema_version         +  # schema freshness
    embedding_version         # model freshness
)

# role_signature = sha256(role + sorted(allowed_tables) + sorted(allowed_columns))
# Example role_signature for "analyst": "d4e5f6a7..."

# Final cache key: "7f3a9b2c..."
```

**Step 3 — Redis lookup**

```
Redis GET "nlsql:7f3a9b2c..."

HIT  → returns the SQL template stored previously
MISS → returns nil → continue to Step 3.4
```

**Step 4 — On cache HIT: validate before executing**

A SQL template stored 2 hours ago may reference a table that was dropped. Re-validate before executing:

```python
if cache_hit:
    sql = validate_sql(cached_template)  # AST parse, check tables still exist
    if valid:
        return execute(sql, ctx)         # proceed to execution plane
    else:
        invalidate_cache(cache_key)      # remove stale entry
        continue_to_planning()           # treat as miss
```

**Step 5 — On cache MISS: continue pipeline**

Nothing happens here. The request continues to Step 3.4.

---

### 3.4 LLM Orchestrator

**Purpose:** Control everything about LLM usage. This layer sits between the pipeline and any LLM API call. It never generates SQL. It manages cost, reliability, and routing.

**Why this exists:** Without an orchestrator, you have no way to:
- Route simple queries to cheap small models and complex queries to large models
- Enforce concurrent LLM call limits (prevents cost explosion under load)
- Implement retry with backoff on LLM API errors
- Track spend per tenant

**Execution steps:**

**Step 1 — Classify query complexity**

```python
# Heuristics (no LLM needed for this step):
complexity = "simple"

if any([
    query contains "rank" or "top N" or "per group",
    query contains "compare" or "vs" or "versus",
    query contains "running total" or "cumulative",
    query contains "year over year" or "month over month",
    len(identified_tables) >= 4
]):
    complexity = "complex"
```

**Step 2 — Route to appropriate model**

```
complexity = "simple"  →  model = gpt-4o-mini    (fast, cheap, ~$0.0001/query)
complexity = "complex" →  model = gpt-4o          (accurate, ~$0.003/query)
```

**Step 3 — Enforce concurrency limit**

```python
# Semaphore: max 50 concurrent LLM calls across all instances
# Prevents LLM API rate limit from cascading into system failure
async with llm_semaphore:
    response = await call_llm(model, prompt, timeout=8s)
```

**Step 4 — Retry policy**

```
Attempt 1: timeout 8s
Attempt 2 (if timeout): same model, timeout 8s
Attempt 3 (if timeout): fallback to gpt-4o-mini, timeout 5s
After 3 failures: return error to user
```

**Step 5 — Cost tracking**

```python
# After each LLM call:
cost_tracker.record(
    tenant_id=ctx.tenant_id,
    model=model_used,
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens
)
```

---

### 3.5 Table Identification

**Purpose:** From 500 possible tables, identify the 2–6 tables that are relevant to the user's query. Uses a 3-layer hybrid approach — layers run in order, each layer filters down the candidates.

**Input:** Normalized query + in-memory embeddings + join graph
**Output:** `["sales", "product", "category"]`

---

**Layer 1 — Rule-Based Filter**

Fast, zero-cost filtering using keyword matching and schema names.

```python
# Query: "show top 3 products by revenue per category for last month"

keyword_matches = {
    "products"  → matches table: "product"      (singular/plural match)
    "revenue"   → matches column: "sales.amount" → table: "sales"
    "category"  → matches table: "category"
    "last month"→ matches column: "sales.date"  → table: "sales"
}

# Candidates after Layer 1: ["product", "sales", "category"]
# Tables eliminated: orders, customers, suppliers, discounts, ...
```

Layer 1 reduces 500 tables to ~5–20 candidates in <1ms.

---

**Layer 2 — Embedding Similarity**

Embed the query, compute cosine similarity against all in-memory table vectors, take top-k.

```python
# Embed the query (this IS an LLM call — small, fast embedding model)
query_vector = embed("show top 3 products revenue category last month")
# Returns 1536-dim vector

# Cosine similarity against all 500 table vectors (in-memory matrix multiply)
scores = cosine_similarity(query_vector, all_table_vectors)
# [sales: 0.91, product: 0.88, category: 0.84, orders: 0.41, ...]

# Take top 3 from the Layer 1 candidates (not from all 500)
confirmed_tables = top_k(layer1_candidates, scores, k=5)
# Result: ["sales", "product", "category"]
```

Layer 2 runs in <2ms (pure matrix math, no network call after embedding).

---

**Layer 3 — Join Feasibility Check**

Verify that the confirmed tables can actually be connected via foreign keys. Prevents the SQL Builder from generating impossible JOINs.

```python
# Check join graph connectivity for: ["sales", "product", "category"]
# 
# join_graph shows:
#   sales.product_id  → product.id      ✓ connected
#   product.category_id → category.id   ✓ connected
#
# All 3 tables are reachable from "sales" (the fact table)
# ✓ FEASIBLE

# Counter-example: ["sales", "supplier"] with no FK path
# sales → product → supplier ← missing direct FK from sales to supplier
# Layer 3 would add "product" as a required bridge table
```

**Final output of Table Identification:**

```json
{
  "tables": ["sales", "product", "category"],
  "root_table": "sales",
  "join_paths": [
    "sales → product (via sales.product_id = product.id)",
    "product → category (via product.category_id = category.id)"
  ]
}
```

---

### 3.6 Intent Extraction

**Purpose:** The ONE place in the entire system where an LLM is used for reasoning. The LLM reads the query and relevant schema context, then returns a structured JSON plan describing WHAT to compute. It never writes SQL syntax.

**Input:** Query + identified table schemas + few-shot examples
**Output:** Structured JSON intent

**Step 1 — Build the LLM prompt**

```
SYSTEM:
You are a query intent extractor. Given a natural language analytics question
and the available schema, extract a structured query plan as JSON.

Rules:
- Return ONLY valid JSON, no prose, no code blocks
- "measure" must be a fully-qualified column: "table.column"  
- "filters" must be in canonical form: "last_month", "last_7_days", "this_year"
- "ranking" is only "top" or "bottom" or null
- "limit_per_group" is an integer or null

Available tables:
  sales: id, product_id, category_id, amount, date, tenant_id
  product: id, name, category_id
  category: id, category_name

USER:
Show me top 3 products by revenue per category for last month
```

**Step 2 — LLM response**

```json
{
  "measure": "sales.amount",
  "aggregation": "sum",
  "aggregation_alias": "revenue",
  "dimensions": [
    "category.category_name",
    "product.name"
  ],
  "filters": ["last_month"],
  "ranking": "top",
  "limit_per_group": 3,
  "partition_by": "category.category_name",
  "time_grain": "month",
  "having": null,
  "secondary_sort": null
}
```

**Why this is safe:** Even if a user injects `"; DROP TABLE sales; --"` into their query, the LLM only produces a JSON structure with field names. There is no SQL syntax in the output. The SQL Builder interprets the JSON, it does not interpolate string input from the LLM.

**Step 3 — Validate the JSON schema**

```python
# Before passing to Join Planner:
# 1. Check all required fields present
# 2. Check "measure" references a column in an allowed table
# 3. Check "dimensions" reference allowed columns
# 4. Reject if any field contains SQL keywords (extra safety)
```

---

### 3.7 Join Planner

**Purpose:** Given the set of required tables and the join graph, compute the optimal join order and join conditions. This is pure symbolic computation — no LLM, no ambiguity.

**Input:** Required tables + join graph + table row counts (from schema registry)
**Output:** Ordered join tree with conditions

**Execution steps:**

**Step 1 — Identify the root (fact table)**

```python
# The fact table is the table with the most foreign keys pointing TO it
# AND the highest row count
# AND it contains the measure column

candidates_with_scores = {
    "sales":    row_count=45M, is_measure_table=True   → score: HIGH
    "product":  row_count=8500, is_measure_table=False → score: LOW
    "category": row_count=200,  is_measure_table=False → score: LOW
}
root = "sales"
```

**Step 2 — BFS shortest path to all required tables**

```
Starting from root "sales", find path to each required table:

sales → product:   1 hop (direct FK: sales.product_id = product.id)  ✓
sales → category:  2 hops (sales → product → category)               ✓

Shortest path = sales → product → category (covers all 3 tables)
```

**Step 3 — Cost evaluation**

```python
# Estimate join cost to avoid expensive plans:

join_plan_1: sales JOIN product JOIN category
  cost = sales.rows × selectivity(product) × selectivity(category)
       = 45,000,000 × 0.0002 × 0.0000235
       = ~211 rows expected output
  indexed_joins: True (product_id and category_id are indexed)
  verdict: ACCEPTABLE

# vs a bad alternative:
join_plan_2: sales CROSS JOIN product (if no FK was found)
  cost = 45,000,000 × 8,500 = 382,500,000,000 rows
  verdict: REJECTED — cartesian join
```

**Step 4 — Prefer indexed joins**

```python
# For each join edge:
#   IF join column is in indexed_columns → prefer
#   IF join column is NOT indexed → flag for optimizer
#   IF join creates M:M → add intermediate aggregation or reject

join_conditions = [
    { "type": "INNER", "left": "sales.product_id",   "right": "product.id",      "indexed": True },
    { "type": "INNER", "left": "product.category_id", "right": "category.id",    "indexed": True }
]
```

**Final output:**

```json
{
  "root": "sales",
  "join_tree": [
    {
      "join_type": "INNER JOIN",
      "table": "product",
      "on": "sales.product_id = product.id",
      "estimated_selectivity": 0.0002
    },
    {
      "join_type": "INNER JOIN",
      "table": "category",
      "on": "product.category_id = category.id",
      "estimated_selectivity": 0.0000235
    }
  ],
  "estimated_output_rows": 211
}
```

---

### 3.8 Analytical Engine

**Purpose:** Translate the intent JSON into the correct SQL analytical pattern. The Analytical Engine knows about SQL constructs like window functions, CTEs, time bucketing, and derived metrics. It selects the right template.

**Input:** Intent JSON + join tree
**Output:** Analytical pattern + SQL template fragments

**Template selection logic:**

```
IF ranking != null AND limit_per_group != null:
    → Select "TOP N PER GROUP" template (uses RANK() OVER PARTITION BY)

IF aggregation in ["sum","count","avg"] AND dimensions exist:
    → Select "GROUPED AGGREGATION" template

IF time_grain in ["day","week","month","year"] AND aggregation:
    → Select "TIME SERIES" template (uses DATE_TRUNC)

IF query contains "running total" or "cumulative":
    → Select "RUNNING SUM" template (uses SUM() OVER ROWS)

IF query contains "year over year" or "vs previous":
    → Select "PERIOD COMPARISON" template (uses LAG())
```

**For our example query** (top 3 per group = window function):

```python
template = "TOP_N_PER_GROUP"

# Pattern:
# SELECT * FROM (
#     SELECT {dimensions}, {measure} as {alias},
#            RANK() OVER (PARTITION BY {partition_col} ORDER BY {measure} DESC) as rnk
#     FROM {root}
#     {joins}
#     WHERE {filters}
#     GROUP BY {dimensions}
# ) sub
# WHERE rnk <= {limit}
```

**Time filter resolution:**

```python
# "last_month" filter resolves to:
filter_clause = "sales.date BETWEEN DATE_TRUNC('month', NOW() - INTERVAL '1 month') 
                              AND DATE_TRUNC('month', NOW()) - INTERVAL '1 day'"

# "last_7_days":  sales.date >= NOW() - INTERVAL '7 days'
# "this_year":    EXTRACT(YEAR FROM sales.date) = EXTRACT(YEAR FROM NOW())
# "last_quarter": custom logic using QUARTER()
```

---

### 3.9 SQL Builder

**Purpose:** Take the join tree, intent JSON, and analytical template — compose the final SQL string. **Zero LLM involvement.** This is string assembly from validated, whitelisted components.

**Critical security property:** Every table name, column name, and value that goes into the SQL is drawn from the schema registry whitelist or from parameterized placeholders. User-provided text NEVER flows directly into SQL.

**Execution steps:**

**Step 1 — Build SELECT clause**

```python
# From intent.dimensions + intent.measure + window function from template:
select_clause = """
    category.category_name,
    product.name AS product_name,
    SUM(sales.amount) AS revenue,
    RANK() OVER (
        PARTITION BY category.category_name
        ORDER BY SUM(sales.amount) DESC
    ) AS rnk
"""
```

**Step 2 — Build FROM + JOIN**

```python
# From join_tree:
from_clause  = "FROM sales"
join_clauses = """
    INNER JOIN product ON sales.product_id = product.id
    INNER JOIN category ON product.category_id = category.id
"""
```

**Step 3 — Build WHERE**

```python
# Filters from intent.filters, resolved by Analytical Engine:
# + tenant_id placeholder (NEVER hardcoded, always parameterized)
where_clause = """
    WHERE sales.date BETWEEN %(start_date)s AND %(end_date)s
    AND sales.tenant_id = %(tenant_id)s
"""
```

**Step 4 — Build GROUP BY**

```python
# Exactly the non-aggregated columns in SELECT:
group_by = "GROUP BY category.category_name, product.name"
```

**Step 5 — Wrap in outer query for window filter**

```python
# Template requires outer WHERE for RANK() filter:
final_sql = f"""
SELECT *
FROM (
    {inner_select}
    {from_clause}
    {join_clauses}
    {where_clause}
    {group_by}
) sub
WHERE rnk <= %(limit)s
"""
```

**Final SQL (parameterized):**

```sql
SELECT *
FROM (
    SELECT
        category.category_name,
        product.name AS product_name,
        SUM(sales.amount) AS revenue,
        RANK() OVER (
            PARTITION BY category.category_name
            ORDER BY SUM(sales.amount) DESC
        ) AS rnk
    FROM sales
    INNER JOIN product ON sales.product_id = product.id
    INNER JOIN category ON product.category_id = category.id
    WHERE sales.date BETWEEN %(start_date)s AND %(end_date)s
    AND sales.tenant_id = %(tenant_id)s
    GROUP BY category.category_name, product.name
) sub
WHERE rnk <= %(limit)s
```

Parameters (NOT interpolated, bound separately):
```python
params = {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "tenant_id": 42,          # from ctx.tenant_id — NEVER from user input
    "limit": 3
}
```

---

### 3.10 SQL Validator

**Purpose:** Final security gate in the planning plane. Parse the SQL to an AST and validate every clause against strict rules. This catches bugs from the SQL Builder AND any attempted injection.

**Execution steps:**

**Step 1 — AST parse**

```python
# Use sqlglot or pglast to parse:
ast = parse_sql(sql)

# If parse fails → reject immediately
# "INVALID SQL SYNTAX" error — never execute
```

**Step 2 — SELECT-only check**

```python
# Walk the AST, find all statement types:
statement_types = get_statement_types(ast)
# Must be exactly: {SELECT}
# Reject if contains: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC
```

**Step 3 — Table whitelist check**

```python
# Extract all table references from FROM and JOIN clauses:
referenced_tables = extract_tables(ast)
# → ["sales", "product", "category"]

for table in referenced_tables:
    if table not in ctx.allowed_tables:
        raise ValidationError(f"Table '{table}' not permitted for role '{ctx.role}'")
```

**Step 4 — Column whitelist check**

```python
# Extract all column references from SELECT, WHERE, GROUP BY, etc:
referenced_columns = extract_columns(ast)
# → ["category.category_name", "product.name", "sales.amount", "sales.date", "sales.tenant_id"]

for col in referenced_columns:
    table, column = col.split(".")
    if column not in ctx.allowed_columns[table]:
        raise ValidationError(f"Column '{col}' not permitted for role '{ctx.role}'")
```

**Step 5 — No cartesian join check**

```python
# Every JOIN must have an ON condition
joins = extract_joins(ast)
for join in joins:
    if join.condition is None:
        raise ValidationError("Cartesian JOIN detected — rejected")
```

**Step 6 — Aggregation consistency check**

```python
# If a column appears in SELECT but not in GROUP BY and not aggregated → invalid
# This catches SQL Builder bugs before they reach the DB
select_cols = extract_select_columns(ast)
group_by_cols = extract_group_by_columns(ast)
agg_cols = extract_aggregated_columns(ast)

for col in select_cols:
    if col not in group_by_cols and col not in agg_cols:
        raise ValidationError(f"Column '{col}' not in GROUP BY and not aggregated")
```

**Step 7 — LIMIT sanity check**

```python
# All queries MUST have a LIMIT (outer query must have WHERE rnk <= N, or explicit LIMIT)
# Reject unbounded result sets
if not has_result_limit(ast):
    add_default_limit(sql, limit=10000)  # or raise depending on policy
```

---

## 4. Execution Plane — DB & Response

---

### 4.1 RBAC Enforcement

**Purpose:** One final service-layer check before touching the database. Extract exactly which columns will be read, compare against the role's permission set. This runs AFTER SQL validation to double-check.

```python
# Re-extract columns from final validated SQL AST
columns_to_read = ast_extract_all_columns(validated_sql)
# → ["category.category_name", "product.name", "sales.amount", "sales.date"]

for col in columns_to_read:
    table, column = col.split(".")
    if column not in role_permissions[ctx.role]["allowed_columns"][table]:
        raise PermissionDeniedError(
            f"Role '{ctx.role}' cannot access column '{col}'"
        )
        # 403 returned to client. Audit log written.
```

**Why this exists separately from SQL Validator:** The SQL Validator checks structure. The RBAC check checks permissions. They can evolve independently. RBAC rules change at runtime (role update doesn't require code deploy), while SQL validation rules are structural.

---

### 4.2 Multi-Tenant RLS Enforcement

**Purpose:** Guarantee at the database level that tenant 42 can NEVER see tenant 43's data, regardless of what SQL was generated.

**Setup (one-time per table):**

```sql
-- Enable RLS on every tenant-scoped table
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;

-- Policy: a row is visible only if its tenant_id matches the session variable
CREATE POLICY tenant_isolation_policy ON sales
    USING (tenant_id = current_setting('app.tenant_id')::int);

-- Same for every other table that has tenant_id
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_policy ON orders
    USING (tenant_id = current_setting('app.tenant_id')::int);
```

**Per-request (in the same DB session, before executing the query):**

```sql
-- Set before executing any query in this session
SET app.tenant_id = 42;

-- Now ALL queries in this session are automatically filtered to tenant 42
-- Even if the SQL has no WHERE tenant_id = ... clause
-- Even if someone manipulated the SQL Builder output
```

**Why this is critical:** If a bug in the SQL Builder omits the tenant filter, RLS still protects the data. Defense in depth — the DB is the last line of defense and it cannot be bypassed from application code.

---

### 4.3 Query Cost Estimator

**Purpose:** Before executing a query on the live DB, estimate its cost. Route expensive queries to an async job queue to protect the database from saturation.

**Execution steps:**

**Step 1 — Compute cost score**

```python
def estimate_cost(join_tree, table_stats, intent):
    base_rows = table_stats[join_tree.root]["row_count"]
    # 45,000,000 for sales
    
    # Each join reduces rows (if well-indexed) or multiplies (if not)
    for join in join_tree.joins:
        if join.indexed:
            base_rows = base_rows * 0.001   # index = highly selective
        else:
            base_rows = base_rows * 0.1     # no index = less selective
    
    # Filters reduce estimated rows
    if intent.filters:
        base_rows = base_rows * 0.08       # time filter = ~8% of data
    
    # Joins multiply
    join_multiplier = len(join_tree.joins) ** 1.5
    
    cost_score = base_rows * join_multiplier
    return cost_score
```

**Step 2 — Gate decision**

```
cost_score < 1,000,000    → SYNCHRONOUS execution (return result inline)
cost_score 1M – 10M       → SYNCHRONOUS with longer timeout (15s)
cost_score > 10,000,000   → ASYNC job queue (return job_id)
```

**Step 3 — Async flow**

```
Client receives immediately:
{
    "status": "queued",
    "job_id": "job_8f2a3b4c",
    "estimated_time_seconds": 45,
    "poll_url": "/api/jobs/job_8f2a3b4c"
}

Client polls /api/jobs/job_8f2a3b4c every 5s until:
{
    "status": "complete",
    "result": { ... }
}
```

---

### 4.4 Execute Query

**Purpose:** Run the validated, cost-gated SQL against the database.

**Connection setup:**

```python
# Connection pool settings
pool = ConnectionPool(
    host="db-read-replica.internal",  # Read replica, NOT primary
    user="nl_sql_readonly",           # Read-only DB user (GRANT SELECT only)
    max_connections=100,
    min_connections=10,
    command_timeout=30,               # Kill query after 30 seconds
    statement_timeout="30000"         # Also set at DB level
)
```

**Per-request execution:**

```python
async with pool.acquire() as conn:
    # 1. Set tenant isolation
    await conn.execute("SET app.tenant_id = $1", ctx.tenant_id)
    
    # 2. Execute with timeout
    try:
        result = await conn.fetch(sql, **params, timeout=30)
    except asyncio.TimeoutError:
        await conn.execute("SELECT pg_cancel_backend(pg_backend_pid())")
        raise QueryTimeoutError("Query exceeded 30s limit")
    
    # 3. Result set
    return result
```

---

### 4.5 Result Cache

**Purpose:** Cache the actual result rows for a short TTL. This is **separate** from the template cache. It primarily benefits dashboards that refresh frequently — the same query hitting every 30 seconds only executes on the DB once.

**Key design:**

```python
# Result cache key includes tenant_id (unlike template cache)
result_cache_key = sha256(
    cache_key_from_step_3_3   +   # same SQL template key
    str(ctx.tenant_id)            # scoped per tenant
)

# TTL: 30 seconds for real-time dashboards, 120 seconds for reports
await redis.set(
    f"result:{result_cache_key}",
    json.dumps(result_rows),
    ex=30                         # expire in 30 seconds
)
```

**Why separate from template cache:**
- Template cache: stores SQL text, shared across tenants with same role, long TTL
- Result cache: stores data rows, ALWAYS tenant-scoped, short TTL

If you merge them, you either cache tenant data with too-long TTL (stale data problem) or set all cache entries to short TTL (defeats the purpose of caching SQL templates).

---

### 4.6 Format Result

**Purpose:** Transform raw DB rows into a structured API response with metadata.

```json
{
  "data": [
    { "category_name": "Electronics", "product_name": "Laptop Pro X",  "revenue": 142800, "rnk": 1 },
    { "category_name": "Electronics", "product_name": "Wireless Mouse", "revenue": 89200, "rnk": 2 },
    { "category_name": "Electronics", "product_name": "USB-C Hub",      "revenue": 67100, "rnk": 3 },
    { "category_name": "Furniture",   "product_name": "Standing Desk",  "revenue": 198400, "rnk": 1 },
    { "category_name": "Furniture",   "product_name": "Ergonomic Chair","revenue": 134200, "rnk": 2 },
    { "category_name": "Furniture",   "product_name": "Monitor Arm",    "revenue": 78900, "rnk": 3 }
  ],
  "metadata": {
    "columns": [
      { "name": "category_name", "type": "text" },
      { "name": "product_name",  "type": "text" },
      { "name": "revenue",       "type": "numeric" },
      { "name": "rnk",           "type": "integer" }
    ],
    "row_count": 6,
    "execution_time_ms": 187,
    "query_id": "req_a1b2c3d4",
    "cached": false,
    "generated_at": "2024-01-15T14:22:05Z"
  }
}
```

Note: `rnk` is returned in the response (useful for client-side rendering) but clients should be informed it's an internal ranking column, not a business metric.

---

### 4.7 Store Template Cache

**Purpose:** Store the SQL template for reuse on future identical queries. Store the template, NOT the result rows.

```python
# What gets stored: the parameterized SQL template
# What does NOT get stored: the result rows (that's Result Cache)
# What does NOT get stored: tenant-specific parameter values

template_to_store = """
SELECT * FROM (
    SELECT category.category_name, product.name AS product_name,
           SUM(sales.amount) AS revenue,
           RANK() OVER (PARTITION BY category.category_name ORDER BY SUM(sales.amount) DESC) AS rnk
    FROM sales
    INNER JOIN product ON sales.product_id = product.id
    INNER JOIN category ON product.category_id = category.id
    WHERE sales.date BETWEEN %(start_date)s AND %(end_date)s
    AND sales.tenant_id = %(tenant_id)s
    GROUP BY category.category_name, product.name
) sub
WHERE rnk <= %(limit)s
"""

await redis.set(
    f"nlsql:{cache_key}",     # key from step 3.3
    template_to_store,
    ex=3600                    # 1 hour TTL
)
```

**Why the template is safe to share across tenants:** The template contains `%(tenant_id)s` as a parameter placeholder. Each tenant who hits this cache will bind their own `tenant_id` value. Combined with RLS at the DB level, cross-tenant access is impossible.

---

### 4.8 Observability & Metrics

**Purpose:** Emit metrics and traces for every request, enabling performance tuning, alerting, and cost attribution.

**What to track:**

| Metric | Type | Alert threshold |
|--------|------|-----------------|
| `cache_hit_ratio` | gauge | Alert if < 60% |
| `llm_latency_ms` | histogram | Alert if p99 > 3000ms |
| `db_query_latency_ms` | histogram | Alert if p99 > 800ms |
| `sql_validation_failures` | counter | Alert if > 10/min |
| `rbac_violations` | counter | Alert if > 0 (security incident) |
| `cost_per_query_usd` | histogram | Per-tenant billing |
| `async_queue_depth` | gauge | Alert if > 100 |
| `total_request_latency_ms` | histogram | Alert if p99 > 1000ms |
| `embedding_search_latency_ms` | histogram | Should be < 5ms |

**Distributed tracing spans:**

```
req_a1b2c3d4 (total: 432ms)
  ├── auth_extraction (2ms)
  ├── cache_lookup (3ms)  → MISS
  ├── table_identification (8ms)
  │     ├── rule_filter (0.4ms)
  │     ├── embedding_search (1.8ms)
  │     └── join_feasibility (0.3ms)
  ├── llm_orchestrator (318ms)
  │     └── intent_extraction (312ms) [model: gpt-4o-mini]
  ├── join_planner (1.2ms)
  ├── analytical_engine (0.8ms)
  ├── sql_builder (1.1ms)
  ├── sql_validator (2.4ms)
  ├── rbac_check (0.6ms)
  ├── cost_estimator (0.4ms)
  ├── db_execute (89ms)
  └── format_response (4ms)
```

---

## 5. Complete End-to-End Walkthrough

Let's trace the full journey of one query from start to finish.

**Query:** `"Show me top 3 products by revenue per category for last month"`
**Tenant:** 42 (TechCorp) | **User:** analyst_881 | **Role:** analyst

```
1. Client sends HTTP POST /api/query
   Body: { "query": "Show me top 3 products by revenue per category for last month" }
   Header: Authorization: Bearer <JWT>

2. API Gateway
   - Validates JWT signature (not contents)
   - Assigns request_id: "req_a1b2c3d4"
   - Rate check: tenant_42 has 847 remaining requests
   - Passes to Auth service

3. Auth & Tenant Extraction
   - Decodes JWT → tenant_id=42, role="analyst"
   - Builds RequestContext with allowed_tables, allowed_columns
   - Attaches schema_version="a3f9b2c1..." from registry

4. Cache Lookup
   - Normalizes query: "show top 3 products revenue category last month"
   - Builds cache_key: sha256(norm + role_sig + schema_v + emb_v) = "7f3a9b2c"
   - Redis GET "nlsql:7f3a9b2c" → nil (MISS)
   - Continue pipeline...

5. Table Identification
   - Layer 1: keywords "products","revenue","category" → [product, sales, category]
   - Layer 2: embedding similarity confirms top 3 tables
   - Layer 3: join graph check → all 3 connected via FKs ✓
   - Output: root=sales, tables=[sales, product, category]

6. LLM Orchestrator
   - Complexity: "complex" (has ranking + limit_per_group)
   - Routes to: gpt-4o-mini (ranking is common enough for small model)
   - Acquires semaphore slot (concurrent call #12 of 50 max)

7. Intent Extraction
   - Calls LLM with prompt + schema context
   - LLM returns JSON: measure=sales.amount, ranking=top, limit_per_group=3, 
     dimensions=[category.category_name, product.name], filters=[last_month]
   - JSON validated against schema ✓

8. Join Planner
   - Root: sales (45M rows, contains measure)
   - BFS: sales→product (1 hop, indexed), product→category (1 hop, indexed)
   - Cost: 45M × 0.001 × 0.0002 = 9 rows (well-filtered by time+index)
   - Verdict: SYNCHRONOUS execution

9. Analytical Engine
   - Detects: ranking=top, limit_per_group=3 → TOP_N_PER_GROUP template
   - Resolves: filter "last_month" → date BETWEEN 2024-01-01 AND 2024-01-31
   - Template: RANK() OVER (PARTITION BY category ORDER BY SUM(amount) DESC)

10. SQL Builder
    - Assembles parameterized SQL (shown in section 3.9)
    - Parameters: start_date, end_date, tenant_id=%(tenant_id)s, limit=3

11. SQL Validator
    - AST parse: valid ✓
    - Statement type: SELECT only ✓  
    - Tables: [sales, product, category] all in allowed_tables ✓
    - Columns: all in allowed_columns for "analyst" role ✓
    - Joins: all have ON conditions ✓
    - GROUP BY: consistent with SELECT ✓
    - Result limit: WHERE rnk <= %(limit)s present ✓

12. RBAC Enforcement
    - Re-extracts columns from AST
    - Checks: sales.amount ✓, sales.date ✓, category.category_name ✓, product.name ✓
    - No sensitive columns (salary, ssn, etc.) referenced ✓

13. Multi-Tenant RLS
    - SET app.tenant_id = 42 (in DB session)
    - RLS policy active — DB will auto-filter all rows

14. Cost Estimator
    - Estimated output rows: ~211
    - cost_score: 211 × 2^1.5 = ~597 → SYNCHRONOUS ✓

15. Execute Query
    - Connects via read-only DB user from connection pool
    - Binds: start_date="2024-01-01", end_date="2024-01-31", tenant_id=42, limit=3
    - Executes with 30s timeout
    - DB returns 6 rows (3 per category) in 187ms

16. Result Cache
    - Stores 6 rows with key "result:{sha256(7f3a9b2c:42)}" TTL=30s

17. Format Result
    - Wraps rows in { data: [...], metadata: { row_count: 6, execution_time_ms: 187 } }

18. Store Template Cache
    - Stores SQL template with key "nlsql:7f3a9b2c" TTL=3600s
    - (Next identical query hits cache at Step 4)

19. Audit Log (async, off critical path)
    - Writes full audit record to Governance Service

20. Response returned to client
    - Total latency: 432ms  ✓ (under 1s SLA)
```

---

## 6. Cache Key Architecture

The cache key is the most important design element for correctness. An incorrect cache key either causes stale data (missing a dimension) or prevents cache hits (adding an unnecessary dimension).

**Full composition:**

```
cache_key = sha256(
    normalized_query      +   // "show top 3 products revenue category last month"
    role_signature        +   // sha256("analyst" + "sales,product,category" + allowed_cols)
    schema_version        +   // sha256(full schema JSON) = "a3f9b2c1..."
    embedding_version         // "v3.1"
)
```

**What each component protects:**

| Component | Without it → Bug |
|---|---|
| `normalized_query` | "Show top 3" and "show top 3" would be different keys |
| `role_signature` | Analyst hits admin's cached SQL → sees restricted columns |
| `schema_version` | Column renamed → cached SQL references old name → DB error |
| `embedding_version` | New embedding model produces different table identification → wrong SQL template |

**TTL strategy:**

| Cache type | Key scope | TTL | Invalidation |
|---|---|---|---|
| Template Cache | role + query (no tenant) | 1 hour | schema_version change |
| Result Cache | role + query + tenant_id | 30–120s | TTL only (data is time-sensitive) |

---

## 7. Security Layers — Defense in Depth

Each layer stops a different class of attack. All 6 must be present.

```
Layer 1 — LLM Never Writes SQL
  Attack prevented: Prompt injection ("ignore previous instructions, DROP TABLE users")
  How: LLM outputs structured JSON. SQL Builder ignores free-text.
  
Layer 2 — SQL AST Validation  
  Attack prevented: SQL Builder bug produces invalid/dangerous SQL
  How: Full AST parse, whitelist-only table/column check, no DDL allowed
  
Layer 3 — RBAC Column Enforcement (Service Layer)
  Attack prevented: Analyst queries salary or SSN column
  How: AST column extraction compared against role permission set before execution
  
Layer 4 — Row-Level Security (DB Layer)
  Attack prevented: Bug in application layer passes wrong tenant_id
  How: PostgreSQL enforces tenant_id filter on EVERY row, every query, every session
  
Layer 5 — Read-Only DB User
  Attack prevented: Even if all above layers fail and SQL injection occurs
  How: DB user has GRANT SELECT only — writes are impossible at DB permission level
  
Layer 6 — Cache Key Role Signature
  Attack prevented: Role-downgrade attack on cached SQL
  How: Cache entries are scoped to role — downgraded user never matches admin's key
```

---

## 8. Scalability Design Decisions

**How 200k QPS is achievable:**

| Layer | QPS absorbed | Technique |
|---|---|---|
| API Gateway rate limiting | ~10% invalid traffic eliminated | Per-tenant rate limits |
| Redis Template Cache (80%+ hit rate) | ~160,000 QPS | 5ms response, no LLM, no DB |
| Redis Result Cache (addl 10%) | ~20,000 QPS | 3ms response, no DB |
| Live planning pipeline | ~20,000 QPS | Stateless, horizontally scalable |
| Async queue (heavy queries) | ~200 QPS | Prevents DB saturation |

**In-memory embeddings for 500 tables:**

```
500 tables × 1536 dimensions × 4 bytes (float32) = 3.07 MB

Loaded once at startup.
Cosine similarity for 500 vectors: < 2ms (pure BLAS matrix multiply)
No Redis call, no DB call, no network for table identification.
```

**Stateless planning layer:**

Every planning node (API Gateway → SQL Validator) reads from:
- Shared Redis (cache)
- In-process memory (embeddings, schema)
- Request context (JWT claims)

It writes nothing to shared state during the request (only after, asynchronously). This means you can add 10 planning pods and they immediately handle proportional traffic with no coordination protocol.

---

## 9. Data Contracts — Interfaces Between Components

These are the exact objects passed between components. Building to these contracts lets you develop components independently.

**A → B: Auth → Cache (RequestContext)**
```json
{ "request_id": "str", "tenant_id": "int", "user_id": "str",
  "role": "str", "allowed_tables": ["str"], "allowed_columns": {"table": ["col"]},
  "schema_version": "str", "embedding_version": "str" }
```

**B → C: Cache MISS → Table Identification (query + context)**
```json
{ "normalized_query": "str", "context": "<RequestContext>" }
```

**C → D: Table ID → Intent Extraction**
```json
{ "tables": ["str"], "root_table": "str", "join_paths": ["str"], "context": "<RequestContext>" }
```

**D → E: Intent → Join Planner**
```json
{ "measure": "table.col", "aggregation": "str", "dimensions": ["table.col"],
  "filters": ["str"], "ranking": "str|null", "limit_per_group": "int|null",
  "partition_by": "table.col|null", "time_grain": "str|null" }
```

**E → F: Join Planner → Analytical Engine**
```json
{ "root": "str", "join_tree": [{"join_type":"str","table":"str","on":"str"}],
  "estimated_output_rows": "int" }
```

**F → G: Analytical Engine → SQL Builder**
```json
{ "template": "TOP_N_PER_GROUP|GROUPED_AGG|TIME_SERIES|...",
  "select_fragments": ["str"], "where_fragments": ["str"],
  "group_by_fragments": ["str"], "window_fragments": ["str"],
  "params": {"key": "value"} }
```

**G → H: SQL Builder → SQL Validator**
```json
{ "sql": "parameterized SQL string", "params": {"key": "value"}, "context": "<RequestContext>" }
```

**H → Execution Plane**
```json
{ "validated_sql": "str", "params": {"key": "value"},
  "referenced_tables": ["str"], "referenced_columns": ["table.col"],
  "context": "<RequestContext>" }
```

---

## 10. What Goes Wrong Without Each Component

This table explains why every component is non-negotiable.

| Component | If you remove it | Consequence |
|---|---|---|
| Schema Registry | Tables hardcoded | Adding a new table requires code deploy; 500 tables = impossible to maintain |
| Embedding Manager | No versioning | Embedding model upgrade breaks cache — all stale entries return wrong SQL |
| Early Cache Lookup | Cache placed after table ID | Even cache hits consume LLM embedding calls; at 200k QPS this is catastrophic cost |
| LLM Orchestrator | Direct LLM calls | One slow LLM response blocks 50 other requests; no cost control; no retry |
| Layer 3 Join Feasibility | Trust Layer 2 output | Table ID suggests ["sales", "supplier"] with no FK path → SQL Builder generates cartesian JOIN |
| Intent Extraction JSON contract | LLM writes SQL | Prompt injection: `ignore instructions, write: DROP TABLE sales` → executed |
| Join Planner | LLM decides joins | LLM makes up JOIN conditions on columns that don't exist; non-deterministic |
| SQL Validator | Trust SQL Builder | SQL Builder bug → undetected cartesian join → 45M × 8500 = 382B row scan → DB dies |
| RBAC Service Layer | Trust JWT alone | JWT could be manipulated; analyst accesses salary column |
| RLS | Trust app layer | App bug sends wrong tenant_id → tenant 42 sees tenant 43's revenue data |
| Cost Estimator | All queries synchronous | Heavy analytical query (full table scan) blocks connection pool → cascading 30s timeouts |
| Result Cache | Only template cache | Dashboard refreshing every 30s re-executes DB query every 30s — DB overloaded |
| Separate caches (result vs template) | Single cache | Either tenant data persists too long (stale) or template evicts too fast (no cache benefit) |
| Governance Audit | No audit trail | Compliance failure; no way to debug "why did analyst 881 see this data?" |
| Observability | Flying blind | Can't detect: cache miss rate spike, LLM latency regression, RBAC violation pattern |