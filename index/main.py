"""Public Bit Stamp Index API.

An optional public index where nodes can broadcast and query stamps.
Runs as a FastAPI server behind Docker Compose.

Endpoints:
    POST /stamp       - Record a new stamp
    GET /stamp/{hash} - Look up a stamp by hash
    GET /search       - Search stamps by query
    GET /health       - Health check
"""

import json
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(
    title="Bit Protocol Public Index",
    description="Open index for Bit Protocol IP stamps",
    version="0.1.0",
)

DB_PATH = Path("/data/stamps.db")  # Docker volume mount


def get_db() -> sqlite3.Connection:
    db_path = DB_PATH if DB_PATH.parent.exists() else Path("stamps.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stamps (
            hash TEXT PRIMARY KEY,
            txid TEXT NOT NULL,
            content_type TEXT NOT NULL,
            key_fingerprint TEXT NOT NULL,
            public_key TEXT,
            metadata TEXT,
            network TEXT DEFAULT 'testnet',
            created_at INTEGER NOT NULL,
            indexed_at INTEGER NOT NULL
        )
    """)
    return conn


# ── Models ───────────────────────────────────────────────────


class StampPost(BaseModel):
    hash: str
    txid: str
    content_type: str = "document"
    key_fingerprint: str
    public_key: str = ""
    metadata: dict = {}
    network: str = "testnet"


class StampResponse(BaseModel):
    hash: str
    txid: str
    content_type: str
    key_fingerprint: str
    public_key: str = ""
    metadata: dict = {}
    network: str = "testnet"
    indexed_at: int


# ── Endpoints ─────────────────────────────────────────────────


@app.post("/stamp", status_code=201)
def create_stamp(stamp: StampPost):
    """Record a new stamp in the public index."""
    conn = get_db()
    try:
        now = int(time.time())
        conn.execute(
            """INSERT OR IGNORE INTO stamps
               (hash, txid, content_type, key_fingerprint, public_key,
                metadata, network, created_at, indexed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                stamp.hash,
                stamp.txid,
                stamp.content_type,
                stamp.key_fingerprint,
                stamp.public_key,
                json.dumps(stamp.metadata),
                stamp.network,
                stamp.created_at if stamp.created_at else now,
                now,
            ),
        )
        conn.commit()
        return {"status": "ok", "hash": stamp.hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/stamp/{file_hash}", response_model=StampResponse)
def get_stamp(file_hash: str):
    """Look up a stamp by its file hash."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM stamps WHERE hash = ?", (file_hash,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Stamp not found")

        d = dict(row)
        if d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except (json.JSONDecodeError, TypeError):
                d["metadata"] = {}
        if not d.get("metadata"):
            d["metadata"] = {}
        return d
    finally:
        conn.close()


@app.get("/search")
def search_stamps(
    q: str = Query("", description="Search query (hash prefix, txid prefix, or key fp)"),
    field: str = Query("hash", description="Field to search"),
    limit: int = Query(50, ge=1, le=200),
):
    """Search stamps by hash, txid, or key fingerprint."""
    valid_fields = {"hash", "txid", "key_fingerprint", "content_type"}
    if field not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field: {field}. Must be one of {valid_fields}",
        )

    conn = get_db()
    try:
        cursor = conn.execute(
            f"SELECT * FROM stamps WHERE {field} LIKE ? ORDER BY indexed_at DESC LIMIT ?",
            (f"%{q}%", limit),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except (json.JSONDecodeError, TypeError):
                    d["metadata"] = {}
            if not d.get("metadata"):
                d["metadata"] = {}
            results.append(d)
        return {"results": results, "count": len(results)}
    finally:
        conn.close()


@app.get("/health")
def health():
    """Health check."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM stamps")
        count = cursor.fetchone()["count"]
        return {"status": "ok", "stamp_count": count}
    finally:
        conn.close()
