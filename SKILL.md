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

## Verification — trustless

Anyone can verify without trusting you or your server:

```bash
# 1. Get the file
curl -O https://raw.githubusercontent.com/YOUR_USER/timestamped-ip/main/concepts/stamped/my-invention.md

# 2. Import your public key
gpg --import keys/YOUR_KEY.asc

# 3. Verify the GPG signature
gpg --verify my-invention.md.asc

# 4. Check the Bitcoin transaction
# OP_RETURN contains: protocol magic + version + content type + SHA-256 hash
# Visit: https://blockstream.info/testnet/tx/<txid>
```

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
