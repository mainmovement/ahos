"""Explainable deterministic retrieval over P2 memory. No embeddings."""

from __future__ import annotations

import re
from typing import Iterable

from architecture.cognitive.loop.contracts import EvidenceClass, RetrievedItem, CognitiveTask
from architecture.cognitive.memory.record import MemoryRecord
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType


_TOKEN = re.compile(r"[a-z0-9_]{4,}")

KIND_TO_EVIDENCE: dict[str, str] = {
    EpistemicKind.OBSERVED_FACT.value: EvidenceClass.DIRECT_OBSERVATION.value,
    EpistemicKind.DERIVED_FACT.value: EvidenceClass.DERIVED_RESULT.value,
    EpistemicKind.INFERENCE.value: EvidenceClass.MODEL_INFERENCE.value,
    EpistemicKind.HYPOTHESIS.value: EvidenceClass.HYPOTHESIS.value,
    EpistemicKind.PREDICTION.value: EvidenceClass.PREDICTION.value,
    EpistemicKind.SIMULATION.value: EvidenceClass.SIMULATION.value,
    EpistemicKind.OPINION.value: EvidenceClass.OPINION.value,
    EpistemicKind.PROCEDURE.value: EvidenceClass.VERIFIED_RECORD.value,
    EpistemicKind.LESSON.value: EvidenceClass.DERIVED_RESULT.value,
}


def evidence_class_for(kind: str) -> str:
    return KIND_TO_EVIDENCE.get(kind, EvidenceClass.UNKNOWN.value)


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def _item(rec: MemoryRecord, reasons: Iterable[str]) -> RetrievedItem:
    return RetrievedItem(
        memory_id=rec.memory_id,
        revision=rec.revision,
        statement=rec.statement,
        match_reasons=tuple(sorted(set(reasons))),
        evidence_class=evidence_class_for(rec.epistemic_kind),
        memory_type=rec.memory_type,
        epistemic_kind=rec.epistemic_kind,
        status=rec.status,
        domain=rec.domain,
        source_id=rec.source_id,
        agent_namespace=rec.agent_namespace,
        observed_at=rec.observed_at,
        created_at=rec.created_at,
        hypothesis_id=rec.hypothesis_id,
        experiment_id=rec.experiment_id,
    )


class MemoryRetriever:
    """Deterministic retrieval with explicit MATCH_REASON strings."""

    def retrieve(
        self,
        store: CognitiveMemoryStore,
        task: CognitiveTask,
        *,
        scan_limit: int = 500,
        now: float | None = None,
    ) -> list[RetrievedItem]:
        recent = store.recent(limit=scan_limit)
        qtok = tokens(task.question) | tokens(task.objective)
        wanted_ids = set(task.requested_evidence)
        hyp = str(task.constraints.get("hypothesis_id") or "")
        exp = str(task.constraints.get("experiment_id") or "")
        out: list[RetrievedItem] = []
        for rec in recent:
            if task.agent_id and rec.agent_namespace and rec.agent_namespace != task.agent_id:
                continue
            reasons: list[str] = []
            if rec.memory_id in wanted_ids:
                reasons.append("exact_id")
            if rec.domain == task.domain:
                reasons.append("same_domain")
            if hyp and rec.hypothesis_id == hyp:
                reasons.append("same_hypothesis")
            if exp and rec.experiment_id == exp:
                reasons.append("same_experiment")
            if rec.memory_type == MemoryType.FAILURE.value:
                reasons.append("failure_relationship")
            if rec.epistemic_kind == EpistemicKind.LESSON.value:
                overlap = tokens(rec.statement) & qtok
                if overlap:
                    reasons.append("lesson_keyword_match")
            overlap = tokens(rec.statement) & qtok
            if overlap:
                reasons.append("task_keyword_match")
            if rec.source_id and rec.source_id.lower() in task.question.lower():
                reasons.append("source_relationship")
            if rec.status == DecayState.STALE.value:
                reasons.append("stale_but_queryable")
            edges = store.find_contradictions(rec.memory_id)
            if edges:
                reasons.append("contradiction_relationship")
            rel = store.find_related_memories(rec.memory_id)
            if rel:
                reasons.append("explicit_relationship")
            if now is not None and rec.observed_at is not None:
                if abs(now - rec.observed_at) <= float(task.constraints.get("temporal_window_sec") or 0):
                    reasons.append("temporal_proximity")
            if reasons:
                out.append(_item(rec, reasons))
        out.sort(key=lambda i: (-len(i.match_reasons), i.memory_id))
        return out
