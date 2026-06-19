"""Local SQLite stamp cache.

Every stamp you create or verify gets recorded locally so you can
search your own history without hitting the network.
"""

import json
import sqlite3
import time
from pathlib import Path

from .key import BIT_DIR
from .types import StampResult

DB_PATH = BIT_DIR / "stamps.db"


def _get_db() -> sqlite3.Connection:
    """Get a connection to the local stamp database."""
    BIT_DIR.mkdir(mode=0o700, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stamps (
            hash TEXT PRIMARY KEY,
            txid TEXT NOT NULL,
            content_type TEXT NOT NULL,
            key_fingerprint TEXT NOT NULL,
            public_key TEXT,
            metadata TEXT,
            network TEXT DEFAULT 'testnet',
            created_at INTEGER NOT NULL
        )
    """)


def save_stamp(result: StampResult) -> None:
    """Save a stamp result to the local database.

    Args:
        result: StampResult from a successful stamp operation
    """
    conn = _get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO stamps
               (hash, txid, content_type, key_fingerprint, public_key, metadata, network, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.file_hash,
                result.txid,
                result.content_type,
                result.key_fingerprint,
                result.public_key,
                json.dumps(result.metadata),
                result.network,
                int(time.time()),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def search_stamps(query: str, field: str = "hash") -> list[dict]:
    """Search local stamps database.

    Args:
        query: Search term
        field: Field to search ('hash', 'txid', 'key_fingerprint', 'content_type')

    Returns:
        List of matching stamp records as dicts
    """
    valid_fields = {"hash", "txid", "key_fingerprint", "content_type"}
    if field not in valid_fields:
        raise ValueError(f"Invalid search field: {field}. Must be one of {valid_fields}")

    conn = _get_db()
    try:
        cursor = conn.execute(
            f"SELECT * FROM stamps WHERE {field} LIKE ? ORDER BY created_at DESC LIMIT 50",
            (f"%{query}%",),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results
    finally:
        conn.close()


def get_stamp(hash_hex: str) -> dict | None:
    """Get a specific stamp by its file hash.

    Args:
        hash_hex: Hex-encoded SHA-256 hash

    Returns:
        Stamp dict or None if not found
    """
    conn = _get_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM stamps WHERE hash = ?", (hash_hex,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        if d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d
    finally:
        conn.close()


def count_stamps() -> int:
    """Get total number of stamps in local database."""
    conn = _get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM stamps")
        return cursor.fetchone()["count"]
    finally:
        conn.close()
