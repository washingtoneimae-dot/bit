# Security Policy

## Private Key Safety

Your Bit Protocol identity key is stored at `~/.bit/key.pem` with file permissions `600` (owner read/write only). This is the only secret that controls your stamps.

- **Back it up.** If you lose `~/.bit/key.pem`, you cannot prove stamps belong to you.
- **Never share it.** Anyone with your key can create stamps under your identity.
- **One key per identity.** There is no key recovery mechanism. Treat the key file like a Bitcoin private key (it is one).

## Blockchain Safety

- Stamps are **immutable once confirmed.** Verify the txid before publishing a stamp as prior art.
- **Bitcoin Testnet is for testing.** Stamps on testnet have no real value and can be reorged. Use `--mainnet` for production.
- **A stamp does not file a patent.** It proves possession at a point in time. Consult a lawyer for IP strategy.

## Reporting a Vulnerability

If you discover a security issue in Bit Protocol:

1. **Do not** open a public GitHub issue
2. Email: washingtoneimae@gmail.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Affected version

You should receive a response within 48 hours. If not, follow up.

## Responsible Disclosure

We request a 90-day disclosure window from the time a fix is deployed to allow users to update.
