"""Bit Protocol CLI — stamp, verify, and search IP proofs on Bitcoin."""

import json
import sys

import click

from . import __version__
from .hash import hash_file, hash_text
from .key import (
    generate_keypair,
    get_key_fingerprint,
    get_my_fingerprint,
    get_pubkey_hex,
    key_exists,
    load_key,
    save_key,
)
from .payload import parse_payload
from .broadcast import (
    extract_op_return,
    fetch_transaction,
    stamp_tx,
)
from .db import count_stamps, get_stamp, save_stamp, search_stamps


@click.group()
@click.version_option(__version__, prog_name="bit")
def cli():
    """Bit Protocol — decentralized IP proof of existence on Bitcoin.

    Stamp your files, code, and ideas to the Bitcoin blockchain as
    immutable proof that you had them at a specific point in time.
    """


# ── init ──────────────────────────────────────────────────────


@cli.command()
def init():
    """Generate your Bit Protocol identity key.

    Creates a secp256k1 keypair stored in ~/.bit/key.pem.
    This key is used to sign all your stamps.
    """
    if key_exists():
        fingerprint = get_my_fingerprint()
        click.echo("✓ Key already exists at ~/.bit/key.pem")
        click.echo(f"  Fingerprint: {fingerprint}")
        click.echo("  Use 'bit stamp <file>' to start stamping.")
        return

    priv_bytes, pub_bytes = generate_keypair()
    save_key(priv_bytes)
    fingerprint = get_key_fingerprint(pub_bytes).hex()
    pub_hex = pub_bytes.hex()

    click.echo("✓ Bit Protocol identity created")
    click.echo(f"  Public key:  {pub_hex}")
    click.echo(f"  Fingerprint: {fingerprint}")
    click.echo(f"  Saved to:    ~/.bit/key.pem")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Get testnet BTC from a faucet and send to your address")
    click.echo("  2. bit stamp myfile.pdf")
    click.echo("")


