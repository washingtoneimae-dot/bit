# Bit Protocol

**Decentralized IP Proof of Existence on Bitcoin.**

Stamp your files, code, and ideas to the Bitcoin blockchain as immutable proof that you had them at a specific point in time. No disclosure. No gatekeepers. No subscription fees.

> **✅ Verified on Bitcoin Testnet** — [txid: b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c](https://blockstream.info/testnet/tx/b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c)

```bash
pip install bit-protocol
bit init
bit stamp my-whitepaper.pdf --utxo=<txid>:<vout>
bit verify my-whitepaper.pdf --txid=<txid>
```

## Why

| Problem | Bit Protocol |
|---------|-------------|
| Patents cost $10K+ and take years | Stamp in seconds for cents in fees |
| Trade secrets have no legal protection if leaked | Prove possession without disclosure |
| Bernstein.io costs $54–$329/mo | Open-source, self-host, free |
| Vendor lock-in | Your keys, your node, your stamps |
| Centralized registries can be seized or shut down | Bitcoin is permissionless and unstoppable |

## How It Works

```
Your file → SHA-256 hash → OP_RETURN payload → Bitcoin tx → Immutable proof
                      ↓
              Local SQLite cache
```

### OP_RETURN Schema

```
| 3 bytes  | 1 byte  | 1 byte  | 32 bytes   | 4 bytes   | ≤42 bytes |
| Protocol | Version | Type    | SHA-256    | Key FP    | Metadata  |
| "BIT"    | 0x01    | 0x01-04 | File hash  | Key ID    | JSON      |
```

Total: **41–83 bytes** — fits within Bitcoin's original OP_RETURN limit and is forward-compatible with Bitcoin Core v30's 100KB expansion.

## Quickstart

### 1. Install

```bash
pip install bit-protocol
```

### 2. Generate your identity

```bash
bit init
```

Creates a secp256k1 keypair at `~/.bit/key.pem`.

### 3. Get testnet BTC

Send some tBTC to your address (shown by `bit status`) from a [testnet faucet](https://coinfaucet.eu/en/btc-testnet/).

### 4. Stamp a file

```bash
bit stamp myfile.pdf --utxo=<txid>:<vout>
```

### 5. Verify

```bash
bit verify myfile.pdf --txid=<txid>
```

### 6. Check your stats

```bash
bit status
```

## Real Example (Testnet)

```bash
# Generate key (one-time)
bit init

# Stamp a file
bit stamp whitepaper.pdf --utxo=62256e0bda6e7972...:0

# Output:
# ✓ Stamped to Bitcoin testnet!
#   txid: b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c
#   View: https://blockstream.info/testnet/tx/b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c

# Verify
bit verify whitepaper.pdf --txid=b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c

# Output:
# ✓ MATCH — PROVEN: You possessed this exact file at block time.
```

## Commands

| Command | Description |
|---------|-------------|
| `bit init` | Generate your identity key |
| `bit status` | Show identity, wallet, and stamp count |
| `bit stamp <file>` | Stamp a file to Bitcoin |
| `bit verify <file> --txid=<id>` | Verify a file against an on-chain stamp |
| `bit search <query>` | Search your local stamp database |

### Options

```bash
bit stamp file.pdf --type=source_code     # Tag content type
bit stamp file.pdf --mainnet              # Use Bitcoin mainnet
bit stamp file.pdf --utxo=abc123:0        # Specify UTXO for fees
bit stamp --text "my idea" --utxo=abc:0   # Stamp from text, not file
bit stamp file.pdf --meta='{"v":"1.0"}'   # Attach metadata
bit stamp file.pdf --fee=5000             # Custom fee in satoshis
```

## Public Index (optional)

Share stamps with the network via an optional public index:

```bash
docker compose up -d
curl http://localhost:8787/health

# Record a stamp
curl -X POST http://localhost:8787/stamp \
  -H "Content-Type: application/json" \
  -d '{"hash":"abc...","txid":"def...","content_type":"document","key_fingerprint":"abcd1234"}'

# Look up a stamp
curl http://localhost:8787/stamp/abc...

# Search
curl "http://localhost:8787/search?q=abc&field=hash"
```

## Pre-commit Hook (optional)

Auto-stamp files on every commit:

```bash
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Stamps all staged `.md` and `.pdf` files. Edit the hook to change tracked extensions.

## Roadmap

- [x] Core protocol schema
- [x] CLI (init, stamp, verify, search)
- [x] Bitcoin testnet broadcast
- [x] Local SQLite database
- [x] Public index API
- [x] Pre-commit git hook
- [x] Live on-chain verification
- [ ] PyPI release (`pip install bit-protocol`)
- [ ] GitHub Action for CI stamping
- [ ] VS Code extension
- [ ] UTXO scanner (auto-select inputs)
- [ ] HD key derivation (BIP32/BIP44 for IP families)
- [ ] Fractional IP tokenization
- [ ] Multi-chain support (Ethereum, Solana)

## Development

```bash
git clone https://github.com/washingtoneimae-dot/bit.git
cd bit
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Strategy

Bit Protocol is the **Linux to Bernstein's Windows** — an open-source protocol that any developer can self-host, customize, or contribute to.

| | Bernstein | Bit |
|---|---|---|
| Model | Closed SaaS | Open Core |
| Price | $54–$329/mo | Free (self-host) |
| Keys | Account-based | Self-sovereign |
| Registry | Centralized | Bitcoin + optional index |
| Legal | WIPO-recognized | Community-built |
| Tokenization | None | Planned (fractional IP) |

The strategy: free self-host → developer adoption → prior art shield → network of interoperable registries that no single entity controls or can ignore.

## License

MIT
