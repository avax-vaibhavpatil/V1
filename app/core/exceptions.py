"""Custom exception classes for the application."""

from typing import Any, Optional


class AnalyticsStudioException(Exception):
    """Base exception for Analytics Studio."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AnalyticsStudioException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class DatasetNotFoundError(AnalyticsStudioException):
    """Raised when a dataset is not found."""

    def __init__(self, dataset_id: str, **kwargs):
        super().__init__(
            f"Dataset '{dataset_id}' not found",
            error_code="DATASET_NOT_FOUND",
            **kwargs,
        )
        self.dataset_id = dataset_id


class SemanticLayerError(AnalyticsStudioException):
    """Raised when semantic layer operations fail."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="SEMANTIC_LAYER_ERROR", **kwargs)


class CalculationError(AnalyticsStudioException):
    """Raised when calculation execution fails."""

    def __init__(self, message: str, formula: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CALCULATION_ERROR", **kwargs)
        self.formula = formula


class QueryExecutionError(AnalyticsStudioException):
    """Raised when query execution fails."""

    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="QUERY_EXECUTION_ERROR", **kwargs)
        self.query = query


class PermissionDeniedError(AnalyticsStudioException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Permission denied", **kwargs):
        super().__init__(message, error_code="PERMISSION_DENIED", **kwargs)


class DatabaseConnectionError(AnalyticsStudioException):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, error_code="DATABASE_CONNECTION_ERROR", **kwargs)


