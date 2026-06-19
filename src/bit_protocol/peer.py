"""Peer-to-peer sync module for Bit Protocol.

Manages known peer indexes and synchronizes stamps between them.
Each peer runs a Docker index at some public URL. Peers exchange
stamps via GET /sync?since=<timestamp> and merge into local DB.

The blockchain is the source of truth — the peer network is just
a distributed search index. Every stamp can be independently
verified against Bitcoin.
"""

import json
import time
from pathlib import Path
from typing import Optional

import httpx

from .key import BIT_DIR
from .db import search_stamps, save_stamp
from .types import StampResult

PEERS_PATH = BIT_DIR / "peers.json"
SYNC_TIMEOUT = 30  # seconds per peer
MAX_SYNC_PAGE = 500


# ── Peer config management ───────────────────────────────────


def _ensure_peers_file():
    """Create peers.json if it doesn't exist."""
    BIT_DIR.mkdir(mode=0o700, exist_ok=True)
    if not PEERS_PATH.exists():
        PEERS_PATH.write_text(json.dumps({"peers": [], "last_sync": {}}))


def _read_peers() -> dict:
    """Read peers config, return {'peers': [...], 'last_sync': {...}}."""
    _ensure_peers_file()
    try:
        return json.loads(PEERS_PATH.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {"peers": [], "last_sync": {}}


def _write_peers(data: dict):
    """Write peers config."""
    PEERS_PATH.write_text(json.dumps(data, indent=2))


def add_peer(url: str) -> bool:
    """Add a peer URL to the known peer list.

    Args:
        url: Full URL of the peer's index (e.g. 'https://bit.example.com:8787')

    Returns:
        True if added, False if already present
    """
    url = url.rstrip("/")
    data = _read_peers()
    if url in data["peers"]:
        return False
    data["peers"].append(url)
    data["peers"].sort()
    _write_peers(data)
    return True


def remove_peer(url: str) -> bool:
    """Remove a peer URL from the known peer list.

    Returns:
        True if removed, False if not found
    """
    url = url.rstrip("/")
    data = _read_peers()
    if url not in data["peers"]:
        return False
    data["peers"].remove(url)
    data["last_sync"].pop(url, None)
    _write_peers(data)
    return True


def list_peers() -> list[str]:
    """Return sorted list of known peer URLs."""
    return _read_peers()["peers"]


def get_last_sync(url: str) -> int:
    """Get the last sync timestamp for a peer."""
    url = url.rstrip("/")
    data = _read_peers()
    return data["last_sync"].get(url, 0)


def set_last_sync(url: str, timestamp: int):
    """Update the last sync timestamp for a peer."""
    url = url.rstrip("/")
    data = _read_peers()
    data["last_sync"][url] = timestamp
    _write_peers(data)


# ── Sync operations ──────────────────────────────────────────


def sync_peer(url: str, limit: int = MAX_SYNC_PAGE) -> dict:
    """Sync stamps from a single peer index.

    Fetches stamps indexed after the last sync time, merges them
    into the local database, and updates the sync cursor.

    Args:
        url: Peer index URL
        limit: Max stamps per sync page

    Returns:
        dict with keys: new_stamps (int), errors (list), synced_at (int)
    """
    url = url.rstrip("/")
    since = get_last_sync(url)
    errors = []
    total_new = 0
    synced_at = 0
    page = 0

    while True:
        page += 1
        try:
            resp = httpx.get(
                f"{url}/sync",
                params={"since": since, "limit": limit},
                timeout=SYNC_TIMEOUT,
            )
            if resp.status_code != 200:
                errors.append(f"Page {page}: HTTP {resp.status_code}")
                break

            data = resp.json()
            stamps = data.get("stamps", [])
            synced_at = data.get("synced_at", int(time.time()))

            if not stamps:
                break  # No more stamps

            new_count = 0
            for s in stamps:
                try:
                    result = StampResult(
                        txid=s["txid"],
                        file_hash=s["hash"],
                        content_type=s["content_type"],
                        key_fingerprint=s["key_fingerprint"],
                        public_key=s.get("public_key", ""),
                        metadata=s.get("metadata", {}),
                        network=s.get("network", "testnet"),
                    )
                    save_stamp(result)
                    new_count += 1
                except Exception as e:
                    errors.append(f"Stamp {s.get('hash', '?')}: {e}")

            total_new += new_count
            since = stamps[-1]["indexed_at"]

            # If we got fewer than limit, that was the last page
            if len(stamps) < limit:
                break

        except httpx.TimeoutException:
            errors.append(f"Page {page}: timeout")
            break
        except httpx.HTTPError as e:
            errors.append(f"Page {page}: {e}")
            break
        except Exception as e:
            errors.append(f"Page {page}: {e}")
            break

    # Update sync cursor to when we finished (so retry catches missed stamps)
    if synced_at > 0:
        set_last_sync(url, synced_at)

    return {
        "new_stamps": total_new,
        "pages": page,
        "errors": errors,
        "synced_at": synced_at,
    }


def sync_all_peers() -> list[dict]:
    """Sync from all known peers.

    Returns:
        List of per-peer sync result dicts
    """
    peers = list_peers()
    results = []
    for url in peers:
        result = sync_peer(url)
        result["url"] = url
        results.append(result)
    return results


def count_peers() -> int:
    """Return the number of known peers."""
    return len(list_peers())
