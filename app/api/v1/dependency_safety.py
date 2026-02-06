"""Dependency safety check API routes."""

from fastapi import APIRouter, HTTPException, status, Query

from app.core.dependencies import DatabaseDep, RequireRead, RequireWrite
from app.core.exceptions import ValidationError
from app.services.dependency_safety_service import DependencySafetyService

router = APIRouter()


@router.get("/dataset/{dataset_id}/usage")
async def check_dataset_usage(
    dataset_id: str,
    db: DatabaseDep,
    user: RequireRead,
):
    """Check if a dataset is used in dashboards or calculations."""
    try:
        usage_info = await DependencySafetyService.check_dataset_usage(db, dataset_id)
        return usage_info
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/dataset/{dataset_id}/validate-deletion")
async def validate_dataset_deletion(
    dataset_id: str,
    db: DatabaseDep,
    user: RequireWrite,
    force: bool = Query(False, description="Force deletion even if used"),
):
    """Validate if a dataset can be safely deleted."""
    try:
        can_delete, error_msg, usage_info = (
            await DependencySafetyService.validate_dataset_deletion(
                db, dataset_id, force=force
            )
        )

        return {
            "can_delete": can_delete,
            "error_message": error_msg,
            "usage_info": usage_info,
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/dataset/{dataset_id}/semantic-impact")
async def check_semantic_change_impact(
    dataset_id: str,
    new_semantic: dict,
    db: DatabaseDep,
    user: RequireRead,
):
    """Check impact of semantic layer changes."""
    try:
        impact = await DependencySafetyService.check_semantic_change_impact(
            db, dataset_id, new_semantic
        )
        return impact
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/calculation/{measure_id}/dependencies")
async def check_calculation_dependencies(
    measure_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """Check if a calculated measure is used in dashboards."""
    try:
        dependencies = await DependencySafetyService.check_calculation_dependencies(
            db, measure_id
        )
        return dependencies
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


