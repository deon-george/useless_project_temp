"""
Traditional Computer Vision Mayonnaise Analysis Pipeline for MayoMandi.

Supports:
1. Spoon Mode: Detects spoon bowl and calculates mayo coverage ratio & volume.
2. Plate Mode: Detects mayonnaise dollops on a plate separate from rice.
3. Container Mode: Detects dip container/ramekin and estimates mayo portion.
4. Reference Card Mode: Direct physical area calibration using 85.6 mm card.

Uses traditional OpenCV & NumPy techniques ONLY (no deep learning/neural nets).
"""

import base64
from typing import Dict, Any, Optional, Tuple, List
import cv2
import numpy as np

from .calibration import (
    DEFAULT_MAYO_DENSITY_G_PER_ML,
    SPOON_VOLUMES_ML,
    REFERENCE_WIDTH_MM,
    detect_reference_card,
    global_mayo_calibrator,
)

# Mayonnaise color parameters (creamy off-white, light yellowish-white)
DEFAULT_MAYO_COLOR_CONFIG = {
    # HSV: Hue: yellow/cream band, Low Saturation (not grey, not saturated), High Value (bright)
    "hsv_lower": np.array([12, 10, 160], dtype=np.uint8),
    "hsv_upper": np.array([50, 95, 255], dtype=np.uint8),
    # LAB: High Lightness, Neutral to very slightly warm
    "lab_lower": np.array([170, 120, 128], dtype=np.uint8),
    "lab_upper": np.array([255, 138, 165], dtype=np.uint8),
    # Texture max variance threshold: mayo is very smooth
    "max_laplacian_variance": 450.0,
}


