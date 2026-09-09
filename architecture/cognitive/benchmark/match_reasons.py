"""Match-reason justification. A reason is correct only if the mechanism holds."""

from __future__ import annotations

from architecture.cognitive.loop.contracts import CognitiveTask, RetrievedItem
from architecture.cognitive.loop.retrieval import tokens
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType


def match_reason_justified(
    item: RetrievedItem,
    task: CognitiveTask,
    store: CognitiveMemoryStore,
    *,
    now: float | None = None,
) -> bool:
    if not item.match_reasons:
        return False
    qtok = tokens(task.question) | tokens(task.objective)
    for reason in item.match_reasons:
        if reason == "exact_id":
            if item.memory_id not in set(task.requested_evidence):
                return False
        elif reason == "same_domain":
            if item.domain != task.domain:
                return False
        elif reason == "same_hypothesis":
            hyp = str(task.constraints.get("hypothesis_id") or "")
            if not hyp or item.hypothesis_id != hyp:
                return False
        elif reason == "same_experiment":
            exp = str(task.constraints.get("experiment_id") or "")
            if not exp or item.experiment_id != exp:
                return False
        elif reason == "failure_relationship":
            if item.memory_type != MemoryType.FAILURE.value:
                return False
        elif reason == "failure_fingerprint":
            if item.memory_type != MemoryType.FAILURE.value:
                return False
        elif reason == "contradiction_of_relevant_memory":
            if not store.find_contradictions(item.memory_id):
                return False
        elif reason == "related_to_relevant_memory":
            if not store.find_related_memories(item.memory_id):
                return False
        elif reason == "lesson_keyword_match":
            if item.epistemic_kind != EpistemicKind.LESSON.value:
                return False
            if not (tokens(item.statement) & qtok):
                return False
        elif reason == "task_keyword_match":
            if not (tokens(item.statement) & qtok):
                return False
        elif reason == "source_relationship":
            if not item.source_id or item.source_id.lower() not in task.question.lower():
                return False
        elif reason == "stale_but_queryable":
            if item.status != DecayState.STALE.value:
                return False
        elif reason == "contradiction_relationship":
            if not store.find_contradictions(item.memory_id):
                return False
        elif reason == "explicit_relationship":
            if not store.find_related_memories(item.memory_id):
                return False
        elif reason == "temporal_proximity":
            window = float(task.constraints.get("temporal_window_sec") or 0)
            if now is None or item.observed_at is None or window <= 0:
                return False
            if abs(now - item.observed_at) > window:
                return False
        elif reason == "type_compatibility":
            if item.epistemic_kind == EpistemicKind.LESSON.value and qtok & {
                "learn",
                "learned",
                "lesson",
                "lessons",
            }:
                continue
            if item.memory_type == MemoryType.FAILURE.value and qtok & {
                "fail",
                "failed",
                "failure",
                "failures",
            }:
                continue
            if item.status in {
                DecayState.STALE.value,
                DecayState.SUPERSEDED.value,
                DecayState.ARCHIVED.value,
            } and qtok & {"historical", "history", "stale", "superseded", "quarter"}:
                continue
            return False
        else:
            return False
    return True
