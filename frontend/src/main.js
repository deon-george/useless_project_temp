// MayoMandi Vanilla JS App with Traditional Computer Vision & Classical NumPy Regression
import heroImage from "./assets/hero.png";

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const API_BASE = configuredApiUrl
  ? `${configuredApiUrl.replace(/\/+$/, "").replace(/\/health$/, "")}/api`
  : "/api";

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

// --- PWA: Service Worker registration ---
function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/sw.js")
        .catch(() => {});
    });
  }
}

// --- PWA: Install prompt handling ---
let deferredPrompt = null;

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  window.MAYOMANDI_INSTALLABLE = true;
  if (isMobile()) {
    renderInstallHint();
  }
});

window.addEventListener("appinstalled", () => {
  deferredPrompt = null;
  window.MAYOMANDI_INSTALLABLE = false;
  hideInstallHint();
});

function isMobile() {
  return /iPhone|iPad|iPod|Android/.test(navigator.userAgent) ||
         (navigator.maxTouchPoints && navigator.maxTouchPoints > 1 && !window.matchMedia("(hover: hover)").matches);
}

window.triggerPwaInstall = function () {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(() => {
      deferredPrompt = null;
    });
  }
};

function renderInstallHint() {
  hideInstallHint();
  const banner = document.createElement("div");
  banner.id = "pwa-install-hint";
  banner.className = "install-hint";
  banner.innerHTML = `
    <button id="pwa-install-btn" class="install-btn">
      <span class="install-icon">📲</span> Install MayoMandi
    </button>
    <button id="pwa-dismiss-hint" class="install-dismiss" aria-label="Dismiss">✕</button>
  `;
  document.body.appendChild(banner);
  document.getElementById("pwa-install-btn").addEventListener("click", () => window.triggerPwaInstall());
  document.getElementById("pwa-dismiss-hint").addEventListener("click", hideInstallHint);
  window.__installHintTimer = setTimeout(hideInstallHint, 15000);
}

function renderIOSInstallHint() {
  hideInstallHint();
  const banner = document.createElement("div");
  banner.id = "pwa-install-hint";
  banner.className = "install-hint ios";
  banner.innerHTML = `
    <div class="ios-instructions">
      <span class="install-icon">📲</span>
      <span>Install MayoMandi: tap <strong>Share</strong> → <strong>Add to Home Screen</strong></span>
    </div>
    <button id="pwa-dismiss-hint" class="install-dismiss" aria-label="Dismiss">✕</button>
  `;
  document.body.appendChild(banner);
  document.getElementById("pwa-dismiss-hint").addEventListener("click", hideInstallHint);
  window.__installHintTimer = setTimeout(hideInstallHint, 20000);
}

window.hideInstallHint = function () {
  if (window.__installHintTimer) {
    clearTimeout(window.__installHintTimer);
    window.__installHintTimer = null;
  }
  const existing = document.getElementById("pwa-install-hint");
  if (existing) existing.remove();
};

