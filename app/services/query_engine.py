"""Query engine for generating and executing SQL queries."""

from typing import Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import QueryExecutionError, ValidationError
from app.core.logging_config import get_logger
from app.services.semantic_service import SemanticService

logger = get_logger(__name__)


class QueryEngine:
    """Engine for generating and executing analytics queries."""

    @staticmethod
    def build_query(
        dataset_table: str,
        schema_name: Optional[str],
        dimensions: list[str],
        measures: list[dict[str, Any]],
        filters: Optional[list[dict[str, Any]]] = None,
        time_filter: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        semantic_schema: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Build SQL query from visualization configuration.

        Args:
            dataset_table: Table name
            schema_name: Schema name (optional)
            dimensions: List of dimension column names
            measures: List of measure configs with column and aggregation
            filters: List of filter conditions
            time_filter: Time-based filter
            limit: Maximum rows to return
            semantic_schema: Semantic layer schema for validation

        Returns:
            SQL query string

        Raises:
            ValidationError: If query configuration is invalid
        """
        # Validate against semantic schema if provided
        if semantic_schema:
            for dim in dimensions:
                is_valid, error = SemanticService.validate_field_usage(
                    semantic_schema, dim, "dimension"
                )
                if not is_valid:
                    raise ValidationError(f"Dimension validation failed: {error}")

            for measure in measures:
                measure_name = measure.get("name")
                aggregation = measure.get("aggregation")
                is_valid, error = SemanticService.validate_field_usage(
                    semantic_schema, measure_name, "measure", aggregation
                )
                if not is_valid:
                    raise ValidationError(f"Measure validation failed: {error}")

        # Build SELECT clause
        select_parts = []
        select_parts.extend(dimensions)

        for measure in measures:
            column = measure.get("column")
            aggregation = measure.get("aggregation", "SUM")
            alias = measure.get("alias", f"{aggregation}_{column}")
            select_parts.append(f"{aggregation}({column}) AS {alias}")

        select_clause = ", ".join(select_parts)

        # Build FROM clause
        if schema_name:
            from_clause = f'"{schema_name}"."{dataset_table}"'
        else:
            from_clause = f'"{dataset_table}"'

        # Build WHERE clause
        where_conditions = []
        if filters:
            for filter_config in filters:
                column = filter_config.get("column")
                operator = filter_config.get("operator", "=")
                value = filter_config.get("value")

                if operator == "=":
                    where_conditions.append(f"{column} = '{value}'")
                elif operator == "!=":
                    where_conditions.append(f"{column} != '{value}'")
                elif operator == "IN":
                    values = ",".join([f"'{v}'" for v in value])
                    where_conditions.append(f"{column} IN ({values})")
                elif operator == ">":
                    where_conditions.append(f"{column} > {value}")
                elif operator == "<":
                    where_conditions.append(f"{column} < {value}")
                elif operator == ">=":
                    where_conditions.append(f"{column} >= {value}")
                elif operator == "<=":
                    where_conditions.append(f"{column} <= {value}")

        if time_filter:
            time_column = time_filter.get("column")
            start_date = time_filter.get("start_date")
            end_date = time_filter.get("end_date")

            if start_date and end_date:
                where_conditions.append(
                    f"{time_column} >= '{start_date}' AND {time_column} <= '{end_date}'"
                )
            elif start_date:
                where_conditions.append(f"{time_column} >= '{start_date}'")
            elif end_date:
                where_conditions.append(f"{time_column} <= '{end_date}'")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Build GROUP BY clause
        group_by_clause = ""
        if dimensions:
            group_by_clause = "GROUP BY " + ", ".join(dimensions)

        # Build ORDER BY clause (optional)
        order_by_clause = ""
        if measures:
            # Default order by first measure descending
            first_measure = measures[0]
            alias = first_measure.get("alias", f"{first_measure.get('aggregation')}_{first_measure.get('column')}")
            order_by_clause = f"ORDER BY {alias} DESC"

        # Build LIMIT clause
        limit_clause = ""
        if limit:
            limit_clause = f"LIMIT {limit}"

        # Assemble query
        query = f"""
        SELECT {select_clause}
        FROM {from_clause}
        {where_clause}
        {group_by_clause}
        {order_by_clause}
        {limit_clause}
        """.strip()

        return query

    @staticmethod
    async def execute_query(
        session: AsyncSession, query: str, timeout: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results.

        Args:
            session: Database session
            query: SQL query string
            timeout: Query timeout in seconds

        Returns:
            List of result rows as dictionaries

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            result = await session.execute(text(query))
            rows = result.fetchall()

            # Convert to list of dicts
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}", exc_info=True)
            raise QueryExecutionError(f"Query execution failed: {str(e)}", query=query)

    @staticmethod
    def optimize_query(query: str) -> str:
        """
        Optimize query for performance.

        Args:
            query: SQL query string

        Returns:
            Optimized query string
        """
        # Basic optimizations
        # In production, add more sophisticated optimizations
        query = query.replace("  ", " ")  # Remove double spaces
        query = "\n".join(line.strip() for line in query.split("\n") if line.strip())
        return query


