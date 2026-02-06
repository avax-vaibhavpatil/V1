"""Dataset API routes."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseDep, RequireRead, RequireWrite
from app.core.exceptions import DatasetNotFoundError
from app.services.dataset_service import DatasetService
from app.services.file_upload_service import FileUploadService

router = APIRouter()


class DatasetCreate(BaseModel):
    """Dataset creation request."""

    id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Dataset name")
    table_name: str = Field(..., description="Database table name")
    grain: str = Field(..., description="Data grain (daily, hourly, weekly, monthly)")
    schema_name: Optional[str] = Field(None, description="Database schema name")
    description: Optional[str] = Field(None, description="Dataset description")
    project_id: Optional[int] = Field(None, description="Project ID (optional)")
    source_type: str = Field("sql", description="Source type: sql or uploaded_file")
    uploaded_file_id: Optional[int] = Field(None, description="Uploaded file ID if source is file")


class DatasetUpdate(BaseModel):
    """Dataset update request."""

    name: Optional[str] = None
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Dataset response model."""

    id: str
    name: str
    description: Optional[str]
    table_name: str
    schema_name: Optional[str]
    grain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    db: DatabaseDep,
    user: RequireRead,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
):
    """List all active datasets."""
    datasets = await DatasetService.list_datasets(
        db, skip=skip, limit=limit, project_id=project_id
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get a dataset by ID."""
    try:
        dataset = await DatasetService.get_dataset_or_raise(db, dataset_id)
        return dataset
    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Create a new dataset."""
    try:
        dataset = await DatasetService.create_dataset(
            session=db,
            dataset_id=dataset_data.id,
            name=dataset_data.name,
            table_name=dataset_data.table_name,
            grain=dataset_data.grain,
            schema_name=dataset_data.schema_name,
            description=dataset_data.description,
            project_id=dataset_data.project_id,
            source_type=dataset_data.source_type,
            uploaded_file_id=dataset_data.uploaded_file_id,
            created_by=user.get("id", "system"),
        )
        await db.commit()
        return dataset
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    dataset_data: DatasetUpdate,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Update dataset metadata."""
    try:
        dataset = await DatasetService.update_dataset(
            session=db,
            dataset_id=dataset_id,
            name=dataset_data.name,
            description=dataset_data.description,
            updated_by=user.get("id", "system"),
        )
        await db.commit()
        return dataset
    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: DatabaseDep,
    user: RequireWrite,
):
    """Deprecate (soft delete) a dataset."""
    try:
        await DatasetService.deprecate_dataset(
            session=db,
            dataset_id=dataset_id,
            updated_by=user.get("id", "system"),
        )
        await db.commit()
    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    db: DatabaseDep,
    user: RequireRead,
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Preview dataset data.
    For uploaded files, reads directly from CSV.
    For SQL datasets, queries the database table.
    """
    try:
        dataset = await DatasetService.get_dataset_or_raise(db, dataset_id)
        
        # Check if this is an uploaded file dataset
        if dataset.source_type == "uploaded_file" and dataset.uploaded_file_id:
            # Get the uploaded file info
            uploaded_file = await FileUploadService.get_uploaded_file(
                db, dataset.uploaded_file_id
            )
            
            if not uploaded_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found"
                )
            
            # Read CSV file directly
            file_path = Path(uploaded_file.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {uploaded_file.file_path}"
                )
            
            results: list[dict[str, Any]] = []
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        if i >= limit:
                            break
                        results.append(dict(row))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to read file: {str(e)}"
                )
            
            return {
                "results": results,
                "row_count": len(results),
                "source": "file",
                "file_path": str(file_path),
            }
        else:
            # For SQL datasets, return empty for now (would need actual table)
            return {
                "results": [],
                "row_count": 0,
                "source": "sql",
                "message": "SQL table preview not implemented",
            }
            
    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

