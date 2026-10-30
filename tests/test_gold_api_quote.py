"""Gold witness parses the API fixture and stays empty when the fetch fails."""
from __future__ import annotations

import json

from architecture.markets.gold_api_quote import URL, fetch_gold_witness, parse_gold
from architecture.markets.http_guard import reset_breakers


def test_gold_fixture() -> None:
    row = parse_gold({"symbol": "XAU", "price": 3993.5, "updatedAt": "2026-10-30T03:48:12Z"}, 9)
    assert row is not None
    assert row["price"] == 3993.5
    assert row["source_timestamp"] == "2026-10-30T03:48:12Z"
    assert row["source_role"] == "witness"
    assert URL == "https://api.gold-api.com/price/XAU"


def test_gold_failure_is_empty() -> None:
    reset_breakers()

    def opener(req, timeout):
        raise TimeoutError("blocked")

    assert fetch_gold_witness(opener=opener, now=5.0) == {}

    def ok(req, timeout):
        return json.dumps({"symbol": "XAU", "price": 3990.0, "updatedAt": "2026-10-30T00:00:00Z"}).encode()

    assert fetch_gold_witness(opener=ok, now=6.0)["XAU"]["price"] == 3990.0
