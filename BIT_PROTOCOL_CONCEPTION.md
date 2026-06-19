Bit Protocol — Session Summary
Date: June 19, 2026
Key: 82597114

This document summarizes the conception and MVP build of Bit Protocol,
a decentralized IP proof-of-existence system on Bitcoin.

=== Architecture Decisions ===

1. No blockchain fork. Bitcoin Core v30 (Oct 2025) raised OP_RETURN
   to 100KB, making Bitcoin sufficient as the data layer.

2. OP_RETURN payload schema locked at 41-83 bytes:
   BIT | v0x01 | content_type | SHA-256(32B) | key_fingerprint(4B) | metadata(≤42B)

3. Legacy transaction format required for Blockstream API compatibility.

4. cryptography library over coincurve (coincurve fails on Python 3.14).

5. Bitcoin testnet first, mainnet opt-in via --mainnet flag.

=== Strategic Positioning ===

- Open-source alternative to Bernstein.io (closed SaaS at $54-329/mo)
- Strategy: free self-host → developer adoption → prior art shield
- "Linux to Bernstein's Windows" — protocol over platform
- Phases: Bitcoin OP_RETURN (v1) → Elements sidechain (v2) → tokenization (v3)

=== MVP Verification ===

Two stamps broadcast and verified on Bitcoin Testnet:

Stamp 1 — b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c
  File: sample.txt → 855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be
  Content: document, key 82597114

Stamp 2 — 9d7930569879d0725988d6ea676dfac76374abbd2241324ab8d300b8fb1c86d6
  File: sample.txt → 855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be
  Content: document (auto-UTXO test)

=== Features Built ===

- CLI: init, stamp, verify, search, status (Click)
- secp256k1 key generation and PEM storage
- UTXO scanner (auto-discover spendable inputs)
- Local SQLite stamp cache
- Peer-to-peer sync between indexes (add/remove/list/sync)
- Docker public index API (FastAPI + SQLite, GET/POST /stamp, /search, /sync)
- GitHub CI (test, build, publish to PyPI, stamp release)
- Pre-commit git hook for auto-stamping
- Published to PyPI as bit-protocol v0.2.0

=== Key Lessons ===

- Blockstream API returns scriptpubkey_type='op_return' not 'nulldata'
- UTXO values from Blockstream are in satoshis (not BTC)
- bitcoinlib defaults to SegWit — must force witness_type='legacy'
- Faucets block WSL IPs — use Windows browser for faucet

=== On-Chain Proof ===
TXID: 64f0bb98e5a90084ee4f6523fc1d96cee0634811bb08c83cfe52f2a532b05002
View: https://blockstream.info/testnet/tx/64f0bb98e5a90084ee4f6523fc1d96cee0634811bb08c83cfe52f2a532b05002
