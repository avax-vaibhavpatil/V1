"""Semantic layer service for parsing and validating semantic JSON."""

from typing import Any, Optional

from app.core.exceptions import SemanticLayerError, ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SemanticService:
    """Service for managing semantic layer definitions."""

    @staticmethod
    def validate_semantic_schema(schema: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate semantic layer JSON schema.

        Args:
            schema: Semantic layer JSON

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["grain", "time_columns", "dimensions", "measures"]
        for field in required_fields:
            if field not in schema:
                return False, f"Missing required field: {field}"

        # Validate grain
        grain = schema.get("grain")
        if not isinstance(grain, str) or grain not in ["daily", "hourly", "weekly", "monthly"]:
            return False, f"Invalid grain: {grain}. Must be one of: daily, hourly, weekly, monthly"

        # Validate time_columns
        time_columns = schema.get("time_columns", [])
        if not isinstance(time_columns, list) or len(time_columns) == 0:
            return False, "time_columns must be a non-empty list"

        # Validate dimensions
        dimensions = schema.get("dimensions", [])
        if not isinstance(dimensions, list):
            return False, "dimensions must be a list"

        for dim in dimensions:
            if not isinstance(dim, dict) or "name" not in dim or "column" not in dim:
                return False, "Each dimension must have 'name' and 'column' fields"

        # Validate measures
        measures = schema.get("measures", [])
        if not isinstance(measures, list):
            return False, "measures must be a list"

        allowed_aggregations = ["SUM", "AVG", "COUNT", "MIN", "MAX", "DISTINCT_COUNT"]
        for measure in measures:
            if not isinstance(measure, dict):
                return False, "Each measure must be a dictionary"
            if "name" not in measure or "column" not in measure:
                return False, "Each measure must have 'name' and 'column' fields"
            aggregations = measure.get("aggregations", [])
            if not isinstance(aggregations, list):
                return False, "measure.aggregations must be a list"
            for agg in aggregations:
                if agg not in allowed_aggregations:
                    return False, f"Invalid aggregation: {agg}. Allowed: {allowed_aggregations}"

        return True, None

    @staticmethod
    def parse_semantic_to_ui_fields(schema: dict[str, Any]) -> dict[str, Any]:
        """
        Convert semantic JSON into UI-selectable fields.

        Args:
            schema: Validated semantic layer JSON

        Returns:
            Dictionary with UI-ready field definitions
        """
        is_valid, error = SemanticService.validate_semantic_schema(schema)
        if not is_valid:
            raise ValidationError(f"Invalid semantic schema: {error}")

        ui_fields = {
            "dimensions": [],
            "measures": [],
            "time_columns": schema.get("time_columns", []),
            "grain": schema.get("grain"),
        }

        # Parse dimensions
        for dim in schema.get("dimensions", []):
            ui_fields["dimensions"].append({
                "id": dim.get("name"),
                "name": dim.get("name"),
                "column": dim.get("column"),
                "type": dim.get("type", "string"),
                "description": dim.get("description"),
            })

        # Parse measures
        for measure in schema.get("measures", []):
            ui_fields["measures"].append({
                "id": measure.get("name"),
                "name": measure.get("name"),
                "column": measure.get("column"),
                "type": measure.get("type", "numeric"),
                "aggregations": measure.get("aggregations", []),
                "description": measure.get("description"),
                "format": measure.get("format"),  # e.g., currency, percentage
            })

        return ui_fields

    @staticmethod
    def get_validation_rules(schema: dict[str, Any]) -> dict[str, Any]:
        """
        Extract validation rules from semantic schema.

        Args:
            schema: Semantic layer JSON

        Returns:
            Dictionary of validation rules
        """
        rules = {
            "allowed_dimensions": [d.get("name") for d in schema.get("dimensions", [])],
            "allowed_measures": [m.get("name") for m in schema.get("measures", [])],
            "allowed_aggregations": {},
            "time_columns": schema.get("time_columns", []),
            "grain": schema.get("grain"),
        }

        # Map measures to their allowed aggregations
        for measure in schema.get("measures", []):
            rules["allowed_aggregations"][measure.get("name")] = measure.get(
                "aggregations", []
            )

        return rules

    @staticmethod
    def validate_field_usage(
        schema: dict[str, Any], field_name: str, field_type: str, aggregation: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a field can be used in a specific way.

        Args:
            schema: Semantic layer JSON
            field_name: Name of the field
            field_type: 'dimension' or 'measure'
            aggregation: Aggregation function if measure

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field_type == "dimension":
            dimensions = [d.get("name") for d in schema.get("dimensions", [])]
            if field_name not in dimensions:
                return False, f"Dimension '{field_name}' not found in semantic layer"
            return True, None

        elif field_type == "measure":
            measures = {m.get("name"): m for m in schema.get("measures", [])}
            if field_name not in measures:
                return False, f"Measure '{field_name}' not found in semantic layer"

            if aggregation:
                allowed_aggs = measures[field_name].get("aggregations", [])
                if aggregation not in allowed_aggs:
                    return (
                        False,
                        f"Aggregation '{aggregation}' not allowed for measure '{field_name}'. "
                        f"Allowed: {allowed_aggs}",
                    )

            return True, None

        return False, f"Invalid field_type: {field_type}. Must be 'dimension' or 'measure'"


