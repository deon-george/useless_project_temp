"""
Vision API routes for MayoMandi.

Provides endpoints for:
- Mandi rice analysis via traditional computer vision + Mayo recommendation
- Mayo vision analysis (spoon, plate, container, reference card)
- Mayo amount checker (dispensing comparison)
- Classical regression calibration mode
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..database.models import Calculation
from ..engine.mayo_engine import calculate_mayo
from ..vision.mandi_vision import process_mandi_image
from ..vision.mayo_vision import process_mayo_image, process_reverse_mayo_photo
from ..vision.calibration import (
    global_mayo_calibrator,
    DEFAULT_MAYO_DENSITY_G_PER_ML,
    REFERENCE_WIDTH_MM,
)

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/mandi")
async def analyze_mandi(
    file: UploadFile = File(...),
    spice_level: str = Form(default="medium"),
    dryness: str = Form(default="normal"),
    mayo_preference: str = Form(default="balanced"),
    db: Session = Depends(get_db),
):
    """
    Analyzes an uploaded mandi photograph using traditional OpenCV computer vision.
    Estimates rice quantity and runs the M.A.N.D.I. algorithm for recommended mayo.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        vision_result = process_mandi_image(contents)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Computer vision error: {str(e)}")

    rice_grams = vision_result["estimated_weight_grams"]

    # Calculate recommended mayonnaise
    mayo_rec = calculate_mayo(
        rice_grams=max(50.0, rice_grams),
        spice_level=spice_level,
        dryness=dryness,
        mayo_preference=mayo_preference,
    )

    # Record in history
    try:
        calc = Calculation(
            rice_grams=rice_grams,
            spice_level=spice_level,
            dryness=dryness,
            mayo_preference=mayo_preference,
            recommended_mayo=mayo_rec.recommended_mayo_grams,
            uselessness_score=mayo_rec.uselessness_score,
        )
        db.add(calc)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "success": True,
        "vision": vision_result,
        "recommendation": {
            "rice_grams": mayo_rec.rice_grams,
            "base_mayo": mayo_rec.base_mayo,
            "spice_factor": mayo_rec.spice_factor,
            "dryness_factor": mayo_rec.dryness_factor,
            "preference_factor": mayo_rec.preference_factor,
            "recommended_mayo_grams": mayo_rec.recommended_mayo_grams,
            "ratio": mayo_rec.ratio,
            "tablespoons": mayo_rec.tablespoons,
            "uselessness_score": mayo_rec.uselessness_score,
            "breakdown": mayo_rec.breakdown,
            "verdict": mayo_rec.verdict,
            "verdict_color": mayo_rec.verdict_color,
        },
    }


@router.post("/reverse")
async def analyze_reverse_mayo(file: UploadFile = File(...)):
    """
    Reverse Calculator traditional computer vision pipeline:
    Analyzes an uploaded photograph of mayonnaise (NO manual grams input).
    Uses OpenCV to segment and estimate mayo quantity, then applies
    classical NumPy least-squares regression to predict edible mandi rice.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        result = process_reverse_mayo_photo(contents)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Reverse Mayo vision error: {str(e)}")

    return result


@router.post("/mayo")

async def analyze_mayo(
    file: UploadFile = File(...),
    mode: str = Form(default="spoon"),
    spoon_type: str = Form(default="tablespoon"),
    density: float = Form(default=DEFAULT_MAYO_DENSITY_G_PER_ML),
):
    """
    Analyzes an uploaded mayonnaise photograph (spoon, plate, or container)
    using traditional computer vision.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        result = process_mayo_image(
            image_bytes=contents,
            mode=mode,
            spoon_type=spoon_type,
            density_g_per_ml=density,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Mayo vision error: {str(e)}")

    return result


@router.post("/check")
async def check_mayo_dispensing(
    file: UploadFile = File(...),
    required_mayo_grams: float = Form(...),
    mode: str = Form(default="spoon"),
    spoon_type: str = Form(default="tablespoon"),
    density: float = Form(default=DEFAULT_MAYO_DENSITY_G_PER_ML),
):
    """
    Mayo Amount Checker / Dispensing Mode.
    Compares detected mayonnaise against required amount from Mandi calculation.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        vision_result = process_mayo_image(
            image_bytes=contents,
            mode=mode,
            spoon_type=spoon_type,
            density_g_per_ml=density,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Mayo vision error: {str(e)}")

    detected_grams = vision_result["estimated_mayo_grams"]
    diff = round(detected_grams - required_mayo_grams, 1)

    if diff >= 0:
        status = "ENOUGH"
        badge = "✓ MAYO ENOUGH"
        color = "#22c55e"
        short_by = 0.0
        extra = diff
        verdict = f"✓ MAYO ENOUGH! Extra: {extra:.1f}g. Your mandi is fully secured."
    else:
        status = "NOT_ENOUGH"
        badge = "❌ NOT ENOUGH MAYO"
        color = "#ef4444"
        short_by = round(abs(diff), 1)
        extra = 0.0
        verdict = f"❌ NOT ENOUGH MAYO. Short by approximately: {short_by:.1f}g. Add more mayo!"

    return {
        "success": True,
        "status": status,
        "badge": badge,
        "color": color,
        "verdict": verdict,
        "required_mayo_grams": required_mayo_grams,
        "detected_mayo_grams": detected_grams,
        "short_by_grams": short_by,
        "extra_grams": extra,
        "vision": vision_result,
    }


@router.post("/calibrate/sample")
async def add_calibration_sample(
    file: UploadFile = File(...),
    sample_name: str = Form(...),
    actual_grams: float = Form(...),
    mode: str = Form(default="plate"),
):
    """
    Uploads a real mayonnaise sample with known weight.
    Extracts visual features using traditional CV and stores for classical regression fitting.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    vision_result = process_mayo_image(contents, mode=mode)
    mayo_area_px = vision_result["measurements"]["mayo_area_pixels"]

    # Feature value: normalized area in thousands of pixels
    feature_val = mayo_area_px / 1000.0
    global_mayo_calibrator.add_sample(sample_name, feature_val, actual_grams)

    return {
        "success": True,
        "sample_added": {
            "sample_name": sample_name,
            "actual_grams": actual_grams,
            "mayo_area_pixels": mayo_area_px,
        },
        "total_samples": len(global_mayo_calibrator.samples),
    }


@router.get("/calibrate/samples")
def get_calibration_samples():
    """Returns the list of current calibration samples and model fit status."""
    return {
        "samples": global_mayo_calibrator.samples,
        "fitted_slope": global_mayo_calibrator.fitted_slope,
        "fitted_intercept": global_mayo_calibrator.fitted_intercept,
        "r_squared": global_mayo_calibrator.r_squared,
        "default_slope": global_mayo_calibrator.default_slope,
    }


@router.post("/calibrate/fit")
def fit_calibration_model():
    """Fits classical regression model (y = m*x + c) using pure NumPy least squares."""
    return global_mayo_calibrator.fit_model()


@router.post("/calibrate/reset")
def reset_calibration():
    """Resets custom calibration samples to default empirical model."""
    global_mayo_calibrator.clear_samples()
    return {"success": True, "message": "Calibration reset to factory empirical model."}
