#!/usr/bin/env python3
"""Phase 7 provider expansion tests: CoinGecko, ChainExplorer, unified collect().

All network access is mocked (CI is network-free, per repo law). Fixtures mirror
the real APIs' documented response shapes.
"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.providers.coingecko import CoinGeckoAdapter
from architecture.providers.chain_explorer import ChainExplorerAdapter
from architecture.providers.coinmarketcap import CoinMarketCapAdapter
from architecture.providers.collect import ProviderCollector, CollectionOutcome
from architecture.providers.registry import ProviderRouter


class MockHttpResponse:
    def __init__(self, data, status: int = 200):
        self._data = json.dumps(data).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._data


class RoutingTransport:
    """Dispatches on URL substring -> payload. Raises on unexpected URL."""

    def __init__(self, routes: dict[str, dict]):
        self.routes = routes
        self.seen_urls = []

    def __call__(self, req, timeout=10):
        url = req.full_url
        self.seen_urls.append(url)
        for substring, payload in self.routes.items():
            if substring in url:
                return MockHttpResponse(payload)
        raise RuntimeError(f"unexpected url: {url}")


class ExplodingTransport:
    def __call__(self, req, timeout=10):
        raise ConnectionError("network unreachable (test)")


# ---------------------------- CoinGecko -----------------------------------------

COINGECKO_FIXTURE = {
    "symbol": "abc",
    "name": "ABC Token",
    "links": {
        "homepage": ["https://abc.example"],
        "twitter_screen_name": "abctoken",
        "telegram_channel_identifier": "abcchannel",
    },
    "market_data": {
        "current_price": {"usd": 0.00123},
        "total_volume": {"usd": 123456.0},
        "market_cap": {"usd": 1234567.0},
        "fully_diluted_valuation": {"usd": 2345678.0},
        "price_change_percentage_1h_in_currency": 1.2,
        "price_change_percentage_24h_in_currency": -3.4,
    },
}


def test_coingecko_token_metrics_parse():
    adapter = CoinGeckoAdapter(transport=RoutingTransport(
        {"api.coingecko.com": COINGECKO_FIXTURE}))
    resp = adapter.fetch_token_metrics("ethereum", "0xabc123")
    assert resp.status == "OK"
    tok = resp.tokens[0]
    assert tok.source_provider == "coingecko"
    assert tok.metrics.price_usd == 0.00123
    assert tok.metrics.market_cap_usd == 1234567.0
    assert tok.metrics.volume_24h == 123456.0
    assert tok.metrics.fdv_usd == 2345678.0
    assert tok.social_presence["twitter"].endswith("abctoken")
    # Honesty law: CoinGecko has NO liquidity field -> UNKNOWN, never invented.
    assert tok.metrics.liquidity_usd is None
    assert "metrics.liquidity_usd" in tok.unknown_fields


def test_coingecko_discovery_unsupported_never_fabricated():
    adapter = CoinGeckoAdapter(transport=RoutingTransport({}))
    resp = adapter.fetch_candidate_tokens("solana", limit=10)
    assert resp.status == "UNSUPPORTED"
    assert resp.tokens == []


def test_coingecko_unmapped_chain_is_error():
    adapter = CoinGeckoAdapter(transport=RoutingTransport({}))
    resp = adapter.fetch_token_metrics("cardano", "addr1")
    assert resp.status == "ERROR"
    assert resp.tokens == []


def test_coingecko_multi_chain_platform_map():
    adapter = CoinGeckoAdapter(transport=RoutingTransport({"api.coingecko.com": COINGECKO_FIXTURE}))
    for chain in ("ethereum", "bsc", "base", "arbitrum", "polygon", "avalanche", "solana"):
        assert adapter.fetch_token_metrics(chain, "x").status == "OK", chain


# ---------------------------- ChainExplorer -------------------------------------

BLOCKSCOUT_ROUTES = {
    "/api/v2/addresses/": {"is_contract": True},
    "/api/v2/smart-contracts/": {"is_verified": True, "address": "0xDeployer0000000000000000000000000000000000001"},
    "/api/v2/tokens/": {"symbol": "abc", "name": "ABC Token", "exchange_rate": 0.5},
}


def test_chain_explorer_blockscout_parse():
    adapter = ChainExplorerAdapter(transport=RoutingTransport(BLOCKSCOUT_ROUTES))
    resp = adapter.fetch_token_metrics("ethereum", "0xToken1111111111111111111111111111111111111")
    assert resp.status == "OK"
    tok = resp.tokens[0]
    assert tok.security.is_contract_verified is True
    assert tok.security.deployer_address == "0xDeployer0000000000000000000000000000000000001"
    assert tok.metrics.price_usd == 0.5
    assert tok.source_provider == "chain_explorer"


def test_chain_explorer_unverified_contract_is_not_failure():
    """404 on the smart-contract endpoint means 'not verified' -> stays UNKNOWN, not an error."""
    routes = dict(BLOCKSCOUT_ROUTES)
    routes["/api/v2/smart-contracts/"] = {"is_verified": False}
    adapter = ChainExplorerAdapter(transport=RoutingTransport(routes))
    resp = adapter.fetch_token_metrics("base", "0xToken")
    assert resp.status == "OK"
    assert resp.tokens[0].security.is_contract_verified is False


def test_chain_explorer_unsupported_chain_returns_unknown_envelope():
    adapter = ChainExplorerAdapter(transport=RoutingTransport({}))
    for chain in ("bsc", "avalanche", "solana"):
        resp = adapter.fetch_token_metrics(chain, "someaddr")
        assert resp.status == "UNSUPPORTED", chain
        assert resp.tokens == []
        assert "UNKNOWN" in resp.error_message


def test_chain_explorer_network_failure_fails_closed():
    adapter = ChainExplorerAdapter(transport=ExplodingTransport())
    resp = adapter.fetch_token_metrics("ethereum", "0xdead")
    assert resp.status == "DOWN"
    assert resp.tokens == []


# ---------------------------- unified collect() facade ---------------------------

DEXSCREENER_FIXTURE = {
    "pairs": [{
        "chainId": "ethereum",
        "dexId": "uniswap",
        "pairAddress": "0xPair111111111111111111111111111111111111111",
        "baseToken": {"symbol": "ABC", "name": "ABC Token"},
        "priceUsd": "0.10",
        "liquidity": {"usd": 50000.0},
        "volume": {"h24": 120000.0},
        "pairCreatedAt": 1755000000000,
    }]
}


def _merge_routes(coingecko_fixture) -> dict:
    return {
        "api.dexscreener.com": DEXSCREENER_FIXTURE,
        "api.geckoterminal.com": {"data": {"attributes": {"price_usd": "0.10",
                                                          "total_reserve_in_usd": "48000",
                                                          "fdv_usd": "900000",
                                                          "volume_usd": {"h24": "110000"}}}},
        "api.coingecko.com": coingecko_fixture,
        "api.gopluslabs.io": {"result": {"0xtoken": {
            "token_symbol": "ABC", "token_name": "ABC Token",
            "is_honeypot": "0", "buy_tax": "0.01", "sell_tax": "0.01",
            "is_open_source": "1", "is_mintable": "0", "cannot_sell_all": "0",
        }}},
        "blockscout.com/api/v2/addresses/": {"is_contract": True},
        "blockscout.com/api/v2/smart-contracts/": {
            "is_verified": True,
            "address": "0xDeployer0000000000000000000000000000000000001"},
        "blockscout.com/api/v2/tokens/": {"symbol": "abc", "name": "ABC Token",
                                          "exchange_rate": 0.5},
    }


def test_collect_merges_providers_with_provenance():
    routes = _merge_routes(COINGECKO_FIXTURE)
    collector = ProviderCollector(transport=RoutingTransport(routes))
    outcome = collector.collect("ethereum", "0xToken")

    assert isinstance(outcome, CollectionOutcome)
    assert outcome.provider_statuses["dexscreener"] == "OK"
    assert outcome.provider_statuses["coingecko"] == "OK"
    assert outcome.provider_statuses["goplus"] == "OK"
    assert outcome.provider_statuses["chain_explorer"] == "OK"

    cand = outcome.candidate
    assert cand.metrics.liquidity_usd == 50000.0            # from dexscreener
    assert cand.metrics.market_cap_usd == 1234567.0         # only coingecko knows this
    assert cand.security.deployer_address.startswith("0xDeployer")  # only explorer knows
    assert cand.social_presence["twitter"].endswith("abctoken")

    assert outcome.field_sources["metrics.liquidity_usd"] == "dexscreener"
    assert outcome.field_sources["metrics.market_cap_usd"] == "coingecko"
    assert outcome.field_sources["security.deployer_address"] == "chain_explorer"
    assert "UNKNOWN" in (cand.unknown_fields or []) or cand.unknown_fields  # unknowns tracked


def test_collect_conflict_first_provider_wins_and_is_logged():
    conflicting = dict(COINGECKO_FIXTURE)
    conflicting["market_data"] = dict(COINGECKO_FIXTURE["market_data"])
    conflicting["market_data"]["current_price"] = {"usd": 0.99}   # conflicts with dexscreener 0.10

    collector = ProviderCollector(transport=RoutingTransport(_merge_routes(conflicting)))
    outcome = collector.collect("ethereum", "0xToken")

    assert outcome.candidate.metrics.price_usd == 0.10            # dexscreener (first) kept
    assert outcome.field_sources["metrics.price_usd"] == "dexscreener"
    assert any("metrics.price_usd" in c for c in outcome.conflicts)


def test_collect_unknown_never_overwrites_known():
    """CoinGecko has no liquidity; a known dexscreener liquidity must survive the merge."""
    collector = ProviderCollector(transport=RoutingTransport(_merge_routes(COINGECKO_FIXTURE)))
    outcome = collector.collect("ethereum", "0xToken")
    assert outcome.candidate.metrics.liquidity_usd == 50000.0
    assert outcome.field_sources["metrics.liquidity_usd"] == "dexscreener"


def test_collect_total_failure_is_all_unknown_low_confidence():
    collector = ProviderCollector(transport=ExplodingTransport())
    outcome = collector.collect("solana", "SomeSolanaAddress1111111111111111111111")

    # DOWN/ERROR = attempted and failed; UNSUPPORTED = honestly not applicable;
    # NO_KEY = unconfigured keyed tier (coinmarketcap is inert without a key).
    assert all(s in ("DOWN", "ERROR", "UNSUPPORTED", "NO_KEY") for s in outcome.provider_statuses.values())
    cand = outcome.candidate
    assert cand.metrics.liquidity_usd is None
    assert cand.security.is_honeypot is None
    assert cand.confidence_level == "LOW"
    assert len(cand.unknown_fields) > 0


def test_collect_security_routing_by_chain_family():
    """solana -> rugcheck only; evm -> goplus + chain_explorer."""
    routes = _merge_routes(COINGECKO_FIXTURE)
    collector = ProviderCollector(transport=RoutingTransport(routes))
    outcome = collector.collect("solana", "SolToken1111111111111111111111111111111111")
    assert "goplus" not in outcome.provider_statuses
    assert "rugcheck" in outcome.provider_statuses
    assert "chain_explorer" in outcome.provider_statuses  # attempted, UNSUPPORTED for solana


def test_registry_exposes_new_providers():
    router = ProviderRouter()
    assert "coingecko" in router.providers
    assert "chain_explorer" in router.providers
    assert "coinmarketcap" in router.providers
    assert router.providers["coinmarketcap"].is_configured is False  # inert by default


# ---------------------------- CoinMarketCap in collect() -----------------------

CMC_INFO_FIXTURE = {
    "data": {
        "98765": {
            "id": 98765, "name": "ABC Token", "symbol": "ABC",
            "platform": {"id": 1027, "name": "Ethereum", "slug": "ethereum",
                         "token_address": "0xToken"},
            "urls": {},
        }
    },
    "status": {"error_code": 0},
}

CMC_QUOTES_FIXTURE = {
    "data": {
        "98765": {"id": 98765, "quote": {"USD": {
            "price": 0.10, "volume_24h": 5000.0, "market_cap": 999999.0,
            "fully_diluted_market_cap": 1000000.0, "percent_change_24h": 5.0,
        }}},
    },
    "status": {"error_code": 0},
}


def test_collect_uses_cmc_market_cap_when_keyed_and_coingecko_lacks_it():
    """coinmarketcap is the last market provider: with a key it fills only the
    fields the keyless providers left UNKNOWN (market cap here)."""
    cg = dict(COINGECKO_FIXTURE)
    cg["market_data"] = dict(COINGECKO_FIXTURE["market_data"])
    cg["market_data"].pop("market_cap", None)   # CoinGecko does not know it

    routes = _merge_routes(cg)
    routes["pro-api.coinmarketcap.com/v2/cryptocurrency/info"] = CMC_INFO_FIXTURE
    routes["pro-api.coinmarketcap.com/v2/cryptocurrency/quotes"] = CMC_QUOTES_FIXTURE

    collector = ProviderCollector(transport=RoutingTransport(routes))
    # ProviderCollector builds adapters without a key by default; inject one.
    collector._providers["coinmarketcap"] = CoinMarketCapAdapter(
        transport=RoutingTransport(routes), api_key="MOCK")
    outcome = collector.collect("ethereum", "0xToken")

    assert outcome.provider_statuses["coinmarketcap"] == "OK"
    assert outcome.candidate.metrics.market_cap_usd == 999999.0
    assert outcome.field_sources["metrics.market_cap_usd"] == "coinmarketcap"
    # already-known fields are never overwritten by CMC (last provider wins law)
    assert outcome.candidate.metrics.liquidity_usd == 50000.0
    assert outcome.field_sources["metrics.liquidity_usd"] == "dexscreener"
