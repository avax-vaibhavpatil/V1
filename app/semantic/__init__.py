"""
Semantic Layer Module for AI Chatbot

This module provides:

1. Schema Loader (schema_loader.py):
   Loads semantic definitions from JSON files in the schemas/ folder
   
   from app.semantic import SemanticSchema, get_schema
   
   schema = get_schema()  # Loads sales_analytics.json by default
   schema = SemanticSchema.load_by_name("inventory")  # Load other schemas

2. LLM Prompts (llm_prompts.py):
   Contains system prompts, example Q&A pairs, and formatting prompts
   
   from app.semantic import build_complete_prompt, get_system_prompt
   
   system_prompt, user_prompt = build_complete_prompt(question, filters)

3. Legacy Python Schema (sales_schema.py):
   Alternative static schema definitions (not recommended for new features)
"""

# ==========================================
# Schema Loader
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
# LLM Prompts (RECOMMENDED for chatbot)
# ==========================================
from app.semantic.llm_prompts import (
    SYSTEM_PROMPT,
    EXAMPLE_QA_PAIRS as LLM_EXAMPLE_QA_PAIRS,
    ERROR_RESPONSES,
    get_system_prompt,
    get_few_shot_examples,
    format_user_prompt,
    format_answer_prompt,
    get_error_response,
    build_complete_prompt,
)

# ==========================================
# Legacy Python-based schema
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
    # Schema loader
    "SemanticSchema",
    "get_schema",
    "get_llm_prompts",
    "get_measure_sql",
    "get_product_category_sql",
    "get_state_value",
    
    # LLM Prompts (recommended)
    "SYSTEM_PROMPT",
    "LLM_EXAMPLE_QA_PAIRS",
    "ERROR_RESPONSES",
    "get_system_prompt",
    "get_few_shot_examples",
    "format_user_prompt",
    "format_answer_prompt",
    "get_error_response",
    "build_complete_prompt",
    
    # Legacy Python-based
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
