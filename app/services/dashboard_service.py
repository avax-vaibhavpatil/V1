"""Dashboard composition service."""

from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger
from app.models.dashboard import Dashboard, DashboardVisual
from app.services.visualization_service import VisualizationService

logger = get_logger(__name__)


class DashboardService:
    """Service for managing dashboards."""

    @staticmethod
    async def get_dashboard(
        session: AsyncSession, dashboard_id: int
    ) -> Optional[Dashboard]:
        """
        Get a dashboard by ID.

        Args:
            session: Database session
            dashboard_id: Dashboard identifier

        Returns:
            Dashboard or None if not found
        """
        result = await session.execute(
            select(Dashboard).where(Dashboard.id == dashboard_id, Dashboard.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_dashboards(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> list[Dashboard]:
        """
        List dashboards.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            user_id: Optional user ID to filter by
            project_id: Optional project ID to filter by

        Returns:
            List of dashboards
        """
        query = select(Dashboard).where(Dashboard.is_active == True)

        if user_id:
            query = query.where(Dashboard.created_by == user_id)

        if project_id is not None:
            query = query.where(Dashboard.project_id == project_id)

        result = await session.execute(
            query.offset(skip).limit(limit).order_by(Dashboard.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_dashboard(
        session: AsyncSession,
        name: str,
        layout_config: dict,
        visuals: list[dict],
        description: Optional[str] = None,
        is_public: bool = False,
        project_id: Optional[int] = None,
        created_by: str = "system",
        semantic_schema: Optional[dict] = None,
    ) -> Dashboard:
        """
        Create a new dashboard.

        Args:
            session: Database session
            name: Dashboard name
            layout_config: Grid layout configuration
            visuals: List of visual configurations
            description: Dashboard description
            is_public: Whether dashboard is public
            created_by: User ID who created
            semantic_schema: Optional semantic schema for validation

        Returns:
            Created dashboard

        Raises:
            ValidationError: If validation fails
        """
        # Validate layout config
        if "columns" not in layout_config or "rows" not in layout_config:
            raise ValidationError("layout_config must have 'columns' and 'rows' fields")

        # Validate and create visuals
        dashboard_visuals = []
        for idx, visual_config in enumerate(visuals):
            visual_type = visual_config.get("visual_type")
            config = visual_config.get("config", {})

            is_valid, error = VisualizationService.validate_visual_config(
                visual_type, config, semantic_schema
            )
            if not is_valid:
                raise ValidationError(f"Visual {idx} validation failed: {error}")

            position = visual_config.get("position", {})
            if "x" not in position or "y" not in position:
                raise ValidationError(f"Visual {idx} must have position with 'x' and 'y' fields")

            dashboard_visual = DashboardVisual(
                visual_type=visual_type,
                visual_config=config,
                position=position,
                order=visual_config.get("order", idx),
            )
            dashboard_visuals.append(dashboard_visual)

        dashboard = Dashboard(
            name=name,
            description=description,
            layout_config=layout_config,
            is_public=is_public,
            project_id=project_id,
            created_by=created_by,
        )
        dashboard.visuals = dashboard_visuals

        session.add(dashboard)
        await session.flush()
        logger.info(f"Created dashboard: {name}")
        return dashboard

    @staticmethod
    async def update_dashboard(
        session: AsyncSession,
        dashboard_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        layout_config: Optional[dict] = None,
        visuals: Optional[list[dict]] = None,
        updated_by: str = "system",
        semantic_schema: Optional[dict] = None,
    ) -> Dashboard:
        """
        Update dashboard.

        Args:
            session: Database session
            dashboard_id: Dashboard identifier
            name: New name
            description: New description
            layout_config: New layout config
            visuals: New visuals list
            updated_by: User ID who updated
            semantic_schema: Optional semantic schema for validation

        Returns:
            Updated dashboard

        Raises:
            ValidationError: If validation fails
        """
        dashboard = await DashboardService.get_dashboard(session, dashboard_id)
        if not dashboard:
            raise ValidationError(f"Dashboard {dashboard_id} not found")

        if name is not None:
            dashboard.name = name
        if description is not None:
            dashboard.description = description
        if layout_config is not None:
            dashboard.layout_config = layout_config

        if visuals is not None:
            # Remove existing visuals
            for visual in dashboard.visuals:
                await session.delete(visual)

            # Add new visuals
            dashboard_visuals = []
            for idx, visual_config in enumerate(visuals):
                visual_type = visual_config.get("visual_type")
                config = visual_config.get("config", {})

                is_valid, error = VisualizationService.validate_visual_config(
                    visual_type, config, semantic_schema
                )
                if not is_valid:
                    raise ValidationError(f"Visual {idx} validation failed: {error}")

                position = visual_config.get("position", {})
                dashboard_visual = DashboardVisual(
                    dashboard_id=dashboard_id,
                    visual_type=visual_type,
                    visual_config=config,
                    position=position,
                    order=visual_config.get("order", idx),
                )
                dashboard_visuals.append(dashboard_visual)

            dashboard.visuals = dashboard_visuals

        dashboard.updated_by = updated_by
        dashboard.updated_at = datetime.utcnow()

        await session.flush()
        logger.info(f"Updated dashboard: {dashboard_id}")
        return dashboard

