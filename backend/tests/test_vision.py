"""
Unit and integration tests for MayoMandi traditional computer vision modules.
"""

import unittest
import numpy as np
import cv2

from app.vision.calibration import (
    REFERENCE_WIDTH_MM,
    REFERENCE_HEIGHT_MM,
    REFERENCE_ASPECT_RATIO,
    detect_reference_card,
    calibrate_plate_scale,
    ClassicalMayoCalibrator,
)
from app.vision.mandi_vision import (
    detect_plate,
    detect_rice,
    cleanup_rice_mask,
    calculate_rice_measurements,
    estimate_rice_weight,
    process_mandi_image,
)
from app.vision.mayo_vision import (
    detect_spoon,
    detect_mayo,
    estimate_mayo_spoon,
    process_mayo_image,
)


class TestCalibrationModule(unittest.TestCase):
    def test_reference_card_dimensions(self):
        self.assertEqual(REFERENCE_WIDTH_MM, 85.6)
        self.assertAlmostEqual(REFERENCE_ASPECT_RATIO, 85.6 / 53.98, places=3)

    def test_detect_reference_card_present(self):
        # Create a synthetic image with a standard 85.6 x 53.98 aspect rectangle
        # say 171 x 108 pixels (aspect = 1.583)
        img = np.full((500, 600, 3), 120, dtype=np.uint8)
        # Draw dark table border, and a bright white rectangular card
        cv2.rectangle(img, (50, 50), (221, 158), (250, 250, 250), -1)
        # Add thin border to ensure crisp edges
        cv2.rectangle(img, (50, 50), (221, 158), (30, 30, 30), 2)

        result = detect_reference_card(img)
        self.assertTrue(result["detected"])
        self.assertIsNotNone(result["pixels_per_mm"])
        self.assertAlmostEqual(result["aspect_ratio"], 171.0 / 108.0, delta=0.25)
        self.assertIn("85.6", result["message"])

    def test_detect_reference_card_absent(self):
        img = np.full((400, 400, 3), 100, dtype=np.uint8)
        result = detect_reference_card(img)
        self.assertFalse(result["detected"])
        self.assertIsNone(result["pixels_per_mm"])

    def test_classical_mayo_calibrator_regression(self):
        calibrator = ClassicalMayoCalibrator()
        calibrator.clear_samples()

        # Add 5 samples: Sample 1 to 5 (10g, 20g, 30g, 40g, 50g)
        for i in range(1, 6):
            calibrator.add_sample(f"Sample {i}", feature_value=float(i * 10), actual_grams=float(i * 10))

        fit_res = calibrator.fit_model()
        self.assertTrue(fit_res["success"])
        self.assertAlmostEqual(fit_res["slope"], 1.0, places=2)
        self.assertAlmostEqual(fit_res["intercept"], 0.0, places=2)
        self.assertAlmostEqual(fit_res["r_squared"], 1.0, places=2)

        pred, conf = calibrator.predict(25.0)
        self.assertAlmostEqual(pred, 25.0, places=1)


class TestMandiVision(unittest.TestCase):
    def test_plate_and_rice_pipeline(self):
        # Create synthetic mandi image: dark background, round silver plate, golden rice mound
        img = np.full((600, 600, 3), 30, dtype=np.uint8)  # Table

        # Plate: gray circle, center (300, 300), radius 220
        cv2.circle(img, (300, 300), 220, (180, 180, 180), -1)
        cv2.circle(img, (300, 300), 220, (100, 100, 100), 3)

        # Rice mound: golden yellow/orange color (BGR: 50, 180, 230), radius 140
        cv2.circle(img, (300, 300), 140, (50, 180, 230), -1)

        # Encode to bytes
        _, buf = cv2.imencode(".jpg", img)
        result = process_mandi_image(buf.tobytes())

        self.assertTrue(result["success"])
        self.assertGreater(result["estimated_weight_grams"], 100)
        self.assertLessEqual(result["minimum_estimated_weight"], result["estimated_weight_grams"])
        self.assertGreaterEqual(result["maximum_estimated_weight"], result["estimated_weight_grams"])
        self.assertGreater(result["confidence"], 0)
        self.assertIn("–", result["uncertainty_range_label"])


class TestMayoVision(unittest.TestCase):
    def test_spoon_mayo_estimation(self):
        # Create synthetic spoon image with mayo
        img = np.full((500, 500, 3), 40, dtype=np.uint8)

        # Spoon bowl ellipse (metal gray)
        cv2.ellipse(img, (250, 250), (100, 60), 0, 0, 360, (180, 180, 180), -1)
        cv2.ellipse(img, (250, 250), (100, 60), 0, 0, 360, (120, 120, 120), 2)

        # Mayo dollop: creamy off-white (BGR: 220, 245, 250) inside spoon bowl
        cv2.ellipse(img, (250, 250), (70, 42), 0, 0, 360, (215, 240, 245), -1)

        _, buf = cv2.imencode(".jpg", img)
        result = process_mayo_image(buf.tobytes(), mode="spoon", spoon_type="tablespoon")

        self.assertTrue(result["success"])
        self.assertGreater(result["estimated_mayo_grams"], 5.0)
        self.assertLess(result["estimated_mayo_grams"], 25.0)
        self.assertGreater(result["confidence"], 50)


if __name__ == "__main__":
    unittest.main()
