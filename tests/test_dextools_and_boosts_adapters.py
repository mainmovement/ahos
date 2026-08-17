"""Wave-25: DEXTools + DexScreener-boosts adapters.

No test here touches the network. Every HTTP call is served by an injected
fake transport, because the deployment target (Iran, filtered) cannot be
assumed to reach anything -- and a test suite that needs egress is a test
suite that lies about whether the code works.

The behaviours being pinned:
  * A missing paid API key is NO_KEY, never DOWN. Configuration gaps and
    outages must stay distinguishable in the health ledger.
  * "unknown" from an audit endpoint stays None. Coercing it to False would
    manufacture a safety claim out of missing data.
  * Boost spend is a RISK marker, not a bullish one.
"""
from __future__ import annotations

import io
import json

import pytest

from architecture.providers.adapters import DEXToolsAdapter, DexScreenerBoostsAdapter


class _FakeResp:
    def __init__(self, payload, status=200):
        self._b = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.status = status

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _transport(payload, status=200, capture=None):
    def _t(req, timeout=None):
        if capture is not None:
            capture.append(req)
        return _FakeResp(payload, status)
    return _t


def _boom(exc=OSError("TLS/SSL connection has been closed (EOF)")):
    def _t(req, timeout=None):
        raise exc
    return _t


# ------------------------------------------------------------- DEXTools --

def test_no_key_is_reported_as_no_key_not_down():
    """A paid provider we chose not to buy is not a broken provider."""
    a = DEXToolsAdapter(api_key="")
    r = a.fetch_candidate_tokens("ethereum")
    assert r.status == "NO_KEY"
    assert r.tokens == []
    assert "DEXTOOLS_API_KEY" in r.error_message


def test_no_key_short_circuits_before_any_network_call():
    calls = []
    a = DEXToolsAdapter(api_key="", transport=_transport({}, capture=calls))
    a.fetch_candidate_tokens("ethereum")
    a.fetch_token_metrics("ethereum", "0xabc")
    assert calls == [], "adapter emitted traffic it knew would 401"


def test_health_check_is_false_without_a_key():
    assert DEXToolsAdapter(api_key="").health_check() is False


def test_is_configured_reflects_the_key():
    assert DEXToolsAdapter(api_key="").is_configured is False
    assert DEXToolsAdapter(api_key="k").is_configured is True


def test_api_key_is_sent_as_header_never_in_the_url():
    """A key in a query string leaks into logs and proxies."""
    calls = []
    a = DEXToolsAdapter(api_key="SECRET123",
                        transport=_transport({"data": []}, capture=calls))
    a.fetch_candidate_tokens("ethereum")
    req = calls[0]
    assert "SECRET123" not in req.full_url
    assert req.get_header("X-api-key") == "SECRET123"


def test_hotpools_are_normalized():
    payload = {"data": [
        {"address": "0xpair", "exchange": {"name": "uniswap"},
         "mainToken": {"address": "0xtok", "symbol": "AAA", "name": "Alpha"}},
        {"address": "0xpair2", "mainToken": {}},           # no address -> skipped
    ]}
    a = DEXToolsAdapter(api_key="k", transport=_transport(payload))
    r = a.fetch_candidate_tokens("ethereum")
    assert r.status == "OK" and len(r.tokens) == 1
    t = r.tokens[0]
    assert t.address == "0xtok" and t.symbol == "AAA"
    assert t.pair_address == "0xpair" and t.dex_id == "uniswap"
    assert t.source_provider == "dextools" and t.raw_payload_sha256


def test_chain_slug_translation():
    calls = []
    a = DEXToolsAdapter(api_key="k", transport=_transport({"data": []}, capture=calls))
    a.fetch_candidate_tokens("ethereum")
    assert "/ether/" in calls[0].full_url  # DEXTools calls it 'ether', not 'ethereum'


@pytest.mark.parametrize("raw,expected", [
    ("yes", True), ("no", False), ("unknown", None), (None, None), ("", None),
])
def test_unknown_audit_flags_stay_unknown(raw, expected):
    """The whole safety model rests on this: absent != safe."""
    a = DEXToolsAdapter(api_key="k",
                        transport=_transport({"data": {"isHoneypot": raw}}))
    r = a.fetch_token_metrics("ethereum", "0xabc")
    assert r.tokens[0].security.is_honeypot is expected


