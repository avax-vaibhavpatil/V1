"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Database dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    Get current authenticated user.

    TODO: Implement proper JWT authentication
    For now, returns a mock user for development.
    """
    # Mock user for development - always return user
    return {
        "id": "user-1",
        "email": "dev@example.com",
        "role": "admin",
        "permissions": ["read", "write", "admin"],
    }


async def require_permission(
    permission: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency to require a specific permission.

    Args:
        permission: Required permission
        user: Current user from get_current_user

    Returns:
        User dict if permission granted

    Raises:
        HTTPException: If permission denied
    """
    user_permissions = user.get("permissions", [])
    if permission not in user_permissions and "admin" not in user_permissions:
        logger.warning(
            f"Permission denied for user {user.get('id')}: required {permission}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required",
        )
    return user


# Common permission dependencies - simplified
RequireRead = Annotated[dict, Depends(get_current_user)]
RequireWrite = Annotated[dict, Depends(get_current_user)]
RequireAdmin = Annotated[dict, Depends(get_current_user)]


