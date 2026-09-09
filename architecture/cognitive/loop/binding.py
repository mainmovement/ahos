"""Deterministic evidence binding. Interpretation layer — does not rewrite memory.

Answers: how may this retrieved memory be used in this reasoning episode?
Does not invent probabilities. Does not convert confidence into truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.loop.contracts import CognitiveContext, CognitiveTask, RetrievedItem
from architecture.cognitive.loop.retrieval import canonical_set, content_tokens
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType, UNKNOWN

ROLE_FACTUAL_PREMISE = "FACTUAL_PREMISE"
ROLE_INFERRED_PREMISE = "INFERRED_PREMISE"
ROLE_EXPLANATION = "EXPLANATION_CANDIDATE"
ROLE_PREDICTION = "PREDICTION_SIGNAL"
ROLE_SIMULATION = "SIMULATION_SIGNAL"
ROLE_PERSPECTIVE = "PERSPECTIVE"
ROLE_PROCEDURE = "PROCEDURE"
ROLE_CONSTRAINT = "CONSTRAINT"
ROLE_CAUTION = "CAUTION"
ROLE_ANALYTICAL = "ANALYTICAL_FINDING"
ROLE_COMPARISON = "COMPARISON_SIDE"
ROLE_HISTORY = "HISTORY"

APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
APPLICABILITY_UNKNOWN = "UNKNOWN"

TEMP_CURRENT = "CURRENT"
TEMP_DATED = "DATED"
TEMP_STALE = "STALE"
TEMP_SUPERSEDED = "SUPERSEDED"
TEMP_HISTORICAL = "HISTORICAL"
TEMP_AGING = "AGING"
TEMP_UNKNOWN = "UNKNOWN_AGE"

SUPPORT_DIRECT = "DIRECT"
SUPPORT_INDIRECT = "INDIRECT"
SUPPORT_NONE = "NONE"
SUPPORT_UNKNOWN = "UNKNOWN"

UNKNOWN_FIELD = frozenset({"", "UNKNOWN", "NONE", "N/A", "unknown", "none", UNKNOWN})


def _explicit(value: Any) -> str:
    text = str(value or "").strip()
    if text in UNKNOWN_FIELD or text.upper() in UNKNOWN_FIELD:
        return ""
    return text


def typed_class_of(item: RetrievedItem) -> str:
    """P5 taxonomy: what the memory IS. FAILURE/EXPERIMENT win over epistemic kind."""
    if item.memory_type == MemoryType.FAILURE.value:
        return "FAILURE"
    if item.memory_type == MemoryType.EXPERIMENT.value:
        return "EXPERIMENT"
    return item.epistemic_kind or "UNKNOWN"


def temporal_state_of(item: RetrievedItem) -> str:
    """Decay status is authoritative. A timestamp does not prove freshness.

    No age-from-clock threshold is invented here. Store decay uses
    expires_at / valid_until only (`CognitiveMemoryStore.apply_decay`).
    ACTIVE + observed_at is DATED, not CURRENT.
    """
    if item.status == DecayState.SUPERSEDED.value:
        return TEMP_SUPERSEDED
    if item.status == DecayState.STALE.value:
        return TEMP_STALE
    if item.status == DecayState.ARCHIVED.value:
        return TEMP_HISTORICAL
    if item.status == DecayState.AGING.value:
        return TEMP_AGING
    if item.observed_at is None:
        return TEMP_UNKNOWN
    return TEMP_DATED


def task_content_tokens(task: CognitiveTask) -> set[str]:
    return canonical_set(content_tokens(task.question) | content_tokens(task.objective))


def addresses_task(statement: str, task: CognitiveTask) -> bool:
    """Deterministic lexical relevance. Valid type ≠ relevant content.

    Uses the existing retrieval tokenizer (4+ char tokens, stopwords,
    documented inflections). Not embeddings. Fail-closed: no overlap → False.
    """
    return bool(canonical_set(content_tokens(statement)) & task_content_tokens(task))


def _payload(store: CognitiveMemoryStore | None, memory_id: str) -> dict[str, Any]:
    if store is None:
        return {}
    rec = store.get(memory_id)
    if rec is None or not isinstance(rec.payload, dict):
        return {}
    return dict(rec.payload)


def _applicability(
    typed: str,
    item: RetrievedItem,
    task: CognitiveTask,
    payload: dict[str, Any],
) -> str:
    if typed == "LESSON":
        app = _explicit(payload.get("applicability"))
        if app and task.domain and app != task.domain:
            return NOT_APPLICABLE
        q_comp = _explicit(task.constraints.get("component"))
        m_comp = _explicit(payload.get("component"))
        if q_comp and m_comp:
            return APPLICABLE if q_comp.lower() == m_comp.lower() else NOT_APPLICABLE
        # Same domain is not the same problem. Missing fingerprints stay UNKNOWN.
        return APPLICABILITY_UNKNOWN
    if typed == "FAILURE":
        q_comp = _explicit(task.constraints.get("component"))
        m_comp = _explicit(payload.get("component"))
        q_ft = _explicit(task.constraints.get("failure_type"))
        m_ft = _explicit(payload.get("failure_type"))
        fail_domain = _explicit(item.domain)
        if (
            fail_domain
            and task.domain
            and fail_domain not in {task.domain, "COGNITIVE_CORE"}
        ):
            return NOT_APPLICABLE
        comp_both = bool(q_comp and m_comp)
        ft_both = bool(q_ft and m_ft)
        if comp_both and q_comp.lower() != m_comp.lower():
            return NOT_APPLICABLE
        if ft_both and q_ft.lower() != m_ft.lower():
            return NOT_APPLICABLE
        if comp_both and ft_both:
            return APPLICABLE
        return APPLICABILITY_UNKNOWN
    if item.domain and task.domain and item.domain not in {task.domain, "COGNITIVE_CORE"}:
        return NOT_APPLICABLE
    if not item.domain or item.domain == "COGNITIVE_CORE":
        return APPLICABILITY_UNKNOWN
    return APPLICABLE


def _roles(typed: str, temporal: str, applicability: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    forbidden = [ROLE_FACTUAL_PREMISE]
    allowed: list[str] = [ROLE_COMPARISON]

    if typed == "OBSERVED_FACT":
        forbidden = []
        if applicability == NOT_APPLICABLE:
            allowed = [ROLE_COMPARISON]
            forbidden = [ROLE_FACTUAL_PREMISE]
        elif temporal in {TEMP_STALE, TEMP_SUPERSEDED, TEMP_HISTORICAL}:
            allowed = [ROLE_HISTORY, ROLE_COMPARISON]
            forbidden = [ROLE_FACTUAL_PREMISE]
        elif temporal == TEMP_UNKNOWN:
            allowed = [ROLE_HISTORY, ROLE_COMPARISON]
            forbidden = [ROLE_FACTUAL_PREMISE]
        else:
            # DATED / AGING / CURRENT: typed observation is eligible; DATED ≠ proven fresh.
            allowed = [ROLE_FACTUAL_PREMISE, ROLE_COMPARISON, ROLE_HISTORY]
    elif typed == "DERIVED_FACT":
        allowed = [ROLE_INFERRED_PREMISE, ROLE_COMPARISON]
        forbidden = [ROLE_FACTUAL_PREMISE]
    elif typed == "INFERENCE":
        allowed = [ROLE_INFERRED_PREMISE, ROLE_EXPLANATION, ROLE_COMPARISON]
    elif typed == "HYPOTHESIS":
        allowed = [ROLE_EXPLANATION, ROLE_COMPARISON]
    elif typed == "PREDICTION":
        allowed = [ROLE_PREDICTION, ROLE_COMPARISON]
    elif typed == "SIMULATION":
        allowed = [ROLE_SIMULATION, ROLE_COMPARISON]
    elif typed == "OPINION":
        allowed = [ROLE_PERSPECTIVE, ROLE_COMPARISON]
    elif typed == "PROCEDURE":
        allowed = [ROLE_PROCEDURE, ROLE_COMPARISON]
        forbidden = [ROLE_FACTUAL_PREMISE]
    elif typed == "LESSON":
        forbidden = [ROLE_FACTUAL_PREMISE]
        if applicability == APPLICABLE:
            allowed = [ROLE_CONSTRAINT, ROLE_COMPARISON]
        else:
            allowed = [ROLE_COMPARISON]
    elif typed == "FAILURE":
        forbidden = [ROLE_FACTUAL_PREMISE]
        if applicability == APPLICABLE:
            allowed = [ROLE_CAUTION, ROLE_HISTORY, ROLE_COMPARISON]
        else:
            allowed = [ROLE_COMPARISON]
    elif typed == "EXPERIMENT":
        allowed = [ROLE_ANALYTICAL, ROLE_COMPARISON]
    else:
        allowed = [ROLE_COMPARISON]
        forbidden = [ROLE_FACTUAL_PREMISE]

    return tuple(allowed), tuple(forbidden)


def _support_strength(typed: str, applicability: str, temporal: str) -> str:
    if applicability == NOT_APPLICABLE:
        return SUPPORT_NONE
    if typed == "OBSERVED_FACT" and temporal in {TEMP_CURRENT, TEMP_AGING, TEMP_DATED}:
        return SUPPORT_DIRECT
    if typed in {"INFERENCE", "DERIVED_FACT", "PROCEDURE", "EXPERIMENT"}:
        return SUPPORT_INDIRECT
    if typed in {"LESSON", "FAILURE"} and applicability == APPLICABLE:
        return SUPPORT_INDIRECT
    if typed in {"HYPOTHESIS", "PREDICTION", "SIMULATION", "OPINION"}:
        return SUPPORT_NONE
    return SUPPORT_UNKNOWN


@dataclass
class EvidenceBinding:
    evidence_id: str
    memory_id: str
    typed_class: str
    relevance: str
    applicability: str
    temporal_state: str
    provenance: dict[str, Any]
    support_strength: str
    contradiction_state: str
    allowed_reasoning_roles: tuple[str, ...]
    forbidden_reasoning_roles: tuple[str, ...]
    statement: str
    domain: str
    status: str
    epistemic_kind: str
    memory_type: str
    match_reasons: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "memory_id": self.memory_id,
            "typed_class": self.typed_class,
            "evidence_class": self.typed_class,
            "relevance": self.relevance,
            "applicability": self.applicability,
            "temporal_state": self.temporal_state,
            "provenance": dict(self.provenance),
            "support_strength": self.support_strength,
            "contradiction_state": self.contradiction_state,
            "allowed_reasoning_roles": list(self.allowed_reasoning_roles),
            "forbidden_reasoning_roles": list(self.forbidden_reasoning_roles),
            "statement": self.statement,
            "domain": self.domain,
            "status": self.status,
            "epistemic_kind": self.epistemic_kind,
            "memory_type": self.memory_type,
            "match_reasons": list(self.match_reasons),
        }

    def may(self, role: str) -> bool:
        if role in self.forbidden_reasoning_roles:
            return False
        return role in self.allowed_reasoning_roles


def bind_item(
    item: RetrievedItem,
    task: CognitiveTask,
    *,
    store: CognitiveMemoryStore | None = None,
    contradicted_ids: set[str] | None = None,
    index: int = 0,
) -> EvidenceBinding:
    payload = _payload(store, item.memory_id)
    typed = typed_class_of(item)
    temporal = temporal_state_of(item)
    applicability = _applicability(typed, item, task, payload)
    allowed, forbidden = _roles(typed, temporal, applicability)
    contradicted = bool(contradicted_ids and item.memory_id in contradicted_ids)
    return EvidenceBinding(
        evidence_id=f"EVD-{index:06d}-{item.memory_id}",
        memory_id=item.memory_id,
        typed_class=typed,
        relevance="RETRIEVED",
        applicability=applicability,
        temporal_state=temporal,
        provenance={
            "source_id": item.source_id,
            "producer": "retrieved",
            "evidence_class_p3": item.evidence_class,
        },
        support_strength=_support_strength(typed, applicability, temporal),
        contradiction_state="CONTESTED" if contradicted else "UNCONTESTED",
        allowed_reasoning_roles=allowed,
        forbidden_reasoning_roles=forbidden,
        statement=item.statement,
        domain=item.domain,
        status=item.status,
        epistemic_kind=item.epistemic_kind,
        memory_type=item.memory_type,
        match_reasons=tuple(item.match_reasons),
        payload=payload,
    )


def bind_context(
    ctx: CognitiveContext,
    task: CognitiveTask,
    *,
    store: CognitiveMemoryStore | None = None,
) -> list[EvidenceBinding]:
    contradicted: set[str] = set()
    for edge in ctx.contradictions:
        if isinstance(edge, dict):
            contradicted.add(str(edge.get("from_id") or ""))
            contradicted.add(str(edge.get("to_id") or ""))
    bindings: list[EvidenceBinding] = []
    for i, item in enumerate(ctx.all_included()):
        bindings.append(
            bind_item(item, task, store=store, contradicted_ids=contradicted, index=i + 1)
        )
    return bindings


def with_role(bindings: list[EvidenceBinding], role: str) -> list[EvidenceBinding]:
    return [b for b in bindings if b.may(role)]


def bound_memory_ids(bindings: list[EvidenceBinding]) -> set[str]:
    return {b.memory_id for b in bindings}


def cited_unbound_ids(cited: list[str], bindings: list[EvidenceBinding]) -> list[str]:
    allowed = bound_memory_ids(bindings)
    return [i for i in cited if i and i not in allowed]
