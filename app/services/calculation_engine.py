"""Calculation engine for DSL parsing and execution."""

import re
from typing import Any, Optional, Union

from app.core.exceptions import CalculationError, ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CalculationEngine:
    """Engine for parsing and validating calculation DSL."""

    # Supported operators
    OPERATORS = ["+", "-", "*", "/", "(", ")"]
    # Supported functions
    FUNCTIONS = ["SUM", "AVG", "COUNT", "MIN", "MAX", "IF", "CASE", "DISTINCT_COUNT"]
    # Reserved keywords
    RESERVED = ["AND", "OR", "NOT", "NULL", "TRUE", "FALSE"]

    @staticmethod
    def validate_formula(formula: str, available_fields: list[str]) -> tuple[bool, Optional[str], Optional[dict]]:
        """
        Validate a calculation formula.

        Args:
            formula: DSL formula string
            available_fields: List of available field names

        Returns:
            Tuple of (is_valid, error_message, validation_result)
        """
        if not formula or not formula.strip():
            return False, "Formula cannot be empty", None

        formula = formula.strip()

        # Check for nested aggregations (not allowed)
        aggregation_pattern = r"\b(SUM|AVG|COUNT|MIN|MAX|DISTINCT_COUNT)\s*\("
        matches = list(re.finditer(aggregation_pattern, formula, re.IGNORECASE))
        if len(matches) > 1:
            return (
                False,
                "Nested aggregations are not allowed. Only one aggregation function per formula.",
                None,
            )

        # Check for balanced parentheses
        if formula.count("(") != formula.count(")"):
            return False, "Unbalanced parentheses", None

        # Extract field references (words that are not operators, functions, or reserved)
        field_pattern = r"\b([A-Za-z_][A-Za-z0-9_]*)\b"
        potential_fields = re.findall(field_pattern, formula)

        # Validate field names
        invalid_fields = []
        for field in potential_fields:
            field_upper = field.upper()
            if (
                field_upper not in CalculationEngine.FUNCTIONS
                and field_upper not in CalculationEngine.RESERVED
                and field not in available_fields
            ):
                invalid_fields.append(field)

        if invalid_fields:
            return (
                False,
                f"Invalid field references: {', '.join(invalid_fields)}",
                {"invalid_fields": invalid_fields},
            )

        # Basic syntax validation - check for invalid operator sequences
        invalid_patterns = [
            r"[+\-*/]{2,}",  # Multiple operators in a row
            r"\([+\-*/]",  # Operator after opening paren
            r"[+\-*/]\)",  # Operator before closing paren
        ]
        for pattern in invalid_patterns:
            if re.search(pattern, formula):
                return False, f"Invalid operator sequence in formula", None

        validation_result = {
            "formula": formula,
            "is_valid": True,
            "fields_used": [f for f in potential_fields if f in available_fields],
        }

        return True, None, validation_result

    @staticmethod
    def parse_formula(formula: str) -> dict[str, Any]:
        """
        Parse a formula into an execution tree.

        Args:
            formula: Validated formula string

        Returns:
            Parsed formula structure

        Raises:
            CalculationError: If parsing fails
        """
        # This is a simplified parser - in production, use a proper expression parser
        # For now, return a structure that can be used for execution
        return {
            "original": formula,
            "normalized": formula.upper().strip(),
            "type": "expression",  # or "aggregation" if starts with SUM/AVG/etc.
        }

    @staticmethod
    def execute_calculation(
        formula: str, data: Union[dict, list[dict]], context: Optional[dict] = None
    ) -> Any:
        """
        Execute a calculation formula on data.

        Args:
            formula: Validated formula
            data: Data to calculate on (dict for single row, list for aggregation)
            context: Additional context variables

        Returns:
            Calculated result

        Raises:
            CalculationError: If execution fails
        """
        try:
            # This is a simplified executor
            # In production, use a proper expression evaluator with sandboxing

            # Replace field references with values
            if isinstance(data, dict):
                # Single row calculation
                result = CalculationEngine._evaluate_single_row(formula, data, context)
            else:
                # Aggregation calculation
                result = CalculationEngine._evaluate_aggregation(formula, data, context)

            return result
        except Exception as e:
            raise CalculationError(
                f"Calculation execution failed: {str(e)}", formula=formula
            )

    @staticmethod
    def _evaluate_single_row(
        formula: str, row: dict, context: Optional[dict]
    ) -> Any:
        """Evaluate formula on a single row."""
        # Replace field names with values
        for field, value in row.items():
            formula = formula.replace(field, str(value) if value is not None else "0")

        # Handle division by zero
        if "/" in formula and "0" in formula.split("/")[1:]:
            raise CalculationError("Division by zero", formula=formula)

        # Evaluate (in production, use a safe evaluator)
        try:
            return eval(formula)  # NOQA: S307 - In production, use a safe evaluator
        except Exception as e:
            raise CalculationError(f"Evaluation error: {str(e)}", formula=formula)

    @staticmethod
    def _evaluate_aggregation(
        formula: str, data: list[dict], context: Optional[dict]
    ) -> Any:
        """Evaluate aggregation formula."""
        # Simplified - in production, implement proper aggregation logic
        # This would handle SUM, AVG, COUNT, etc.
        return 0  # Placeholder

    @staticmethod
    def check_division_by_zero(formula: str) -> tuple[bool, Optional[str]]:
        """
        Check if formula could result in division by zero.

        Args:
            formula: Formula to check

        Returns:
            Tuple of (has_risk, warning_message)
        """
        if "/" not in formula:
            return False, None

        # Simple check - in production, use static analysis
        return True, "Formula contains division - ensure denominator is never zero"


