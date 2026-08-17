"""
intelligence.pipeline — Evidence-Driven Intelligence Pipeline (Phase 4 integration)

Connects Feature Registry → Scoring V2 → Risk Engine → Explanations
using only Evidence objects, wired to existing architecture via core adapters.

No raw values, no trading primitives, no isolated modules.

Usage
-----
from intelligence.pipeline import IntelligencePipeline
from core.models.evidence import Evidence

pipeline = IntelligencePipeline()
result = pipeline.analyze(evidence_map)  # evidence_map: dict[str, Evidence]
# result.score_result, result.risk_result, result.explanation, result.decision

The pipeline is pure/deterministic and can be called from:
  - architecture/pipeline/orchestrator (via adapter)
  - core/adapters/council_adapter (for panel augmentation)
  - telegram_ai/service (for Persian explanations)
  - tests / research notebooks

Evidence contract is enforced at entry: every value must be Evidence
carrying source, value, timestamp, confidence, verification_status, metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.models.evidence import Evidence, Confidence
from core.models.token import Token

from .features.registry import FeatureRegistry, get_global_registry
from .scoring.engine import OpportunityScoringEngineV2, ScoreResult
from .risk.engine import RiskEngine, RiskEngineResult
from .explanations.generator import ExplanationGenerator, Explanation
from core.models.decision import Decision


@dataclass(frozen=True)
class IntelligenceResult:
    """
    Combined intelligence output — evidence-anchored, decision-compatible.
    """

    score_result: ScoreResult
    risk_result: RiskEngineResult
    explanation: Explanation
    decision: Decision
    feature_provenance: str
    pipeline_version: str = "intelligence-pipeline@1.0.0"
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_result": self.score_result.to_dict(),
            "risk_result": self.risk_result.to_dict(),
            "explanation": self.explanation.to_dict(),
            "decision": self.decision.to_dict(),
            "feature_provenance": self.feature_provenance,
            "pipeline_version": self.pipeline_version,
            "computed_at": self.computed_at,
        }


class IntelligencePipeline:
    """
    Evidence-only intelligence pipeline — integrates all sub-engines.

    Design
    ------
    * Consumes only `dict[str, Evidence]` (or list[Evidence] via helper).
    * Validates that every feature's required evidence is present or marks UNKNOWN.
    * Scoring and Risk are computed from the same evidence_map (no second fetch).
    * Explanation is generated from ScoreResult + RiskEngineResult + evidence audit.
    * Decision is derived from ScoreResult (advisory_only=True, never executes).
    """

    PIPELINE_VERSION = "intelligence-pipeline@1.0.0"

    def __init__(
        self,
        feature_registry: Optional[FeatureRegistry] = None,
        scoring_engine: Optional[OpportunityScoringEngineV2] = None,
        risk_engine: Optional[RiskEngine] = None,
        explanation_generator: Optional[ExplanationGenerator] = None,
    ):
        self.feature_registry = feature_registry or get_global_registry()
        self.scoring_engine = scoring_engine or OpportunityScoringEngineV2()
        self.risk_engine = risk_engine or RiskEngine()
        self.explanation_generator = explanation_generator or ExplanationGenerator()

    # ------------------------------------------------------------------
    # Main entry — evidence map
    # ------------------------------------------------------------------

    def analyze(
        self,
        evidence_map: Dict[str, Evidence],
        token: Token | Dict[str, Any] | None = None,
        now: float | None = None,
    ) -> IntelligenceResult:
        """
        Analyze an evidence map.

        Parameters
        ----------
        evidence_map: dict[str, Evidence] — evidence-only (raw values raise ValueError)
        token: Token or dict {chain, address, symbol} for Decision identity; if None, synthetic token is used
        now: epoch for deterministic tests
        """
        if not isinstance(evidence_map, dict):
            raise ValueError("IntelligencePipeline.analyze requires dict[str, Evidence] — evidence only")
        for k, v in evidence_map.items():
            if not isinstance(v, Evidence):
                raise TypeError(f"Evidence only: evidence_map[{k!r}] must be Evidence, got {type(v).__name__}")
            if not v.has_required_fields():
                raise ValueError(f"Evidence for {k!r} missing required fields (source, value, timestamp, confidence, verification_status, metadata)")

        ts = now if now is not None else time.time()

        # 1. Feature provenance (audit)
        feature_provenance = self.feature_registry.provenance()

        # 2. Scoring (evidence-only)
        score_result = self.scoring_engine.score_from_map(evidence_map, now=ts)

        # 3. Risk (evidence-only, same map)
        risk_result = self.risk_engine.assess(evidence_map, now=ts)

        # 4. Evidence audit for explanation (eligible vs total)
        audit = {
            "total": len(evidence_map),
            "eligible": len([ev for ev in evidence_map.values() if ev.is_council_eligible()]),
        }

        # 5. Explanation (deterministic Persian)
        explanation = self.explanation_generator.generate(score_result, risk_result, evidence_audit=audit, now=ts)

        # 6. Decision (advisory)
        # Build token if not supplied — synthetic but evidence-anchored
        if token is None:
            # Use first evidence's source timestamp as token discovery time if available
            first_ev = next(iter(evidence_map.values()), None)
            ts_token = first_ev.timestamp if first_ev else ts
            token = Token(
                chain="solana",
                address="So11111111111111111111111111111111111111112",
                symbol="SYNTH",
                evidence=first_ev or Evidence(
                    source="intelligence_pipeline",
                    timestamp=ts,
                    confidence=Confidence.UNKNOWN,
                    verification_status="UNKNOWN",
                    raw_reference="",
                    value=None,
                    metadata={},
                ) if first_ev else __import__("core.models.evidence", fromlist=["Evidence"]).Evidence.unknown(),
                first_seen_ts=ts_token,
            )
            # Synthetic token with unknown evidence is allowed for tests; real pipeline passes real token
            # To avoid UNKNOWN placeholder rejection, use evidence from map if present
            if first_ev and first_ev.value is not None:
                # Already have evidence
                pass
        decision = score_result.to_decision(token, rationale=explanation.brief, evidence_objs=list(evidence_map.values()))

        return IntelligenceResult(
            score_result=score_result,
            risk_result=risk_result,
            explanation=explanation,
            decision=decision,
            feature_provenance=feature_provenance,
            pipeline_version=self.PIPELINE_VERSION,
            computed_at=ts,
        )

    # ------------------------------------------------------------------
    # Helper — list[Evidence] → map (for callers with list form)
    # ------------------------------------------------------------------

    def analyze_list(
        self,
        evidence_list: List[Evidence],
        token: Token | Dict[str, Any] | None = None,
        now: float | None = None,
    ) -> IntelligenceResult:
        """
        List form: evidence_list → evidence_map via source/value heuristics.
        Prefer analyze(evidence_map) for explicit keys; this helper is for
        discovery_adapter-style lists.
        """
        if not isinstance(evidence_list, list):
            raise ValueError("analyze_list requires list[Evidence]")
        # Map by source last segment or metadata name if present
        m: Dict[str, Evidence] = {}
        for ev in evidence_list:
            if not isinstance(ev, Evidence):
                raise TypeError(f"analyze_list elements must be Evidence, got {type(ev).__name__}")
            key = ev.metadata.get("name") or ev.metadata.get("metric") or ev.source.split(":")[-1] or ev.source
            # Deduplicate by keeping latest timestamp
            if key in m and m[key].timestamp > ev.timestamp:
                continue
            m[key] = ev
        return self.analyze(m, token=token, now=now)

    # ------------------------------------------------------------------
    # Wiring helper — from existing architecture candidate/score context
    # ------------------------------------------------------------------

    @classmethod
    def from_candidate(
        cls,
        candidate: Any,
        token: Token | Dict[str, Any] | None = None,
        now: float | None = None,
    ) -> IntelligenceResult:
        """
        Adapter: NormalizedTokenCandidate → Evidence map → intelligence result.
        Uses core.adapters.discovery_adapter.candidate_to_observation internally
        would be raw; instead we build evidence_map explicitly evidence-only.
        """
        from core.governance.council_evidence import CouncilEvidenceGate

        gate = CouncilEvidenceGate()
        inputs = gate.ingest_candidate(candidate, now=now)
        # inputs are CouncilInput(evidence) — convert to map
        evidence_map: Dict[str, Evidence] = {}
        for inp in inputs:
            # Gate already ensures is_council_eligible; we keep all for scoring
            evidence_map[inp.name] = inp.evidence
        # Also include security signals if any were withheld but still needed for risk
        # The gate's eligible filter is for council, not for risk — risk should see all
        # so we include both eligible and ineligible here for full risk picture
        # (risk analyzers handle UNKNOWN gracefully)
        pipeline = cls()
        return pipeline.analyze(evidence_map, token=token, now=now)
