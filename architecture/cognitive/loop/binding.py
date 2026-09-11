"""Deterministic evidence binding. Interpretation layer — does not rewrite memory.

Answers: how may this retrieved memory be used in this reasoning episode?
Does not invent probabilities. Does not convert confidence into truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.loop.contracts import CognitiveContext, CognitiveTask, RetrievedItem, TaskType
from architecture.cognitive.loop.retrieval import canonical_set, content_tokens
from architecture.cognitive.loop.support import (
    CLAUSE_AFFIRMED,
    CLAUSE_NEGATED,
    CLAUSE_UNCERTAIN,
    ENTITY_AMBIGUOUS,
    ENTITY_MISMATCH,
    ENTITY_NONE,
    ENTITY_SCOPED,
    POLARITY_CONTRADICTS,
    POLARITY_NEGATED,
    POLARITY_UNKNOWN,
    SUPPORT_DIRECT as TASK_DIRECT_SUPPORT,
    SUPPORT_UNKNOWN as TASK_SUPPORT_UNKNOWN,
    SupportAssessment,
    classify_support,
    positive_support_eligible,
)
from architecture.cognitive.memory.observation import (
    current_grant_verify_context,
    latest_observation_fields,
    observation_grant_permits_factual,
)
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
    return typed_class_from_parts(item.memory_type, item.epistemic_kind)


def typed_class_from_parts(memory_type: str, epistemic_kind: str) -> str:
    if memory_type == MemoryType.FAILURE.value:
        return "FAILURE"
    if memory_type == MemoryType.EXPERIMENT.value:
        return "EXPERIMENT"
    return epistemic_kind or "UNKNOWN"


def temporal_state_of(item: RetrievedItem) -> str:
    """Decay status is authoritative. A timestamp does not prove freshness.

    No age-from-clock threshold is invented here. Store decay uses
    expires_at / valid_until only (`CognitiveMemoryStore.apply_decay`).
    ACTIVE + observed_at is DATED, not CURRENT. TEMP_CURRENT is reserved
    for an explicit freshness proof this layer does not compute.
    """
    return temporal_from_parts(item.status, item.observed_at)


def temporal_from_parts(status: str, observed_at: float | None) -> str:
    """Ignore any copied temporal_state field. Status + observed_at are source."""
    if status == DecayState.SUPERSEDED.value:
        return TEMP_SUPERSEDED
    if status == DecayState.STALE.value:
        return TEMP_STALE
    if status == DecayState.ARCHIVED.value:
        return TEMP_HISTORICAL
    if status == DecayState.AGING.value:
        return TEMP_AGING
    if observed_at is None:
        return TEMP_UNKNOWN
    return TEMP_DATED


def task_content_tokens(task: CognitiveTask) -> set[str]:
    return canonical_set(content_tokens(task.question) | content_tokens(task.objective))


def addresses_task(statement: str, task: CognitiveTask) -> bool:
    """Deterministic lexical relevance. Valid type ≠ relevant content.

    Uses the existing retrieval tokenizer (4+ char tokens, stopwords,
    documented inflections). Not embeddings. Fail-closed: no overlap → False.
    Lexical match is candidate relevance only — not evidence support.
    """
    return bool(canonical_set(content_tokens(statement)) & task_content_tokens(task))


def assess_task_support(statement: str, task: CognitiveTask) -> SupportAssessment:
    """Task-support class. Separate from addresses_task (lexical relevance)."""
    return classify_support(statement, task)


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


def _roles(
    typed: str,
    temporal: str,
    applicability: str,
    *,
    grant_ok: bool = False,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
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
        elif not grant_ok:
            # Label without a verified ObservationGrant is data only.
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


def _support_strength(
    typed: str, applicability: str, temporal: str, *, grant_ok: bool = False
) -> str:
    if applicability == NOT_APPLICABLE:
        return SUPPORT_NONE
    if typed == "OBSERVED_FACT" and not grant_ok:
        return SUPPORT_UNKNOWN
    if typed == "OBSERVED_FACT" and temporal in {TEMP_CURRENT, TEMP_AGING, TEMP_DATED}:
        return SUPPORT_DIRECT
    if typed in {"INFERENCE", "DERIVED_FACT", "PROCEDURE", "EXPERIMENT"}:
        return SUPPORT_INDIRECT
    if typed in {"LESSON", "FAILURE"} and applicability == APPLICABLE:
        return SUPPORT_INDIRECT
    if typed in {"HYPOTHESIS", "PREDICTION", "SIMULATION", "OPINION"}:
        return SUPPORT_NONE
    return SUPPORT_UNKNOWN


@dataclass(frozen=True)
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
    addresses_task_flag: bool = False
    support_class: str = TASK_SUPPORT_UNKNOWN
    support_polarity: str = POLARITY_UNKNOWN
    support_reason: str = ""
    alien_tokens: tuple[str, ...] = ()
    clause_force: str = CLAUSE_AFFIRMED
    entity_state: str = ENTITY_NONE
    evidence_entities: tuple[str, ...] = ()
    task_entities: tuple[str, ...] = ()
    task_question: str = ""
    task_objective: str = ""
    task_domain: str = ""
    task_component: str = ""
    task_failure_type: str = ""
    observed_at: float | None = None
    source_type: str = ""
    valid_until: float | None = None
    task_created_at: float = 0.0
    authority_now: float = 0.0

    def _task_snapshot(self) -> CognitiveTask:
        return CognitiveTask(
            task_id="bound-snapshot",
            task_type=TaskType.ANALYZE.value,
            objective=self.task_objective or "bound",
            question=self.task_question,
            domain=self.task_domain or self.domain or "software",
            requester="binding",
            created_at=0.0,
            data_label="SYNTHETIC_TEST_DATA",
            constraints={
                "component": self.task_component,
                "failure_type": self.task_failure_type,
            },
        )

    def _live_assessment(self):
        """Authoritative recompute from statement + task snapshot. Fields are hints."""
        if not self.task_question and not self.statement:
            return None
        return classify_support(self.statement, self._task_snapshot())

    def live_typed_class(self) -> str:
        return typed_class_from_parts(self.memory_type, self.epistemic_kind)

    def live_temporal_state(self) -> str:
        return temporal_from_parts(self.status, self.observed_at)

    def live_applicability(self) -> str:
        item = RetrievedItem(
            memory_id=self.memory_id,
            revision=1,
            statement=self.statement,
            match_reasons=self.match_reasons,
            evidence_class="",
            memory_type=self.memory_type,
            epistemic_kind=self.epistemic_kind,
            status=self.status,
            domain=self.domain,
            source_id="",
            agent_namespace="",
            observed_at=self.observed_at,
            created_at=0.0,
        )
        return _applicability(
            self.live_typed_class(), item, self._task_snapshot(), dict(self.payload)
        )

    def live_grant_ok(self) -> bool:
        now = self.authority_now
        return observation_grant_permits_factual(
            statement=self.statement,
            epistemic_kind=self.epistemic_kind,
            memory_type=self.memory_type,
            source_type=self.source_type or str(self.provenance.get("source_type") or ""),
            source_id=str(self.provenance.get("source_id") or ""),
            observed_at=self.observed_at,
            valid_until=self.valid_until,
            domain=self.domain,
            payload=self.payload,
            now=now,
            status=self.status,
        )

    def live_roles(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return _roles(
            self.live_typed_class(),
            self.live_temporal_state(),
            self.live_applicability(),
            grant_ok=self.live_grant_ok(),
        )

    def live_addresses_task(self) -> bool:
        return addresses_task(self.statement, self._task_snapshot())

    def is_task_relevant_uncertain(self) -> bool:
        live = self._live_assessment()
        if live is None:
            return False
        return live.clause_force == CLAUSE_UNCERTAIN and self.live_addresses_task()

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
            "support_class": self.support_class,
            "support_polarity": self.support_polarity,
            "support_reason": self.support_reason,
            "clause_force": self.clause_force,
            "entity_state": self.entity_state,
            "evidence_entities": list(self.evidence_entities),
            "task_entities": list(self.task_entities),
            "task_question": self.task_question,
            "addresses_task": self.addresses_task_flag,
            "alien_tokens": list(self.alien_tokens),
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
        """Roles are recomputed. Stored allowed/forbidden tuples cannot escalate."""
        allowed, forbidden = self.live_roles()
        if role in forbidden:
            return False
        return role in allowed

    def may_support_task(self) -> bool:
        """Load-bearing: recomputes from statement. Stored polarity cannot override."""
        live = self._live_assessment()
        if live is not None:
            return positive_support_eligible(live)
        return positive_support_eligible(
            SupportAssessment(
                support_class=self.support_class,
                polarity=self.support_polarity,
                clause_force=self.clause_force,
                entity_state=self.entity_state,
                evidence_entities=self.evidence_entities,
                task_entities=self.task_entities,
                reason=self.support_reason,
                subject_overlap=(),
                object_overlap=(),
                alien_tokens=self.alien_tokens,
            )
        )

    def contradicts_task(self) -> bool:
        """Same-entity contrary/negated evidence. Mismatch is not contradiction."""
        live = self._live_assessment()
        support_class = live.support_class if live is not None else self.support_class
        polarity = live.polarity if live is not None else self.support_polarity
        clause_force = live.clause_force if live is not None else self.clause_force
        entity_state = live.entity_state if live is not None else self.entity_state
        if support_class != TASK_DIRECT_SUPPORT:
            return False
        if entity_state in {ENTITY_MISMATCH, ENTITY_AMBIGUOUS, ENTITY_SCOPED}:
            return False
        if clause_force == CLAUSE_UNCERTAIN:
            return False
        if clause_force == CLAUSE_NEGATED:
            return True
        return polarity in {POLARITY_CONTRADICTS, POLARITY_NEGATED}


def _trusted_now(task: CognitiveTask, now: float | None) -> float | None:
    """Episode authority time. Never CognitiveTask.created_at."""
    del task
    if now is not None:
        return float(now)
    ctx = current_grant_verify_context()
    if ctx is not None:
        return float(ctx.trusted_now)
    return None


def bind_item(
    item: RetrievedItem,
    task: CognitiveTask,
    *,
    store: CognitiveMemoryStore | None = None,
    contradicted_ids: set[str] | None = None,
    index: int = 0,
    now: float | None = None,
) -> EvidenceBinding:
    latest = latest_observation_fields(store, item.memory_id)
    if latest is not None:
        statement = latest.statement
        domain = latest.domain
        status = latest.status
        epistemic_kind = latest.epistemic_kind
        memory_type = latest.memory_type
        observed_at = latest.observed_at
        valid_until = latest.valid_until
        source_type = latest.source_type
        source_id = latest.source_id
        payload = dict(latest.payload) if isinstance(latest.payload, dict) else {}
        typed = typed_class_from_parts(memory_type, epistemic_kind)
        temporal = temporal_from_parts(status, observed_at)
    else:
        statement = item.statement
        domain = item.domain
        status = item.status
        epistemic_kind = item.epistemic_kind
        memory_type = item.memory_type
        observed_at = item.observed_at
        valid_until = None
        source_type = ""
        source_id = item.source_id
        payload = _payload(store, item.memory_id)
        typed = typed_class_of(item)
        temporal = temporal_state_of(item)
    applicability = _applicability(
        typed,
        RetrievedItem(
            memory_id=item.memory_id,
            revision=item.revision,
            statement=statement,
            match_reasons=item.match_reasons,
            evidence_class=item.evidence_class,
            memory_type=memory_type,
            epistemic_kind=epistemic_kind,
            status=status,
            domain=domain,
            source_id=source_id,
            agent_namespace=item.agent_namespace,
            observed_at=observed_at,
            created_at=item.created_at,
        ),
        task,
        payload,
    )
    trusted_now = _trusted_now(task, now)
    grant_ok = False
    if trusted_now is not None:
        grant_ok = observation_grant_permits_factual(
            statement=statement,
            epistemic_kind=epistemic_kind,
            memory_type=memory_type,
            source_type=source_type,
            source_id=source_id,
            observed_at=observed_at,
            valid_until=valid_until,
            domain=domain,
            payload=payload,
            now=trusted_now,
            status=status,
        )
    allowed, forbidden = _roles(typed, temporal, applicability, grant_ok=grant_ok)
    contradicted = bool(contradicted_ids and item.memory_id in contradicted_ids)
    support = classify_support(statement, task)
    lexical = addresses_task(statement, task)
    return EvidenceBinding(
        evidence_id=f"EVD-{index:06d}-{item.memory_id}",
        memory_id=item.memory_id,
        typed_class=typed,
        relevance="RETRIEVED",
        applicability=applicability,
        temporal_state=temporal,
        provenance={
            "source_id": source_id,
            "source_type": source_type,
            "producer": "retrieved",
            "evidence_class_p3": item.evidence_class,
        },
        support_strength=_support_strength(
            typed, applicability, temporal, grant_ok=grant_ok
        ),
        contradiction_state="CONTESTED" if contradicted else "UNCONTESTED",
        allowed_reasoning_roles=allowed,
        forbidden_reasoning_roles=forbidden,
        statement=statement,
        domain=domain,
        status=status,
        epistemic_kind=epistemic_kind,
        memory_type=memory_type,
        match_reasons=tuple(item.match_reasons),
        payload=payload,
        addresses_task_flag=lexical,
        support_class=support.support_class,
        support_polarity=support.polarity,
        support_reason=support.reason,
        alien_tokens=support.alien_tokens,
        clause_force=support.clause_force,
        entity_state=support.entity_state,
        evidence_entities=support.evidence_entities,
        task_entities=support.task_entities,
        task_question=task.question,
        task_objective=task.objective,
        task_domain=task.domain,
        task_component=str(task.constraints.get("component") or ""),
        task_failure_type=str(task.constraints.get("failure_type") or ""),
        observed_at=observed_at,
        source_type=source_type,
        valid_until=valid_until,
        task_created_at=float(task.created_at) if task.created_at else 0.0,
        authority_now=float(trusted_now) if trusted_now is not None else 0.0,
    )


def bind_context(
    ctx: CognitiveContext,
    task: CognitiveTask,
    *,
    store: CognitiveMemoryStore | None = None,
    now: float | None = None,
) -> list[EvidenceBinding]:
    contradicted: set[str] = set()
    for edge in ctx.contradictions:
        if isinstance(edge, dict):
            contradicted.add(str(edge.get("from_id") or ""))
            contradicted.add(str(edge.get("to_id") or ""))
    bindings: list[EvidenceBinding] = []
    for i, item in enumerate(ctx.all_included()):
        bindings.append(
            bind_item(
                item,
                task,
                store=store,
                contradicted_ids=contradicted,
                index=i + 1,
                now=now,
            )
        )
    return bindings


def with_role(bindings: list[EvidenceBinding], role: str) -> list[EvidenceBinding]:
    return [b for b in bindings if b.may(role)]


def bound_memory_ids(bindings: list[EvidenceBinding]) -> set[str]:
    return {b.memory_id for b in bindings}


def cited_unbound_ids(cited: list[str], bindings: list[EvidenceBinding]) -> list[str]:
    allowed = bound_memory_ids(bindings)
    return [i for i in cited if i and i not in allowed]
