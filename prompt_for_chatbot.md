# AI Chatbot for Sales Analytics Dashboard

## 1. Overview

This document describes the system design and implementation plan for an **AI-powered chatbot** integrated with the Sales Analytics Dashboard.

The chatbot will:

* Understand natural language questions
* Query the PostgreSQL database in real time
* Use dashboard filters as context
* Return accurate business answers

---

## 2. Current Problem

The existing chatbot is **hardcoded** and works using:

* Regex pattern matching
* Predefined question types
* Frontend table data only

### Limitations

| Issue                | Description                                    |
| -------------------- | ---------------------------------------------- |
| Fixed patterns       | Only understands ~15 predefined question types |
| Limited data         | Uses only 50–100 rows loaded in frontend       |
| No custom queries    | Cannot answer dynamic questions                |
| Hardcoded categories | Does not match real database schema            |
| No deep analytics    | Cannot answer complex business questions       |

---

## 3. Target Solution

A **dynamic AI chatbot** that:

* Understands any natural language question
* Generates SQL queries using an LLM
* Queries the PostgreSQL database
* Returns real-time answers

---

## 4. High-Level Architecture

```
React Dashboard
   │
   │ POST /api/chat
   ▼
FastAPI Chat API
   │
   ├── Schema Context
   ├── Metric Definitions
   ├── Dashboard Filters
   │
   ▼
LLM (SQL Generator)
   │
   ▼
SQL Guardrails
   │
   ▼
PostgreSQL (sales_analytics)
   │
   ▼
Query Result
   │
   ▼
LLM (Answer Formatter)
   │
   ▼
Frontend Chat UI
```

---

## 5. Database Schema

### Table

```
public.sales_analytics
```

### Grain

One row represents:

```
Customer + Item + Branch + Date
```

---

## 6. Semantic Data Model

The chatbot will use a semantic layer to understand the database.

### Measures (Aggregated Values)

| Business Metric | Column               | Logic                     |
| --------------- | -------------------- | ------------------------- |
| Sales           | saleamt_ason         | SUM(saleamt_ason)         |
| Quantity        | saleqty_ason         | SUM(saleqty_ason)         |
| Profit/Loss     | profitloss_ason      | SUM(profitloss_ason)      |
| Metal Weight    | metalweightsold_ason | SUM(metalweightsold_ason) |
| Receivables     | item_receivable      | SUM(item_receivable)      |

### Derived Metric

**Margin %**

```
margin_percent = SUM(profitloss_ason) / SUM(saleamt_ason) * 100
```

---

### Dimensions

#### Customer

* customercode
* customername
* groupheadname
* customer_state
* customer_category
* customer_type

#### Product

* itemcode
* itemname
* itemgroup
* itemsubgroup
* brand
* material

#### Organization

* companyname
* branchname
* regionalheadname
* handledbyname

#### Time

* asondate
* period

---

## 7. Supported Question Types

### Basic Analytics

* Total sales
* Top customers
* Sales by state
* Sales by product category

### Filtered Queries

* Sales in Gujarat for Building Wires
* Margin of LT Cables in April
* Top customers in Maharashtra

### Comparative Queries

* Compare January vs December sales
* Month-over-month growth
* State with lowest margin

### Advanced Business Intelligence

* Distributors with declining sales
* Best performing regional head
* Profit trends by category

---

## 8. API Design

### Endpoint

```
POST /api/chat
```

### Request

```json
{
  "question": "Top 5 customers in Gujarat",
  "filters": {
    "period": "April",
    "itemgroup": "Building Wires",
    "brand": "Polycab",
    "material": "Copper",
    "customer_type": "Regular"
  }
}
```

### Response

```json
{
  "answer": "Top 5 customers in Gujarat for Building Wires are...",
  "sql": "SELECT ...",
  "data": [...]
}
```

---

## 9. Backend Processing Flow

### Step-by-step flow

1. Receive question and filters
2. Load semantic schema
3. Build LLM prompt
4. Generate SQL query
5. Validate SQL
6. Execute query on PostgreSQL
7. Format answer using LLM
8. Return response to frontend

