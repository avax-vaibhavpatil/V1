"""
Semantic Layer Module for AI Chatbot

This module provides two approaches:

1. JSON-based (RECOMMENDED): 
   Use schema_loader.py which loads from sales_analytics.json
   
   from app.semantic import get_schema, get_llm_prompts
   
   schema = get_schema()
   system_prompt, user_prompt = get_llm_prompts(question, filters)

2. Python-based (Alternative):
   Use sales_schema.py for static schema definitions
   
   from app.semantic import SalesAnalyticsSchema
   
   sql = SalesAnalyticsSchema.get_measure_sql("sales")
"""

# ==========================================
# JSON-based loader (RECOMMENDED)
# ==========================================
from app.semantic.schema_loader import (
    SemanticSchema,
    get_schema,
    get_llm_prompts,
    get_measure_sql,
    get_product_category_sql,
    get_state_value,
)

# ==========================================
# Python-based schema (Alternative)
# ==========================================
from app.semantic.sales_schema import (
    SalesAnalyticsSchema,
    Measure,
    Dimension,
    DerivedMetric,
    BusinessTermMapping,
    AggregationType,
    ColumnType,
    LLM_SYSTEM_PROMPT,
    LLM_USER_PROMPT_TEMPLATE,
    ANSWER_FORMATTING_PROMPT,
    EXAMPLE_QA_PAIRS,
    get_full_llm_prompt,
)

__all__ = [
    # JSON-based (recommended)
    "SemanticSchema",
    "get_schema",
    "get_llm_prompts",
    "get_measure_sql",
    "get_product_category_sql",
    "get_state_value",
    
    # Python-based (alternative)
    "SalesAnalyticsSchema",
    "Measure",
    "Dimension",
    "DerivedMetric",
    "BusinessTermMapping",
    "AggregationType",
    "ColumnType",
    "LLM_SYSTEM_PROMPT",
    "LLM_USER_PROMPT_TEMPLATE",
    "ANSWER_FORMATTING_PROMPT",
    "EXAMPLE_QA_PAIRS",
    "get_full_llm_prompt",
]
