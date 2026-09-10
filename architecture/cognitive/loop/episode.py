"""Episode-level polarity and write-back policy. Not entailment.

Per-item support classification is necessary but not sufficient. A bound
episode that contains both decision-bearing SUPPORT and CONTRADICTS must
not collapse to WEAKLY_SUPPORTED merely because no CONTRADICTS graph edge
exists. Callers of reason() / CognitiveOrchestrator cannot opt out.

This is not a world model. It aggregates already-classified bindings.
"""

from __future__ import annotations

from typing import Any, Iterable

from architecture.cognitive.loop.contracts import CognitiveVerdict
from architecture.cognitive.loop.support import CLAUSE_UNCERTAIN
from architecture.cognitive.loop.binding import ROLE_FACTUAL_PREMISE

MIXED_POLARITY = "mixed_polarity"
MIXED_UNCERTAIN = "mixed_uncertainty"
POLICY_CLEAR = "clear"

POSITIVE_VERDICTS = frozenset(
    {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    }
)


def decision_bearing_supporters(bindings: Iterable[Any]) -> list[Any]:
    """Bindings that may authorize a positive conclusion.

    Decision-bearing = may_support_task() AND eligible FACTUAL_PREMISE.
    Stale/historical/unknown-age observations and non-facts cannot authorize.
    Lexical METACOGNITIVE inventory is not decision-bearing.
    """
    return [
        b
        for b in bindings
        if b.may_support_task() and b.may(ROLE_FACTUAL_PREMISE)
    ]


def decision_bearing_contraries(bindings: Iterable[Any]) -> list[Any]:
    """Bindings that contradict the task proposition. Graph edges not required."""
    return [b for b in bindings if b.contradicts_task()]


def decision_bearing_uncertain(bindings: Iterable[Any]) -> list[Any]:
    """Task-relevant uncertain clauses. Presence unresolved the episode."""
    return [
        b
        for b in bindings
        if getattr(b, "clause_force", "") == CLAUSE_UNCERTAIN
        and getattr(b, "addresses_task_flag", False)
    ]


def episode_positive_block_reason(bindings: Iterable[Any]) -> str:
    """If non-empty, a positive verdict is forbidden for this episode.

    Policy (deterministic, graph-edge independent):
      SUPPORTS + CONTRADICTS → mixed_polarity
      SUPPORTS + task-relevant UNCERTAIN → mixed_uncertainty
    ENTITY_MISMATCH items are non-decision-bearing; they do not by themselves
    veto a MATCH/NONE supporter about a compatible proposition.
    """
    items = list(bindings)
    if not decision_bearing_supporters(items):
        return ""
    if decision_bearing_contraries(items):
        return MIXED_POLARITY
    if decision_bearing_uncertain(items):
        return MIXED_UNCERTAIN
    return ""


def reusable_writeback_permitted(verdict: str, bindings: Iterable[Any]) -> bool:
    """Architecture boundary: reusable LESSON/HYPOTHESIS/INFERENCE eligibility.

    Must be consulted below orchestration callers. A WEAKLY_SUPPORTED string
    is not enough when the episode is mixed, uncertain, or has no supporter.
    Assumptions are not evidence. Graph edges are not required.
    """
    if verdict not in POSITIVE_VERDICTS:
        return False
    if episode_positive_block_reason(bindings):
        return False
    if not decision_bearing_supporters(bindings):
        return False
    return True


def apply_episode_positive_policy(candidate: Any, bindings: Iterable[Any]) -> Any:
    """Non-bypassable post-mode/post-critic gate. Callers cannot opt out.

    SUPPORTS + CONTRADICTS → CONTESTED (graph edge not required).
    SUPPORTS + task-relevant UNCERTAIN → UNRESOLVED.
    Remaining positives may cite only decision-bearing supporters.
    """
    items = list(bindings)
    code = episode_positive_block_reason(items)
    positive = getattr(candidate, "verdict", "") in POSITIVE_VERDICTS
    if not positive:
        return candidate
    steps = list(getattr(candidate, "steps", []) or [])
    if code == MIXED_POLARITY:
        candidate.verdict = CognitiveVerdict.CONTESTED.value
        candidate.epistemic = "CONTESTED"
        steps.append(
            "episode policy: SUPPORTS + CONTRADICTS fail-closed; graph edge not required"
        )
        candidate.steps = steps
        contraries = [b.memory_id for b in decision_bearing_contraries(items)]
        candidate.contradicting_ids = list(
            dict.fromkeys(list(getattr(candidate, "contradicting_ids", []) or []) + contraries)
        )
        return candidate
    if code == MIXED_UNCERTAIN:
        candidate.verdict = CognitiveVerdict.UNRESOLVED.value
        candidate.epistemic = "UNCERTAIN"
        steps.append("episode policy: SUPPORTS + UNCERTAIN fail-closed")
        candidate.steps = steps
        return candidate
    supporters = {b.memory_id for b in decision_bearing_supporters(items)}
    candidate.supporting_ids = [
        i for i in (getattr(candidate, "supporting_ids", []) or []) if i in supporters
    ]
    candidate.premises = [
        i for i in (getattr(candidate, "premises", []) or []) if i in supporters
    ]
    if not supporters:
        candidate.verdict = CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
        candidate.epistemic = "INSUFFICIENT_EVIDENCE"
        steps.append("episode policy: no decision-bearing supporter")
        candidate.steps = steps
        candidate.supporting_ids = []
    return candidate
