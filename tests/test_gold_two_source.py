"""M13 gold two-source witness — the law's test harness for the gold market.

The owner's two-source law (حافظه_ادامه/2026-10-09_04-46_قانون_شاهد_دو_منبعی_
همه_بازارها.md) is binding on gold as much as on crypto, and its build mandate
(line 21) is explicit: *"Add tests that prove single-source and conflicting
inputs fail closed for that market."* These are those tests.

The law's clauses, one test each:
  :6  minimum two independent sources        -> test_two_independent_feeds_verify
  :7  one source / empty / stale / unreachable -> UNKNOWN, never PASS
  :8  disagreement beyond a coded tolerance  -> CONFLICT, never PASS
  :9  independence = different upstream data -> test_one_adapter_twice_is_not_two_sources
  :11 tolerances are code, not judgement     -> the tolerance is a constant, and the
        boundary is pinned by test_conflict_boundary_is_the_coded_tolerance
  :15 gold: two independent spot or futures feeds -> both adapters are real spot/futures
        tapes, and a proxy masquerading as spot is rejected (test_a_proxy_token_price_...)
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from architecture.providers.gold import (
    CONFLICT,
    GOLD_MAX_AGE_SEC,
    GOLD_TOLERANCE_PCT,
    INSTRUMENT_FUTURES,
    INSTRUMENT_SPOT,
    STALE,
    UNRESOLVED,
    VERIFIED,
    GoldApiSpotAdapter,
    GoldPriceAdapter,
    GoldPriceError,
    GoldPriceWitness,
    YahooGoldFuturesAdapter,
    is_keyless_pair,
    production_gold_adapters,
    resolve_gold_price,
)

NOW = 1_791_579_599.0  # 2026-10-09 ~20:53 UTC, inside the measured window


class _FakeResp:
    """Minimal urlopen stand-in: returns canned bytes with a status attribute."""

    def __init__(self, raw: bytes, status: int = 200):
        self._raw = raw
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._raw


def _transport(payload: Any, status: int = 200):
    def _fn(req, timeout=None):  # noqa: ARG001 - signature must match urlopen
        return _FakeResp(json.dumps(payload).encode(), status)
    return _fn


def _goldapi(price: float, updated_at: str = "2026-10-09T20:42:14Z") -> dict:
    return {"price": price, "symbol": "XAU", "currency": "USD", "updatedAt": updated_at}


def _yahoo(price: float, ts: float = NOW) -> dict:
    return {"chart": {"result": [{"meta": {
        "regularMarketPrice": price,
        "regularMarketTime": ts,
        "instrumentType": "FUTURE",
        "exchangeName": "CMX",
        "shortName": "Gold Dec 26",
    }}]}}


def _epoch(iso: str) -> float:
    import datetime as dt
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


# --------------------------------------------------------------- adapters ---


def test_the_production_pair_is_two_keyless_independent_spot_or_futures_feeds():
    adapters = production_gold_adapters()
    assert len(adapters) == 2
    assert is_keyless_pair(adapters) is True
    ids = {a.provider_id for a in adapters}
    assert len(ids) == 2, "the two default providers must not be the same source"
    instruments = {a.instrument for a in adapters}
    assert instruments <= {INSTRUMENT_SPOT, INSTRUMENT_FUTURES}, (
        "the gold clause admits spot or futures only")


def test_adapters_quote_the_same_unit():
    """A spot/futures pair is only commensurable if both quote per troy ounce."""
    spot = GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90))).fetch_price(now=NOW)
    fut = YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30))).fetch_price(now=NOW)
    assert spot.unit == fut.unit
    assert spot.raw_sha256 != fut.raw_sha256


def test_quotes_carry_provider_provenance():
    spot = GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90))).fetch_price(now=NOW)
    assert spot.provider_id == "goldapi_spot"
    assert spot.instrument == INSTRUMENT_SPOT
    assert spot.price_usd == pytest.approx(4196.90)
    assert spot.observed_at == _epoch("2026-10-09T20:42:14Z")
    assert len(spot.raw_sha256) == 64 and spot.url.startswith("https://")


# ------------------------------------------------- law :6 two sources PASS --


def test_two_independent_feeds_verify():
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30))),
    ), now=NOW)
    assert w.state == VERIFIED
    assert w.reason.startswith("min_sources_met")
    assert w.price_usd is not None
    # The verified price is the mean only *after* agreement was established.
    assert w.price_usd == pytest.approx((4196.90 + 4220.30) / 2, abs=1e-6)
    assert w.spread_pct == pytest.approx(0.5584, abs=0.01)


def test_verified_price_never_invents_a_digit_when_feeds_agree_exactly():
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(4200.0))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4200.0))),
    ), now=NOW)
    assert w.state == VERIFIED
    assert w.price_usd == pytest.approx(4200.0)


# ----------------------------------- law :7 single source never becomes PASS --


def test_one_source_only_is_unresolved():
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90))),
    ), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None
    assert "insufficient_independent_sources" in w.reason


def test_one_adapter_passed_twice_is_not_two_sources():
    """Law line 9: two endpoints of one feed are not independent."""
    a = GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90)))
    w = resolve_gold_price((a, a), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None


def test_an_unreachable_provider_contributes_nothing():
    def _boom(req, timeout=None):  # noqa: ARG001
        raise OSError("connection refused")
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_boom),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30))),
    ), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None
    assert "goldapi_spot" in w.reason and "unreachable" in w.reason


def test_an_empty_or_malformed_answer_is_not_a_source():
    def _empty(req, timeout=None):  # noqa: ARG001
        return _FakeResp(b"{}")
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_empty),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30))),
    ), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None


def test_a_non_json_body_is_reported_not_swallowed():
    def _html(req, timeout=None):  # noqa: ARG001
        return _FakeResp(b"<html>502</html>")
    with pytest.raises(GoldPriceError):
        GoldApiSpotAdapter(transport=_html).fetch_price(now=NOW)


def test_a_stale_quote_contributes_nothing():
    """Law line 7: stale is one of the single-source conditions."""
    fresh_spot = _goldapi(4196.90, updated_at="2026-10-09T20:42:14Z")
    stale_futures_price = 4220.30
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(fresh_spot)),
        YahooGoldFuturesAdapter(
            transport=_transport(_yahoo(stale_futures_price, ts=NOW - GOLD_MAX_AGE_SEC - 1))),
    ), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None
    assert "stale" in w.reason


def test_a_quote_exactly_at_the_freshness_boundary_is_used():
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90,
                                                        updated_at="2026-10-09T20:42:14Z"))),
        YahooGoldFuturesAdapter(
            transport=_transport(_yahoo(4220.30, ts=NOW - GOLD_MAX_AGE_SEC))),
    ), now=NOW)
    assert w.state == VERIFIED
    assert w.price_usd is not None


# ------------------------------------- law :8 disagreement never becomes PASS --


def test_conflict_is_reported_with_both_prices_and_never_passes():
    w = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4500.0))),
    ), now=NOW)
    assert w.state == CONFLICT
    assert w.price_usd is None
    assert "source_disagreement" in w.reason
    # A conflict is shown, never averaged away.
    assert w.spread_pct is not None and w.spread_pct > GOLD_TOLERANCE_PCT
    assert len(w.quotes) == 2


def test_conflict_boundary_is_the_coded_tolerance():
    """Law line 11: the tolerance is a number in code, and this is its edge."""
    base = 4000.0
    inside = base * (1 + (GOLD_TOLERANCE_PCT / 100.0)) * 0.999
    outside = base * (1 + (GOLD_TOLERANCE_PCT / 100.0)) * 1.001

    ok = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(base))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(inside))),
    ), now=NOW)
    assert ok.state == VERIFIED, f"{inside} should be inside the coded tolerance"

    bad = resolve_gold_price((
        GoldApiSpotAdapter(transport=_transport(_goldapi(base))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(outside))),
    ), now=NOW)
    assert bad.state == CONFLICT, f"{outside} should be outside the coded tolerance"


def test_the_tolerance_is_a_named_constant_not_a_judgement():
    assert GOLD_TOLERANCE_PCT == 2.0
    assert isinstance(GOLD_MAX_AGE_SEC, (int, float))


# ---------------------------------------------- law :15 spot or futures only --


def test_a_futures_tape_that_stops_being_a_future_is_rejected():
    """The clause admits futures; if the symbol stops resolving to one, say so."""
    payload = _yahoo(4220.30)
    payload["chart"]["result"][0]["meta"]["instrumentType"] = "ETF"
    with pytest.raises(GoldPriceError):
        YahooGoldFuturesAdapter(transport=_transport(payload)).fetch_price(now=NOW)


def test_the_spot_adapter_refuses_a_non_xau_symbol():
    payload = _goldapi(4196.90)
    payload["symbol"] = "XAG"
    with pytest.raises(GoldPriceError):
        GoldApiSpotAdapter(transport=_transport(payload)).fetch_price(now=NOW)


def test_a_proxy_token_price_is_not_wired_in_as_a_source():
    """PAXG is a redeemable claim that tracks gold, not spot gold.

    The Astra memo forbids presenting a proxy as spot, and the gold clause
    requires spot or futures -- so no adapter here quotes a token. This test
    pins that: if someone later adds a PAXG adapter to the production pair,
    the witness must not silently start treating a proxy as a spot feed.
    """
    for adapter in production_gold_adapters():
        assert "paxg" not in adapter.provider_id.lower()
        assert "proxy" not in adapter.provider_id.lower()
        assert adapter.instrument in {INSTRUMENT_SPOT, INSTRUMENT_FUTURES}


# --------------------------------------------------------------- keylessness --


def test_a_keyed_provider_is_not_an_unattended_witness():
    class _KeyedSpot(GoldApiSpotAdapter):
        provider_id = "keyed_spot"
        requires_credentials = True

    w = resolve_gold_price((
        _KeyedSpot(transport=_transport(_goldapi(4196.90))),
        YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30))),
    ), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None
    assert "keyed_provider_present" in w.reason


def test_a_provider_that_forgets_to_declare_is_not_assumed_free():
    class _Undeclared(GoldPriceAdapter):
        provider_id = "undeclared"
        # deliberately no requires_credentials -- the class default must not be
        # read as "keyless"
        url = "https://example.invalid/price"

        def fetch_price(self, *, now: float):
            raise NotImplementedError

    assert is_keyless_pair((_Undeclared(),)) is False


def test_no_adapters_at_all_is_unresolved_not_verified():
    w = resolve_gold_price((), now=NOW)
    assert w.state == UNRESOLVED
    assert w.price_usd is None
    assert "no_sources_configured" in w.reason


# ------------------------------------------------------------------ summary --


def test_a_witness_never_reports_a_price_without_two_sources():
    """The invariant that matters downstream: a price implies VERIFIED.

    Behavioural, over every fail-closed path the resolver has, rather than a
    grep of its source: any state that is not VERIFIED must carry no price.
    """
    spot = GoldApiSpotAdapter(transport=_transport(_goldapi(4196.90)))
    futures = YahooGoldFuturesAdapter(transport=_transport(_yahoo(4220.30)))

    def _boom(req, timeout=None):  # noqa: ARG001
        raise OSError("connection refused")

    cases = [
        ("agree", (spot, futures), {}),
        ("one source", (spot,), {}),
        ("duplicate", (spot, spot), {}),
        ("unreachable", (GoldApiSpotAdapter(transport=_boom), futures), {}),
        ("conflict", (spot, YahooGoldFuturesAdapter(transport=_transport(_yahoo(4500.0)))), {}),
        ("stale", (spot, YahooGoldFuturesAdapter(
            transport=_transport(_yahoo(4220.30, ts=NOW - GOLD_MAX_AGE_SEC - 1)))), {}),
        ("empty", (), {}),
    ]
    for name, adapters, kw in cases:
        w = resolve_gold_price(adapters, now=NOW, **kw)
        if w.state == VERIFIED:
            assert w.price_usd is not None, f"{name}: VERIFIED without a price"
        else:
            assert w.price_usd is None, (
                f"{name}: state {w.state} must not carry a price, got {w.price_usd}")
        assert w.state in {VERIFIED, CONFLICT, STALE, UNRESOLVED}


def test_the_witness_states_are_the_house_vocabulary():
    for state in (VERIFIED, CONFLICT, STALE, UNRESOLVED):
        assert isinstance(state, str)
    assert GoldPriceWitness(state=UNRESOLVED, reason="x", price_usd=None).price_usd is None
