"""SHA-256 file hashing."""

import hashlib

CHUNK_SIZE = 65536  # 64KB chunks for memory-efficient hashing


def hash_file(path: str) -> bytes:
    """SHA-256 hash of a file. Returns 32 raw bytes.

    Reads in chunks to handle large files without loading into memory.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.digest()


def hash_bytes(data: bytes) -> bytes:
    """SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).digest()


def hash_text(text: str) -> bytes:
    """SHA-256 hash of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).digest()