---

## 10. Enhanced LLM Prompt Structure

The semantic layer is defined in `app/semantic/sales_schema.py` and provides:

### 10.1 System Prompt (Full Context)

```
You are an expert SQL analyst for a cable manufacturing company's sales database.
Your task is to convert natural language questions into accurate PostgreSQL queries.

DATABASE: PostgreSQL
TABLE: sales_analytics
GRAIN: One row = Sales data for one customer + item + branch + date

MEASURES (Always use aggregation functions):
  - saleamt_ason: Sales amount in INR (Indian Rupees)
    SQL: SUM(saleamt_ason)
    Aliases: sale, revenue, sales amount, turnover, sales value

  - saleqty_ason: Sales quantity (units sold)
    SQL: SUM(saleqty_ason)
    Aliases: qty, units, volume, quantity sold

  - profitloss_ason: Profit or Loss amount in INR
    SQL: SUM(profitloss_ason)
    Aliases: profit, pnl, p&l, profit/loss, earnings

  - metalweightsold_ason: Metal weight sold in KG
    SQL: SUM(metalweightsold_ason)
    Aliases: weight, metal weight, tonnage

  - item_receivable: Outstanding receivables in INR
    SQL: SUM(item_receivable)
    Aliases: receivables, outstanding, dues, ar

DERIVED METRICS (Calculated fields):
  - margin_percent: Profit margin as percentage
    SQL: ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2)
    Aliases: margin, margin %, profit margin

  - avg_order_value: Average order value
    SQL: ROUND(SUM(saleamt_ason) / NULLIF(SUM(saleqty_ason), 0), 2)
    Aliases: aov, average order

DIMENSIONS (Grouping/Filtering columns):
  - customername: Customer/Client name
    Aliases: customer, client, buyer

  - groupheadname: Distributor/Dealer name (main sales entity)
    Aliases: distributor, dealer, group head, partner, entity

  - customer_state: Indian state
    Aliases: state, region, location, geography

  - itemgroup: Product category
    Aliases: product group, category, product category

  - itemname: Product name
    Aliases: product, item, material name

  - brand: Brand name
    Aliases: product brand

  - material: Material type (Copper, Aluminium)
    Aliases: material type, conductor material

  - period: Time period (e.g., "January 2026")
    Aliases: month, time period

  - regionalheadname: Regional Head name
    Aliases: regional manager, rm, zone head

  - handledbyname: Salesperson name
    Aliases: sales person, handler, sales rep

PRODUCT CATEGORY MAPPINGS (CRITICAL - Use exact SQL):
  - "Building Wires"
    SQL: itemgroup LIKE 'CABLES : BUILDING WIRES%'
    Aliases: building wire, house wire, hw, bw

  - "LT Cables"
    SQL: itemgroup = 'CABLES : LT'
    Aliases: lt cable, low tension, ltc

  - "Flexibles"
    SQL: itemgroup = 'CABLES : LDC (FLEX ETC)'
    Aliases: flexible, flex, ldc, submersible

  - "HT & EHV Cables"
    SQL: itemgroup = 'CABLES : HT & EHV'
    Aliases: ht cable, ehv, high tension, hv cable

INDIAN STATES (Use exact spelling):
  Maharashtra, Gujarat, Karnataka, Tamil Nadu, Delhi, Rajasthan,
  Madhya Pradesh, Uttar Pradesh, West Bengal, Kerala, etc.

IMPORTANT RULES:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, DROP
2. ALWAYS use SUM(), AVG(), COUNT() for measures
3. Use GROUP BY for any dimension in SELECT
4. Use NULLIF(x, 0) to prevent division by zero
5. Limit results to 100 rows maximum
6. Period values are "Month Year" format (e.g., "January 2026")
7. For product categories, use EXACT SQL from mappings above
8. For margins, multiply by 100 and use ROUND()
9. Use ILIKE for case-insensitive text matching
10. Order results by main metric DESC

OUTPUT: Return ONLY the SQL query. No explanations.
```

### 10.2 User Prompt Template

