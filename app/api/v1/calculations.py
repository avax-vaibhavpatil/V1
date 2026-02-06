"""Calculation API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import RequireRead
from app.core.exceptions import ValidationError, CalculationError
from app.services.calculation_engine import CalculationEngine

router = APIRouter()


class FormulaValidationRequest(BaseModel):
    """Formula validation request."""

    formula: str = Field(..., description="Calculation formula in DSL")
    available_fields: list[str] = Field(..., description="List of available field names")


class FormulaValidationResponse(BaseModel):
    """Formula validation response."""

    is_valid: bool
    error_message: Optional[str] = None
    validation_result: Optional[dict] = None


@router.post("/validate", response_model=FormulaValidationResponse)
async def validate_formula(
    request: FormulaValidationRequest,
    user: RequireRead,
):
    """Validate a calculation formula."""
    is_valid, error, validation_result = CalculationEngine.validate_formula(
        request.formula, request.available_fields
    )

    return FormulaValidationResponse(
        is_valid=is_valid,
        error_message=error,
        validation_result=validation_result,
    )


@router.post("/parse")
async def parse_formula(
    request: dict,
    user: RequireRead,
):
    """Parse a formula into execution tree."""
    formula = request.get("formula")
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="formula is required"
        )

    try:
        parsed = CalculationEngine.parse_formula(formula)
        return parsed
    except CalculationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/check-division-by-zero")
async def check_division_by_zero(
    request: dict,
    user: RequireRead,
):
    """Check if formula could result in division by zero."""
    formula = request.get("formula")
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="formula is required"
        )

    has_risk, warning = CalculationEngine.check_division_by_zero(formula)
    return {"has_risk": has_risk, "warning": warning}


