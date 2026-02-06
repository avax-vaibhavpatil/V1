"""Dependency safety checks to prevent breaking changes."""

from typing import Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger
from app.models.dataset import Dataset
from app.models.dashboard import Dashboard, DashboardVisual
from app.models.calculation import CalculatedMeasure

logger = get_logger(__name__)


class DependencySafetyService:
    """Service for checking dependencies before destructive operations."""

    @staticmethod
    async def check_dataset_usage(
        session: AsyncSession, dataset_id: str
    ) -> dict[str, Any]:
        """
        Check if a dataset is used in dashboards or calculations.

        Args:
            session: Database session
            dataset_id: Dataset identifier

        Returns:
            Dictionary with usage information
        """
        dataset = await session.get(Dataset, dataset_id)
        if not dataset:
            raise ValidationError(f"Dataset {dataset_id} not found")

        # Check dashboards using this dataset
        # This is simplified - in production, parse visual_config to find dataset references
        dashboard_count = await session.execute(
            select(func.count(Dashboard.id)).where(
                Dashboard.is_active == True,
                # TODO: Parse visual_config JSON to check for dataset_id
                # For now, we'll check all active dashboards
            )
        )
        dashboard_count = dashboard_count.scalar() or 0

        # Check calculated measures
        measure_count = await session.execute(
            select(func.count(CalculatedMeasure.id)).where(
                CalculatedMeasure.dataset_id == dataset_id,
                CalculatedMeasure.is_active == True,
            )
        )
        measure_count = measure_count.scalar() or 0

        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "used_in_dashboards": dashboard_count,
            "used_in_calculations": measure_count,
            "can_delete": dashboard_count == 0 and measure_count == 0,
            "warnings": [],
        }

    @staticmethod
    async def validate_dataset_deletion(
        session: AsyncSession, dataset_id: str, force: bool = False
    ) -> tuple[bool, Optional[str], dict[str, Any]]:
        """
        Validate if a dataset can be safely deleted.

        Args:
            session: Database session
            dataset_id: Dataset identifier
            force: If True, allow deletion even if used

        Returns:
            Tuple of (can_delete, error_message, usage_info)
        """
        usage_info = await DependencySafetyService.check_dataset_usage(
            session, dataset_id
        )

        if usage_info["can_delete"] or force:
            return True, None, usage_info

        error_msg = (
            f"Cannot delete dataset '{usage_info['dataset_name']}'. "
            f"It is used in {usage_info['used_in_dashboards']} dashboard(s) "
            f"and {usage_info['used_in_calculations']} calculation(s). "
            f"Use force=true to delete anyway."
        )

        return False, error_msg, usage_info

    @staticmethod
    async def check_semantic_change_impact(
        session: AsyncSession, dataset_id: str, new_semantic: dict
    ) -> dict[str, Any]:
        """
        Check impact of semantic layer changes.

        Args:
            session: Database session
            dataset_id: Dataset identifier
            new_semantic: New semantic layer definition

        Returns:
            Dictionary with impact analysis
        """
        dataset = await session.get(Dataset, dataset_id)
        if not dataset:
            raise ValidationError(f"Dataset {dataset_id} not found")

        # Get current semantic definition
        # This is simplified - in production, get actual current semantic
        current_semantic = {}  # TODO: Get from SemanticVersion

        # Compare dimensions
        current_dims = {d.get("name") for d in current_semantic.get("dimensions", [])}
        new_dims = {d.get("name") for d in new_semantic.get("dimensions", [])}
        removed_dims = current_dims - new_dims
        added_dims = new_dims - current_dims

        # Compare measures
        current_measures = {
            m.get("name") for m in current_semantic.get("measures", [])
        }
        new_measures = {m.get("name") for m in new_semantic.get("measures", [])}
        removed_measures = current_measures - new_measures
        added_measures = new_measures - current_measures

        warnings = []
        if removed_dims:
            warnings.append(
                f"Removed dimensions: {', '.join(removed_dims)}. "
                f"This may break dashboards using these dimensions."
            )
        if removed_measures:
            warnings.append(
                f"Removed measures: {', '.join(removed_measures)}. "
                f"This may break dashboards using these measures."
            )

        return {
            "dataset_id": dataset_id,
            "removed_dimensions": list(removed_dims),
            "added_dimensions": list(added_dims),
            "removed_measures": list(removed_measures),
            "added_measures": list(added_measures),
            "warnings": warnings,
            "has_breaking_changes": len(removed_dims) > 0 or len(removed_measures) > 0,
        }

    @staticmethod
    async def check_calculation_dependencies(
        session: AsyncSession, measure_id: int
    ) -> dict[str, Any]:
        """
        Check if a calculated measure is used in dashboards.

        Args:
            session: Database session
            measure_id: Calculated measure identifier

        Returns:
            Dictionary with usage information
        """
        measure = await session.get(CalculatedMeasure, measure_id)
        if not measure:
            raise ValidationError(f"Calculated measure {measure_id} not found")

        # Check dashboards using this measure
        # This is simplified - in production, parse visual_config to find measure references
        dashboard_count = 0  # TODO: Implement actual check

        return {
            "measure_id": measure_id,
            "measure_name": measure.name,
            "used_in_dashboards": dashboard_count,
            "can_delete": dashboard_count == 0,
        }

