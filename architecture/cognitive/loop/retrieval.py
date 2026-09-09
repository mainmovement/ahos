"""Explainable deterministic retrieval over P2 memory. No embeddings.

P4.2: contextual signals (same_domain, unanchored edges, mere FAILURE type,
stale/recency) are not sufficient alone. Relationships expand relevance from
anchors; they do not create it from nothing.

P4.3: lexical/structural similarity is not task identity. Generic two-token
overlap and cross-domain operation cousins are not sufficient anchors.
Explicit structured mismatch rejects; missing metadata is not a mismatch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from architecture.cognitive.loop.contracts import CognitiveTask, EvidenceClass, RetrievedItem
from architecture.cognitive.memory.record import MemoryRecord
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType


_TOKEN = re.compile(r"[a-z0-9_]{4,}")

# Deterministic stopwords: not sufficient as the only lexical overlap.
STOPWORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "been",
        "before",
        "both",
        "could",
        "current",
        "data",
        "does",
        "during",
        "each",
        "from",
        "have",
        "here",
        "into",
        "just",
        "label",
        "learn",
        "like",
        "memory",
        "more",
        "most",
        "must",
        "never",
        "none",
        "note",
        "only",
        "over",
        "point",
        "prior",
        "retrieve",
        "same",
        "should",
        "some",
        "such",
        "synthetic",
        "synthetic_test_data",
        "test",
        "than",
        "that",
        "them",
        "then",
        "there",
        "they",
        "this",
        "through",
        "under",
        "very",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "will",
        "with",
        "within",
        "without",
        "would",
        "your",
    }
)

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

# Ranking components (documented, integer, deterministic).
SCORE_EXACT_ID = 100
SCORE_STRUCTURED_KEY = 80
SCORE_SOURCE = 70
SCORE_FAILURE_FINGERPRINT = 60
SCORE_LEXICAL_PER_TOKEN = 10
SCORE_LEXICAL_CAP = 50
SCORE_CONTRA_EXPAND = 45
SCORE_RELATED_EXPAND = 35
SCORE_TYPE_COMPAT = 25
SCORE_DOMAIN_BOOST = 5
SCORE_TEMPORAL_BOOST = 3
MIN_STRONG_LEXICAL = 2
# 1-token + same-domain is an anchor only if that token is rare in-domain.
MAX_DOMAIN_DF = 3
# A token seen in this many domains is a generic operation/structure word.
GENERIC_DOMAIN_SPAN = 3
# Cross-domain 2-token overlap needs a domain-specific token (span == 1)
# or at least this many overlapping tokens.
CROSS_DOMAIN_STRONG_OVERLAP = 3

NON_EVIDENTIAL_KINDS = frozenset(
    {
        EpistemicKind.OPINION.value,
        EpistemicKind.PREDICTION.value,
        EpistemicKind.SIMULATION.value,
    }
)
UNKNOWN_FIELD = frozenset({"", "UNKNOWN", "NONE", "N/A", "unknown", "none"})

LESSON_INTENT = frozenset({"learn", "learned", "lesson", "lessons"})
FAILURE_INTENT = frozenset({"fail", "failed", "failure", "failures"})
HISTORY_INTENT = frozenset({"historical", "history", "stale", "superseded", "quarter"})

# Closed inflection table. Not a stemmer; only documented pairs.
INFLECTIONS = {
    "contradicted": "contradict",
    "contradicts": "contradict",
    "failures": "failure",
    "lessons": "lesson",
    "recovered": "recover",
    "recovers": "recover",
    "retried": "retry",
    "retries": "retry",
    "supported": "support",
    "supports": "support",
    "timeouts": "timeout",
}


def evidence_class_for(kind: str) -> str:
    return KIND_TO_EVIDENCE.get(kind, EvidenceClass.UNKNOWN.value)


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


def content_tokens(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in STOPWORDS}


# Type/schema words printed into statements. Not task fingerprints.
SCHEMA_LABELS = frozenset(
    {
        "episodic",
        "experiment",
        "failure",
        "hypothesis",
        "inference",
        "lesson",
        "opinion",
        "prediction",
        "procedure",
        "simulation",
    }
)


def memory_tokens(text: str) -> set[str]:
    return content_tokens(text) - SCHEMA_LABELS


def canonical_token(tok: str) -> str:
    return INFLECTIONS.get(tok, tok)


def canonical_set(toks: Iterable[str]) -> set[str]:
    return {canonical_token(t) for t in toks}


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


@dataclass
class QuerySignals:
    tokens: set[str]
    raw_tokens: set[str]
    wanted_ids: set[str]
    hypothesis_id: str
    experiment_id: str
    intents: frozenset[str]
    fingerprint: str

    @property
    def has_signal(self) -> bool:
        return bool(
            self.wanted_ids
            or self.hypothesis_id
            or self.experiment_id
            or self.tokens
        )


def _intents_from_raw(raw: set[str]) -> frozenset[str]:
    found: set[str] = set()
    if raw & LESSON_INTENT:
        found.add("lesson")
    if raw & FAILURE_INTENT:
        found.add("failure")
    if raw & HISTORY_INTENT:
        found.add("history")
    return frozenset(found)


def normalize_query(task: CognitiveTask) -> QuerySignals:
    raw = tokens(task.question) | tokens(task.objective)
    qtok = content_tokens(task.question) | content_tokens(task.objective)
    hyp = str(task.constraints.get("hypothesis_id") or "").strip()
    exp = str(task.constraints.get("experiment_id") or "").strip()
    wanted = {str(x) for x in task.requested_evidence if str(x).strip()}
    intents = _intents_from_raw(raw)
    fp = "|".join(
        [
            ",".join(sorted(wanted)),
            hyp,
            exp,
            ",".join(sorted(qtok)),
            ",".join(sorted(intents)),
            task.domain,
            task.agent_id,
        ]
    )
    return QuerySignals(
        tokens=qtok,
        raw_tokens=raw,
        wanted_ids=wanted,
        hypothesis_id=hyp,
        experiment_id=exp,
        intents=intents,
        fingerprint=fp,
    )


def _namespace_blocked(task: CognitiveTask, rec: MemoryRecord) -> bool:
    if task.agent_id and rec.agent_namespace and rec.agent_namespace != task.agent_id:
        return True
    # Unscoped queries must not see another agent's private memories.
    if not task.agent_id and rec.agent_namespace:
        return True
    return False


def _explicit_field(value: Any) -> str:
    text = str(value or "").strip()
    if text in UNKNOWN_FIELD or text.upper() in UNKNOWN_FIELD:
        return ""
    return text


def _hard_mismatch(rec: MemoryRecord, task: CognitiveTask) -> str:
    payload = rec.payload if isinstance(rec.payload, dict) else {}
    pairs = (
        ("COMPONENT", task.constraints.get("component"), payload.get("component")),
        ("OPERATION", task.constraints.get("operation"), payload.get("operation")),
        ("FAILURE_TYPE", task.constraints.get("failure_type"), payload.get("failure_type")),
    )
    for name, qv, mv in pairs:
        q = _explicit_field(qv)
        m = _explicit_field(mv)
        if q and m and canonical_token(q.lower()) != canonical_token(m.lower()):
            return f"HARD_MISMATCH_{name}"
    if rec.epistemic_kind == EpistemicKind.LESSON.value:
        app = _explicit_field(payload.get("applicability"))
        if app and task.domain and app != task.domain:
            return "HARD_MISMATCH_APPLICABILITY"
    return ""


def _token_domain_span(records: list[MemoryRecord]) -> dict[str, int]:
    domains: dict[str, set[str]] = {}
    for rec in records:
        if rec.agent_namespace:
            continue
        for tok in canonical_set(memory_tokens(rec.statement)):
            domains.setdefault(tok, set()).add(rec.domain)
    return {tok: len(ds) for tok, ds in domains.items()}


def _failure_keys(rec: MemoryRecord) -> set[str]:
    payload = rec.payload if isinstance(rec.payload, dict) else {}
    blob = " ".join(
        str(payload.get(k) or "")
        for k in ("failure_type", "component", "observed_failure", "attempted_action")
    )
    return memory_tokens(rec.statement) | memory_tokens(blob)


def _lexical_overlap(rec: MemoryRecord, qtok: set[str]) -> set[str]:
    return canonical_set(memory_tokens(rec.statement)) & canonical_set(qtok)


def _domain_document_frequency(records: list[MemoryRecord]) -> dict[tuple[str, str], int]:
    df: dict[tuple[str, str], int] = {}
    for rec in records:
        for tok in canonical_set(memory_tokens(rec.statement)):
            key = (rec.domain, tok)
            df[key] = df.get(key, 0) + 1
    return df


def _rare_in_domain(overlap: set[str], domain: str, df: dict[tuple[str, str], int]) -> bool:
    if len(overlap) != 1:
        return False
    tok = next(iter(overlap))
    return df.get((domain, tok), 0) <= MAX_DOMAIN_DF


def _type_compatibility(rec: MemoryRecord, signals: QuerySignals) -> bool:
    if "lesson" in signals.intents and rec.epistemic_kind == EpistemicKind.LESSON.value:
        return True
    if "failure" in signals.intents and rec.memory_type == MemoryType.FAILURE.value:
        return True
    if "history" in signals.intents and rec.status in {
        DecayState.STALE.value,
        DecayState.SUPERSEDED.value,
        DecayState.ARCHIVED.value,
    }:
        return True
    return False


@dataclass
class Rejection:
    memory_id: str
    reason: str


@dataclass
class RelevanceVector:
    identity: int = 0
    structured: int = 0
    lexical: int = 0
    domain: int = 0
    relationship: int = 0
    temporal: int = 0
    hard_mismatch: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "identity": self.identity,
            "structured": self.structured,
            "lexical": self.lexical,
            "domain": self.domain,
            "relationship": self.relationship,
            "temporal": self.temporal,
            "hard_mismatch": self.hard_mismatch,
        }


@dataclass
class RetrievalResult:
    items: list[RetrievedItem]
    rejected: list[Rejection] = field(default_factory=list)
    query_fingerprint: str = ""
    candidate_count: int = 0
    accepted_count: int = 0
    no_relevant_memory: bool = False
    vectors: dict[str, dict[str, int]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [i.as_dict() for i in self.items],
            "rejected": [{"memory_id": r.memory_id, "reason": r.reason} for r in self.rejected],
            "query_fingerprint": self.query_fingerprint,
            "candidate_count": self.candidate_count,
            "accepted_count": self.accepted_count,
            "no_relevant_memory": self.no_relevant_memory,
            "vectors": dict(self.vectors),
        }


class MemoryRetriever:
    """Two-stage deterministic retrieval: anchors, then relationship expansion."""

    def retrieve(
        self,
        store: CognitiveMemoryStore,
        task: CognitiveTask,
        *,
        scan_limit: int = 500,
        now: float | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedItem]:
        return self.retrieve_explained(
            store, task, scan_limit=scan_limit, now=now, top_k=top_k
        ).items

    def retrieve_explained(
        self,
        store: CognitiveMemoryStore,
        task: CognitiveTask,
        *,
        scan_limit: int = 500,
        now: float | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        signals = normalize_query(task)
        recent = store.recent(limit=scan_limit)
        rejected: list[Rejection] = []
        if not signals.has_signal:
            for rec in recent:
                if _namespace_blocked(task, rec):
                    rejected.append(Rejection(rec.memory_id, "NAMESPACE_BLOCKED"))
                else:
                    rejected.append(Rejection(rec.memory_id, "NO_QUERY_SIGNAL"))
            return RetrievalResult(
                items=[],
                rejected=rejected,
                query_fingerprint=signals.fingerprint,
                candidate_count=len(recent),
                accepted_count=0,
                no_relevant_memory=True,
            )

        by_id = {rec.memory_id: rec for rec in recent}
        anchors: dict[str, list[str]] = {}
        scores: dict[str, int] = {}
        vectors: dict[str, RelevanceVector] = {}
        visible = [rec for rec in recent if not _namespace_blocked(task, rec)]
        domain_df = _domain_document_frequency(visible)
        domain_span = _token_domain_span(visible)

        for rec in recent:
            if _namespace_blocked(task, rec):
                rejected.append(Rejection(rec.memory_id, "NAMESPACE_BLOCKED"))
                continue
            reasons, score, rejection, vec = self._anchor_reasons(
                rec,
                task,
                signals,
                now=now,
                domain_df=domain_df,
                domain_span=domain_span,
            )
            if reasons:
                anchors[rec.memory_id] = reasons
                scores[rec.memory_id] = score
                vectors[rec.memory_id] = vec
            else:
                rejected.append(Rejection(rec.memory_id, rejection or "BELOW_RELEVANCE_THRESHOLD"))
                if vec.hard_mismatch:
                    vectors[rec.memory_id] = vec

        # Stage B: expand only from relevant anchors (one hop).
        expanded: dict[str, list[str]] = {}
        for aid in list(anchors):
            rec = by_id.get(aid) or store.get(aid)
            if rec is None:
                continue
            for edge in store.find_contradictions(aid):
                other = edge.to_id if edge.from_id == aid else edge.from_id
                other_rec = by_id.get(other) or store.get(other)
                if other_rec is None:
                    continue
                if _namespace_blocked(task, other_rec):
                    rejected.append(Rejection(other, "NAMESPACE_BLOCKED"))
                    continue
                if other not in anchors and other not in expanded:
                    expanded[other] = ["contradiction_of_relevant_memory"]
                    scores[other] = scores.get(other, 0) + SCORE_CONTRA_EXPAND
                    by_id.setdefault(other, other_rec)
                    vectors.setdefault(other, RelevanceVector()).relationship = 1
            for rel in store.find_related_memories(aid):
                if _namespace_blocked(task, rel):
                    rejected.append(Rejection(rel.memory_id, "NAMESPACE_BLOCKED"))
                    continue
                if rel.memory_id in anchors or rel.memory_id in expanded:
                    continue
                # One-hop related expansion: only SUPERSEDES / SUPPORTS / DERIVED, still anchored.
                expanded[rel.memory_id] = ["related_to_relevant_memory"]
                scores[rel.memory_id] = scores.get(rel.memory_id, 0) + SCORE_RELATED_EXPAND
                by_id.setdefault(rel.memory_id, rel)
                vectors.setdefault(rel.memory_id, RelevanceVector()).relationship = 1

        accepted_ids = set(anchors) | set(expanded)
        items: list[RetrievedItem] = []
        for mid in accepted_ids:
            rec = by_id[mid]
            reasons = list(anchors.get(mid) or []) + list(expanded.get(mid) or [])
            vec = vectors.setdefault(mid, RelevanceVector())
            if rec.domain == task.domain:
                reasons.append("same_domain")
                scores[mid] = scores.get(mid, 0) + SCORE_DOMAIN_BOOST
                vec.domain = 1
            if rec.status == DecayState.STALE.value:
                reasons.append("stale_but_queryable")
            type_reason = _type_compatibility(rec, signals)
            if type_reason:
                reasons.append("type_compatibility")
                scores[mid] = scores.get(mid, 0) + SCORE_TYPE_COMPAT
            if now is not None and rec.observed_at is not None:
                window = float(task.constraints.get("temporal_window_sec") or 0)
                if window > 0 and abs(now - rec.observed_at) <= window:
                    reasons.append("temporal_proximity")
                    scores[mid] = scores.get(mid, 0) + SCORE_TEMPORAL_BOOST
                    vec.temporal = 1
            items.append(_item(rec, reasons))

        items.sort(key=lambda i: (-scores.get(i.memory_id, 0), i.memory_id))
        if top_k is not None:
            items = items[: max(0, int(top_k))]

        # Drop rejections that were later accepted via expansion.
        accepted_set = {i.memory_id for i in items}
        rejected = [r for r in rejected if r.memory_id not in accepted_set]
        rejected.sort(key=lambda r: (r.reason, r.memory_id))

        return RetrievalResult(
            items=items,
            rejected=rejected,
            query_fingerprint=signals.fingerprint,
            candidate_count=len(recent),
            accepted_count=len(items),
            no_relevant_memory=len(items) == 0,
            vectors={mid: vectors[mid].as_dict() for mid in accepted_set if mid in vectors},
        )

    def _anchor_reasons(
        self,
        rec: MemoryRecord,
        task: CognitiveTask,
        signals: QuerySignals,
        *,
        now: float | None,
        domain_df: dict[tuple[str, str], int],
        domain_span: dict[str, int],
    ) -> tuple[list[str], int, str, RelevanceVector]:
        vec = RelevanceVector()
        mismatch = _hard_mismatch(rec, task)
        if mismatch:
            vec.hard_mismatch = 1
            return [], 0, mismatch, vec

        reasons: list[str] = []
        score = 0
        overlap = _lexical_overlap(rec, signals.tokens)
        structured = False

        if rec.memory_id in signals.wanted_ids:
            reasons.append("exact_id")
            score += SCORE_EXACT_ID
            vec.identity = 1
            structured = True
        if signals.hypothesis_id and rec.hypothesis_id == signals.hypothesis_id:
            reasons.append("same_hypothesis")
            score += SCORE_STRUCTURED_KEY
            vec.structured = 1
            structured = True
        if signals.experiment_id and rec.experiment_id == signals.experiment_id:
            reasons.append("same_experiment")
            score += SCORE_STRUCTURED_KEY
            vec.structured = 1
            structured = True
        if rec.source_id and rec.source_id.lower() in (task.question or "").lower():
            reasons.append("source_relationship")
            score += SCORE_SOURCE
            vec.structured = 1
            structured = True

        # Namespaced query: shared (empty-namespace) rows need a structured key.
        if task.agent_id and not rec.agent_namespace and not structured:
            return [], 0, "SHARED_WITHOUT_NAMESPACE_SCOPE", vec

        has_structured_query = bool(
            signals.wanted_ids or signals.hypothesis_id or signals.experiment_id
        )
        allow_lexical = not has_structured_query or structured

        generic_ops = {tok for tok, span in domain_span.items() if span >= GENERIC_DOMAIN_SPAN}
        q_ops = canonical_set(signals.tokens) & generic_ops
        ov_ops = overlap & generic_ops
        specific_overlap = any(domain_span.get(tok, 0) <= 1 for tok in overlap)
        cross_domain = rec.domain != task.domain

        strong_lexical = len(overlap) >= MIN_STRONG_LEXICAL
        if cross_domain and strong_lexical:
            strong_lexical = len(overlap) >= CROSS_DOMAIN_STRONG_OVERLAP or specific_overlap
        weak_same_domain = rec.domain == task.domain and _rare_in_domain(
            overlap, rec.domain, domain_df
        )
        lookalike = bool(
            q_ops and not ov_ops and len(overlap) < CROSS_DOMAIN_STRONG_OVERLAP and not structured
        )
        if lookalike:
            strong_lexical = False
            weak_same_domain = False

        lexical_ok = allow_lexical and (strong_lexical or weak_same_domain)
        if rec.epistemic_kind in NON_EVIDENTIAL_KINDS and not structured:
            lexical_ok = False
        if "lesson" in signals.intents and rec.epistemic_kind != EpistemicKind.LESSON.value:
            if not structured:
                lexical_ok = False
        if "failure" in signals.intents and rec.memory_type != MemoryType.FAILURE.value:
            if not structured:
                lexical_ok = False

        if lexical_ok:
            reasons.append("task_keyword_match")
            score += min(SCORE_LEXICAL_CAP, SCORE_LEXICAL_PER_TOKEN * len(overlap))
            vec.lexical = len(overlap)
            if rec.epistemic_kind == EpistemicKind.LESSON.value:
                reasons.append("lesson_keyword_match")

        if rec.memory_type == MemoryType.FAILURE.value and allow_lexical:
            fail_overlap = canonical_set(_failure_keys(rec)) & canonical_set(signals.tokens)
            strong_fail = len(fail_overlap) >= MIN_STRONG_LEXICAL
            if cross_domain and strong_fail:
                strong_fail = len(fail_overlap) >= CROSS_DOMAIN_STRONG_OVERLAP or any(
                    domain_span.get(tok, 0) <= 1 for tok in fail_overlap
                )
            weak_fail_same_domain = rec.domain == task.domain and _rare_in_domain(
                fail_overlap, rec.domain, domain_df
            )
            if (strong_fail or weak_fail_same_domain) and not lookalike:
                if "failure" in signals.intents or "lesson" not in signals.intents:
                    reasons.append("failure_fingerprint")
                    score += SCORE_FAILURE_FINGERPRINT
                    vec.structured = max(vec.structured, 1)

        if reasons:
            return reasons, score, "", vec

        if lookalike:
            return [], 0, "GENERIC_LOOKALIKE", vec
        if cross_domain and overlap:
            return [], 0, "CROSS_DOMAIN_GENERIC_OVERLAP", vec
        if rec.epistemic_kind in NON_EVIDENTIAL_KINDS and overlap:
            return [], 0, "NON_EVIDENTIAL_KIND", vec
        if "lesson" in signals.intents and rec.epistemic_kind != EpistemicKind.LESSON.value:
            return [], 0, "LESSON_APPLICABILITY_MISMATCH", vec
        if "failure" in signals.intents and rec.memory_type != MemoryType.FAILURE.value:
            return [], 0, "UNRELATED_FAILURE", vec
        if has_structured_query and overlap:
            return [], 0, "STRUCTURED_QUERY_LEXICAL_LOOKALIKE", vec
        if rec.domain == task.domain:
            return [], 0, "DOMAIN_ONLY", vec
        if rec.memory_type == MemoryType.FAILURE.value:
            return [], 0, "UNRELATED_FAILURE", vec
        if rec.contradiction_state and rec.contradiction_state not in {"UNCONTESTED", "UNKNOWN"}:
            return [], 0, "UNRELATED_CONTRADICTION", vec
        if overlap:
            return [], 0, "WEAK_LEXICAL_OVERLAP", vec
        return [], 0, "BELOW_RELEVANCE_THRESHOLD", vec