// iOS doesn't fire beforeinstallprompt — show manual instructions
if (isMobile() && /iPhone|iPad|iPod/.test(navigator.userAgent)) {
  window.addEventListener("load", () => {
    if (!window.MAYOMANDI_INSTALLABLE && !sessionStorage.getItem("iosInstallDismissed")) {
      renderIOSInstallHint();
    }
  });
}

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
        <nav class="nav-bar">
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
        <img src="${heroImage}" alt="MayoMandi — mandi and mayo" class="mandi-image" />
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
        <div class="estimation-summary-box">
          <div class="est-rice-group">
            <span class="est-sub-label">Estimated Rice Quantity</span>
            <div class="est-main-grams">${intOrFloat(v.estimated_weight_grams)} g</div>
            <div class="est-range-text">Estimated Range: ${v.uncertainty_range_label}</div>
          </div>
          <div class="est-conf-group">
            <span class="confidence-pill ${v.confidence >= 80 ? "confidence-high" : "confidence-med"}">
              Confidence: ${v.confidence}%
            </span>
            <p class="est-card-note">
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

          <div class="result-action-buttons">
            <button class="primary-btn" onclick="resetMandiVision()">
              🔄 Analyze Another Mandi
            </button>
            <a href="#/reverse" class="secondary-btn">
              🥄 Have Mayo? Reverse Calculator
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
          <div class="card reverse-upload-card">
            <div class="reverse-hero-icon">🥄</div>
            <h3 class="reverse-title">Photograph your mayo</h3>
            <p class="reverse-desc">
              Place your mayonnaise on the<br><strong>MayoMandi reference plate/card</strong>.
            </p>

            ${r.previewUrl ? `
              <div class="reverse-preview-wrapper">
                <img src="${r.previewUrl}" alt="Selected Mayo Preview" />
              </div>
            ` : ""}

            <div class="vision-actions">
              <label class="primary-btn file-upload-btn">
                📷 Upload Mayo Photo
                <input type="file" id="reverse-file-input" accept="image/*" style="display: none;" onchange="handleReverseFileSelect(event)" />
              </label>
              <button type="button" class="secondary-btn camera-open-btn" onclick="toggleReverseCamera(true)">
                📸 Use Camera
              </button>
            </div>

            ${r.selectedFile ? `
              <div class="reverse-submit-container">
                <button type="button" class="primary-btn analyze-action-btn" onclick="executeReverseAnalysis()">
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
        <div class="reverse-detected-box">
          <div class="reverse-detected-title">
            🥄 MAYO DETECTED
          </div>
          <div class="reverse-detected-sub">Estimated:</div>
          <div class="reverse-mayo-val">
            ${Math.round(r.estimated_mayo_grams)} g
          </div>
          <div class="reverse-detected-range">
            Estimated range: <strong>${r.uncertainty_range_label}</strong>
          </div>
          <div>
            <span class="confidence-pill ${r.confidence >= 80 ? "confidence-high" : "confidence-med"}">
              Confidence: ${r.confidence}%
            </span>
          </div>
        </div>

        <div class="dashed-divider"></div>

        <!-- YOU CAN EAT SECTION -->
        <div class="reverse-eat-box">
          <div class="reverse-eat-title">
            🍚 YOU CAN EAT
          </div>
          <div class="reverse-eat-val">
            ≈ ${Math.round(r.predicted_rice_grams)} g mandi
          </div>
        </div>

        <div class="dashed-divider"></div>

        <!-- METHOD & HUMOROUS MESSAGE -->
        <div style="margin: 16px 0; font-size: 0.95rem; color: var(--text); line-height: 1.5;">
          <strong>Method:</strong><br />
          <span>${r.method}</span>
        </div>

        <div class="quote" style="font-size: 1.05rem; font-weight: 600; margin: 18px 0;">
          "${r.message}"
        </div>

        <div style="margin-top: 24px;">
          <button type="button" class="primary-btn full-width-mobile" onclick="resetReverseCalculator()">
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
      <div class="stats-summary-grid">
        <div class="stat-pill-card">
          <span class="stat-pill-label">Total Calculations</span>
          <span class="stat-pill-val">${state.stats.total_calculations}</span>
        </div>
        <div class="stat-pill-card">
          <span class="stat-pill-label">Total Imaginary Mayo</span>
          <span class="stat-pill-val">${state.stats.total_imaginary_mayo_grams} g</span>
        </div>
        <div class="stat-pill-card">
          <span class="stat-pill-label">Average Mayo / Calc</span>
          <span class="stat-pill-val">${state.stats.average_mayo_per_calc} g</span>
        </div>
      </div>
    ` : "";

    const html = `
      <div class="page history">
        <div class="card wide">
          <h2>📊 Mayo History</h2>
          <p class="subtitle">Complete audit trail of all mandi and mayo ratio calculations</p>
          ${statsHtml}
          ${state.history.length === 0
            ? "<p style='text-align:center; padding: 24px; color:var(--text);'>No history yet. Calculate some mayo!</p>"
            : `
            <div class="history-table-container">
              <div class="mobile-table-hint">👉 Swipe horizontally to view all calculation columns</div>
              <div class="history-table-wrapper">
                <table class="history-table">
                  <thead>
                    <tr>
                      <th>Rice (g)</th><th>Mayo (g)</th><th>Ratio</th><th>Uselessness</th><th>Spice</th><th>Dryness</th><th>Preference</th>
                    </tr>
                  </thead>
                  <tbody>${rows}</tbody>
                </table>
              </div>
            </div>
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
  registerServiceWorker();
  render();
  window.addEventListener("hashchange", () => {
    stopCamera();
    render();
  });
  window.addEventListener("popstate", render);
}

init();
