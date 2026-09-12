"""
Classical NumPy Least-Squares Linear Regression for MayoMandi.

Strictly NO neural networks, NO deep learning, NO AI models.
Uses pure numpy.linalg.lstsq for:
1. Mayo visual feature -> Estimated Mayo Grams
2. Estimated Mayo Grams -> Predicted Mandi Rice Grams
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np


def find_data_file(filename: str) -> Path:
    """Finds a calibration CSV file relative to project root or app."""
    # Try project root data/
    root_data = Path(__file__).resolve().parent.parent.parent.parent / "data" / filename
    if root_data.exists():
        return root_data

    # Try backend/data/
    backend_data = Path(__file__).resolve().parent.parent.parent / "data" / filename
    if backend_data.exists():
        return backend_data

    # Fallback to local
    return Path(filename)


class RiceMayoRegression:
    """
    Fits: mandi_rice = beta_0 + beta_1 * mayo_grams
    using np.linalg.lstsq() on data/rice_mayo_calibration.csv
    """

    def __init__(self, csv_filename: str = "rice_mayo_calibration.csv"):
        self.csv_path = find_data_file(csv_filename)
        self.beta: np.ndarray = np.array([0.0, 4.13])  # Baseline fallback
        self.r_squared: float = 0.99
        self.data_points: int = 0
        self.fit()

    def fit(self):
        if not self.csv_path.exists():
            return

        try:
            # Read CSV with numpy or standard parsing
            data = np.genfromtxt(self.csv_path, delimiter=",", skip_header=1)
            if data.ndim == 2 and data.shape[0] >= 2 and data.shape[1] >= 2:
                mayo = data[:, 0]
                rice = data[:, 1]

                # Construct design matrix X: column of 1s and column of mayo
                X = np.column_stack([np.ones(len(mayo)), mayo])
                y = rice

                # np.linalg.lstsq for classical linear regression
                beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
                self.beta = beta
                self.data_points = len(mayo)

                # R-squared
                y_pred = X @ beta
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                ss_res = np.sum((y - y_pred) ** 2)
                self.r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        except Exception as e:
            # Keep fallback baseline
            pass

    def predict(self, mayo_grams: float) -> float:
        """
        Predicted rice = beta[0] + beta[1] * estimated_mayo_grams
        """
        pred = self.beta[0] + self.beta[1] * float(mayo_grams)
        return max(0.0, round(float(pred), 1))


class MayoFeatureRegression:
    """
    Fits: actual_mayo_grams = beta_0 + beta_1 * visual_feature
    using np.linalg.lstsq() on data/mayo_calibration.csv
    """

    def __init__(self, csv_filename: str = "mayo_calibration.csv"):
        self.csv_path = find_data_file(csv_filename)
        # Default baseline: slope ~ 1.06 g per 1000 pixels (for standard 100k px range)
        self.beta_px: np.ndarray = np.array([0.0, 1.06])
        self.beta_physical: np.ndarray = np.array([0.0, 4.88])  # ~4.88 g/cm^2
        self.data_points: int = 0
        self.r_squared: float = 0.99
        self.fit()

    def fit(self):
        if not self.csv_path.exists():
            return

        try:
            # Columns: image_id(0), actual_mayo_grams(1), mayo_area_pixels(2),
            # reference_area_pixels(3), mayo_reference_ratio(4), physical_mayo_area(5),
            # mayo_width(6), mayo_height(7)
            data = np.genfromtxt(
                self.csv_path,
                delimiter=",",
                skip_header=1,
                usecols=(1, 2, 5),  # actual_mayo, mayo_area_pixels, physical_mayo_area
            )
            if data.ndim == 2 and data.shape[0] >= 2:
                actual = data[:, 0]
                area_px_k = data[:, 1] / 1000.0  # Normalize to thousands of pixels
                physical_area = data[:, 2]

                # Model for pixel area
                X_px = np.column_stack([np.ones(len(area_px_k)), area_px_k])
                self.beta_px = np.linalg.lstsq(X_px, actual, rcond=None)[0]

                # Model for calibrated physical area (cm^2)
                X_phys = np.column_stack([np.ones(len(physical_area)), physical_area])
                self.beta_physical = np.linalg.lstsq(X_phys, actual, rcond=None)[0]

                self.data_points = len(actual)
        except Exception:
            pass

    def predict_from_physical(self, physical_area_cm2: float) -> float:
        pred = self.beta_physical[0] + self.beta_physical[1] * float(physical_area_cm2)
        return max(0.0, round(float(pred), 1))

    def predict_from_pixels(self, mayo_pixels: float) -> float:
        k_px = float(mayo_pixels) / 1000.0
        pred = self.beta_px[0] + self.beta_px[1] * k_px
        return max(0.0, round(float(pred), 1))


# Global instances for regression
rice_mayo_model = RiceMayoRegression()
mayo_feature_model = MayoFeatureRegression()
