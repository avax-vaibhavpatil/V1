"""Database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings
from app.core.exceptions import DatabaseConnectionError
from app.core.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Create async engine
# Handle SQLite vs PostgreSQL connection parameters
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}
    engine_kwargs = {
        "url": settings.database_url,
        "echo": settings.DB_ECHO,
        "connect_args": connect_args,
    }
else:
    engine_kwargs = {
        "url": settings.database_url,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "echo": settings.DB_ECHO,
        "pool_pre_ping": True,
    }

engine = create_async_engine(**engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            # Re-raise the original exception instead of wrapping it
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}. Continuing anyway...")
        # For SQLite, this might fail if tables already exist, which is OK


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")

