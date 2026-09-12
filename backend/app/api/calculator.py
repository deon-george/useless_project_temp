from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import Calculation
from ..schemas.calculator import (
    CalculationRequest,
    CalculationResponse,
    ReverseRequest,
    ReverseResponse,
    BreakdownItem,
)
from ..engine.mayo_engine import (
    calculate_mayo,
    reverse_calculate,
)

router = APIRouter(prefix="/api", tags=["calculator"])


@router.post("/calculate", response_model=CalculationResponse)
def calculate(request: CalculationRequest, db: Session = Depends(get_db)):
    result = calculate_mayo(
        rice_grams=request.rice_grams,
        spice_level=request.spice_level,
        dryness=request.dryness,
        mayo_preference=request.mayo_preference,
    )

    # Save to history
    calc = Calculation(
        rice_grams=request.rice_grams,
        spice_level=request.spice_level,
        dryness=request.dryness,
        mayo_preference=request.mayo_preference,
        recommended_mayo=result.recommended_mayo_grams,
        uselessness_score=result.uselessness_score,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)

    return result


@router.post("/reverse-calculate", response_model=ReverseResponse)
def reverse_calculate_endpoint(request: ReverseRequest):
    rice = reverse_calculate(
        mayo_grams=request.mayo_grams,
        spice_level=request.spice_level,
        dryness=request.dryness,
        mayo_preference=request.mayo_preference,
    )

    tbsp = round(request.mayo_grams / 14.0)
    ratio = f"1 : {rice / request.mayo_grams:.2f}"

    # Sustainability rating
    ratio_val = request.mayo_grams / rice if rice > 0 else 0
    if ratio_val > 0.333:
        sustainability = "CRIMINAL — You are legally required to eat more rice."
    elif ratio_val > 0.25:
        sustainability = "EXCELLENT — A healthy, mayo-conscious eater."
    elif ratio_val > 0.167:
        sustainability = "GOOD — Balance is key."
    else:
        sustainability = "MILD — You could use more mayo."

    potential_servings = max(1, round(rice / 300))

    return ReverseResponse(
        mayo_grams=request.mayo_grams,
        recommended_rice_grams=rice,
        potential_servings=potential_servings,
        mayo_sustainability=sustainability,
        ratio=ratio,
    )

