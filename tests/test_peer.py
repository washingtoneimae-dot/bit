"""Tests for the peer sync module."""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from bit_protocol.peer import (
    add_peer,
    count_peers,
    get_last_sync,
    list_peers,
    remove_peer,
    set_last_sync,
    sync_peer,
)


@pytest.fixture(autouse=True)
def clean_peers():
    """Use a temp peers.json for each test."""
    from bit_protocol.key import BIT_DIR
    path = BIT_DIR / "peers.json"
    if path.exists():
        path.unlink()
    yield
    if path.exists():
        path.unlink()


class TestPeerConfig:
    def test_add_peer(self):
        assert add_peer("https://peer1.com:8787")
        peers = list_peers()
        assert "https://peer1.com:8787" in peers

    def test_add_duplicate_returns_false(self):
        add_peer("https://peer1.com:8787")
        assert not add_peer("https://peer1.com:8787")

    def test_add_trailing_slash_normalized(self):
        add_peer("https://peer1.com:8787/")
        peers = list_peers()
        assert "https://peer1.com:8787" in peers
        assert "https://peer1.com:8787/" not in peers

    def test_remove_peer(self):
        add_peer("https://peer1.com:8787")
        assert remove_peer("https://peer1.com:8787")
        assert list_peers() == []

    def test_remove_nonexistent_returns_false(self):
        assert not remove_peer("https://nope.com:8787")

    def test_list_empty(self):
        assert list_peers() == []

    def test_list_multiple(self):
        add_peer("https://a.com:8787")
        add_peer("https://b.com:8787")
        peers = list_peers()
        assert len(peers) == 2

    def test_count(self):
        assert count_peers() == 0
        add_peer("https://a.com:8787")
        assert count_peers() == 1

    def test_last_sync_defaults_zero(self):
        add_peer("https://a.com:8787")
        assert get_last_sync("https://a.com:8787") == 0

    def test_set_and_get_last_sync(self):
        add_peer("https://a.com:8787")
        ts = 1000000
        set_last_sync("https://a.com:8787", ts)
        assert get_last_sync("https://a.com:8787") == ts

    def test_remove_clears_last_sync(self):
        add_peer("https://a.com:8787")
        set_last_sync("https://a.com:8787", 1000)
        remove_peer("https://a.com:8787")
        add_peer("https://a.com:8787")
        assert get_last_sync("https://a.com:8787") == 0


class TestPeerSync:
    def test_sync_peer_handles_empty_response(self):
        """Peer with no new stamps returns zero."""
        add_peer("https://empty-peer:8787")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"stamps": [], "synced_at": 100, "count": 0}

        with patch("httpx.get", return_value=mock_resp):
            result = sync_peer("https://empty-peer:8787")

        assert result["new_stamps"] == 0
        assert result["pages"] == 1
        assert result["errors"] == []

    def test_sync_peer_handles_http_error(self):
        """Peer returning error is handled gracefully."""
        add_peer("https://broken-peer:8787")

        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("httpx.get", return_value=mock_resp):
            result = sync_peer("https://broken-peer:8787")

        assert result["new_stamps"] == 0
        assert len(result["errors"]) > 0

    def test_sync_peer_handles_network_timeout(self):
        """Peer that times out is handled gracefully."""
        add_peer("https://slow-peer:8787")

        with patch("httpx.get", side_effect=TimeoutError("timeout")):
            result = sync_peer("https://slow-peer:8787", limit=500)

        assert result["new_stamps"] == 0
        assert len(result["errors"]) > 0

    def test_sync_peer_merges_stamps(self):
        """Stamps from peer are saved to local DB."""
        from bit_protocol.db import search_stamps

        add_peer("https://stamp-peer:8787")
        ts = int(time.time())
        mock_stamps = [
            {
                "hash": "aa" * 32,
                "txid": "bb" * 32,
                "content_type": "document",
                "key_fingerprint": "abcd1234",
                "public_key": "cc" * 33,
                "metadata": {"v": "1"},
                "network": "testnet",
                "indexed_at": ts,
            }
        ]

        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {
            "stamps": mock_stamps, "synced_at": ts + 1, "count": 1
        }

        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {
            "stamps": [], "synced_at": ts + 2, "count": 0
        }

        with patch("httpx.get", side_effect=[mock_resp1, mock_resp2]):
            result = sync_peer("https://stamp-peer:8787")

        assert result["new_stamps"] == 1

        # Verify it's in local DB
        found = search_stamps("aa" * 32, "hash")
        assert len(found) == 1
        assert found[0]["txid"] == "bb" * 32