def detect_spoon(image: np.ndarray) -> Dict[str, Any]:
    """
    Detects a spoon and its bowl region using traditional edge detection,
    contour analysis, and ellipse fitting.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Edge detection & thresholding
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = (h * w) * 0.04
    max_area = (h * w) * 0.85

    best_bowl_cnt = None
    best_ellipse = None
    best_score = 0.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # Spoons have an elliptical head / bowl
        if len(hull) >= 5:
            ellipse = cv2.fitEllipse(hull)
            (center, (d1, d2), angle) = ellipse
            major = max(d1, d2)
            minor = min(d1, d2)
            if minor > 10:
                aspect = major / minor
                # Spoon bowls typically have an aspect ratio of 1.2 to 2.4
                if 1.15 <= aspect <= 2.8 and solidity > 0.60:
                    score = area * solidity / aspect
                    if score > best_score:
                        best_score = score
                        best_bowl_cnt = hull
                        best_ellipse = ellipse

    mask = np.zeros((h, w), dtype=np.uint8)
    if best_bowl_cnt is not None:
        cv2.drawContours(mask, [best_bowl_cnt], -1, 255, -1)
        bowl_area = float(cv2.contourArea(best_bowl_cnt))
        detected = True
    else:
        # Fallback to an elliptical center region
        detected = False
        ew, eh = int(w * 0.45), int(h * 0.45)
        cv2.ellipse(mask, (w // 2, h // 2), (ew // 2, eh // 2), 0, 0, 360, 255, -1)
        bowl_area = float(np.pi * (ew / 2) * (eh / 2))

    return {
        "detected": detected,
        "mask": mask,
        "contour": best_bowl_cnt,
        "ellipse": best_ellipse,
        "bowl_area_px": bowl_area,
    }


def detect_container(image: np.ndarray) -> Dict[str, Any]:
    """
    Detects a sauce ramekin / dip container / cup using contour circularity/convexity.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 35, 110)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = (h * w) * 0.05
    max_area = (h * w) * 0.85

    best_cnt = None
    best_score = 0.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        peri = cv2.arcLength(cnt, True)
        if peri == 0:
            continue
        circularity = 4 * np.pi * (area / (peri * peri))
        hull = cv2.convexHull(cnt)
        solidity = area / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

        if circularity > 0.45 and solidity > 0.70:
            score = area * circularity * solidity
            if score > best_score:
                best_score = score
                best_cnt = hull

    mask = np.zeros((h, w), dtype=np.uint8)
    if best_cnt is not None:
        cv2.drawContours(mask, [best_cnt], -1, 255, -1)
        area_px = float(cv2.contourArea(best_cnt))
        detected = True
    else:
        detected = False
        ew, eh = int(w * 0.5), int(h * 0.5)
        cv2.ellipse(mask, (w // 2, h // 2), (ew // 2, eh // 2), 0, 0, 360, 255, -1)
        area_px = float(np.pi * (ew / 2) * (eh / 2))

    return {
        "detected": detected,
        "mask": mask,
        "contour": best_cnt,
        "container_area_px": area_px,
    }


def detect_mayo(
    image: np.ndarray,
    region_mask: Optional[np.ndarray] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, List[np.ndarray]]:
    """
    Traditional mayonnaise segmentation using HSV, LAB, brightness,
    and texture analysis within a candidate region.
    """
    cfg = config or DEFAULT_MAYO_COLOR_CONFIG
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # 1. Color thresholding in HSV & LAB
    hsv_mask = cv2.inRange(hsv, cfg["hsv_lower"], cfg["hsv_upper"])
    lab_mask = cv2.inRange(lab, cfg["lab_lower"], cfg["lab_upper"])

    # High lightness white/cream (bright mayo)
    # Saturation must be low (< 80) and Lightness high (> 175)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    lightness = lab[:, :, 0]

    mayo_color = cv2.bitwise_or(hsv_mask, lab_mask)

    # General bright creamy mask
    creamy_bright = cv2.bitwise_and(
        cv2.inRange(lightness, 165, 255),
        cv2.inRange(sat, 5, 85),
    )
    creamy_bright = cv2.bitwise_and(creamy_bright, cv2.inRange(val, 160, 255))

    initial_mask = cv2.bitwise_or(mayo_color, creamy_bright)

    # 2. Restrict to candidate region (spoon bowl, container, or plate)
    if region_mask is not None:
        initial_mask = cv2.bitwise_and(initial_mask, initial_mask, mask=region_mask)

    # 3. Morphological Cleanup
    filtered = cv2.medianBlur(initial_mask, 5)

    # Opening to eliminate small specks/reflections
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, open_kernel)

    # Closing to consolidate smooth mayo dollop
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, close_kernel, iterations=2)

    # 4. Connected components filtering
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    clean_mask = np.zeros_like(closed)
    min_area = 100

    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            clean_mask[labels == i] = 255

    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    cv2.drawContours(clean_mask, valid_contours, -1, 255, -1)

    return clean_mask, valid_contours


def estimate_mayo_spoon(
    mayo_area_px: float,
    bowl_area_px: float,
    spoon_type: str = "tablespoon",
    density_g_per_ml: float = DEFAULT_MAYO_DENSITY_G_PER_ML,
    is_spoon_detected: bool = True,
) -> Dict[str, Any]:
    """
    Estimates mayonnaise volume and grams from a spoon photo.
    """
    capacity_ml = SPOON_VOLUMES_ML.get(spoon_type.lower(), 15.0)

    coverage_ratio = mayo_area_px / bowl_area_px if bowl_area_px > 0 else 0.0
    coverage_ratio = min(1.35, coverage_ratio)  # Account for heaped mounds up to 135%

    # Mound factor: a dollop on a spoon has 3D height
    # Coverage ~0.8 usually implies full bowl ~15 mL
    mound_factor = 1.15 if coverage_ratio > 0.65 else 1.0

    estimated_ml = capacity_ml * coverage_ratio * mound_factor
    estimated_ml = max(1.0, estimated_ml) if coverage_ratio > 0.05 else 0.0
    estimated_grams = estimated_ml * density_g_per_ml

    # Uncertainty calculation
    margin_pct = 0.12 if is_spoon_detected else 0.20
    confidence = 85 if is_spoon_detected else 60

    estimated_grams = round(estimated_grams, 1)
    min_grams = round(max(0.0, estimated_grams * (1.0 - margin_pct)), 1)
    max_grams = round(estimated_grams * (1.0 + margin_pct), 1)

    return {
        "estimated_mayo_grams": estimated_grams,
        "minimum_estimated_weight": min_grams,
        "maximum_estimated_weight": max_grams,
        "estimated_mayo_ml": round(estimated_ml, 1),
        "spoon_capacity_ml": capacity_ml,
        "spoon_type": spoon_type,
        "coverage_ratio": round(coverage_ratio, 3),
        "confidence": confidence,
        "uncertainty_range_label": f"{min_grams}–{max_grams} g",
        "notes": [
            f"Mode: Spoon ({spoon_type}, {capacity_ml} mL capacity).",
            f"Coverage ratio: {coverage_ratio * 100:.1f}%.",
            f"Configured mayo density: {density_g_per_ml:.2f} g/mL.",
        ],
    }


