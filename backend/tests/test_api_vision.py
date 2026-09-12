"""
API integration tests for MayoMandi Vision endpoints.
"""

import unittest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from app.main import app


class TestVisionEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Generate a test mandi image
        img = np.full((500, 500, 3), 40, dtype=np.uint8)
        cv2.circle(img, (250, 250), 180, (190, 190, 190), -1)  # Plate
        cv2.circle(img, (250, 250), 120, (50, 180, 230), -1)   # Rice
        _, buf = cv2.imencode(".jpg", img)
        self.mandi_bytes = buf.tobytes()

        # Generate a test spoon mayo image
        spoon_img = np.full((400, 400, 3), 40, dtype=np.uint8)
        cv2.ellipse(spoon_img, (200, 200), (80, 50), 0, 0, 360, (180, 180, 180), -1)
        cv2.ellipse(spoon_img, (200, 200), (60, 35), 0, 0, 360, (220, 240, 250), -1)
        _, s_buf = cv2.imencode(".jpg", spoon_img)
        self.mayo_bytes = s_buf.tobytes()

    def test_mandi_endpoint(self):
        files = {"file": ("mandi.jpg", self.mandi_bytes, "image/jpeg")}
        data = {
            "spice_level": "spicy",
            "dryness": "dry",
            "mayo_preference": "lover",
        }
        res = self.client.post("/api/vision/mandi", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("vision", body)
        self.assertIn("recommendation", body)
        self.assertGreater(body["vision"]["estimated_weight_grams"], 50)
        self.assertGreater(body["recommendation"]["recommended_mayo_grams"], 0)
        self.assertTrue(len(body["vision"]["overlay_base64"]) > 100)

    def test_mayo_endpoint(self):
        files = {"file": ("mayo.jpg", self.mayo_bytes, "image/jpeg")}
        data = {"mode": "spoon", "spoon_type": "tablespoon"}
        res = self.client.post("/api/vision/mayo", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertGreater(body["estimated_mayo_grams"], 0)
        self.assertIn("uncertainty_range_label", body)

    def test_check_endpoint(self):
        files = {"file": ("mayo.jpg", self.mayo_bytes, "image/jpeg")}
        # Check against high requirement (e.g. 185g) -> should be NOT_ENOUGH
        data = {"required_mayo_grams": 185.0, "mode": "spoon"}
        res = self.client.post("/api/vision/check", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["status"], "NOT_ENOUGH")
        self.assertIn("❌ NOT ENOUGH MAYO", body["badge"])
        self.assertGreater(body["short_by_grams"], 100)

        # Check against low requirement (e.g. 5g) -> should be ENOUGH
        files2 = {"file": ("mayo.jpg", self.mayo_bytes, "image/jpeg")}
        data2 = {"required_mayo_grams": 5.0, "mode": "spoon"}
        res2 = self.client.post("/api/vision/check", files=files2, data=data2)
        self.assertEqual(res2.status_code, 200)
        body2 = res2.json()
        self.assertEqual(body2["status"], "ENOUGH")
        self.assertIn("✓ MAYO ENOUGH", body2["badge"])

    def test_calibration_endpoints(self):
        # Reset
        res_reset = self.client.post("/api/vision/calibrate/reset")
        self.assertEqual(res_reset.status_code, 200)

        # Add sample 1
        files1 = {"file": ("s1.jpg", self.mayo_bytes, "image/jpeg")}
        res1 = self.client.post(
            "/api/vision/calibrate/sample",
            files=files1,
            data={"sample_name": "Sample 1", "actual_grams": 15.0},
        )
        self.assertEqual(res1.status_code, 200)

        # Add sample 2
        files2 = {"file": ("s2.jpg", self.mayo_bytes, "image/jpeg")}
        res2 = self.client.post(
            "/api/vision/calibrate/sample",
            files=files2,
            data={"sample_name": "Sample 2", "actual_grams": 30.0},
        )
        self.assertEqual(res2.status_code, 200)

        # Get samples
        res_get = self.client.get("/api/vision/calibrate/samples")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.json()["samples"]), 2)

        # Fit model
        res_fit = self.client.post("/api/vision/calibrate/fit")
        self.assertEqual(res_fit.status_code, 200)
        self.assertTrue(res_fit.json()["success"])

    def test_reverse_photo_endpoint(self):
        files = {"file": ("mayo_plate.jpg", self.mayo_bytes, "image/jpeg")}
        res = self.client.post("/api/vision/reverse", files=files)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("estimated_mayo_grams", body)
        self.assertIn("predicted_rice_grams", body)
        self.assertIn("uncertainty_range_label", body)
        self.assertGreater(body["confidence"], 0)
        self.assertEqual(body["method"], "OpenCV Mayo Estimation + NumPy Least-Squares Regression")
        self.assertEqual(body["message"], "Your mayonnaise has been mathematically converted into mandi.")
        self.assertTrue(len(body["overlay_base64"]) > 0)


if __name__ == "__main__":
    unittest.main()
