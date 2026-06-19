"""Tests for the Bit Protocol core modules."""

import json
import tempfile
from pathlib import Path

import pytest

from bit_protocol.hash import hash_file, hash_bytes, hash_text
from bit_protocol.payload import build_payload, parse_payload
from bit_protocol.types import ContentType, StampResult, StampProof
from bit_protocol.key import (
    generate_keypair,
    get_key_fingerprint,
)

# ── Test fixtures ─────────────────────────────────────────────


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"hello world")
        f.flush()
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def sample_keypair():
    """Generate a keypair for tests."""
    priv, pub = generate_keypair()
    return priv, pub


# ── hash tests ────────────────────────────────────────────────


class TestHash:
    def test_hash_file(self, temp_file):
        result = hash_file(temp_file)
        assert len(result) == 32
        # sha256 of "hello world"
        assert result.hex() == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_hash_bytes(self):
        result = hash_bytes(b"hello world")
        assert len(result) == 32
        assert result.hex() == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_hash_text(self):
        result = hash_text("hello world")
        assert len(result) == 32
        assert result.hex() == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_hash_empty_file(self, temp_file):
        # Write empty file
        Path(temp_file).write_text("")
        result = hash_file(temp_file)
        assert result.hex() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# ── payload tests ─────────────────────────────────────────────


class TestPayload:
    def test_build_minimal(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        file_hash = bytes.fromhex(
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        )
        payload = build_payload(file_hash, "document", fp)
        assert len(payload) == 41  # minimum: 3+1+1+32+4
        assert payload[:3] == b"BIT"
        assert payload[3] == 1  # version
        assert payload[4] == 0x01  # document type

    def test_build_with_metadata(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        file_hash = bytes.fromhex(
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        )
        metadata = {"p": "1.0", "a": "test"}
        payload = build_payload(file_hash, "source_code", fp, metadata)
        assert len(payload) > 41
        assert payload[:3] == b"BIT"
        assert payload[4] == 0x02  # source code type

    def test_roundtrip(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        file_hash = bytes.fromhex(
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        )
        metadata = {"v": "2", "name": "test-idea"}
        payload = build_payload(file_hash, "design", fp, metadata)
        parsed = parse_payload(payload)

        assert parsed["version"] == 1
        assert parsed["content_type"] == "design"
        assert parsed["file_hash"] == file_hash.hex()
        assert parsed["key_fingerprint"] == fp.hex()
        assert parsed["metadata"] == metadata

    def test_all_content_types(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        file_hash = b"\x00" * 32

        for ct_name in ["document", "source_code", "design", "other"]:
            payload = build_payload(file_hash, ct_name, fp)
            parsed = parse_payload(payload)
            assert parsed["content_type"] == ct_name

    def test_payload_too_short(self):
        with pytest.raises(ValueError, match="too short"):
            parse_payload(b"BIT\x01")

    def test_invalid_magic(self):
        with pytest.raises(ValueError, match="invalid protocol magic"):
            parse_payload(b"XXX\x01\x01" + b"\x00" * 32 + b"\x00" * 4)

    def test_invalid_content_type(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        with pytest.raises(ValueError, match="unknown content type"):
            build_payload(b"\x00" * 32, "invalid_type", fp)

    def test_wrong_hash_length(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        with pytest.raises(ValueError, match="must be 32 bytes"):
            build_payload(b"\x00" * 16, "document", fp)

    def test_wrong_fingerprint_length(self):
        with pytest.raises(ValueError, match="must be 4 bytes"):
            build_payload(b"\x00" * 32, "document", b"\x00" * 8)

    def test_metadata_overflow(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        # Metadata that's too large for remaining space
        big_meta = {"x": "a" * 100}
        with pytest.raises(ValueError, match="metadata.*exceeds"):
            build_payload(b"\x00" * 32, "document", fp, big_meta)

    def test_total_size_limit(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        payload = build_payload(b"\x00" * 32, "document", fp)
        assert len(payload) <= 83


# ── key tests ─────────────────────────────────────────────────


class TestKey:
    def test_generate_keypair(self):
        priv, pub = generate_keypair()
        assert len(priv) == 32
        assert len(pub) == 33  # compressed public key

    def test_generate_different_keys(self):
        p1, pub1 = generate_keypair()
        p2, pub2 = generate_keypair()
        assert p1 != p2
        assert pub1 != pub2

    def test_key_fingerprint_length(self, sample_keypair):
        _, pub = sample_keypair
        fp = get_key_fingerprint(pub)
        assert len(fp) == 4

    def test_key_fingerprint_deterministic(self, sample_keypair):
        _, pub = sample_keypair
        fp1 = get_key_fingerprint(pub)
        fp2 = get_key_fingerprint(pub)
        assert fp1 == fp2

    def test_key_fingerprint_differs(self):
        _, pub1 = generate_keypair()
        _, pub2 = generate_keypair()
        fp1 = get_key_fingerprint(pub1)
        fp2 = get_key_fingerprint(pub2)
        assert fp1 != fp2

    def test_content_type_values(self):
        assert ContentType.DOCUMENT.value == 0x01
        assert ContentType.SOURCE_CODE.value == 0x02
        assert ContentType.DESIGN.value == 0x03
        assert ContentType.OTHER.value == 0x04
