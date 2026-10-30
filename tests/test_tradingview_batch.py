"""TradingView batch flags the feed delay and falls back when the fetch fails."""
from __future__ import annotations

import json

from architecture.markets.http_guard import reset_breakers
from architecture.markets.tradingview_batch import TICKERS, fetch_tradingview_batch, parse_tradingview


def test_delay_flag_follows_the_feed() -> None:
    payload = {"data": [
        {"s": "FX:EURUSD", "d": [1.1189, "streaming"]},
        {"s": "XETR:DAX", "d": [26039.68, "delayed_streaming_900"]},
        {"s": "CME_MINI:ES1!", "d": [7676.0, "delayed_streaming_600"]},
        {"s": "EUREX:FDAX1!", "d": [26099.0, "delayed_streaming_900"]},
    ]}
    out = parse_tradingview(payload, 40)
    assert out["EURUSD"]["delay_flag"] == "streaming" and out["EURUSD"]["delay_s"] == 0
    assert out["DAX"]["delay_flag"] == "delayed_900s"
    assert out["ES"]["delay_flag"] == "delayed_600s"
    assert out["FDAX"]["source"] == "tradingview:EUREX:FDAX1!"
    assert "BRENT" not in TICKERS


def test_failed_batch_returns_no_prices() -> None:
    reset_breakers()

    def opener(req, timeout):
        raise TimeoutError("blocked")

    assert fetch_tradingview_batch(opener=opener, now=50.0) == {}
    body = req_count = {"n": 0}

    def ok(req, timeout):
        body["n"] += 1
        assert json.loads(req.data.decode())["symbols"]["tickers"]
        return json.dumps({"data": [{"s": "NYMEX:CL1!", "d": [103.44, "delayed_streaming_600"]}]}).encode()

    out = fetch_tradingview_batch(opener=ok, now=60.0)
    assert body["n"] == 1
    assert out["CL"]["price"] == 103.44
    assert out["CL"]["delay_flag"] == "delayed_600s"
