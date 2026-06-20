---
name: ip-timestamping
description: "Complete IP timestamping workflow — GPG signing, Bitcoin testnet stamping via Bit Protocol, automated registry with git push. One command: stamp <file> [category]"
version: 1.0.0
license: MIT
platforms: [linux, macos, wsl]
metadata:
  hermes:
    tags: [ip, timestamping, bitcoin, gpg, proof-of-existence, blockchain]
    related_skills: [bitcoin-python-dev, plan]
---

# IP Timestamping

One-command cryptographic proof of existence for your ideas, code, and designs. GPG signs your document (proving authorship), then stamps its SHA-256 hash to Bitcoin testnet (proving it existed before a specific block). The signed document and stamp log auto-push to GitHub.

## When to use

- You have an idea, algorithm, or design you want timestamped proof for
- You want to establish prior art without filing a patent
- You want independently verifiable proof that a document existed at a point in time
- You want everything in one command: sign → stamp → log → push

## Prerequisites

```bash
# 1. GPG key (for signing)
gpg --full-generate-key
# Use RSA 4096, no expiry, your email

# 2. Bit Protocol (for Bitcoin testnet stamping)
pip install bit-protocol
bit init

# 3. Fund your testnet address
bit status  # shows your address
# Send tBTC from https://coinfaucet.eu/en/btc-testnet/
```

## Setup — one time per machine

### 1. Create your IP registry

```bash
mkdir -p ~/timestamped-ip/{concepts,protocols,designs,systems}/{stamped,pending}
mkdir -p ~/timestamped-ip/proofs
mkdir -p ~/timestamped-ip/keys

cd ~/timestamped-ip
git init
git add -A && git commit -m "init: IP timestamping registry"
gh repo create timestamped-ip --public --source=. --push
```

### 2. Create the stamp script

Save as `~/.hermes/scripts/stamp.sh` and `chmod +x` it. The script does:

```
GPG clearsign → Bitcoin testnet stamp → move to stamped/ → log in INDEX.md → git push
```

Full script:

```bash
#!/bin/bash
set -e

FILE="$1"
CATEGORY="${2:-concepts}"
IP_DIR="$HOME/timestamped-ip"
BIT_DIR="$HOME/bit-protocol"
INDEX="$IP_DIR/INDEX.md"

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Usage: stamp <file> [concepts|protocols|designs|systems]"
    exit 1
fi

FILENAME=$(basename "$FILE")
NAME="${FILENAME%.*}"

echo "=== Stamping: $NAME ==="
echo "  Category: $CATEGORY"

# 1. GPG clearsign
echo "  [1/4] Signing with GPG..."
gpg --clearsign "$FILE"
SIGNED="${FILE}.asc"

# 2. Stamp to Bitcoin testnet
echo "  [2/4] Stamping to Bitcoin testnet..."
cd "$BIT_DIR" && source venv/bin/activate 2>/dev/null || true
TX_OUTPUT=$(bit stamp "$SIGNED" 2>&1)
TXID=$(echo "$TX_OUTPUT" | grep -oP 'txid[:\s]+\K[a-f0-9]{64}' | head -1)
echo "  → $TXID"

# 3. Move to stamped/
STAMP_DIR="$IP_DIR/$CATEGORY/stamped"
mkdir -p "$STAMP_DIR"
mv "$FILE" "$STAMP_DIR/"
mv "$SIGNED" "$STAMP_DIR/"

# 4. Log in INDEX.md
SHA=$(sha256sum "$STAMP_DIR/$FILENAME" | cut -d' ' -f1 | head -c 10)
DATE=$(date +%Y-%m-%d)
NUM=$(grep -c '^|' "$INDEX" 2>/dev/null || echo 0)
NUM=$((NUM + 1))
ENTRY="| $NUM | $DATE | $CATEGORY | $NAME | ${SHA}... | [\`${TXID:0:8}...\`](https://blockstream.info/testnet/tx/$TXID) | ✓ |"
echo "$ENTRY" >> "$INDEX"
echo "  [4/4] Logged to INDEX.md"

# 5. Push registry to GitHub
cd "$IP_DIR"
git add INDEX.md "$STAMP_DIR/$FILENAME" "$STAMP_DIR/$FILENAME.asc"
git commit -m "stamp #$NUM: $NAME ($CATEGORY) - $TXID" --quiet
git push --quiet 2>/dev/null
echo "  [✓] Pushed to GitHub"

echo ""
echo "=== Done ==="
echo "  File:    $STAMP_DIR/$FILENAME"
echo "  Txid:    $TXID"
echo "  Verify:  https://blockstream.info/testnet/tx/$TXID"
```

### 3. Add the alias

```bash
echo "alias stamp='~/.hermes/scripts/stamp.sh'" >> ~/.bashrc
source ~/.bashrc
```

## Daily use

```bash
# Write your idea
vim my-invention.md

# One command
stamp my-invention.md concepts

# Output:
# === Stamping: my-invention ===
#   [1/4] Signing with GPG...
#   [2/4] Stamping to Bitcoin testnet...
#   → abc123...txid
#   [3/4] Moved to concepts/stamped/
#   [4/4] Logged to INDEX.md
#   [✓] Pushed to GitHub
# === Done ===
#   Verify:  https://blockstream.info/testnet/tx/abc123...
```

Your file is now:
- GPG-signed (proves YOU authored it)
- Stamped on Bitcoin testnet (proves WHEN)
- In your public registry on GitHub
- Independently verifiable by anyone

## Verifying your own stamps

