<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />

# 🍗 MayoMandi 🎯

> **The scientifically unnecessary mandi-to-mayo ratio finder powered by Traditional Computer Vision & Classical NumPy Regression.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Traditional_CV-5C3EE8.svg)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Least_Squares_Regression-013243.svg)](https://numpy.org/)
[![Vite](https://img.shields.io/badge/Vite-Vanilla_JS-646CFF.svg)](https://vitejs.dev/)
[![Mobile Responsive](https://img.shields.io/badge/Mobile-Responsive-success.svg)](#-5-mobile-responsive-web-experience)
[![TinkerHub](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)](https://www.tinkerhub.org/)
[![Useless Projects 3.0](https://img.shields.io/badge/UselessProjects--3.0-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)](https://tinkerhub.org/events/1M8ORET9A1/useless-projects-3.0)

---

## 📋 Basic Details

### Team Name: MayoMandi Team

### Team Members
- **Team Lead:** Deone George ([@deongeorge](https://github.com/deongeorge))

---

### 💡 Project Description
**MayoMandi** is a scientifically unnecessary, technically complete full-stack application that calculates the ideal mayonnaise amount for your mandi plate—or in reverse, photograph your mayonnaise and let classical NumPy least-squares regression predict how much mandi rice you are entitled to consume.

### ❓ The Problem (that doesn't exist)
Nobody agrees on the correct metric ratio of mayonnaise required to accompany authentic mandi rice. Adding too little mayo results in dry, unlubricated rice. Adding too much mayo is culinary criminal behavior. Diners have been forced to guess ratios without rigorous linear algebra, physical calibration markers, or computer vision assistance.

### 💡 The Solution (that nobody asked for)
An end-to-end traditional computer vision pipeline paired with classical NumPy least-squares regression. Users can snap photos on mobile or desktop; OpenCV isolates food boundaries via multi-color space thresholding and metric reference scaling; NumPy predicts edible quantities; and a fully mobile-responsive interface delivers instantaneous gastronomic verdicts.

---
### Google Drive Video Link : https://drive.google.com/file/d/1L2Tohva75o418UeFcd9GkfdK6wYQk2gS/view?usp=sharing
### Live Link : https://useless-project-temp-dusky.vercel.app/

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

### 3. 🧮 Manual Calculator & Uselessness Score Gauge
- Forward numeric calculation using grams of mandi rice.
- Dynamic **Engineering Uselessness Gauge** (0% scientific necessity, 100% engineering effort).
- Complete mathematical breakdown showing each parameter's multiplier impact on final mayonnaise volume.

---

### 4. 📊 Calculation History & Aggregate Analytics
- Automatic persistent logging of every calculation to SQLite (`mayomandi.db`).
- Summary analytics endpoint (`/api/history/stats`) tracking total calculations performed, total imaginary mayo grams consumed, and average mayo per calculation.
- Tabular audit trail showing rice grams, recommended mayo, ratio, spice, dryness, and preference.

---

### 5. 📱 Mobile-First Responsive Web Experience
The entire web interface is optimized for mobile touch devices and all desktop resolutions:
- **Swipeable Navigation Tabs:** Header transforms into a clean horizontal scrollable pill bar on mobile viewports for smooth thumb navigation.
- **2x2 Touch Segmented Controls:** Spice, dryness, and preference pickers adapt into balanced 2x2 grids on screens $\le 640\text{ px}$ with $\ge 46\text{ px}$ touch targets.
- **Mobile Camera Integration:** Direct support for rear-facing / environment cameras (`playsinline`, `facingMode: "environment"`) with responsive frame capture.
- **Horizontally Scrollable History Table:** 7-column calculation log wrapped in a touch-scrolling container with mobile swipe hint indicators.
- **Zero Horizontal Overflow:** Strict layout constraints and dynamic fluid typography (`clamp()`) eliminate horizontal page scrolling on all devices.
- **iOS Safari Auto-Zoom Prevention:** Form inputs maintain a minimum 16px font size to prevent disorienting mobile browser zooming.

---

### 6. ⚖️ Mayo Dispensing Checker & Empirical Calibration
- **Dispensing Checker (`/api/vision/check`):** Verifies whether detected mayonnaise in an image satisfies the required amount from a prior mandi recommendation, outputting `ENOUGH` or `NOT ENOUGH` with exact gram discrepancies.
- **Empirical Calibration API (`/api/vision/calibrate/*`):** Upload real scale samples, extract visual contour features, and fit custom linear models ($y = m \cdot x + c$) using pure NumPy least squares.

---

## 🏗️ System Architecture

```
[ Mobile / Desktop Browser ]
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (Vite + Vanilla JS)                │
│  - Mobile Swipe Nav & 2x2 Touch Segmented Controls          │
│  - Live Webcam / Rear-Facing Camera Stream API              │
│  - Mandi Vision & Reverse Calculator Photo Views            │
│  - Horizontally Scrollable Audit History Table              │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / Multipart Form Data
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend Layer (FastAPI)                   │
│  /api/calculate              /api/reverse-calculate         │
│  /api/vision/mandi           /api/vision/reverse            │
│  /api/vision/mayo            /api/vision/check              │
│  /api/vision/calibrate/*     /api/history/*                 │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│  Traditional Computer Vision │ │ Classical Linear Regression │
│  (OpenCV - No Neural Nets)   │ │ (NumPy np.linalg.lstsq)     │
│  - Multi-Color HSV/LAB       │ │ - Model: rice = β0 + β1*mayo│
│  - Morphological Operations  │ │ - Data: rice_mayo_calib.csv │
│  - ID-1 Card 85.6mm Metric   │ │ - Feature regression model  │
└──────────────┬───────────────┘ └─────────────┬───────────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Persistence & Analytics Engine          │
│  - Stores calculations, ratios, timestamps, uselessness %   │
└─────────────────────────────────────────────────────────────┘
```

---
## Screenshots

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

## 📡 Complete API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/calculate` | Manual numeric forward calculation |
| `POST` | `/api/reverse-calculate` | Manual numeric reverse calculation |
| `POST` | `/api/vision/mandi` | Mandi photo analysis: traditional OpenCV rice segmentation & mayo recommendation |
| `POST` | `/api/vision/reverse` | **Reverse Calculator:** Photo-only OpenCV mayo estimation + NumPy regression |
| `POST` | `/api/vision/mayo` | Direct mayo vision analysis (spoon, plate, or container mode) |
| `POST` | `/api/vision/check` | Mayo amount checker: verifies if dispensed mayo meets required mandi threshold |
| `POST` | `/api/vision/calibrate/sample` | Upload real-world mayo calibration sample with scale weight |
| `GET` | `/api/vision/calibrate/samples` | List current calibration samples and model fit status |
| `POST` | `/api/vision/calibrate/fit` | Fits classical regression model ($y = m \cdot x + c$) via `np.linalg.lstsq` |
| `POST` | `/api/vision/calibrate/reset` | Resets custom calibration samples to empirical baseline model |
| `GET` | `/api/history/` | View historical calculations log |
| `GET` | `/api/history/stats` | View aggregate statistics (total calculations, total mayo, averages) |

---

## 📐 The M.A.N.D.I. Forward Algorithm

$$\text{base\_mayo} = \frac{\text{rice}}{4}$$

$$\text{recommended} = \text{base} \times \text{spice\_factor} \times \text{dryness\_factor} \times \text{preference\_factor}$$

- **Spice:** `mild` (0.85) → `medium` (1.00) → `spicy` (1.20) → `nuclear` (1.50)
- **Dryness:** `moist` (0.85) → `normal` (1.00) → `dry` (1.15) → `sahara` (1.35)
- **Preference:** `minimal` (0.75) → `balanced` (1.00) → `lover` (1.25) → `criminal` (1.60)

---

## 🧪 Running Automated Tests

MayoMandi includes comprehensive automated test suites validating traditional OpenCV segmentation, ID-1 reference card metric calibration, NumPy least-squares regression, and all FastAPI endpoints:

```bash
# Run backend pytest suite (11 passing tests)
cd backend
python3 -m pytest

# Run frontend linter and production build
cd ../frontend
npm run lint
npm run build
```

---

## 👥 Team Contributions

- **Deone George:** Full-stack implementation, traditional computer vision pipeline design (HSV/LAB segmentation, morphological filtering, ID-1 card metric calibration), classical NumPy least-squares regression engine, FastAPI backend architecture, SQLite persistence, Vite/Vanilla JS SPA, and mobile-first responsive design.

---

<div align="center">

Made with ❤️ at **TinkerHub Useless Projects** 

[![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)](https://www.tinkerhub.org/)
[![Static Badge](https://img.shields.io/badge/UselessProjects--3.0-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)](https://tinkerhub.org/events/1M8ORET9A1/useless-projects-3.0)

</div>
