"""Explicit inference objects and critic constraint application.

Every meaningful conclusion is traceable to typed evidence and assumptions.
The critic may ACCEPT, DOWNGRADE, CONTEST, REQUIRE_MORE_EVIDENCE, or REFUSE.
REFUSE is live when an accepted candidate cites unbound or task-irrelevant evidence.
It must not rewrite memory or silently invent evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.loop.binding import (
    ROLE_FACTUAL_PREMISE,
    EvidenceBinding,
)
from architecture.cognitive.loop.contracts import (
    Assumption,
    CognitiveVerdict,
    EpistemicAnswer,
)


ACTION_ACCEPT = "ACCEPT"
ACTION_DOWNGRADE = "DOWNGRADE"
ACTION_CONTEST = "CONTEST"
ACTION_REQUIRE_MORE = "REQUIRE_MORE_EVIDENCE"
ACTION_REFUSE = "REFUSE"

FINDING_EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"
FINDING_TYPE_VIOLATION = "TYPE_VIOLATION"
FINDING_TEMPORAL_VIOLATION = "TEMPORAL_VIOLATION"
FINDING_APPLICABILITY_VIOLATION = "APPLICABILITY_VIOLATION"
FINDING_CONTRADICTION = "CONTRADICTION_VIOLATION"
FINDING_UNSUPPORTED_ASSUMPTION = "UNSUPPORTED_ASSUMPTION"
FINDING_MISSING_PREMISE = "MISSING_PREMISE"
FINDING_OVERCONFIDENCE = "OVERCONFIDENCE"
FINDING_SCOPE_MISMATCH = "SCOPE_MISMATCH"


@dataclass
class Inference:
    inference_id: str
    conclusion: str
    conclusion_class: str
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]
    assumptions: tuple[Assumption, ...]
    reasoning_mode: str
    applicability: str
    temporal_scope: str
    uncertainty: str
    status: str
    premises: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    missing_premises: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    candidate_status: str = ""
    critic_action: str = ACTION_ACCEPT
    critic_findings: tuple[str, ...] = ()
    lesson_applied: bool = False
    failure_applied: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "inference_id": self.inference_id,
            "conclusion": self.conclusion,
            "conclusion_class": self.conclusion_class,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(self.contradicting_evidence_ids),
            "assumptions": [a.as_dict() for a in self.assumptions],
            "reasoning_mode": self.reasoning_mode,
            "applicability": self.applicability,
            "temporal_scope": self.temporal_scope,
            "uncertainty": self.uncertainty,
            "status": self.status,
            "premises": list(self.premises),
            "alternatives": list(self.alternatives),
            "missing_premises": list(self.missing_premises),
            "steps": list(self.steps),
            "candidate_status": self.candidate_status,
            "critic_action": self.critic_action,
            "critic_findings": list(self.critic_findings),
            "lesson_applied": self.lesson_applied,
            "failure_applied": self.failure_applied,
        }


@dataclass
class CandidateInference:
    verdict: str
    epistemic: str
    conclusion: str
    conclusion_class: str
    premises: list[str] = field(default_factory=list)
    supporting_ids: list[str] = field(default_factory=list)
    contradicting_ids: list[str] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    missing_premises: list[str] = field(default_factory=list)
    lesson_applied: bool = False
    failure_applied: bool = False
    type_violations: list[str] = field(default_factory=list)
    temporal_scope: str = "CURRENT"
    applicability: str = "EPISODE"


def apply_constraint(
    candidate: CandidateInference,
    *,
    action: str,
    findings: list[str],
) -> CandidateInference:
    """Return a new candidate with verdict constrained by critic action."""
    out = CandidateInference(
        verdict=candidate.verdict,
        epistemic=candidate.epistemic,
        conclusion=candidate.conclusion,
        conclusion_class=candidate.conclusion_class,
        premises=list(candidate.premises),
        supporting_ids=list(candidate.supporting_ids),
        contradicting_ids=list(candidate.contradicting_ids),
        assumptions=list(candidate.assumptions),
        steps=list(candidate.steps),
        alternatives=list(candidate.alternatives),
        missing_premises=list(candidate.missing_premises),
        lesson_applied=candidate.lesson_applied,
        failure_applied=candidate.failure_applied,
        type_violations=list(candidate.type_violations),
        temporal_scope=candidate.temporal_scope,
        applicability=candidate.applicability,
    )
    codes = {f.split(":")[0] for f in findings}
    if action == ACTION_ACCEPT:
        out.steps.append("critic ACCEPT: no constraint")
        return out
    out.steps.append(f"critic {action}: {', '.join(findings) or 'unspecified'}")
    if action == ACTION_REFUSE:
        out.verdict = CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
        out.epistemic = EpistemicAnswer.UNKNOWN.value
        return out
    if action == ACTION_REQUIRE_MORE:
        out.verdict = CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
        out.epistemic = EpistemicAnswer.INSUFFICIENT_EVIDENCE.value
        return out
    if action == ACTION_CONTEST:
        if FINDING_CONTRADICTION in codes:
            out.verdict = CognitiveVerdict.UNRESOLVED.value
            out.epistemic = EpistemicAnswer.CONTESTED.value
        else:
            out.verdict = CognitiveVerdict.CONTESTED.value
            out.epistemic = EpistemicAnswer.CONTESTED.value
        return out
    if action == ACTION_DOWNGRADE:
        if FINDING_MISSING_PREMISE in codes:
            out.verdict = CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
            out.epistemic = EpistemicAnswer.INSUFFICIENT_EVIDENCE.value
        elif FINDING_TYPE_VIOLATION in codes and out.verdict in {
            CognitiveVerdict.SUPPORTED.value,
            CognitiveVerdict.WEAKLY_SUPPORTED.value,
        }:
            out.verdict = CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
            out.epistemic = EpistemicAnswer.UNKNOWN.value
        elif FINDING_CONTRADICTION in codes:
            out.verdict = CognitiveVerdict.UNRESOLVED.value
            out.epistemic = EpistemicAnswer.CONTESTED.value
        elif out.verdict == CognitiveVerdict.SUPPORTED.value:
            out.verdict = CognitiveVerdict.WEAKLY_SUPPORTED.value
            out.epistemic = EpistemicAnswer.PROBABLE.value
        elif out.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value:
            out.epistemic = EpistemicAnswer.UNCERTAIN.value
        return out
    return out


def to_inference(
    candidate: CandidateInference,
    *,
    mode: str,
    action: str,
    findings: list[str],
    inference_id: str = "INF-000001",
) -> Inference:
    return Inference(
        inference_id=inference_id,
        conclusion=candidate.conclusion,
        conclusion_class=candidate.conclusion_class,
        supporting_evidence_ids=tuple(candidate.supporting_ids),
        contradicting_evidence_ids=tuple(candidate.contradicting_ids),
        assumptions=tuple(candidate.assumptions),
        reasoning_mode=mode,
        applicability=candidate.applicability,
        temporal_scope=candidate.temporal_scope,
        uncertainty=candidate.epistemic,
        status=candidate.verdict,
        premises=tuple(candidate.premises),
        alternatives=tuple(candidate.alternatives),
        missing_premises=tuple(candidate.missing_premises),
        steps=tuple(candidate.steps),
        candidate_status=candidate.verdict if action == ACTION_ACCEPT else "CONSTRAINED",
        critic_action=action,
        critic_findings=tuple(findings),
        lesson_applied=candidate.lesson_applied,
        failure_applied=candidate.failure_applied,
    )


def factual_ids(bindings: list[EvidenceBinding]) -> list[str]:
    return [b.memory_id for b in bindings if b.may(ROLE_FACTUAL_PREMISE)]
