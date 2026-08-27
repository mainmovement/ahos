#!/usr/bin/env python3
"""AHOS Evidence-Based Opportunity Scoring Engine (Section VIII / Phase 4).

Strict Stage Separation:
  DATA -> SIGNALS -> EVIDENCE -> FEATURES -> RISK -> OPPORTUNITY -> CONFIDENCE -> INVALIDATION

Phase 4: this module is the compatibility facade over the integrated intelligence
engine. `OpportunityScorer.evaluate` still accepts a normalized candidate so every
existing caller keeps working, but the candidate is converted to Evidence at the
boundary and every calculation consumes Evidence objects only.

Principles:
  - Deterministic decision floor: 100% computable without any AI API keys.
  - Provable explainability: Provides structured answers to all 8 canonical questions.
  - Transparent penalties for missing / UNKNOWN data.
  - Non-trading: produces Opportunity Intelligence, NEVER automated trade orders.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any

from ..risk.engine import RiskFinding as RiskItem


@dataclass
class EvidenceItem:
    key: str
    description: str
    value: Any
    provider: str
    timestamp: float
    freshness_seconds: float
    status: str                                  # VERIFIED | DERIVED | UNKNOWN | STALE


@dataclass
class InvalidationCondition:
    condition_id: str
    trigger_description: str
    threshold: str
    is_triggered: bool = False


@dataclass
class OpportunityScoreReport:
    token_address: str
    token_chain: str
    token_symbol: str
    token_name: str
    opportunity_score: float                     # 0.0 to 100.0
    confidence_level: str                        # HIGH | MED | LOW
    risk_level: str                              # LOW | MED | HIGH | CRITICAL
    positive_reasons: list[str]
    risk_deductions: list[RiskItem]
    evidence_items: list[EvidenceItem]
    missing_unknowns: list[str]
    invalidation_conditions: list[InvalidationCondition]
    score_breakdown: dict[str, float]
    computed_at_ts: float = field(default_factory=time.time)
    provenance_sha256: str = ""
    source_provider: str = "UNKNOWN"     # which provider supplied the candidate
    intel_evidence_items: list[dict] = field(default_factory=list)  # full intel evidence (beyond the 4 canonical items)
    # P0 security authority (set by the pipeline's SecurityGate BEFORE ranking).
    # None means the gate was not applied (e.g. direct scorer.evaluate calls); the
    # production pipeline always sets these. Only "PASS" may become a positive opportunity.
    security_disposition: str | None = None   # PASS | PASS_WITH_UNKNOWN | SECURITY_VETO
    recommendation_cap: str | None = None      # PASS | WATCH | AVOID

    def is_security_cleared(self) -> bool:
        """True only when the security gate explicitly PASSED this candidate."""
        return self.security_disposition == "PASS"

    def answer_why_scored(self) -> str:
        return "\n".join(f"+ {r}" for r in self.positive_reasons) if self.positive_reasons else "امتیاز پایه حداقلی"

    def answer_evidence(self) -> list[dict]:
        return [asdict(e) for e in self.evidence_items]

    def answer_intel_evidence(self) -> list[dict]:
        """Full intel-surface evidence (virality, whales, security-derived,
        ...) with provider provenance — beyond the frozen 4-item
        `answer_evidence()` contract."""
        return [dict(e) for e in self.intel_evidence_items]

    def answer_missing(self) -> list[str]:
        return self.missing_unknowns

    def answer_risks(self) -> list[dict]:
        return [asdict(r) for r in self.risk_deductions]

    def answer_invalidation(self) -> list[dict]:
        return [asdict(c) for c in self.invalidation_conditions]


class OpportunityScorer:
    """Deterministic opportunity evaluation facade.

    Public `evaluate(candidate)` is preserved for the existing pipeline, alerts,
    Telegram cards, and tests. Internally it materializes Evidence and delegates
    to `IntelligenceEngine` — no scoring math runs on raw candidate fields.
    """

    def __init__(self, intelligence=None):
        self._intelligence = intelligence

    @property
    def intelligence(self):
        if self._intelligence is None:
            from ..intelligence.engine import IntelligenceEngine
            self._intelligence = IntelligenceEngine()
        return self._intelligence

    @intelligence.setter
    def intelligence(self, value) -> None:
        self._intelligence = value

    @staticmethod
    def attach_virality(bundle, candidate, now: float):
        """Compute the candidate's ViralitySignal and extend the evidence
        bundle with the canonical intel.viral atoms (provider provenance).

        Honesty: `evidence_from_virality` marks is_paid_promotion /
        wash_suspected DERIVED only when the underlying data (boost spend /
        txn counts) was actually observed; otherwise the atom is UNKNOWN with
        value None — the raw signal's False-on-missing default never leaks
        into the evidence bundle as a fabricated negative.
        """
        from ..intel.viral import ViralityTracker
        from ..intelligence.adapters import evidence_from_virality

        signal = ViralityTracker().analyze(
            candidate,
            boost_amount=getattr(candidate, "boost_amount", None),
            now=now,
        )
        boost_seen = getattr(candidate, "boost_amount", None) is not None
        metrics = getattr(candidate, "metrics", None)
        txns_seen = any(
            getattr(metrics, f, None) is not None
            for f in ("txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells"))
        return bundle.extended(
            evidence_from_virality(signal, boost_seen=boost_seen, txns_seen=txns_seen))

    def evaluate(self, candidate: Any,
                 previous_candidate: Any | None = None,
                 now: float | None = None) -> OpportunityScoreReport:
        from ..intelligence.evidence import materialize_evidence

        ts = time.time() if now is None else now
        bundle = materialize_evidence(candidate, now=ts)
        bundle = self.attach_virality(bundle, candidate, ts)
        report = self.intelligence.evaluate(bundle)
        report = self.from_intelligence(report)
        # Stamp the candidate's discovery provider so calibration can segment
        # by provider (Q8). The report itself does not otherwise know it.
        report.source_provider = str(getattr(candidate, "source_provider", "") or "")
        return report

    @staticmethod
    def from_intelligence(report) -> OpportunityScoreReport:
        """Project an IntelligenceReport onto the historical score-report contract."""
        ident = report.evidence.identity
        evidence_items = [
            EvidenceItem(
                key=e.key,
                description=e.description,
                value=e.value,
                provider=e.provider,
                timestamp=e.timestamp,
                freshness_seconds=e.freshness_seconds,
                status=e.status,
            )
            for e in report.explanation.report_evidence
        ]
        # Full intel-surface evidence (virality, whale, security-derived, ...):
        # everything in the bundle beyond the frozen 4 canonical report items,
        # with provider provenance. The legacy `evidence_items` contract is
        # untouched (backward compatible; ledger known-field counts unchanged).
        canonical_keys = {e.key for e in evidence_items}
        intel_evidence_items = [
            {
                "key": e.key,
                "description": e.description,
                "value": e.value,
                "provider": e.provider,
                "status": e.status,
                "source_field": e.source_field,
            }
            for e in report.evidence.all_items()
            if e.key not in canonical_keys
        ]
        return OpportunityScoreReport(
            token_address=ident.address,
            token_chain=ident.chain,
            token_symbol=ident.symbol,
            token_name=ident.name,
            opportunity_score=report.score.opportunity_score,
            confidence_level=report.score.confidence_level,
            risk_level=report.score.risk_level,
            positive_reasons=list(report.explanation.positive_reasons),
            risk_deductions=list(report.risk.findings),
            evidence_items=evidence_items,
            missing_unknowns=list(report.explanation.missing_unknowns),
            invalidation_conditions=list(report.explanation.invalidation_conditions),
            score_breakdown=dict(report.score.components),
            computed_at_ts=report.evidence.evaluated_at,
            provenance_sha256=report.evidence.provenance_sha256(),
            intel_evidence_items=intel_evidence_items,
        )
