from __future__ import annotations

from typing import Optional

import numpy as np

from database import users_connection

try:
    from insightface.app import FaceAnalysis
    from insightface.data import get_image as ins_get_image

    _face_app = FaceAnalysis(name="buffalo_l", providers=["CPU"])
    _face_app.prepare(ctx_id=0, det_size=(640, 640))
    INSIGHTFACE_AVAILABLE = True
except Exception:
    INSIGHTFACE_AVAILABLE = False


def _deterministic_embedding(image_bytes: bytes) -> bytes:
    digest = __import__("hashlib").sha256(image_bytes).digest()
    arr = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    if arr.shape[0] < 512:
        arr = np.pad(arr, (0, 512 - arr.shape[0]), mode="wrap")
    arr = arr[:512]
    arr = arr / np.linalg.norm(arr)
    return arr.astype(np.float32).tobytes()


def extract_embedding(image_bytes: bytes) -> bytes:
    if INSIGHTFACE_AVAILABLE:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            image = ins_get_image(tmp.name)
            faces = _face_app.get(image)
            if not faces:
                raise ValueError("No face detected")
            return faces[0].normed_embedding.astype(np.float32).tobytes()
    return _deterministic_embedding(image_bytes)


def match_user(image_bytes: bytes, threshold: float = 0.75) -> Optional[dict]:
    embedding = extract_embedding(image_bytes)
    query = np.frombuffer(embedding, dtype=np.float32)
    query = query / np.linalg.norm(query)

    matched_user = None
    best_similarity = -1.0

    with users_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, upi_id, embedding FROM users"
        ).fetchall()
        for row in rows:
            candidate = np.frombuffer(row["embedding"], dtype=np.float32)
            candidate = candidate / np.linalg.norm(candidate)
            similarity = float(np.dot(query, candidate))
            if similarity > best_similarity:
                best_similarity = similarity
                matched_user = row

    effective_threshold = 0.99 if not INSIGHTFACE_AVAILABLE else threshold
    if matched_user and best_similarity >= effective_threshold:
        return {
            "id": matched_user["id"],
            "name": matched_user["name"],
            "upi_id": matched_user["upi_id"],
            "similarity": best_similarity,
        }
    return None
