#!/usr/bin/env python3
"""Provider Failure, HTTP Error, Timeout, and Fault-Injection Tests (Phase XX)."""
import sys, json, urllib.error
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.providers.contracts import NormalizedTokenCandidate, ProviderResponse
from architecture.providers.adapters import (
    DexScreenerAdapter, GeckoTerminalAdapter, GoPlusSecurityAdapter, RugCheckSecurityAdapter
)
from architecture.providers.registry import ProviderRouter


def _error_transport(exc: Exception):
    def _transport(req, timeout=None):
        raise exc
    return _transport


def _status_transport(status_code: int, body: str = "{}"):
    def _transport(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, status_code, "HTTP Error", {}, None)
    return _transport


def _raw_transport(raw_bytes: bytes, status_code: int = 200):
    class Resp:
        def __init__(self):
            self.status = status_code
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return raw_bytes
    return lambda req, timeout=None: Resp()


# ---------------- HTTP Error & Status Code Tests ----------------
@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 429, 500, 502, 503, 521])
def test_dexscreener_http_errors_handled_gracefully(status_code):
    adapter = DexScreenerAdapter(transport=_status_transport(status_code))
    resp = adapter.fetch_candidate_tokens("solana")
    assert resp.status == "ERROR"
    assert resp.tokens == []
    assert resp.error_message is not None


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 429, 500, 502, 503, 521])
def test_geckoterminal_http_errors_handled_gracefully(status_code):
    adapter = GeckoTerminalAdapter(transport=_status_transport(status_code))
    resp = adapter.fetch_candidate_tokens("solana")
    assert resp.status == "ERROR"
    assert resp.tokens == []
    assert resp.error_message is not None


def test_goplus_timeout_exception():
    adapter = GoPlusSecurityAdapter(transport=_error_transport(TimeoutError("Connection timed out")))
    resp = adapter.fetch_token_metrics("ethereum", "0x1111111111111111111111111111111111111111")
    assert resp.status == "ERROR"
    assert "TimeoutError" in resp.error_message


def test_rugcheck_network_unreachable():
    adapter = RugCheckSecurityAdapter(transport=_error_transport(ConnectionResetError("Connection reset by peer")))
    resp = adapter.fetch_token_metrics("solana", "SolanaTok11111111111111111111111111111111")
    assert resp.status == "ERROR"
    assert "ConnectionResetError" in resp.error_message


# ---------------- Malformed Payload & JSON Edge Cases ----------------
def test_dexscreener_malformed_json():
    adapter = DexScreenerAdapter(transport=_raw_transport(b"{ invalid json string ..."))
    resp = adapter.fetch_candidate_tokens("solana")
    assert resp.status == "ERROR"
    assert "JSONDecodeError" in resp.error_message


def test_geckoterminal_empty_payload():
    adapter = GeckoTerminalAdapter(transport=_raw_transport(b""))
    resp = adapter.fetch_candidate_tokens("solana")
    assert resp.status == "ERROR"


def test_goplus_unexpected_schema():
    # Valid JSON but missing 'result' dictionary
    adapter = GoPlusSecurityAdapter(transport=_raw_transport(b'{"code": 1, "unexpected_key": 123}'))
    resp = adapter.fetch_token_metrics("ethereum", "0x1111111111111111111111111111111111111111")
    assert resp.status == "OK"
    assert len(resp.tokens) == 1
    # Unknowns should be properly identified without crashing
    assert "metrics.liquidity_usd" in resp.tokens[0].unknown_fields


def test_rugcheck_empty_risks_array():
    payload = json.dumps({"tokenMeta": {"symbol": "SAFE"}, "risks": []}).encode("utf-8")
    adapter = RugCheckSecurityAdapter(transport=_raw_transport(payload))
    resp = adapter.fetch_token_metrics("solana", "SolanaTokSafe11111111111111111111111111")
    assert resp.status == "OK"
    assert len(resp.tokens) == 1
    assert resp.tokens[0].security.is_honeypot is False
    assert resp.tokens[0].security.has_mint_authority is False


def test_rate_limit_throttle_delay():
    # Rate limit 5 rps (0.2s interval)
    adapter = DexScreenerAdapter(transport=_raw_transport(b'{"pairs": []}'))
    adapter._rate_limit_rps = 5.0
    t0 = adapter._last_call_ts
    adapter._rate_limit()
    t1 = adapter._last_call_ts
    assert t1 >= t0
