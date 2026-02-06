"""
Enhanced Semantic Layer for Sales Analytics Chatbot

This module provides a comprehensive semantic layer that translates
business terms to SQL expressions for the AI chatbot.

Features:
- Business term to column mappings
- Product category mappings (CRITICAL for correct SQL)
- Derived metrics with SQL expressions
- Common question patterns with SQL templates
- Dimension and measure definitions with aliases
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# Enums for Type Safety
# ============================================

class AggregationType(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT(DISTINCT {})"
    MIN = "MIN"
    MAX = "MAX"


class ColumnType(str, Enum):
    MEASURE = "measure"
    DIMENSION = "dimension"
    DATE = "date"


# ============================================
# Data Classes for Schema Definition
# ============================================

@dataclass
class Measure:
    """Definition of a measure (numeric column that can be aggregated)."""
    column: str
    description: str
    aggregation: AggregationType = AggregationType.SUM
    aliases: List[str] = field(default_factory=list)
    format_type: str = "number"  # number, currency, percent
    unit: Optional[str] = None


@dataclass
class Dimension:
    """Definition of a dimension (categorical/grouping column)."""
    column: str
    description: str
    aliases: List[str] = field(default_factory=list)
    sample_values: List[str] = field(default_factory=list)
    is_hierarchical: bool = False
    parent_dimension: Optional[str] = None


@dataclass
class DerivedMetric:
    """Definition of a calculated/derived metric."""
    name: str
    description: str
    sql_expression: str
    aliases: List[str] = field(default_factory=list)
    format_type: str = "percent"


@dataclass
class BusinessTermMapping:
    """Maps business terms to SQL expressions."""
    business_term: str
    sql_expression: str
    category: str  # product, location, time, etc.
    description: str
    aliases: List[str] = field(default_factory=list)


# ============================================
# SALES ANALYTICS SEMANTIC SCHEMA
# ============================================

class SalesAnalyticsSchema:
    """
    Complete semantic schema for the sales_analytics table.
    Provides mappings, definitions, and SQL generation helpers.
    """
    
    TABLE_NAME = "sales_analytics"
    
    # ------------------------------------------
    # MEASURES (Numeric columns for aggregation)
    # ------------------------------------------
    
    MEASURES: Dict[str, Measure] = {
        "sales": Measure(
            column="saleamt_ason",
            description="Sales amount in INR (Indian Rupees)",
            aggregation=AggregationType.SUM,
            aliases=[
                "sale", "revenue", "sales amount", "sale amount", 
                "sales value", "sale value", "turnover", "sales revenue",
                "total sales", "sales figure", "sales number"
            ],
            format_type="currency",
            unit="INR"
        ),
        "quantity": Measure(
            column="saleqty_ason",
            description="Sales quantity (units sold)",
            aggregation=AggregationType.SUM,
            aliases=[
                "qty", "units", "volume", "sales quantity", "quantity sold",
                "units sold", "pieces", "items sold", "sale quantity"
            ],
            format_type="number",
            unit="units"
        ),
        "profit": Measure(
            column="profitloss_ason",
            description="Profit or Loss amount in INR",
            aggregation=AggregationType.SUM,
            aliases=[
                "profit loss", "pnl", "p&l", "profit/loss", "profitability",
                "net profit", "earnings", "gain", "loss", "profit amount"
            ],
            format_type="currency",
            unit="INR"
        ),
        "metal_weight": Measure(
            column="metalweightsold_ason",
            description="Metal weight sold in KG",
            aggregation=AggregationType.SUM,
            aliases=[
                "weight", "metal weight", "weight sold", "metal sold",
                "kg sold", "tonnage", "metal quantity"
            ],
            format_type="number",
            unit="KG"
        ),
        "receivables": Measure(
            column="item_receivable",
            description="Outstanding receivables amount in INR",
            aggregation=AggregationType.SUM,
            aliases=[
                "receivable", "outstanding", "dues", "pending payment",
                "credit", "accounts receivable", "ar", "debtors"
            ],
            format_type="currency",
            unit="INR"
        ),
    }
    
    # ------------------------------------------
    # DERIVED METRICS (Calculated fields)
    # ------------------------------------------
    
    DERIVED_METRICS: Dict[str, DerivedMetric] = {
        "margin_percent": DerivedMetric(
            name="margin_percent",
            description="Profit margin as percentage of sales",
            sql_expression="ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2)",
            aliases=[
                "margin", "margin %", "profit margin", "margin percentage",
                "profitability %", "profit %", "profit percentage"
            ],
            format_type="percent"
        ),
        "avg_sales_per_customer": DerivedMetric(
            name="avg_sales_per_customer",
            description="Average sales per customer",
            sql_expression="ROUND(SUM(saleamt_ason) / NULLIF(COUNT(DISTINCT customername), 0), 2)",
            aliases=["average sales", "sales per customer", "customer average"],
            format_type="currency"
        ),
        "avg_order_value": DerivedMetric(
            name="avg_order_value",
            description="Average order/transaction value",
            sql_expression="ROUND(SUM(saleamt_ason) / NULLIF(SUM(saleqty_ason), 0), 2)",
            aliases=["aov", "average order", "avg transaction", "per unit value"],
            format_type="currency"
        ),
        "sales_per_kg": DerivedMetric(
            name="sales_per_kg",
            description="Sales amount per KG of metal",
            sql_expression="ROUND(SUM(saleamt_ason) / NULLIF(SUM(metalweightsold_ason), 0), 2)",
            aliases=["sales per weight", "rate per kg", "price per kg"],
            format_type="currency"
        ),
        "receivables_ratio": DerivedMetric(
            name="receivables_ratio",
            description="Receivables as percentage of sales",
            sql_expression="ROUND(SUM(item_receivable) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2)",
            aliases=["receivable ratio", "credit ratio", "outstanding ratio"],
            format_type="percent"
        ),
    }
    
    # ------------------------------------------
    # DIMENSIONS (Grouping/filtering columns)
    # ------------------------------------------
    
    DIMENSIONS: Dict[str, Dimension] = {
        # Customer Dimensions
        "customer": Dimension(
            column="customername",
            description="Customer/Client name",
            aliases=["customer name", "client", "buyer", "account"],
        ),
        "customer_code": Dimension(
            column="customercode",
            description="Customer identifier code",
            aliases=["customer id", "client code", "account code"],
        ),
        "distributor": Dimension(
            column="groupheadname",
            description="Distributor/Dealer/Group Head name (main sales entity)",
            aliases=[
                "dealer", "group head", "sales entity", "partner",
                "channel partner", "entity", "group", "distributor name"
            ],
        ),
        "state": Dimension(
            column="customer_state",
            description="Indian state where customer is located",
            aliases=[
                "customer state", "region", "location", "geography",
                "area", "territory"
            ],
            sample_values=["Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Delhi"]
        ),
        "customer_category": Dimension(
            column="customer_category",
            description="Category classification of customer",
            aliases=["category", "customer type category", "segment"],
        ),
        "customer_type": Dimension(
            column="customer_type",
            description="Type of customer (Regular, Project, etc.)",
            aliases=["type", "customer classification", "client type"],
        ),
        "industry": Dimension(
            column="industry",
            description="Industry sector of the customer",
            aliases=["sector", "business industry", "vertical", "segment"],
        ),
        
        # Product Dimensions
        "product": Dimension(
            column="itemname",
            description="Product/Item name",
            aliases=["item", "product name", "material name", "sku name"],
        ),
        "product_code": Dimension(
            column="itemcode",
            description="Product/Item code",
            aliases=["item code", "sku", "material code", "product id"],
        ),
        "product_group": Dimension(
            column="itemgroup",
            description="Product category/group (Building Wires, LT Cables, etc.)",
            aliases=[
                "item group", "category", "product category", 
                "main group", "product line"
            ],
        ),
        "product_subgroup": Dimension(
            column="itemsubgroup",
            description="Product subcategory",
            aliases=["item subgroup", "subcategory", "sub group"],
        ),
        "brand": Dimension(
            column="brand",
            description="Brand name of the product",
            aliases=["product brand", "brand name", "make"],
        ),
        "material": Dimension(
            column="material",
            description="Material type (Copper, Aluminium, etc.)",
            aliases=["material type", "raw material", "conductor material"],
            sample_values=["Copper", "Aluminium", "CU", "AL"]
        ),
        
        # Organization Dimensions
        "company": Dimension(
            column="companyname",
            description="Company name",
            aliases=["organization", "org", "business unit"],
        ),
        "branch": Dimension(
            column="branchname",
            description="Branch/Location name",
            aliases=["location", "office", "branch name"],
        ),
        "regional_head": Dimension(
            column="regionalheadname",
            description="Regional Head name (sales hierarchy)",
            aliases=[
                "regional manager", "rm", "region head", "area head",
                "zonal head", "zone head"
            ],
        ),
        "salesperson": Dimension(
            column="handledbyname",
            description="Salesperson/Handler name",
            aliases=[
                "sales person", "handler", "sales rep", "sales executive",
                "se", "sales representative", "handled by"
            ],
        ),
        
        # Time Dimensions
        "period": Dimension(
            column="period",
            description="Time period (Month Year format, e.g., 'January 2026')",
            aliases=["month", "time period", "reporting period", "month year"],
            sample_values=["January 2026", "February 2026", "December 2025"]
        ),
        "date": Dimension(
            column="asondate",
            description="Transaction/Snapshot date",
            aliases=["as on date", "transaction date", "sales date", "report date"],
        ),
    }
    
    # ------------------------------------------
    # PRODUCT CATEGORY MAPPINGS (CRITICAL!)
    # ------------------------------------------
    # These map business terms to actual database values
    
    PRODUCT_CATEGORY_MAPPINGS: Dict[str, BusinessTermMapping] = {
        "building_wires": BusinessTermMapping(
            business_term="Building Wires",
            sql_expression="itemgroup LIKE 'CABLES : BUILDING WIRES%'",
            category="product",
            description="Building/House wiring cables",
            aliases=[
                "building wire", "house wire", "house wiring", "hw",
                "bw", "building cables", "domestic wire", "housing wire"
            ]
        ),
        "lt_cables": BusinessTermMapping(
            business_term="LT Cables",
            sql_expression="itemgroup = 'CABLES : LT'",
            category="product",
            description="Low Tension power cables",
            aliases=[
                "lt cable", "low tension", "lt power cable", "ltc",
                "low tension cable", "lt"
            ]
        ),
        "flexibles": BusinessTermMapping(
            business_term="Flexibles",
            sql_expression="itemgroup = 'CABLES : LDC (FLEX ETC)'",
            category="product",
            description="Flexible cables and wires",
            aliases=[
                "flexible", "flex", "flexible cable", "ldc", "flexible wire",
                "submersible cable", "multicore flexible"
            ]
        ),
        "ht_ehv_cables": BusinessTermMapping(
            business_term="HT & EHV Cables",
            sql_expression="itemgroup = 'CABLES : HT & EHV'",
            category="product",
            description="High Tension and Extra High Voltage cables",
            aliases=[
                "ht cable", "ht cables", "ehv", "high tension", "ht",
                "ehv cable", "high voltage", "hv cable", "ht power cable",
                "ht ehv", "ht and ehv"
            ]
        ),
        "all_cables": BusinessTermMapping(
            business_term="All Cables",
            sql_expression="itemgroup LIKE 'CABLES%'",
            category="product",
            description="All cable products",
            aliases=["cables", "all products", "total", "overall"]
        ),
    }
    
    # ------------------------------------------
    # TIME PERIOD MAPPINGS
    # ------------------------------------------
    
    TIME_PERIOD_MAPPINGS: Dict[str, str] = {
        # Month names to period format
        "january": "January",
        "february": "February", 
        "march": "March",
        "april": "April",
        "may": "May",
        "june": "June",
        "july": "July",
        "august": "August",
        "september": "September",
        "october": "October",
        "november": "November",
        "december": "December",
        
        # Abbreviations
        "jan": "January",
        "feb": "February",
        "mar": "March",
        "apr": "April",
        "jun": "June",
        "jul": "July",
        "aug": "August",
        "sep": "September",
        "oct": "October",
        "nov": "November",
        "dec": "December",
        
        # Quarters
        "q1": "quarter_1",  # Apr, May, Jun (Indian FY)
        "q2": "quarter_2",  # Jul, Aug, Sep
        "q3": "quarter_3",  # Oct, Nov, Dec
        "q4": "quarter_4",  # Jan, Feb, Mar
        
        # Special periods
        "ytd": "year_to_date",
        "mtd": "month_to_date",
        "last month": "previous_month",
        "this month": "current_month",
        "last year": "previous_year",
        "this year": "current_year",
    }
    
    # ------------------------------------------
    # INDIAN STATE MAPPINGS
    # ------------------------------------------
    
    STATE_MAPPINGS: Dict[str, str] = {
        # Full names (already correct)
        "maharashtra": "Maharashtra",
        "gujarat": "Gujarat",
        "karnataka": "Karnataka",
        "tamil nadu": "Tamil Nadu",
        "tamilnadu": "Tamil Nadu",
        "andhra pradesh": "Andhra Pradesh",
        "telangana": "Telangana",
        "kerala": "Kerala",
        "rajasthan": "Rajasthan",
        "madhya pradesh": "Madhya Pradesh",
        "mp": "Madhya Pradesh",
        "uttar pradesh": "Uttar Pradesh",
        "up": "Uttar Pradesh",
        "west bengal": "West Bengal",
        "wb": "West Bengal",
        "delhi": "Delhi",
        "ncr": "Delhi",
        "punjab": "Punjab",
        "haryana": "Haryana",
        "bihar": "Bihar",
        "odisha": "Odisha",
        "orissa": "Odisha",
        "jharkhand": "Jharkhand",
        "chhattisgarh": "Chhattisgarh",
        "assam": "Assam",
        "goa": "Goa",
        
        # Abbreviations
        "mh": "Maharashtra",
        "gj": "Gujarat",
        "ka": "Karnataka",
        "tn": "Tamil Nadu",
        "ap": "Andhra Pradesh",
        "ts": "Telangana",
        "kl": "Kerala",
        "rj": "Rajasthan",
    }
    
    # ------------------------------------------
    # COMPARISON OPERATORS MAPPING
    # ------------------------------------------
    
    COMPARISON_MAPPINGS: Dict[str, str] = {
        # Greater than
        "more than": ">",
        "greater than": ">",
        "above": ">",
        "over": ">",
        "exceeding": ">",
        "higher than": ">",
        
        # Less than
        "less than": "<",
        "below": "<",
        "under": "<",
        "lower than": "<",
        
        # Equal
        "equal to": "=",
        "exactly": "=",
        "is": "=",
        
        # Greater or equal
        "at least": ">=",
        "minimum": ">=",
        
        # Less or equal
        "at most": "<=",
        "maximum": "<=",
        "up to": "<=",
        
        # Not equal
        "not": "!=",
        "except": "!=",
        "excluding": "!=",
    }
    
    # ------------------------------------------
    # RANKING TERMS MAPPING
    # ------------------------------------------
    
    RANKING_MAPPINGS: Dict[str, dict] = {
        "top": {"order": "DESC", "type": "best"},
        "best": {"order": "DESC", "type": "best"},
        "highest": {"order": "DESC", "type": "best"},
        "leading": {"order": "DESC", "type": "best"},
        "largest": {"order": "DESC", "type": "best"},
        "maximum": {"order": "DESC", "type": "best"},
        
        "bottom": {"order": "ASC", "type": "worst"},
        "worst": {"order": "ASC", "type": "worst"},
        "lowest": {"order": "ASC", "type": "worst"},
        "smallest": {"order": "ASC", "type": "worst"},
        "minimum": {"order": "ASC", "type": "worst"},
        "least": {"order": "ASC", "type": "worst"},
    }
    
    # ------------------------------------------
    # AGGREGATION TERMS MAPPING
    # ------------------------------------------
    
    AGGREGATION_MAPPINGS: Dict[str, str] = {
        "total": "SUM",
        "sum": "SUM",
        "overall": "SUM",
        "aggregate": "SUM",
        
        "average": "AVG",
        "avg": "AVG",
        "mean": "AVG",
        
        "count": "COUNT",
        "number of": "COUNT",
        "how many": "COUNT",
        
        "maximum": "MAX",
        "max": "MAX",
        "highest": "MAX",
        
        "minimum": "MIN",
        "min": "MIN",
        "lowest": "MIN",
    }
    
    # ------------------------------------------
    # HELPER METHODS
    # ------------------------------------------
    
    @classmethod
    def get_measure_sql(cls, measure_name: str) -> Optional[str]:
        """Get SQL expression for a measure."""
        measure_name_lower = measure_name.lower()
        
        # Direct match
        if measure_name_lower in cls.MEASURES:
            m = cls.MEASURES[measure_name_lower]
            return f"{m.aggregation.value}({m.column})"
        
        # Search in aliases
        for key, measure in cls.MEASURES.items():
            if measure_name_lower in [a.lower() for a in measure.aliases]:
                return f"{measure.aggregation.value}({measure.column})"
        
        # Check derived metrics
        if measure_name_lower in cls.DERIVED_METRICS:
            return cls.DERIVED_METRICS[measure_name_lower].sql_expression
        
        for key, derived in cls.DERIVED_METRICS.items():
            if measure_name_lower in [a.lower() for a in derived.aliases]:
                return derived.sql_expression
        
        return None
    
    @classmethod
    def get_dimension_column(cls, dimension_name: str) -> Optional[str]:
        """Get column name for a dimension."""
        dimension_name_lower = dimension_name.lower()
        
        # Direct match
        if dimension_name_lower in cls.DIMENSIONS:
            return cls.DIMENSIONS[dimension_name_lower].column
        
        # Search in aliases
        for key, dimension in cls.DIMENSIONS.items():
            if dimension_name_lower in [a.lower() for a in dimension.aliases]:
                return dimension.column
        
        return None
    
    @classmethod
    def get_product_category_sql(cls, category_term: str) -> Optional[str]:
        """Get SQL WHERE clause for a product category."""
        category_lower = category_term.lower().strip()
        
        for key, mapping in cls.PRODUCT_CATEGORY_MAPPINGS.items():
            if category_lower == mapping.business_term.lower():
                return mapping.sql_expression
            if category_lower in [a.lower() for a in mapping.aliases]:
                return mapping.sql_expression
        
        return None
    
    @classmethod
    def get_state_value(cls, state_term: str) -> Optional[str]:
        """Get normalized state name."""
        state_lower = state_term.lower().strip()
        return cls.STATE_MAPPINGS.get(state_lower, state_term.title())
    
    @classmethod
    def generate_prompt_context(cls) -> str:
        """Generate the complete prompt context for the LLM."""
        
        # Build measures section
        measures_text = "MEASURES (Always use aggregation functions):\n"
        for key, measure in cls.MEASURES.items():
            aliases_str = ", ".join(measure.aliases[:5])
            measures_text += f"  - {measure.column}: {measure.description}\n"
            measures_text += f"    SQL: {measure.aggregation.value}({measure.column})\n"
            measures_text += f"    Aliases: {aliases_str}\n"
        
        # Build derived metrics section
        derived_text = "\nDERIVED METRICS (Calculated fields):\n"
        for key, derived in cls.DERIVED_METRICS.items():
            aliases_str = ", ".join(derived.aliases[:3])
            derived_text += f"  - {derived.name}: {derived.description}\n"
            derived_text += f"    SQL: {derived.sql_expression}\n"
            derived_text += f"    Aliases: {aliases_str}\n"
        
        # Build dimensions section
        dimensions_text = "\nDIMENSIONS (Grouping/Filtering columns):\n"
        for key, dimension in cls.DIMENSIONS.items():
            aliases_str = ", ".join(dimension.aliases[:4])
            dimensions_text += f"  - {dimension.column}: {dimension.description}\n"
            dimensions_text += f"    Aliases: {aliases_str}\n"
        
        # Build product category mappings (CRITICAL)
        categories_text = "\nPRODUCT CATEGORY MAPPINGS (CRITICAL - Use exact SQL):\n"
        for key, mapping in cls.PRODUCT_CATEGORY_MAPPINGS.items():
            aliases_str = ", ".join(mapping.aliases[:5])
            categories_text += f"  - \"{mapping.business_term}\"\n"
            categories_text += f"    SQL: {mapping.sql_expression}\n"
            categories_text += f"    Aliases: {aliases_str}\n"
        
        # Build state mappings
        states_text = "\nINDIAN STATES (Use exact spelling):\n"
        states_text += "  Maharashtra, Gujarat, Karnataka, Tamil Nadu, Delhi, Rajasthan, etc.\n"
        
        return measures_text + derived_text + dimensions_text + categories_text + states_text


# ============================================
# LLM PROMPT TEMPLATE
# ============================================

LLM_SYSTEM_PROMPT = """You are an expert SQL analyst for a cable manufacturing company's sales database.
Your task is to convert natural language questions into accurate PostgreSQL queries.

