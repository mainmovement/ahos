"""AHOS Multi-Chain DEX Liquidity Pool Tracker (GeckoTerminal & DexScreener Pattern).

Tracks decentralized exchange liquidity pool reserves, swap volumes,
reserve balances, and liquidity exitability.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


class DEXPoolTracker:
    """Analyzes DEX liquidity pool health, reserves, and exitability."""

    @staticmethod
    def evaluate_pool_metrics(
        pool_address: str,
        chain: str,
        dex_name: str,
        base_reserve_usd: float,
        quote_reserve_usd: float,
        volume_24h_usd: float,
        buys_24h: int,
        sells_24h: int,
    ) -> Dict[str, Any]:
        """Evaluates DEX liquidity pool balance and exitability health."""
        total_liquidity_usd = base_reserve_usd + quote_reserve_usd
        if total_liquidity_usd <= 0:
            return {
                "pool_address": pool_address,
                "chain": chain,
                "dex_name": dex_name,
                "total_liquidity_usd": 0.0,
                "pool_health_score": 0.0,
                "exitability_rating": "CRITICAL_ILLIQUID",
            }

        # 1. Reserve Balance Ratio (ideal: 50% base / 50% quote)
        base_ratio = base_reserve_usd / total_liquidity_usd
        balance_penalty = abs(base_ratio - 0.5) * 2.0  # 0 is perfectly balanced, 1 is 100% one-sided
        balance_score = max(0.0, 100.0 * (1.0 - balance_penalty))

        # 2. Volume-to-Liquidity Ratio (Turnover)
        turnover = volume_24h_usd / total_liquidity_usd

        # 3. Buy/Sell Transaction Ratio
        total_txs = buys_24h + sells_24h
        buy_ratio = (buys_24h / total_txs) if total_txs > 0 else 0.5
        tx_pressure_score = (
            buy_ratio * 100.0 if total_txs >= 10 else 50.0
        )

        # 4. Composite Pool Health Score
        health_score = (
            (balance_score * 0.40)
            + (min(100.0, total_liquidity_usd / 1000.0) * 0.40)
            + (tx_pressure_score * 0.20)
        )

        if total_liquidity_usd >= 100000.0 and balance_score >= 80.0:
            rating = "HIGH_EXITABILITY"
        elif total_liquidity_usd >= 20000.0 and balance_score >= 50.0:
            rating = "MODERATE_EXITABILITY"
        else:
            rating = "LOW_EXITABILITY_RISK"

        return {
            "pool_address": pool_address,
            "chain": chain,
            "dex_name": dex_name,
            "total_liquidity_usd": round(total_liquidity_usd, 2),
            "base_ratio": round(base_ratio, 3),
            "balance_score": round(balance_score, 1),
            "turnover_24h": round(turnover, 2),
            "buy_ratio": round(buy_ratio, 3),
            "pool_health_score": round(health_score, 1),
            "exitability_rating": rating,
        }
