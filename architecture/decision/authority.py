#!/usr/bin/env python3
"""Canonical Decision Authority — the single Lane B decision brain.

Wraps `DecisionAdvisor` (do not create a second brain). Pipeline:

    IDENTITY
      → EVIDENCE INTEGRITY / FRESHNESS
      → SECURITY
      → LIQUIDITY / EXITABILITY
      → DETERMINISTIC OPPORTUNITY SCORING
      → RISK
      → CONFIDENCE  (independent of opportunity score)
      → OPTIONAL AI CHALLENGE (downgrade / abstain only)
      → CANONICAL DECISION

Consumers (Web, Telegram, Alerts, Paper, AI Council, ranking, APIs) may
present or consume this object. They may not mint a competing recommendation.

AI is advisory. It cannot override invalid identity, security REJECT /
INCOMPLETE / STALE, or fabricate evidence. NO_TRADE is a valid outcome.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from architecture.ai.council_live import CouncilVerdict
from architecture.decision.advisor import ADVISOR_VERSION, Advice, DecisionAdvisor
from architecture.identity.gates import (
    identity_allows_positive_decision,
    pool_liquidity_claims_allowed,
    token_monitoring_allowed,
)
from architecture.identity.resolution import resolve_identity
from architecture.identity.types import IdentityResolution, IdentitySource
from architecture.intel.exitability import ExitabilityAnalyzer
from architecture.providers.contracts import NormalizedTokenCandidate
from architecture.scoring.engine import OpportunityScoreReport
from architecture.security.gate import (
    POLICY_VERSION as SECURITY_POLICY_VERSION,
    SecurityOverlay,
    SecurityState,
    evaluate_security_from_candidate,
    security_allows_positive_eligibility,
)

AUTHORITY_VERSION = "AHOS-CANONICAL-DECISION-v1"


class CanonicalOutcome(str, Enum):
    """Public decision vocabulary. Maps advisor ENTER/WAIT/AVOID; does not
    replace those actions inside DecisionAdvisor."""

    BUY = "BUY"
    WATCH = "WATCH"
    SKIP = "SKIP"
    REJECT = "REJECT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HIGH_RISK = "HIGH_RISK"
    MONITOR_ONLY = "MONITOR_ONLY"
    NO_TRADE = "NO_TRADE"


POSITIVE_OUTCOMES = frozenset({CanonicalOutcome.BUY})


@dataclass(frozen=True)
class AiChallengeRecord:
    challenged: bool
    original_advisor_action: str | None
    resulting_advisor_action: str | None
    council_stance: str | None
    panel_verdict: str | None
    effect: str  # NONE | DOWNGRADE | ABSTAIN
    upgrade_blocked: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenged": self.challenged,
            "original_advisor_action": self.original_advisor_action,
            "resulting_advisor_action": self.resulting_advisor_action,
            "council_stance": self.council_stance,
            "panel_verdict": self.panel_verdict,
            "effect": self.effect,
            "upgrade_blocked": self.upgrade_blocked,
            "reason": self.reason,
        }


@dataclass
class CanonicalDecision:
    """The one canonical decision object downstream consumers must read."""

    outcome: CanonicalOutcome
    advisor_action: str
    conviction: str
    identity_state: str
    security_state: str
    opportunity_score: float | None
    confidence_level: str
    risk_level: str
    primary_reason: str
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    hard_vetoes: list[str] = field(default_factory=list)
    ai_challenge: AiChallengeRecord | None = None
    advice: Advice | None = None
    security: SecurityOverlay | None = None
    identity: IdentityResolution | None = None
    monitoring_only: bool = False
    suggested_size_usd: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    computed_ts: float = field(default_factory=time.time)
    version: str = AUTHORITY_VERSION

    @property
    def is_positive(self) -> bool:
        """BUY only. WATCH / MONITOR_ONLY / NO_TRADE are not positive recs."""
        return (
            self.outcome in POSITIVE_OUTCOMES
            and self.advisor_action == "ENTER"
            and not self.hard_vetoes
            and not self.monitoring_only
        )

    @property
    def alerts_allowed(self) -> bool:
        return self.is_positive

    @property
    def paper_allowed(self) -> bool:
        return self.is_positive

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "advisor_action": self.advisor_action,
            "conviction": self.conviction,
            "identity_state": self.identity_state,
            "security_state": self.security_state,
            "opportunity_score": self.opportunity_score,
            "confidence_level": self.confidence_level,
            "risk_level": self.risk_level,
            "primary_reason": self.primary_reason,
            "reasons": list(self.reasons),
            "risks": list(self.risks),
            "unknowns": list(self.unknowns),
            "hard_vetoes": list(self.hard_vetoes),
            "ai_challenge": self.ai_challenge.to_dict() if self.ai_challenge else None,
            "monitoring_only": self.monitoring_only,
            "is_positive": self.is_positive,
            "alerts_allowed": self.alerts_allowed,
            "paper_allowed": self.paper_allowed,
            "suggested_size_usd": self.suggested_size_usd,
            "provenance": dict(self.provenance),
            "computed_ts": self.computed_ts,
            "version": self.version,
        }


def identity_from_candidate(
    candidate: NormalizedTokenCandidate,
    now: float | None = None,
) -> IdentityResolution:
    """Fail-closed identity bind from a collected candidate.

    A single market provider is insufficient (UNRESOLVED). Orchestrator tests
    that need VERIFIED identity inject a resolver or a fixture.
    """
    sources: list[IdentitySource] = []
    if candidate.source_provider and candidate.address:
        sources.append(
            IdentitySource(
                provider=str(candidate.source_provider),
                chain=candidate.chain,
                address=candidate.address,
                retrieved_ts=candidate.retrieved_ts,
                kind="market",
            )
        )
    return resolve_identity(
        chain=candidate.chain,
        address=candidate.address,
        symbol=candidate.symbol,
        name=candidate.name,
        sources=sources,
        pool_dex=candidate.dex_id,
        pool_address=candidate.pair_address,
        pool_base_token=candidate.address if candidate.pair_address else None,
        now=now,
    )


def _identity_label(identity: IdentityResolution | None) -> str:
    if identity is None:
        return "MISSING"
    return identity.token.state.value


def _map_gate_failure(
    *,
    identity: IdentityResolution | None,
    overlay: SecurityOverlay | None,
    advice: Advice,
    score_report: OpportunityScoreReport,
) -> CanonicalOutcome | None:
    """Return a hard-gate outcome, or None if gates did not block."""
    ident = _identity_label(identity)
    if identity is None or not identity_allows_positive_decision(identity):
        if ident in ("INVALID", "CONFLICT", "UNSUPPORTED"):
            return CanonicalOutcome.REJECT
        if ident == "STALE":
            return CanonicalOutcome.NO_TRADE
        return CanonicalOutcome.INSUFFICIENT_EVIDENCE

    state = overlay.state if overlay is not None else None
    if overlay is None or not security_allows_positive_eligibility(overlay):
        if state == SecurityState.REJECT:
            return CanonicalOutcome.REJECT
        if state == SecurityState.STALE:
            return CanonicalOutcome.NO_TRADE
        return CanonicalOutcome.INSUFFICIENT_EVIDENCE

    if advice.action == "AVOID" and advice.hard_vetoes:
        if score_report.risk_level == "CRITICAL":
            return CanonicalOutcome.HIGH_RISK
        return CanonicalOutcome.REJECT
    return None


def _map_post_gate(
    advice: Advice,
    score_report: OpportunityScoreReport,
    *,
    monitoring_only: bool,
) -> CanonicalOutcome:
    if monitoring_only:
        return CanonicalOutcome.MONITOR_ONLY
    if advice.action == "ENTER":
        return CanonicalOutcome.BUY
    if advice.action == "WAIT":
        if score_report.confidence_level == "LOW" or (
            score_report.missing_unknowns and advice.action == "WAIT"
            and any("نقدینگی نامعلوم" in (r or "") or "liquidity" in (r or "").lower()
                    for r in advice.reasons)
        ):
            if any("نقدینگی نامعلوم" in (r or "") for r in advice.reasons):
                return CanonicalOutcome.INSUFFICIENT_EVIDENCE
        return CanonicalOutcome.WATCH
    if score_report.risk_level == "CRITICAL":
        return CanonicalOutcome.HIGH_RISK
    if (advice.deterministic_score or 0) < 40.0:
        return CanonicalOutcome.SKIP
    return CanonicalOutcome.NO_TRADE


def _ai_challenge(
    advice: Advice,
    *,
    gates_open: bool,
    council: CouncilVerdict | None,
    panel: Any,
) -> AiChallengeRecord:
    stance = council.final_stance if council is not None and council.council_status == "ONLINE" else None
    panel_verdict = getattr(panel, "verdict", None) if panel is not None else None
    original = None
    resulting = advice.action
    challenged = False
    effect = "NONE"
    upgrade_blocked = False
    reason = "no AI challenge"

    if not gates_open and stance in ("ENTER", "WATCH", "BUY"):
        upgrade_blocked = True
        challenged = True
        reason = "AI_CHALLENGE: upgrade blocked — identity/security gates are closed"
        return AiChallengeRecord(
            True, original, resulting, stance, panel_verdict, "NONE", True, reason,
        )

    if council is not None and council.council_status == "ONLINE":
        if stance == "AVOID" and resulting in ("ENTER", "WAIT"):
            challenged = True
            effect = "DOWNGRADE"
            reason = "AI_CHALLENGE: council AVOID applied as safety ratchet"
        elif stance == "UNCLEAR" and advice.conviction != "HIGH":
            challenged = True
            effect = "ABSTAIN"
            reason = "AI_CHALLENGE: council UNCLEAR recorded; conviction not upgraded"
        elif stance == "ENTER" and resulting != "ENTER":
            upgrade_blocked = True
            challenged = True
            reason = "AI_CHALLENGE: council ENTER cannot upgrade deterministic result"

    if panel is not None:
        if panel_verdict in ("CAUTION", "INSUFFICIENT_EVIDENCE") and resulting != "ENTER":
            challenged = True
            if effect == "NONE":
                effect = "DOWNGRADE" if panel_verdict == "CAUTION" else "ABSTAIN"
                reason = f"AI_CHALLENGE: panel {panel_verdict}"

    return AiChallengeRecord(
        challenged, original, resulting, stance, panel_verdict, effect,
        upgrade_blocked, reason,
    )


class CanonicalDecisionAuthority:
    """Single canonical authority. Composes DecisionAdvisor; does not fork it."""

    def __init__(
        self,
        advisor: DecisionAdvisor | None = None,
        bankroll_usd: float = 100.0,
        exit_analyzer: ExitabilityAnalyzer | None = None,
    ):
        self.advisor = advisor or DecisionAdvisor(bankroll_usd=bankroll_usd)
        self.exit_analyzer = exit_analyzer or ExitabilityAnalyzer()

    def decide(
        self,
        candidate: NormalizedTokenCandidate,
        score_report: OpportunityScoreReport,
        *,
        identity: IdentityResolution | None = None,
        now: float | None = None,
        exitability=None,
        virality=None,
        whale=None,
        narrative=None,
        council: CouncilVerdict | None = None,
        panel=None,
        identity_resolver: Callable[..., IdentityResolution] | None = None,
    ) -> CanonicalDecision:
        ts = time.time() if now is None else now
        if identity is None and identity_resolver is not None:
            identity = identity_resolver(candidate, ts)
        overlay = evaluate_security_from_candidate(
            candidate, now=ts, exitability=exitability,
        )
        if exitability is None:
            try:
                exitability = self.exit_analyzer.analyze(candidate, 200)
            except Exception:  # noqa: BLE001 — fail closed on exit analysis
                exitability = None

        advice = self.advisor.advise_entry(
            candidate, score_report,
            exitability=exitability, virality=virality, whale=whale,
            narrative=narrative, council=council, panel=panel,
            now=ts, identity=identity,
        )

        ident_state = _identity_label(identity)
        sec_state = overlay.state.value if overlay is not None else "MISSING"
        confidence = score_report.confidence_level or "LOW"
        # Confidence is evidence quality, never a copy of opportunity_score.
        if confidence not in ("HIGH", "MED", "LOW"):
            confidence = "LOW"

        gates_open = (
            identity_allows_positive_decision(identity)
            and security_allows_positive_eligibility(overlay)
        )
        monitoring = (
            token_monitoring_allowed(identity)
            and not pool_liquidity_claims_allowed(identity)
            and gates_open
        )

        hard = _map_gate_failure(
            identity=identity, overlay=overlay, advice=advice, score_report=score_report,
        )
        if hard is not None:
            outcome = hard
            monitoring = False
        else:
            outcome = _map_post_gate(advice, score_report, monitoring_only=monitoring)

        if outcome == CanonicalOutcome.BUY and monitoring:
            outcome = CanonicalOutcome.MONITOR_ONLY
        if outcome == CanonicalOutcome.BUY and not gates_open:
            outcome = CanonicalOutcome.NO_TRADE
        if monitoring and outcome == CanonicalOutcome.BUY:
            outcome = CanonicalOutcome.MONITOR_ONLY

        if outcome == CanonicalOutcome.MONITOR_ONLY:
            monitoring = True

        ai = _ai_challenge(advice, gates_open=gates_open, council=council, panel=panel)

        if outcome == CanonicalOutcome.BUY and not gates_open:
            outcome = CanonicalOutcome.REJECT
        if outcome == CanonicalOutcome.BUY and advice.action != "ENTER":
            outcome = CanonicalOutcome.NO_TRADE

        primary = (
            (advice.hard_vetoes[0] if advice.hard_vetoes else None)
            or (advice.reasons[0] if advice.reasons else None)
            or outcome.value
        )
        provenance = {
            "source_provider": getattr(candidate, "source_provider", None),
            "retrieved_ts": getattr(candidate, "retrieved_ts", None),
            "collection_ts": ts,
            "identity_state": ident_state,
            "identity_token_id": identity.token.token_id if identity is not None else None,
            "identity_policy_version": identity.policy_version if identity is not None else None,
            "identity_reason": identity.token.reason if identity is not None else "missing_identity",
            "pool_state": (
                identity.pool.state.value if identity is not None and identity.pool is not None else "MISSING"
            ),
            "security_state": sec_state,
            "security_policy_version": overlay.policy_version if overlay is not None else None,
            "security_reason": overlay.reason if overlay is not None else "missing_security",
            "scoring_version": AUTHORITY_VERSION,
            "advisor_version": ADVISOR_VERSION,
            "security_overlay_version": SECURITY_POLICY_VERSION,
            "opportunity_score": score_report.opportunity_score,
            "confidence_level": confidence,
            "risk_level": score_report.risk_level,
            "missing_unknowns": list(score_report.missing_unknowns or []),
            "ai_challenge": ai.to_dict(),
            "outcome": outcome.value,
            "advisor_action": advice.action,
            "no_invented_evidence": True,
        }
        return CanonicalDecision(
            outcome=outcome,
            advisor_action=advice.action,
            conviction=advice.conviction,
            identity_state=ident_state,
            security_state=sec_state,
            opportunity_score=score_report.opportunity_score,
            confidence_level=confidence,
            risk_level=score_report.risk_level,
            primary_reason=str(primary),
            reasons=list(advice.reasons),
            risks=list(advice.risks),
            unknowns=list(advice.unknowns),
            hard_vetoes=list(advice.hard_vetoes),
            ai_challenge=ai,
            advice=advice,
            security=overlay,
            identity=identity,
            monitoring_only=monitoring or outcome == CanonicalOutcome.MONITOR_ONLY,
            suggested_size_usd=advice.suggested_size_usd if outcome == CanonicalOutcome.BUY else None,
            provenance=provenance,
            computed_ts=ts,
        )
