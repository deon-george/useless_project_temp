from __future__ import annotations

from datetime import datetime
from typing import Optional

from database import payments_connection


def create_payment(
    payer_name: str,
    payee_upi_id: str,
    amount: float,
    txn_ref: str,
    status: str = "SUCCESS",
) -> int:
    now = datetime.utcnow().isoformat()
    with payments_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO payments (payer_name, payee_upi_id, amount, status, txn_ref, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payer_name, payee_upi_id, amount, status, txn_ref, now),
        )
        return cursor.lastrowid


def get_payment(payment_id: int) -> Optional[dict]:
    with payments_connection() as conn:
        row = conn.execute(
            """
            SELECT id, payer_name, payee_upi_id, amount, status, txn_ref, created_at
            FROM payments WHERE id = ?
            """,
            (payment_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def list_payments() -> list[dict]:
    with payments_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, payer_name, payee_upi_id, amount, status, txn_ref, created_at
            FROM payments ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