# ── stamp ─────────────────────────────────────────────────────


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--type",
    "content_type",
    default="document",
    type=click.Choice(["document", "source_code", "design", "other"]),
    help="Type of content being stamped",
)
@click.option(
    "--mainnet",
    is_flag=True,
    default=False,
    help="Stamp to Bitcoin mainnet (requires real BTC)",
)
@click.option(
    "--utxo",
    help="UTXO to spend for fees: 'txid:vout' (auto-detected if omitted)",
)
@click.option(
    "--text",
    is_flag=True,
    default=False,
    help="Input is raw text, not a file path",
)
@click.option(
    "--meta",
    help="JSON metadata string, e.g. '{\"v\":\"1.0\"}'",
)
@click.option(
    "--fee",
    default=2000,
    type=int,
    help="Transaction fee in satoshis (default: 2000)",
)
def stamp(input_path, content_type, mainnet, utxo, text, meta, fee):
    """Stamp a file to Bitcoin as proof of existence.

    INPUT_PATH is the file to stamp (or text if --text is set).

    Creates an OP_RETURN transaction with the file's SHA-256 hash
    and broadcasts it to the Bitcoin blockchain.

    If no --utxo is provided, Bit auto-scans your address for
    spendable UTXOs. You need testnet BTC in your wallet first.
    """
    if not key_exists():
        click.echo("✗ No Bit identity found. Run 'bit init' first.", err=True)
        sys.exit(1)

    network = "mainnet" if mainnet else "testnet"

    # Hash the input
    if text:
        file_hash = hash_text(input_path)
        display_name = f"text: {input_path[:50]}"
    else:
        file_hash = hash_file(input_path)
        display_name = str(input_path)

    # Parse metadata
    metadata = None
    if meta:
        try:
            metadata = json.loads(meta)
        except json.JSONDecodeError as e:
            click.echo(f"✗ Invalid JSON metadata: {e}", err=True)
            sys.exit(1)

    # Get key fingerprint
    _, pub_bytes = load_key()
    fingerprint = get_key_fingerprint(pub_bytes)

    click.echo(f" Stamping: {display_name}")
    click.echo(f"  Network:  {network}")
    click.echo(f"  Hash:     {file_hash.hex()}")
    click.echo(f"  Type:     {content_type}")
    click.echo(f"  Fee:      {fee} sats")
    if metadata:
        click.echo(f"  Metadata: {json.dumps(metadata)}")

    try:
        result = stamp_tx(
            file_hash=file_hash,
            content_type=content_type,
            key_fingerprint=fingerprint,
            metadata=metadata,
            fee_sats=fee,
            network=network,
            utxo=utxo,
        )

        # Save to local database
        save_stamp(result)

        click.echo("")
        click.echo(f"✓ Stamped to Bitcoin {network}!")
        click.echo(f"  txid: {result.txid}")
        click.echo(f"  Hash: {result.file_hash}")
        click.echo("")

        if network == "testnet":
            click.echo(f"  View: https://blockstream.info/testnet/tx/{result.txid}")
        else:
            click.echo(f"  View: https://blockstream.info/tx/{result.txid}")

    except ValueError as e:
        click.echo("")
        click.echo(str(e), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Stamp failed: {e}", err=True)
        sys.exit(1)


# ── verify ────────────────────────────────────────────────────


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--txid", required=True, help="Transaction ID to verify against")
@click.option("--mainnet", is_flag=True, default=False, help="Check mainnet")
@click.option("--text", is_flag=True, default=False, help="Input is raw text")
def verify(input_path, txid, mainnet, text):
    """Verify a file matches an on-chain stamp.

    Hashes the file locally and compares it against the OP_RETURN
    data in the specified Bitcoin transaction.
    """
    network = "mainnet" if mainnet else "testnet"

    # Hash the input
    if text:
        file_hash = hash_text(input_path)
        display_name = f"text: {input_path[:50]}"
    else:
        file_hash = hash_file(input_path)
        display_name = str(input_path)

    local_hash_hex = file_hash.hex()

    click.echo(f" Verifying: {display_name}")
    click.echo(f"  Local hash: {local_hash_hex}")
    click.echo(f"  txid:       {txid}")
    click.echo(f"  Network:    {network}")
    click.echo("")

    try:
        tx_data = fetch_transaction(txid, network)
        op_return_data = extract_op_return(tx_data)

        if not op_return_data:
            click.echo("✗ No OP_RETURN data found in this transaction.", err=True)
            sys.exit(1)

        for i, payload_bytes in enumerate(op_return_data):
            try:
                parsed = parse_payload(payload_bytes)
                onchain_hash = parsed["file_hash"]
                match = onchain_hash == local_hash_hex

                status = "✓ MATCH" if match else "✗ MISMATCH"

                click.echo(f"  OP_RETURN #{i + 1}: {status}")
                click.echo(f"    On-chain hash: {onchain_hash}")
                click.echo(f"    Content type:  {parsed.get('content_type', '?')}")
                click.echo(f"    Key fp:        {parsed.get('key_fingerprint', '?')}")

                if "metadata" in parsed:
                    click.echo(
                        f"    Metadata:      {json.dumps(parsed['metadata'])}"
                    )

                if match:
                    click.echo("")
                    click.echo("✓ PROVEN: You possessed this exact file at block time.")

            except ValueError as e:
                click.echo(f"  OP_RETURN #{i + 1}: Not a Bit Protocol payload")
                click.echo(f"    ({e})")

    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Verification failed: {e}", err=True)
        sys.exit(1)


# ── search ────────────────────────────────────────────────────


@cli.command()
@click.argument("query")
@click.option(
    "--field",
    default="hash",
    type=click.Choice(["hash", "txid", "key_fingerprint", "content_type"]),
    help="Field to search",
)
def search(query, field):
    """Search local stamp database.

    QUERY is the search term (hash, txid, key fingerprint, or content type).

    Searches your local stamp history. For remote queries, use the
    public index API (see README).
    """
    results = search_stamps(query, field)

    if not results:
        click.echo(f"No stamps found matching '{query}' in field '{field}'.")
        click.echo("")
        click.echo("  Try:")
        click.echo("    bit search <full_hash>          # exact hash match")
        click.echo("    bit search abc123 --field=txid   # txid prefix")
        return

    click.echo(f"Found {len(results)} stamp(s):")
    click.echo("")

    for r in results:
        click.echo(f"  Hash:   {r['hash']}")
        click.echo(f"  txid:   {r['txid']}")
        click.echo(f"  Type:   {r['content_type']}")
        click.echo(f"  Key:    {r['key_fingerprint']}")
        click.echo(f"  Net:    {r.get('network', 'testnet')}")
        click.echo("")


# ── status ────────────────────────────────────────────────────


@cli.command()
def status():
    """Show Bit Protocol status and stats."""
    has_key = key_exists()
    stamp_count = count_stamps()

    click.echo("Bit Protocol Status")
    click.echo("===================")
    click.echo("")

    if has_key:
        fingerprint = get_my_fingerprint()
        pubkey = get_pubkey_hex()
        click.echo(f"  Identity:      ✓ {fingerprint}")
        click.echo(f"  Public key:    {pubkey[:20]}...{pubkey[-8:]}")
    else:
        click.echo(f"  Identity:      ✗ Not initialized (run 'bit init')")

    click.echo(f"  Local stamps:  {stamp_count}")
    click.echo(f"  Data dir:      ~/.bit/")


if __name__ == "__main__":
    cli()
