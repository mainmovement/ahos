#!/usr/bin/env python3
"""Month 2 (M-GAP-011): pump.fun launchpad adapter.

No test touches the network. Every call is served by an injected fake
transport.

Behaviours pinned:
  * Discovery feed parses newly created coins; fields the payload does not
    carry stay UNKNOWN (never invented).
  * pump.fun is Solana-only -> every other chain is UNSUPPORTED.
  * A reachable-but-empty feed is OK-with-zero-tokens (honest market state),
    still distinguishable from DOWN (M-GAP-002 discipline).
  * Network failure -> DOWN; 429 -> RATE_LIMIT; malformed payload -> ERROR.
  * fetch_token_metrics is UNSUPPORTED: the feed is discovery-only, so no
    fabricated enrichment is ever emitted.
  * The probe exercises the feed live-classifiable (SUCCESS/ERROR/TLS_ERROR).
"""
from __future__ import annotations

import io
import json
import urllib.error

from architecture.providers.probe import probe_providers
from architecture.providers.pumpfun import PumpFunLaunchpadAdapter
from architecture.providers.registry import ProviderRouter

COINS_FIXTURE = [
    {
        "mint": "NewCoinMint111111111111111111111111111111",
        "name": "New Coin",
        "symbol": "NEWC",
        "price": 0.000123,
        "usd_market_cap": 45000.0,
        "created_timestamp": "2026-08-20T01:02:03.456Z",
        "twitter": "https://x.com/newcoin",
        "telegram": "https://t.me/newcoin",
        "website": "https://newcoin.example",
    },
    {
        "mint": "OldCoinMint222222222222222222222222222222",
        "name": "Older Coin",
        "symbol": "OLDC",
        "price": 0.001,
        "market_cap": 120000.0,
        "creation_time": 1784516523,
        "twitter": "",
    },
    {
        # minimal record: only a mint — everything else must stay UNKNOWN
        "mint": "BareMint3333333333333333333333333333333333",
    },
]


class _FakeResp(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(json.dumps(payload).encode() if not isinstance(payload, bytes) else payload)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _transport(payload, status=200, capture=None):
    def _t(req, timeout=None):
        if capture is not None:
            capture.append(req.full_url)
        return _FakeResp(payload, status)
    return _t


def _boom(exc=OSError("TLS/SSL connection has been closed (EOF)")):
    def _t(req, timeout=None):
        raise exc
    return _t


def _http_error(code):
    return urllib.error.HTTPError("https://frontend-api.pump.fun/coins", code,
                                  "err", {}, io.BytesIO(b"{}"))


# ------------------------------------------------------------- discovery

def test_discovery_parses_launchpad_feed():
    a = PumpFunLaunchpadAdapter(transport=_transport(COINS_FIXTURE))
    resp = a.fetch_candidate_tokens("solana", limit=20)
    assert resp.status == "OK"
    assert len(resp.tokens) == 3
    assert resp.raw_sha256 and len(resp.raw_sha256) == 64

    newc = resp.tokens[0]
    assert newc.chain == "solana"
    assert newc.address == COINS_FIXTURE[0]["mint"]
    assert newc.symbol == "NEWC"
    assert newc.metrics.price_usd == 0.000123
    assert newc.metrics.market_cap_usd == 45000.0
    assert newc.pair_created_ts is not None
    assert newc.social_presence.get("twitter") == "https://x.com/newcoin"
    assert newc.social_presence.get("telegram") == "https://t.me/newcoin"
    assert newc.source_provider == "pumpfun"
    assert "metrics.volume_24h" in newc.unknown_fields  # feed has no volume

    oldc = resp.tokens[1]
    assert oldc.metrics.market_cap_usd == 120000.0  # 'market_cap' alias
    assert oldc.pair_created_ts is not None          # epoch creation_time
    assert not oldc.social_presence.get("twitter")   # empty string -> absent


def test_discovery_minimal_record_keeps_unknowns():
    a = PumpFunLaunchpadAdapter(transport=_transport(COINS_FIXTURE))
    resp = a.fetch_candidate_tokens("solana", limit=20)
    bare = resp.tokens[2]
    assert bare.address == COINS_FIXTURE[2]["mint"]
    assert bare.symbol == "UNKNOWN"
    assert bare.metrics.price_usd is None
    assert bare.metrics.market_cap_usd is None
    assert bare.pair_created_ts is None
    assert "metrics.price_usd" in bare.unknown_fields
    assert "metrics.market_cap_usd" in bare.unknown_fields
    assert "pair_created_ts" in bare.unknown_fields


def test_non_solana_chain_is_unsupported_never_fabricated():
    a = PumpFunLaunchpadAdapter(transport=_transport(COINS_FIXTURE))
    for ch in ("ethereum", "bsc", "base", "avalanche"):
        resp = a.fetch_candidate_tokens(ch)
        assert resp.status == "UNSUPPORTED"
        assert resp.tokens == []
        assert "Solana-only" in (resp.error_message or "")


def test_empty_feed_is_honest_empty_not_failure():
    a = PumpFunLaunchpadAdapter(transport=_transport([]))
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "OK"
    assert resp.tokens == []


# ------------------------------------------------------------- failures

def test_network_failure_is_down():
    a = PumpFunLaunchpadAdapter(transport=_boom())
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "DOWN"
    assert resp.tokens == []


def test_http_429_is_rate_limit():
    def _t(req, timeout=None):
        raise _http_error(429)
    a = PumpFunLaunchpadAdapter(transport=_t)
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "RATE_LIMIT"


def test_http_5xx_is_down():
    def _t(req, timeout=None):
        raise _http_error(503)
    a = PumpFunLaunchpadAdapter(transport=_t)
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "DOWN"
    assert "provider-side" in (resp.error_message or "")


def test_malformed_payload_fails_closed():
    a = PumpFunLaunchpadAdapter(transport=_transport(b"{not json"))
    resp = a.fetch_candidate_tokens("solana")
    assert resp.status == "DOWN"  # parse error inside _fetch -> fail closed
    assert resp.tokens == []


def test_token_metrics_is_unsupported_discovery_only():
    a = PumpFunLaunchpadAdapter(transport=_transport(COINS_FIXTURE))
    resp = a.fetch_token_metrics("solana", "SomeMint")
    assert resp.status == "UNSUPPORTED"
    assert resp.tokens == []
    assert "discovery-only" in (resp.error_message or "")


# ------------------------------------------------------------- integration

def test_registered_in_provider_router():
    router = ProviderRouter()
    assert "pumpfun" in router.providers
    assert "discovery" in router.providers["pumpfun"].capabilities


def test_probe_classifies_launchpad_success_and_failure_honestly():
    class Live:
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return type("R", (), {"status": "OK", "tokens": [object()],
                                  "error_message": None})()

    class Dead:
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            raise ConnectionError("TLS/SSL connection has been closed")

    good = probe_providers(providers={"pumpfun": Live()})
    assert good.any_success

    bad = probe_providers(providers={"pumpfun": Dead()})
    assert not bad.any_success
    assert bad.results[0].status == "TLS_ERROR"
