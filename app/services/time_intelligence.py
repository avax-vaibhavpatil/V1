"""Time intelligence engine for period comparisons."""

from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TimeComparison(str, Enum):
    """Supported time comparison types."""

    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"
    ROLLING_7_DAYS = "rolling_7_days"
    ROLLING_30_DAYS = "rolling_30_days"
    ROLLING_90_DAYS = "rolling_90_days"
    YEAR_TO_DATE = "year_to_date"
    MONTH_TO_DATE = "month_to_date"


class TimeIntelligenceEngine:
    """Engine for time-based analytics comparisons."""

    @staticmethod
    def calculate_time_range(
        comparison_type: TimeComparison,
        base_start: datetime,
        base_end: datetime,
        grain: str = "daily",
    ) -> tuple[datetime, datetime]:
        """
        Calculate time range for comparison.

        Args:
            comparison_type: Type of comparison
            base_start: Base period start date
            base_end: Base period end date
            grain: Data grain (daily, weekly, monthly)

        Returns:
            Tuple of (comparison_start, comparison_end)

        Raises:
            ValidationError: If comparison type is invalid
        """
        period_days = (base_end - base_start).days

        if comparison_type == TimeComparison.PREVIOUS_PERIOD:
            # Same length period before base_start
            comparison_end = base_start - timedelta(days=1)
            comparison_start = comparison_end - timedelta(days=period_days)
            return comparison_start, comparison_end

        elif comparison_type == TimeComparison.SAME_PERIOD_LAST_YEAR:
            # Same dates, previous year
            comparison_start = base_start.replace(year=base_start.year - 1)
            comparison_end = base_end.replace(year=base_end.year - 1)
            return comparison_start, comparison_end

        elif comparison_type == TimeComparison.ROLLING_7_DAYS:
            # Last 7 days ending at base_end
            comparison_start = base_end - timedelta(days=7)
            return comparison_start, base_end

        elif comparison_type == TimeComparison.ROLLING_30_DAYS:
            # Last 30 days ending at base_end
            comparison_start = base_end - timedelta(days=30)
            return comparison_start, base_end

        elif comparison_type == TimeComparison.ROLLING_90_DAYS:
            # Last 90 days ending at base_end
            comparison_start = base_end - timedelta(days=90)
            return comparison_start, base_end

        elif comparison_type == TimeComparison.YEAR_TO_DATE:
            # Start of year to base_end
            comparison_start = base_end.replace(month=1, day=1)
            return comparison_start, base_end

        elif comparison_type == TimeComparison.MONTH_TO_DATE:
            # Start of month to base_end
            comparison_start = base_end.replace(day=1)
            return comparison_start, base_end

        else:
            raise ValidationError(f"Unsupported comparison type: {comparison_type}")

    @staticmethod
    def generate_comparison_query(
        base_query: str,
        time_column: str,
        comparison_type: TimeComparison,
        base_start: datetime,
        base_end: datetime,
        grain: str = "daily",
    ) -> str:
        """
        Generate SQL query for time comparison.

        Args:
            base_query: Base SQL query
            time_column: Time column name
            comparison_type: Type of comparison
            base_start: Base period start
            base_end: Base period end
            grain: Data grain

        Returns:
            SQL query for comparison period
        """
        comp_start, comp_end = TimeIntelligenceEngine.calculate_time_range(
            comparison_type, base_start, base_end, grain
        )

        # Replace time filter in base query
        # This is simplified - in production, use proper SQL parsing
        old_filter = f"{time_column} >= '{base_start}' AND {time_column} <= '{base_end}'"
        new_filter = f"{time_column} >= '{comp_start}' AND {time_column} <= '{comp_end}'"

        comparison_query = base_query.replace(old_filter, new_filter)
        return comparison_query

    @staticmethod
    def calculate_percentage_change(
        current_value: float, previous_value: float
    ) -> Optional[float]:
        """
        Calculate percentage change between two values.

        Args:
            current_value: Current period value
            previous_value: Previous period value

        Returns:
            Percentage change, or None if previous_value is 0
        """
        if previous_value == 0:
            return None
        return ((current_value - previous_value) / previous_value) * 100

    @staticmethod
    def validate_time_range(
        start_date: datetime, end_date: datetime, grain: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate time range against grain.

        Args:
            start_date: Start date
            end_date: End date
            grain: Data grain

        Returns:
            Tuple of (is_valid, error_message)
        """
        if start_date > end_date:
            return False, "Start date must be before end date"

        days_diff = (end_date - start_date).days

        if grain == "daily" and days_diff < 0:
            return False, "Invalid date range for daily grain"
        elif grain == "hourly" and days_diff > 365:
            return False, "Date range too large for hourly grain (max 365 days)"
        elif grain == "monthly" and days_diff < 30:
            return False, "Date range too small for monthly grain (min 30 days)"

        return True, None


