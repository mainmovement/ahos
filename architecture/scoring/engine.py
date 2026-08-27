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

    @staticmethod
    def attach_narrative(
        bundle,
        candidate,
        now: float,
        *,
        items=None,
        feeds_ok: list | None = None,
        feeds_failed: list | None = None,
        collector=None,
        fetch: bool | None = None,
    ):
        """Attach narrative (RSS) evidence atoms — R-69 / P0-3 feed-through.

        Network law
        -----------
        Default for `OpportunityScorer.evaluate` is *no* live fetch
        (`AHOS_NARRATIVE_FETCH` unset/0) so unit tests stay offline and fast.
        The production pipeline orchestrator prefetches once per cycle and
        passes `items` (+ feed provenance). Set `AHOS_NARRATIVE_FETCH=1` to
        allow evaluate() itself to hit RSS.

        Honesty: unreachable / disabled feeds → UNKNOWN label, never NEUTRAL
        fabricated from silence. Narrative never overrides security vetoes.
        """
        import os

        from ..intel.news import NewsCollector, NarrativeSignal
        from ..intelligence.adapters import evidence_from_narrative

        if fetch is None:
            fetch = os.environ.get("AHOS_NARRATIVE_FETCH", "0").strip() == "1"

        collector = collector or NewsCollector()
        symbol = str(getattr(candidate, "symbol", "") or "").strip()
        name = str(getattr(candidate, "name", "") or "").strip()
        keywords = [k for k in (symbol, name) if k and len(k) >= 2]
        subject = symbol or name or "MARKET"

        if items is not None:
            signal = collector.analyze(
                subject=subject,
                keywords=keywords or None,
                items=list(items),
                now=now,
                feeds_ok=feeds_ok,
                feeds_failed=feeds_failed,
            )
        elif fetch:
            signal = collector.analyze(
                subject=subject,
                keywords=keywords or None,
                now=now,
            )
        else:
            signal = NarrativeSignal(
                subject=subject,
                sentiment=0.0,
                label="UNKNOWN",
                mention_count=0,
                high_impact_count=0,
                computed_ts=now,
                error_state={
                    "kind": "narrative_fetch_disabled",
                    "detail": "AHOS_NARRATIVE_FETCH!=1 and no prefetched items",
                },
            )
        return bundle.extended(evidence_from_narrative(signal))

    @staticmethod
    def attach_market_structure(bundle, candidate, now: float):
        """Attach deterministic market-structure evidence (Lane B intel)."""
        from ..intel.market_structure import MarketStructureAnalyzer
        from ..intelligence.adapters import evidence_from_market_structure

        signal = MarketStructureAnalyzer().analyze(candidate, now=now)
        return bundle.extended(evidence_from_market_structure(signal))

    @staticmethod
    def attach_tokenomics(bundle, candidate, now: float):
        """Attach tokenomics evidence from observed supply/authority fields."""
        from ..intel.tokenomics import TokenomicsAnalyzer
        from ..intelligence.adapters import evidence_from_tokenomics

        signal = TokenomicsAnalyzer().analyze(candidate, now=now)
        return bundle.extended(evidence_from_tokenomics(signal))

    @staticmethod
    def attach_catalysts(bundle, candidate, now: float, *, news_items=None):
        """Attach provenance-aware catalyst catalog (deterministic heuristics)."""
        from ..intel.catalyst import CatalystDetector
        from ..intelligence.adapters import evidence_from_catalysts

        report = CatalystDetector().detect(
            candidate, news_items=news_items, now=now)
        return bundle.extended(evidence_from_catalysts(report))

    def evaluate(self, candidate: Any,
                 previous_candidate: Any | None = None,
                 now: float | None = None) -> OpportunityScoreReport:
        from ..intelligence.evidence import materialize_evidence

        ts = time.time() if now is None else now
        bundle = materialize_evidence(candidate, now=ts)
        bundle = self.attach_virality(bundle, candidate, ts)
        bundle = self.attach_narrative(bundle, candidate, ts)
        bundle = self.attach_market_structure(bundle, candidate, ts)
        bundle = self.attach_tokenomics(bundle, candidate, ts)
        bundle = self.attach_catalysts(bundle, candidate, ts)
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
