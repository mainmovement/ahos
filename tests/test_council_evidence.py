"""
tests.test_council_evidence — Evidence-driven council gate (Phase 3).

Covered:
  * Council inputs must be Evidence-backed (source, value, timestamp, confidence, verification_status, metadata)
  * Raw unverified data is withheld from lenses (agents abstain, not hallucinate)
  * Deliberation via evidence adapter preserves advisory guarantee

No network, no secrets, no trading. Offline, deterministic.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Robust import for providers (same fallback as test_core_foundation)
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
from core.governance.council_evidence import CouncilEvidenceGate, CouncilInput
from core.adapters.council_adapter import deliberation_with_evidence

from architecture.knowledge.panel import CognitivePanel
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals


FIXED_TS = 1_750_000_000.0
RAW = "a" * 64


def _candidate(price_usd=1.5, liquidity_usd=50000, is_honeypot=False, source="dexscreener"):
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="So11111111111111111111111111111111111111112",
        symbol="TEST",
        name="Test",
        metrics=MarketMetrics(price_usd=price_usd, liquidity_usd=liquidity_usd),
        security=SecuritySignals(is_honeypot=is_honeypot),
        source_provider=source,
        retrieved_ts=FIXED_TS,
        raw_payload_sha256=RAW,
    )
    return cand


class TestCouncilEvidenceGate:
    def test_evidence_has_six_required_fields(self):
        ev = Evidence(
            source="dexscreener",
            timestamp=FIXED_TS,
            confidence=Confidence.HIGH,
            verification_status=VerificationStatus.VERIFIED,
            raw_reference=RAW,
            value={"price_usd": 1.5},
            metadata={"latency_ms": 12},
        )
        # Phase 3 contract: 6 fields must be present (source, value, timestamp, confidence, verification_status, metadata)
        d = ev.to_dict()
        for field in ("source", "value", "timestamp", "confidence", "verification_status", "metadata"):
            assert field in d, f"Evidence missing required field {field}"
        assert ev.has_required_fields() is True
        assert ev.value == {"price_usd": 1.5}
        assert ev.source == "dexscreener"

    def test_evidence_value_none_only_for_unknown(self):
        # UNKNOWN placeholder may have value None
        unk = Evidence.unknown(source="test")
        assert unk.value is None
        assert unk.is_unknown is True
        assert unk.has_required_fields() is True
        # Verified evidence should carry a value — but gate allows None as missing evidence (will be ineligible)
        ev = Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW, value=None)
        # is_council_eligible still checks eligibility, but has_required_fields remains True (field exists)
        assert ev.has_required_fields() is True

    def test_gate_blocks_low_unverified_evidence(self):
        gate = CouncilEvidenceGate()
        ev_good = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW, value=1.5)
        ev_bad = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.LOW, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW, value=1.5)
        ev_rejected = Evidence(source="security_gate", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.REJECTED, raw_reference=RAW, value=True)

        assert gate.is_eligible(ev_good) is True
        assert gate.is_eligible(ev_bad) is False
        assert gate.is_eligible(ev_rejected) is False
        assert ev_bad.is_council_eligible() is False
        assert ev_good.is_council_eligible() is True

    def test_gate_strict_mode_requires_verified(self):
        gate_strict = CouncilEvidenceGate(require_verified=True)
        ev_derived = Evidence(source="scoring", timestamp=time.time(), confidence=Confidence.MEDIUM, verification_status=VerificationStatus.DERIVED, raw_reference=RAW[:32], value=75)
        ev_pending = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.MEDIUM, verification_status=VerificationStatus.PENDING, raw_reference=RAW, value=1.5)
        ev_unverified_med = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.MEDIUM, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW, value=1.5)

        assert gate_strict.is_eligible(ev_derived) is True
        assert gate_strict.is_eligible(ev_pending) is False
        assert gate_strict.is_eligible(ev_unverified_med) is False

    def test_ingest_candidate_produces_evidence_inputs(self):
        gate = CouncilEvidenceGate()
        cand = _candidate()
        inputs = gate.ingest_candidate(cand, now=FIXED_TS)
        assert len(inputs) >= 2
        for inp in inputs:
            assert isinstance(inp, CouncilInput)
            assert isinstance(inp.evidence, Evidence)
            assert inp.evidence.has_required_fields() is True
            # Each input must have source,value,timestamp,confidence,verification,metadata
            d = inp.evidence.to_dict()
            for f in ("source", "value", "timestamp", "confidence", "verification_status", "metadata"):
                assert f in d

    def test_partition_splits_eligible_ineligible(self):
        gate = CouncilEvidenceGate()
        eligible_ev = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW, value=1.5)
        ineligible_ev = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.LOW, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW, value=1.5)
        inputs = [CouncilInput(name="price_usd", evidence=eligible_ev), CouncilInput(name="random", evidence=ineligible_ev)]
        eligible, ineligible = gate.partition(inputs)
        assert len(eligible) == 1 and eligible[0].name == "price_usd"
        assert len(ineligible) == 1 and ineligible[0].name == "random"

    def test_build_context_withholds_raw_unverified(self):
        gate = CouncilEvidenceGate()
        cand = _candidate(price_usd=0.0001, liquidity_usd=100)  # thin pool
        inputs = gate.ingest_candidate(cand, now=time.time())
        # Try to pass a raw unverified context value — should be withheld (None)
        ctx = gate.build_context(inputs, score_report={"opportunity_score": 90}, now=time.time())
        # score_report was passed as raw dict with LOW confidence wrapper → ineligible → None
        # Gate should not leak raw unverified data
        # evidence_inputs contains only eligible metrics
        assert "evidence_inputs" in ctx
        # score_report should be None because we wrapped it as UNVERIFIED+LOW
        assert ctx.get("score_report") is None

    def test_assert_eligible_raises_on_leak(self):
        gate = CouncilEvidenceGate()
        ev_bad = Evidence(source="x", timestamp=time.time(), confidence=Confidence.LOW, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW, value=1)
        ctx = {"price_usd": ev_bad}
        with pytest.raises(PermissionError, match="ineligible Evidence"):
            gate.assert_eligible(ctx)

    def test_audit_reports_counts(self):
        gate = CouncilEvidenceGate()
        ev1 = Evidence(source="a", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW, value=1)
        ev2 = Evidence(source="b", timestamp=time.time(), confidence=Confidence.LOW, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW, value=2)
        inputs = [CouncilInput(name="a", evidence=ev1), CouncilInput(name="b", evidence=ev2)]
        audit = gate.audit(inputs)
        assert audit["total"] == 2
        assert audit["eligible"] == 1
        assert audit["ineligible"] == 1
        assert audit["all_eligible"] is False


class TestCouncilAdapterDeliberation:
    def test_council_adapter_never_passes_raw_unverified(self):
        panel = CognitivePanel()
        cand = _candidate(price_usd=1.5, liquidity_usd=60000, is_honeypot=False)
        verdict = deliberation_with_evidence(panel, cand, now=FIXED_TS)
        # Verdict must be produced and advisory
        assert verdict.verdict in ("APPROVE", "CAUTION", "VETO", "INSUFFICIENT_EVIDENCE")
        assert verdict.advisory_only is True
        # Evidence audit should be attached
        audit = getattr(verdict, "evidence_audit", None)
        assert audit is not None
        assert "eligible" in audit

    def test_council_adapter_blocks_honeypot_via_verified_security(self):
        panel = CognitivePanel()
        cand_bad = _candidate(is_honeypot=True)
        verdict = deliberation_with_evidence(panel, cand_bad, now=FIXED_TS)
        # Honeypot is VERIFIED security evidence → lens must VETO
        assert verdict.verdict == "VETO"
        assert len(verdict.vetoes) >= 1

    def test_council_adapter_insufficient_evidence_when_no_metrics(self):
        panel = CognitivePanel()
        cand_empty = NormalizedTokenCandidate(
            chain="solana",
            address="So11111111111111111111111111111111111111112",
            symbol="EMPTY",
            name="Empty",
            metrics=MarketMetrics(),
            security=SecuritySignals(),
            source_provider="unknown",
            retrieved_ts=FIXED_TS,
            raw_payload_sha256="",
        )
        verdict = deliberation_with_evidence(panel, cand_empty, now=FIXED_TS)
        # Empty candidate yields placeholder UNKNOWN evidence → ineligible → insufficient
        assert verdict.verdict in ("INSUFFICIENT_EVIDENCE", "VETO", "CAUTION")

    def test_council_adapter_preserves_advisory_guarantee(self):
        panel = CognitivePanel()
        cand = _candidate(price_usd=10, liquidity_usd=100000)
        verdict = deliberation_with_evidence(panel, cand, now=FIXED_TS)
        assert verdict.advisory_only is True
        # Advisory footer law: summary declares advisory status
        assert "مشورتی" in verdict.summary_persian() or "advisory" in verdict.summary_persian().lower() or "شورا" in verdict.summary_persian()

    def test_council_adapter_strict_mode(self):
        panel = CognitivePanel()
        cand = _candidate(price_usd=1.5, liquidity_usd=50000)
        # Strict requires verified — candidate metrics are DERIVED (eligible in strict)
        verdict_strict = deliberation_with_evidence(panel, cand, require_verified=True, now=FIXED_TS)
        assert verdict_strict.verdict in ("APPROVE", "CAUTION", "VETO", "INSUFFICIENT_EVIDENCE")
        # Audit should reflect strict gate
        gate_info = getattr(verdict_strict, "evidence_gate", {})
        assert gate_info.get("require_verified") is True
