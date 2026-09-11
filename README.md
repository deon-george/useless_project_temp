# FacePay 🎯

A face-recognition based mock UPI payment system built for the TinkerHub Useless Projects hackathon.

## Basic Details

### Team Name: FacePay Team

### Team Members
- Team Lead: Deone George

### Project Description
FacePay is a "useless" but technically complete payment system where you scan a person's face to identify them, then send a mock UPI payment. The face recognition links to a registered user identity, and the payment produces a mock UPI receipt. It solves the ridiculous problem of "what if Venmo required a selfie every time?"

### The Problem (that doesn't exist)
Sending money is too easy. Where's the friction? Where's the biometric theater? We need to make sure the person receiving money actually has a face.

### The Solution (that nobody asked for)
Scan a face → match to registered identity → enter amount → get a mock UPI receipt. Built with InsightFace for embeddings, FastAPI for the backend, React for the frontend, and SQLite for persistence. Works even without GPU/model weights via a deterministic SHA-256 fallback.

## Technical Details

### Technologies/Components Used

**For Software:**
- **Languages:** Python 3.11+, JavaScript (ES2022)
- **Frameworks:** FastAPI, React 18, Vite
- **Libraries:** InsightFace (face detection/embedding), NumPy, SQLite3, Pydantic v2
- **Tools:** Uvicorn, npm, Git

**For Hardware:**
- Webcam (for face capture)
- Any machine with Python 3.11+ and Node 18+

### Implementation

**Architecture:**
- **Client Layer:** React UI served via Vite, communicates with backend over HTTP/JSON
- **API Layer:** FastAPI server routes requests to three services
- **Service Layer:**
  - Face Engine — facial recognition via InsightFace (or deterministic fallback)
  - User Service — manages users in SQLite
  - Payment Service — records mock payments in SQLite
- **Data Flow:** Face Engine output + User Service data → Identity resolution → Payment Service → Payment Receipt

**Installation:**

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

**Run:**

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn app:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Then open http://localhost:5173

### Project Documentation

#### Screenshots
![Face Scan](docs/screenshots/face-scan.png)
*Face scan screen with webcam preview and capture button*

![Payment Form](docs/screenshots/payment-form.png)
*Payment form showing identified user and amount entry*

![Receipt](docs/screenshots/receipt.png)
*Mock UPI payment receipt with transaction reference*

#### Diagrams
![Workflow](docs/diagrams/workflow.png)
*Architecture diagram showing client → API → services → data flow*

### Project Demo

**Video:** [Add your demo video link here]

**What the video demonstrates:**
1. User registration with face capture
2. Face scan identification flow
3. Payment form with amount and payee UPI
4. Mock UPI receipt generation

## Team Contributions
- Deone George: Full-stack implementation, architecture design, face recognition integration, UI/UX

---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)