def estimate_mayo_area_metric(
    mayo_area_px: float,
    pixels_per_mm: Optional[float],
    density_g_per_ml: float = DEFAULT_MAYO_DENSITY_G_PER_ML,
    mode_name: str = "plate",
) -> Dict[str, Any]:
    """
    Estimates mayo grams using calibrated metric area (from reference card) or empirical fallback.
    """
    if mayo_area_px < 150:
        return {
            "estimated_mayo_grams": 0.0,
            "minimum_estimated_weight": 0.0,
            "maximum_estimated_weight": 0.0,
            "estimated_mayo_ml": 0.0,
            "confidence": 0,
            "uncertainty_range_label": "0 g",
            "notes": ["No significant mayonnaise detected."],
        }

    if pixels_per_mm and pixels_per_mm > 0:
        # mm^2 = px / (px/mm)^2 -> cm^2
        area_cm2 = (mayo_area_px / (pixels_per_mm ** 2)) / 100.0
        # Mayo dollop height: viscous emulsion forms a dome with h ~ 0.5 + 0.1 * sqrt(area)
        radius = np.sqrt(area_cm2 / np.pi)
        avg_height_cm = 0.45 + (0.10 * radius)
        volume_cm3 = area_cm2 * avg_height_cm
        raw_grams = volume_cm3 * density_g_per_ml
        confidence = 84
        margin_pct = 0.14
        notes = [
            f"Calibrated physical mayo area: {area_cm2:.1f} cm².",
            f"Calculated using 85.6mm reference card.",
        ]
    else:
        # Fallback empirical estimation based on pixel area
        # A typical dip portion (~30-50g) occupies ~40,000 px in standard resolution
        pred_grams, conf = global_mayo_calibrator.predict(mayo_area_px / 1000.0)
        raw_grams = max(5.0, pred_grams)
        confidence = int(conf * 70)
        margin_pct = 0.22
        notes = ["Estimated using fallback empirical model (no reference card detected)."]

    estimated_grams = round(raw_grams, 1)
    min_grams = round(max(0.0, estimated_grams * (1.0 - margin_pct)), 1)
    max_grams = round(estimated_grams * (1.0 + margin_pct), 1)
    estimated_ml = round(estimated_grams / density_g_per_ml, 1)

    return {
        "estimated_mayo_grams": estimated_grams,
        "minimum_estimated_weight": min_grams,
        "maximum_estimated_weight": max_grams,
        "estimated_mayo_ml": estimated_ml,
        "confidence": confidence,
        "uncertainty_range_label": f"{min_grams}–{max_grams} g",
        "notes": notes,
    }


