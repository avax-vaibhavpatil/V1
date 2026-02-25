"""Service for querying LLM metadata from database."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.services.chat_service import AnalyticsSessionLocal

logger = get_logger(__name__)


class LLMMetadataService:
    """Service for fetching LLM metadata queries and token statistics."""

    @staticmethod
    async def list_queries(
        skip: int = 0,
        limit: int = 50,
        report_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List LLM metadata queries with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            report_id: Optional report ID filter

        Returns:
            List of query metadata dictionaries
        """
        try:
            async with AnalyticsSessionLocal() as session:
                # Build query - PostgreSQL tables typically have id and created_at
                # If they don't exist, we'll handle the error gracefully
                query = """
                    SELECT 
                        user_question,
                        tokens_used,
                        created_at
                    FROM metadata.llm_metadata
                    WHERE 1=1
                """
                params = {"skip": skip, "limit": limit}

                if report_id:
                    query += " AND report_id = :report_id"
                    params["report_id"] = report_id

                query += " ORDER BY created_at DESC NULLS LAST LIMIT :limit OFFSET :skip"

                result = await session.execute(text(query), params)
                rows = result.fetchall()

                # Convert to list of dicts
                columns = result.keys()
                queries = [dict(zip(columns, row)) for row in rows]

                # Convert datetime to ISO format string and add id if not present
                for idx, query_data in enumerate(queries):
                    if query_data.get("created_at"):
                        if isinstance(query_data["created_at"], datetime):
                            query_data["created_at"] = query_data["created_at"].isoformat()
                    # Add a synthetic id if not present (use index)
                    if "id" not in query_data:
                        query_data["id"] = idx + skip + 1
                    # Ensure created_at exists (use empty string if not)
                    if "created_at" not in query_data:
                        query_data["created_at"] = ""

                return queries

        except Exception as e:
            logger.error(f"Failed to list LLM metadata queries: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_token_statistics(
        report_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated token usage statistics.

        Args:
            report_id: Optional report ID filter

        Returns:
            Dictionary with token statistics
        """
        try:
            async with AnalyticsSessionLocal() as session:
                # Build query
                query = """
                    SELECT 
                        COUNT(*) as total_queries,
                        COALESCE(SUM(tokens_used), 0) as total_tokens,
                        COALESCE(AVG(tokens_used), 0) as avg_tokens,
                        COALESCE(MIN(tokens_used), 0) as min_tokens,
                        COALESCE(MAX(tokens_used), 0) as max_tokens
                    FROM metadata.llm_metadata
                    WHERE 1=1
                """
                params = {}

                if report_id:
                    query += " AND report_id = :report_id"
                    params["report_id"] = report_id

                result = await session.execute(text(query), params)
                row = result.fetchone()

                if row:
                    columns = result.keys()
                    stats = dict(zip(columns, row))
                    # Convert numeric types
                    stats["total_queries"] = int(stats["total_queries"]) if stats["total_queries"] else 0
                    stats["total_tokens"] = int(stats["total_tokens"]) if stats["total_tokens"] else 0
                    stats["avg_tokens"] = float(stats["avg_tokens"]) if stats["avg_tokens"] else 0.0
                    stats["min_tokens"] = int(stats["min_tokens"]) if stats["min_tokens"] else 0
                    stats["max_tokens"] = int(stats["max_tokens"]) if stats["max_tokens"] else 0
                    return stats

                return {
                    "total_queries": 0,
                    "total_tokens": 0,
                    "avg_tokens": 0.0,
                    "min_tokens": 0,
                    "max_tokens": 0,
                }

        except Exception as e:
            logger.error(f"Failed to get token statistics: {e}", exc_info=True)
            raise

