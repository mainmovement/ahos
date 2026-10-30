"""Hyperliquid xyz mids are a witness. A failed post yields no prices."""
from __future__ import annotations

import json

from architecture.markets.http_guard import reset_breakers
from architecture.markets.hyperliquid_mids import fetch_hyperliquid_mids, parse_mids


def test_parse_keeps_the_named_perps() -> None:
    out = parse_mids({
        "xyz:SP500": "7647.25", "xyz:XYZ100": "28817.5", "xyz:GOLD": "3994.45",
        "xyz:CL": "103.285", "xyz:BRENTOIL": "112.175", "xyz:EUR": "1.11935",
        "xyz:JPY": "157.36", "xyz:NVDA": "208.385", "xyz:AAPL": "349.92",
    }, 20)
    assert out["SPX"]["price"] == 7647.25 and out["SPX"]["basis_future"] == "ES"
    assert out["NDX"]["basis_future"] == "NQ"
    assert out["BZ"]["source"] == "hyperliquid:xyz:BRENTOIL"
    assert out["NVDA"]["delay_flag"] == "realtime"
    assert "AAPL" not in out


def test_failed_post_returns_nothing() -> None:
    reset_breakers()

    def opener(req, timeout):
        assert json.loads(req.data.decode()) == {"type": "allMids", "dex": "xyz"}
        raise TimeoutError("blocked")

    assert fetch_hyperliquid_mids(opener=opener, now=10.0) == {}
