"""Application configuration management."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Analytics Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
    ]

    # Database - Main application database (SQLite for now, can be changed to PostgreSQL)
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5430  # Changed from 5432 to 5430 to match PostgreSQL port
    DB_NAME: str = "analytics_studio"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Analytics Database (analytics_llm) - For all reports (Sales Analytics, Stock Inventory, Gateway Analytics)
    ANALYTICS_DB_HOST: str = "localhost"
    ANALYTICS_DB_PORT: int = 5430
    ANALYTICS_DB_NAME: str = "analytics_llm"
    ANALYTICS_DB_USER: str = "postgres"
    ANALYTICS_DB_PASSWORD: str = "root"
    ANALYTICS_DB_POOL_SIZE: int = 5
    ANALYTICS_DB_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis (for caching)
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600  # 1 hour

    # Query Limits
    MAX_QUERY_ROWS: int = 100000
    QUERY_TIMEOUT_SECONDS: int = 300

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def analytics_database_url(self) -> str:
        """Construct analytics database URL from components."""
        return (
            f"postgresql+asyncpg://{self.ANALYTICS_DB_USER}:{self.ANALYTICS_DB_PASSWORD}"
            f"@{self.ANALYTICS_DB_HOST}:{self.ANALYTICS_DB_PORT}/{self.ANALYTICS_DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


