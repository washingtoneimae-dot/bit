"""Data types for the Bit Protocol."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class ContentType(IntEnum):
    """Supported content types for IP stamps."""

    DOCUMENT = 0x01
    SOURCE_CODE = 0x02
    DESIGN = 0x03
    OTHER = 0x04


CONTENT_TYPE_NAMES = {ct: ct.name.lower() for ct in ContentType}
CONTENT_TYPE_FROM_NAME = {ct.name.lower(): ct for ct in ContentType}


@dataclass
class StampResult:
    """Result of a successful stamp operation."""

    txid: str
    file_hash: str  # hex
    content_type: str
    key_fingerprint: str  # hex
    public_key: str  # hex
    metadata: dict = field(default_factory=dict)
    network: str = "testnet"
    fee_sats: int = 0


@dataclass
class StampProof:
    """Parsed proof from a verified stamp."""

    match: bool
    file_hash: str  # hex
    onchain_hash: str  # hex
    content_type: str
    key_fingerprint: str
    timestamp: str
    metadata: dict = field(default_factory=dict)
    network: str = "testnet"
