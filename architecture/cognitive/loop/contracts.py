"""P3 cognitive-loop contracts. Not AGI. No LLM required."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    ANALYZE = "ANALYZE"
    COMPARE = "COMPARE"
    EXPLAIN = "EXPLAIN"
    INVESTIGATE = "INVESTIGATE"
    PREDICT = "PREDICT"
    CRITIQUE = "CRITIQUE"
    HYPOTHESIZE = "HYPOTHESIZE"
    TEST = "TEST"
    LEARN = "LEARN"
    SELF_RESEARCH = "SELF_RESEARCH"


class ReasoningMode(str, Enum):
    DEDUCTIVE = "DEDUCTIVE"
    INDUCTIVE = "INDUCTIVE"
    ABDUCTIVE = "ABDUCTIVE"
    COMPARATIVE = "COMPARATIVE"
    CAUSAL_HYPOTHESIS = "CAUSAL_HYPOTHESIS"
    TEMPORAL = "TEMPORAL"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    ADVERSARIAL = "ADVERSARIAL"
    METACOGNITIVE = "METACOGNITIVE"


class EvidenceClass(str, Enum):
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    VERIFIED_RECORD = "VERIFIED_RECORD"
    DERIVED_RESULT = "DERIVED_RESULT"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTION = "PREDICTION"
    SIMULATION = "SIMULATION"
    OPINION = "OPINION"
    UNKNOWN = "UNKNOWN"


class ClaimOrigin(str, Enum):
    OBSERVED = "OBSERVED"
    RETRIEVED = "RETRIEVED"
    INFERRED = "INFERRED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


class CognitiveVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class EpistemicAnswer(str, Enum):
    KNOWN = "KNOWN"
    PROBABLE = "PROBABLE"
    UNCERTAIN = "UNCERTAIN"
    CONTESTED = "CONTESTED"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STALE = "STALE"


@dataclass
class CognitiveTask:
    task_id: str
    task_type: str
    objective: str
    question: str
    domain: str
    requester: str
    created_at: float = field(default_factory=time.time)
    constraints: dict[str, Any] = field(default_factory=dict)
    requested_evidence: list[str] = field(default_factory=list)
    deadline_ts: float | None = None
    ttl_seconds: float | None = None
    context_id: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    reasoning_mode: str = ReasoningMode.COMPARATIVE.value
    agent_id: str = ""
    write_back: bool = True
    data_label: str = "SYNTHETIC_TEST_DATA"

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "objective": self.objective,
            "question": self.question,
            "domain": self.domain,
            "requester": self.requester,
            "created_at": self.created_at,
            "constraints": dict(self.constraints),
            "requested_evidence": list(self.requested_evidence),
            "deadline_ts": self.deadline_ts,
            "ttl_seconds": self.ttl_seconds,
            "context_id": self.context_id,
            "provenance": dict(self.provenance),
            "reasoning_mode": self.reasoning_mode,
            "agent_id": self.agent_id,
            "write_back": self.write_back,
            "data_label": self.data_label,
        }


@dataclass
class RetrievedItem:
    memory_id: str
    revision: int
    statement: str
    match_reasons: tuple[str, ...]
    evidence_class: str
    memory_type: str
    epistemic_kind: str
    status: str
    domain: str
    source_id: str
    agent_namespace: str
    observed_at: float | None
    created_at: float
    hypothesis_id: str = ""
    experiment_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "revision": self.revision,
            "statement": self.statement,
            "match_reasons": list(self.match_reasons),
            "evidence_class": self.evidence_class,
            "memory_type": self.memory_type,
            "epistemic_kind": self.epistemic_kind,
            "status": self.status,
            "domain": self.domain,
            "source_id": self.source_id,
            "agent_namespace": self.agent_namespace,
            "observed_at": self.observed_at,
            "created_at": self.created_at,
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
        }


@dataclass
class Assumption:
    assumption_id: str
    statement: str
    basis: str
    confidence: float | None
    impact: str
    origin: str = ClaimOrigin.ASSUMED.value

    def as_dict(self) -> dict[str, Any]:
        return {
            "assumption_id": self.assumption_id,
            "statement": self.statement,
            "basis": self.basis,
            "confidence": self.confidence,
            "impact": self.impact,
            "origin": self.origin,
        }


@dataclass
class Critique:
    questions: tuple[str, ...]
    weakest_assumption: str
    alternative_explanation: str
    too_strong: bool
    prediction_confused_with_fact: bool
    stale_used_as_current: bool
    missing_evidence: tuple[str, ...]
    action: str = "ACCEPT"
    findings: tuple[str, ...] = ()
    constraint_applied: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "questions": list(self.questions),
            "weakest_assumption": self.weakest_assumption,
            "alternative_explanation": self.alternative_explanation,
            "too_strong": self.too_strong,
            "prediction_confused_with_fact": self.prediction_confused_with_fact,
            "stale_used_as_current": self.stale_used_as_current,
            "missing_evidence": list(self.missing_evidence),
            "action": self.action,
            "findings": list(self.findings),
            "constraint_applied": self.constraint_applied,
        }


@dataclass
class ContextBudget:
    max_memories: int = 20
    max_tokens_estimate: int = 4000
    max_age_seconds: float | None = None
    max_per_type: int = 8
    max_per_source: int = 8


@dataclass
class CognitiveContext:
    facts: tuple[RetrievedItem, ...]
    inferences: tuple[RetrievedItem, ...]
    hypotheses: tuple[RetrievedItem, ...]
    predictions: tuple[RetrievedItem, ...]
    experiments: tuple[RetrievedItem, ...]
    outcomes: tuple[RetrievedItem, ...]
    contradictions: tuple[dict[str, Any], ...]
    failures: tuple[RetrievedItem, ...]
    procedures: tuple[RetrievedItem, ...]
    lessons: tuple[RetrievedItem, ...]
    unknowns: tuple[str, ...]
    excluded: tuple[dict[str, str], ...]
    contradiction_present: bool
    context_incomplete: bool
    token_estimate: int
    opinions: tuple[RetrievedItem, ...] = ()
    simulations: tuple[RetrievedItem, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        def pack(items: tuple[RetrievedItem, ...]) -> list[dict[str, Any]]:
            return [i.as_dict() for i in items]

        return {
            "facts": pack(self.facts),
            "inferences": pack(self.inferences),
            "hypotheses": pack(self.hypotheses),
            "predictions": pack(self.predictions),
            "opinions": pack(self.opinions),
            "simulations": pack(self.simulations),
            "experiments": pack(self.experiments),
            "outcomes": pack(self.outcomes),
            "contradictions": list(self.contradictions),
            "failures": pack(self.failures),
            "procedures": pack(self.procedures),
            "lessons": pack(self.lessons),
            "unknowns": list(self.unknowns),
            "excluded": list(self.excluded),
            "contradiction_present": self.contradiction_present,
            "context_incomplete": self.context_incomplete,
            "token_estimate": self.token_estimate,
        }

    def all_included(self) -> list[RetrievedItem]:
        buckets = (
            self.facts,
            self.inferences,
            self.hypotheses,
            self.predictions,
            self.opinions,
            self.simulations,
            self.experiments,
            self.outcomes,
            self.failures,
            self.procedures,
            self.lessons,
        )
        out: list[RetrievedItem] = []
        seen: set[str] = set()
        for bucket in buckets:
            for item in bucket:
                if item.memory_id not in seen:
                    seen.add(item.memory_id)
                    out.append(item)
        return out


@dataclass
class ReasoningTrace:
    task_id: str
    mode: str
    mode_status: str
    retrieved_ids: tuple[str, ...]
    selected_ids: tuple[str, ...]
    excluded: tuple[dict[str, str], ...]
    assumptions: tuple[Assumption, ...]
    inferences: tuple[str, ...]
    contradictions: tuple[dict[str, Any], ...]
    steps: tuple[str, ...]
    uncertainty: str
    conclusion: str
    open_questions: tuple[str, ...]
    verdict: str
    inference_records: tuple[dict[str, Any], ...] = ()
    critic_findings: tuple[str, ...] = ()
    constraint_actions: tuple[str, ...] = ()
    evidence_classes: tuple[str, ...] = ()
    premises: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "mode_status": self.mode_status,
            "retrieved_ids": list(self.retrieved_ids),
            "selected_ids": list(self.selected_ids),
            "excluded": list(self.excluded),
            "assumptions": [a.as_dict() for a in self.assumptions],
            "inferences": list(self.inferences),
            "contradictions": list(self.contradictions),
            "steps": list(self.steps),
            "uncertainty": self.uncertainty,
            "conclusion": self.conclusion,
            "open_questions": list(self.open_questions),
            "verdict": self.verdict,
            "inference_records": list(self.inference_records),
            "critic_findings": list(self.critic_findings),
            "constraint_actions": list(self.constraint_actions),
            "evidence_classes": list(self.evidence_classes),
            "premises": list(self.premises),
        }


@dataclass
class CognitiveResult:
    task_id: str
    verdict: str
    epistemic: str
    conclusion: str
    critique: Critique
    trace: ReasoningTrace
    context: CognitiveContext | None = None
    retrieved: tuple[RetrievedItem, ...] = ()
    hypothesis_id: str = ""
    experiment_id: str = ""
    lesson_memory_id: str = ""
    episode_memory_id: str = ""
    failure_memory_id: str = ""
    novelty: dict[str, Any] = field(default_factory=dict)
    authorized_execution: bool = False
    lesson_applied: bool = False
    failure_applied: bool = False
    critic_action: str = "ACCEPT"

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "verdict": self.verdict,
            "epistemic": self.epistemic,
            "conclusion": self.conclusion,
            "critique": self.critique.as_dict(),
            "trace": self.trace.as_dict(),
            "context": None if self.context is None else self.context.as_dict(),
            "retrieved": [i.as_dict() for i in self.retrieved],
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
            "lesson_memory_id": self.lesson_memory_id,
            "episode_memory_id": self.episode_memory_id,
            "failure_memory_id": self.failure_memory_id,
            "novelty": dict(self.novelty),
            "authorized_execution": self.authorized_execution,
            "lesson_applied": self.lesson_applied,
            "failure_applied": self.failure_applied,
            "critic_action": self.critic_action,
        }
