"""
Semantic Schema Loader

Loads the semantic layer from JSON file and provides helper methods.
This is the RECOMMENDED approach: JSON as source of truth + Python for methods.

Usage:
    from app.semantic.schema_loader import SemanticSchema
    
    schema = SemanticSchema.load()  # Load from JSON file
    
    # Get SQL for a measure
    sql = schema.get_measure_sql("sales")  # → "SUM(saleamt_ason)"
    
    # Get product category SQL
    sql = schema.get_product_category_sql("building wires")  # → "itemgroup LIKE 'CABLES : BUILDING WIRES%'"
    
    # Generate LLM prompts
    system_prompt, user_prompt = schema.get_llm_prompts(question, filters)
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from functools import lru_cache


class SemanticSchema:
    """
    Semantic schema loaded from JSON file.
    Provides helper methods for SQL generation and LLM prompts.
    """
    
    # Default path to JSON file
    DEFAULT_JSON_PATH = Path(__file__).parent.parent.parent / "sales_analytics.json"
    
    def __init__(self, schema_data: dict):
        """Initialize with loaded schema data."""
        self._raw = schema_data
        self._table_data = schema_data.get("tables", {}).get("public.sales_analytics", {})
        
        # Extract components
        self.columns = self._table_data.get("columns", {})
        self.measures = self._table_data.get("measures", [])
        self.dimensions = self._table_data.get("dimensions", [])
        self.derived_measures = self._table_data.get("derived_measures", [])
        self.business_mappings = self._table_data.get("business_term_mappings", {})
        self.llm_config = self._table_data.get("llm_config", {})
        self.metadata = self._table_data.get("metadata", {})
        
        # Build lookup caches
        self._build_caches()
    
    def _build_caches(self):
        """Build internal lookup caches for fast access."""
        # Alias to column name mapping
        self._alias_to_column: Dict[str, str] = {}
        for col_name, col_data in self.columns.items():
            aliases = col_data.get("aliases", [])
            for alias in aliases:
                self._alias_to_column[alias.lower()] = col_name
            # Also map the column name itself
            self._alias_to_column[col_name.lower()] = col_name
        
        # Product category alias to key mapping
        self._product_alias_to_key: Dict[str, str] = {}
        product_cats = self.business_mappings.get("product_categories", {})
        for key, data in product_cats.items():
            if key.startswith("_"):
                continue
            # Map business term
            self._product_alias_to_key[data.get("business_term", "").lower()] = key
            # Map aliases
            for alias in data.get("aliases", []):
                self._product_alias_to_key[alias.lower()] = key
        
        # State alias mapping
        self._state_alias_to_value: Dict[str, str] = {}
        states = self.business_mappings.get("indian_states", {})
        for key, data in states.items():
            if key.startswith("_"):
                continue
            value = data.get("value", "")
            self._state_alias_to_value[key.replace("_", " ").lower()] = value
            self._state_alias_to_value[value.lower()] = value
            for alias in data.get("aliases", []):
                self._state_alias_to_value[alias.lower()] = value
        
        # Derived measure alias mapping
        self._derived_alias_to_expression: Dict[str, str] = {}
        for dm in self.derived_measures:
            name = dm.get("name", "")
            expr = dm.get("expression", "")
            self._derived_alias_to_expression[name.lower()] = expr
            for alias in dm.get("aliases", []):
                self._derived_alias_to_expression[alias.lower()] = expr
    
    @classmethod
    def load(cls, json_path: Optional[str] = None) -> "SemanticSchema":
        """
        Load semantic schema from JSON file.
        
        Args:
            json_path: Path to JSON file. Uses default if not provided.
            
        Returns:
            SemanticSchema instance
        """
        path = Path(json_path) if json_path else cls.DEFAULT_JSON_PATH
        
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(data)
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_instance(cls) -> "SemanticSchema":
        """Get cached singleton instance."""
        return cls.load()
    
    # ==========================================
    # Column/Measure Methods
    # ==========================================
    
    def get_column_name(self, alias_or_name: str) -> Optional[str]:
        """Get actual column name from alias or name."""
        return self._alias_to_column.get(alias_or_name.lower())
    
    def get_column_info(self, column_name: str) -> Optional[dict]:
        """Get full column information."""
        return self.columns.get(column_name)
    
    def is_measure(self, column_name: str) -> bool:
        """Check if column is a measure."""
        col = self.get_column_name(column_name)
        if col:
            return col in self.measures
        return False
    
    def is_dimension(self, column_name: str) -> bool:
        """Check if column is a dimension."""
        col = self.get_column_name(column_name)
        if col:
            return col in self.dimensions
        return False
    
    def get_measure_sql(self, measure_name: str) -> Optional[str]:
        """
        Get SQL expression for a measure.
        
        Args:
            measure_name: Measure name or alias
            
        Returns:
            SQL expression like "SUM(saleamt_ason)" or None if not found
        """
        measure_lower = measure_name.lower()
        
        # Check derived measures first
        if measure_lower in self._derived_alias_to_expression:
            return self._derived_alias_to_expression[measure_lower]
        
        # Check regular measures
        col_name = self.get_column_name(measure_name)
        if col_name and col_name in self.measures:
            col_info = self.columns.get(col_name, {})
            agg = col_info.get("aggregation", "sum").upper()
            return f"{agg}({col_name})"
        
        return None
    
    def get_dimension_column(self, dimension_name: str) -> Optional[str]:
        """Get column name for a dimension."""
        col_name = self.get_column_name(dimension_name)
        if col_name and col_name in self.dimensions:
            return col_name
        return None
    
    # ==========================================
    # Business Term Mapping Methods
    # ==========================================
    
    def get_product_category_sql(self, category_term: str) -> Optional[str]:
        """
        Get SQL WHERE clause for a product category.
        
        Args:
            category_term: Business term like "Building Wires" or "lt cables"
            
        Returns:
            SQL expression like "itemgroup LIKE 'CABLES : BUILDING WIRES%'" or None
        """
        key = self._product_alias_to_key.get(category_term.lower().strip())
        if key:
            product_cats = self.business_mappings.get("product_categories", {})
            return product_cats.get(key, {}).get("sql_expression")
        return None
    
    def get_state_value(self, state_term: str) -> str:
        """
        Get normalized state name.
        
        Args:
            state_term: State name or abbreviation like "mh" or "maharashtra"
            
        Returns:
            Normalized state name like "Maharashtra"
        """
        return self._state_alias_to_value.get(
            state_term.lower().strip(), 
            state_term.title()
        )
    
    def get_month_name(self, month_term: str) -> Optional[str]:
        """Get normalized month name."""
        months = self.business_mappings.get("time_periods", {}).get("months", {})
        return months.get(month_term.lower())
    
    def get_comparison_operator(self, term: str) -> Optional[str]:
        """Get SQL comparison operator from natural language term."""
        operators = self.business_mappings.get("comparison_operators", {})
        return operators.get(term.lower().replace(" ", "_"))
    
    def get_ranking_info(self, term: str) -> Optional[dict]:
        """Get ranking information (order direction) from term."""
        rankings = self.business_mappings.get("ranking_terms", {})
        return rankings.get(term.lower())
    
    def get_aggregation_function(self, term: str) -> Optional[str]:
        """Get SQL aggregation function from natural language term."""
        aggs = self.business_mappings.get("aggregation_terms", {})
        return aggs.get(term.lower().replace(" ", "_"))
    
    # ==========================================
    # LLM Prompt Methods
    # ==========================================
    
    def generate_schema_context(self) -> str:
        """Generate formatted schema context for LLM prompt."""
        lines = []
        
        # Measures section
        lines.append("MEASURES (Always use aggregation functions):")
        for measure_name in self.measures:
            col = self.columns.get(measure_name, {})
            aliases = ", ".join(col.get("aliases", [])[:5])
            agg = col.get("aggregation", "sum").upper()
            lines.append(f"  - {measure_name}: {col.get('description', '')}")
            lines.append(f"    SQL: {agg}({measure_name})")
            lines.append(f"    Aliases: {aliases}")
        
        # Derived measures section
        lines.append("\nDERIVED METRICS (Calculated fields):")
        for dm in self.derived_measures:
            aliases = ", ".join(dm.get("aliases", [])[:3])
            lines.append(f"  - {dm['name']}: {dm.get('description', '')}")
            lines.append(f"    SQL: {dm['expression']}")
            lines.append(f"    Aliases: {aliases}")
        
        # Dimensions section
        lines.append("\nDIMENSIONS (Grouping/Filtering columns):")
        for dim_name in self.dimensions[:15]:  # Limit to most important
            col = self.columns.get(dim_name, {})
            aliases = ", ".join(col.get("aliases", [])[:4])
            lines.append(f"  - {dim_name}: {col.get('description', '')}")
            lines.append(f"    Aliases: {aliases}")
        
        # Product category mappings (CRITICAL)
        lines.append("\nPRODUCT CATEGORY MAPPINGS (CRITICAL - Use exact SQL):")
        product_cats = self.business_mappings.get("product_categories", {})
        for key, data in product_cats.items():
            if key.startswith("_"):
                continue
            aliases = ", ".join(data.get("aliases", [])[:5])
            lines.append(f"  - \"{data['business_term']}\"")
            lines.append(f"    SQL: {data['sql_expression']}")
            lines.append(f"    Aliases: {aliases}")
        
        # States
        lines.append("\nINDIAN STATES (Use exact spelling):")
        lines.append("  Maharashtra, Gujarat, Karnataka, Tamil Nadu, Delhi, Rajasthan, etc.")
        
        return "\n".join(lines)
    
    def get_llm_prompts(
        self, 
        question: str, 
        filters: Optional[dict] = None
    ) -> Tuple[str, str]:
        """
        Generate complete LLM prompts for SQL generation.
        
        Args:
            question: User's natural language question
            filters: Current dashboard filters
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Generate schema context
        schema_context = self.generate_schema_context()
        
        # Build system prompt
        system_template = self.llm_config.get(
            "system_prompt_template",
            "You are an expert SQL analyst.\n\n{schema_context}\n\nGenerate only SELECT queries."
        )
        system_prompt = system_template.format(schema_context=schema_context)
        
        # Format filters
        filter_str = "None"
        if filters:
            filter_parts = []
            for key, value in filters.items():
                if value and value != "ALL":
                    filter_parts.append(f"  - {key}: {value}")
            if filter_parts:
                filter_str = "\n".join(filter_parts)
        
        # Build user prompt
        user_template = self.llm_config.get(
            "user_prompt_template",
            "FILTERS:\n{filters}\n\nQUESTION:\n{question}\n\nGenerate SQL:"
        )
        user_prompt = user_template.format(filters=filter_str, question=question)
        
        return system_prompt, user_prompt
    
    def get_answer_format_prompt(
        self, 
        question: str, 
        sql: str, 
        results: Any
    ) -> str:
        """Generate prompt for formatting query results."""
        template = self.llm_config.get(
            "answer_format_template",
            "Format these results:\n\nQuestion: {question}\nSQL: {sql}\nResults: {results}"
        )
        return template.format(
            question=question,
            sql=sql,
            results=str(results)
        )
    
    def get_example_qa_pairs(self) -> List[dict]:
        """Get example question-SQL pairs for few-shot learning."""
        return self.llm_config.get("example_qa_pairs", [])
    
    # ==========================================
    # Utility Methods
    # ==========================================
    
    def get_all_aliases(self) -> Dict[str, str]:
        """Get all alias to column mappings."""
        return self._alias_to_column.copy()
    
    def get_table_info(self) -> dict:
        """Get table metadata."""
        return {
            "description": self._table_data.get("description"),
            "metadata": self.metadata,
            "model": self._table_data.get("model"),
        }
    
    def reload(self):
        """Reload schema from JSON file (for hot-reloading)."""
        # Clear the cached instance
        SemanticSchema.get_instance.cache_clear()
        return SemanticSchema.load()


# ==========================================
# Convenience Functions
# ==========================================

def get_schema() -> SemanticSchema:
    """Get the semantic schema instance (cached)."""
    return SemanticSchema.get_instance()


def get_llm_prompts(question: str, filters: Optional[dict] = None) -> Tuple[str, str]:
    """Generate LLM prompts for a question."""
    return get_schema().get_llm_prompts(question, filters)


def get_measure_sql(measure_name: str) -> Optional[str]:
    """Get SQL expression for a measure."""
    return get_schema().get_measure_sql(measure_name)


def get_product_category_sql(category_term: str) -> Optional[str]:
    """Get SQL WHERE clause for a product category."""
    return get_schema().get_product_category_sql(category_term)


def get_state_value(state_term: str) -> str:
    """Get normalized state name."""
    return get_schema().get_state_value(state_term)

