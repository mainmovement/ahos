#!/usr/bin/env python3
"""Tests for Evidence-Based Opportunity Scoring (Section VIII)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals


def test_scorer_high_quality_opportunity():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="GoodSolanaTok11111111111111111111111111111",
        symbol="GOOD",
        name="Good Token",
        metrics=MarketMetrics(
            price_usd=0.05,
            liquidity_usd=60000.0,
            volume_1h=30000.0,
            txns_1h_buys=60,
            txns_1h_sells=20
        ),
        security=SecuritySignals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True,
            has_mint_authority=False,
            has_freeze_authority=False,
            top10_holder_concentration_pct=25.0
        ),
        social_presence={"twitter": "https://x.com/good"},
        source_provider="dexscreener",
        retrieved_ts=time.time()
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)

    assert rep.opportunity_score >= 80.0
    assert rep.confidence_level == "HIGH"
    assert rep.risk_level == "LOW"
    assert len(rep.positive_reasons) >= 3
    assert len(rep.invalidation_conditions) == 4
    assert len(rep.missing_unknowns) == 0


def test_scorer_critical_honeypot_penalty():
    cand = NormalizedTokenCandidate(
        chain="ethereum",
        address="0x2222222222222222222222222222222222222222",
        symbol="SCAM",
        name="Scam Token",
        metrics=MarketMetrics(
            liquidity_usd=50000.0,
            volume_1h=20000.0
        ),
        security=SecuritySignals(
            is_honeypot=True
        ),
        source_provider="goplus",
        retrieved_ts=time.time()
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)

    assert rep.opportunity_score == 0.0
    assert rep.risk_level == "CRITICAL"
    assert any(r.risk_id == "CRITICAL_HONEYPOT" for r in rep.risk_deductions)


def test_scorer_explainability_answers():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaTokExplain1111111111111111111111111111",
        symbol="EXPL",
        name="Explain Token",
        metrics=MarketMetrics(liquidity_usd=15000.0, volume_1h=8000.0),
        source_provider="geckoterminal",
        retrieved_ts=time.time()
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)

    assert rep.answer_why_scored() != ""
    assert len(rep.answer_evidence()) >= 2
    assert len(rep.answer_missing()) >= 1
    assert len(rep.answer_invalidation()) == 4
