from __future__ import annotations

from datetime import datetime
from typing import Optional

import secrets
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_payments_db, init_users_db
from routers import identify, payment, register
from services import face_engine

app = FastAPI(title="FacePay Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_users_db()
init_payments_db()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "insightface": face_engine.INSIGHTFACE_AVAILABLE,
    }


app.include_router(register.router, prefix="/api", tags=["register"])
app.include_router(identify.router, prefix="/api", tags=["identify"])
app.include_router(payment.router, prefix="/api", tags=["payment"])
