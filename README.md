# Bit Protocol

**Decentralized IP Proof of Existence on Bitcoin.**

Stamp your files, code, and ideas to the Bitcoin blockchain as immutable proof that you had them at a specific point in time. No disclosure. No gatekeepers. No subscription fees.

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

Send some tBTC to your address (shown by `bit status`) from a testnet faucet.

### 4. Stamp a file

```bash
bit stamp myfile.pdf --utxo=<txid>:<vout>
```

### 5. Verify

```bash
bit verify myfile.pdf --txid=<txid>
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

## Roadmap

- [x] Core protocol schema
- [x] CLI (init, stamp, verify, search)
- [x] Bitcoin testnet broadcast
- [x] Local SQLite database
- [x] Public index API
- [ ] Pre-commit git hook (`bit stamp` on commit)
- [ ] GitHub Action for CI stamping
- [ ] VS Code extension
- [ ] UTXO scanner (auto-select inputs)
- [ ] HD key derivation (BIP32/BIP44 for IP families)
- [ ] Fractional IP tokenization
- [ ] Multi-chain support (Ethereum, Solana)

## Development

```bash
git clone https://github.com/yourusername/bit-protocol.git
cd bit-protocol
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
