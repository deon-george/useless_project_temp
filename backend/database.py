import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).resolve().parent


def _connect(db_name: str) -> sqlite3.Connection:
    path = DB_DIR / db_name
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_users_db() -> None:
    with _connect("users.db") as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                upi_id TEXT NOT NULL UNIQUE,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def init_payments_db() -> None:
    with _connect("payments.db") as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_name TEXT NOT NULL,
                payee_upi_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                txn_ref TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@contextmanager
def users_connection():
    conn = _connect("users.db")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@contextmanager
def payments_connection():
    conn = _connect("payments.db")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
