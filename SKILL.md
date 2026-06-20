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

### Designed for AI agents

This workflow is built so you tell your AI agent what to do — the agent handles everything:

```
You: "timestamp my gradient descent idea"
Agent: writes the document → GPG signs it → stamps to Bitcoin → logs it → pushes to GitHub
       → "Done. Txid: f9e8d7... Verify: https://blockstream.info/testnet/tx/f9e8d7..."
```

Once the one-time setup is done (below), the agent uses a single `stamp` command for every IP filing. No manual steps. No remembering flags. Just tell the agent what to protect.

### For developers setting up their own agent

If you're a developer teaching your AI agent this workflow, run the setup once (prerequisites + alias), then your agent can file IP on command.

### For AI agents — how to handle an IP filing request

When your user says "timestamp this" / "file this IP" / "stamp my idea":

0. **Pre-flight check** — run the health check from Prerequisites. If anything is missing (no GPG key, no tBTC, no stamp script), stop and tell the developer what to install. Don't proceed with missing prerequisites — the stamp will fail.

1. **Write the document** — create a well-structured `.md` file describing the concept, algorithm, or design. Include: title, date, summary, technical claims, and any novel elements. Save to `~/timestamped-ip/<category>/pending/<name>.md`.

2. **Stamp it** — run `stamp <path> <category>`. The alias handles GPG signing, Bitcoin broadcast, file organization, INDEX.md logging, and git push automatically.

3. **Report back** — tell the user the txid and verification URL. The stamp is now cryptographically proven on Bitcoin testnet and publicly verifiable at `github.com/<user>/timestamped-ip`.

4. **Ask about key backup** — if this is the first stamp (or you detect no backup exists), ask: "Your private keys (GPG + Bitcoin) are only on this machine. Want me to encrypt and back them up?" If yes, run the backup procedure in the Security section below. This protects the developer's identity — without these keys, their stamped IP can't be proven as theirs.

No manual steps between writing and verification. The agent owns the entire pipeline.

| User says | Agent uses category | Example |
|-----------|-------------------|---------|
| "timestamp my algorithm" / "a new formula" | `concepts` | Theoretical ideas, math, algorithms |
| "timestamp this protocol" / "a blockchain spec" | `protocols` | OP_RETURN schemas, data formats, network specs |
| "timestamp my architecture" / "system design" | `designs` | System diagrams, data models, UI/UX |
| "timestamp this codebase" / "my implementation" | `systems` | Working software, implementations |

## When to use

- You have an idea, algorithm, or design you want timestamped proof for
- You want to establish prior art without filing a patent
- You want independently verifiable proof that a document existed at a point in time
- You want everything in one command: sign → stamp → log → push

## Prerequisites — must be done before anything works

These five things must exist before the first stamp. The agent should check all of them when asked to file IP.

### Quick health check

```bash
# Run this — if all three pass, you're ready
gpg --list-secret-keys | grep -q "sec" && echo "✓ GPG key exists" || echo "✗ No GPG key — run: gpg --full-generate-key"
ls ~/.bit/key.pem >/dev/null 2>&1 && echo "✓ Bit Protocol initialized" || echo "✗ Not initialized — run: pip install bit-protocol && bit init"
bit status 2>/dev/null | grep -q "Identity" && bit status | grep "stamps" || echo "✗ No tBTC — fund your address from https://coinfaucet.eu/en/btc-testnet/"
ls ~/.hermes/scripts/stamp.sh >/dev/null 2>&1 && echo "✓ stamp alias ready" || echo "✗ No stamp script — see Setup section"
ls ~/timestamped-ip/INDEX.md >/dev/null 2>&1 && echo "✓ Registry exists" || echo "✗ No registry — see Setup section"
```

### 1. GPG key

```bash
gpg --full-generate-key
# Use RSA 4096, no expiry, your email
```

### 2. Bit Protocol

```bash
pip install bit-protocol
bit init
```

### 3. Funded testnet address

```bash
bit status  # shows your address
# Send tBTC from https://coinfaucet.eu/en/btc-testnet/
# You need testnet BTC for transaction fees (~500 satoshis per stamp)
```

### 4. The `stamp` script and alias

See Setup section below — one-time install.

### 5. Your IP registry

See Setup section below — one-time folder + git init.

### For AI agents — how to set up each prerequisite

When the health check finds something missing, don't just print an error. Help the developer fix it, or do it yourself:

| Missing | Agent can do? | Action |
|---------|:---:|--------|
| GPG key | ✅ Yes | Run `gpg --batch --generate-key` with the developer's name/email. Ask them for their name and email first. |
| Bit Protocol | ✅ Yes | Run `pip install bit-protocol && bit init`. Use the venv if one exists in the project. |
| tBTC funds | ❌ No | Show the developer their address (`bit status`) and the faucet URL. They must fund it in a browser. |
| Stamp script | ✅ Yes | Create `~/.hermes/scripts/stamp.sh` from the template below, `chmod +x` it, and add the alias to `~/.bashrc`. |
| IP registry | ✅ Yes | Create the folder structure, `git init`, and `gh repo create`. Ask the developer for the repo name first. |

