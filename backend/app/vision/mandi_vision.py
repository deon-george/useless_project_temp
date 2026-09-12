"""
Traditional Computer Vision Mandi Rice Analysis Pipeline for MayoMandi.

Pipeline:
MANDI IMAGE -> Preprocessing -> Plate Detection -> Rice Segmentation
-> Morphological Cleanup -> Contour Extraction -> Rice Measurements
-> Calibration -> Quantity Estimation -> Mayo Recommendation

Uses traditional OpenCV & NumPy techniques ONLY (no deep learning/neural nets).
"""

import base64
from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np

from .calibration import detect_reference_card, calibrate_plate_scale, REFERENCE_WIDTH_MM


# Rice segmentation color threshold presets (OpenCV scales: H:0-180, S:0-255, V:0-255; L:0-255, A:0-255, B:0-255)
DEFAULT_RICE_CONFIG = {
    # HSV bounds for golden/yellow/spiced mandi rice
    "hsv_lower": np.array([8, 25, 65], dtype=np.uint8),
    "hsv_upper": np.array([45, 235, 255], dtype=np.uint8),
    # LAB bounds (L: brightness, A: green-red, B: blue-yellow)
    "lab_lower": np.array([65, 115, 128], dtype=np.uint8),
    "lab_upper": np.array([255, 155, 195], dtype=np.uint8),
    # Meat exclusion (dark roasted chicken / spices)
    "chicken_l_max": 60,
}


def detect_plate(image: np.ndarray) -> Dict[str, Any]:
    """
    Detects the serving plate/thalam using traditional edge detection,
    thresholding, circularity/elliptical contour analysis, and convex hull.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Mild blur to suppress table grain while preserving plate boundaries
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # Edge detection
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_plate_area = (h * w) * 0.10  # Plate must occupy at least 10% of image
    max_plate_area = (h * w) * 0.92  # At most 92% of image

    best_plate_cnt = None
    best_score = 0.0

    img_center = np.array([w / 2.0, h / 2.0])

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_plate_area or area > max_plate_area:
            continue

        # Hull for convexity
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # Centroid distance to image center (plates are usually centered)
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        center_dist = np.linalg.norm(np.array([cx, cy]) - img_center)
        center_norm = 1.0 - min(1.0, center_dist / (max(h, w) / 2.0))

        # Check aspect ratio of bounding box
        bx, by, bw, bh = cv2.boundingRect(hull)
        aspect = min(bw, bh) / max(bw, bh)

        # Plates viewed from ~45 degrees appear as ellipses (aspect 0.55 - 1.0)
        if aspect >= 0.50 and solidity > 0.70:
            score = (area / (h * w)) * 0.4 + solidity * 0.3 + center_norm * 0.2 + aspect * 0.1
            if score > best_score:
                best_score = score
                best_plate_cnt = hull

    # Fallback: if no clear plate contour is found, use an elliptical region centered in image
    fallback_used = False
    if best_plate_cnt is None or best_score < 0.25:
        fallback_used = True
        # Create an elliptical fallback plate covering 68% of image width and height
        ellipse_w = int(w * 0.72)
        ellipse_h = int(h * 0.72)
        ex = int(w / 2)
        ey = int(h / 2)
        plate_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(plate_mask, (ex, ey), (ellipse_w // 2, ellipse_h // 2), 0, 0, 360, 255, -1)
        plate_area = float(np.pi * (ellipse_w / 2) * (ellipse_h / 2))
        plate_diam_px = float(max(ellipse_w, ellipse_h))
        plate_contour = None
    else:
        plate_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(plate_mask, [best_plate_cnt], -1, 255, -1)
        plate_area = float(cv2.contourArea(best_plate_cnt))
        bx, by, bw, bh = cv2.boundingRect(best_plate_cnt)
        plate_diam_px = float(max(bw, bh))
        plate_contour = best_plate_cnt

    return {
        "mask": plate_mask,
        "contour": plate_contour,
        "area_px": plate_area,
        "diameter_px": plate_diam_px,
        "fallback_used": fallback_used,
    }


def detect_rice(
    image: np.ndarray,
    plate_mask: np.ndarray,
    config: Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Traditional rice segmentation combining HSV, LAB, brightness,
    saturation, and position within the plate.
    """
    cfg = config or DEFAULT_RICE_CONFIG

    # Color space conversions
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # 1. HSV Rice Mask (hue range for mandi rice, moderate saturation, good brightness)
    hsv_mask = cv2.inRange(hsv, cfg["hsv_lower"], cfg["hsv_upper"])

    # 2. LAB Rice Mask (high L lightness, warm A, yellowish B)
    lab_mask = cv2.inRange(lab, cfg["lab_lower"], cfg["lab_upper"])

    # Combine color criteria (either color space detection that is consistent)
    combined_color = cv2.bitwise_and(hsv_mask, lab_mask)

    # Also capture lighter rice grains that may have lower saturation
    # (High lightness L > 140, Hue in warm spectrum)
    l_channel = lab[:, :, 0]
    b_channel = lab[:, :, 1]
    bright_rice = cv2.bitwise_and(
        cv2.inRange(l_channel, 120, 255),
        cv2.inRange(hsv[:, :, 0], 5, 50),
    )
    # Bright rice must have slight warmth (B in LAB > 125)
    bright_rice = cv2.bitwise_and(bright_rice, cv2.inRange(lab[:, :, 2], 126, 210))

    initial_rice = cv2.bitwise_or(combined_color, bright_rice)

    # Restrict strictly to inside plate
    rice_in_plate = cv2.bitwise_and(initial_rice, initial_rice, mask=plate_mask)

    # Exclude dark roasted chicken pieces (L < chicken_l_max)
    dark_mask = cv2.inRange(l_channel, 0, cfg["chicken_l_max"])
    rice_in_plate = cv2.bitwise_and(rice_in_plate, rice_in_plate, mask=cv2.bitwise_not(dark_mask))

    return rice_in_plate


