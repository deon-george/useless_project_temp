from __future__ import annotations

from typing import Optional

from database import users_connection


def create_user(name: str, upi_id: str, embedding: bytes) -> int:
    with users_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, upi_id, embedding) VALUES (?, ?, ?)",
            (name, upi_id, embedding),
        )
        return cursor.lastrowid


def get_user(user_id: int) -> Optional[dict]:
    with users_connection() as conn:
        row = conn.execute(
            "SELECT id, name, upi_id, embedding, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def list_users() -> list[dict]:
    with users_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, upi_id, embedding, created_at FROM users"
        ).fetchall()
        return [dict(row) for row in rows]
