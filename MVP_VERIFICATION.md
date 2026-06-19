# MVP Verification — Bit Protocol on Bitcoin Testnet

**Date:** June 19, 2026
**Network:** Bitcoin Testnet
**File:** `tests/fixtures/sample.txt`
**Content:** "This is a sample file for testing Bit Protocol stamps. It contains some text that can be hashed and verified."

## End-to-End Proof

### Step 1: Generate identity

```bash
$ bit init
✓ Bit Protocol identity created
  Public key:  03712ed346b3bd6416c7f09891133c3bfd4e5c21cb5aff3ae517542e29fe6aa296
  Fingerprint: 82597114
  Saved to:    ~/.bit/key.pem
```

### Step 2: Get testnet BTC

Sent to `mrF25nP77VrRS3kK1S7h8bUTgcsjWk1dSq` via testnet faucet.

```
tx: 469208a534f9c42dcfad24f674d3d255ad57f531c554b05fd1cf1b33d6cf0034
Amount: 0.00117514 tBTC
```

### Step 3: Stamp file

```bash
$ bit stamp tests/fixtures/sample.txt --utxo=62256e0bda6e7972...:0
```

**Result:**
```
✓ Stamped to Bitcoin testnet!
  txid: b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c
  Hash: 855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be
```

### Step 4: Verify

```bash
$ bit verify tests/fixtures/sample.txt --txid=b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c
```

**Result:**
```
✓ MATCH
  On-chain hash: 855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be
  Content type:  document
  Key fp:        82597114
✓ PROVEN: You possessed this exact file at block time.
```

## On-Chain Evidence

- **Transaction:** https://blockstream.info/testnet/tx/b98761beaf2b4e8fb60b3fe6ee767f2cb9347fb785f8b57e02328b00cef4ab4c
- **OP_RETURN hex:** `6a294249540101855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be82597114`
- **Decoded:**
  - `6a` = OP_RETURN
  - `29` = 41 bytes follow
  - `424954` = "BIT" (protocol magic)
  - `01` = version 1
  - `01` = content type: document
  - `855659f9da3c7738bb5b5b73b6fc8a4285f1d26841284fe628391ade117af5be` = SHA-256 hash
  - `82597114` = key fingerprint

## Key Learnings

| Issue | Fix |
|-------|-----|
| `bitcoinlib` uses SegWit by default | Force `witness_type='legacy'` for Blockstream API |
| API returns `scriptpubkey_type='op_return'` | Accept both `'op_return'` and `'nulldata'` |
| `cryptography>=49` removed `PrivateFormat.Raw` for EC | Use `private_numbers().private_value.to_bytes(32)` |
| `coincurve` build fails on Python 3.14 | Use `cryptography` library instead |
| Faucets block WSL IPs | Request from native Windows browser |

## Test Suite

```
$ pytest tests/ -v
============================= 21 passed in 0.05s ==============================
```

## Cost

- Transaction fee: 2,000 satoshis (~$0.02 at time of writing)
- Remaining balance: 113,514 satoshis
