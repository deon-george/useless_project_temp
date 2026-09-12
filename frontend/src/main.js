// MayoMandi Vanilla JS App with Traditional Computer Vision & Classical NumPy Regression
const API_BASE = "/api";

// --- API Functions ---
async function apiCalculate(data) {
  const res = await fetch(`${API_BASE}/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Calculation failed");
  return res.json();
}

async function apiReverseVision(formData) {
  const res = await fetch(`${API_BASE}/vision/reverse`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Reverse Mayo Vision analysis failed");
  }
  return res.json();
}

async function apiAnalyzeMandi(formData) {
  const res = await fetch(`${API_BASE}/vision/mandi`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Mandi Vision processing failed");
  }
  return res.json();
}

async function apiHistory() {
  const res = await fetch(`${API_BASE}/history/`);
  if (!res.ok) throw new Error("History fetch failed");
  return res.json();
}

async function apiStats() {
  const res = await fetch(`${API_BASE}/history/stats`);
  if (!res.ok) throw new Error("Stats fetch failed");
  return res.json();
}

// --- Global Application State ---
let state = {
  page: "home",

  // Mandi Vision State
  mandiVision: {
    loading: false,
    error: null,
    result: null,
    cameraActive: false,
  },

  // Reverse Calculator (Photo ONLY) State
  reverse: {
    loading: false,
    error: null,
    selectedFile: null,
    previewUrl: null,
    result: null,
    cameraActive: false,
  },

  // Manual Calculator State
  riceGrams: "750",
  spice: "spicy",
  dryness: "dry",
  preference: "lover",
  result: null,

  history: [],
  stats: null,
};

let activeCameraStream = null;

// --- Camera Streaming Utilities ---
async function startCamera(videoElementId) {
  try {
    if (activeCameraStream) {
      stopCamera();
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    activeCameraStream = stream;
    const video = document.getElementById(videoElementId);
    if (video) {
      video.srcObject = stream;
      video.play();
    }
  } catch (err) {
    alert("Camera access denied or unavailable: " + err.message);
  }
}

function stopCamera() {
  if (activeCameraStream) {
    activeCameraStream.getTracks().forEach((t) => t.stop());
    activeCameraStream = null;
  }
}

function captureFrameBlob(videoElementId) {
  return new Promise((resolve, reject) => {
    const video = document.getElementById(videoElementId);
    if (!video || !video.videoWidth) {
      return reject(new Error("Camera feed is not ready."));
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("Failed to capture image frame."));
    }, "image/jpeg", 0.9);
  });
}

// --- Router and View Renderer ---
function getRoute() {
  const hash = window.location.hash || "#/";
  return hash.substring(2).split("/")[0] || "home";
}

function setStateAndRender(newState) {
  Object.assign(state, newState);
  render();
}

function renderFrame(route, contentHtml) {
  const activeNav = (path) => (path === route ? "active" : "");
  return `
    <div class="app">
      <header class="site-header">
        <a href="#/" class="logo"><span>🍗</span> Mayo<em>Mandi</em></a>
        <nav>
          <a href="#/" class="${activeNav("home")}">Home</a>
          <a href="#/mandi-vision" class="${activeNav("mandi-vision")}">🍗 Mandi Vision</a>
          <a href="#/reverse" class="${activeNav("reverse")}">🥄 Reverse Calculator</a>
          <a href="#/calculator" class="${activeNav("calculator")}">🧮 Calculator</a>
          <a href="#/history" class="${activeNav("history")}">📊 History</a>
        </nav>
      </header>
      ${contentHtml}
      <footer>
        <p>Made with 🥄 and traditional <strong>OpenCV Computer Vision + NumPy Least-Squares Regression</strong> (No neural networks).</p>
      </footer>
    </div>
  `;
}

// ==============================================
// 1. HOME VIEW
// ==============================================
function renderHome() {
  return `
    <section class="hero">
      <div class="blob one"></div>
      <div class="blob two"></div>
      <div class="hero-text">
        <span class="eyebrow">TRADITIONAL COMPUTER VISION</span>
        <h1>🍗 Mayo<em>MANDI</em></h1>
        <div class="title-wave"></div>
        <p class="subtitle">The scientifically unnecessary mandi-to-mayo ratio finder powered by traditional computer vision and classical NumPy regression.</p>
        <div class="steps">
          <div class="step"><span class="step-icon">📸</span> Mandi Vision</div>
          <div class="step"><span class="step-icon">🥄</span> Reverse Calculator</div>
          <div class="step"><span class="step-icon">📐</span> NumPy Regression</div>
        </div>
        <div class="hero-actions">
          <a href="#/mandi-vision" class="primary-btn">📸 Mandi Vision</a>
          <a href="#/reverse" class="secondary-btn">🥄 Reverse Calculator</a>
        </div>
      </div>
      <div class="hero-art">
        <img src="/src/assets/hero.png" alt="MayoMandi — mandi and mayo" class="mandi-image" />
        <div class="brush"></div>
        <div class="brush-text">Mandi<br>+<br>Mayo<br>= Happiness ❤️</div>
        <div class="annotation one">Traditional CV<br>Rice Estimation! <span class="annotation-arrow">↘</span></div>
        <div class="annotation two"><span class="annotation-arrow">↗</span><br>Photo-to-Mandi<br>NumPy lstsq!</div>
      </div>
    </section>

    <section class="quick-start">
      <h2>Vision & Calculation Suite</h2>
      <p>Select a tool below to begin your traditional CV analysis.</p>
      <div class="features-grid">
        <a href="#/mandi-vision" class="feature-card primary">
          <div class="tool-icon">📸</div>
          <h2>Mandi Vision</h2>
          <p>Photograph your mandi plate. Traditional OpenCV segments rice and estimates recommended mayo.</p>
          <div class="card-bottom"><span>CV Powered</span><div class="arrow">→</div></div>
        </a>

        <a href="#/reverse" class="feature-card primary">
          <div class="tool-icon">🥄</div>
          <h2>Reverse Calculator</h2>
          <p>"I have mayonnaise. How much mandi can I eat?" Photograph mayo only — NumPy least-squares predicts rice.</p>
          <div class="card-bottom"><span>Photo Only</span><div class="arrow">→</div></div>
        </a>

        <a href="#/calculator" class="feature-card">
          <div class="tool-icon">🧮</div>
          <h2>Manual Calculator</h2>
          <p>Input rice grams manually to calculate mayo and uselessness score.</p>
          <div class="card-bottom"><span>Numeric</span><div class="arrow">→</div></div>
        </a>

        <a href="#/history" class="feature-card">
          <div class="tool-icon">📊</div>
          <h2>Calculation History</h2>
          <p>View previous calculations, aggregate consumption, and stats.</p>
          <div class="card-bottom"><span>History</span><div class="arrow">→</div></div>
        </a>
      </div>
    </section>
  `;
}

// ==============================================
// 2. FEATURE 1 — MANDI VISION VIEW
// ==============================================
function renderMandiVision() {
  const spiceOptions = ["mild", "medium", "spicy", "nuclear"];
  const drynessOptions = ["moist", "normal", "dry", "sahara"];
  const prefOptions = ["minimal", "balanced", "lover", "criminal"];

  const v = state.mandiVision;

  if (v.result) {
    return renderMandiVisionResult(v.result);
  }

  return `
    <div class="page">
      <div class="card wide" style="max-width: 720px;">
        <h2>📸 Mandi Vision (Traditional CV)</h2>
        <p class="subtitle" style="font-size: 1.25rem; font-weight: 700; color: var(--accent-dark); margin-bottom: 4px;">
          How much mandi do you have?
        </p>
        <p style="text-align: center; color: var(--text); margin-top: 0;">
          Take a clear photo of your mandi.
        </p>

        <div class="limitation-banner">
          <span style="font-size: 1.5rem;">⚠️</span>
          <div>
            <strong>Important Scientific Limitation:</strong> A normal 2D photograph cannot directly measure exact food mass.
            MayoMandi uses traditional OpenCV color-space segmentation (HSV/LAB), morphological filtering, and empirical geometric mound models to estimate rice quantity.
            All estimates include an uncertainty range and confidence interval.
          </div>
        </div>

        <div class="instructions-card">
          <h4>📋 Instructions for Better Estimation</h4>
          <ul>
            <li>Keep the whole plate visible in the frame</li>
            <li>Use good, even lighting (avoid harsh directional shadows)</li>
            <li>Avoid extreme camera angles</li>
            <li>Keep the camera approximately <strong>45° above the plate</strong></li>
            <li><strong>Place the MayoMandi reference card (85.6 mm) beside the plate</strong> for calibrated real-world dimensions</li>
          </ul>
        </div>

        <form id="mandi-vision-form" class="input-form">
          <div class="field">
            <label>Spice level</label>
            <div class="segmented">
              ${spiceOptions.map((s) => `
                <button type="button" class="${state.spice === s ? "active" : ""}" onclick="setStateAndRender({spice:'${s}'})">
                  ${s === "mild" ? "🌶️" : s === "medium" ? "🌶️🌶️" : s === "spicy" ? "🌶️🌶️🌶️" : "☠️"} ${s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          <div class="field">
            <label>Dryness</label>
            <div class="segmented">
              ${drynessOptions.map((d) => `
                <button type="button" class="${state.dryness === d ? "active" : ""}" onclick="setStateAndRender({dryness:'${d}'})">
                  ${d === "moist" ? "💧" : d === "normal" ? "👌" : d === "dry" ? "🏜️" : "🏜️☀️"} ${d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          <div class="field">
            <label>Mayo addiction</label>
            <div class="segmented">
              ${prefOptions.map((p) => `
                <button type="button" class="${state.preference === p ? "active" : ""}" onclick="setStateAndRender({preference:'${p}'})">
                  ${p === "minimal" ? "🥄" : p === "balanced" ? "⚖️" : p === "lover" ? "🥄🥄" : "💀"} ${p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          ${v.cameraActive ? `
            <div class="camera-box">
              <video id="mandi-video" class="camera-video" playsinline autoplay></video>
              <div class="camera-controls">
                <button type="button" class="primary-btn" onclick="captureAndAnalyzeMandi()">📸 Capture Photo</button>
                <button type="button" class="secondary-btn" onclick="toggleMandiCamera(false)">Close Camera</button>
              </div>
            </div>
          ` : `
            <div class="vision-actions">
              <label class="primary-btn" style="cursor:pointer;">
                📁 Upload Mandi Image
                <input type="file" id="mandi-file-input" accept="image/*" style="display:none;" onchange="handleMandiFileUpload(event)" />
              </label>
              <button type="button" class="secondary-btn" onclick="toggleMandiCamera(true)">
                📷 Use Camera
              </button>
            </div>
          `}

          ${v.loading ? `
            <div style="text-align:center; padding: 20px;">
              <div class="loading-spinner"></div>
              <p><strong>Running Traditional OpenCV Computer Vision...</strong></p>
              <small style="color:var(--text)">Plate contour extraction → HSV/LAB rice segmentation → Morphological cleanup → Calibration...</small>
            </div>
          ` : ""}

          ${v.error ? `
            <div class="verdict" style="background:#fee2e2; color:#b91c1c;">
              ${v.error}
            </div>
          ` : ""}
        </form>
      </div>
    </div>
  `;
}

function renderMandiVisionResult(result) {
  const v = result.vision;
  const rec = result.recommendation;
  const cal = v.calibration;
  const m = v.measurements;

  return `
    <div class="page">
      <div class="card wide" style="max-width: 780px;">
        <h2>🍗 Mandi Vision Analysis Complete</h2>
        <p class="subtitle">Traditional OpenCV plate segmentation & rice estimation</p>

        <!-- Traditional CV Debug Overlay -->
        ${v.overlay_base64 ? `
          <div class="cv-overlay-box">
            <span class="cv-overlay-badge">OpenCV Traditional CV</span>
            <img src="data:image/jpeg;base64,${v.overlay_base64}" alt="Mandi OpenCV Overlay" />
          </div>
        ` : ""}

        <!-- Estimation Card -->
        <div style="display:flex; justify-content:space-around; align-items:center; flex-wrap:wrap; background:var(--bg); border:1px solid var(--border); border-radius:12px; padding:18px; margin:14px 0;">
          <div style="text-align:center;">
            <span style="font-size:0.85rem; color:var(--text); text-transform:uppercase; font-weight:700;">Estimated Rice Quantity</span>
            <div style="font-size:2.8rem; font-weight:800; color:var(--accent-dark);">${intOrFloat(v.estimated_weight_grams)} g</div>
            <div style="font-size:0.95rem; font-weight:600; color:var(--text-h);">Estimated Range: ${v.uncertainty_range_label}</div>
          </div>
          <div style="text-align:center; margin-top:8px;">
            <span class="confidence-pill ${v.confidence >= 80 ? "confidence-high" : "confidence-med"}">
              Confidence: ${v.confidence}%
            </span>
            <p style="font-size:0.82rem; color:var(--text); margin:6px 0 0;">
              ${cal.reference_card_detected ? "💳 Physical card calibrated (85.6mm)" : "⚠️ Fallback plate geometry"}
            </p>
          </div>
        </div>

        <!-- Metric Details -->
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-label">Rice / Plate Ratio</span>
            <span class="metric-val">${(m.rice_plate_ratio * 100).toFixed(1)}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Rice Area</span>
            <span class="metric-val">${Math.round(m.rice_area_pixels).toLocaleString()} px</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Solidity</span>
            <span class="metric-val">${m.solidity}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Physical Area</span>
            <span class="metric-val">${m.calibrated_physical_area_cm2 ? m.calibrated_physical_area_cm2 + " cm²" : "N/A"}</span>
          </div>
        </div>

        <!-- Mayo Recommendation Section -->
        <div class="card result-card" style="margin-top:20px; box-shadow:none; border:2px dashed var(--accent);">
          <h3>Recommended Mayonnaise</h3>
          <div class="result-mayo">
            <span class="result-emoji">🥄</span>
            <span class="result-value">${rec.recommended_mayo_grams} g</span>
            <span class="result-label">≈ ${rec.tablespoons} Tablespoons (Ratio ${rec.ratio})</span>
          </div>
          <div class="verdict" style="color:${rec.verdict_color === 'red' ? '#ef4444' : '#16a34a'};">
            ${rec.verdict}
          </div>

          <div style="margin-top:16px; display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
            <button class="primary-btn" onclick="resetMandiVision()">
              🔄 Analyze Another Mandi
            </button>
            <a href="#/reverse" class="secondary-btn">
              🥄 Have Mayo? Go to Reverse Calculator
            </a>
          </div>
        </div>
      </div>
    </div>
  `;
}

function intOrFloat(n) {
  return Number.isInteger(n) ? n : n.toFixed(1);
}

function toggleMandiCamera(activate) {
  state.mandiVision.cameraActive = activate;
  render();
  if (activate) {
    setTimeout(() => startCamera("mandi-video"), 100);
  } else {
    stopCamera();
  }
}

async function captureAndAnalyzeMandi() {
  try {
    const blob = await captureFrameBlob("mandi-video");
    stopCamera();
    state.mandiVision.cameraActive = false;
    await executeMandiVision(blob);
  } catch (err) {
    alert("Camera capture failed: " + err.message);
  }
}

async function handleMandiFileUpload(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  await executeMandiVision(file);
}

async function executeMandiVision(fileOrBlob) {
  state.mandiVision.loading = true;
  state.mandiVision.error = null;
  render();

  try {
    const formData = new FormData();
    formData.append("file", fileOrBlob, "mandi.jpg");
    formData.append("spice_level", state.spice);
    formData.append("dryness", state.dryness);
    formData.append("mayo_preference", state.preference);

    const res = await apiAnalyzeMandi(formData);
    state.mandiVision.result = res;
  } catch (err) {
    state.mandiVision.error = err.message || "Failed to analyze mandi image.";
  } finally {
    state.mandiVision.loading = false;
    render();
  }
}

function resetMandiVision() {
  state.mandiVision.result = null;
  state.mandiVision.error = null;
  state.mandiVision.cameraActive = false;
  stopCamera();
  render();
}

// ==============================================
// 3. FEATURE 2 — REVERSE CALCULATOR (PHOTO ONLY)
// ==============================================
function renderReverse() {
  const r = state.reverse;

  if (r.result) {
    return renderReverseResult(r.result);
  }

  return `
    <div class="page">
      <div class="card wide" style="max-width: 680px;">
        <h2>Reverse Calculator</h2>
        <p class="subtitle" style="font-size: 1.25rem; font-weight: 700; color: var(--accent-dark); margin-bottom: 20px;">
          "I have mayonnaise.<br>How much mandi can I eat?"
        </p>

        ${r.cameraActive ? `
          <div class="camera-box">
            <video id="reverse-video" class="camera-video" playsinline autoplay></video>
            <div class="camera-controls">
              <button type="button" class="primary-btn" onclick="captureReverseFrame()">📸 Capture Mayo</button>
              <button type="button" class="secondary-btn" onclick="toggleReverseCamera(false)">Close Camera</button>
            </div>
          </div>
        ` : `
          <!-- The exact container requested by the user -->
          <div class="card" style="border: 2px dashed var(--accent); background: var(--bg-alt); text-align: center; padding: 40px 24px; box-shadow: none; margin: 16px auto;">
            <div style="font-size: 3.6rem; margin-bottom: 8px;">🥄</div>
            <h3 style="font-size: 1.45rem; margin: 0 0 10px; color: var(--text-h);">Photograph your mayo</h3>
            <p style="color: var(--text); font-size: 1.05rem; margin: 0 0 24px; line-height: 1.5;">
              Place your mayonnaise on the<br><strong>MayoMandi reference plate/card</strong>.
            </p>

            ${r.previewUrl ? `
              <div style="margin: 16px auto; max-width: 320px; border-radius: 10px; overflow: hidden; border: 2px solid var(--border);">
                <img src="${r.previewUrl}" alt="Selected Mayo Preview" style="width: 100%; display: block;" />
              </div>
            ` : ""}

            <div class="vision-actions" style="justify-content: center; gap: 12px; margin-top: 14px;">
              <label class="primary-btn" style="cursor: pointer; padding: 13px 24px; font-size: 1.05rem;">
                📷 Upload Mayo Photo
                <input type="file" id="reverse-file-input" accept="image/*" style="display: none;" onchange="handleReverseFileSelect(event)" />
              </label>
              <button type="button" class="secondary-btn" style="padding: 12px 20px;" onclick="toggleReverseCamera(true)">
                📸 Use Camera
              </button>
            </div>

            ${r.selectedFile ? `
              <div style="margin-top: 22px;">
                <button type="button" class="primary-btn" style="background: #16a34a; font-size: 1.15rem; padding: 14px 32px; box-shadow: 0 4px 14px rgba(22, 163, 74, 0.3);" onclick="executeReverseAnalysis()">
                  🥄 ANALYZE MY MAYO
                </button>
              </div>
            ` : ""}
          </div>
        `}

        ${r.loading ? `
          <div style="text-align: center; padding: 24px;">
            <div class="loading-spinner"></div>
            <p style="font-size: 1.1rem; font-weight: 700; color: var(--text-h); margin-bottom: 6px;">
              Analyzing mayonnaise photograph...
            </p>
            <p style="color: var(--text); font-size: 0.9rem; margin: 0;">
              Plate/reference detection → HSV/LAB mayo segmentation → Area measurement → <strong>NumPy least-squares regression</strong>
            </p>
          </div>
        ` : ""}

        ${r.error ? `
          <div class="verdict" style="background: #fee2e2; color: #b91c1c; margin-top: 16px;">
            ${r.error}
          </div>
        ` : ""}
      </div>
    </div>
  `;
}

function renderReverseResult(r) {
  return `
    <div class="page">
      <div class="card result-card" style="max-width: 680px; text-align: center;">
        <h2 style="letter-spacing: 0.5px; font-size: 1.5rem; margin-bottom: 16px; color: var(--text-h);">
          REVERSE CALCULATION COMPLETE
        </h2>

        ${r.overlay_base64 ? `
          <div class="cv-overlay-box">
            <span class="cv-overlay-badge">OpenCV Traditional CV</span>
            <img src="data:image/jpeg;base64,${r.overlay_base64}" alt="Reverse Mayo CV Overlay" />
          </div>
        ` : ""}

        <!-- MAYO DETECTED SECTION -->
        <div style="margin: 20px 0; padding: 18px; background: var(--bg); border-radius: 12px; border: 1px solid var(--border);">
          <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-h); margin-bottom: 6px;">
            🥄 MAYO DETECTED
          </div>
          <div style="font-size: 0.88rem; color: var(--text); font-weight: 600;">Estimated:</div>
          <div style="font-size: 2.8rem; font-weight: 800; color: var(--accent-dark); line-height: 1.1; margin: 4px 0;">
            ${Math.round(r.estimated_mayo_grams)} g
          </div>
          <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-h); margin: 6px 0;">
            Estimated range: <strong>${r.uncertainty_range_label}</strong>
          </div>
          <div>
            <span class="confidence-pill ${r.confidence >= 80 ? "confidence-high" : "confidence-med"}">
              Confidence: ${r.confidence}%
            </span>
          </div>
        </div>

        <div style="border-top: 2px dashed var(--border); margin: 24px auto; width: 85%;"></div>

        <!-- YOU CAN EAT SECTION -->
        <div style="margin: 20px 0; padding: 22px; background: #f0fdf4; border-radius: 14px; border: 2px solid #86efac;">
          <div style="font-size: 1.25rem; font-weight: 800; color: #166534; margin-bottom: 6px;">
            🍚 YOU CAN EAT
          </div>
          <div style="font-size: 3.2rem; font-weight: 900; color: #15803d; line-height: 1.1;">
            ≈ ${Math.round(r.predicted_rice_grams)} g mandi
          </div>
        </div>

        <div style="border-top: 2px dashed var(--border); margin: 24px auto; width: 85%;"></div>

        <!-- METHOD & HUMOROUS MESSAGE -->
        <div style="margin: 16px 0; font-size: 0.95rem; color: var(--text); line-height: 1.5;">
          <strong>Method:</strong><br />
          <span>${r.method}</span>
        </div>

        <div class="quote" style="font-size: 1.05rem; font-weight: 600; margin: 18px 0;">
          "${r.message}"
        </div>

        <div style="margin-top: 24px;">
          <button type="button" class="primary-btn" onclick="resetReverseCalculator()">
            📷 Photograph Another Mayo
          </button>
        </div>
      </div>
    </div>
  `;
}

function toggleReverseCamera(activate) {
  state.reverse.cameraActive = activate;
  render();
  if (activate) {
    setTimeout(() => startCamera("reverse-video"), 100);
  } else {
    stopCamera();
  }
}

async function captureReverseFrame() {
  try {
    const blob = await captureFrameBlob("reverse-video");
    stopCamera();
    state.reverse.cameraActive = false;
    state.reverse.selectedFile = blob;
    state.reverse.previewUrl = URL.createObjectURL(blob);
    render();
  } catch (err) {
    alert("Camera capture failed: " + err.message);
  }
}

function handleReverseFileSelect(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  state.reverse.selectedFile = file;
  state.reverse.previewUrl = URL.createObjectURL(file);
  render();
}

async function executeReverseAnalysis() {
  if (!state.reverse.selectedFile) return;

  state.reverse.loading = true;
  state.reverse.error = null;
  render();

  try {
    const formData = new FormData();
    formData.append("file", state.reverse.selectedFile, "mayo.jpg");

    const res = await apiReverseVision(formData);
    state.reverse.result = res;
  } catch (err) {
    state.reverse.error = err.message || "Failed to analyze mayonnaise photograph.";
  } finally {
    state.reverse.loading = false;
    render();
  }
}

function resetReverseCalculator() {
  state.reverse.selectedFile = null;
  state.reverse.previewUrl = null;
  state.reverse.result = null;
  state.reverse.error = null;
  state.reverse.cameraActive = false;
  stopCamera();
  render();
}

// ==============================================
// 4. MANUAL CALCULATOR VIEW
// ==============================================
function renderCalculator() {
  const spiceOptions = ["mild", "medium", "spicy", "nuclear"];
  const drynessOptions = ["moist", "normal", "dry", "sahara"];
  const prefOptions = ["minimal", "balanced", "lover", "criminal"];

  if (state.result) {
    return renderResultCard(state.result);
  }

  return `
    <div class="page calculator">
      <div class="card">
        <h2>🍗 MayoMandi Manual Calculator</h2>
        <p class="subtitle">How much mandi do you have?</p>
        <form id="calc-form" class="input-form">
          <div class="field">
            <label>Rice quantity (grams)</label>
            <input type="number" id="riceGrams" class="number-input" min="1" step="1" value="${state.riceGrams}" />
          </div>

          <div class="field">
            <label>Spice level</label>
            <div class="segmented">
              ${spiceOptions.map((s) => `
                <button type="button" class="${state.spice === s ? "active" : ""}" onclick="setStateAndRender({spice:'${s}'})">
                  ${s === "mild" ? "🌶️" : s === "medium" ? "🌶️🌶️" : s === "spicy" ? "🌶️🌶️🌶️" : "☠️"} ${s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          <div class="field">
            <label>Dryness</label>
            <div class="segmented">
              ${drynessOptions.map((d) => `
                <button type="button" class="${state.dryness === d ? "active" : ""}" onclick="setStateAndRender({dryness:'${d}'})">
                  ${d === "moist" ? "💧" : d === "normal" ? "👌" : d === "dry" ? "🏜️" : "🏜️☀️"} ${d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          <div class="field">
            <label>Mayo addiction</label>
            <div class="segmented">
              ${prefOptions.map((p) => `
                <button type="button" class="${state.preference === p ? "active" : ""}" onclick="setStateAndRender({preference:'${p}'})">
                  ${p === "minimal" ? "🥄" : p === "balanced" ? "⚖️" : p === "lover" ? "🥄🥄" : "💀"} ${p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              `).join("")}
            </div>
          </div>

          <button type="button" class="primary-btn" onclick="handleCalculate()">🥄 CALCULATE</button>
        </form>
      </div>
    </div>
  `;
}

function renderResultCard(result) {
  const uselessness = result.uselessness_score;
  const filled = Math.round((uselessness / 100) * 20);
  const empty = 20 - filled;
  const gaugeColor = uselessness > 80 ? "#ef4444" : uselessness > 50 ? "#f59e0b" : "#22c55e";

  const breakdownHtml = result.breakdown.map((item) => `
    <div class="breakdown-row">
      <span>${item.step}</span>
      <span>${item.amount > 0 ? "+" : ""}${item.amount} ${item.unit}</span>
    </div>
  `).join("");

  return `
    <div class="page calculator">
      <div class="card result-card">
        <h2>MAYO ANALYSIS COMPLETE</h2>
        <div class="result-main">
          <div class="result-mayo">
            <span class="result-emoji">🥄</span>
            <span class="result-value">${result.recommended_mayo_grams} g</span>
            <span class="result-label">RECOMMENDED MAYO</span>
          </div>
        </div>

        <div class="result-stats">
          <div class="stat"><span>Ratio:</span> <strong>${result.ratio}</strong></div>
          <div class="stat"><span>Tablespoons:</span> <strong>≈ ${result.tablespoons} tbsp</strong></div>
        </div>

        <div class="verdict" style="color:${gaugeColor}">
          ${result.verdict}
        </div>

        <div class="uselessness-gauge">
          <label>Uselessness Score</label>
          <div class="gauge-bar">
            <div class="gauge-fill" style="width:${uselessness}%;background-color:${gaugeColor}"></div>
            <span class="gauge-text">
              ${"█".repeat(filled)}${"░".repeat(empty)} ${uselessness}%
            </span>
          </div>
          <small>Scientific necessity: 0%</small>
          <small>Engineering effort: ${"█".repeat(20)} 100%</small>
        </div>

        <div class="breakdown">
          <h3>WHY?</h3>
          ${breakdownHtml}
        </div>

        <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-top:16px;">
          <button onclick="setStateAndRender({result:null})" class="secondary-btn">← Calculate Again</button>
        </div>
      </div>
    </div>
  `;
}

async function handleCalculate() {
  const riceInput = document.getElementById("riceGrams");
  state.riceGrams = riceInput.value;

  try {
    const res = await apiCalculate({
      rice_grams: parseFloat(state.riceGrams),
      spice_level: state.spice,
      dryness: state.dryness,
      mayo_preference: state.preference,
    });
    state.result = res;
    render();
  } catch (err) {
    alert("Failed to calculate! Is the backend running? " + err.message);
  }
}

// ==============================================
// 5. HISTORY VIEW
// ==============================================
function renderHistory() {
  return `
    <div class="page history">
      <div class="card">
        <h2>📊 Mayo History</h2>
        <p>Loading history…</p>
      </div>
    </div>
  `;
}

async function renderHistoryContent() {
  try {
    const [hist, stats] = await Promise.all([apiHistory(), apiStats()]);
    state.history = hist;
    state.stats = stats;
  } catch (err) {
    console.error("Failed to load history:", err);
  }

  const route = getRoute();
  if (route === "history") {
    const rows = state.history.map((row) => `
      <tr>
        <td>${row.rice_grams}</td>
        <td>${row.recommended_mayo_grams}</td>
        <td>${row.ratio}</td>
        <td>${row.uselessness_score}%</td>
        <td>${row.spice_level}</td>
        <td>${row.dryness}</td>
        <td>${row.mayo_preference}</td>
      </tr>
    `).join("");

    const statsHtml = state.stats ? `
      <div class="stats-summary">
        <p><strong>Total calculations:</strong> ${state.stats.total_calculations}</p>
        <p><strong>Total imaginary mayo:</strong> ${state.stats.total_imaginary_mayo_grams} g</p>
        <p><strong>Average mayo per calc:</strong> ${state.stats.average_mayo_per_calc} g</p>
      </div>
    ` : "";

    const html = `
      <div class="page history">
        <div class="card">
          <h2>📊 Mayo History</h2>
          ${statsHtml}
          ${state.history.length === 0
            ? "<p>No history yet. Calculate some mayo!</p>"
            : `
            <table class="history-table">
              <thead>
                <tr>
                  <th>Rice (g)</th><th>Mayo (g)</th><th>Ratio</th><th>Uselessness</th><th>Spice</th><th>Dryness</th><th>Preference</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
            `
          }
        </div>
      </div>
    `;
    document.getElementById("app").innerHTML = renderFrame("history", html);
  }
}

// ==============================================
// MAIN ROUTING
// ==============================================
function render() {
  const route = getRoute();
  state.page = route;

  let contentHtml = "";
  switch (route) {
    case "":
    case "home":
      contentHtml = renderHome();
      break;
    case "mandi-vision":
      contentHtml = renderMandiVision();
      break;
    case "reverse":
      contentHtml = renderReverse();
      break;
    case "calculator":
      contentHtml = renderCalculator();
      break;
    case "history":
      contentHtml = renderHistory();
      break;
    default:
      contentHtml = renderHome();
  }

  document.getElementById("app").innerHTML = renderFrame(route, contentHtml);

  if (route === "history") {
    renderHistoryContent();
  }
}

// Global window attachments for inline handlers
window.setStateAndRender = setStateAndRender;
window.handleCalculate = handleCalculate;
window.toggleMandiCamera = toggleMandiCamera;
window.captureAndAnalyzeMandi = captureAndAnalyzeMandi;
window.handleMandiFileUpload = handleMandiFileUpload;
window.resetMandiVision = resetMandiVision;
window.toggleReverseCamera = toggleReverseCamera;
window.captureReverseFrame = captureReverseFrame;
window.handleReverseFileSelect = handleReverseFileSelect;
window.executeReverseAnalysis = executeReverseAnalysis;
window.resetReverseCalculator = resetReverseCalculator;

function init() {
  render();
  window.addEventListener("hashchange", () => {
    stopCamera();
    render();
  });
  window.addEventListener("popstate", render);
}

init();
