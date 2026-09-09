"""Bounded context assembly. Incomplete context is explicit."""

from __future__ import annotations

from collections import defaultdict

from architecture.cognitive.loop.contracts import (
    CognitiveContext,
    ContextBudget,
    RetrievedItem,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType


def _est_tokens(item: RetrievedItem) -> int:
    return max(1, (len(item.statement) + 7) // 4)


def assemble_context(
    retrieved: list[RetrievedItem],
    store: CognitiveMemoryStore,
    *,
    budget: ContextBudget | None = None,
    now: float | None = None,
) -> CognitiveContext:
    budget = budget or ContextBudget()
    excluded: list[dict[str, str]] = []
    selected: list[RetrievedItem] = []
    seen: set[str] = set()
    per_type: dict[str, int] = defaultdict(int)
    per_source: dict[str, int] = defaultdict(int)
    token_sum = 0
    incomplete = False

    for item in retrieved:
        if item.memory_id in seen:
            excluded.append({"memory_id": item.memory_id, "reason": "duplicate"})
            continue
        if budget.max_age_seconds is not None and now is not None and item.observed_at is not None:
            if now - item.observed_at > budget.max_age_seconds:
                excluded.append({"memory_id": item.memory_id, "reason": "max_age"})
                incomplete = True
                continue
        if per_type[item.memory_type] >= budget.max_per_type:
            excluded.append({"memory_id": item.memory_id, "reason": "max_per_type"})
            incomplete = True
            continue
        if per_source[item.source_id] >= budget.max_per_source:
            excluded.append({"memory_id": item.memory_id, "reason": "max_per_source"})
            incomplete = True
            continue
        cost = _est_tokens(item)
        if token_sum + cost > budget.max_tokens_estimate:
            excluded.append({"memory_id": item.memory_id, "reason": "max_tokens_estimate"})
            incomplete = True
            continue
        if len(selected) >= budget.max_memories:
            excluded.append({"memory_id": item.memory_id, "reason": "max_memories"})
            incomplete = True
            continue
        seen.add(item.memory_id)
        selected.append(item)
        per_type[item.memory_type] += 1
        per_source[item.source_id] += 1
        token_sum += cost

    def bucket(*kinds: str, types: tuple[str, ...] = ()) -> tuple[RetrievedItem, ...]:
        rows = []
        for it in selected:
            if kinds and it.epistemic_kind in kinds:
                rows.append(it)
            elif types and it.memory_type in types:
                rows.append(it)
        return tuple(rows)

    facts = bucket(EpistemicKind.OBSERVED_FACT.value, EpistemicKind.DERIVED_FACT.value)
    inferences = bucket(EpistemicKind.INFERENCE.value)
    hypotheses = bucket(EpistemicKind.HYPOTHESIS.value)
    predictions = bucket(EpistemicKind.PREDICTION.value)
    experiments = tuple(i for i in selected if i.memory_type == MemoryType.EXPERIMENT.value)
    outcomes = tuple(
        i for i in selected
        if i.memory_type == MemoryType.EXPERIMENT.value or i.epistemic_kind == EpistemicKind.LESSON.value
    )
    failures = tuple(i for i in selected if i.memory_type == MemoryType.FAILURE.value)
    procedures = bucket(EpistemicKind.PROCEDURE.value)
    lessons = bucket(EpistemicKind.LESSON.value)

    contradictions: list[dict] = []
    ids = {i.memory_id for i in selected}
    for item in selected:
        for edge in store.find_contradictions(item.memory_id):
            if edge.from_id in ids or edge.to_id in ids:
                contradictions.append(edge.as_dict())
    # unique by edge_id
    uniq = {c["edge_id"]: c for c in contradictions}

    unknowns: list[str] = []
    if not facts:
        unknowns.append("no DIRECT_OBSERVATION/DERIVED_FACT in assembled context")
    if not selected:
        unknowns.append("empty assembled context")
        incomplete = True

    stale_as_current = any(
        i.status == DecayState.STALE.value and i.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
        for i in selected
    )
    if stale_as_current:
        unknowns.append("stale observations present; not current")

    return CognitiveContext(
        facts=facts,
        inferences=inferences,
        hypotheses=hypotheses,
        predictions=predictions,
        experiments=experiments,
        outcomes=outcomes,
        contradictions=tuple(uniq.values()),
        failures=failures,
        procedures=procedures,
        lessons=lessons,
        unknowns=tuple(unknowns),
        excluded=tuple(excluded),
        contradiction_present=bool(uniq),
        context_incomplete=incomplete,
        token_estimate=token_sum,
    )