def test_audit_taxes_are_normalized_to_percent():
    a = DEXToolsAdapter(api_key="k", transport=_transport(
        {"data": {"buyTax": 0.05, "sellTax": 12.0}}))
    sec = a.fetch_token_metrics("ethereum", "0xabc").tokens[0].security
    assert sec.buy_tax_pct == pytest.approx(5.0)   # fraction -> percent
    assert sec.sell_tax_pct == pytest.approx(12.0)  # already percent


def test_transport_failure_becomes_error_not_an_exception():
    a = DEXToolsAdapter(api_key="k", transport=_boom())
    for r in (a.fetch_candidate_tokens("ethereum"),
              a.fetch_token_metrics("ethereum", "0xabc")):
        assert r.status == "ERROR" and r.tokens == []
        assert "OSError" in r.error_message


def test_plan_selects_the_base_url():
    assert "/trial/v2" in DEXToolsAdapter(api_key="k")._base_url
    assert "/standard/v2" in DEXToolsAdapter(api_key="k", plan="standard")._base_url


# --------------------------------------------------------------- boosts --

def test_boost_map_keys_are_lowercased_addresses():
    payload = [{"tokenAddress": "0xABCdef", "chainId": "ethereum", "totalAmount": 300},
               {"tokenAddress": "SoLAddr", "chainId": "solana", "amount": 50}]
    b = DexScreenerBoostsAdapter(transport=_transport(payload))
    m = b.fetch_boost_map()
    assert m == {"0xabcdef": 300.0, "soladdr": 50.0}


def test_boost_map_is_empty_on_failure_and_that_means_unknown():
    b = DexScreenerBoostsAdapter(transport=_boom())
    assert b.fetch_boost_map() == {}


def test_boost_rows_are_filtered_by_chain():
    payload = [{"tokenAddress": "0xa", "chainId": "ethereum", "totalAmount": 1},
               {"tokenAddress": "s1", "chainId": "solana", "totalAmount": 2}]
    b = DexScreenerBoostsAdapter(transport=_transport(payload))
    r = b.fetch_candidate_tokens("solana")
    assert [t.address for t in r.tokens] == ["s1"]


def test_boost_limit_is_respected():
    payload = [{"tokenAddress": f"s{i}", "chainId": "solana", "totalAmount": i}
               for i in range(10)]
    b = DexScreenerBoostsAdapter(transport=_transport(payload))
    assert len(b.fetch_candidate_tokens("solana", limit=3).tokens) == 3


def test_malformed_boost_rows_are_skipped_not_fatal():
    payload = [{"tokenAddress": "0xa", "chainId": "eth", "totalAmount": "not-a-number"},
               {"chainId": "eth", "totalAmount": 5},
               {"tokenAddress": "0xb", "chainId": "eth", "totalAmount": 7}]
    b = DexScreenerBoostsAdapter(transport=_transport(payload))
    assert b.fetch_boost_map() == {"0xb": 7.0}


def test_boost_feed_exposes_no_market_metrics():
    """It is an attention source. Pretending otherwise would fake price data."""
    b = DexScreenerBoostsAdapter(transport=_transport([]))
    r = b.fetch_token_metrics("solana", "abc")
    assert r.status == "OK" and r.tokens == []


def test_paid_boost_raises_paid_promotion_risk_flag():
    """End-to-end: boost spend must surface as a risk, never as bullishness."""
    from architecture.intel.viral import ViralityTracker
    from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics

    cand = NormalizedTokenCandidate(
        chain="solana", address="s1", symbol="AAA", name="Alpha",
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=50_000.0,
            volume_5m=1000.0, volume_1h=6000.0,
            txns_5m_buys=30, txns_5m_sells=20,
            txns_1h_buys=300, txns_1h_sells=300),
        source_provider="test", retrieved_ts=0.0)

    boosted = ViralityTracker().analyze(cand, boost_amount=500.0)
    clean = ViralityTracker().analyze(cand, boost_amount=None)
    assert boosted.is_paid_promotion is True
    assert clean.is_paid_promotion is False
    # The promotion must be voiced to the user, not silently absorbed.
    assert any("تبلیغ پولی" in w for w in (boosted.warnings + boosted.reasons))
