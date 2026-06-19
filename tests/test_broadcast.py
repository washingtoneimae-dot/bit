"""Tests for UTXO scanner and broadcast module."""

import pytest
from unittest.mock import patch, MagicMock

from bit_protocol.broadcast import find_utxo, _fetch_utxos


class TestUtxoScanner:
    def test_find_utxo_returns_none_when_empty(self):
        """No UTXOs available returns None."""
        with patch("bit_protocol.broadcast._fetch_utxos", return_value=[]):
            result = find_utxo("mrTest", "testnet", 2546)
            assert result is None

    def test_find_utxo_skips_small_utxos(self):
        """UTXO below min_sats is skipped."""
        utxos = [{"txid": "abc", "vout": 0, "value": 500}]  # too small
        with patch("bit_protocol.broadcast._fetch_utxos", return_value=utxos):
            result = find_utxo("mrTest", "testnet", 2546)
            assert result is None

    def test_find_utxo_returns_valid(self):
        """Valid UTXO with enough value is returned."""
        mock_utxos = [{"txid": "aa" * 32, "vout": 0, "value": 100000}]
        mock_tx_data = {
            "vout": [{"scriptpubkey": "76a914" + "00" * 20 + "88ac"}]
        }

        with (
            patch("bit_protocol.broadcast._fetch_utxos", return_value=mock_utxos),
            patch("httpx.get") as mock_get,
        ):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_tx_data
            mock_get.return_value = mock_resp

            result = find_utxo("mrTest", "testnet", 2546)
            assert result is not None
            assert result[0] == "aa" * 32  # txid
            assert result[1] == 0  # vout
            assert result[2] == 100000  # value
            assert "76a914" in result[3]  # script
