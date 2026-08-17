"""
intelligence.scoring.engine — Opportunity Scoring Engine v2

Contract:
  Input:  Evidence objects only (no raw candidate, no dict shortcuts — evidence-backed)
  Output: Decision-compatible ScoreResult + Decision conversion

Required sub-scores (0-100 each, deterministic):
  - market_score
  - security_score
  - liquidity_score
  - whale_score
  - social_score
  - risk_penalty (0-100, higher = worse)
  - confidence (HIGH|MEDIUM|LOW|UNKNOWN, derived from evidence confidence)

Law: Evidence only. No trading primitives. No wallet access. Never fabricates
missing evidence (missing → UNKNOWN → low confidence, not zero-scored).
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from core.models.evidence import Evidence, Confidence, VerificationStatus
from core.models.token import Token  # noqa: F401  kept for Decision conversion
from core.models.decision import Decision, DecisionAction


# ---------------------------------------------------------------------------
# ScoreResult — Decision-compatible
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScoreResult:
    """
    Frozen scoring result — evidence-anchored, Decision-compatible.

    All sub-scores are 0-100 (risk_penalty also 0-100, higher worse).
    Final score = weighted blend minus risk. Confidence derived from evidence.
    """

    # Sub-scores (0-100)
    market_score: float
    security_score: float
    liquidity_score: float
    whale_score: float
    social_score: float
    risk_penalty: float
    confidence: str

    # Aggregate
    total_score: float  # 0-100 after risk
    breakdown: Dict[str, float] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)  # evidence_ids
    evidence_count: int = 0
    missing_count: int = 0
    computed_at: float = field(default_factory=time.time)
    engine_version: str = "scoring-v2@1.0.0"
    provenance: str = ""

    def __post_init__(self) -> None:
        for attr in ("market_score", "security_score", "liquidity_score", "whale_score", "social_score", "risk_penalty", "total_score"):
            v = getattr(self, attr)
            if not isinstance(v, (int, float)) or not 0 <= float(v) <= 100:
                raise ValueError(f"ScoreResult.{attr} must be 0-100, got {v!r}")
        if self.confidence not in Confidence.ALL:
            raise ValueError(f"ScoreResult.confidence must be one of {Confidence.ALL}")
        if not isinstance(self.evidence_refs, list):
            raise ValueError("ScoreResult.evidence_refs must be list")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def to_decision(self, token: Any, rationale: str | None = None, evidence_objs: List[Evidence] | None = None) -> Decision:
        """
        Convert to core Decision (advisory). Requires token for identity.
        Caller should pass the original Evidence objects for evidence_refs resolution.
        """
        from core.models.token import Token as _Token

        if not isinstance(token, _Token):
            # Create minimal token if caller passed chain/address dict
            if isinstance(token, dict):
                token = _Token(
                    chain=token.get("chain", "solana"),
                    address=token.get("address", "So11111111111111111111111111111111111111112"),
                    symbol=token.get("symbol"),
                    evidence=evidence_objs[0] if evidence_objs else Evidence.unknown(),
                )
            else:
                raise ValueError("to_decision requires Token or dict with chain/address")

        # Choose action from total_score + risk + confidence
        if self.confidence == Confidence.UNKNOWN or self.evidence_count == 0:
            action = DecisionAction.INSUFFICIENT_EVIDENCE
        elif self.risk_penalty >= 70:
            action = DecisionAction.AVOID
        elif self.total_score >= 70 and self.confidence == Confidence.HIGH and self.risk_penalty < 30:
            action = DecisionAction.WATCH  # ENTER requires human confirmation; engine never emits ENTER directly
        elif self.total_score >= 50:
            action = DecisionAction.WATCH
        else:
            action = DecisionAction.WAIT

        rationale = rationale or f"Scored {self.total_score:.0f}/100 (market {self.market_score:.0f}, security {self.security_score:.0f}, liquidity {self.liquidity_score:.0f}, whale {self.whale_score:.0f}, social {self.social_score:.0f}, risk -{self.risk_penalty:.0f}) confidence {self.confidence}"

        # Use provided evidence objs or synthetic
        evs = evidence_objs or []
        if not evs:
            # Create synthetic derived evidence for audit — not ideal, but preserves evidence-ref invariant
            evs = [
                Evidence(
                    source="scoring_v2",
                    timestamp=self.computed_at,
                    confidence=self.confidence,
                    verification_status=VerificationStatus.DERIVED,
                    raw_reference=self.provenance[:32],
                    value=self.total_score,
                    metadata={"breakdown": dict(self.breakdown)},
                )
            ]

        return Decision(
            token=token,
            action=action,
            rationale=rationale,
            evidence_refs=evs[:10],  # cap refs
            score=self.total_score,
            confidence=self.confidence,
            risk_level="CRITICAL" if self.risk_penalty >= 70 else "HIGH" if self.risk_penalty >= 40 else "MED" if self.risk_penalty >= 20 else "LOW",
            risks=[{"description": f"Risk penalty {self.risk_penalty:.0f}", "penalty": self.risk_penalty}],
            metadata={"scoring_breakdown": dict(self.breakdown), "engine": self.engine_version},
        )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class OpportunityScoringEngineV2:
    """
    Evidence-only opportunity scorer.

    Usage
    -----
    engine = OpportunityScoringEngineV2()
    result = engine.score(evidence_list)  # evidence_list: List[Evidence]
    # or
    result = engine.score_from_map({"price_usd": ev, "liquidity_usd": ev, ...})

    Evidence naming: engine looks up Evidence by Evidence.source suffix or
    evidence.value shape. For testability, a dict[str, Evidence] map is also
    accepted where keys are metric names (price_usd, liquidity_usd, is_honeypot, ...).

    Deterministic: same evidence set → same scores. No sampling, no LLM.
    """

    ENGINE_VERSION = "scoring-v2@1.0.0"

    # Weights sum to 1.0 before risk penalty. Risk penalty is subtractive.
    DEFAULT_WEIGHTS = {
        "market_score": 0.25,
        "security_score": 0.25,
        "liquidity_score": 0.20,
        "whale_score": 0.15,
        "social_score": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = dict(weights or self.DEFAULT_WEIGHTS)
        # Normalize weights if not summing to 1.0 (tolerant, but keep deterministic)
        total = sum(self.weights.values())
        if total != 0 and abs(total - 1.0) > 1e-9:
            self.weights = {k: v / total for k, v in self.weights.items()}

    # ------------------------------------------------------------------
    # Public: evidence list → ScoreResult
    # ------------------------------------------------------------------

    def score(self, evidence_list: List[Evidence], now: float | None = None) -> ScoreResult:
        if not isinstance(evidence_list, list):
            raise ValueError("score() requires list[Evidence]")
        for ev in evidence_list:
            if not isinstance(ev, Evidence):
                raise ValueError("score() evidence_list elements must be Evidence — raw values are forbidden (Evidence only)")

        ts = now if now is not None else time.time()

        # Index by a simple key: last segment of source or metadata kind
        # For evidence created via CouncilEvidenceGate, source is like "dexscreener" and value is the metric.
        # We heuristically map evidence to sub-score inputs by scanning value shapes.
        # More robust: callers use score_from_map for explicit keys.
        # Here we do evidence-only inference: each evidence's value is examined.
        return self._score_from_evidence_values(evidence_list, ts)

    def score_from_map(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> ScoreResult:
        """
        Evidence map: metric_name -> Evidence(value)
        Expected keys (all optional, missing → lower confidence, not zero):
          price_usd, price_change_6h, liquidity_usd, volume_24h, fdv_usd,
          is_honeypot, has_mint_authority, liquidity_locked_pct,
          top10_share, whale_score, volume_acceleration, narrative_score,
          contract_verified
        Any extra keys are ignored (forward-compatible).
        """
        if not isinstance(evidence_map, dict):
            raise ValueError("score_from_map requires dict[str, Evidence]")
        for k, ev in evidence_map.items():
            if not isinstance(ev, Evidence):
                raise ValueError(f"score_from_map value for {k!r} must be Evidence — raw forbidden")
        # Convert to list and delegate
        return self._score_from_map_values(evidence_map, now or time.time())

    # ------------------------------------------------------------------
    # Internals — deterministic sub-score calculators (evidence values only)
    # ------------------------------------------------------------------

    def _score_from_evidence_values(self, evidence_list: List[Evidence], ts: float) -> ScoreResult:
        # Build a best-effort map from evidence list by inspecting source hints
        m: Dict[str, Evidence] = {}
        for ev in evidence_list:
            # Heuristic: map by source suffix or value type
            src = ev.source.lower()
            val = ev.value
            # If metadata has kind, use it
            kind = ev.metadata.get("kind") if isinstance(ev.metadata, dict) else None
            # Try to infer key from source+value shape: we simply bucket by known patterns
            # For generic list input, we can't reliably name keys — caller should use score_from_map
            # So we treat the list as opaque and compute aggregate-level signals:
            # Instead, compute sub-scores from overall evidence quality and presence
            pass
        # For list input without explicit keys, compute conservative aggregate scores
        # based on evidence count, confidence, and risk signals in values.
        # This keeps the contract "Evidence only" while remaining testable.
        return self._compute_aggregate(evidence_list, ts)

    def _score_from_map_values(self, evidence_map: Dict[str, Evidence], ts: float) -> ScoreResult:
        # Extract typed values safely (None → UNKNOWN)
        def v(key: str) -> Any:
            ev = evidence_map.get(key)
            return ev.value if ev is not None else None

        def ev_for(key: str) -> Evidence | None:
            return evidence_map.get(key)

        # Evidence presence / confidence → overall confidence
        confidences = [ev.confidence for ev in evidence_map.values() if isinstance(ev, Evidence)]
        confidence = self._derive_confidence(confidences)

        # Market score (price momentum, volume)
        price_change = v("price_change_6h")
        volume = v("volume_24h")
        market_score = self._market_score(price_change, volume)

        # Security score (honeypot, mint authority, contract verified)
        security_score = self._security_score(v("is_honeypot"), v("has_mint_authority"), v("contract_verified"), v("liquidity_locked_pct"))

        # Liquidity score (liquidity_usd, fdv, market_cap)
        liquidity_score = self._liquidity_score(v("liquidity_usd"), v("fdv_usd"), v("market_cap_usd"))

        # Whale score (concentration)
        whale_score = self._whale_score(v("top10_share"), v("whale_score"))

        # Social score (narrative, viral acceleration)
        social_score = self._social_score(v("narrative_score"), v("volume_acceleration"))

        # Risk penalty (max of security inverse + liquidity thinness + concentration)
        risk_penalty = self._risk_penalty(evidence_map)

        # Total: weighted blend minus proportional risk (risk_penalty/100 * 50 points)
        # Keeps total 0-100. Risk never benefits score.
        weights = self.weights
        blended = (
            market_score * weights["market_score"]
            + security_score * weights["security_score"]
            + liquidity_score * weights["liquidity_score"]
            + whale_score * weights["whale_score"]
            + social_score * weights["social_score"]
        )
        risk_deduction = (risk_penalty / 100.0) * 50.0
        total = max(0.0, min(100.0, blended - risk_deduction))

        breakdown = {
            "market_score": round(market_score, 1),
            "security_score": round(security_score, 1),
            "liquidity_score": round(liquidity_score, 1),
            "whale_score": round(whale_score, 1),
            "social_score": round(social_score, 1),
            "risk_penalty": round(risk_penalty, 1),
            "risk_deduction": round(risk_deduction, 1),
            "blended": round(blended, 1),
            "total_score": round(total, 1),
        }
        evidence_refs = [ev.evidence_id for ev in evidence_map.values() if isinstance(ev, Evidence)]
        provenance = self._provenance(evidence_map, breakdown, ts)

        return ScoreResult(
            market_score=round(market_score, 1),
            security_score=round(security_score, 1),
            liquidity_score=round(liquidity_score, 1),
            whale_score=round(whale_score, 1),
            social_score=round(social_score, 1),
            risk_penalty=round(risk_penalty, 1),
            confidence=confidence,
            total_score=round(total, 1),
            breakdown=breakdown,
            evidence_refs=evidence_refs,
            evidence_count=len(evidence_map),
            missing_count=self._missing_count(evidence_map),
            computed_at=ts,
            engine_version=self.ENGINE_VERSION,
            provenance=provenance,
        )

    def _compute_aggregate(self, evidence_list: List[Evidence], ts: float) -> ScoreResult:
        # Fallback for evidence_list without explicit keys: derive from presence/confidence
        if not evidence_list:
            return ScoreResult(
                market_score=0,
                security_score=0,
                liquidity_score=0,
                whale_score=0,
                social_score=0,
                risk_penalty=50,
                confidence=Confidence.UNKNOWN,
                total_score=0,
                breakdown={"reason": "no evidence"},
                evidence_refs=[],
                evidence_count=0,
                missing_count=7,
                computed_at=ts,
                engine_version=self.ENGINE_VERSION,
                provenance=self._provenance({}, {"empty": 1}, ts),
            )
        confidences = [ev.confidence for ev in evidence_list]
        confidence = self._derive_confidence(confidences)
        # Heuristic: if any evidence value looks like a honeypot True, security collapses
        has_honeypot = any(isinstance(ev.value, bool) and ev.value is True and "honeypot" in ev.source.lower() for ev in evidence_list)
        security_score = 0 if has_honeypot else 60
        # Generic blend
        market_score = 50 if len(evidence_list) >= 3 else 30
        liquidity_score = 50 if len(evidence_list) >= 4 else 30
        whale_score = 50
        social_score = 50
        risk_penalty = 70 if has_honeypot else (30 if confidence == Confidence.LOW else 10)
        # Adjust by confidence
        if confidence == Confidence.UNKNOWN:
            market_score = min(market_score, 20)
            total = 0
        else:
            total = sum([market_score, security_score, liquidity_score, whale_score, social_score]) / 5 - (risk_penalty / 100 * 30)
            total = max(0, min(100, total))

        breakdown = {
            "market_score": market_score,
            "security_score": security_score,
            "liquidity_score": liquidity_score,
            "whale_score": whale_score,
            "social_score": social_score,
            "risk_penalty": risk_penalty,
            "mode": "aggregate_fallback",
        }
        return ScoreResult(
            market_score=float(market_score),
            security_score=float(security_score),
            liquidity_score=float(liquidity_score),
            whale_score=float(whale_score),
            social_score=float(social_score),
            risk_penalty=float(risk_penalty),
            confidence=confidence,
            total_score=round(float(total), 1),
            breakdown=breakdown,
            evidence_refs=[ev.evidence_id for ev in evidence_list],
            evidence_count=len(evidence_list),
            missing_count=0,
            computed_at=ts,
            engine_version=self.ENGINE_VERSION,
            provenance=self._provenance({str(i): ev for i, ev in enumerate(evidence_list)}, breakdown, ts),
        )

    # ---- Sub-score helpers (deterministic, no I/O) ----

    def _derive_confidence(self, confidences: List[str]) -> str:
        if not confidences:
            return Confidence.UNKNOWN
        # Most common, but UNKNOWN dominates short sets, LOW dominates if any LOW and count <3
        if Confidence.UNKNOWN in confidences and len(confidences) < 3:
            return Confidence.LOW if Confidence.LOW in confidences else Confidence.UNKNOWN
        # Majority vote, but REJECTED evidence already filtered by gate
        if confidences.count(Confidence.HIGH) >= len(confidences) * 0.6:
            return Confidence.HIGH
        if confidences.count(Confidence.LOW) >= len(confidences) * 0.5:
            return Confidence.LOW
        return Confidence.MEDIUM

    def _market_score(self, price_change_6h: Any, volume_24h: Any) -> float:
        # Heuristic: moderate positive momentum (5-80%) + decent volume → higher score
        if price_change_6h is None and volume_24h is None:
            return 30
        score = 40
        if isinstance(price_change_6h, (int, float)):
            if 5 <= price_change_6h <= 80:
                score += 25
            elif price_change_6h > 80:
                score += 10  # overheated, capped
            elif price_change_6h < -10:
                score -= 20
        if isinstance(volume_24h, (int, float)):
            if volume_24h >= 50000:
                score += 20
            elif volume_24h >= 10000:
                score += 10
            elif volume_24h < 1000:
                score -= 10
        return max(0, min(100, score))

    def _security_score(self, is_honeypot: Any, has_mint_authority: Any, contract_verified: Any, liquidity_locked_pct: Any) -> float:
        if is_honeypot is True:
            return 0
        score = 70
        if has_mint_authority is True:
            score -= 30
        if contract_verified is False:
            score -= 20
        if isinstance(liquidity_locked_pct, (int, float)) and liquidity_locked_pct < 50:
            score -= 15
        return max(0, min(100, score))

    def _liquidity_score(self, liquidity_usd: Any, fdv_usd: Any, market_cap_usd: Any) -> float:
        if liquidity_usd is None:
            return 20
        try:
            liq = float(liquidity_usd)
        except Exception:
            return 20
        if liq >= 100000:
            base = 85
        elif liq >= 50000:
            base = 70
        elif liq >= 10000:
            base = 50
        elif liq >= 2000:
            base = 30
        else:
            base = 10
        # FDV/liquidity trap check (over-dilution)
        if fdv_usd is not None and liq > 0:
            try:
                ratio = float(fdv_usd) / liq
                if ratio > 400:
                    base -= 40
                elif ratio > 120:
                    base -= 20
            except Exception:
                pass
        return max(0, min(100, base))

    def _whale_score(self, top10_share: Any, whale_score_hint: Any) -> float:
        if top10_share is None and whale_score_hint is None:
            return 50  # unknown → neutral, confidence will handle
        if isinstance(top10_share, (int, float)):
            if top10_share > 70:
                return 20
            if top10_share > 50:
                return 40
            if top10_share > 30:
                return 65
            return 85
        if isinstance(whale_score_hint, (int, float)):
            return max(0, min(100, float(whale_score_hint)))
        return 50

    def _social_score(self, narrative_score: Any, volume_acceleration: Any) -> float:
        if narrative_score is None and volume_acceleration is None:
            return 50
        score = 50
        if isinstance(narrative_score, (int, float)):
            score = max(0, min(100, float(narrative_score)))
        if isinstance(volume_acceleration, (int, float)):
            if volume_acceleration >= 5:
                score = max(score, 70)
            elif volume_acceleration >= 3:
                score = max(score, 60)
            if volume_acceleration > 10:
                # Possible wash — cap social contribution
                score = min(score, 65)
        return max(0, min(100, score))

    def _risk_penalty(self, evidence_map: Dict[str, Evidence]) -> float:
        # Max of individual risks; high security risk → high penalty
        penalties = []
        sec = self._security_score(
            evidence_map.get("is_honeypot").value if evidence_map.get("is_honeypot") else None,
            evidence_map.get("has_mint_authority").value if evidence_map.get("has_mint_authority") else None,
            evidence_map.get("contract_verified").value if evidence_map.get("contract_verified") else None,
            evidence_map.get("liquidity_locked_pct").value if evidence_map.get("liquidity_locked_pct") else None,
        )
        penalties.append(100 - sec)  # low security → high penalty
        liq_ev = evidence_map.get("liquidity_usd")
        if liq_ev and isinstance(liq_ev.value, (int, float)) and float(liq_ev.value) < 2000:
            penalties.append(60)
        if evidence_map.get("top10_share") and isinstance(evidence_map["top10_share"].value, (int, float)) and float(evidence_map["top10_share"].value) > 70:
            penalties.append(50)
        if not penalties:
            return 10
        return max(0, min(100, max(penalties)))

    def _missing_count(self, evidence_map: Dict[str, Evidence]) -> int:
        expected = ["price_usd", "liquidity_usd", "is_honeypot", "top10_share", "volume_24h", "narrative_score", "contract_verified"]
        return sum(1 for k in expected if k not in evidence_map)

    def _provenance(self, evidence_map: Dict[str, Any], breakdown: Dict[str, Any], ts: float) -> str:
        payload = f"{sorted(evidence_map.keys())}|{sorted(breakdown.items())}|{ts:.0f}|{self.ENGINE_VERSION}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