DATABASE: PostgreSQL
TABLE: sales_analytics
GRAIN: One row = Sales data for one customer + item + branch + date

{schema_context}

IMPORTANT RULES:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, DROP
2. ALWAYS use SUM(), AVG(), COUNT() for measures - never return raw measure columns
3. Use GROUP BY for any dimension in SELECT
4. Use NULLIF(x, 0) to prevent division by zero
5. Limit results to 100 rows maximum
6. Period values are in format "Month Year" (e.g., "January 2026")
7. For product categories, use EXACT SQL expressions from the mappings above
8. For margins/percentages, multiply by 100 and use ROUND()
9. Use ILIKE for case-insensitive text matching
10. Order results meaningfully (usually by the main metric DESC)

COMMON PATTERNS:
- Top N customers: ORDER BY SUM(saleamt_ason) DESC LIMIT N
- Sales by state: GROUP BY customer_state
- Category comparison: Use CASE WHEN or separate queries
- Month over month: Compare periods using window functions or UNION
- Margin calculation: SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0)

OUTPUT FORMAT:
Return ONLY the SQL query. No explanations, no markdown, no comments.
"""

LLM_USER_PROMPT_TEMPLATE = """CURRENT FILTERS APPLIED (include in WHERE clause):
{filters}

USER QUESTION:
{question}

