# Contributing to Bit Protocol

Thanks for wanting to build on this. Bit Protocol is designed to be forked,
extended, and improved by anyone. Here's how to get started.

## Quick Start

```bash
git clone https://github.com/washingtoneimae-dot/bit.git
cd bit
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## How to Add On

The OP_RETURN payload schema is the standard. Everything builds on it.

```
| 3 bytes  | 1 byte  | 1 byte  | 32 bytes   | 4 bytes   | ≤42 bytes |
| "BIT"    | 0x01    | 0x01-04 | SHA-256    | Key FP    | JSON      |
```

If you build a tool that reads or writes this schema, it's compatible with
every other Bit Protocol tool. No coordination needed.

### Ideas for Extensions

- **GitHub Action** — auto-stamp on every release
- **VS Code extension** — right-click → stamp
- **VS Code extension** — right-click → verify
- **UTXO scanner** — auto-detect spendable UTXOs (remove `--utxo` requirement)
- **Web dashboard** — browse stamps, verify via drag-and-drop
- **Multi-chain** — stamp to Ethereum, Solana, or other chains
- **BIP32 HD keys** — hierarchical key derivation for IP families
- **Cross-registry sync** — federate public indexes into a prior art network
- **Tokenization** — fractional IP ownership as custom assets (Elements phase)

### OSS Principles

1. **Lock the schema early, extend later.** The OP_RETURN format is the
   only thing that needs to be standard. Everything else is a plugin.
2. **Local-first.** The CLI should work with zero network dependencies
   (except the Bitcoin broadcast itself).
3. **Self-sovereign keys.** Users generate their own keys. No accounts.
   No logins. No vendor lock-in.
4. **Testnet by default.** Mainnet is opt-in via `--mainnet`.

## Code Structure

```
src/bit_protocol/
├── hash.py       # SHA-256 file hashing
├── payload.py    # OP_RETURN build/parse (THE STANDARD)
├── types.py      # Dataclasses, enums
├── key.py        # secp256k1 key management
├── broadcast.py  # Bitcoin tx construction + Blockstream API
├── db.py         # Local SQLite cache
└── cli.py        # Click CLI (init, stamp, verify, search, status)
```

## Testing

```bash
pytest tests/ -v           # All tests
pytest tests/test_core.py  # Core tests only
```

Write tests for any new module. The payload schema tests are the most
critical — they protect the standard.

## Pull Request Process

1. Fork the repo
2. Create a feature branch
3. Write tests
4. Ensure all tests pass
5. Open a PR with a clear description of what and why

## License

MIT — fork freely, build whatever you want.