```
CURRENT FILTERS APPLIED (include in WHERE clause):
{filters}

USER QUESTION:
{question}

Generate the SQL query:
```

### 10.3 Example Question-SQL Pairs (Few-Shot Learning)

| Question | SQL |
|----------|-----|
| Top 5 customers by sales | `SELECT customername, SUM(saleamt_ason) as total_sales FROM sales_analytics GROUP BY customername ORDER BY total_sales DESC LIMIT 5` |
| Total sales in Gujarat for Building Wires | `SELECT SUM(saleamt_ason) FROM sales_analytics WHERE customer_state = 'Gujarat' AND itemgroup LIKE 'CABLES : BUILDING WIRES%'` |
| Margin by product category | `SELECT itemgroup, ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) as margin FROM sales_analytics GROUP BY itemgroup` |
| Distributors with negative margin | `SELECT groupheadname, ... HAVING SUM(profitloss_ason) < 0` |

### 10.4 Answer Formatting Prompt

After SQL execution, format results using:

```
You are a helpful data analyst assistant.
Format the SQL query results into a clear, conversational response.

RULES:
1. Use natural language, not technical jargon
2. Format numbers properly:
   - Currency: ₹X.XX Cr (crores) or ₹X.XX Lakh
   - Percentages: X.X%
   - Quantities: X,XXX units
3. Highlight key insights
4. Keep response concise but informative
5. Use bullet points for lists
6. Use bold (**text**) for emphasis

ORIGINAL QUESTION: {question}
SQL EXECUTED: {sql}
RESULTS: {results}

Format a helpful response:
```

---

## 11. SQL Guardrails

To ensure database safety:

### Allowed

* SELECT queries only

### Blocked

* INSERT
* UPDATE
* DELETE
* DROP
* ALTER

### Example validator

```python
def validate_sql(sql: str):
    sql_lower = sql.lower()

    blocked = ["delete", "update", "insert", "drop", "alter"]
    for word in blocked:
        if word in sql_lower:
            raise Exception("Unsafe SQL detected")

    if not sql_lower.strip().startswith("select"):
        raise Exception("Only SELECT allowed")

    return sql
```

---

## 12. Folder Structure

```
app/
 ├── main.py
 ├── api/
 │    └── v1/
 │         ├── reports.py          # Add chat endpoint here
 │         └── chat.py             # (Alternative) Separate chat API
 ├── services/
 │    ├── chat_service.py          # Main chat orchestration
 │    ├── llm_service.py           # LLM API integration
 │    ├── sql_validator.py         # SQL safety checks
 │    └── query_executor.py        # Safe query execution
 ├── semantic/
 │    ├── __init__.py              # Module exports
 │    └── sales_schema.py          # Complete semantic layer ✅ CREATED
 └── db/
      └── connection.py
```

### 12.1 Semantic Layer File Structure (sales_schema.py)

The semantic layer (`app/semantic/sales_schema.py`) contains:

```python
# Data Classes
class Measure          # Numeric columns with aggregation
class Dimension        # Categorical/grouping columns  
class DerivedMetric    # Calculated fields (margin, etc.)
class BusinessTermMapping  # Business term → SQL expression

# Main Schema Class
class SalesAnalyticsSchema:
    MEASURES = {...}              # 5 measures defined
    DERIVED_METRICS = {...}       # 5 derived metrics
    DIMENSIONS = {...}            # 18 dimensions
    PRODUCT_CATEGORY_MAPPINGS     # CRITICAL mappings
    TIME_PERIOD_MAPPINGS          # Month → SQL
    STATE_MAPPINGS                # State abbreviations
    COMPARISON_MAPPINGS           # "more than" → ">"
    RANKING_MAPPINGS              # "top" → DESC
    AGGREGATION_MAPPINGS          # "total" → SUM

    # Helper Methods
    get_measure_sql()             # Get SQL for measure
    get_dimension_column()        # Get column name
    get_product_category_sql()    # Get category WHERE clause
    generate_prompt_context()     # Build full LLM prompt

# Prompt Templates
LLM_SYSTEM_PROMPT              # System context
LLM_USER_PROMPT_TEMPLATE       # User question template
ANSWER_FORMATTING_PROMPT       # Response formatting

# Examples for Few-Shot Learning
EXAMPLE_QA_PAIRS               # 8 question-SQL pairs
```