def cleanup_rice_mask(raw_mask: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
    """
    Cleans up the initial rice segmentation mask using traditional morphological operations:
    Gaussian blur, opening, closing, connected-component filtering, and contour filtering.
    """
    # 1. Median filter to eliminate single-pixel salt-and-pepper noise
    filtered = cv2.medianBlur(raw_mask, 5)

    # 2. Morphological Opening to remove tiny isolated specks
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, open_kernel, iterations=1)

    # 3. Morphological Closing to consolidate rice grains into a continuous mound
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, close_kernel, iterations=2)

    # 4. Connected Components filtering
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    clean_mask = np.zeros_like(closed)

    # Keep components with area > 120 pixels
    min_comp_area = 120
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_comp_area:
            clean_mask[labels == i] = 255

    # 5. Extract contours and filter
    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) >= min_comp_area]

    # Fill internal small gaps within valid rice contours
    cv2.drawContours(clean_mask, valid_contours, -1, 255, -1)

    return clean_mask, valid_contours


def calculate_rice_measurements(
    rice_mask: np.ndarray,
    valid_contours: List[np.ndarray],
    plate_area_px: float,
    pixels_per_mm: Optional[float],
) -> Dict[str, Any]:
    """
    Computes geometric measurements of the detected mandi rice:
    - rice pixel area
    - largest rice contour
    - total rice contour area
    - rice perimeter
    - bounding-box width/height
    - convex hull
    - solidity
    - rice/plate area ratio
    - approximate physical area in cm^2 (if calibrated)
    """
    rice_area_px = float(cv2.countNonZero(rice_mask))
    rice_plate_ratio = rice_area_px / plate_area_px if plate_area_px > 0 else 0.0

    if not valid_contours:
        return {
            "rice_area_px": 0.0,
            "largest_contour_area_px": 0.0,
            "total_contour_area_px": 0.0,
            "perimeter_px": 0.0,
            "bbox_w": 0,
            "bbox_h": 0,
            "solidity": 0.0,
            "rice_plate_ratio": 0.0,
            "physical_area_cm2": None,
        }

    largest_cnt = max(valid_contours, key=cv2.contourArea)
    largest_area_px = float(cv2.contourArea(largest_cnt))
    total_cnt_area_px = float(sum(cv2.contourArea(c) for c in valid_contours))

    perimeter_px = float(sum(cv2.arcLength(c, True) for c in valid_contours))

    # Bounding box of all rice contours combined
    all_points = np.vstack(valid_contours)
    bx, by, bw, bh = cv2.boundingRect(all_points)

    # Convex hull and solidity
    hull = cv2.convexHull(all_points)
    hull_area = float(cv2.contourArea(hull))
    solidity = rice_area_px / hull_area if hull_area > 0 else 0.0

    # Physical area if calibrated
    physical_area_cm2 = None
    if pixels_per_mm and pixels_per_mm > 0:
        # mm^2 = px / (px/mm)^2 -> cm^2 = mm^2 / 100
        physical_area_cm2 = (rice_area_px / (pixels_per_mm ** 2)) / 100.0

    return {
        "rice_area_px": rice_area_px,
        "largest_contour_area_px": largest_area_px,
        "total_contour_area_px": total_cnt_area_px,
        "perimeter_px": perimeter_px,
        "bbox_w": bw,
        "bbox_h": bh,
        "solidity": round(solidity, 3),
        "rice_plate_ratio": round(rice_plate_ratio, 3),
        "physical_area_cm2": round(physical_area_cm2, 1) if physical_area_cm2 is not None else None,
        "largest_contour": largest_cnt,
        "all_contours": valid_contours,
        "convex_hull": hull,
    }


