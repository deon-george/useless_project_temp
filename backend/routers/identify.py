from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from services import face_engine

router = APIRouter()


@router.post("/identify", response_model=dict)
def identify_user(image_file: UploadFile = File(...)) -> dict:
    image_bytes = image_file.file.read()
    match = face_engine.match_user(image_bytes)
    if not match:
        raise HTTPException(status_code=404, detail="No matching user found")
    return match
