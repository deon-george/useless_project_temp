# 🍗 MayoMandi

> **The scientifically unnecessary mandi-to-mayo ratio finder powered by Traditional Computer Vision & Classical NumPy Regression.**

Input or photograph your mandi → MayoMandi calculates the recommended mayonnaise.
Have mayonnaise? Photograph your mayo → Traditional OpenCV & NumPy least-squares regression calculates how much mandi rice you can eat!

---

## ⚠️ Important Scientific Limitation

> **A normal 2D photograph cannot directly measure exact food mass.**

Physical mass depends on 3D volume, packing fraction, moisture content, and density—none of which are fully captured in a single flat photograph.

Therefore:
- The system **NEVER claims**: *"Exact rice weight"* or *"Exact mayonnaise weight"*.
- The system **ALWAYS uses**: *"Estimated rice quantity"* and *"Estimated mayonnaise quantity"*.
- Every visual estimate displays an **uncertainty range** (e.g. `135–165 g` or `650–820 g`) and an explicit **confidence percentage** (e.g. `84%` or `87%`).

---

## 🔬 Technology Requirement: Strictly Traditional CV & Classical Regression

MayoMandi intentionally **DOES NOT USE**:
- ❌ YOLO
- ❌ CNNs / Neural Networks
- ❌ Deep Learning / PyTorch / TensorFlow / Transformers
- ❌ Pretrained AI vision models or third-party AI image APIs

Instead, all vision processing and mathematical modeling is implemented with genuine, transparent **traditional computer vision** and **classical linear algebra**:
- Multi-color space decomposition (**RGB**, **HSV**, **LAB**)
- Adaptive and Otsu thresholding
- Brightness and saturation distribution analysis
- Edge detection (Canny / Sobel) and gradient operators
- Contour hierarchy detection and polygon approximation (`approxPolyDP`)
- Connected-component analysis (`connectedComponentsWithStats`)
- Morphological operations (Gaussian/median blur, opening, closing, dilation, erosion)
- Convex hull and solidity calculation
- Perspective transformation and metric calibration (`REFERENCE_WIDTH_MM = 85.6`)
- Classical least-squares linear regression via **NumPy** (`np.linalg.lstsq`)

---

## 🚀 Key Features

### 1. 📸 Mandi Vision
Upload or capture a photograph of your mandi plate:
- **Plate Detection:** Identifies circular / elliptical serving dishes or thalams.
- **Reference Card Calibration:** Detects an optional standard physical reference card (`REFERENCE_WIDTH_MM = 85.6 mm`, ISO/IEC 7810 ID-1) to calculate `pixels_per_mm`. If no card is present, a geometric plate fallback is used with adjusted confidence.
- **Rice Segmentation (`detect_rice`):** Segments rice within the plate using HSV (golden/yellow hue 8–45) and LAB (high lightness L > 65, warm B > 128) with chicken/meat exclusion.
- **Morphological Cleanup:** Median filtering, opening, closing, and connected-component area filtering to isolate the continuous rice mound.
- **Mound Quantity Model:** Estimates 3D mound height from projected 2D surface area and applies bulk density ($\sim 0.80\text{ g/cm}^3$) to derive estimated rice grams and uncertainty bounds.
- **Mayo Recommendation:** Applies the M.A.N.D.I. algorithm for spice, dryness, and preference factors.

---

### 2. 🥄 Reverse Calculator (Photo ONLY)
**"I have mayonnaise. How much mandi can I eat?"**

The Reverse Calculator **never asks for manual numeric grams entry**. The user provides **only a photograph of the mayonnaise**:

```
📷 MAYONNAISE PHOTO
        ↓
Traditional OpenCV
        ↓
Plate/reference detection
        ↓
Mayonnaise segmentation (inside plate/reference boundary)
        ↓
Mayonnaise area measurement
        ↓
Physical calibration (85.6 mm card or reference plate)
        ↓
Estimated mayonnaise grams (e.g. 150 g [135–165 g, 84% conf])
        ↓
NumPy least-squares linear regression (np.linalg.lstsq)
        ↓
Predicted mandi rice quantity (e.g. ≈ 620 g mandi)
```

#### NumPy Least-Squares Linear Regression
Trained on physical measurements from `data/rice_mayo_calibration.csv`:

$$X = \begin{bmatrix} 1 & \text{mayo}_1 \\ 1 & \text{mayo}_2 \\ \vdots & \vdots \end{bmatrix}, \quad y = \begin{bmatrix} \text{rice}_1 \\ \text{rice}_2 \\ \vdots \end{bmatrix}$$

$$\beta = \text{np.linalg.lstsq}(X, y, \text{rcond=None})[0]$$

$$\text{predicted\_rice} = \beta_0 + \beta_1 \times \text{estimated\_mayo\_grams}$$

---

## 📂 Physical Calibration Datasets

Stored in `data/` and modular so values can be replaced with real kitchen scale measurements:

1. **`data/mayo_calibration.csv`**:
   Maps visual OpenCV features to actual mayonnaise weight:
   `image_id,actual_mayo_grams,mayo_area_pixels,reference_area_pixels,mayo_reference_ratio,physical_mayo_area,mayo_width,mayo_height`

2. **`data/rice_mayo_calibration.csv`**:
   Real physical calibration pairs of mayonnaise grams to edible mandi rice grams:
   `mayo_grams,rice_grams`

---

## 🛠️ Quick Start

### Backend (FastAPI + OpenCV + NumPy)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vite + Vanilla JS)

```bash
cd frontend
npm install
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/calculate` | Manual numeric forward calculation |
| POST | `/api/vision/mandi` | Traditional CV Mandi analysis & Mayo recommendation |
| POST | `/api/vision/reverse` | **Reverse Calculator:** Photo-only OpenCV Mayo estimation + NumPy regression |
| GET | `/api/history/` | View calculation history |
| GET | `/api/history/stats` | View aggregate statistics |

---

## 📐 The M.A.N.D.I. Forward Algorithm

$$\text{base\_mayo} = \frac{\text{rice}}{4}$$

$$\text{recommended} = \text{base} \times \text{spice\_factor} \times \text{dryness\_factor} \times \text{preference\_factor}$$

- **Spice:** mild (0.85) → medium (1.00) → spicy (1.20) → nuclear (1.50)
- **Dryness:** moist (0.85) → normal (1.00) → dry (1.15) → sahara (1.35)
- **Preference:** minimal (0.75) → balanced (1.00) → lover (1.25) → criminal (1.60)
