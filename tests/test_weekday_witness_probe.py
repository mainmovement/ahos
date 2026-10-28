from __future__ import annotations

import time

from architecture.markets.paper_trader import INSTRUMENTS
from architecture.markets.weekday_witness_probe import build_witness_probe_payload, tradable_for_paper


def test_weekend_blocks_cash_desk_even_if_verified():
    now = time.time()
    ok, reason = tradable_for_paper(
        "GOLD",
        "VERIFIED",
        {"market_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "price": 4000},
        now=now,
        weekend_tehran=True,
    )
    assert ok is False and reason == "WEEKEND_CASH_SESSION"


def test_a_future_quote_is_not_tradable_and_the_1200_boundary_holds():
    from datetime import datetime, timezone
    now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc).timestamp()
    ahead = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 1))
    ok, reason = tradable_for_paper(
        "CRYPTO", "VERIFIED", {"market_time": ahead, "price": 100}, now=now, weekend_tehran=False,
    )
    assert ok is False and reason == "QUOTE_TIME_AHEAD"
    edge = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 1200))
    ok, reason = tradable_for_paper(
        "CRYPTO", "VERIFIED", {"market_time": edge, "price": 100}, now=now, weekend_tehran=False,
    )
    assert ok is True and reason == "OK"
    stale = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 1201))
    ok, reason = tradable_for_paper(
        "CRYPTO", "VERIFIED", {"market_time": stale, "price": 100}, now=now, weekend_tehran=False,
    )
    assert ok is False and reason == "MARKET_CLOSED_OR_STALE"
    ok, reason = tradable_for_paper(
        "CRYPTO", "VERIFIED", {"market_time": "2026-10-26t15:00:00Z", "price": 100}, now=now, weekend_tehran=False,
    )
    assert ok is False and reason == "MARKET_TIME_UNKNOWN"
    ok, reason = tradable_for_paper(
        "CRYPTO", "CONFLICT", {"market_time": edge, "price": 100}, now=now, weekend_tehran=False,
    )
    assert ok is False and reason == "WITNESS_CONFLICT"


def test_stale_quote_not_tradable():
    now = time.time()
    ok, reason = tradable_for_paper(
        "CRYPTO",
        "VERIFIED",
        {"market_time": "2020-01-01T00:00:00Z", "price": 1},
        now=now,
        weekend_tehran=False,
    )
    assert ok is False and reason == "MARKET_CLOSED_OR_STALE"


def test_build_payload_tradable_subset_on_weekend():
    quotes = {
        "BTC": {"price": 100, "market_time": "2026-10-24T04:00:00Z", "source": "a"},
        "XAU": {"price": 4000, "market_time": "2026-10-24T04:00:00Z", "source": "a"},
    }
    second = {"BTC": {"price": 100, "source": "b"}, "XAU": {"price": 4001, "source": "b"}}
    from datetime import datetime, timezone

    u = datetime(2026, 10, 24, 4, 5, tzinfo=timezone.utc)
    payload = build_witness_probe_payload(
        {k: INSTRUMENTS[k] for k in ("BTC", "XAU")},
        quotes,
        second,
        now=u.timestamp(),
        fetch_ts=u,
    )
    assert "CRYPTO" in payload["verified_asset_classes"]
    assert payload["session_gate"]["weekend_tehran"] is True
    assert "GOLD" not in payload.get("tradable_asset_classes", [])
    assert "CRYPTO" in payload.get("tradable_asset_classes", [])
