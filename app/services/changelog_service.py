"""Changelog service for tracking changes."""

from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.models.changelog import Changelog, ChangeType

logger = get_logger(__name__)


class ChangelogService:
    """Service for managing changelog entries."""

    @staticmethod
    async def create_changelog_entry(
        session: AsyncSession,
        change_type: ChangeType,
        entity_id: str,
        entity_type: str,
        action: str,
        changes: dict,
        created_by: str,
        impacted_assets: Optional[dict] = None,
        notes: Optional[str] = None,
    ) -> Changelog:
        """
        Create a changelog entry.

        Args:
            session: Database session
            change_type: Type of change
            entity_id: ID of changed entity
            entity_type: Type of entity
            action: Action performed (created, updated, deleted)
            changes: Dictionary of what changed
            created_by: User ID who made the change
            impacted_assets: Optional dictionary of impacted assets
            notes: Optional notes

        Returns:
            Created changelog entry
        """
        changelog = Changelog(
            change_type=change_type,
            entity_id=entity_id,
            entity_type=entity_type,
            action=action,
            changes=changes,
            impacted_assets=impacted_assets,
            created_by=created_by,
            notes=notes,
        )

        session.add(changelog)
        await session.flush()
        logger.info(f"Created changelog entry: {change_type} - {entity_type}:{entity_id}")
        return changelog

    @staticmethod
    async def get_changelog(
        session: AsyncSession,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Changelog]:
        """
        Get changelog entries.

        Args:
            session: Database session
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            change_type: Filter by change type
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of changelog entries
        """
        query = select(Changelog)

        if entity_type:
            query = query.where(Changelog.entity_type == entity_type)
        if entity_id:
            query = query.where(Changelog.entity_id == entity_id)
        if change_type:
            query = query.where(Changelog.change_type == change_type)

        result = await session.execute(
            query.order_by(Changelog.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_entity_history(
        session: AsyncSession, entity_type: str, entity_id: str
    ) -> list[Changelog]:
        """
        Get full history for an entity.

        Args:
            session: Database session
            entity_type: Type of entity
            entity_id: Entity identifier

        Returns:
            List of changelog entries for the entity
        """
        return await ChangelogService.get_changelog(
            session, entity_type=entity_type, entity_id=entity_id, limit=1000
        )


