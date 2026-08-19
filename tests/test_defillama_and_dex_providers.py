"""Tests for DefiLlama and DEX Pool Intelligence Adapters (OSS-006)."""

from __future__ import annotations

import pytest

from architecture.providers.defillama import DefiLlamaAdapter
from architecture.providers.dex_pools import DEXPoolTracker


def test_defillama_adapter_mock_mode():
    adapter = DefiLlamaAdapter(mock_mode=True)

    tvl_data = adapter.get_protocol_tvl("uniswap")
    assert tvl_data["protocol"] == "uniswap"
    assert tvl_data["tvl_usd"] > 0
    assert tvl_data["confidence"] >= 0.90
    assert tvl_data["is_mock"] is True

    price_data = adapter.get_token_price("solana", "So11111111111111111111111111111111111111112")
    assert price_data["price_usd"] == 185.0
    assert price_data["symbol"] == "SOL"


def test_dex_pool_tracker_healthy_pool():
    metrics = DEXPoolTracker.evaluate_pool_metrics(
        pool_address="0x123456789",
        chain="solana",
        dex_name="raydium",
        base_reserve_usd=75000.0,
        quote_reserve_usd=75000.0,
        volume_24h_usd=250000.0,
        buys_24h=120,
        sells_24h=80,
    )

    assert metrics["total_liquidity_usd"] == 150000.0
    assert metrics["balance_score"] == 100.0
    assert metrics["exitability_rating"] == "HIGH_EXITABILITY"
    assert metrics["pool_health_score"] > 80.0


def test_dex_pool_tracker_illiquid_pool():
    metrics = DEXPoolTracker.evaluate_pool_metrics(
        pool_address="0xbadpool",
        chain="ethereum",
        dex_name="uniswap_v2",
        base_reserve_usd=1000.0,
        quote_reserve_usd=100.0,  # Unbalanced
        volume_24h_usd=500.0,
        buys_24h=2,
        sells_24h=1,
    )

    assert metrics["total_liquidity_usd"] == 1100.0
    assert metrics["balance_score"] < 50.0
    assert metrics["exitability_rating"] == "LOW_EXITABILITY_RISK"