def estimate_rice_weight(
    features: Dict[str, Any],
    has_reference_card: bool,
    plate_fallback: bool,
) -> Dict[str, Any]:
    """
    Empirical traditional mathematical model for rice quantity estimation.

    Scientific note: A 2D photograph cannot measure exact food mass.
    Returns:
    - estimated_weight_grams
    - minimum_estimated_weight
    - maximum_estimated_weight
    - confidence (percentage)
    """
    rice_area_px = features.get("rice_area_px", 0.0)
    rice_plate_ratio = features.get("rice_plate_ratio", 0.0)
    physical_area_cm2 = features.get("physical_area_cm2")
    solidity = features.get("solidity", 0.85)

    if rice_area_px < 500 or rice_plate_ratio < 0.03:
        return {
            "estimated_weight_grams": 0.0,
            "minimum_estimated_weight": 0.0,
            "maximum_estimated_weight": 0.0,
            "confidence": 0,
            "uncertainty_range_label": "0 g",
            "notes": ["No significant rice detected on plate."],
        }

    # Cooked mandi rice bulk density ~0.78 - 0.84 g/cm^3
    RICE_BULK_DENSITY = 0.80

    notes = []

    if has_reference_card and physical_area_cm2 is not None and physical_area_cm2 > 10.0:
        # Calibrated physical model:
        # Rice mound on a flat plate forms a rounded dome / truncated ellipsoid.
        # Average mound height in cm roughly scales with sqrt(Area): h ~ 1.2 + 0.12 * sqrt(Area)
        # Typical mound height is 2.5 - 4.5 cm for 300g - 900g portions.
        mound_radius = np.sqrt(physical_area_cm2 / np.pi)
        estimated_avg_height_cm = 1.2 + (0.13 * mound_radius)
        # Volume of dome ~ Area * avg_height
        estimated_volume_cm3 = physical_area_cm2 * estimated_avg_height_cm * max(0.7, solidity)
        raw_weight = estimated_volume_cm3 * RICE_BULK_DENSITY

        confidence = 87
        margin_pct = 0.12  # ±12% uncertainty
        notes.append("Calibrated using physical reference card (85.6 mm).")
    else:
        # Fallback model based on standard mandi thalam plate (~28 cm diameter, ~615 cm^2)
        # Plate ratio of 0.8 is typically a full portion (~750g - 800g)
        # Plate ratio of 0.5 is ~450g
        # Empirical curve: weight = 950 * (ratio ^ 1.15)
        raw_weight = 950.0 * (max(0.01, rice_plate_ratio) ** 1.12)

        confidence = 65 if not plate_fallback else 55
        margin_pct = 0.18  # ±18% uncertainty
        notes.append("Estimated using plate-relative geometric fallback (no reference card detected).")

    # Round to realistic numbers
    estimated_weight = round(raw_weight / 5.0) * 5.0
    estimated_weight = max(50.0, estimated_weight)

    min_weight = round((estimated_weight * (1.0 - margin_pct)) / 5.0) * 5.0
    max_weight = round((estimated_weight * (1.0 + margin_pct)) / 5.0) * 5.0

    return {
        "estimated_weight_grams": float(estimated_weight),
        "minimum_estimated_weight": float(min_weight),
        "maximum_estimated_weight": float(max_weight),
        "confidence": int(confidence),
        "uncertainty_range_label": f"{int(min_weight)}–{int(max_weight)} g",
        "notes": notes,
    }


