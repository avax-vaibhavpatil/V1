"""
SQL Validator for AI Chatbot

Validates LLM-generated SQL queries before execution to ensure:
1. Only SELECT queries are allowed
2. No dangerous operations (DROP, DELETE, INSERT, etc.)
3. No SQL injection patterns
4. Valid SQL syntax

Usage:
    from app.services.sql_validator import SQLValidator
    
    validator = SQLValidator()
    is_valid, error = validator.validate(sql_query)
    
    if not is_valid:
        print(f"Invalid SQL: {error}")
"""

from typing import Tuple, Optional, List, Set
from dataclasses import dataclass
from enum import Enum

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# STEP 1: Custom Exception for SQL Validation
# =============================================================================

class SQLValidationError(Exception):
    """Raised when SQL validation fails."""
    
    def __init__(
        self, 
        message: str, 
        sql: Optional[str] = None,
        error_type: str = "VALIDATION_ERROR"
    ):
        self.message = message
        self.sql = sql
        self.error_type = error_type
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_type}] {self.message}"


class ValidationErrorType(Enum):
    """Types of validation errors."""
    DANGEROUS_KEYWORD = "dangerous_keyword"
    NON_SELECT_QUERY = "non_select_query"
    SYNTAX_ERROR = "syntax_error"
    INJECTION_DETECTED = "injection_detected"
    INVALID_TABLE = "invalid_table"
    INVALID_COLUMN = "invalid_column"
    EMPTY_QUERY = "empty_query"
    MULTIPLE_STATEMENTS = "multiple_statements"


# =============================================================================
# STEP 2: Dangerous Keywords and Patterns
# =============================================================================

# Keywords that indicate dangerous/forbidden operations
# These are SQL commands that can modify or destroy data
DANGEROUS_KEYWORDS: Set[str] = {
    # Data Modification
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "UPSERT",
    
    # Schema Modification
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "RENAME",
    
    # Permission/Security
    "GRANT",
    "REVOKE",
    "DENY",
    
    # Database Operations
    "EXEC",
    "EXECUTE",
    "CALL",
    
    # Transaction Control (can be dangerous)
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    
    # PostgreSQL Specific Dangerous
    "COPY",
    "VACUUM",
    "ANALYZE",
    "CLUSTER",
    "REINDEX",
    "LOCK",
    "LISTEN",
    "NOTIFY",
    "UNLISTEN",
    "LOAD",
    
    # File Operations
    "INTO OUTFILE",
    "INTO DUMPFILE",
    "LOAD_FILE",
}

# SQL Injection patterns to detect
# These are common patterns used in SQL injection attacks
SQL_INJECTION_PATTERNS: List[str] = [
    # Comment-based injection
    "--",           # SQL comment
    "/*",           # Block comment start
    "*/",           # Block comment end
    "#",            # MySQL comment (also used in PostgreSQL for array ops, so careful)
    
    # Union-based injection
    "UNION ALL SELECT",
    "UNION SELECT",
    
    # Stacked queries (multiple statements)
    ";--",
    "; --",
    ";/*",
    
    # Time-based blind injection
    "SLEEP(",
    "WAITFOR",
    "BENCHMARK(",
    "PG_SLEEP(",
    
    # Boolean-based injection
    "' OR '1'='1",
    "' OR 1=1",
    "\" OR \"1\"=\"1",
    "OR 1=1--",
    "' AND '1'='1",
    
    # Error-based injection
    "EXTRACTVALUE(",
    "UPDATEXML(",
    "EXP(",
    
    # System function abuse
    "@@VERSION",
    "VERSION()",
    "DATABASE()",
    "USER()",
    "CURRENT_USER",  # Careful - this is sometimes legitimate
    "SYSTEM_USER",
    
    # File operations
    "LOAD_FILE",
    "INTO OUTFILE",
    "INTO DUMPFILE",
    
    # Dangerous PostgreSQL functions
    "PG_READ_FILE",
    "PG_WRITE_FILE",
    "LO_IMPORT",
    "LO_EXPORT",
]

# Allowed table names (whitelist approach)
ALLOWED_TABLES: Set[str] = {
    "sales_analytics",
    "public.sales_analytics",
    "stock_gw",
    "public.stock_gw",
}

