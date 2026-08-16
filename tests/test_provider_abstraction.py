#!/usr/bin/env python3
"""Tests for Provider Abstraction Framework (Section VII)."""
import sys, json, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals, UNKNOWN_VALUE
)
from architecture.providers.adapters import (
    DexScreenerAdapter, GeckoTerminalAdapter, GoPlusSecurityAdapter, RugCheckSecurityAdapter
)
from architecture.providers.registry import ProviderRouter


class MockHttpResponse:
    def __init__(self, data: dict, status: int = 200):
        self._data = json.dumps(data).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._data


def test_unknown_fields_identification():
    candidate = NormalizedTokenCandidate(
        chain="solana",
        address="TestAddress1111111111111111111111111111",
        symbol="TEST",
        name="Test Token",
        source_provider="unit_test"
    )
    unknowns = candidate.identify_unknowns()
    assert "metrics.liquidity_usd" in unknowns
    assert "metrics.volume_1h" in unknowns
    assert "security.is_honeypot" in unknowns
    assert "social_presence" in unknowns


def test_dexscreener_adapter_parsing():
    mock_payload = {
        "pairs": [
            {
                "chainId": "solana",
                "dexId": "raydium",
                "pairAddress": "PairAddr1111111111111111111111111111",
                "baseToken": {
                    "address": "TokAddr1111111111111111111111111111",
                    "symbol": "DEX",
                    "name": "Dex Token"
                },
                "priceUsd": "1.25",
                "liquidity": {"usd": 50000.0},
                "volume": {"h1": 12000.0, "h24": 150000.0, "m5": 500.0},
                "txns": {"h1": {"buys": 45, "sells": 20}}
            }
        ]
    }
    adapter = DexScreenerAdapter(transport=lambda req, timeout=None: MockHttpResponse(mock_payload))
    resp = adapter.fetch_candidate_tokens("solana", limit=1)
    assert resp.status == "OK"
    assert len(resp.tokens) == 1
    tok = resp.tokens[0]
    assert tok.symbol == "DEX"
    assert tok.metrics.price_usd == 1.25
    assert tok.metrics.liquidity_usd == 50000.0
    assert tok.metrics.volume_1h == 12000.0
    assert tok.metrics.txns_1h_buys == 45


def test_goplus_security_adapter_parsing():
    mock_payload = {
        "code": 1,
        "message": "OK",
        "result": {
            "0x1111111111111111111111111111111111111111": {
                "is_honeypot": "0",
                "buy_tax": "0.01",
                "sell_tax": "0.01",
                "is_open_source": "1",
                "can_take_back_ownership": "0",
                "is_mintable": "0"
            }
        }
    }
    adapter = GoPlusSecurityAdapter(transport=lambda req, timeout=None: MockHttpResponse(mock_payload))
    resp = adapter.fetch_token_metrics("ethereum", "0x1111111111111111111111111111111111111111")
    assert resp.status == "OK"
    assert len(resp.tokens) == 1
    sec = resp.tokens[0].security
    assert sec.is_honeypot is False
    assert sec.is_contract_verified is True
    assert sec.is_ownership_renounced is True
    assert sec.has_mint_authority is False


def test_provider_router_deduplication():
    mock_payload = {
        "pairs": [
            {
                "chainId": "solana",
                "baseToken": {"address": "SharedAddr111111111111111111111111111", "symbol": "SHR", "name": "Shared"},
                "priceUsd": "2.0"
            }
        ]
    }
    router = ProviderRouter(transport=lambda req, timeout=None: MockHttpResponse(mock_payload))
    candidates = router.discover_candidates("solana", limit=5)
    # Deduplication ensures unique (chain, address)
    addrs = [c.address for c in candidates]
    assert len(addrs) == len(set(addrs))
