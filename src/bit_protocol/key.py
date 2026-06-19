"""secp256k1 key management for Bit Protocol.

Generates, stores, and loads ECDSA keypairs for signing stamps.
Keys are stored in PEM format under ~/.bit/.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

BIT_DIR = Path.home() / ".bit"
KEY_PATH = BIT_DIR / "key.pem"
PUBKEY_PATH = BIT_DIR / "pubkey.pem"


def _ensure_dir():
    """Create ~/.bit/ directory with secure permissions."""
    BIT_DIR.mkdir(mode=0o700, exist_ok=True)


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate a new secp256k1 keypair.

    Returns:
        (private_key_bytes, compressed_public_key_bytes)
    """
    private_key = ec.generate_private_key(ec.SECP256K1())
    priv_int = private_key.private_numbers().private_value
    priv_bytes = priv_int.to_bytes(32, byteorder="big")
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    return priv_bytes, pub_bytes


def save_key(private_key_bytes: bytes):
    """Save private key to ~/.bit/key.pem in SEC1 PEM format.

    Args:
        private_key_bytes: 32-byte raw private key
    """
    _ensure_dir()
    priv_int = int.from_bytes(private_key_bytes, byteorder="big")
    key = ec.derive_private_key(priv_int, ec.SECP256K1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    KEY_PATH.write_bytes(pem)
    KEY_PATH.chmod(0o600)  # Owner read/write only


def load_key() -> tuple[bytes, bytes]:
    """Load keypair from ~/.bit/.

    Returns:
        (private_key_bytes, compressed_public_key_bytes)

    Raises:
        FileNotFoundError: If key hasn't been generated yet
    """
    if not KEY_PATH.exists():
        raise FileNotFoundError(
            "No Bit Protocol key found. Run 'bit init' first."
        )
    pem = KEY_PATH.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    priv_int = key.private_numbers().private_value
    priv_bytes = priv_int.to_bytes(32, byteorder="big")
    pub_key = key.public_key()
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    return priv_bytes, pub_bytes


def key_exists() -> bool:
    """Check if a key has been generated and saved."""
    return KEY_PATH.exists()


def get_pubkey_hex() -> Optional[str]:
    """Get the hex-encoded compressed public key if available."""
    try:
        _, pub_bytes = load_key()
        return pub_bytes.hex()
    except FileNotFoundError:
        return None


# --- Fingerprint ---


def get_key_fingerprint(public_key: bytes) -> bytes:
    """Derive 4-byte key fingerprint from a public key.

    First 4 bytes of SHA-256(compressed_public_key).
    This is used in the OP_RETURN payload to identify which key signed the stamp.

    Args:
        public_key: 33-byte compressed public key

    Returns:
        4-byte fingerprint
    """
    return hashlib.sha256(public_key).digest()[:4]


def get_my_fingerprint() -> Optional[str]:
    """Get hex fingerprint of the current key, or None if not initialized."""
    try:
        _, pub_bytes = load_key()
        return get_key_fingerprint(pub_bytes).hex()
    except FileNotFoundError:
        return None
