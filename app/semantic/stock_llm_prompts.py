"""
LLM Prompts for Stock Inventory Chatbot

Semantic layer for natural language to SQL over stock_gw table.
Covers: fresh stock, aging stock, slow moving, dead stock, godown/branch/company/make.
"""

from typing import Optional, Dict, List, Tuple, Any


# =============================================================================
# SYSTEM PROMPT - Stock Inventory SQL Generation
# =============================================================================

SYSTEM_PROMPT = """You are an expert SQL analyst for a Stock Inventory system. Your role is to convert natural language questions into accurate PostgreSQL queries against the **stock_gw** table (godown-wise inventory aging and stock health).

## DATABASE SCHEMA

**Table:** public.stock_gw
**Description:** Godown-wise inventory: aging buckets (0-3M, 3-6M, 6M-1Y, 1-2Y, 2-3Y, 3-4Y, above 4Y), stock condition, branch, company, make. One row per entity (branch/godown) with aggregated stock values and quantities.

### MEASURES (Always use SUM for value/qty columns)
| Column | Description | SQL Usage |
|--------|-------------|-----------|
| stgw_val0_3m | Fresh stock value (0-3 months) in INR | SUM(stgw_val0_3m) |
| stgw_qty0_3m | Fresh stock quantity (0-3 months) | SUM(stgw_qty0_3m) |
| stgw_val3_6m | Stock value 3-6 months | SUM(stgw_val3_6m) |
| stgw_qty3_6m | Stock qty 3-6 months | SUM(stgw_qty3_6m) |
| stgw_val6m_1y | Stock value 6 months to 1 year | SUM(stgw_val6m_1y) |
| stgw_qty6m_1y | Stock qty 6M-1Y | SUM(stgw_qty6m_1y) |
| stgw_val1y_2y | Slow moving value (1-2 years) | SUM(stgw_val1y_2y) |
| stgw_qty1y_2y | Slow moving qty 1-2Y | SUM(stgw_qty1y_2y) |
| stgw_val2y_3y, stgw_val3y_4y, stgw_valabv_4y | Dead stock value (2-3Y, 3-4Y, above 4Y) | SUM(...) each or combined |
| stgw_qty2y_3y, stgw_qty3y_4y, stgw_qtyabv_4y | Dead stock qty | SUM(...) |
| stgw_good_val | Good condition stock value | SUM(stgw_good_val) |
| stgw_good_nos | Good condition count (NOS) | SUM(stgw_good_nos) |
| stgw_sale_value | Sales value from stock | SUM(stgw_sale_value) |
| stgw_sale90 | Sales in last 90 days | SUM(stgw_sale90) |
| stgw_profit_loss | Profit/Loss | SUM(stgw_profit_loss) |
| stgw_stock_lvl_value | Stock level value | SUM(stgw_stock_lvl_value) |
| stgw_total_profit_loss | Total P&L | SUM(stgw_total_profit_loss) |

### BUSINESS TERMS → COLUMNS
| User Says | SQL (value) | SQL (qty) |
|-----------|-------------|-----------|
| Fresh stock, 0-3 months, 0-3M | SUM(stgw_val0_3m) | SUM(stgw_qty0_3m) |
| Aging stock, 3M-1Y, 3 months to 1 year | SUM(stgw_val3_6m)+SUM(stgw_val6m_1y) | SUM(stgw_qty3_6m)+SUM(stgw_qty6m_1y) |
| Slow moving, 1-2 years, 1Y-2Y | SUM(stgw_val1y_2y) | SUM(stgw_qty1y_2y) |
| Dead stock, above 2 years, >2Y | SUM(stgw_val2y_3y)+SUM(stgw_val3y_4y)+SUM(stgw_valabv_4y) | SUM(stgw_qty2y_3y)+SUM(stgw_qty3y_4y)+SUM(stgw_qtyabv_4y) |
| Total stock value | Sum of all stgw_val* columns | Sum of all stgw_qty* columns |

### DIMENSIONS (Grouping & Filtering)
| Column | Description | Sample Values |
|--------|-------------|---------------|
| stgw_date | Stock as-on date | DATE |
| branch_name | Branch / location name | Mumbai, Bangalore, Chennai |
| company_name | Company / business unit | Company names |
| stgw_make | Make / brand | Polycab, Schneider, Legrand, ABB/Havells, Others |
| stgw_godown_code | Godown code | Godown identifiers |
| stgw_inventory_rating | Inventory rating category | A, B, C, D, E, F, G |

### DERIVED TOTALS
- Total stock value (all aging) = SUM(stgw_val0_3m) + SUM(stgw_val3_6m) + SUM(stgw_val6m_1y) + SUM(stgw_val1y_2y) + SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y)
- Total fresh stock value = SUM(stgw_val0_3m)
- Total dead stock value = SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y)

## RULES
1. **Always generate SELECT only** - Never UPDATE, DELETE, INSERT, DROP, ALTER.
2. **Always use aggregation** - SUM() for value/qty columns when reporting totals or by dimension.
3. **Table name** - Use "stock_gw" (no schema prefix in query).
4. **GROUP BY** - When grouping by branch, company, or make, include all non-aggregated columns in GROUP BY.
5. **Handle NULLs** - Use COALESCE(column, 0) for numeric columns in expressions if needed.
6. **Limit results** - Use LIMIT 10 or 20 for "top" or "list" queries unless user asks for more.
7. **ORDER BY** - Use DESC NULLS LAST for "top" / "highest"; ASC for "lowest".
8. **Do not use UNION** - Prefer a single SELECT with ORDER BY for highest/lowest.
9. **Date filter** - stgw_date is the as-on date; filter with EXTRACT(YEAR FROM stgw_date), EXTRACT(MONTH FROM stgw_date) if period/fiscal filters are provided.

## OUTPUT FORMAT
Return ONLY the SQL query. No explanations, no markdown code blocks, just the raw SQL.
"""


