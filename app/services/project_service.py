"""Project service for workspace management."""

from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger
from app.models.project import Project

logger = get_logger(__name__)


class ProjectService:
    """Service for managing projects."""

    @staticmethod
    async def get_project(
        session: AsyncSession, project_id: int
    ) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            session: Database session
            project_id: Project identifier

        Returns:
            Project or None if not found
        """
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_project_or_raise(
        session: AsyncSession, project_id: int
    ) -> Project:
        """
        Get a project by ID or raise exception if not found.

        Args:
            session: Database session
            project_id: Project identifier

        Returns:
            Project

        Raises:
            ValidationError: If project not found
        """
        project = await ProjectService.get_project(session, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")
        return project

    @staticmethod
    async def list_projects(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> list[Project]:
        """
        List all active projects.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            user_id: Optional user ID to filter by

        Returns:
            List of projects
        """
        query = select(Project).where(Project.is_active == True)

        if user_id:
            query = query.where(Project.created_by == user_id)

        result = await session.execute(
            query.offset(skip).limit(limit).order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_project(
        session: AsyncSession,
        name: str,
        description: Optional[str] = None,
        created_by: str = "system",
    ) -> Project:
        """
        Create a new project.

        Args:
            session: Database session
            name: Project name
            description: Project description
            created_by: User ID who created

        Returns:
            Created project

        Raises:
            ValidationError: If validation fails
        """
        if not name or not name.strip():
            raise ValidationError("Project name cannot be empty")

        project = Project(
            name=name.strip(),
            description=description,
            created_by=created_by,
        )

        session.add(project)
        await session.flush()
        logger.info(f"Created project: {name}")
        return project

    @staticmethod
    async def update_project(
        session: AsyncSession,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "system",
    ) -> Project:
        """
        Update project metadata.

        Args:
            session: Database session
            project_id: Project identifier
            name: New name
            description: New description
            updated_by: User ID who updated

        Returns:
            Updated project

        Raises:
            ValidationError: If project not found
        """
        project = await ProjectService.get_project_or_raise(session, project_id)

        if name is not None:
            if not name.strip():
                raise ValidationError("Project name cannot be empty")
            project.name = name.strip()
        if description is not None:
            project.description = description

        project.updated_by = updated_by
        project.updated_at = datetime.utcnow()

        await session.flush()
        logger.info(f"Updated project: {project_id}")
        return project

    @staticmethod
    async def delete_project(
        session: AsyncSession, project_id: int, updated_by: str = "system"
    ) -> Project:
        """
        Delete (soft delete) a project.

        Args:
            session: Database session
            project_id: Project identifier
            updated_by: User ID who deleted

        Returns:
            Deleted project

        Raises:
            ValidationError: If project not found
        """
        project = await ProjectService.get_project_or_raise(session, project_id)
        project.is_active = False
        project.updated_by = updated_by
        project.updated_at = datetime.utcnow()

        await session.flush()
        logger.info(f"Deleted project: {project_id}")
        return project


