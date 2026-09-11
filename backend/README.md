FacePay Backend

Overview
- FastAPI backend for face-based registration, identification, and mock UPI payments.
- Uses SQLite for persistence and InsightFace for face embeddings when available.
- Falls back to a deterministic embedding stub derived from image bytes when InsightFace/model weights are unavailable.

Endpoints
- POST /api/register
  - Query/body: name, upi_id
  - Optional multipart: image_file
  - Returns saved user id and identifiers.

- POST /api/identify
  - Multipart: image_file
  - Returns matched user if similarity exceeds threshold.

- POST /api/pay
  - Body: payer_name, payee_upi_id, amount
  - Returns mock UPI payment JSON with txn_ref and status.

Run
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- uvicorn app:app --reload

Data
- SQLite databases: users.db and payments.db in backend/.

Notes
- Embedding comparison is cosine similarity on normalized 512-d vectors.
- Deterministic stub uses SHA-256 of image bytes padded/repeated into a fixed vector, so registration remains reproducible without model weights.
