#!/usr/bin/env python3
"""Phase 5 security intelligence — Evidence-only contract and holder risk."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence import (
    EvidenceContractError,
    IntelligenceEngine,
    materialize_evidence,
)
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.risk import RiskEngine
from architecture.security import (
    ContractAnalyzer,
    HolderAnalyzer,
    LiquidityAnalyzer,
    ManipulationDetector,
    SecurityIntelligence,
    sanitize_secrets,
    REDACTED_TEXT,
)

NOW = 1_787_000_000.0


def _cand(**kwargs) -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain="solana",
        address=kwargs.pop("address", "SecTok111111111111111111111111111111111"),
        symbol=kwargs.pop("symbol", "SEC"),
        name="Security Token",
        source_provider=kwargs.pop("source_provider", "dexscreener"),
        retrieved_ts=NOW,
        metrics=kwargs.pop("metrics", MarketMetrics(liquidity_usd=40000.0, volume_1h=12000.0)),
        security=kwargs.pop("security", SecuritySignals()),
        social_presence=kwargs.pop("social_presence", {}),
        pair_created_ts=kwargs.pop("pair_created_ts", None),
    )


def test_hygiene_reexport_still_works():
    assert REDACTED_TEXT in sanitize_secrets("sk-1234567890abcdefghijklmnopqrstuvwxyz12")


def test_analyzers_reject_raw_data():
    raw = _cand()
    with pytest.raises(EvidenceContractError):
        ContractAnalyzer().analyze(raw)  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        LiquidityAnalyzer().analyze({"x": 1})  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        HolderAnalyzer().analyze(raw)  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        ManipulationDetector().analyze(raw)  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        SecurityIntelligence().analyze(raw)  # type: ignore[arg-type]


def test_ownership_mint_freeze_and_proxy():
    cand = _cand(security=SecuritySignals(
        is_ownership_renounced=False,
        has_mint_authority=True,
        has_freeze_authority=True,
        is_honeypot=False,
        is_contract_verified=False,
    ))
    # duck-type proxy onto the security object
    cand.security.is_proxy = True  # type: ignore[attr-defined]
    bundle = materialize_evidence(cand, now=NOW)
    report = SecurityIntelligence().analyze(bundle)
    ids = {f.risk_id for f in report.findings}
    assert "OWNERSHIP_NOT_RENOUNCED" in ids
    assert "MINT_AUTHORITY_ACTIVE" in ids
    assert "FREEZE_AUTHORITY_ACTIVE" in ids
    assert "PROXY_UPGRADEABLE" in ids
    assert "UNVERIFIED_CONTRACT" in ids
    assert report.has("MINT_AUTHORITY_ACTIVE")
    assert any(e.key == "contract_risk_label" for e in report.derived_evidence)


def test_honeypot_and_deployer_rug_are_critical():
    cand = _cand(security=SecuritySignals(is_honeypot=True, deployer_past_rug_count=2))
    report = SecurityIntelligence().analyze(materialize_evidence(cand, now=NOW))
    assert report.has("CRITICAL_HONEYPOT")
    assert report.has("DEPLOYER_PRIOR_RUG")
    assert any(f.severity == "CRITICAL" for f in report.findings)


def test_unlocked_and_young_pool_liquidity_risk():
    cand = _cand(
        pair_created_ts=NOW - 3600,
        security=SecuritySignals(liquidity_locked_pct=5.0, liquidity_burned_pct=0.0),
    )
    report = LiquidityAnalyzer().analyze(materialize_evidence(cand, now=NOW))
    ids = {f.risk_id for f in report.findings}
    assert "UNLOCKED_LP" in ids
    assert "YOUNG_UNLOCKED_POOL" in ids
    assert report.lock_quality is not None and report.lock_quality < 0.3


def test_holder_concentration_and_single_wallet():
    cand = _cand()
    cand.security.top10_holder_concentration_pct = 85.0
    cand.security.top1_holder_concentration_pct = 30.0  # type: ignore[attr-defined]
    cand.holder_count = 12
    report = HolderAnalyzer().analyze(materialize_evidence(cand, now=NOW))
    ids = {f.risk_id for f in report.findings}
    assert "HIGH_HOLDER_CONCENTRATION" in ids
    assert "SINGLE_WALLET_DOMINANCE" in ids
    assert "THIN_HOLDER_BASE" in ids


def test_manipulation_tax_and_wash():
    from architecture.intelligence.evidence import make_derived_evidence

    cand = _cand(security=SecuritySignals(sell_tax_pct=40.0, buy_tax_pct=12.0))
    bundle = materialize_evidence(cand, now=NOW).extended([
        make_derived_evidence(
            "wash_suspected", "wash", True, provider="t", timestamp=NOW,
            source_field="wash",
        )
    ])
    report = ManipulationDetector().analyze(bundle)
    ids = {f.risk_id for f in report.findings}
    assert "EXTREME_SELL_TAX" in ids
    assert "HIGH_BUY_TAX" in ids
    assert "WASH_SUSPECTED" in ids


def test_unknown_does_not_invent_findings():
    report = SecurityIntelligence().analyze(materialize_evidence(_cand(), now=NOW))
    # No security flags set → no invented ownership/proxy/lock findings
    assert not report.has("OWNERSHIP_NOT_RENOUNCED")
    assert not report.has("PROXY_UPGRADEABLE")
    assert not report.has("UNLOCKED_LP")


def test_risk_engine_merges_without_double_counting():
    cand = _cand(security=SecuritySignals(is_honeypot=True, has_mint_authority=True))
    bundle = materialize_evidence(cand, now=NOW)
    risk = RiskEngine().assess(bundle)
    honeypots = [f for f in risk.findings if f.risk_id == "CRITICAL_HONEYPOT"]
    mints = [f for f in risk.findings if f.risk_id == "MINT_AUTHORITY_ACTIVE"]
    assert len(honeypots) == 1
    assert len(mints) == 1


def test_clean_token_still_has_empty_risk_findings():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="GoodSolanaTok11111111111111111111111111111",
        symbol="GOOD", name="Good Token",
        source_provider="dexscreener", retrieved_ts=NOW,
        metrics=MarketMetrics(
            price_usd=0.05, liquidity_usd=60000.0, volume_1h=30000.0,
            txns_1h_buys=60, txns_1h_sells=20,
        ),
        security=SecuritySignals(
            is_honeypot=False, is_contract_verified=True,
            is_ownership_renounced=True, has_mint_authority=False,
            has_freeze_authority=False, top10_holder_concentration_pct=25.0,
        ),
        social_presence={"twitter": "https://x.com/good"},
    )
    intel = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    assert intel.risk.findings == []
    assert intel.security is not None
    assert intel.features.get("ownership_hygiene") is not None
    assert intel.opportunity_score >= 80.0


def test_security_findings_reduce_opportunity_score():
    clean = _cand(security=SecuritySignals(is_honeypot=False, is_contract_verified=True),
                  social_presence={"x": "1"})
    dirty = _cand(security=SecuritySignals(
        is_honeypot=False, is_contract_verified=True, has_mint_authority=True,
    ), social_presence={"x": "1"})
    engine = IntelligenceEngine()
    a = engine.evaluate(materialize_evidence(clean, now=NOW))
    b = engine.evaluate(materialize_evidence(dirty, now=NOW))
    assert b.opportunity_score < a.opportunity_score
    assert b.risk.has("MINT_AUTHORITY_ACTIVE")
