"""Visualization configuration service."""

from typing import Any, Optional

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VisualizationService:
    """Service for managing visualization configurations."""

    VALID_VISUAL_TYPES = ["kpi", "line", "bar", "column", "stacked_bar", "table", "pie"]
    VALID_SORT_ORDERS = ["asc", "desc"]

    @staticmethod
    def validate_visual_config(
        visual_type: str, config: dict[str, Any], semantic_schema: Optional[dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate visualization configuration.

        Args:
            visual_type: Type of visual (kpi, line, bar, etc.)
            config: Visual configuration dictionary
            semantic_schema: Optional semantic schema for validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if visual_type not in VisualizationService.VALID_VISUAL_TYPES:
            return False, f"Invalid visual type: {visual_type}. Valid types: {VisualizationService.VALID_VISUAL_TYPES}"

        # Validate required fields based on visual type
        if visual_type == "kpi":
            if "measure" not in config:
                return False, "KPI visual requires 'measure' field"
        else:
            if "dimensions" not in config or not config.get("dimensions"):
                return False, f"{visual_type} visual requires at least one dimension"
            if "measures" not in config or not config.get("measures"):
                return False, f"{visual_type} visual requires at least one measure"

        # Validate measures structure
        if "measures" in config:
            for measure in config["measures"]:
                if not isinstance(measure, dict):
                    return False, "Each measure must be a dictionary"
                if "name" not in measure:
                    return False, "Each measure must have 'name' field"
                if "aggregation" not in measure:
                    return False, "Each measure must have 'aggregation' field"

        # Validate sorting if provided
        if "sorting" in config:
            sorting = config["sorting"]
            if not isinstance(sorting, dict):
                return False, "sorting must be a dictionary"
            if "field" not in sorting or "order" not in sorting:
                return False, "sorting must have 'field' and 'order' fields"
            if sorting["order"] not in VisualizationService.VALID_SORT_ORDERS:
                return False, f"sorting.order must be one of: {VisualizationService.VALID_SORT_ORDERS}"

        # Validate time_grain if provided
        if "time_grain" in config:
            valid_grains = ["daily", "hourly", "weekly", "monthly", "yearly"]
            if config["time_grain"] not in valid_grains:
                return False, f"time_grain must be one of: {valid_grains}"

        # Validate against semantic schema if provided
        if semantic_schema:
            from app.services.semantic_service import SemanticService

            if "dimensions" in config:
                for dim in config["dimensions"]:
                    is_valid, error = SemanticService.validate_field_usage(
                        semantic_schema, dim, "dimension"
                    )
                    if not is_valid:
                        return False, f"Dimension validation: {error}"

            measures = config.get("measures", [])
            if not measures and "measure" in config:
                measures = [config["measure"]]

            for measure in measures:
                measure_name = measure.get("name") if isinstance(measure, dict) else measure
                aggregation = measure.get("aggregation") if isinstance(measure, dict) else None
                is_valid, error = SemanticService.validate_field_usage(
                    semantic_schema, measure_name, "measure", aggregation
                )
                if not is_valid:
                    return False, f"Measure validation: {error}"

        return True, None

    @staticmethod
    def create_kpi_config(
        measure: dict[str, Any],
        filters: Optional[list[dict[str, Any]]] = None,
        time_filter: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create KPI card configuration.

        Args:
            measure: Measure configuration
            filters: Optional filters
            time_filter: Optional time filter

        Returns:
            KPI configuration dictionary
        """
        return {
            "visual_type": "kpi",
            "measure": measure,
            "filters": filters or [],
            "time_filter": time_filter,
        }

    @staticmethod
    def create_chart_config(
        visual_type: str,
        dimensions: list[str],
        measures: list[dict[str, Any]],
        filters: Optional[list[dict[str, Any]]] = None,
        time_filter: Optional[dict[str, Any]] = None,
        sorting: Optional[dict[str, Any]] = None,
        time_grain: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create chart configuration.

        Args:
            visual_type: Type of chart (line, bar, column, etc.)
            dimensions: List of dimension names
            measures: List of measure configurations
            filters: Optional filters
            time_filter: Optional time filter
            sorting: Optional sorting configuration
            time_grain: Optional time grain

        Returns:
            Chart configuration dictionary
        """
        return {
            "visual_type": visual_type,
            "dimensions": dimensions,
            "measures": measures,
            "filters": filters or [],
            "time_filter": time_filter,
            "sorting": sorting,
            "time_grain": time_grain,
        }

    @staticmethod
    def create_table_config(
        dimensions: list[str],
        measures: list[dict[str, Any]],
        filters: Optional[list[dict[str, Any]]] = None,
        time_filter: Optional[dict[str, Any]] = None,
        sorting: Optional[dict[str, Any]] = None,
        limit: Optional[int] = 100,
    ) -> dict[str, Any]:
        """
        Create table configuration.

        Args:
            dimensions: List of dimension names
            measures: List of measure configurations
            filters: Optional filters
            time_filter: Optional time filter
            sorting: Optional sorting configuration
            limit: Maximum rows to display

        Returns:
            Table configuration dictionary
        """
        return {
            "visual_type": "table",
            "dimensions": dimensions,
            "measures": measures,
            "filters": filters or [],
            "time_filter": time_filter,
            "sorting": sorting,
            "limit": limit,
        }


