"""Frankfurter converts USD-base rates into EURUSD and USDJPY, and fails closed."""
from __future__ import annotations

import json

from architecture.markets.frankfurter_fx import fetch_frankfurter, parse_frankfurter
from architecture.markets.http_guard import reset_breakers


def test_daily_fx_conversion() -> None:
    out = parse_frankfurter({"amount": 1.0, "base": "USD", "date": "2026-10-29", "rates": {"EUR": 0.89847, "JPY": 158.06}}, 7)
    assert abs(out["EURUSD"]["price"] - (1.0 / 0.89847)) < 1e-9
    assert out["USDJPY"]["price"] == 158.06
    assert out["EURUSD"]["delay_flag"] == "daily"
    assert out["USDJPY"]["source_timestamp"] == "2026-10-29T00:00:00Z"


def test_frankfurter_failure_is_empty() -> None:
    reset_breakers()

    def opener(req, timeout):
        raise TimeoutError("blocked")

    assert fetch_frankfurter(opener=opener, now=1.0) == {}

    def ok(req, timeout):
        return json.dumps({"date": "2026-10-29", "rates": {"EUR": 0.9, "JPY": 150.0}}).encode()

    out = fetch_frankfurter(opener=ok, now=2.0)
    assert abs(out["EURUSD"]["price"] - (1.0 / 0.9)) < 1e-9
