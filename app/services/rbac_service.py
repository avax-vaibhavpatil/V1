"""Role-Based Access Control service."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.core.logging_config import get_logger
from app.models.user import User, Role, Permission

logger = get_logger(__name__)


class RBACService:
    """Service for managing roles and permissions."""

    # Default roles and their permissions
    DEFAULT_ROLES = {
        "viewer": ["read"],
        "editor": ["read", "write"],
        "analyst": ["read", "write", "create_dashboard"],
        "admin": ["read", "write", "create_dashboard", "admin"],
    }

    @staticmethod
    async def get_user_permissions(
        session: AsyncSession, user_id: str
    ) -> list[str]:
        """
        Get all permissions for a user.

        Args:
            session: Database session
            user_id: User identifier

        Returns:
            List of permission names
        """
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            return []

        permissions = set()
        for role in user.roles:
            if role.is_active:
                for perm in role.permissions:
                    permissions.add(perm.name)

        return list(permissions)

    @staticmethod
    async def check_permission(
        session: AsyncSession, user_id: str, permission: str
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            session: Database session
            user_id: User identifier
            permission: Permission name to check

        Returns:
            True if user has permission, False otherwise
        """
        permissions = await RBACService.get_user_permissions(session, user_id)
        return permission in permissions or "admin" in permissions

    @staticmethod
    async def require_permission(
        session: AsyncSession, user_id: str, permission: str
    ) -> None:
        """
        Require a permission or raise exception.

        Args:
            session: Database session
            user_id: User identifier
            permission: Required permission

        Raises:
            PermissionDeniedError: If user lacks permission
        """
        has_permission = await RBACService.check_permission(session, user_id, permission)
        if not has_permission:
            raise PermissionDeniedError(
                f"User {user_id} does not have permission: {permission}"
            )

    @staticmethod
    async def get_user_role(
        session: AsyncSession, user_id: str
    ) -> Optional[str]:
        """
        Get primary role name for a user.

        Args:
            session: Database session
            user_id: User identifier

        Returns:
            Role name or None
        """
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user or not user.roles:
            return None

        # Return first active role
        for role in user.roles:
            if role.is_active:
                return role.name

        return None

    @staticmethod
    async def can_access_resource(
        session: AsyncSession,
        user_id: str,
        resource_type: str,
        action: str,
        resource_owner: Optional[str] = None,
    ) -> bool:
        """
        Check if user can perform action on resource.

        Args:
            session: Database session
            user_id: User identifier
            resource_type: Type of resource (dataset, dashboard, etc.)
            action: Action to perform (read, write, delete)
            resource_owner: Optional owner of resource

        Returns:
            True if access allowed
        """
        # Admin can do anything
        if await RBACService.check_permission(session, user_id, "admin"):
            return True

        # Owner can do anything to their resource
        if resource_owner and user_id == resource_owner:
            return True

        # Check specific permission
        permission_name = f"{resource_type}:{action}"
        return await RBACService.check_permission(session, user_id, permission_name)


