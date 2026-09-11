from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services import face_engine, user_service

router = APIRouter()


@router.post("/register", response_model=dict)
def register_user(
    name: str = Form(...),
    upi_id: str = Form(...),
    image_file: UploadFile | None = File(None),
) -> dict:
    if image_file and image_file.filename:
        image_bytes = image_file.file.read()
        embedding = face_engine.extract_embedding(image_bytes)
    else:
        embedding = face_engine._deterministic_embedding(upi_id.encode("utf-8"))

    user_id = user_service.create_user(name, upi_id, embedding)
    return {"id": user_id, "name": name, "upi_id": upi_id}
