"""OP_RETURN payload construction and parsing.

Implements the Bit Protocol payload standard:

| Offset | Size | Field            | Description                          |
|--------|------|------------------|--------------------------------------|
| 0      | 3    | Protocol magic   | ASCII "BIT"                          |
| 3      | 1    | Version          | 0x01 (current)                       |
| 4      | 1    | Content type     | see ContentType enum                 |
| 5      | 32   | SHA-256 hash     | File fingerprint                     |
| 37     | 4    | Key fingerprint  | First 4 bytes of SHA-256(pubkey)     |
| 41     | ≤42  | Metadata (opt)   | Compact JSON                         |
"""

import json
from typing import Optional

from .types import ContentType, CONTENT_TYPE_FROM_NAME, CONTENT_TYPE_NAMES

PROTOCOL_MAGIC = b"BIT"
VERSION = b"\x01"

# Maximum metadata payload for Bitcoin Core v30+ nodes (100KB total)
# We cap at 42 bytes for backward compat with Knots nodes (42-byte limit)
# Total: 3 + 1 + 1 + 32 + 4 + 42 = 83 bytes (original Bitcoin limit)
MAX_METADATA_BYTES = 42
MAX_TOTAL_BYTES = 83


def build_payload(
    file_hash: bytes,
    content_type: str,
    key_fingerprint: bytes,
    metadata: Optional[dict] = None,
) -> bytes:
    """Build the OP_RETURN payload bytes.

    Args:
        file_hash: 32-byte SHA-256 hash of the file
        content_type: One of 'document', 'source_code', 'design', 'other'
        key_fingerprint: 4-byte key fingerprint
        metadata: Optional dict (will be JSON-encoded, must fit in remaining space)

    Returns:
        Binary payload ready for OP_RETURN output

    Raises:
        ValueError: If payload exceeds max size or fields are wrong length
    """
    if len(file_hash) != 32:
        raise ValueError(f"file_hash must be 32 bytes, got {len(file_hash)}")
    if content_type not in CONTENT_TYPE_FROM_NAME:
        raise ValueError(f"unknown content type: {content_type}")
    if len(key_fingerprint) != 4:
        raise ValueError(f"key_fingerprint must be 4 bytes, got {len(key_fingerprint)}")

    type_byte = bytes([CONTENT_TYPE_FROM_NAME[content_type].value])

    payload = PROTOCOL_MAGIC + VERSION + type_byte + file_hash + key_fingerprint

    if metadata:
        meta_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        remaining = MAX_TOTAL_BYTES - len(payload)
        if len(meta_bytes) > remaining:
            raise ValueError(
                f"metadata ({len(meta_bytes)} bytes) exceeds "
                f"remaining space ({remaining} bytes)"
            )
        payload += meta_bytes

    if len(payload) > MAX_TOTAL_BYTES:
        raise ValueError(
            f"payload exceeds {MAX_TOTAL_BYTES} bytes: {len(payload)}"
        )

    return payload


def parse_payload(payload: bytes) -> dict:
    """Parse an OP_RETURN payload back into structured fields.

    Args:
        payload: Raw bytes from OP_RETURN script

    Returns:
        Dict with keys: version, content_type, file_hash, key_fingerprint, metadata

    Raises:
        ValueError: If payload doesn't match Bit Protocol format
    """
    if len(payload) < 41:
        raise ValueError(
            f"payload too short ({len(payload)} bytes), minimum is 41"
        )
    if payload[:3] != PROTOCOL_MAGIC:
        raise ValueError(
            f"invalid protocol magic: {payload[:3]!r}, expected {PROTOCOL_MAGIC!r}"
        )

    version = payload[3]
    type_byte = payload[4]
    file_hash = payload[5:37]
    key_fingerprint = payload[37:41]
    metadata_raw = payload[41:] if len(payload) > 41 else b""

    # Reverse content type lookup
    try:
        content_type = ContentType(type_byte)
        content_type_name = CONTENT_TYPE_NAMES[content_type]
    except (ValueError, KeyError):
        content_type_name = f"unknown(0x{type_byte:02x})"

    result = {
        "version": version,
        "content_type": content_type_name,
        "file_hash": file_hash.hex(),
        "key_fingerprint": key_fingerprint.hex(),
    }

    if metadata_raw:
        try:
            result["metadata"] = json.loads(metadata_raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            result["metadata_raw"] = metadata_raw.hex()

    return result