def generate_mandi_overlay(
    image: np.ndarray,
    plate_info: Dict[str, Any],
    rice_mask: np.ndarray,
    card_info: Dict[str, Any],
    weight_info: Dict[str, Any],
    measurements: Dict[str, Any],
) -> str:
    """
    Renders visual debug overlays on the image:
    - Plate contour in bright cyan
    - Rice mask in warm golden yellow
    - Reference card in magenta
    - Measurement banners
    Returns base64 encoded JPEG.
    """
    overlay = image.copy()
    h, w = image.shape[:2]

    # 1. Draw plate boundary
    if plate_info.get("contour") is not None:
        cv2.drawContours(overlay, [plate_info["contour"]], -1, (255, 200, 0), 3)

    # 2. Rice semi-transparent mask overlay (golden yellow)
    rice_color = np.zeros_like(image)
    rice_color[rice_mask > 0] = (30, 190, 255)  # Golden warm tint in BGR
    cv2.addWeighted(rice_color, 0.45, overlay, 0.55, 0, overlay)

    # Rice contours
    if measurements.get("all_contours"):
        cv2.drawContours(overlay, measurements["all_contours"], -1, (0, 220, 255), 2)

    # 3. Draw reference card if detected
    if card_info.get("detected") and card_info.get("ordered_pts"):
        pts = np.array(card_info["ordered_pts"], dtype=np.int32)
        cv2.polylines(overlay, [pts], True, (255, 0, 255), 3)
        cv2.putText(
            overlay,
            f"REF CARD ({REFERENCE_WIDTH_MM}mm)",
            (pts[0][0], max(20, pts[0][1] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 255),
            2,
        )

    # 4. Top header banner
    banner_h = 75
    banner = np.zeros((banner_h, w, 3), dtype=np.uint8)
    banner[:] = (30, 25, 20)  # Dark background

    weight_text = f"Estimated Rice: ~{int(weight_info['estimated_weight_grams'])} g [{weight_info['uncertainty_range_label']}]"
    conf_text = f"Confidence: {weight_info['confidence']}% | Ratio: {measurements['rice_plate_ratio']:.2f}"
    if card_info.get("detected"):
        conf_text += f" | Physical: {measurements.get('physical_area_cm2', 0)} cm2"

    cv2.putText(banner, weight_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 225, 255), 2)
    cv2.putText(banner, conf_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    combined = np.vstack([banner, overlay])

    # Encode to base64 JPEG
    success, buffer = cv2.imencode(".jpg", combined, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    return base64.b64encode(buffer).decode("utf-8")


def process_mandi_image(
    image_bytes: bytes,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for Mandi Vision analysis.
    Executes traditional CV pipeline on raw uploaded image bytes.
    """
    # Decode image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image file or unsupported image format.")

    # Downscale if excessively large for fast, reliable processing
    max_dim = 1200
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # 1. Detect Plate
    plate_info = detect_plate(image)

    # 2. Detect Reference Card (outside plate)
    card_info = detect_reference_card(image, exclude_mask=plate_info["mask"])

    # 3. Calibrate metric scale
    px_per_mm, plate_diam_mm, scale_source = calibrate_plate_scale(
        plate_info["diameter_px"], card_info
    )

    # 4. Rice segmentation
    raw_rice_mask = detect_rice(image, plate_info["mask"], config)

    # 5. Morphological cleanup
    clean_rice_mask, valid_contours = cleanup_rice_mask(raw_rice_mask)

    # 6. Geometric measurements
    measurements = calculate_rice_measurements(
        clean_rice_mask, valid_contours, plate_info["area_px"], px_per_mm
    )

    # 7. Quantity estimation
    weight_info = estimate_rice_weight(
        measurements,
        has_reference_card=card_info["detected"],
        plate_fallback=plate_info["fallback_used"],
    )

    # 8. Render visual debug overlay
    overlay_b64 = generate_mandi_overlay(
        image, plate_info, clean_rice_mask, card_info, weight_info, measurements
    )

    return {
        "success": True,
        "estimated_weight_grams": weight_info["estimated_weight_grams"],
        "minimum_estimated_weight": weight_info["minimum_estimated_weight"],
        "maximum_estimated_weight": weight_info["maximum_estimated_weight"],
        "confidence": weight_info["confidence"],
        "uncertainty_range_label": weight_info["uncertainty_range_label"],
        "notes": weight_info["notes"],
        "measurements": {
            "rice_area_pixels": measurements["rice_area_px"],
            "plate_area_pixels": plate_info["area_px"],
            "rice_plate_ratio": measurements["rice_plate_ratio"],
            "solidity": measurements["solidity"],
            "bbox_width_px": measurements["bbox_w"],
            "bbox_height_px": measurements["bbox_h"],
            "calibrated_physical_area_cm2": measurements["physical_area_cm2"],
        },
        "calibration": {
            "reference_card_detected": card_info["detected"],
            "scale_source": scale_source,
            "pixels_per_mm": round(px_per_mm, 2) if px_per_mm else None,
            "card_message": card_info["message"],
        },
        "overlay_base64": overlay_b64,
    }
