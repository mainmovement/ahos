"""M58.1 paper decision self-evaluation.

Scores a recorded call against a later outcome and files an UNVERIFIED lesson.
It does not change gates, weights, or the live soak ledger.
"""
from __future__ import annotations

from dataclasses import dataclass

from architecture.learning.lessons_ledger import LessonsLedger


@dataclass(frozen=True, slots=True)
class DecisionScore:
    hit: bool
    lesson_id: str
    retrieval_weight: float
    gate_limit: float


def evaluate_paper_decision(
    ledger: LessonsLedger,
    *,
    lesson_id: str,
    market: str,
    decision_ts: str,
    predicted: str,
    outcome_ts: str,
    realized: str,
    evidence_ref: str,
    gate_limit: float,
) -> DecisionScore:
    if outcome_ts <= decision_ts:
        raise ValueError("outcome is not after the decision; refusing future leak")
    hit = predicted == realized
    claim = f"predicted {predicted}; realized {realized}; hit={hit}"
    ledger.append(
        lesson_id=lesson_id,
        source="trade_loss" if not hit else "trade_review",
        market=market,
        taxonomy="direction",
        evidence_refs=(evidence_ref,),
        claim=claim,
        counterfactual=f"the other call would have been {'a miss' if hit else 'a hit'}",
        valid_from=outcome_ts,
    )
    weight = ledger.retrieval_weight(lesson_id, as_of=outcome_ts)
    return DecisionScore(
        hit=hit,
        lesson_id=lesson_id,
        retrieval_weight=weight,
        gate_limit=gate_limit,
    )
