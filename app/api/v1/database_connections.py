"""Database connection API routes."""

from turtle import left
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseDep, RequireRead, RequireAdmin
from app.core.exceptions import ValidationError, DatabaseConnectionError
from app.services.database_connection_service import DatabaseConnectionService

router = APIRouter()


class DatabaseConnectionCreate(BaseModel):
    """Database connection creation request."""

    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Connection name")
    db_type: str = Field(..., description="Database type (postgresql, mysql)")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    schema_name: Optional[str] = Field(None, description="Schema name")
    is_read_only: bool = Field(True, description="Read-only connection")


class ConnectionTestRequest(BaseModel):
    """Connection test request."""

    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str


@router.post("/test")
async def test_connection(
    request: ConnectionTestRequest,
    user: RequireAdmin,
):
    """Test a database connection."""
    is_connected, error = await DatabaseConnectionService.test_connection(
        request.db_type,
        request.host,
        request.port,
        request.database,
        request.username,
        request.password,
    )

    return {
        "is_connected": is_connected,
        "error_message": error,
    }


@router.get("/project/{project_id}")
async def list_connections(
    project_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """List database connections for a project."""
    connections = await DatabaseConnectionService.list_connections(db, project_id)
    return connections


@router.get("/{connection_id}")
async def get_connection(
    connection_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get a database connection by ID."""
    connection = await DatabaseConnectionService.get_connection(db, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )
    return connection


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: DatabaseConnectionCreate,
    db: DatabaseDep,
    user: RequireAdmin,
):
    """Create a new database connection (admin only)."""
    try:
        connection = await DatabaseConnectionService.create_connection(
            session=db,
            project_id=connection_data.project_id,
            name=connection_data.name,
            db_type=connection_data.db_type,
            host=connection_data.host,
            port=connection_data.port,
            database=connection_data.database,
            username=connection_data.username,
            password=connection_data.password,
            schema_name=connection_data.schema_name,
            is_read_only=connection_data.is_read_only,
            created_by=user.get("id", "system"),
        )
        await db.commit()
        return connection
    except (ValidationError, DatabaseConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/{connection_id}/datasets")
async def list_connection_datasets(
    connection_id: int,
    db: DatabaseDep,
    user: RequireRead,
    schema_name: Optional[str] = None,
):
    """List available tables/views from a database connection."""
    try:
        datasets = await DatabaseConnectionService.list_datasets(
            db, connection_id, schema_name
        )
        return datasets
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )