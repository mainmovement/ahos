#!/usr/bin/env python3
"""Deep Feature & Scoring Permutation Matrix Tests (Phase XXI)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals


@pytest.mark.parametrize("liq,vol,expected_min_score", [
    (100000.0, 50000.0, 70.0),
    (50000.0, 25000.0, 60.0),
    (10000.0, 5000.0, 40.0),
    (2000.0, 1000.0, 20.0),
])
def test_scoring_liquidity_and_volume_brackets(liq, vol, expected_min_score):
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="BracketSolana1111111111111111111111111111",
        symbol="BRKT",
        name="Bracket Token",
        source_provider="dexscreener",
        metrics=MarketMetrics(liquidity_usd=liq, volume_1h=vol, txns_1h_buys=20, txns_1h_sells=10),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True)
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    assert rep.opportunity_score >= expected_min_score


@pytest.mark.parametrize("buys,sells,expected_pressure_reason", [
    (80, 20, "برتری خریداران"),
    (50, 50, "تعادل مناسب"),
])
def test_scoring_buy_sell_pressure_analysis(buys, sells, expected_pressure_reason):
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="TxPressureSolana1111111111111111111111111",
        symbol="TXP",
        name="Tx Pressure",
        source_provider="dexscreener",
        metrics=MarketMetrics(liquidity_usd=20000.0, volume_1h=10000.0, txns_1h_buys=buys, txns_1h_sells=sells),
        security=SecuritySignals(is_honeypot=False)
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    assert any(expected_pressure_reason in r for r in rep.positive_reasons)


def test_scoring_mint_and_freeze_authority_penalties():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="MintFreezeSolana1111111111111111111111111",
        symbol="MFTOK",
        name="Mint Freeze",
        source_provider="rugcheck",
        metrics=MarketMetrics(liquidity_usd=30000.0, volume_1h=10000.0),
        security=SecuritySignals(
            is_honeypot=False,
            has_mint_authority=True,
            has_freeze_authority=True
        )
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    assert any(r.risk_id == "MINT_AUTHORITY_ACTIVE" for r in rep.risk_deductions)
    assert any(r.risk_id == "FREEZE_AUTHORITY_ACTIVE" for r in rep.risk_deductions)
    assert rep.risk_level in ("HIGH", "CRITICAL")


def test_scoring_unverified_contract_penalty():
    cand = NormalizedTokenCandidate(
        chain="ethereum",
        address="0x4444444444444444444444444444444444444444",
        symbol="UNVER",
        name="Unverified",
        source_provider="goplus",
        metrics=MarketMetrics(liquidity_usd=20000.0, volume_1h=10000.0),
        security=SecuritySignals(
            is_honeypot=False,
            is_contract_verified=False
        )
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    assert any(r.risk_id == "UNVERIFIED_CONTRACT" for r in rep.risk_deductions)


def test_scoring_confidence_levels():
    scorer = OpportunityScorer()

    # Complete data -> HIGH confidence
    cand_full = NormalizedTokenCandidate(
        chain="solana",
        address="FullSolana1111111111111111111111111111111",
        symbol="FULL",
        name="Full Data",
        source_provider="dexscreener",
        metrics=MarketMetrics(price_usd=1.0, liquidity_usd=20000.0, volume_1h=10000.0),
        security=SecuritySignals(is_honeypot=False, top10_holder_concentration_pct=30.0),
        social_presence={"x": "https://x.com/full"}
    )
    assert scorer.evaluate(cand_full).confidence_level == "HIGH"

    # Missing multiple fields -> LOW confidence
    cand_sparse = NormalizedTokenCandidate(
        chain="solana",
        address="SparseSolana11111111111111111111111111111",
        symbol="SPARSE",
        name="Sparse Data",
        source_provider="dexscreener"
    )
    assert scorer.evaluate(cand_sparse).confidence_level == "LOW"
