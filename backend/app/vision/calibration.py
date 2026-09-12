"""
Traditional Computer Vision Calibration Module for MayoMandi.

Implements reference object detection, real-world metric calibration,
and empirical/classical regression models without neural networks or deep learning.
"""

from typing import Optional, Tuple, Dict, Any, List
import numpy as np
import cv2

# Standard physical credit/ID card dimensions (ISO/IEC 7810 ID-1)
REFERENCE_WIDTH_MM: float = 85.6
REFERENCE_HEIGHT_MM: float = 53.98
REFERENCE_ASPECT_RATIO: float = REFERENCE_WIDTH_MM / REFERENCE_HEIGHT_MM  # ~1.5858

# Standard fallback plate diameter if no reference card is present (in mm)
FALLBACK_PLATE_DIAMETER_MM: float = 280.0

# Mayonnaise density in grams per milliliter (commercial mayo is ~0.92 - 0.95 g/mL)
DEFAULT_MAYO_DENSITY_G_PER_ML: float = 0.94

# Standard measuring spoon volumes in mL
SPOON_VOLUMES_ML = {
    "tablespoon": 15.0,
    "teaspoon": 5.0,
    "dessertspoon": 10.0,
}


def order_quad_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 quadrilateral points in order: Top-Left, Top-Right, Bottom-Right, Bottom-Left.
    """
    pts = pts.reshape(4, 2).astype(np.float32)
    rect = np.zeros((4, 2), dtype=np.float32)

    # Sum: TL has min sum, BR has max sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Diff: TR has min diff (x - y is largest positive), BL has max diff (y - x is largest positive)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def detect_reference_card(
    image: np.ndarray,
    exclude_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Detects the MayoMandi reference card (standard 85.6 mm width) using
    traditional OpenCV edge detection, contour analysis, polygon approximation,
    aspect ratio verification, and perspective analysis.

    Returns:
        Dict containing detection status, pixels_per_mm, contour, bounding box, etc.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # If an exclude mask (e.g. plate region) is provided, mask it out
    if exclude_mask is not None:
        gray = cv2.bitwise_and(gray, gray, mask=cv2.bitwise_not(exclude_mask))

    # Preprocessing: bilateral filter or Gaussian blur to smooth texture while keeping card edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection: Canny + Otsu thresholding combination
    high_thresh, _ = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    low_thresh = 0.5 * high_thresh
    edges = cv2.Canny(blurred, max(20, int(low_thresh)), max(50, int(high_thresh)))

    # Morphological closing to seal broken edges of card boundary
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_area = (h * w) * 0.003  # At least 0.3% of image
    max_area = (h * w) * 0.40   # At most 40% of image

    best_candidate = None
    best_score = 0.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.035 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            ordered = order_quad_points(approx)
            tl, tr, br, bl = ordered

            w_top = np.linalg.norm(tr - tl)
            w_bot = np.linalg.norm(br - bl)
            h_left = np.linalg.norm(bl - tl)
            h_right = np.linalg.norm(br - tr)

            avg_w = (w_top + w_bot) / 2.0
            avg_h = (h_left + h_right) / 2.0

            if avg_h < 1 or avg_w < 1:
                continue

            # Long side vs short side
            card_long = max(avg_w, avg_h)
            card_short = min(avg_w, avg_h)
            aspect = card_long / card_short

            # Standard card aspect ratio is ~1.586
            aspect_diff = abs(aspect - REFERENCE_ASPECT_RATIO)
            if aspect_diff < 0.45:  # Accept realistic perspective tilt
                rect_area = avg_w * avg_h
                rectangularity = area / rect_area if rect_area > 0 else 0
                if 0.70 <= rectangularity <= 1.30:
                    score = (1.0 / (1.0 + aspect_diff)) * rectangularity
                    if score > best_score:
                        best_score = score
                        best_candidate = {
                            "contour": approx,
                            "ordered_pts": ordered,
                            "card_long_px": card_long,
                            "card_short_px": card_short,
                            "aspect_ratio": aspect,
                            "area_px": area,
                        }

    if best_candidate is not None:
        px_per_mm = best_candidate["card_long_px"] / REFERENCE_WIDTH_MM
        return {
            "detected": True,
            "pixels_per_mm": float(px_per_mm),
            "reference_width_px": float(best_candidate["card_long_px"]),
            "aspect_ratio": float(best_candidate["aspect_ratio"]),
            "contour": best_candidate["contour"].tolist(),
            "ordered_pts": best_candidate["ordered_pts"].tolist(),
            "confidence_boost": 0.20,
            "message": f"Reference card detected ({best_candidate['card_long_px']:.1f} px = {REFERENCE_WIDTH_MM} mm). Calibrated scale: {px_per_mm:.2f} px/mm.",
        }

    return {
        "detected": False,
        "pixels_per_mm": None,
        "reference_width_px": None,
        "aspect_ratio": None,
        "contour": None,
        "ordered_pts": None,
        "confidence_boost": 0.0,
        "message": "Reference card not detected. Using plate-relative fallback estimation (lower confidence).",
    }


def calibrate_plate_scale(
    plate_diameter_px: float,
    card_scale: Dict[str, Any],
) -> Tuple[float, float, str]:
    """
    Computes pixels_per_mm and estimated plate diameter (in mm).
    Uses the reference card if detected, otherwise falls back to standard plate diameter.

    Returns:
        (pixels_per_mm, plate_diameter_mm, calibration_source_label)
    """
    if card_scale.get("detected") and card_scale.get("pixels_per_mm"):
        px_per_mm = card_scale["pixels_per_mm"]
        plate_diam_mm = plate_diameter_px / px_per_mm
        return px_per_mm, plate_diam_mm, "reference_card"

    # Fallback to standard plate diameter
    px_per_mm = plate_diameter_px / FALLBACK_PLATE_DIAMETER_MM
    return px_per_mm, FALLBACK_PLATE_DIAMETER_MM, "fallback_plate_assumption"


class ClassicalMayoCalibrator:
    """
    Empirical and classical regression calibrator for mayonnaise samples.
    Fits sample data (visual feature -> actual mayo grams) using NumPy least-squares
    linear regression without neural networks.
    """

    def __init__(self):
        # Default empirical relationship for area in cm^2 -> mayo grams
        # Assuming ~0.5 cm average dome height and ~0.94 g/mL density -> ~0.47 g/cm^2
        self.default_slope = 0.47
        self.default_intercept = 0.0

        # Custom calibration samples: list of dicts {"sample_name": str, "feature": float, "actual_grams": float}
        self.samples: List[Dict[str, Any]] = []
        self.fitted_slope: Optional[float] = None
        self.fitted_intercept: Optional[float] = None
        self.r_squared: Optional[float] = None

    def add_sample(self, sample_name: str, feature_value: float, actual_grams: float):
        self.samples.append({
            "sample_name": sample_name,
            "feature": float(feature_value),
            "actual_grams": float(actual_grams),
        })

    def clear_samples(self):
        self.samples = []
        self.fitted_slope = None
        self.fitted_intercept = None
        self.r_squared = None

    def fit_model(self) -> Dict[str, Any]:
        """
        Fits y = slope * x + intercept using numpy least squares.
        Requires at least 2 samples.
        """
        if len(self.samples) < 2:
            return {
                "success": False,
                "message": f"Need at least 2 samples to fit classical regression (currently have {len(self.samples)}).",
                "slope": self.default_slope,
                "intercept": self.default_intercept,
                "r_squared": None,
                "sample_count": len(self.samples),
            }

        x = np.array([s["feature"] for s in self.samples], dtype=np.float64)
        y = np.array([s["actual_grams"] for s in self.samples], dtype=np.float64)

        if np.ptp(x) < 1e-6:
            # All samples have the same visual feature; fallback to mean ratio
            mean_x = np.maximum(np.mean(x), 1e-6)
            slope = float(np.mean(y) / mean_x)
            intercept = 0.0
            r2 = 0.80
        else:
            # 1st degree polynomial fit (linear regression)
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-9 else 1.0

        self.fitted_slope = float(slope)
        self.fitted_intercept = float(intercept)
        self.r_squared = float(max(0.0, min(1.0, r2)))

        return {
            "success": True,
            "message": f"Model fitted successfully with {len(self.samples)} samples (R² = {self.r_squared:.3f}).",
            "slope": self.fitted_slope,
            "intercept": self.fitted_intercept,
            "r_squared": self.r_squared,
            "sample_count": len(self.samples),
        }

    def predict(self, feature_value: float) -> Tuple[float, float]:
        """
        Predicts mayo grams given visual feature value.
        Returns: (predicted_grams, model_confidence)
        """
        if self.fitted_slope is not None and self.fitted_intercept is not None:
            pred = self.fitted_slope * feature_value + self.fitted_intercept
            conf = self.r_squared if self.r_squared is not None else 0.85
            return max(0.0, float(pred)), float(conf)

        # Fallback to default empirical model
        pred = self.default_slope * feature_value + self.default_intercept
        return max(0.0, float(pred)), 0.70


# Global singleton instance for storing interactive calibration samples
global_mayo_calibrator = ClassicalMayoCalibrator()