```bash
# 1. Get the signed file
curl -O https://raw.githubusercontent.com/YOUR_USER/timestamped-ip/main/concepts/stamped/my-invention.md

# 2. Import your public key
gpg --import keys/YOUR_KEY.asc

# 3. Verify the GPG signature
gpg --verify my-invention.md.asc

# 4. Check the Bitcoin transaction
# OP_RETURN contains: protocol magic + version + content type + SHA-256 hash
# Visit: https://blockstream.info/testnet/tx/<txid>
```

## Verifying other people's stamps

This is the power of the system — you can verify anyone's IP claims without trusting them, their server, or any central authority.

### Step 1: Find their stamp

Stamps are public. You can find them via:
- Their GitHub registry (e.g. `github.com/<user>/timestamped-ip`)
- Their `INDEX.md` which lists every stamp with txids
- A Bitcoin block explorer if you have the txid
- Peer indexes if they run one

Example — Alice claims she invented something on March 15, 2025. Her `INDEX.md` shows:

```markdown
| 7 | 2025-03-15 | concepts | Gradient Descent 2.0 | a1b2c3d4e5... | [`f9e8d7c6...`](https://blockstream.info/testnet/tx/f9e8...) | ✓ |
```

### Step 2: Get her document and signature

```bash
# Clone her registry
git clone https://github.com/alice/timestamped-ip.git
cd timestamped-ip

# The document and its .asc signature are both in concepts/stamped/
ls concepts/stamped/gradient-descent-2.0.md*
# → gradient-descent-2.0.md
# → gradient-descent-2.0.md.asc
```

### Step 3: Get her public key

```bash
# Option A: From her repo
gpg --import keys/alice.asc

# Option B: From a keyserver
gpg --keyserver keys.openpgp.org --recv-keys <her-fingerprint>

# Option C: From the signature itself (extracts key ID)
gpg --verify gradient-descent-2.0.md.asc 2>&1 | grep "using.*key"
# → using RSA key ABCD1234...
gpg --keyserver keys.openpgp.org --recv-keys ABCD1234...
```

### Step 4: Verify authorship (GPG)

```bash
gpg --verify concepts/stamped/gradient-descent-2.0.md.asc

# Good signature → Alice definitely wrote this
# BAD signature → file was tampered with
# Can't check → need her public key first (step 3)
```

### Step 5: Verify timing (Bitcoin)

```bash
# Compute the SHA-256 of the file she stamped
sha256sum concepts/stamped/gradient-descent-2.0.md

# Now look at the Bitcoin transaction
# Option A: Block explorer
curl -s https://blockstream.info/testnet/api/tx/f9e8d7c6... | python3 -c "
import sys, json
tx = json.load(sys.stdin)
for out in tx['vout']:
    if out['scriptpubkey_type'] == 'op_return':
        hex_data = out['scriptpubkey'][4:]  # skip '6a' + len byte
        raw = bytes.fromhex(hex_data)
        # Bytes 5-36 are the SHA-256 (after 3B magic + 1B version + 1B type)
        stamped_hash = raw[5:37].hex()
        print(f'On-chain hash: {stamped_hash}')
"

# Option B: bit verify
bit verify concepts/stamped/gradient-descent-2.0.md --txid=f9e8d7c6...
```

### What the verification proves

| Check | Proves | Trust required |
|-------|--------|---------------|
| GPG signature is valid | Alice authored this exact document | Trust Alice's public key (one-time) |
| SHA-256 matches OP_RETURN | The document you have is what was stamped | None (math only) |
| Transaction is in a block | The document existed BEFORE that block was mined | None (Bitcoin PoW) |
| Block timestamp | The document existed before block time ±2 hours | None (blockchain consensus) |

### Red flags

| Situation | What it means |
|-----------|--------------|
| GPG key was created AFTER the Bitcoin tx | The key didn't exist at stamp time — authorship unprovable |
| SHA-256 doesn't match OP_RETURN | The file she's showing you is not what was stamped |
| No GPG signature, just a hash | Anyone could have stamped it — proves timing but NOT authorship |
| Repository has force-pushes | INDEX.md history may have been rewritten — check Bitcoin, not git |

No gatekeepers. No subscription. No disclosure. Just math.

## Folder structure

```
timestamped-ip/
  README.md          ← registration info, your GPG fingerprint, verification steps
  INDEX.md           ← full stamping log (date, hash, txid, category)
  keys/              ← your GPG public key (.asc)
  concepts/
    stamped/         ← confirmed on Bitcoin testnet
    pending/         ← drafted, not yet stamped
  protocols/
  designs/
  systems/
  proofs/            ← verification scripts
```

## INDEX.md format

```markdown
| # | Date | Category | Title | SHA-256 | Txid | Verified |
|---|------|----------|-------|---------|------|----------|
| 1 | 2025-01-15 | concepts | My Algorithm | abc123de... | [`f4e2a1...`](https://...) | ✓ |
```

## Security

- **Private GPG key:** Local only (`~/.gnupg/`), never shared, never committed
- **Bitcoin private key:** Local only (`~/.bit/key.pem`, 0600), never shared
- **Public key:** Published in `keys/` and on `keys.openpgp.org` for verification
- **Backup:** Encrypt both private keys with GPG and store offline

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `No spendable UTXO` | No tBTC in wallet | Send from faucet to your `bit status` address |
| `gpg: skipped` | Wrong key ID | Use `gpg --list-secret-keys` to find your key |
| `bit: command not found` | Bit Protocol not installed | `pip install bit-protocol && bit init` |
| Port already in use (index) | Docker conflict | `docker compose down && docker compose up -d` |
