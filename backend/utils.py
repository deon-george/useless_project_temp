from __future__ import annotations

import re
from typing import Any


def success_response(data: Any) -> dict:
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400) -> dict:
    return {"success": False, "error": message, "status_code": status_code}


def validate_amount(amount: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    return round(float(amount), 2)


def validate_upi(upi_id: str) -> str:
    if not re.match(r"^[\w.\-]+@[\w.\-]+$", upi_id):
        raise ValueError("Invalid UPI ID format")
    return upi_id