# =============================================================================
# EXAMPLE QUESTION-SQL PAIRS (Stock Inventory)
# =============================================================================

EXAMPLE_QA_PAIRS: List[Dict[str, str]] = [
    {
        "question": "Total fresh stock",
        "sql": """SELECT COALESCE(SUM(stgw_val0_3m), 0) AS total_fresh_stock_value,
       COALESCE(SUM(stgw_qty0_3m), 0) AS total_fresh_stock_qty
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
    {
        "question": "Give me total fresh stock",
        "sql": """SELECT COALESCE(SUM(stgw_val0_3m), 0) AS total_fresh_stock_value,
       COALESCE(SUM(stgw_qty0_3m), 0) AS total_fresh_stock_qty
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
    {
        "question": "Total stock value across all godowns",
        "sql": """SELECT COALESCE(SUM(stgw_val0_3m) + SUM(stgw_val3_6m) + SUM(stgw_val6m_1y) + SUM(stgw_val1y_2y) + SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS total_stock_value,
       COALESCE(SUM(stgw_val0_3m), 0) AS fresh_stock,
       COALESCE(SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS dead_stock
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
    {
        "question": "Stock by branch",
        "sql": """SELECT branch_name AS branch,
       COALESCE(SUM(stgw_val0_3m), 0) AS fresh_stock_value,
       COALESCE(SUM(stgw_val3_6m) + SUM(stgw_val6m_1y), 0) AS aging_stock_value,
       COALESCE(SUM(stgw_val1y_2y), 0) AS slow_moving_value,
       COALESCE(SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS dead_stock_value
FROM stock_gw
WHERE branch_name IS NOT NULL AND stgw_date IS NOT NULL
GROUP BY branch_name
ORDER BY fresh_stock_value DESC NULLS LAST
LIMIT 20"""
    },
    {
        "question": "Top 10 branches by fresh stock value",
        "sql": """SELECT branch_name AS branch,
       COALESCE(SUM(stgw_val0_3m), 0) AS fresh_stock_value
FROM stock_gw
WHERE branch_name IS NOT NULL AND stgw_date IS NOT NULL
GROUP BY branch_name
ORDER BY fresh_stock_value DESC NULLS LAST
LIMIT 10"""
    },
    {
        "question": "Total dead stock and slow moving stock",
        "sql": """SELECT COALESCE(SUM(stgw_val1y_2y), 0) AS total_slow_moving_value,
       COALESCE(SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS total_dead_stock_value
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
    {
        "question": "Stock value by make",
        "sql": """SELECT stgw_make AS make,
       COALESCE(SUM(stgw_val0_3m), 0) AS fresh_stock,
       COALESCE(SUM(stgw_val0_3m) + SUM(stgw_val3_6m) + SUM(stgw_val6m_1y) + SUM(stgw_val1y_2y) + SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS total_stock_value
FROM stock_gw
WHERE stgw_make IS NOT NULL AND stgw_date IS NOT NULL
GROUP BY stgw_make
ORDER BY total_stock_value DESC NULLS LAST"""
    },
    {
        "question": "Aging stock 3 months to 1 year total",
        "sql": """SELECT COALESCE(SUM(stgw_val3_6m) + SUM(stgw_val6m_1y), 0) AS aging_3m_to_1y_value,
       COALESCE(SUM(stgw_qty3_6m) + SUM(stgw_qty6m_1y), 0) AS aging_3m_to_1y_qty
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
    {
        "question": "Good stock value and count by branch",
        "sql": """SELECT branch_name AS branch,
       COALESCE(SUM(stgw_good_val), 0) AS good_stock_value,
       COALESCE(SUM(stgw_good_nos), 0) AS good_stock_nos
FROM stock_gw
WHERE branch_name IS NOT NULL AND stgw_date IS NOT NULL
GROUP BY branch_name
ORDER BY good_stock_value DESC NULLS LAST
LIMIT 15"""
    },
    {
        "question": "Total inventory value and sales from stock",
        "sql": """SELECT COALESCE(SUM(stgw_val0_3m) + SUM(stgw_val3_6m) + SUM(stgw_val6m_1y) + SUM(stgw_val1y_2y) + SUM(stgw_val2y_3y) + SUM(stgw_val3y_4y) + SUM(stgw_valabv_4y), 0) AS total_inventory_value,
       COALESCE(SUM(stgw_sale_value), 0) AS total_sale_value,
       COALESCE(SUM(stgw_total_profit_loss), 0) AS total_profit_loss
FROM stock_gw
WHERE stgw_date IS NOT NULL"""
    },
]


USER_PROMPT_TEMPLATE = """CURRENT FILTERS APPLIED:
{filters}

USER QUESTION:
{question}

Generate the SQL query:"""


ANSWER_FORMAT_PROMPT = """You are a helpful stock inventory assistant. Format the query results into a clear, conversational response.

RULES:
1. Be concise but informative
2. Format large numbers with commas (e.g., 1,234,567)
3. Use ₹ symbol for currency amounts (stock value, sales)
4. For stock/inventory context say "stock inventory" or "inventory data", not "sales analytics"
5. If results are empty, say "No data found for this query"
6. Highlight key insights (top branch, total fresh stock, etc.)
7. Keep response under 300 words

ORIGINAL QUESTION:
{question}

SQL EXECUTED:
{sql}

QUERY RESULTS:
{results}

Provide a natural language response:"""


def get_few_shot_examples(count: int = 5) -> List[Dict[str, str]]:
    return EXAMPLE_QA_PAIRS[:count]


def format_user_prompt(question: str, filters: Optional[Dict] = None) -> str:
    if filters:
        filter_lines = []
        for key, value in filters.items():
            if value and value != "ALL":
                filter_lines.append(f"  - {key}: {value}")
        filter_str = "\n".join(filter_lines) if filter_lines else "None"
    else:
        filter_str = "None"
    return USER_PROMPT_TEMPLATE.format(filters=filter_str, question=question)


def build_complete_prompt_stock(
    question: str,
    filters: Optional[Dict] = None,
    include_examples: int = 5,
) -> Tuple[str, str]:
    """Build system and user prompts for stock inventory SQL generation."""
    system_parts = [SYSTEM_PROMPT]
    if include_examples > 0:
        examples = get_few_shot_examples(include_examples)
        system_parts.append("\n## EXAMPLE QUERIES\n")
        for i, ex in enumerate(examples, 1):
            system_parts.append(f"**Example {i}:**")
            system_parts.append(f"Question: {ex['question']}")
            system_parts.append(f"SQL:\n{ex['sql']}\n")
    system_prompt = "\n".join(system_parts)
    user_prompt = format_user_prompt(question, filters)
    return system_prompt, user_prompt


def format_answer_prompt_stock(question: str, sql: str, results: Any) -> str:
    if isinstance(results, list):
        results_str = str(results[:20]) if len(results) > 20 else str(results)
    else:
        results_str = str(results)
    return ANSWER_FORMAT_PROMPT.format(
        question=question,
        sql=sql,
        results=results_str
    )
