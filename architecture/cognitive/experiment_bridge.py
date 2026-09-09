"""Bridge to existing ExperimentLedger — no second experiment brain.

Cognitive experiments get ledger experiment_id values and MUST NOT overwrite
observed soak/outcome rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from architecture.evolution.experiment import ExperimentLedger, ExperimentRecord, RESULTS

from .contracts import HypothesisState
from .hypothesis import HypothesisStore, HypothesisTransitionError


@dataclass
class CognitiveExperiment:
    experiment_id: str
    hypothesis_id: str
    ledger_record: ExperimentRecord

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "hypothesis_id": self.hypothesis_id,
            "ledger": self.ledger_record.as_dict(),
        }


def record_cognitive_experiment(
    *,
    hypothesis_store: HypothesisStore,
    hypothesis_id: str,
    baseline: str,
    method: str,
    result: str,
    ledger: ExperimentLedger | None = None,
    ledger_path: Path | str | None = None,
    evidence_refs: list[str] | None = None,
    failure_reason: str | None = None,
    reusable_lesson: str = "",
) -> CognitiveExperiment:
    if result not in RESULTS:
        raise ValueError(f"unknown result {result!r}; allowed={RESULTS}")
    hyp = hypothesis_store.get(hypothesis_id)
    if hyp is None:
        raise KeyError(hypothesis_id)
    led = ledger or ExperimentLedger(ledger_path)
    rec = led.record(
        hypothesis=hyp.statement,
        baseline=baseline,
        attempted_change=method,
        result=result,
        failure_reason=failure_reason,
        reusable_lesson=reusable_lesson,
        evidence_refs=evidence_refs or [],
        classification="COGNITIVE",
        subsystem="architecture.cognitive",
    )
    exp_id = rec.experiment_id
    if hyp.state == HypothesisState.PROPOSED.value:
        hypothesis_store.transition(hypothesis_id, HypothesisState.UNDER_REVIEW)
        hyp = hypothesis_store.get(hypothesis_id)
    if hyp and hyp.state == HypothesisState.UNDER_REVIEW.value:
        try:
            hypothesis_store.transition(
                hypothesis_id, HypothesisState.TESTING, experiment_id=exp_id,
            )
        except HypothesisTransitionError:
            hypothesis_store.attach_experiment(hypothesis_id, exp_id)
    else:
        hypothesis_store.attach_experiment(hypothesis_id, exp_id)
    return CognitiveExperiment(
        experiment_id=exp_id, hypothesis_id=hypothesis_id, ledger_record=rec,
    )
