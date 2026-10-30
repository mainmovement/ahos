"""CNBC primary quotes parse a fixture and do not include Brent."""
from __future__ import annotations

import json

from architecture.markets.cnbc_quotes import SYMBOLS, fetch_cnbc_primary, parse_cnbc
from architecture.markets.http_guard import fetch_json, reset_breakers
from architecture.markets.second_source import CNBC_MAP


def test_cnbc_fixture_is_realtime_and_has_no_brent() -> None:
    payload = {"FormattedQuoteResult": {"FormattedQuote": [
        {"symbol": ".SPX", "code": 0, "last": "7,720.39", "last_time": "2026-10-29T16:32:47.000-0400"},
        {"symbol": ".NDX", "code": 0, "last": "26100.5", "last_time": "2026-10-29T16:32:47.000-0400"},
        {"symbol": "@LCO.1", "code": 0, "last": "112.00", "last_time": "2026-10-29T16:32:47.000-0400"},
    ]}}
    out = parse_cnbc(payload, 12)
    assert out["SPX"]["price"] == 7720.39
    assert out["SPX"]["delay_flag"] == "realtime"
    assert out["SPX"]["source_timestamp"].startswith("2026-10-29")
    assert out["NDX"]["latency_ms"] == 12
    assert "BRENT" not in out
    assert "BRENT" not in SYMBOLS
    assert "BRENT" not in CNBC_MAP


def test_cnbc_fetch_uses_the_opener_once_per_retry_pair() -> None:
    reset_breakers()
    calls = {"n": 0}

    def opener(req, timeout):
        calls["n"] += 1
        assert timeout == 8.0
        assert ".SPX" in req.full_url and "BRENT" not in req.full_url and "@LCO" not in req.full_url
        body = {"FormattedQuoteResult": {"FormattedQuote": [
            {"symbol": "NVDA", "code": 0, "last": "208.10", "last_time": "2026-10-29T16:00:00.000-0400"},
        ]}}
        return json.dumps(body).encode()

    out = fetch_cnbc_primary(opener=opener, now=1_000.0)
    assert calls["n"] == 1
    assert out["NVDA"]["price"] == 208.10
    assert out["NVDA"]["source"] == "cnbc:NVDA"


def test_breaker_opens_after_three_failed_calls() -> None:
    reset_breakers()

    def opener(req, timeout):
        raise TimeoutError("blocked")

    for i in range(3):
        failed = fetch_json("https://example.test", source="cnbc", opener=opener, now=100.0 + i)
        assert failed["ok"] is False
    opened = fetch_json("https://example.test", source="cnbc", opener=opener, now=103.0)
    assert opened["reason"] == "circuit_open"
