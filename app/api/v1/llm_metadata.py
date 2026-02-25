"""LLM Metadata API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.dependencies import RequireRead
from app.services.llm_metadata_service import LLMMetadataService

router = APIRouter()


class LLMMetadataResponse(BaseModel):
    """LLM metadata query response."""

    id: Optional[int] = None
    user_question: str
    tokens_used: Optional[int] = None
    created_at: Optional[str] = None


class TokenStatisticsResponse(BaseModel):
    """Token statistics response."""

    total_queries: int
    total_tokens: int
    avg_tokens: float
    min_tokens: int
    max_tokens: int


@router.get("", response_model=list[LLMMetadataResponse])
async def list_queries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    report_id: Optional[str] = Query(None, description="Filter by report ID"),
    user: RequireRead = None,
):
    """List LLM metadata queries with pagination."""
    try:
        queries = await LLMMetadataService.list_queries(
            skip=skip,
            limit=limit,
            report_id=report_id,
        )
        return queries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch queries: {str(e)}"
        )


@router.get("/stats", response_model=TokenStatisticsResponse)
async def get_token_statistics(
    report_id: Optional[str] = Query(None, description="Filter by report ID"),
    user: RequireRead = None,
):
    """Get aggregated token usage statistics."""
    try:
        stats = await LLMMetadataService.get_token_statistics(report_id=report_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )

