#!/usr/bin/env python3
"""Month 2 (M-GAP-011): CoinMarketCap adapter.

No test here touches the network. Every HTTP call is served by an injected
fake transport — the deployment target cannot be assumed to reach anything,
and a test suite that needs egress is a test suite that lies.

Behaviours pinned:
  * Missing COINMARKETCAP_API_KEY is NO_KEY, never DOWN, and emits ZERO
    traffic (DEXTools inert-until-configured contract).
  * CMC free tier has no discovery listing endpoint -> UNSUPPORTED, never a
    fabricated candidate list.
  * "Address not indexed" (empty data / 404) is OK-with-zero-tokens — a fact,
    not a failure (CoinGecko semantics).
  * Invalid/inactive keys (400 + error_code 1001/1002, or 401/403) are
    AUTH_REQUIRED; 429 is RATE_LIMIT; only real infrastructure failure is
    DOWN. Configuration gaps and outages stay distinguishable.
  * DEX liquidity is not provided by CMC -> liquidity_usd stays UNKNOWN.
"""
from __future__ import annotations

import io
import json
import urllib.error

import pytest

from architecture.providers.coinmarketcap import CoinMarketCapAdapter
from architecture.providers.contracts import NormalizedTokenCandidate
from architecture.providers.probe import probe_providers
from architecture.providers.registry import ProviderRouter

CMC_HOST = "pro-api.coinmarketcap.com"

# ----------------------------------------------------------------- fixtures --

INFO_PAYLOAD = {
    "data": {
        "12345": {
            "id": 12345,
            "name": "Test Token",
            "symbol": "TTK",
            "platform": {"id": 1027, "name": "Ethereum", "slug": "ethereum",
                         "token_address": "0xabc123"},
            "urls": {
                "website": ["https://example.com"],
                "twitter": ["https://twitter.com/ttk"],
                "chat": ["https://t.me/ttk_official"],
                "reddit": [],
            },
        }
    },
    "status": {"timestamp": "2026-08-20T00:00:00Z", "error_code": 0,
               "elapsed": 1, "credit_count": 1},
}

QUOTES_PAYLOAD = {
    "data": {
        "12345": {
            "id": 12345,
            "name": "Test Token",
            "symbol": "TTK",
            "cmc_rank": 1234,
            "quote": {"USD": {
                "price": 0.5,
                "volume_24h": 25000.0,
                "percent_change_1h": 2.5,
                "percent_change_6h": 8.0,
                "percent_change_24h": 15.0,
                "market_cap": 500000.0,
                "fully_diluted_market_cap": 750000.0,
            }},
        }
    },
    "status": {"timestamp": "2026-08-20T00:00:00Z", "error_code": 0,
               "elapsed": 1, "credit_count": 1},
}


class _FakeResp(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(json.dumps(payload).encode() if not isinstance(payload, bytes) else payload)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _routing_transport(routes: dict, capture=None, http_errors: dict | None = None):
    """routes: {substring: payload}; http_errors: {substring: HTTPError}."""
    def _t(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req.get_full_url()
        if capture is not None:
            capture.append(url)
        for key, exc in (http_errors or {}).items():
            if key in url:
                raise exc
        for key, payload in routes.items():
            if key in url:
                return _FakeResp(payload)
        raise AssertionError(f"unrouted URL: {url}")
    return _t


def _cmc_http_error(code: int, body: dict | None = None) -> urllib.error.HTTPError:
    raw = json.dumps(body).encode() if body is not None else b""
    return urllib.error.HTTPError(
        url=f"https://{CMC_HOST}/", code=code, msg="err", hdrs={}, fp=io.BytesIO(raw))


def _routes(info=INFO_PAYLOAD, quotes=QUOTES_PAYLOAD) -> dict:
    return {
        "/v2/cryptocurrency/info?": info,
        "/v2/cryptocurrency/quotes/latest?": quotes,
    }


def _adapter(transport, key="test-key") -> CoinMarketCapAdapter:
    return CoinMarketCapAdapter(transport=transport, api_key=key)


# ------------------------------------------------------------ no-key contract

def test_no_key_is_no_key_not_down():
    a = CoinMarketCapAdapter(api_key="")
    resp = a.fetch_token_metrics("ethereum", "0xabc")
    assert resp.status == "NO_KEY"
    assert resp.tokens == []
    assert "COINMARKETCAP_API_KEY" in (resp.error_message or "")
    # Discovery is UNSUPPORTED with or without a key: the capability itself
    # does not exist on the CMC free tier (never fabricated).
    assert a.fetch_candidate_tokens("ethereum").status == "UNSUPPORTED"


def test_no_key_short_circuits_before_any_network_call():
    calls = []
    a = CoinMarketCapAdapter(api_key="", transport=_routing_transport(_routes(), capture=calls))
    a.fetch_candidate_tokens("ethereum")
    a.fetch_token_metrics("ethereum", "0xabc")
    a.fetch_token_metrics("solana", "So1111")
    assert calls == [], "adapter emitted traffic it knew would be rejected"


def test_health_check_is_false_without_a_key():
    assert CoinMarketCapAdapter(api_key="").health_check() is False


def test_is_configured_reflects_the_key():
    assert CoinMarketCapAdapter(api_key="").is_configured is False
    assert CoinMarketCapAdapter(api_key="k").is_configured is True


def test_health_check_with_key_uses_transport():
    a = _adapter(_routing_transport({CMC_HOST: {}}))
    assert a.health_check() is True


# --------------------------------------------------------------- discovery

def test_discovery_is_unsupported_never_fabricated():
    a = _adapter(_routing_transport(_routes()))
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "UNSUPPORTED"
    assert resp.tokens == []
    assert "no candidate-discovery" in (resp.error_message or "")


# ------------------------------------------------------------ token metrics

def test_token_metrics_parse():
    calls = []
    a = _adapter(_routing_transport(_routes(), capture=calls))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "OK"
    assert len(calls) == 2, "info + quotes lookups"
    assert all(CMC_HOST in u for u in calls)
    assert resp.raw_sha256 and len(resp.raw_sha256) == 64

    tok = resp.tokens[0]
    assert isinstance(tok, NormalizedTokenCandidate)
    assert tok.symbol == "TTK"
    assert tok.name == "Test Token"
    assert tok.chain == "ethereum"
    assert tok.source_provider == "coinmarketcap"
    assert tok.metrics.price_usd == 0.5
    assert tok.metrics.volume_24h == 25000.0
    assert tok.metrics.market_cap_usd == 500000.0
    assert tok.metrics.fdv_usd == 750000.0
    assert tok.metrics.price_change_1h == 2.5
    assert tok.metrics.price_change_6h == 8.0
    assert tok.metrics.price_change_24h == 15.0
    # CMC provides no DEX liquidity — must stay UNKNOWN, never guessed.
    assert tok.metrics.liquidity_usd is None
    assert "metrics.liquidity_usd" in tok.unknown_fields
    assert tok.social_presence.get("twitter") == "https://twitter.com/ttk"
    assert tok.social_presence.get("telegram") == "https://t.me/ttk_official"
    assert tok.social_presence.get("website") == "https://example.com"


def test_address_not_indexed_is_ok_empty():
    a = _adapter(_routing_transport(_routes(info={"data": {}})))
    resp = a.fetch_token_metrics("ethereum", "0xneverlisted")
    assert resp.status == "OK"
    assert resp.tokens == []
    assert "not indexed" in (resp.error_message or "")


def test_address_not_indexed_on_this_platform_is_ok_empty():
    """Same address listed on another chain must not be claimed for ours."""
    other_chain = json.loads(json.dumps(INFO_PAYLOAD))
    other_chain["data"]["12345"]["platform"] = {
        "id": 1839, "name": "BNB Smart Chain", "slug": "binance-smart-chain",
        "token_address": "0xabc123"}
    a = _adapter(_routing_transport(_routes(info=other_chain)))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "OK"
    assert resp.tokens == []
    assert "not on chain 'ethereum'" in (resp.error_message or "")


def test_unmapped_chain_is_error_fields_stay_unknown():
    a = _adapter(_routing_transport(_routes()))
    resp = a.fetch_token_metrics("fantom", "0xabc123")
    assert resp.status == "ERROR"
    assert resp.tokens == []
    assert "no CMC platform mapping" in (resp.error_message or "")


def test_platform_map_covers_all_canonical_chains():
    for ch in ("ethereum", "eth", "bsc", "base", "arbitrum", "polygon",
               "avalanche", "solana"):
        assert ch in CoinMarketCapAdapter.PLATFORM_MATCH, ch


def test_solana_mint_matches_via_slug():
    info = json.loads(json.dumps(INFO_PAYLOAD))
    info["data"]["54321"] = {
        "id": 54321, "name": "Sol Token", "symbol": "SOLT",
        "platform": {"id": 5426, "name": "Solana", "slug": "solana",
                     "token_address": "So1111"},
        "urls": {},
    }
    info["data"].pop("12345")
    quotes = json.loads(json.dumps(QUOTES_PAYLOAD))
    quotes["data"] = {"54321": quotes["data"]["12345"]}
    quotes["data"]["54321"]["id"] = 54321
    a = _adapter(_routing_transport(_routes(info=info, quotes=quotes)))
    resp = a.fetch_token_metrics("solana", "So1111")
    assert resp.status == "OK"
    assert resp.tokens[0].symbol == "SOLT"


# ------------------------------------------------------- HTTP error mapping

def test_bad_key_error_code_1001_is_auth_required():
    err = _cmc_http_error(400, {"status": {"error_code": 1001,
                                           "error_message": "invalid key"}})
    a = _adapter(_routing_transport(_routes(), http_errors={"info?": err}))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "AUTH_REQUIRED"
    assert resp.tokens == []


def test_http_401_is_auth_required():
    a = _adapter(_routing_transport(_routes(), http_errors={"info?": _cmc_http_error(401)}))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "AUTH_REQUIRED"


def test_http_429_is_rate_limit():
    a = _adapter(_routing_transport(_routes(), http_errors={"info?": _cmc_http_error(429)}))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "RATE_LIMIT"


def test_http_5xx_is_down_not_auth():
    a = _adapter(_routing_transport(_routes(), http_errors={"info?": _cmc_http_error(503)}))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "DOWN"


def test_http_404_is_ok_empty():
    a = _adapter(_routing_transport(_routes(), http_errors={"info?": _cmc_http_error(404)}))
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "OK"
    assert resp.tokens == []


def test_network_failure_fails_closed():
    def _boom(req, timeout=None):
        raise OSError("TLS/SSL connection has been closed (EOF)")
    a = _adapter(_boom)
    resp = a.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "DOWN"
    assert resp.tokens == []


# ------------------------------------------------------------- integration

def test_registered_in_provider_router():
    router = ProviderRouter()
    assert "coinmarketcap" in router.providers
    assert router.providers["coinmarketcap"].is_configured is False


def test_probe_reports_enrichment_only_as_unsupported():
    """CMC has no discovery capability, so the discovery probe must report
    UNSUPPORTED — never a reachability-implying EMPTY (M-GAP-016 rule for
    security/enrichment-only adapters)."""
    report = probe_providers(providers={"coinmarketcap": CoinMarketCapAdapter(api_key="")})
    result = report.results[0]
    assert result.status == "UNSUPPORTED"
    assert "no discovery capability" in (result.detail or "")


def test_probe_default_map_covers_every_registered_provider():
    """Any provider registered in ProviderRouter must also appear in the
    --probe-providers default map, or the probe artifact silently misses it."""
    import inspect

    from architecture.providers import probe as probe_mod
    from architecture.providers.registry import ProviderRouter

    src = inspect.getsource(probe_mod.probe_providers)
    for pid in ProviderRouter().providers:
        assert pid in src, f"probe default map missing registered provider {pid}"