def generate_mayo_overlay(
    image: np.ndarray,
    region_cnt: Optional[np.ndarray],
    mayo_mask: np.ndarray,
    valid_contours: List[np.ndarray],
    result_info: Dict[str, Any],
    card_info: Dict[str, Any],
) -> str:
    """
    Renders visual debug overlays on the mayo image:
    - Spoon / Container outline in cyan
    - Mayo mask in cream / bright red outline
    - Reference card in magenta (if detected)
    - Measurement banner
    Returns base64 encoded JPEG.
    """
    overlay = image.copy()
    h, w = image.shape[:2]

    # Draw Spoon/Container boundary
    if region_cnt is not None:
        cv2.drawContours(overlay, [region_cnt], -1, (255, 200, 0), 2)

    # Mayo mask overlay (creamy white with red contour)
    mayo_color = np.zeros_like(image)
    mayo_color[mayo_mask > 0] = (240, 245, 255)
    cv2.addWeighted(mayo_color, 0.40, overlay, 0.60, 0, overlay)

    if valid_contours:
        cv2.drawContours(overlay, valid_contours, -1, (0, 0, 255), 2)

    # Reference card if present
    if card_info.get("detected") and card_info.get("ordered_pts"):
        pts = np.array(card_info["ordered_pts"], dtype=np.int32)
        cv2.polylines(overlay, [pts], True, (255, 0, 255), 3)

    # Header banner
    banner_h = 75
    banner = np.zeros((banner_h, w, 3), dtype=np.uint8)
    banner[:] = (25, 25, 25)

    grams = result_info.get("estimated_mayo_grams", 0.0)
    rng = result_info.get("uncertainty_range_label", "")
    ml = result_info.get("estimated_mayo_ml", 0.0)
    conf = result_info.get("confidence", 0)

    cv2.putText(
        banner,
        f"Estimated Mayo: ~{grams} g ({ml} mL) [{rng}]",
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 230, 180),
        2,
    )
    cv2.putText(
        banner,
        f"Confidence: {conf}% | Mode: {result_info.get('notes', [''])[0]}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (200, 200, 200),
        1,
    )

    combined = np.vstack([banner, overlay])
    success, buffer = cv2.imencode(".jpg", combined, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    return base64.b64encode(buffer).decode("utf-8")


def process_mayo_image(
    image_bytes: bytes,
    mode: str = "spoon",
    spoon_type: str = "tablespoon",
    density_g_per_ml: float = DEFAULT_MAYO_DENSITY_G_PER_ML,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for Mayo Vision analysis.
    Executes traditional CV pipeline for spoon, plate, container, or card modes.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image file or unsupported image format.")

    max_dim = 1200
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # Check for reference card
    card_info = detect_reference_card(image)
    px_per_mm = card_info.get("pixels_per_mm")

    region_cnt = None
    region_mask = None
    region_area_px = float(h * w)

    if mode == "spoon":
        spoon_info = detect_spoon(image)
        region_mask = spoon_info["mask"]
        region_cnt = spoon_info["contour"]
        region_area_px = spoon_info["bowl_area_px"]
        is_region_detected = spoon_info["detected"]
    elif mode == "container":
        cont_info = detect_container(image)
        region_mask = cont_info["mask"]
        region_cnt = cont_info["contour"]
        region_area_px = cont_info["container_area_px"]
        is_region_detected = cont_info["detected"]
    else:  # plate or card
        is_region_detected = True
        region_mask = None

    # Detect mayonnaise within region
    mayo_mask, valid_contours = detect_mayo(image, region_mask, config)
    mayo_area_px = float(cv2.countNonZero(mayo_mask))

    # Estimation calculation
    if mode == "spoon":
        result_info = estimate_mayo_spoon(
            mayo_area_px,
            region_area_px,
            spoon_type=spoon_type,
            density_g_per_ml=density_g_per_ml,
            is_spoon_detected=is_region_detected,
        )
    else:
        result_info = estimate_mayo_area_metric(
            mayo_area_px,
            pixels_per_mm=px_per_mm,
            density_g_per_ml=density_g_per_ml,
            mode_name=mode,
        )

    # Render overlay
    overlay_b64 = generate_mayo_overlay(
        image, region_cnt, mayo_mask, valid_contours, result_info, card_info
    )

    return {
        "success": True,
        "mode": mode,
        "estimated_mayo_grams": result_info["estimated_mayo_grams"],
        "minimum_estimated_weight": result_info["minimum_estimated_weight"],
        "maximum_estimated_weight": result_info["maximum_estimated_weight"],
        "estimated_mayo_ml": result_info["estimated_mayo_ml"],
        "confidence": result_info["confidence"],
        "uncertainty_range_label": result_info["uncertainty_range_label"],
        "notes": result_info["notes"],
        "measurements": {
            "mayo_area_pixels": mayo_area_px,
            "region_area_pixels": region_area_px,
            "coverage_ratio": result_info.get("coverage_ratio"),
            "reference_card_detected": card_info["detected"],
            "pixels_per_mm": round(px_per_mm, 2) if px_per_mm else None,
        },
        "overlay_base64": overlay_b64,
    }


def estimate_mayo_weight(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Empirical & classical calibrated estimator for mayonnaise weight from visual features.
    Uses calibration relationships from data/mayo_calibration.csv via NumPy least squares.

    Returns:
    - estimated_mayo_grams
    - minimum_mayo_grams
    - maximum_mayo_grams
    - confidence
    - uncertainty_range_label
    """
    from .regression import mayo_feature_model

    mayo_area_px = features.get("mayo_area_pixels", 0.0)
    physical_area_cm2 = features.get("physical_mayo_area_cm2")
    has_ref = features.get("reference_detected", False)

    if mayo_area_px < 300:
        return {
            "estimated_mayo_grams": 0.0,
            "minimum_mayo_grams": 0.0,
            "maximum_mayo_grams": 0.0,
            "confidence": 0,
            "uncertainty_range_label": "0 g",
            "notes": ["No significant mayonnaise detected in photograph."],
        }

    # Use classical calibration model
    if has_ref and physical_area_cm2 and physical_area_cm2 > 1.0:
        raw_grams = mayo_feature_model.predict_from_physical(physical_area_cm2)
        confidence = 84
        margin_pct = 0.10  # e.g. 150g -> 135-165g
        notes = ["Calibrated using MayoMandi reference object (85.6 mm)."]
    else:
        raw_grams = mayo_feature_model.predict_from_pixels(mayo_area_px)
        confidence = 72
        margin_pct = 0.14
        notes = ["Estimated using plate-relative pixel calibration (no reference card)."]

    raw_grams = max(10.0, raw_grams)
    estimated_grams = round(raw_grams)
    min_grams = round(estimated_grams * (1.0 - margin_pct))
    max_grams = round(estimated_grams * (1.0 + margin_pct))

    return {
        "estimated_mayo_grams": float(estimated_grams),
        "minimum_mayo_grams": float(min_grams),
        "maximum_mayo_grams": float(max_grams),
        "confidence": int(confidence),
        "uncertainty_range_label": f"{int(min_grams)}–{int(max_grams)} g",
        "notes": notes,
    }


def process_reverse_mayo_photo(image_bytes: bytes) -> Dict[str, Any]:
    """
    Complete Reverse Calculator traditional computer vision pipeline:
    1. Preprocessing
    2. Reference/plate detection
    3. Mayonnaise segmentation inside plate/reference region
    4. Morphological cleanup & contour detection
    5. Mayo area measurement & physical calibration
    6. Mayo quantity estimation (estimate_mayo_weight)
    7. NumPy least-squares linear regression (predicted mandi rice)
    """
    from .regression import rice_mayo_model

    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image file or unsupported image format.")

    max_dim = 1200
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # 1. Reference card detection
    card_info = detect_reference_card(image)
    px_per_mm = card_info.get("pixels_per_mm")

    # 2. Plate / container detection
    plate_info = detect_container(image)
    if not plate_info["detected"]:
        # Fallback to spoon bowl or circular region
        spoon_candidate = detect_spoon(image)
        if spoon_candidate["detected"]:
            plate_info = {
                "detected": True,
                "mask": spoon_candidate["mask"],
                "contour": spoon_candidate["contour"],
                "container_area_px": spoon_candidate["bowl_area_px"],
            }
        else:
            # Elliptical center region fallback
            pw, ph = int(w * 0.70), int(h * 0.70)
            p_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(p_mask, (w // 2, h // 2), (pw // 2, ph // 2), 0, 0, 360, 255, -1)
            plate_info = {
                "detected": False,
                "mask": p_mask,
                "contour": None,
                "container_area_px": float(np.pi * (pw / 2) * (ph / 2)),
            }

    # 3. Mayo segmentation strictly inside plate/reference boundary
    mayo_mask, valid_contours = detect_mayo(image, region_mask=plate_info["mask"])
    mayo_area_px = float(cv2.countNonZero(mayo_mask))

    # 4. Geometric & physical measurements
    physical_area_cm2 = None
    if px_per_mm and px_per_mm > 0:
        physical_area_cm2 = (mayo_area_px / (px_per_mm ** 2)) / 100.0

    bbox_w, bbox_h = 0, 0
    perimeter_px = 0.0
    if valid_contours:
        all_pts = np.vstack(valid_contours)
        _, _, bbox_w, bbox_h = cv2.boundingRect(all_pts)
        perimeter_px = float(sum(cv2.arcLength(c, True) for c in valid_contours))

    features = {
        "mayo_area_pixels": mayo_area_px,
        "physical_mayo_area_cm2": physical_area_cm2,
        "mayo_perimeter_px": perimeter_px,
        "mayo_bbox_width": bbox_w,
        "mayo_bbox_height": bbox_h,
        "mayo_plate_ratio": mayo_area_px / plate_info["container_area_px"] if plate_info["container_area_px"] > 0 else 0,
        "reference_detected": card_info["detected"],
        "pixels_per_mm": px_per_mm,
    }

    # 5. Mayo quantity estimation
    weight_info = estimate_mayo_weight(features)
    estimated_mayo_grams = weight_info["estimated_mayo_grams"]

    # 6. NumPy least-squares regression -> predicted rice quantity
    predicted_rice = rice_mayo_model.predict(estimated_mayo_grams)

    # 7. Render OpenCV overlay
    overlay = image.copy()
    if plate_info.get("contour") is not None:
        cv2.drawContours(overlay, [plate_info["contour"]], -1, (255, 200, 0), 2)

    mayo_color = np.zeros_like(image)
    mayo_color[mayo_mask > 0] = (245, 248, 255)
    cv2.addWeighted(mayo_color, 0.40, overlay, 0.60, 0, overlay)

    if valid_contours:
        cv2.drawContours(overlay, valid_contours, -1, (0, 0, 255), 2)

    if card_info.get("detected") and card_info.get("ordered_pts"):
        pts = np.array(card_info["ordered_pts"], dtype=np.int32)
        cv2.polylines(overlay, [pts], True, (255, 0, 255), 3)

    # Banner
    banner_h = 75
    banner = np.zeros((banner_h, w, 3), dtype=np.uint8)
    banner[:] = (25, 25, 25)

    cv2.putText(
        banner,
        f"Detected Mayo: ~{int(estimated_mayo_grams)} g [{weight_info['uncertainty_range_label']}]",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 230, 180),
        2,
    )
    cv2.putText(
        banner,
        f"You Can Eat: ~{int(predicted_rice)} g Mandi (NumPy Least-Squares)",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (100, 255, 150),
        2,
    )

    combined = np.vstack([banner, overlay])
    success, buffer = cv2.imencode(".jpg", combined, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    overlay_b64 = base64.b64encode(buffer).decode("utf-8") if success else ""

    return {
        "success": True,
        "estimated_mayo_grams": weight_info["estimated_mayo_grams"],
        "minimum_mayo_grams": weight_info["minimum_mayo_grams"],
        "maximum_mayo_grams": weight_info["maximum_mayo_grams"],
        "confidence": weight_info["confidence"],
        "uncertainty_range_label": weight_info["uncertainty_range_label"],
        "predicted_rice_grams": predicted_rice,
        "method": "OpenCV Mayo Estimation + NumPy Least-Squares Regression",
        "message": "Your mayonnaise has been mathematically converted into mandi.",
        "measurements": {
            "mayo_area_pixels": mayo_area_px,
            "physical_mayo_area_cm2": round(physical_area_cm2, 2) if physical_area_cm2 else None,
            "reference_card_detected": card_info["detected"],
            "pixels_per_mm": round(px_per_mm, 2) if px_per_mm else None,
        },
        "overlay_base64": overlay_b64,
    }