Generate the SQL query:"""


# ============================================
# EXAMPLE QUESTIONS AND SQL (For few-shot learning)
# ============================================

EXAMPLE_QA_PAIRS = [
    {
        "question": "Top 5 customers by sales",
        "sql": """SELECT customername, SUM(saleamt_ason) as total_sales
FROM sales_analytics
GROUP BY customername
ORDER BY total_sales DESC
LIMIT 5"""
    },
    {
        "question": "Total sales in Gujarat for Building Wires",
        "sql": """SELECT SUM(saleamt_ason) as total_sales
FROM sales_analytics
WHERE customer_state = 'Gujarat'
AND itemgroup LIKE 'CABLES : BUILDING WIRES%'"""
    },
    {
        "question": "Margin percentage by product category",
        "sql": """SELECT 
    itemgroup,
    SUM(saleamt_ason) as total_sales,
    SUM(profitloss_ason) as total_profit,
    ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) as margin_percent
FROM sales_analytics
GROUP BY itemgroup
ORDER BY total_sales DESC"""
    },
    {
        "question": "Compare sales of LT Cables vs Building Wires",
        "sql": """SELECT 
    CASE 
        WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN 'Building Wires'
        WHEN itemgroup = 'CABLES : LT' THEN 'LT Cables'
    END as category,
    SUM(saleamt_ason) as total_sales,
    SUM(profitloss_ason) as total_profit
