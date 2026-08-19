"""Tests for AHOS Resilient AI Router & Debate Council (OSS-002 & OSS-007)."""

from __future__ import annotations

import pytest

from architecture.ai.debate_council import AdversarialDebateCouncil
from architecture.ai.router import AIProviderRouter


def test_ai_provider_router_heuristic_fallback():
    # When Ollama is offline (invalid URL), should seamlessly fallback to Tier 3
    router = AIProviderRouter(ollama_url="http://127.0.0.1:99999")
    result = router.generate_completion("Analyze market liquidity")

    assert result["success"] is True
    assert result["tier"] == "TIER_3_DETERMINISTIC_HEURISTIC"
    assert "recommendation" in result["data"]


def test_debate_council_normal_consensus():
    council = AdversarialDebateCouncil()
    debate = council.conduct_debate(
        token_symbol="SOL",
        price_usd=185.0,
        liquidity_usd=150000.0,
        security_score=92.0,
        momentum_score=85.0,
    )

    assert debate["token_symbol"] == "SOL"
    assert debate["risk_veto"] is False
    assert debate["consensus_recommendation"] == "HIGH_OPPORTUNITY"
    assert debate["consensus_score"] > 80.0
    assert "BULL_RESEARCHER" in debate["bull_perspective"]["persona"]


def test_debate_council_risk_veto_low_security():
    council = AdversarialDebateCouncil()
    debate = council.conduct_debate(
        token_symbol="SHADY",
        price_usd=0.001,
        liquidity_usd=50000.0,
        security_score=25.0,  # Below 40 threshold
        momentum_score=95.0,
    )

    assert debate["risk_veto"] is True
    assert debate["consensus_recommendation"] == "REJECT_RISK_VETO"
    assert debate["consensus_score"] == 0.0
    assert "Security score below 40.0" in debate["risk_veto_reason"]


def test_debate_council_risk_veto_low_liquidity():
    council = AdversarialDebateCouncil()
    debate = council.conduct_debate(
        token_symbol="TINY",
        price_usd=1.0,
        liquidity_usd=2000.0,  # Below 5k threshold
        security_score=95.0,
        momentum_score=90.0,
    )

    assert debate["risk_veto"] is True
    assert "Pool liquidity under $5,000" in debate["risk_veto_reason"]
