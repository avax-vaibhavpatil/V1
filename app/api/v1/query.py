"""Query execution API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseDep, RequireRead
from app.core.exceptions import QueryExecutionError, ValidationError, DatasetNotFoundError
from app.services.query_engine import QueryEngine
from app.services.dataset_service import DatasetService
from app.services.semantic_service import SemanticService

router = APIRouter()


class QueryRequest(BaseModel):
    """Query execution request."""

    dataset_id: str = Field(..., description="Dataset identifier")
    dimensions: list[str] = Field(..., description="List of dimension column names")
    measures: list[dict] = Field(..., description="List of measure configs")
    filters: Optional[list[dict]] = Field(None, description="Filter conditions")
    time_filter: Optional[dict] = Field(None, description="Time-based filter")
    limit: Optional[int] = Field(100, description="Maximum rows to return")


@router.post("/execute")
async def execute_query(
    request: QueryRequest,
    db: DatabaseDep,
    user: RequireRead,
):
    """Execute an analytics query."""
    try:
        # Get dataset
        dataset = await DatasetService.get_dataset_or_raise(db, request.dataset_id)

        # Get semantic schema if available
        semantic_schema = None
        if dataset.semantic_definitions:
            # Get latest semantic version
            # This is simplified - in production, get the actual schema
            semantic_schema = {}

        # Build query
        query = QueryEngine.build_query(
            dataset_table=dataset.table_name,
            schema_name=dataset.schema_name,
            dimensions=request.dimensions,
            measures=request.measures,
            filters=request.filters,
            time_filter=request.time_filter,
            limit=request.limit,
            semantic_schema=semantic_schema,
        )

        # Optimize query
        query = QueryEngine.optimize_query(query)

        # Execute query
        results = await QueryEngine.execute_query(db, query)

        return {
            "query": query,
            "results": results,
            "row_count": len(results),
        }

    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except (ValidationError, QueryExecutionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


