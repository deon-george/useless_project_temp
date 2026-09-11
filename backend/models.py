from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    upi_id: str
    embedding: bytes
    created_at: datetime


@dataclass
class Payment:
    id: int
    payer_name: str
    payee_upi_id: str
    amount: float
    status: str
    txn_ref: str
    created_at: datetime
