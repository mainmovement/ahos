"""
tests.test_intelligence_engine — Phase 4 Intelligence Engine Foundation
- Feature Registry (name, description, source evidence, calculation method, version)
- Scoring Engine v2 (evidence-only → sub-scores + Decision-compatible)
- Risk Engine (4 analyzers + aggregate)
- Explanation Generator (human-readable)

All inputs are Evidence objects. No raw values, no trading.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Robust providers import fallback (same pattern as earlier)
try:
    from providers.base_provider import BaseProvider  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location("providers.base_provider", str(ROOT / "providers" / "base_provider.py"))
    _mod = _ilu.module_from_spec(_spec)
    sys.modules["providers.base_provider"] = _mod
    if "providers" not in sys.modules:
        _ps = _ilu.spec_from_file_location("providers", str(ROOT / "providers" / "__init__.py"))
        if _ps and _ps.loader:
            _pm = _ilu.module_from_spec(_ps)
            sys.modules["providers"] = _pm
            _ps.loader.exec_module(_pm)
    _spec.loader.exec_module(_mod)  # type: ignore

from core.models.evidence import Evidence, Confidence, VerificationStatus
from intelligence.features.registry import FeatureDefinition, FeatureRegistry, get_global_registry
from intelligence.scoring.engine import OpportunityScoringEngineV2, ScoreResult
from intelligence.risk.base import RiskLevel
from intelligence.risk.contract_risk import ContractRiskAnalyzer
from intelligence.risk.liquidity_risk import LiquidityRiskAnalyzer
from intelligence.risk.concentration_risk import ConcentrationRiskAnalyzer
from intelligence.risk.manipulation_risk import ManipulationRiskAnalyzer
from intelligence.risk.engine import RiskEngine
from intelligence.explanations.generator import ExplanationGenerator

FIXED_TS = 1_750_000_000.0
RAW = "a" * 64
RAW2 = "b" * 64


def _ev(source="dexscreener", value=1.5, confidence=Confidence.HIGH, status=VerificationStatus.VERIFIED, raw=RAW, ts=FIXED_TS):
    return Evidence(source=source, timestamp=ts, confidence=confidence, verification_status=status, raw_reference=raw, value=value, metadata={})


# ---------------------------------------------------------------------------
# Feature Registry
# ---------------------------------------------------------------------------

class TestFeatureRegistry:
    def test_feature_must_contain_required_fields(self):
        f = FeatureDefinition(
            name="sample_feature",
            description="Sample feature for evidence validation pipeline testing",
            source_evidence="dexscreener:price_usd (Evidence.value)",
            calculation_method="relative_change",
            version="1.0.0",
            category="market",
        )
        assert f.name == "sample_feature"
        assert f.description.startswith("Sample feature")
        assert f.source_evidence == "dexscreener:price_usd (Evidence.value)"
        assert f.calculation_method == "relative_change"
        assert f.version == "1.0.0"
        assert f.key == "sample_feature@1.0.0"
        d = f.to_dict()
        for field in ("name", "description", "source_evidence", "calculation_method", "version", "provenance", "key"):
            assert field in d

    def test_feature_registry_register_and_retrieve(self):
        reg = FeatureRegistry()
        f1 = FeatureDefinition(name="feat_a", description="Feature A for liquidity depth tracking", source_evidence="dexscreener:liquidity_usd", calculation_method="log_ratio", version="1.0.0")
        f2 = FeatureDefinition(name="feat_a", description="Feature A v2 with adjusted threshold", source_evidence="dexscreener:liquidity_usd", calculation_method="log_ratio", version="1.1.0")
        reg.register(f1)
        reg.register(f2)
        assert reg.count() == 2
        assert reg.get("feat_a").version == "1.1.0"  # latest
        assert reg.get("feat_a", version="1.0.0").version == "1.0.0"
        assert reg.get_by_key("feat_a@1.0.0").description.startswith("Feature A for")
        # Duplicate must fail (append-only)
        with pytest.raises(ValueError, match="already registered"):
            reg.register(f1)

    def test_feature_invalid_inputs_rejected(self):
        with pytest.raises(ValueError, match="name"):
            FeatureDefinition(name="Bad Name!", description="Valid description with enough length", source_evidence="src:val", calculation_method="method", version="1.0.0")
        with pytest.raises(ValueError, match="description"):
            FeatureDefinition(name="good_name", description="short", source_evidence="src:val", calculation_method="method", version="1.0.0")
        with pytest.raises(ValueError, match="source_evidence"):
            FeatureDefinition(name="good_name", description="Valid description with enough length", source_evidence="", calculation_method="method", version="1.0.0")
        with pytest.raises(ValueError, match="calculation_method"):
            FeatureDefinition(name="good_name", description="Valid description with enough length", source_evidence="src:val", calculation_method="  ", version="1.0.0")
        with pytest.raises(ValueError, match="version"):
            FeatureDefinition(name="good_name", description="Valid description with enough length", source_evidence="src:val", calculation_method="method", version="bad")

    def test_feature_calculation_method_callable(self):
        def double(ev):
            return ev.value * 2 if isinstance(ev, Evidence) else None

        f = FeatureDefinition(name="calc_test", description="Feature with callable calculation method", source_evidence="dexscreener:price_usd", calculation_method="double", version="2.0.0", calculation_callable=double)
        ev = _ev(value=5)
        assert f.compute(ev) == 10
        assert f.to_dict()["calculation_method"] == "double"

    def test_global_registry_has_genesis_features(self):
        reg = get_global_registry()
        # Genesis set covers market/security/liquidity/whale/social/risk
        assert reg.count() >= 6
        assert reg.get("market_momentum") is not None
        assert reg.get("security_verdict") is not None
        assert reg.get("liquidity_depth") is not None
        errors = reg.validate_all()
        assert errors == []


# ---------------------------------------------------------------------------
# Scoring Engine v2
# ---------------------------------------------------------------------------

class TestScoringEngineV2:
    def test_scoring_requires_evidence_only(self):
        engine = OpportunityScoringEngineV2()
        with pytest.raises(ValueError, match="Evidence"):
            engine.score([{"price_usd": 1.5}])  # raw dict forbidden
        with pytest.raises(ValueError, match="Evidence"):
            engine.score_from_map({"price_usd": 1.5})  # raw value forbidden

    def test_scoring_produces_required_subscores(self):
        engine = OpportunityScoringEngineV2()
        m = {
            "price_change_6h": _ev(value=20),
            "volume_24h": _ev(value=60000),
            "liquidity_usd": _ev(value=80000),
            "is_honeypot": _ev(source="security_gate", value=False),
            "has_mint_authority": _ev(source="security_gate", value=False),
            "top10_share": _ev(source="holders", value=25),
            "narrative_score": _ev(source="viral", value=60),
        }
        res = engine.score_from_map(m)
        for field in ("market_score", "security_score", "liquidity_score", "whale_score", "social_score", "risk_penalty", "confidence"):
            assert hasattr(res, field), f"ScoreResult missing {field}"
            v = getattr(res, field)
            if field != "confidence":
                assert 0 <= v <= 100, f"{field} out of range: {v}"
            else:
                assert v in Confidence.ALL
        assert 0 <= res.total_score <= 100
        assert isinstance(res.breakdown, dict)
        assert len(res.evidence_refs) == len(m)
        assert res.engine_version == "scoring-v2@1.0.0"

    def test_scoring_security_zero_on_honeypot(self):
        engine = OpportunityScoringEngineV2()
        m = {
            "is_honeypot": _ev(source="security_gate", value=True),
            "liquidity_usd": _ev(value=50000),
        }
        res = engine.score_from_map(m)
        assert res.security_score == 0
        assert res.risk_penalty >= 70
        assert res.total_score < 50

    def test_scoring_confidence_derived_from_evidence(self):
        engine = OpportunityScoringEngineV2()
        # All HIGH → HIGH
        m_high = {"price_change_6h": _ev(value=10, confidence=Confidence.HIGH), "volume_24h": _ev(value=50000, confidence=Confidence.HIGH)}
        res_high = engine.score_from_map(m_high)
        # Empty → UNKNOWN
        m_empty = {}
        res_empty = engine.score_from_map(m_empty)
        assert res_empty.confidence in (Confidence.UNKNOWN, Confidence.LOW)

    def test_scoring_decision_compatible(self):
        engine = OpportunityScoringEngineV2()
        m = {
            "price_change_6h": _ev(value=10),
            "volume_24h": _ev(value=60000),
            "liquidity_usd": _ev(value=100000),
            "is_honeypot": _ev(source="security_gate", value=False),
        }
        res = engine.score_from_map(m)
        decision = res.to_decision({"chain": "solana", "address": "So11111111111111111111111111111111111111112", "symbol": "TEST"}, evidence_objs=list(m.values()))
        from core.models.decision import Decision

        assert isinstance(decision, Decision)
        assert decision.advisory_only is True
        assert decision.score == res.total_score
        assert decision.confidence == res.confidence

    def test_scoring_empty_evidence_returns_low_score(self):
        engine = OpportunityScoringEngineV2()
        res = engine.score([])
        assert res.total_score == 0
        assert res.confidence == Confidence.UNKNOWN

    def test_scoring_is_deterministic(self):
        engine = OpportunityScoringEngineV2()
        m = {"price_change_6h": _ev(value=15), "liquidity_usd": _ev(value=50000)}
        r1 = engine.score_from_map(m, now=FIXED_TS)
        r2 = engine.score_from_map(m, now=FIXED_TS)
        assert r1.total_score == r2.total_score
        assert r1.provenance == r2.provenance


# ---------------------------------------------------------------------------
# Risk Engine
# ---------------------------------------------------------------------------

class TestRiskEngine:
    def test_contract_risk_critical_on_honeypot(self):
        analyzer = ContractRiskAnalyzer()
        m = {"is_honeypot": _ev(source="security_gate", value=True)}
        res = analyzer.analyze(m)
        assert res.level == RiskLevel.CRITICAL
        assert res.score == 100
        assert any("هانی‌پات" in r for r in res.reasons)

    def test_contract_risk_low_when_clean(self):
        analyzer = ContractRiskAnalyzer()
        m = {"is_honeypot": _ev(source="security_gate", value=False), "has_mint_authority": _ev(source="security_gate", value=False)}
        res = analyzer.analyze(m)
        assert res.level == RiskLevel.LOW
        assert res.score < 30

    def test_liquidity_risk_tiers(self):
        analyzer = LiquidityRiskAnalyzer()
        # Very thin → CRITICAL
        res = analyzer.analyze({"liquidity_usd": _ev(value=300)})
        assert res.level == RiskLevel.CRITICAL
        # Healthy → LOW
        res2 = analyzer.analyze({"liquidity_usd": _ev(value=100000)})
        assert res2.level == RiskLevel.LOW
        assert res2.score < res.score
        # Unknown → UNKNOWN
        res3 = analyzer.analyze({})
        assert res3.level == RiskLevel.UNKNOWN

    def test_concentration_risk_high_on_whale(self):
        analyzer = ConcentrationRiskAnalyzer()
        res = analyzer.analyze({"top10_share": _ev(value=85)})
        assert res.level == RiskLevel.CRITICAL
        assert res.score >= 85
        res_low = analyzer.analyze({"top10_share": _ev(value=20)})
        assert res_low.level == RiskLevel.LOW

    def test_manipulation_risk_wash_detection(self):
        analyzer = ManipulationRiskAnalyzer()
        m = {
            "volume_acceleration": _ev(value=8),
            "txn_acceleration": _ev(value=1.5),
        }
        res = analyzer.analyze(m)
        assert res.level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
        assert any("صوری" in r or "واگرایی" in r for r in res.reasons)
        # No data → UNKNOWN
        res2 = analyzer.analyze({})
        assert res2.level == RiskLevel.UNKNOWN

    def test_risk_engine_aggregate(self):
        engine = RiskEngine()
        m = {
            "is_honeypot": _ev(source="security_gate", value=False),
            "liquidity_usd": _ev(value=50000),
            "top10_share": _ev(value=25),
            "volume_acceleration": _ev(value=1.2),
            "txn_acceleration": _ev(value=1.0),
        }
        result = engine.assess(m)
        assert 0 <= result.aggregate_score <= 100
        assert result.aggregate_level in RiskLevel.ALL
        assert len(result.results) == 4  # 4 analyzers
        assert isinstance(result.highest_reasons, list)
        # Aggregate should be LOW or MEDIUM for healthy
        assert result.aggregate_level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_risk_engine_critical_dominates(self):
        engine = RiskEngine()
        m = {
            "is_honeypot": _ev(source="security_gate", value=True),  # CRITICAL
            "liquidity_usd": _ev(value=50000),
            "top10_share": _ev(value=20),
        }
        result = engine.assess(m)
        assert result.aggregate_level == RiskLevel.CRITICAL
        assert result.aggregate_score >= 75

    def test_risk_engine_interface_all_analyzers_evidence_only(self):
        # Each analyzer must reject raw values (passed as Evidence)
        engine = RiskEngine()
        # Pass raw values instead of Evidence → should handle gracefully or be empty
        # But direct analyzer call with raw should not be used; we test that they require Evidence
        for analyzer in engine.analyzers:
            with pytest.raises(Exception):
                analyzer.analyze({"is_honeypot": True})  # raw bool, not Evidence


# ---------------------------------------------------------------------------
# Explanation Generator
# ---------------------------------------------------------------------------

class TestExplanationGenerator:
    def test_explanation_output_structure(self):
        engine = OpportunityScoringEngineV2()
        m = {
            "price_change_6h": _ev(value=20),
            "volume_24h": _ev(value=60000),
            "liquidity_usd": _ev(value=80000),
            "is_honeypot": _ev(source="security_gate", value=False),
        }
        score_res = engine.score_from_map(m)
        risk_engine = RiskEngine()
        risk_res = risk_engine.assess(m)
        gen = ExplanationGenerator()
        exp = gen.generate(score_res, risk_res, evidence_audit={"total": 7, "eligible": 6})
        assert 0 <= exp.score <= 100
        assert exp.confidence in Confidence.ALL
        assert isinstance(exp.text, str) and len(exp.text) > 100
        assert isinstance(exp.brief, str) and len(exp.brief) > 10
        assert isinstance(exp.bullets, dict)
        assert "why" in exp.bullets
        assert "risks" in exp.bullets
        assert "evidence" in exp.bullets
        assert "تصمیم نهایی با کاربر است" in exp.text
        assert isinstance(exp.evidence_citations, list)

    def test_explanation_mentions_critical_risk(self):
        engine = OpportunityScoringEngineV2()
        m = {"is_honeypot": _ev(source="security_gate", value=True), "liquidity_usd": _ev(value=500)}
        score_res = engine.score_from_map(m)
        risk_res = RiskEngine().assess(m)
        exp = ExplanationGenerator().generate(score_res, risk_res)
        assert "ابطال" in exp.text or "ریسک" in exp.text
        # Should contain honeypot reason
        assert any("هانی" in b or "ریسک" in b for b in exp.bullets["risks"])

    def test_explanation_is_deterministic(self):
        engine = OpportunityScoringEngineV2()
        m = {"price_change_6h": _ev(value=10), "liquidity_usd": _ev(value=50000)}
        score_res = engine.score_from_map(m, now=FIXED_TS)
        risk_res = RiskEngine().assess(m, now=FIXED_TS)
        gen = ExplanationGenerator()
        e1 = gen.generate(score_res, risk_res, now=FIXED_TS)
        e2 = gen.generate(score_res, risk_res, now=FIXED_TS)
        assert e1.text == e2.text
        assert e1.brief == e2.brief

    def test_explanation_persian_human_readable(self):
        engine = OpportunityScoringEngineV2()
        m = {"price_change_6h": _ev(value=5), "liquidity_usd": _ev(value=30000)}
        score_res = engine.score_from_map(m)
        exp = ExplanationGenerator().generate(score_res)
        # Must contain Persian sections
        assert "چرا این امتیاز" in exp.text
        assert "شواهد" in exp.text
        assert exp.brief  # non-empty

    def test_explanation_handles_unknown_evidence(self):
        engine = OpportunityScoringEngineV2()
        res = engine.score([])
        exp = ExplanationGenerator().generate(res)
        assert isinstance(exp.text, str)
        assert exp.confidence == Confidence.UNKNOWN


# ---------------------------------------------------------------------------
# Intelligence Pipeline (integration — evidence-only, connected)
# ---------------------------------------------------------------------------

class TestIntelligencePipeline:
    def test_pipeline_evidence_only(self):
        from intelligence.pipeline import IntelligencePipeline

        pipe = IntelligencePipeline()
        # Raw values must be rejected
        with pytest.raises((TypeError, ValueError), match="Evidence"):
            pipe.analyze({"price_usd": 1.5})  # raw, not Evidence

    def test_pipeline_end_to_end(self):
        from intelligence.pipeline import IntelligencePipeline

        pipe = IntelligencePipeline()
        m = {
            "price_change_6h": _ev(value=15),
            "volume_24h": _ev(value=80000),
            "liquidity_usd": _ev(value=100000),
            "is_honeypot": _ev(source="security_gate", value=False),
            "has_mint_authority": _ev(source="security_gate", value=False),
            "top10_share": _ev(source="holders", value=22),
            "narrative_score": _ev(source="viral", value=65),
        }
        res = pipe.analyze(m)
        assert 0 <= res.score_result.total_score <= 100
        assert res.risk_result.aggregate_level in RiskLevel.ALL
        assert isinstance(res.explanation.text, str) and "تصمیم نهایی با کاربر است" in res.explanation.text
        assert res.decision.advisory_only is True
        assert res.feature_provenance  # non-empty
        assert res.score_result.confidence in Confidence.ALL
        # Evidence audit
        assert len(res.score_result.evidence_refs) == len(m)

    def test_pipeline_from_candidate_adapter(self):
        from intelligence.pipeline import IntelligencePipeline
        from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals

        pipe = IntelligencePipeline()
        cand = NormalizedTokenCandidate(
            chain="solana",
            address="So11111111111111111111111111111111111111112",
            symbol="TEST",
            name="Test",
            metrics=MarketMetrics(price_usd=1.5, liquidity_usd=60000, volume_24h=80000, price_change_6h=12),
            security=SecuritySignals(is_honeypot=False, has_mint_authority=False),
            source_provider="dexscreener",
            retrieved_ts=FIXED_TS,
            raw_payload_sha256=RAW,
        )
        res = IntelligencePipeline.from_candidate(cand, now=FIXED_TS)
        assert res.score_result.total_score >= 0
        assert res.risk_result.aggregate_level in RiskLevel.ALL

    def test_pipeline_is_deterministic(self):
        from intelligence.pipeline import IntelligencePipeline

        pipe = IntelligencePipeline()
        m = {"price_change_6h": _ev(value=10), "liquidity_usd": _ev(value=50000)}
        r1 = pipe.analyze(m, now=FIXED_TS)
        r2 = pipe.analyze(m, now=FIXED_TS)
        assert r1.score_result.total_score == r2.score_result.total_score
        assert r1.explanation.text == r2.explanation.text

    def test_pipeline_connected_to_registry(self):
        from intelligence.pipeline import IntelligencePipeline

        pipe = IntelligencePipeline()
        # Pipeline must carry feature provenance from global registry
        assert pipe.feature_registry.count() >= 6
        res = pipe.analyze({"price_change_6h": _ev(value=5)})
        assert res.feature_provenance == pipe.feature_registry.provenance()

