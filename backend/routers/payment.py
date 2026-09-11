from __future__ import annotations

from datetime import datetime
from typing import Optional

import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import payment_service

router = APIRouter()


class PayRequest(BaseModel):
    payer_name: str
    payee_upi_id: str
    amount: float


class PaymentResponse(BaseModel):
    txn_ref: str
    status: str
    amount: float
    payee_upi_id: str
    payer_name: str
    created_at: datetime


@router.post("/pay", response_model=PaymentResponse)
def pay(request: PayRequest) -> PaymentResponse:
    txn_ref = f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4)}"
    payment_service.create_payment(
        payer_name=request.payer_name,
        payee_upi_id=request.payee_upi_id,
        amount=request.amount,
        txn_ref=txn_ref,
        status="SUCCESS",
    )
    now = datetime.utcnow()
    return PaymentResponse(
        txn_ref=txn_ref,
        status="SUCCESS",
        amount=request.amount,
        payee_upi_id=request.payee_upi_id,
        payer_name=request.payer_name,
        created_at=now,
    )
