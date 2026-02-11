"""
LLM Prompts for Sales Analytics Chatbot

This file contains:
1. Comprehensive system prompt for SQL generation
2. 20 example question-SQL pairs for few-shot learning
3. Answer formatting prompts

IMPORTANT: This file is separate from the semantic JSON to allow:
- Easy updates to prompts without changing data definitions
- Version control for prompt engineering
- Different prompts for different LLM providers
"""

from typing import Optional, Dict, List, Tuple, Any


# =============================================================================
# SYSTEM PROMPT - Comprehensive SQL Generation Guide
# =============================================================================

SYSTEM_PROMPT = """You are an expert SQL analyst for a Sales Analytics system. Your role is to convert natural language questions into accurate PostgreSQL queries.

## DATABASE SCHEMA

**Table:** public.sales_analytics
**Description:** Sales transactions for electrical products (cables, wires, switches, fans, lights)

### MEASURES (Always use aggregation functions)
| Column | Description | SQL Usage |
|--------|-------------|-----------|
| saleamt_ason | Sales amount in INR | SUM(saleamt_ason) |
| saleqty_ason | Quantity sold (units) | SUM(saleqty_ason) |
| profitloss_ason | Profit/Loss in INR | SUM(profitloss_ason) |
| metalweightsold_ason | Metal weight in KG | SUM(metalweightsold_ason) |
| item_receivable | Outstanding dues in INR | SUM(item_receivable) |

### DIMENSIONS (Grouping & Filtering)
| Column | Description | Sample Values |
|--------|-------------|---------------|
| period | Month Year format | 'January 2026', 'December 2025' |
| asondate | Transaction date | DATE format |
| groupheadname | **Distributor/Dealer** (PRIMARY ENTITY) | 'ABC TRADERS', 'XYZ DISTRIBUTORS' |
| customername | Customer name | 'CUSTOMER A', 'CUSTOMER B' |
| customer_state | Indian state | 'Maharashtra', 'Gujarat', 'Karnataka' |
| customer_category | Rating (A-G) | 'A', 'B', 'C', 'D', 'E', 'F', 'G' |
| customer_type | Type | 'Regular', 'New', 'Review' |
| industry | Industry segment | 'DEALER   LOCAL', 'CONTRACTOR   SMALL AND MEDIUM' |
| itemname | Product name | Specific product names |
| itemgroup | Product category | 'CABLES : BUILDING WIRES', 'CABLES : LT' |
| itemsubgroup | Product subcategory | Subcategory names |
| brand | Brand name | 'POLYCAB', 'PRIMA POLYCAB', 'ANCHOR' |
| material | Material type | 'Copper', 'Aluminium' |
| branchname | Branch/Office | Branch names |
| regionalheadname | Regional manager | Manager names |
| handledbyname | Salesperson | Salesperson names |
| companyname | Company/Business unit | Company names |

## CRITICAL PRODUCT CATEGORY MAPPINGS
⚠️ Users say business terms, but database uses specific values. ALWAYS use these exact SQL expressions:

| User Says | SQL Expression |
|-----------|----------------|
| "Building Wires", "BW", "house wire" | itemgroup LIKE 'CABLES : BUILDING WIRES%' |
| "LT Cables", "LT", "low tension" | itemgroup = 'CABLES : LT' |
| "Flexibles", "flex", "LDC" | itemgroup = 'CABLES : LDC (FLEX ETC)' |
| "HT Cables", "HT & EHV", "high tension" | itemgroup = 'CABLES : HT & EHV' |
| "Switches" | itemgroup = 'SWITCHES (WD)' |
| "Fans", "ceiling fans" | itemgroup = 'FANS' |
| "Lights", "lighting" | itemgroup = 'LIGHT FIXTURE' |
| "All Cables" | itemgroup LIKE 'CABLES%' |

## DERIVED METRICS (Use exact expressions)
| Metric | SQL Expression |
|--------|----------------|
| Margin % | ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) |
| Avg Sales Value | ROUND(SUM(saleamt_ason) / NULLIF(COUNT(*), 0), 2) |
| Sales per Customer | ROUND(SUM(saleamt_ason) / NULLIF(COUNT(DISTINCT customername), 0), 2) |
| Customer Count | COUNT(DISTINCT customername) |
| Distributor Count | COUNT(DISTINCT groupheadname) |
| Receivables % | ROUND(SUM(item_receivable) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) |

## INDIAN STATE MAPPINGS
| Abbreviation | Full Name |
|--------------|-----------|
| MH | Maharashtra |
| GJ | Gujarat |
| KA | Karnataka |
| TN | Tamil Nadu |
| DL, NCR | Delhi |
| RJ | Rajasthan |
| MP | Madhya Pradesh |
| UP | Uttar Pradesh |
| WB | West Bengal |
| PB | Punjab |
| HR | Haryana |

## RULES
1. **Always generate SELECT queries only** - Never UPDATE, DELETE, INSERT, DROP, ALTER
2. **Always use aggregation for measures** - SUM(), COUNT(), AVG()
3. **Always use proper GROUP BY** when using aggregations with dimensions
4. **Handle NULL values** - Use NULLIF() to prevent division by zero
5. **Use COALESCE for display** - COALESCE(column, 'Unknown') for cleaner results
6. **Limit results** - Default LIMIT 10 for top/bottom queries unless specified
7. **Use table alias** - Refer to table as 'sales_analytics' without schema prefix
8. **Format currency** - Round to 2 decimal places for amounts
9. **Period filter format** - Period column uses 'Month YYYY' format (e.g., 'January 2026')
10. **Case-insensitive LIKE** - Use ILIKE for text searches

## OUTPUT FORMAT
Return ONLY the SQL query. No explanations, no markdown code blocks, just the raw SQL.
"""


