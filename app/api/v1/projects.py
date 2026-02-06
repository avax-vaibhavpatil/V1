"""Project management API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseDep, RequireRead, RequireWrite
from app.core.exceptions import ValidationError
from app.services.project_service import ProjectService

router = APIRouter()


class ProjectCreate(BaseModel):
    """Project creation request."""

    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectUpdate(BaseModel):
    """Project update request."""

    name: Optional[str] = None
    description: Optional[str] = None


@router.get("")
async def list_projects(
    db: DatabaseDep,
    user: RequireRead,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
):
    """List all active projects."""
    # Don't filter by user_id by default to show all projects
    projects = await ProjectService.list_projects(
        db, skip=skip, limit=limit, user_id=user_id
    )
    # Convert SQLAlchemy models to dicts for JSON serialization
    return [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "created_by": p.created_by,
        "is_active": p.is_active,
    } for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get a project by ID."""
    try:
        project = await ProjectService.get_project_or_raise(db, project_id)
        return project
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Create a new project."""
    try:
        project = await ProjectService.create_project(
            session=db,
            name=project_data.name,
            description=project_data.description,
            created_by=user.get("id", "system"),
        )
        await db.commit()
        return project
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Update project metadata."""
    try:
        project = await ProjectService.update_project(
            session=db,
            project_id=project_id,
            name=project_data.name,
            description=project_data.description,
            updated_by=user.get("id", "system"),
        )
        await db.commit()
        return project
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Delete (soft delete) a project."""
    try:
        await ProjectService.delete_project(
            session=db,
            project_id=project_id,
            updated_by=user.get("id", "system"),
        )
        await db.commit()
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


