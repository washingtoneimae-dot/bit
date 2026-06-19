# Bit Protocol

**Decentralized IP Proof of Existence on Bitcoin.**

Stamp your files, code, and ideas to the Bitcoin blockchain as immutable proof that you had them at a specific point in time. No disclosure. No gatekeepers. No subscription fees.

```bash
pip install bit-protocol
bit init
bit stamp my-whitepaper.pdf
bit verify my-whitepaper.pdf --txid=<txid>
```

> **✅ Verified on Bitcoin Testnet**
> [Sample file](https://blockstream.info/testnet/tx/b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c) ·
> [Conception doc](https://blockstream.info/testnet/tx/64f0bb98e5a90084ee4f6523fc1d96cee0634811bb08c83cfe52f2a532b05002) ·
> [5G SSB Observer](https://blockstream.info/testnet/tx/3ed6dc22bd669c04620490f29e0b50adf8332e009f5e5e2786e3cc1a42048b0c)

---

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
              Local SQLite cache ←──── Peer sync (optional)
```

### OP_RETURN Schema

```
| 3 bytes  | 1 byte  | 1 byte  | 32 bytes   | 4 bytes   | ≤42 bytes |
| Protocol | Version | Type    | SHA-256    | Key FP    | Metadata  |
| "BIT"    | 0x01    | 0x01-04 | File hash  | Key ID    | JSON      |
```

Total: **41–83 bytes** — fits Bitcoin's original OP_RETURN limit and is forward-compatible with Bitcoin Core v30's 100KB expansion.

## Quickstart

```bash
# 1. Install
pip install bit-protocol

# 2. Generate your identity
bit init

# 3. Get testnet BTC from a faucet (send to address from `bit status`)
#    https://coinfaucet.eu/en/btc-testnet/

# 4. Stamp a file — UTXO auto-detected, no hex hunting
bit stamp myfile.pdf

# 5. Verify
bit verify myfile.pdf --txid=<txid>

# 6. Check stats
bit status
```

## Commands

| Command | Description |
|---------|-------------|
| `bit init` | Generate your identity key |
| `bit status` | Show identity, peers, and stamp count |
| `bit stamp <file>` | Stamp a file to Bitcoin |
| `bit verify <file> --txid=<id>` | Verify a file against an on-chain stamp |
| `bit search <query>` | Search your local stamp database |
| `bit peer add <url>` | Connect to another index for stamp sharing |
| `bit peer list` | Show all connected peers |
| `bit peer sync` | Pull stamps from all connected peers |

### Options

```bash
bit stamp file.pdf --type=source_code      # Tag content type
bit stamp file.pdf --mainnet               # Use Bitcoin mainnet
bit stamp file.pdf --utxo=abc123:0         # Manual UTXO override
bit stamp --text "my idea"                 # Stamp from text, not file
bit stamp file.pdf --meta='{"v":"1.0"}'    # Attach metadata
bit stamp file.pdf --fee=5000              # Custom fee in satoshis
```

## Peer-to-Peer Sync

Bit indexes can discover and exchange stamps over a gossip network.

```bash
# Alice runs her index
docker compose up -d     # bit.alice.com:8787

# Bob connects and syncs
bit peer add https://bit.alice.com:8787
bit peer sync
```

```
bit peer add <url>      → Register a peer
bit peer list           → Show all connected peers
bit peer sync           → Pull new stamps from all peers
bit peer remove <url>   → Disconnect a peer
```

**Trust model:** The blockchain is the source of truth. Every stamp synced from a peer can be independently verified against Bitcoin. Peers are a search network, not a consensus layer.

## Public Index (optional)

Run your own public index to share stamps with the network:

```bash
docker compose up -d
```

### API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/stamp` | Record a stamp `{hash, txid, content_type, key_fingerprint, public_key?, metadata?, network?}` |
| `GET` | `/stamp/{hash}` | Look up a stamp by SHA-256 hash |
| `GET` | `/search?q=&field=` | Search by hash, txid, key_fingerprint, or content_type |
| `GET` | `/sync?since=<ts>&limit=` | Pull stamps indexed after a timestamp (peer sync) |
| `GET` | `/health` | Health check + stamp count |

```bash
curl http://localhost:8787/health

POST /stamp
curl -X POST http://localhost:8787/stamp \
  -H "Content-Type: application/json" \
  -d '{"hash":"abc...","txid":"def...","content_type":"document","key_fingerprint":"abcd1234"}'

GET /stamp/{hash}
curl http://localhost:8787/stamp/abc...

GET /search
curl "http://localhost:8787/search?q=abc&field=hash"

GET /sync
curl "http://localhost:8787/sync?since=0&limit=100"
```

## Pre-commit Hook (optional)

Auto-stamp staged files on every commit:

```bash
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Tracks `.md`, `.pdf`, `.txt`, `.py`, `.js` files by default. Edit `TRACKED_EXTENSIONS` in the hook to change. Requires `BIT_UTXO` env var or a funded wallet.

## Verified Proofs

These documents exist in this repo and are timestamped on Bitcoin Testnet:

| Document | Txid | Purpose |
|----------|------|---------|
| `BIT_PROTOCOL_CONCEPTION.md` | [`64f0bb98...`](https://blockstream.info/testnet/tx/64f0bb98e5a90084ee4f6523fc1d96cee0634811bb08c83cfe52f2a532b05002) | Project conception & architecture decisions |
| `5G_SSB_Phase-Shift_Observer.md` | [`3ed6dc22...`](https://blockstream.info/testnet/tx/3ed6dc22bd669c04620490f29e0b50adf8332e009f5e5e2786e3cc1a42048b0c) | Zero-hardware tower structural health monitor |

Verify any of them:

```bash
git clone https://github.com/washingtoneimae-dot/bit.git
cd bit
bit verify BIT_PROTOCOL_CONCEPTION.md --txid=64f0bb98...
bit verify 5G_SSB_Phase-Shift_Observer.md --txid=3ed6dc22...
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `No spendable UTXO found` | No tBTC in your wallet | Send tBTC from a [faucet](https://coinfaucet.eu/en/btc-testnet/) to your address (`bit status`) |
| `Faucet says "bots not allowed"` | WSL/datacenter IP flagged | Open the faucet in a normal Windows/Mac browser instead |
| `Broadcast failed: TX decode` | Network issue or Blockstream down | Wait 30s and retry; check [Blockstream status](https://blockstream.info/testnet/) |
| `The read operation timed out` | Network connectivity issue | Retry; if persistent, use `--utxo=<txid>:<vout>` to skip UTXO scan |
| `metadata exceeds remaining space` | Metadata JSON too long for OP_RETURN | Keep metadata under 42 bytes of JSON; use short keys |

## Development

```bash
git clone https://github.com/washingtoneimae-dot/bit.git
cd bit
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Roadmap

- [x] Core protocol schema (OP_RETURN payload standard)
- [x] CLI (init, stamp, verify, search, status)
- [x] Bitcoin testnet broadcast + mainnet support
- [x] UTXO scanner (auto-discover spendable inputs)
- [x] Local SQLite database
- [x] Public index API (FastAPI + Docker)
- [x] Peer-to-peer sync between indexes
- [x] Pre-commit git hook
- [x] GitHub CI (test, build, publish to PyPI)
- [x] PyPI release (`pip install bit-protocol`)
- [x] Live on-chain verification (3 stamps verified)
- [ ] HD key derivation (BIP32/BIP44 for IP families)
- [ ] Fractional IP tokenization
- [ ] Multi-chain support (Ethereum, Solana)
- [ ] VS Code extension

## Strategy

Bit Protocol is the **Linux to Bernstein's Windows** — an open-source protocol that any developer can self-host, customize, or contribute to.

| | Bernstein | Bit |
|---|---|---|
| Model | Closed SaaS | Open Core |
| Price | $54–$329/mo | Free (self-host) |
| Keys | Account-based | Self-sovereign |
| Registry | Centralized | Bitcoin + peer network |
| Legal | WIPO-recognized | Community-built + on-chain proof |
| Tokenization | None | Planned (fractional IP) |

The strategy: free self-host → developer adoption → prior art shield → network of interoperable registries that no single entity controls or can ignore.

## Security

Private keys are stored in `~/.bit/key.pem` with `chmod 600` (owner read/write only). The key never leaves your machine. Transactions are signed locally. Blockchain verification is trustless — anyone can independently verify a stamp without the Bit Protocol software.

See `SECURITY.md` for vulnerability reporting.

## License

MIT
