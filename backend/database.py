"""
Lightweight SQLite persistence layer for Smart Bharat.

Keeps things dependency-free (no external DB needed) so the deployed demo
works out of the box on any host. Provides connection pooling context manager
and complaint record access helpers.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

DB_PATH = Path(__file__).parent / "smart_bharat.db"


def init_db() -> None:
    """
    Initialize the database: create tables and indexes if they do not exist.
    
    Creates the complaints table with proper schema and adds indexes on
    status and id columns for faster queries.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT,
                status TEXT NOT NULL DEFAULT 'submitted',
                language TEXT NOT NULL DEFAULT 'en',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # Create indexes for faster lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_id ON complaints(id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)")
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """
    Yield a SQLite connection with row factory set for dict-like access.
    
    Yields:
        sqlite3.Connection: Connection with Row factory for dict-style access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_complaint_by_id(conn: sqlite3.Connection, complaint_id: int) -> Optional[dict]:
    """
    Fetch a single complaint record by ID using an existing connection.
    
    Args:
        conn: Active sqlite3.Connection with row factory set.
        complaint_id: Integer complaint ID to fetch.
    
    Returns:
        Dictionary representation of the complaint row if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()
    return dict(row) if row else None