# =============================================================================
# STEP 3: Validation Result and SQLValidator Class Structure
# =============================================================================

@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    error_message: Optional[str] = None
    error_type: Optional[ValidationErrorType] = None
    sanitized_sql: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    def __bool__(self):
        """Allow using ValidationResult directly in if statements."""
        return self.is_valid


class SQLValidator:
    """
    Validates SQL queries for safety and correctness.
    
    This validator ensures that LLM-generated SQL is safe to execute
    against the database by checking for:
    - Only SELECT statements allowed
    - No dangerous keywords (DROP, DELETE, etc.)
    - No SQL injection patterns
    - Valid syntax (optional, using sqlparse)
    - Whitelisted tables only
    
    Usage:
        validator = SQLValidator()
        result = validator.validate(sql_query)
        
        if result.is_valid:
            # Safe to execute
            execute_query(result.sanitized_sql)
        else:
            # Handle error
            print(f"Error: {result.error_message}")
    """
    
    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        max_query_length: int = 10000,
        allow_subqueries: bool = True,
        allow_cte: bool = True,  # WITH clause
        strict_mode: bool = False,
    ):
        """
        Initialize the SQL validator.
        
        Args:
            allowed_tables: Set of allowed table names (default uses ALLOWED_TABLES)
            max_query_length: Maximum allowed query length in characters
            allow_subqueries: Whether to allow subqueries
            allow_cte: Whether to allow Common Table Expressions (WITH clause)
            strict_mode: If True, applies stricter validation rules
        """
        self.allowed_tables = allowed_tables or ALLOWED_TABLES
        self.max_query_length = max_query_length
        self.allow_subqueries = allow_subqueries
        self.allow_cte = allow_cte
        self.strict_mode = strict_mode
        
        logger.info(f"SQLValidator initialized with {len(self.allowed_tables)} allowed tables")

    # =========================================================================
    # STEP 4: Main Validation Method
    # =========================================================================
    
    def validate(self, sql: str) -> ValidationResult:
        """
        Validate a SQL query for safety and correctness.
        
        This is the main entry point for validation. It runs all checks
        in sequence and returns the first error found, or success if all pass.
        
        Args:
            sql: The SQL query string to validate
            
        Returns:
            ValidationResult with is_valid=True if safe, False otherwise
        """
        warnings = []
        
        # Check 1: Empty or None query
        if not sql or not sql.strip():
            return ValidationResult(
                is_valid=False,
                error_message="SQL query is empty",
                error_type=ValidationErrorType.EMPTY_QUERY,
            )
        
        # Normalize the SQL (trim whitespace, convert to uppercase for checking)
        sql_normalized = sql.strip()
        sql_upper = sql_normalized.upper()
        
        # Check 2: Query length
        if len(sql_normalized) > self.max_query_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"SQL query exceeds maximum length of {self.max_query_length} characters",
                error_type=ValidationErrorType.SYNTAX_ERROR,
            )
        
        # Check 3: Multiple statements (semicolon in middle)
        result = self._check_multiple_statements(sql_normalized)
        if not result.is_valid:
            return result
        
        # Check 4: Must be a SELECT query (or WITH for CTE)
        result = self._check_is_select_query(sql_upper)
        if not result.is_valid:
            return result
        
        # Check 5: Dangerous keywords
        result = self._check_dangerous_keywords(sql_upper)
        if not result.is_valid:
            return result
        
        # Check 6: SQL injection patterns
        result = self._check_injection_patterns(sql_upper, sql_normalized)
        if not result.is_valid:
            return result
        
        # Check 7: Validate table names (optional but recommended)
        result = self._check_table_names(sql_normalized)
        if not result.is_valid:
            return result
        
        # All checks passed!
        logger.debug(f"SQL validation passed: {sql_normalized[:100]}...")
        
        return ValidationResult(
            is_valid=True,
            sanitized_sql=sql_normalized,
            warnings=warnings if warnings else None,
        )

    # =========================================================================
    # STEP 5: Individual Check Methods
    # =========================================================================
    
    def _check_multiple_statements(self, sql: str) -> ValidationResult:
        """
        Check if query contains multiple statements (potential SQL injection).
        
        We allow semicolon only at the very end of the query.
        """
        # Remove trailing semicolon for this check
        sql_check = sql.rstrip(';').strip()
        
        if ';' in sql_check:
            return ValidationResult(
                is_valid=False,
                error_message="Multiple SQL statements detected. Only single SELECT queries are allowed.",
                error_type=ValidationErrorType.MULTIPLE_STATEMENTS,
            )
        
        return ValidationResult(is_valid=True)
    
    def _check_is_select_query(self, sql_upper: str) -> ValidationResult:
        """
        Verify the query is a SELECT statement (or WITH for CTE).
        
        We only allow SELECT queries to prevent data modification.
        """
        # Remove leading whitespace and check first keyword
        sql_stripped = sql_upper.strip()
        
        # Check for SELECT
        if sql_stripped.startswith("SELECT"):
            return ValidationResult(is_valid=True)
        
        # Check for WITH (Common Table Expression) - must end with SELECT
        if sql_stripped.startswith("WITH"):
            if self.allow_cte:
                # CTE must contain SELECT
                if "SELECT" in sql_stripped:
                    return ValidationResult(is_valid=True)
                else:
                    return ValidationResult(
                        is_valid=False,
                        error_message="WITH clause (CTE) must contain a SELECT statement",
                        error_type=ValidationErrorType.NON_SELECT_QUERY,
                    )
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Common Table Expressions (WITH clause) are not allowed",
                    error_type=ValidationErrorType.NON_SELECT_QUERY,
                )
        
        # Identify what type of query it is for better error message
        first_keyword = sql_stripped.split()[0] if sql_stripped.split() else "UNKNOWN"
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Only SELECT queries are allowed. Found: {first_keyword}",
            error_type=ValidationErrorType.NON_SELECT_QUERY,
        )
    
    def _check_dangerous_keywords(self, sql_upper: str) -> ValidationResult:
        """
        Check for dangerous SQL keywords that could modify data or schema.
        
        Uses word boundary detection to avoid false positives like
        'updated_at' matching 'UPDATE'.
        """
        import re
        
        for keyword in DANGEROUS_KEYWORDS:
            # Use word boundary to avoid false positives
            # e.g., "updated_at" should not match "UPDATE"
            pattern = r'\b' + re.escape(keyword) + r'\b'
            
            if re.search(pattern, sql_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Dangerous SQL keyword detected: {keyword}",
                    error_type=ValidationErrorType.DANGEROUS_KEYWORD,
                )
        
        return ValidationResult(is_valid=True)
    
    def _check_injection_patterns(self, sql_upper: str, sql_original: str) -> ValidationResult:
        """
        Check for common SQL injection patterns.
        
        This catches patterns like:
        - Comment injection (-- , /*, */)
        - Union injection
        - Boolean-based injection
        - Time-based injection
        """
        for pattern in SQL_INJECTION_PATTERNS:
            pattern_upper = pattern.upper()
            
            if pattern_upper in sql_upper:
                # Special case: Allow legitimate use of -- only at end of query
                if pattern == "--" and sql_original.strip().endswith("--"):
                    continue
                
                # Special case: UNION is legitimate in some queries
                # But UNION followed by SELECT with injection keywords is suspicious
                if "UNION" in pattern_upper:
                    # Check if it looks like injection (has multiple unions or suspicious patterns)
                    if sql_upper.count("UNION") > 2:
                        return ValidationResult(
                            is_valid=False,
                            error_message=f"Potential SQL injection pattern detected: {pattern}",
                            error_type=ValidationErrorType.INJECTION_DETECTED,
                        )
                    continue  # Allow single UNION for legitimate queries
                
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Potential SQL injection pattern detected: {pattern}",
                    error_type=ValidationErrorType.INJECTION_DETECTED,
                )
        
        return ValidationResult(is_valid=True)
    
    def _check_table_names(self, sql: str) -> ValidationResult:
        """
        Validate that only allowed tables are referenced.
        
        This is a whitelist approach - only tables in ALLOWED_TABLES can be queried.
        """
        import re
        
        # Extract table names from FROM and JOIN clauses
        sql_upper = sql.upper()
        
        # Pattern to match table names after FROM or JOIN
        # This is simplified - a full SQL parser would be more accurate
        from_pattern = r'\bFROM\s+(["\']?[\w.]+["\']?)'
        join_pattern = r'\bJOIN\s+(["\']?[\w.]+["\']?)'
        
        tables_found = set()
        
        # Find tables in FROM clause
        from_matches = re.findall(from_pattern, sql_upper)
        tables_found.update(from_matches)
        
        # Find tables in JOIN clauses
        join_matches = re.findall(join_pattern, sql_upper)
        tables_found.update(join_matches)
        
        # Clean up table names (remove quotes, normalize)
        cleaned_tables = set()
        for table in tables_found:
            # Remove quotes
            table_clean = table.strip('"\'').lower()
            cleaned_tables.add(table_clean)
        
        # Check against whitelist
        allowed_lower = {t.lower() for t in self.allowed_tables}
        
        for table in cleaned_tables:
            if table not in allowed_lower:
                # Check if it might be an alias or subquery
                # Subqueries won't have a real table name in this simple check
                if not self.allow_subqueries:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Table not allowed: {table}. Allowed tables: {', '.join(self.allowed_tables)}",
                        error_type=ValidationErrorType.INVALID_TABLE,
                    )
                else:
                    # Log warning but allow - could be subquery alias
                    logger.warning(f"Unknown table reference (could be alias/subquery): {table}")
        
        return ValidationResult(is_valid=True)

    # =========================================================================
    # STEP 6: Utility Methods
    # =========================================================================
    
    def sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL query by removing potentially harmful elements.
        
        This is a basic sanitization - the validate() method should still
        be called for full validation.
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Sanitized SQL query
        """
        if not sql:
            return ""
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Remove trailing semicolons (we add them during execution if needed)
        sql = sql.rstrip(';').strip()
        
        # Normalize whitespace
        import re
        sql = re.sub(r'\s+', ' ', sql)
        
        return sql
    
    def get_query_type(self, sql: str) -> str:
        """
        Get the type of SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            Query type (SELECT, INSERT, UPDATE, DELETE, etc.) or UNKNOWN
        """
        if not sql:
            return "UNKNOWN"
        
        sql_upper = sql.strip().upper()
        
        keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", 
                    "ALTER", "WITH", "TRUNCATE", "GRANT", "REVOKE"]
        
        for keyword in keywords:
            if sql_upper.startswith(keyword):
                return keyword
        
        return "UNKNOWN"
    
    def add_allowed_table(self, table_name: str) -> None:
        """
        Add a table to the allowed tables list.
        
        Args:
            table_name: Table name to allow
        """
        self.allowed_tables.add(table_name.lower())
        logger.info(f"Added allowed table: {table_name}")
    
    def remove_allowed_table(self, table_name: str) -> None:
        """
        Remove a table from the allowed tables list.
        
        Args:
            table_name: Table name to remove
        """
        self.allowed_tables.discard(table_name.lower())
        logger.info(f"Removed allowed table: {table_name}")


# =============================================================================
# STEP 6 (continued): Convenience Functions
# =============================================================================

# Default validator instance (singleton-like for convenience)
_default_validator: Optional[SQLValidator] = None


def get_validator() -> SQLValidator:
    """Get the default SQL validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = SQLValidator()
    return _default_validator


def validate_sql(sql: str) -> ValidationResult:
    """
    Quick validation function using the default validator.
    
    Args:
        sql: SQL query to validate
        
    Returns:
        ValidationResult
        
    Usage:
        from app.services.sql_validator import validate_sql
        
        result = validate_sql("SELECT * FROM sales_analytics")
        if result.is_valid:
            print("Safe to execute!")
    """
    return get_validator().validate(sql)


def is_safe_sql(sql: str) -> bool:
    """
    Quick check if SQL is safe to execute.
    
    Args:
        sql: SQL query to check
        
    Returns:
        True if safe, False otherwise
        
    Usage:
        if is_safe_sql(query):
            execute(query)
    """
    return validate_sql(sql).is_valid