# =============================================================================
# EXAMPLE QUESTION-SQL PAIRS (Few-shot Learning)
# =============================================================================

EXAMPLE_QA_PAIRS: List[Dict[str, str]] = [
    # ========== TOP/BOTTOM PERFORMERS ==========
    {
        "question": "Top 5 distributors by sales",
        "sql": """SELECT groupheadname AS distributor, 
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
GROUP BY groupheadname
ORDER BY total_sales DESC
LIMIT 5"""
    },
    {
        "question": "Bottom 10 customers by sales",
        "sql": """SELECT customername AS customer,
       SUM(saleamt_ason) AS total_sales,
       COUNT(*) AS transaction_count
FROM sales_analytics
GROUP BY customername
HAVING SUM(saleamt_ason) > 0
ORDER BY total_sales ASC
LIMIT 10"""
    },
    {
        "question": "Top 5 salespersons by revenue",
        "sql": """SELECT handledbyname AS salesperson,
       SUM(saleamt_ason) AS total_revenue,
       COUNT(DISTINCT customername) AS customer_count,
       COUNT(DISTINCT groupheadname) AS distributor_count
FROM sales_analytics
WHERE handledbyname IS NOT NULL
GROUP BY handledbyname
ORDER BY total_revenue DESC
LIMIT 5"""
    },
    
    # ========== GEOGRAPHIC ANALYSIS ==========
    {
        "question": "Sales by state",
        "sql": """SELECT customer_state AS state,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       COUNT(DISTINCT customername) AS customer_count
FROM sales_analytics
WHERE customer_state IS NOT NULL
GROUP BY customer_state
ORDER BY total_sales DESC"""
    },
    {
        "question": "Top customers in Gujarat",
        "sql": """SELECT customername AS customer,
       SUM(saleamt_ason) AS total_sales,
       SUM(saleqty_ason) AS total_quantity
FROM sales_analytics
WHERE customer_state = 'Gujarat'
GROUP BY customername
ORDER BY total_sales DESC
LIMIT 10"""
    },
    {
        "question": "Sales in Maharashtra and Karnataka",
        "sql": """SELECT customer_state AS state,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE customer_state IN ('Maharashtra', 'Karnataka')
GROUP BY customer_state
ORDER BY total_sales DESC"""
    },
    
    # ========== PRODUCT CATEGORY ANALYSIS ==========
    {
        "question": "Total sales of building wires",
        "sql": """SELECT SUM(saleamt_ason) AS total_sales,
       SUM(saleqty_ason) AS total_quantity,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE itemgroup LIKE 'CABLES : BUILDING WIRES%'"""
    },
    {
        "question": "Sales breakdown by product category",
        "sql": """SELECT itemgroup AS product_category,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct,
       SUM(metalweightsold_ason) AS total_weight_kg
FROM sales_analytics
GROUP BY itemgroup
ORDER BY total_sales DESC"""
    },
    {
        "question": "Compare building wires vs LT cables sales",
        "sql": """SELECT 
    CASE 
        WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN 'Building Wires'
        WHEN itemgroup = 'CABLES : LT' THEN 'LT Cables'
    END AS category,
    SUM(saleamt_ason) AS total_sales,
    SUM(profitloss_ason) AS total_profit,
    ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE itemgroup LIKE 'CABLES : BUILDING WIRES%' 
   OR itemgroup = 'CABLES : LT'
GROUP BY 
    CASE 
        WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN 'Building Wires'
        WHEN itemgroup = 'CABLES : LT' THEN 'LT Cables'
    END
ORDER BY total_sales DESC"""
    },
    {
        "question": "Top 5 products in flexibles category",
        "sql": """SELECT itemname AS product,
       SUM(saleamt_ason) AS total_sales,
       SUM(saleqty_ason) AS total_quantity
FROM sales_analytics
WHERE itemgroup = 'CABLES : LDC (FLEX ETC)'
GROUP BY itemname
ORDER BY total_sales DESC
LIMIT 5"""
    },
    
    # ========== PROFITABILITY ANALYSIS ==========
    {
        "question": "Who has negative margin?",
        "sql": """SELECT groupheadname AS distributor,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
GROUP BY groupheadname
HAVING SUM(profitloss_ason) < 0
ORDER BY total_profit ASC
LIMIT 20"""
    },
    {
        "question": "Most profitable products",
        "sql": """SELECT itemname AS product,
       itemgroup AS category,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
GROUP BY itemname, itemgroup
HAVING SUM(saleamt_ason) > 100000
ORDER BY margin_pct DESC
LIMIT 10"""
    },
    {
        "question": "Profit margin by brand",
        "sql": """SELECT brand,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE brand IS NOT NULL
GROUP BY brand
ORDER BY total_sales DESC"""
    },
    
    # ========== TIME-BASED ANALYSIS ==========
    {
        "question": "Monthly sales trend",
        "sql": """SELECT period,
       SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       COUNT(DISTINCT customername) AS active_customers
FROM sales_analytics
GROUP BY period
ORDER BY period DESC
LIMIT 12"""
    },
    {
        "question": "Sales in January 2026",
        "sql": """SELECT SUM(saleamt_ason) AS total_sales,
       SUM(saleqty_ason) AS total_quantity,
       SUM(profitloss_ason) AS total_profit,
       COUNT(DISTINCT customername) AS customer_count,
       COUNT(DISTINCT groupheadname) AS distributor_count
FROM sales_analytics
WHERE period = 'January 2026'"""
    },
    
    # ========== AGGREGATION QUERIES ==========
    {
        "question": "Total sales and profit",
        "sql": """SELECT SUM(saleamt_ason) AS total_sales,
       SUM(profitloss_ason) AS total_profit,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS overall_margin_pct,
       SUM(saleqty_ason) AS total_quantity,
       SUM(metalweightsold_ason) AS total_weight_kg
FROM sales_analytics"""
    },
    {
        "question": "How many customers do we have?",
        "sql": """SELECT COUNT(DISTINCT customername) AS total_customers,
       COUNT(DISTINCT groupheadname) AS total_distributors,
       COUNT(DISTINCT customer_state) AS states_covered,
       COUNT(*) AS total_transactions
FROM sales_analytics"""
    },
    {
        "question": "Average order value",
        "sql": """SELECT ROUND(SUM(saleamt_ason) / NULLIF(COUNT(*), 0), 2) AS avg_order_value,
       ROUND(SUM(saleamt_ason) / NULLIF(COUNT(DISTINCT customername), 0), 2) AS avg_per_customer,
       ROUND(SUM(saleamt_ason) / NULLIF(COUNT(DISTINCT groupheadname), 0), 2) AS avg_per_distributor
FROM sales_analytics"""
    },
    
    # ========== MATERIAL ANALYSIS ==========
    {
        "question": "Copper vs Aluminium sales",
        "sql": """SELECT material,
       SUM(saleamt_ason) AS total_sales,
       SUM(metalweightsold_ason) AS total_weight_kg,
       ROUND(SUM(saleamt_ason) / NULLIF(SUM(metalweightsold_ason), 0), 2) AS rate_per_kg,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE material IN ('Copper', 'Aluminium')
GROUP BY material
ORDER BY total_sales DESC"""
    },
    
    # ========== RECEIVABLES ANALYSIS ==========
    {
        "question": "Distributors with highest outstanding",
        "sql": """SELECT groupheadname AS distributor,
       SUM(item_receivable) AS total_receivables,
       SUM(saleamt_ason) AS total_sales,
       ROUND(SUM(item_receivable) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS receivable_pct
FROM sales_analytics
GROUP BY groupheadname
HAVING SUM(item_receivable) > 0
ORDER BY total_receivables DESC
LIMIT 10"""
    },
    
    # ========== INDUSTRY/SEGMENT ANALYSIS ==========
    {
        "question": "Sales by industry segment",
        "sql": """SELECT industry AS segment,
       SUM(saleamt_ason) AS total_sales,
       COUNT(DISTINCT customername) AS customer_count,
       ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) AS margin_pct
FROM sales_analytics
WHERE industry IS NOT NULL
GROUP BY industry
ORDER BY total_sales DESC"""
    },
]


