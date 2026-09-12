from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from ..database.database import get_db
from ..database.models import Calculation
from ..schemas.calculator import CalculationResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=list[CalculationResponse])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(Calculation)
        .order_by(Calculation.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        CalculationResponse(
            rice_grams=r.rice_grams,
            base_mayo=r.rice_grams / 4.0,
            spice_factor=1.0,
            dryness_factor=1.0,
            preference_factor=1.0,
            recommended_mayo_grams=r.recommended_mayo,
            ratio=f"1 : {(r.rice_grams / r.recommended_mayo):.2f}"
            if r.recommended_mayo
            else "N/A",
            tablespoons=round(r.recommended_mayo / 14.0),
            uselessness_score=r.uselessness_score or 0,
            breakdown=[],
            verdict="",
            verdict_color="green",
        )
        for r in rows
    ]


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    rows = db.query(Calculation).all()
    total_mayo = sum(r.recommended_mayo for r in rows)
    total_calcs = len(rows)
    avg_mayo = total_mayo / total_calcs if total_calcs > 0 else 0

    # Leaderboard-style stats
    if rows:
        # Find the calculation with the highest mayo-to-rice ratio
        ratios = [(r.id, r.recommended_mayo / r.rice_grams) for r in rows]
        top_ratio_id = max(ratios, key=lambda x: x[1])[0] if ratios else None
    else:
        top_ratio_id = None

    return {
        "total_calculations": total_calcs,
        "total_imaginary_mayo_grams": round(total_mayo, 1),
        "average_mayo_per_calc": round(avg_mayo, 1),
        "top_mayo_ratio_id": top_ratio_id,
    }
