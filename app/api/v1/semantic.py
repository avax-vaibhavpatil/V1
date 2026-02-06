"""Semantic layer API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import RequireRead
from app.core.exceptions import ValidationError
from app.services.semantic_service import SemanticService
from app.services.dataset_service import DatasetService

router = APIRouter()


class SemanticSchemaRequest(BaseModel):
    """Semantic schema validation request."""

    schema_json: dict = Field(..., description="Semantic layer JSON schema")
    
    @property
    def schema(self) -> dict:
        """Get schema data."""
        return self.schema_json


class SemanticSchemaResponse(BaseModel):
    """Semantic schema validation response."""

    is_valid: bool
    error_message: Optional[str] = None
    ui_fields: Optional[dict] = None
    validation_rules: Optional[dict] = None


@router.post("/validate", response_model=SemanticSchemaResponse)
async def validate_semantic_schema(
    request: SemanticSchemaRequest,
    user: RequireRead,
):
    """Validate a semantic layer JSON schema."""
    is_valid, error = SemanticService.validate_semantic_schema(request.schema_json)

    response = SemanticSchemaResponse(is_valid=is_valid, error_message=error)

    if is_valid:
        response.ui_fields = SemanticService.parse_semantic_to_ui_fields(request.schema_json)
        response.validation_rules = SemanticService.get_validation_rules(request.schema_json)

    return response


@router.post("/parse", response_model=dict)
async def parse_semantic_schema(
    request: SemanticSchemaRequest,
    user: RequireRead,
):
    """Parse semantic schema into UI fields."""
    try:
        ui_fields = SemanticService.parse_semantic_to_ui_fields(request.schema_json)
        return ui_fields
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/validate-field")
async def validate_field_usage(
    request: dict,
    user: RequireRead,
):
    """Validate if a field can be used in a specific way."""
    schema = request.get("schema")
    field_name = request.get("field_name")
    field_type = request.get("field_type")
    aggregation = request.get("aggregation")

    if not all([schema, field_name, field_type]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: schema, field_name, field_type",
        )

    is_valid, error = SemanticService.validate_field_usage(
        schema, field_name, field_type, aggregation
    )

    return {"is_valid": is_valid, "error_message": error}