FROM sales_analytics
WHERE itemgroup LIKE 'CABLES : BUILDING WIRES%' 
   OR itemgroup = 'CABLES : LT'
GROUP BY 1
ORDER BY total_sales DESC"""
    },
    {
        "question": "Sales by state for January 2026",
        "sql": """SELECT 
    customer_state,
    SUM(saleamt_ason) as total_sales,
    COUNT(DISTINCT customername) as customer_count
FROM sales_analytics
WHERE period = 'January 2026'
AND customer_state IS NOT NULL
GROUP BY customer_state
ORDER BY total_sales DESC
LIMIT 20"""
    },
    {
        "question": "Which distributors have negative margin?",
        "sql": """SELECT 
    groupheadname as distributor,
    SUM(saleamt_ason) as total_sales,
    SUM(profitloss_ason) as total_profit,
    ROUND(SUM(profitloss_ason) * 100.0 / NULLIF(SUM(saleamt_ason), 0), 2) as margin_percent
FROM sales_analytics
GROUP BY groupheadname
HAVING SUM(profitloss_ason) < 0
ORDER BY margin_percent ASC
LIMIT 20"""
    },
    {
        "question": "Month wise sales trend",
        "sql": """SELECT 
    period,
    SUM(saleamt_ason) as total_sales,
    SUM(profitloss_ason) as total_profit,
    SUM(saleqty_ason) as total_quantity