**When the developer says "set me up" or "file my first IP":**

1. Run the health check.
2. For each ✗, follow the table above — do what you can, ask the developer for what only they can do.
3. Re-run the health check until all five show ✓.
4. Then proceed to the stamp workflow.

**Don't silently skip missing prerequisites.** A stamp with no GPG key still works on-chain but proves nothing about authorship. A stamp with no tBTC fails outright. Check first.

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

## Daily use — tell your agent, not your terminal

```bash
# You say this to your AI agent:
"stamp my idea about zero-knowledge decaf proofs"

# The agent does:
# 1. Writes a well-structured document (~/.hermes/.../zk-decaf.md)
# 2. Runs: stamp ~/.hermes/.../zk-decaf.md concepts
# 3. Reports back:
#
# === Stamping: zk-decaf ===
#   [1/4] Signing with GPG...
#   [2/4] Stamping to Bitcoin testnet...
#   → abc123...txid
#   [3/4] Moved to concepts/stamped/
#   [4/4] Logged to INDEX.md
#   [✓] Pushed to GitHub
# === Done ===
#   Verify:  https://blockstream.info/testnet/tx/abc123...
```

The agent handles formatting, signing, broadcasting, logging, and pushing. You just describe the idea. Your IP registry at `github.com/<you>/timestamped-ip` updates automatically.

If you're running the command yourself (not through an agent):

```bash
stamp my-invention.md concepts

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

## Try it now — verify a real stamp

This is a live, working example. It verifies a SACCO system specification that was stamped on June 20, 2026. Copy-paste the whole block:

```bash
# Clone the public registry
git clone https://github.com/washingtoneimae-dot/timestamped-ip.git
cd timestamped-ip

# Import the author's public key
gpg --import keys/washington-imae.asc
# → key 7989D2E21C9D29E657422BCA2B88E8165712F528 imported

# Verify the GPG signature (proves authorship)
gpg --verify systems/stamped/sacco-system.md.asc
# → Good signature from "Washington Imae"

# Compute the SHA-256 yourself
sha256sum systems/stamped/sacco-system.md

# Extract the on-chain hash from Bitcoin
curl -s https://blockstream.info/testnet/api/tx/d6ddec32da4406952d39529f2a7d2d1d423050aa605bcf49fa433b7d0bab562e | python3 -c "
import sys, json
tx = json.load(sys.stdin)
for out in tx['vout']:
    if out['scriptpubkey_type'] == 'op_return':
        raw = bytes.fromhex(out['scriptpubkey'][4:])
        print(f'Protocol: {raw[0:3].decode()}')
        print(f'Version:  {raw[3]}')
        print(f'SHA-256:  {raw[5:37].hex()}')
"
# Both SHA-256 values should match → the file hasn't been modified

# Or use Bit Protocol CLI instead of curl
bit verify systems/stamped/sacco-system.md --txid=d6ddec32da4406952d39529f2a7d2d1d423050aa605bcf49fa433b7d0bab562e
```

You just proved, without trusting anyone:
- Who wrote it (GPG signature)
- When it existed (Bitcoin block timestamp)
- That it hasn't changed (SHA-256 match)

Everything you needed was public. The private keys never left the author's machine.

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

### Backing up your private keys

Without these keys, you lose the ability to prove you authored your stamps. The agent should ask about this on the first stamp — but the developer can also do it manually:

```bash
mkdir -p ~/.hermes/backups

# Export GPG private key
gpg --export-secret-keys --armor YOUR_EMAIL > ~/.hermes/backups/gpg-private.asc

# Copy Bitcoin private key
cp ~/.bit/key.pem ~/.hermes/backups/bit-key.pem

# Encrypt both with your own GPG key
cd ~/.hermes/backups
tar czf - gpg-private.asc bit-key.pem | gpg --encrypt --armor -r YOUR_EMAIL > privkeys-backup.tar.gz.asc

# Delete the cleartext copies
rm gpg-private.asc bit-key.pem

# Now store privkeys-backup.tar.gz.asc somewhere safe (USB drive, offline storage, trusted cloud)
```

Only YOU can decrypt this backup (it's encrypted with your GPG public key). Keep it offline. If your machine dies, you can restore:

```bash
gpg --decrypt privkeys-backup.tar.gz.asc | tar xzf -
gpg --import gpg-private.asc
cp bit-key.pem ~/.bit/key.pem && chmod 600 ~/.bit/key.pem
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `No spendable UTXO` | No tBTC in wallet | Send from faucet to your `bit status` address |
| `gpg: skipped` | Wrong key ID | Use `gpg --list-secret-keys` to find your key |
| `bit: command not found` | Bit Protocol not installed | `pip install bit-protocol && bit init` |
| Port already in use (index) | Docker conflict | `docker compose down && docker compose up -d` |
