#!/usr/bin/env python3
"""Phase 4 intelligence engine — Evidence-only calculations.

Proves:
  - features / risk / scoring / explanations refuse raw data
  - IntelligenceEngine consumes EvidenceBundle
  - OpportunityScorer facade preserves the historic deterministic floor
  - optional intel signals attach only as extra Evidence
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.explanations import ExplanationEngine
from architecture.features import FeatureExtractor, FeatureVector
from architecture.intelligence import (
    Evidence,
    EvidenceBundle,
    EvidenceContractError,
    IntelligenceEngine,
    TokenRef,
    materialize_evidence,
)
from architecture.intelligence.adapters import (
    collect_intel_evidence,
    evidence_from_narrative,
    evidence_from_virality,
)
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.risk import RiskEngine
from architecture.scoring.calculator import OpportunityCalculator
from architecture.scoring.engine import OpportunityScorer
from architecture.intel.news import NarrativeSignal
from architecture.intel.viral import ViralitySignal


NOW = 1_787_000_000.0


def _candidate(**kwargs) -> NormalizedTokenCandidate:
    metrics = kwargs.pop("metrics", MarketMetrics(
        price_usd=0.05, liquidity_usd=60000.0, volume_1h=30000.0,
        txns_1h_buys=60, txns_1h_sells=20,
    ))
    security = kwargs.pop("security", SecuritySignals(
        is_honeypot=False, is_contract_verified=True,
        is_ownership_renounced=True, has_mint_authority=False,
        has_freeze_authority=False, top10_holder_concentration_pct=25.0,
    ))
    return NormalizedTokenCandidate(
        chain=kwargs.pop("chain", "solana"),
        address=kwargs.pop("address", "GoodSolanaTok11111111111111111111111111111"),
        symbol=kwargs.pop("symbol", "GOOD"),
        name=kwargs.pop("name", "Good Token"),
        metrics=metrics,
        security=security,
        social_presence=kwargs.pop("social_presence", {"twitter": "https://x.com/good"}),
        source_provider=kwargs.pop("source_provider", "dexscreener"),
        retrieved_ts=kwargs.pop("retrieved_ts", NOW),
    )


def _empty_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        identity=TokenRef("solana", "x", "X", "X", "none", NOW),
        items=(),
        evaluated_at=NOW,
    )


def test_materialize_evidence_emits_provenance_bearing_atoms():
    bundle = materialize_evidence(_candidate(), now=NOW)
    assert isinstance(bundle, EvidenceBundle)
    assert all(isinstance(e, Evidence) for e in bundle.items)
    liq = bundle.known("liquidity_usd")
    assert liq is not None and liq.value == 60000.0
    assert liq.status == "VERIFIED"
    assert liq.sha256
    assert bundle.provenance_sha256()


def test_feature_extractor_rejects_raw_candidate():
    with pytest.raises(EvidenceContractError):
        FeatureExtractor().extract(_candidate())  # type: ignore[arg-type]


def test_risk_engine_rejects_raw_candidate():
    with pytest.raises(EvidenceContractError):
        RiskEngine().assess({"liquidity_usd": 1})  # type: ignore[arg-type]


def test_calculator_rejects_raw_candidate():
    feats = FeatureVector()
    risk = RiskEngine().assess(_empty_bundle())
    with pytest.raises(EvidenceContractError):
        OpportunityCalculator().calculate(_candidate(), feats, risk)  # type: ignore[arg-type]


def test_explainer_rejects_raw_candidate():
    bundle = _empty_bundle()
    feats = FeatureExtractor().extract(bundle)
    risk = RiskEngine().assess(bundle)
    score = OpportunityCalculator().calculate(bundle, feats, risk)
    with pytest.raises(EvidenceContractError):
        ExplanationEngine().explain(_candidate(), feats, risk, score)  # type: ignore[arg-type]


def test_intelligence_engine_rejects_raw_candidate():
    with pytest.raises(EvidenceContractError):
        IntelligenceEngine().evaluate(_candidate())  # type: ignore[arg-type]


def test_scorer_facade_matches_intelligence_engine():
    cand = _candidate()
    scorer_rep = OpportunityScorer().evaluate(cand, now=NOW)
    intel = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    facade = OpportunityScorer.from_intelligence(intel)
    assert scorer_rep.opportunity_score == facade.opportunity_score == intel.opportunity_score
    assert scorer_rep.confidence_level == facade.confidence_level == "HIGH"
    assert scorer_rep.risk_level == facade.risk_level == "LOW"
    assert scorer_rep.positive_reasons == facade.positive_reasons
    assert [r.risk_id for r in scorer_rep.risk_deductions] == [r.risk_id for r in facade.risk_deductions]


def test_high_quality_token_scores_via_evidence_only():
    intel = IntelligenceEngine().evaluate(materialize_evidence(_candidate(), now=NOW))
    assert intel.opportunity_score >= 80.0
    assert intel.features.base_score >= 80.0
    assert intel.risk.findings == []
    assert len(intel.explanation.report_evidence) >= 4
    assert intel.explanation.missing_unknowns == []
    assert len(intel.explanation.invalidation_conditions) == 4


def test_honeypot_is_a_critical_evidence_backed_veto():
    cand = _candidate(
        symbol="SCAM",
        security=SecuritySignals(is_honeypot=True),
        metrics=MarketMetrics(liquidity_usd=50000.0, volume_1h=20000.0),
        social_presence={},
        source_provider="goplus",
    )
    intel = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    assert intel.opportunity_score == 0.0
    assert intel.risk_level == "CRITICAL"
    assert intel.risk.has("CRITICAL_HONEYPOT")
    assert any(e.key == "is_honeypot" and e.value is True for e in intel.evidence.items)


def test_unknown_fields_are_evidence_not_zeros():
    cand = NormalizedTokenCandidate(
        chain="solana", address="SparseSolana11111111111111111111111111111",
        symbol="SPARSE", name="Sparse Data", source_provider="dexscreener",
        retrieved_ts=NOW,
    )
    bundle = materialize_evidence(cand, now=NOW)
    assert numeric_is_unknown(bundle, "liquidity_usd")
    intel = IntelligenceEngine().evaluate(bundle)
    assert intel.confidence_level == "LOW"
    assert len(intel.explanation.missing_unknowns) >= 3


def numeric_is_unknown(bundle: EvidenceBundle, key: str) -> bool:
    item = bundle.get(key)
    return item is None or item.value is None or item.status == "UNKNOWN"


def test_determinism_same_evidence_same_report():
    cand = _candidate()
    a = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    b = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    assert a.opportunity_score == b.opportunity_score
    assert a.score.components == b.score.components
    assert a.explanation.positive_reasons == b.explanation.positive_reasons
    assert [r.risk_id for r in a.risk.findings] == [r.risk_id for r in b.risk.findings]


def test_intel_signals_attach_as_extra_evidence_only():
    narrative = NarrativeSignal(
        subject="GOOD", sentiment=0.6, label="BULLISH",
        mention_count=2, high_impact_count=0,
        evidence=[{"title": "listing", "source": "coindesk", "sha256": "abc123def456"}],
        computed_ts=NOW,
    )
    virality = ViralitySignal(
        subject="GOOD", label="VIRAL", score=70.0,
        txn_acceleration=4.0, volume_acceleration=3.0, buy_pressure=2.0,
        wash_suspected=True, is_paid_promotion=False, computed_ts=NOW,
    )
    # The fixture signal was computed FROM observed txn data, so the caller
    # declares txns_seen — otherwise the honest default (UNKNOWN) would
    # suppress the wash flag (never a fabricated negative from missing data).
    extra = collect_intel_evidence(narrative=narrative, virality=virality,
                                   boost_seen=True, txns_seen=True)
    assert extra
    assert all(isinstance(e, Evidence) for e in extra)
    assert any(e.key == "narrative_label" for e in extra)
    assert evidence_from_narrative(narrative)
    assert evidence_from_virality(virality, boost_seen=True, txns_seen=True)

    intel = IntelligenceEngine().evaluate(
        materialize_evidence(_candidate(), now=NOW), extra=extra,
    )
    assert intel.evidence.get("wash_suspected") is not None
    assert intel.risk.has("WASH_SUSPECTED")

    # WITHOUT the flags the same signal must NOT leak a fabricated wash
    # finding — the honest default is UNKNOWN/absent.
    intel_unflagged = IntelligenceEngine().evaluate(
        materialize_evidence(_candidate(), now=NOW),
        extra=collect_intel_evidence(narrative=narrative, virality=virality),
    )
    wash = intel_unflagged.evidence.get("wash_suspected")
    assert wash is not None and wash.value is None and wash.status == "UNKNOWN"


def test_extended_bundle_does_not_mutate_original():
    bundle = materialize_evidence(_candidate(), now=NOW)
    extra = [Evidence(
        key="probe", description="probe", value=1, provider="t",
        timestamp=NOW, freshness_seconds=0, status="VERIFIED",
    )]
    extended = bundle.extended(extra)
    assert bundle.get("probe") is None
    assert extended.get("probe") is not None
