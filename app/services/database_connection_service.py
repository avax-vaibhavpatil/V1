"""Database connection service for SQL database management."""

import asyncio
from typing import Optional, Any
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool

from app.core.exceptions import ValidationError, DatabaseConnectionError
from app.core.logging_config import get_logger
from app.models.project import DatabaseConnection, Project

logger = get_logger(__name__)


class DatabaseConnectionService:
    """Service for managing SQL database connections."""

    SUPPORTED_DB_TYPES = ["postgresql", "mysql"]

    @staticmethod
    def _build_connection_url(
        db_type: str, host: str, port: int, database: str, username: str, password: str
    ) -> str:
        """
        Build database connection URL.

        Args:
            db_type: Database type (postgresql, mysql)
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password

        Returns:
            Connection URL string
        """
        if db_type == "postgresql":
            return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValidationError(f"Unsupported database type: {db_type}")

    @staticmethod
    async def test_connection(
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        timeout: int = 5,
    ) -> tuple[bool, Optional[str]]:
        """
        Test database connection.

        Args:
            db_type: Database type
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password
            timeout: Connection timeout in seconds

        Returns:
            Tuple of (is_connected, error_message)
        """
        try:
            url = DatabaseConnectionService._build_connection_url(
                db_type, host, port, database, username, password
            )

            engine = create_async_engine(
                url, poolclass=NullPool, connect_args={"timeout": timeout}
            )

            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            await engine.dispose()
            return True, None

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            return False, str(e)

    @staticmethod
    async def get_connection(
        session: AsyncSession, connection_id: int
    ) -> Optional[DatabaseConnection]:
        """
        Get a database connection by ID.

        Args:
            session: Database session
            connection_id: Connection identifier

        Returns:
            DatabaseConnection or None
        """
        result = await session.execute(
            select(DatabaseConnection).where(
                DatabaseConnection.id == connection_id,
                DatabaseConnection.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_connections(
        session: AsyncSession, project_id: int
    ) -> list[DatabaseConnection]:
        """
        List database connections for a project.

        Args:
            session: Database session
            project_id: Project identifier

        Returns:
            List of database connections
        """
        result = await session.execute(
            select(DatabaseConnection)
            .where(
                DatabaseConnection.project_id == project_id,
                DatabaseConnection.is_active == True,
            )
            .order_by(DatabaseConnection.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_connection(
        session: AsyncSession,
        project_id: int,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        schema_name: Optional[str] = None,
        is_read_only: bool = True,
        created_by: str = "system",
    ) -> DatabaseConnection:
        """
        Create a new database connection.

        Args:
            session: Database session
            project_id: Project identifier
            name: Connection name
            db_type: Database type (postgresql, mysql)
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password (will be encrypted)
            schema_name: Optional schema name
            is_read_only: Whether connection is read-only
            created_by: User ID who created

        Returns:
            Created database connection

        Raises:
            ValidationError: If validation fails
        """
        # Validate project exists
        project = await session.get(Project, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        # Validate db_type
        if db_type not in DatabaseConnectionService.SUPPORTED_DB_TYPES:
            raise ValidationError(
                f"Unsupported database type: {db_type}. Supported: {DatabaseConnectionService.SUPPORTED_DB_TYPES}"
            )

        # Test connection
        is_connected, error = await DatabaseConnectionService.test_connection(
            db_type, host, port, database, username, password
        )
        if not is_connected:
            raise DatabaseConnectionError(f"Connection test failed: {error}")

        # TODO: Encrypt password before storing
        # For now, store as-is (NOT PRODUCTION READY)
        password_encrypted = password  # Placeholder

        connection = DatabaseConnection(
            project_id=project_id,
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password_encrypted=password_encrypted,
            schema_name=schema_name,
            is_read_only=is_read_only,
            created_by=created_by,
        )

        session.add(connection)
        await session.flush()
        logger.info(f"Created database connection: {name} for project {project_id}")
        return connection

    @staticmethod
    async def list_datasets(
        session: AsyncSession,
        connection_id: int,
        schema_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        List available tables/views from a database connection.

        Args:
            session: Database session
            connection_id: Connection identifier
            schema_name: Optional schema name to filter

        Returns:
            List of dataset metadata dictionaries
        """
        connection = await DatabaseConnectionService.get_connection(
            session, connection_id
        )
        if not connection:
            raise ValidationError(f"Connection {connection_id} not found")

        # Get password (decrypt in production)
        password = connection.password_encrypted  # TODO: Decrypt

        url = DatabaseConnectionService._build_connection_url(
            connection.db_type,
            connection.host,
            connection.port,
            connection.database,
            connection.username,
            password,
        )

        engine = create_async_engine(url, poolclass=NullPool)

        try:
            async with engine.begin() as conn:
                if connection.db_type == "postgresql":
                    if schema_name:
                        query = text(
                            """
                            SELECT table_name, table_type
                            FROM information_schema.tables
                            WHERE table_schema = :schema
                            ORDER BY table_name
                            """
                        )
                        result = await conn.execute(query, {"schema": schema_name})
                    else:
                        query = text(
                            """
                            SELECT table_name, table_type, table_schema
                            FROM information_schema.tables
                            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                            ORDER BY table_schema, table_name
                            """
                        )
                        result = await conn.execute(query)

                elif connection.db_type == "mysql":
                    if schema_name:
                        query = text(
                            """
                            SELECT table_name, table_type
                            FROM information_schema.tables
                            WHERE table_schema = :schema
                            ORDER BY table_name
                            """
                        )
                        result = await conn.execute(query, {"schema": schema_name})
                    else:
                        query = text(
                            """
                            SELECT table_name, table_type, table_schema
                            FROM information_schema.tables
                            WHERE table_schema = DATABASE()
                            ORDER BY table_name
                            """
                        )
                        result = await conn.execute(query)

                rows = result.fetchall()
                datasets = []
                for row in rows:
                    datasets.append(
                        {
                            "table_name": row[0],
                            "table_type": row[1],
                            "schema_name": row[2] if len(row) > 2 else schema_name,
                        }
                    )

                return datasets

        finally:
            await engine.dispose()


