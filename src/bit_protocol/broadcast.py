"""Bitcoin transaction construction and broadcast.

Builds OP_RETURN transactions, signs them, and broadcasts via Blockstream API.
Supports Bitcoin Testnet (default) and Mainnet.
"""

import httpx
from bitcoinlib.transactions import Transaction
from bitcoinlib.keys import Key

from .key import load_key
from .payload import build_payload
from .types import StampResult

BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api/"
BLOCKSTREAM_MAINNET = "https://blockstream.info/api/"

DEFAULT_FEE_SATS = 2000  # 2k sats ~ $1-2, enough for testnet

# Timeouts
TX_TIMEOUT = 30  # seconds for broadcast
FETCH_TIMEOUT = 15


def _blockstream_url(network: str) -> str:
    """Get the Blockstream API base URL for the given network."""
    if network == "mainnet":
        return BLOCKSTREAM_MAINNET
    return BLOCKSTREAM_TESTNET


def _fetch_utxos(address: str, network: str = "testnet") -> list[dict]:
    """Fetch UTXOs for an address from Blockstream API.

    Args:
        address: Bitcoin address (P2PKH)
        network: 'testnet' or 'mainnet'

    Returns:
        List of UTXOs with txid, vout, value, scriptpubkey

    Raises:
        httpx.HTTPError: If API request fails
    """
    base = _blockstream_url(network)
    resp = httpx.get(
        f"{base}address/{address}/utxo",
        timeout=FETCH_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _derive_address(
    public_key_hex: str, network: str = "testnet"
) -> str:
    """Derive a P2PKH address from a public key hex string.

    Args:
        public_key_hex: Hex-encoded compressed public key
        network: 'testnet' or 'mainnet'

    Returns:
        Bitcoin address string
    """
    key = Key(import_key=public_key_hex, is_private=False, network=network)
    return key.address()


def _estimate_fee(tx: Transaction, fee_sats: int = DEFAULT_FEE_SATS) -> int:
    """Calculate fee based on tx size.

    Uses a simple sat/vB rate. For testnet, minimum relay is usually fine.

    Args:
        tx: Unsigned transaction (for size estimation)
        fee_sats: Fee in satoshis

    Returns:
        Fee in satoshis
    """
    # For MVP, use fixed fee. v2 will estimate from network conditions.
    return fee_sats


def stamp_tx(
    file_hash: bytes,
    content_type: str,
    key_fingerprint: bytes,
    metadata: dict | None = None,
    fee_sats: int = DEFAULT_FEE_SATS,
    network: str = "testnet",
    utxo: str | None = None,
) -> StampResult:
    """Create, sign, and broadcast an OP_RETURN stamp transaction.

    This is the main entry point for the stamp operation.

    Args:
        file_hash: 32-byte SHA-256 hash
        content_type: Content type string
        key_fingerprint: 4-byte key fingerprint
        metadata: Optional metadata dict
        fee_sats: Transaction fee in satoshis
        network: 'testnet' or 'mainnet'
        utxo: UTXO to spend in format 'txid:vout'.
              If None, auto-selects first available UTXO.

    Returns:
        StampResult with txid and details

    Raises:
        ValueError: If UTXO not found or insufficient funds
        httpx.HTTPError: If broadcast fails
        FileNotFoundError: If key not initialized
    """
    # Build the OP_RETURN payload
    payload = build_payload(file_hash, content_type, key_fingerprint, metadata)
    op_return_script = b"\x6a" + bytes([len(payload)]) + payload  # OP_RETURN + len + data

    # Load key
    priv_bytes, pub_bytes = load_key()
    pub_hex = pub_bytes.hex()
    priv_hex = priv_bytes.hex()

    # Derive address for UTXO lookup
    addr = _derive_address(pub_hex, network)

    # Create transaction (legacy format — OP_RETURN works with both)
    tx = Transaction(network=network, witness_type='legacy')

    # Add OP_RETURN output (value = 0)
    tx.add_output(0, lock_script=op_return_script)

    # Handle input (UTXO to spend for fees)
    if utxo:
        parts = utxo.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid UTXO format: {utxo}. Use 'txid:vout'")
        utxo_txid, utxo_vout = parts[0], int(parts[1])

        # Fetch the UTXO details to get the value and script
        base = _blockstream_url(network)
        tx_resp = httpx.get(
            f"{base}tx/{utxo_txid}",
            timeout=FETCH_TIMEOUT,
        )
        tx_resp.raise_for_status()
        tx_data = tx_resp.json()

        utxo_vout_data = tx_data["vout"][utxo_vout]
        utxo_value = utxo_vout_data["value"]
        utxo_script = utxo_vout_data["scriptpubkey"]

        # Add input - value from Blockstream API is in satoshis
        tx.add_input(
            prev_txid=utxo_txid,
            output_n=utxo_vout,
            value=utxo_value,
            locking_script=utxo_script,
        )

        # Add change output if there's excess
        fee = _estimate_fee(tx, fee_sats)
        change = utxo_value - fee  # both in satoshis
        if change > 546:  # dust threshold
            tx.add_output(change, address=addr)

        # Sign
        key = Key(import_key=priv_hex, network=network)
        tx.sign(key)
    else:
        # No UTXO provided — build unsigned tx for user to sign manually
        # This is the "offline" mode
        raise ValueError(
            "No UTXO provided. You need a Bitcoin UTXO to pay transaction fees.\n\n"
            f"Get testnet BTC from a faucet sent to this address: {addr}\n"
            "Then retry with: bit stamp <file> --utxo=<txid>:<vout>"
        )

    # Broadcast
    raw_hex = tx.raw_hex()
    base = _blockstream_url(network)
    broadcast_resp = httpx.post(
        f"{base}tx",
        content=raw_hex,
        timeout=TX_TIMEOUT,
    )

    if broadcast_resp.status_code != 200:
        error_msg = broadcast_resp.text.strip()
        raise RuntimeError(
            f"Broadcast failed (HTTP {broadcast_resp.status_code}): {error_msg}"
        )

    txid = broadcast_resp.text.strip()

    return StampResult(
        txid=txid,
        file_hash=file_hash.hex(),
        content_type=content_type,
        key_fingerprint=key_fingerprint.hex(),
        public_key=pub_hex,
        metadata=metadata or {},
        network=network,
        fee_sats=fee_sats,
    )


def fetch_transaction(txid: str, network: str = "testnet") -> dict:
    """Fetch a transaction from Blockstream API.

    Args:
        txid: Transaction ID (hex string)
        network: 'testnet' or 'mainnet'

    Returns:
        Transaction data as dict with vout, vin, etc.

    Raises:
        httpx.HTTPError: If API request fails
        ValueError: If transaction not found
    """
    base = _blockstream_url(network)
    resp = httpx.get(f"{base}tx/{txid}", timeout=FETCH_TIMEOUT)
    if resp.status_code == 404:
        raise ValueError(f"Transaction not found: {txid}")
    resp.raise_for_status()
    return resp.json()


def extract_op_return(tx_data: dict) -> list[bytes]:
    """Extract OP_RETURN data from transaction outputs.

    Args:
        tx_data: Transaction data dict from Blockstream API

    Returns:
        List of OP_RETURN payload bytes (one per nulldata output)
    """
    results = []
    for vout in tx_data.get("vout", []):
        if vout.get("scriptpubkey_type") in ("nulldata", "op_return"):
            script_hex = vout.get("scriptpubkey", "")
            script_bytes = bytes.fromhex(script_hex)
            # Skip OP_RETURN (0x6a) and length byte, take the data
            if len(script_bytes) > 2:
                results.append(script_bytes[2:])
    return results


def get_utxo_status(txid: str, vout: int, network: str = "testnet") -> dict:
    """Check if a UTXO is unspent and get its details.

    Args:
        txid: Transaction ID
        vout: Output index
        network: 'testnet' or 'mainnet'

    Returns:
        Dict with status, value, script info
    """
    base = _blockstream_url(network)
    resp = httpx.get(
        f"{base}tx/{txid}", timeout=FETCH_TIMEOUT
    )
    if resp.status_code != 200:
        return {"status": "not_found"}

    tx_data = resp.json()
    if vout >= len(tx_data["vout"]):
        return {"status": "invalid_vout"}

    vout_data = tx_data["vout"][vout]
    return {
        "status": "unspent" if vout_data.get("spent") is False else "spent",
        "value_btc": vout_data["value"],
        "script_type": vout_data.get("scriptpubkey_type"),
    }