# =============================================================================
# USER PROMPT TEMPLATE
# =============================================================================

USER_PROMPT_TEMPLATE = """CURRENT FILTERS APPLIED:
{filters}

USER QUESTION:
{question}

Generate the SQL query:"""


# =============================================================================
# ANSWER FORMATTING PROMPT
# =============================================================================

ANSWER_FORMAT_PROMPT = """You are a helpful sales analytics assistant. Format the query results into a clear, conversational response.

RULES:
1. Be concise but informative
2. Format large numbers with commas (e.g., 1,234,567)
3. Use ₹ symbol for currency amounts
4. Round percentages to 2 decimal places
5. If results are empty, say "No data found for this query"
6. Highlight key insights (top performer, trends, anomalies)
7. Use bullet points for lists
8. Keep response under 300 words

ORIGINAL QUESTION:
{question}

SQL EXECUTED:
{sql}

QUERY RESULTS:
{results}

Provide a natural language response:"""


# =============================================================================
# ERROR HANDLING PROMPTS
# =============================================================================

ERROR_RESPONSES = {
    "no_results": "I couldn't find any data matching your query. This could mean:\n• The filters are too restrictive\n• No transactions exist for the specified criteria\n• Try broadening your search",
    
    "invalid_question": "I'm not sure how to answer that question. I can help you with:\n• Sales analysis (top performers, trends, comparisons)\n• Profitability analysis (margins, profits by category)\n• Geographic analysis (sales by state/region)\n• Product analysis (category-wise, brand-wise)\n\nCould you rephrase your question?",
    
    "sql_error": "I encountered an error processing your request. Let me try a simpler approach or you can rephrase your question.",
    
    "timeout": "The query is taking too long. Try being more specific:\n• Add a time filter (e.g., 'in January 2026')\n• Limit to specific state or category\n• Ask for top 5 instead of all",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_prompt() -> str:
    """Get the complete system prompt."""
    return SYSTEM_PROMPT


def get_few_shot_examples(count: int = 5) -> List[Dict[str, str]]:
    """
    Get a subset of example Q&A pairs for few-shot learning.
    
    Args:
        count: Number of examples to return (default 5)
        
    Returns:
        List of example dictionaries with 'question' and 'sql' keys
    """
    # Return diverse examples covering different query types
    return EXAMPLE_QA_PAIRS[:count]


def format_user_prompt(question: str, filters: Optional[Dict] = None) -> str:
    """
    Format the user prompt with question and filters.
    
    Args:
        question: User's natural language question
        filters: Dictionary of active filters
        
    Returns:
        Formatted user prompt string
    """
    if filters:
        filter_lines = []
        for key, value in filters.items():
            if value and value != "ALL":
                filter_lines.append(f"  - {key}: {value}")
        filter_str = "\n".join(filter_lines) if filter_lines else "None"
    else:
        filter_str = "None"
    
    return USER_PROMPT_TEMPLATE.format(
        filters=filter_str,
        question=question
    )


def format_answer_prompt(question: str, sql: str, results: Any) -> str:
    """
    Format the answer formatting prompt.
    
    Args:
        question: Original user question
        sql: SQL query that was executed
        results: Query results (list of dicts or similar)
        
    Returns:
        Formatted prompt for answer generation
    """
    # Convert results to readable format
    if isinstance(results, list):
        if len(results) == 0:
            results_str = "No results"
        elif len(results) <= 20:
            results_str = str(results)
        else:
            results_str = f"{str(results[:20])}\n... and {len(results) - 20} more rows"
    else:
        results_str = str(results)
    
    return ANSWER_FORMAT_PROMPT.format(
        question=question,
        sql=sql,
        results=results_str
    )


def get_error_response(error_type: str) -> str:
    """
    Get appropriate error response message.
    
    Args:
        error_type: Type of error ('no_results', 'invalid_question', 'sql_error', 'timeout')
        
    Returns:
        User-friendly error message
    """
    return ERROR_RESPONSES.get(error_type, ERROR_RESPONSES["sql_error"])


def build_complete_prompt(
    question: str, 
    filters: Optional[Dict] = None,
    include_examples: int = 5
) -> Tuple[str, str]:
    """
    Build complete system and user prompts for LLM.
    
    Args:
        question: User's question
        filters: Active dashboard filters
        include_examples: Number of few-shot examples to include
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Build system prompt with examples
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

