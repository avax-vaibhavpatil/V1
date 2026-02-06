"""Dashboard API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseDep, RequireRead, RequireWrite
from app.core.exceptions import ValidationError
from app.services.dashboard_service import DashboardService
from app.services.dataset_service import DatasetService
from app.services.semantic_service import SemanticService

router = APIRouter()


class DashboardCreate(BaseModel):
    """Dashboard creation request."""

    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    layout_config: dict = Field(..., description="Grid layout configuration")
    visuals: list[dict] = Field(..., description="List of visual configurations")
    is_public: bool = Field(False, description="Whether dashboard is public")
    project_id: Optional[int] = Field(None, description="Project ID (optional)")
    dataset_id: Optional[str] = Field(None, description="Optional dataset ID for validation")


class DashboardUpdate(BaseModel):
    """Dashboard update request."""

    name: Optional[str] = None
    description: Optional[str] = None
    layout_config: Optional[dict] = None
    visuals: Optional[list[dict]] = None


@router.get("")
async def list_dashboards(
    db: DatabaseDep,
    user: RequireRead,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
):
    """List dashboards."""
    # Don't filter by user_id to show all dashboards in the project
    dashboards = await DashboardService.list_dashboards(
        db, skip=skip, limit=limit, user_id=None, project_id=project_id
    )
    return dashboards


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get a dashboard by ID."""
    dashboard = await DashboardService.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found"
        )
    return dashboard


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Create a new dashboard."""
    # Get semantic schema if dataset_id provided
    semantic_schema = None
    if dashboard_data.dataset_id:
        dataset = await DatasetService.get_dataset(db, dashboard_data.dataset_id)
        if dataset and dataset.semantic_definitions:
            # Get latest semantic version
            # This is simplified - in production, get the actual schema
            semantic_schema = {}

    try:
        dashboard = await DashboardService.create_dashboard(
            session=db,
            name=dashboard_data.name,
            layout_config=dashboard_data.layout_config,
            visuals=dashboard_data.visuals,
            description=dashboard_data.description,
            is_public=dashboard_data.is_public,
            project_id=dashboard_data.project_id,
            created_by=user.get("id", "system"),
            semantic_schema=semantic_schema,
        )
        await db.commit()
        return dashboard
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.patch("/{dashboard_id}")
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Update dashboard."""
    try:
        dashboard = await DashboardService.update_dashboard(
            session=db,
            dashboard_id=dashboard_id,
            name=dashboard_data.name,
            description=dashboard_data.description,
            layout_config=dashboard_data.layout_config,
            visuals=dashboard_data.visuals,
            updated_by=user.get("id", "system"),
        )
        await db.commit()
        return dashboard
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Delete (soft delete) a dashboard."""
    dashboard = await DashboardService.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found"
        )
    
    # Soft delete
    dashboard.is_active = False
    await db.commit()

