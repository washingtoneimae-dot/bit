#!/usr/bin/env bash
# Bit Protocol pre-commit hook
# Stamps staged files to Bitcoin testnet on every commit.
# 
# Usage: cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
# Configure which file extensions to track:
TRACKED_EXTENSIONS="md|pdf|txt|py|js|ts|rs|go"

set -e

# Only run if bit CLI is installed
if ! command -v bit &> /dev/null; then
    exec </dev/tty 2>/dev/null || true
    exit 0
fi

# Check if identity exists
if ! bit status 2>/dev/null | grep -q "Identity.*✓"; then
    exec </dev/tty 2>/dev/null || true
    exit 0
fi

# Get staged files matching tracked extensions
STAGED=$(git diff --cached --name-only --diff-filter=ACM | \
    grep -E "\.($TRACKED_EXTENSIONS)$" || true)

if [ -z "$STAGED" ]; then
    exit 0
fi

echo "🔏 Bit Protocol: stamping staged files..."

for file in $STAGED; do
    if [ -f "$file" ]; then
        echo "  Stamping: $file"
        # Note: stamp requires --utxo. For automated use, set
        # BIT_UTXO environment variable or run a UTXO scanner first.
        if [ -n "$BIT_UTXO" ]; then
            bit stamp "$file" --utxo="$BIT_UTXO" --quiet 2>/dev/null || \
                echo "  ⚠  Skipped $file (no UTXO available)"
        else
            echo "  ⚠  Skipped $file (set BIT_UTXO env var)"
        fi
    fi
done

exec </dev/tty 2>/dev/null || true
exit 0