---

## 13. Implementation Phases

### Phase 1: Basic Chatbot

* Question → SQL → DB → Answer
* No memory
* Basic filters

**Time:** 2–3 days

---

### Phase 2: Dashboard-Aware Chatbot

* Auto-apply dashboard filters
* Improved prompt
* Better error handling

**Time:** 2–3 days

---

### Phase 3: Production Features

* Query caching
* Logging
* Rate limiting
* Monitoring
* Feedback system

**Time:** 3–5 days

---

## 14. Recommended Tech Stack

| Layer      | Technology              |
| ---------- | ----------------------- |
| Frontend   | React (existing)        |
| Backend    | FastAPI                 |
| LLM        | OpenAI GPT-4.1 / GPT-4o |
| Database   | PostgreSQL              |
| ORM/Driver | SQLAlchemy or asyncpg   |

---

## 15. Security & Performance Considerations

### Security

* SQL validation using `sqlparse` library
* Read-only database user
* Query timeouts (10 seconds max)
* Whitelist only SELECT statements

### Performance

* Limit result size (100 rows max)
* Cache frequent queries (Redis)
* Add indexes on:

  * customer_state
  * itemgroup
  * period
  * asondate
  * groupheadname

---

## 15.1 Error Handling & Edge Cases

### Question Types to Handle

| Scenario | Response Strategy |
|----------|-------------------|
| Invalid SQL generated | Retry with simplified prompt or return fallback message |
| No results found | "No data found matching your criteria. Try different filters." |
| Query timeout | "Query took too long. Try a more specific question." |
| Non-data question ("Hello") | "I can only answer questions about sales data. Try asking about sales, customers, or products." |
| Ambiguous question | Ask for clarification or make reasonable assumption |
| Unknown entity/product | "I couldn't find [X]. Did you mean [Y]?" with fuzzy matching |

### SQL Validation (Using sqlparse)

```python
import sqlparse

def validate_sql(sql: str) -> str:
    """Validate SQL is safe to execute."""
    
    # Parse the SQL
    parsed = sqlparse.parse(sql)
    if not parsed:
        raise ValueError("Could not parse SQL")
    
    statement = parsed[0]
    
    # Only allow SELECT
    if statement.get_type() != 'SELECT':
        raise ValueError("Only SELECT queries allowed")
    
    # Check for dangerous keywords in context
    sql_lower = sql.lower()
    dangerous_patterns = [
        'insert into',
        'update ',
        'delete from',
        'drop ',
        'alter ',
        'truncate ',
        'create ',
        'grant ',
        'revoke ',
        '; --',  # SQL injection
        'union select',  # Potential injection
    ]
    
    for pattern in dangerous_patterns:
        if pattern in sql_lower:
            raise ValueError(f"Unsafe SQL pattern detected: {pattern}")
    
    return sql
```

### Fallback Responses

```python
FALLBACK_RESPONSES = {
    "parse_error": "I couldn't understand that question. Could you rephrase it?",
    "no_data": "No data found for your query. Try adjusting your filters.",
    "timeout": "The query took too long. Try asking about a specific time period or category.",
    "invalid_category": "I don't recognize that product category. Valid options: Building Wires, LT Cables, Flexibles, HT Cables.",
    "invalid_state": "I don't recognize that state. Please use full state names like 'Maharashtra' or 'Gujarat'.",
    "general_error": "Something went wrong. Please try again or rephrase your question.",
}
```

---

## 16. Success Criteria

The chatbot is considered successful if it:

* Answers any business question from the database
* Uses real-time data
* Matches dashboard filters
* Produces accurate SQL queries
* Responds within 2–5 seconds

---

## 17. Summary

### Current System

```
Question → Regex → JS Function → Frontend data
```

### New AI System

```
Question → LLM → SQL → PostgreSQL → Answer
```

This transforms the chatbot from a **pattern matcher** into a **true AI analytics assistant**.
