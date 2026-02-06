"""Changelog API routes."""

from typing import Optional
from fastapi import APIRouter, Query
from app.models.changelog import ChangeType

from app.core.dependencies import DatabaseDep, RequireRead
from app.services.changelog_service import ChangelogService

router = APIRouter()


@router.get("")
async def get_changelog(
    db: DatabaseDep,
    user: RequireRead,
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    change_type: Optional[ChangeType] = Query(None, description="Filter by change type"),
    skip: int = 0,
    limit: int = 100,
):
    """Get changelog entries."""
    entries = await ChangelogService.get_changelog(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        change_type=change_type,
        skip=skip,
        limit=limit,
    )
    return entries


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get full history for an entity."""
    history = await ChangelogService.get_entity_history(db, entity_type, entity_id)
    return history