FROM sales_analytics
WHERE period IS NOT NULL
GROUP BY period
ORDER BY period"""
    },
    {
        "question": "Top 10 products by quantity sold",
        "sql": """SELECT 
    itemname as product,
    SUM(saleqty_ason) as total_quantity,
    SUM(saleamt_ason) as total_sales
FROM sales_analytics
GROUP BY itemname
ORDER BY total_quantity DESC
LIMIT 10"""
    },
]


def get_full_llm_prompt(question: str, filters: dict = None) -> tuple[str, str]:
    """
    Generate the complete LLM prompt for SQL generation.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    schema_context = SalesAnalyticsSchema.generate_prompt_context()
    system_prompt = LLM_SYSTEM_PROMPT.format(schema_context=schema_context)
    
    # Format filters
    filter_str = "None"
    if filters:
        filter_parts = []
        for key, value in filters.items():
            if value and value != "ALL":
                filter_parts.append(f"  - {key}: {value}")
        if filter_parts:
            filter_str = "\n".join(filter_parts)
    
    user_prompt = LLM_USER_PROMPT_TEMPLATE.format(
        filters=filter_str,
        question=question
    )
    
    return system_prompt, user_prompt


# ============================================
# ANSWER FORMATTING PROMPT
# ============================================

ANSWER_FORMATTING_PROMPT = """You are a helpful data analyst assistant. 
Format the SQL query results into a clear, conversational response.

RULES:
1. Use natural language, not technical jargon
2. Format numbers properly:
   - Currency: ₹X.XX Cr (for crores) or ₹X.XX Lakh (for lakhs)
   - Percentages: X.X%
   - Quantities: X,XXX units
3. Highlight key insights
4. Keep response concise but informative
5. If data is empty, say so politely
6. Use bullet points for lists
7. Use bold (**text**) for emphasis

ORIGINAL QUESTION: {question}

SQL QUERY EXECUTED:
{sql}

QUERY RESULTS:
{results}

Format a helpful response:"""

