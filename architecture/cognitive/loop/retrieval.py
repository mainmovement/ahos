"""Explainable deterministic retrieval over P2 memory. No embeddings.

P4.2: contextual signals (same_domain, unanchored edges, mere FAILURE type,
stale/recency) are not sufficient alone. Relationships expand relevance from
anchors; they do not create it from nothing.
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

LESSON_INTENT = frozenset({"learn", "learned", "lesson", "lessons"})
FAILURE_INTENT = frozenset({"fail", "failed", "failure", "failures"})
HISTORY_INTENT = frozenset({"historical", "history", "stale", "superseded", "quarter"})


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
    return bool(task.agent_id and rec.agent_namespace and rec.agent_namespace != task.agent_id)


def _failure_keys(rec: MemoryRecord) -> set[str]:
    payload = rec.payload if isinstance(rec.payload, dict) else {}
    blob = " ".join(
        str(payload.get(k) or "")
        for k in ("failure_type", "component", "observed_failure", "attempted_action")
    )
    return memory_tokens(rec.statement) | memory_tokens(blob)


def _lexical_overlap(rec: MemoryRecord, qtok: set[str]) -> set[str]:
    return memory_tokens(rec.statement) & qtok


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
class RetrievalResult:
    items: list[RetrievedItem]
    rejected: list[Rejection] = field(default_factory=list)
    query_fingerprint: str = ""
    candidate_count: int = 0
    accepted_count: int = 0
    no_relevant_memory: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [i.as_dict() for i in self.items],
            "rejected": [{"memory_id": r.memory_id, "reason": r.reason} for r in self.rejected],
            "query_fingerprint": self.query_fingerprint,
            "candidate_count": self.candidate_count,
            "accepted_count": self.accepted_count,
            "no_relevant_memory": self.no_relevant_memory,
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

        for rec in recent:
            if _namespace_blocked(task, rec):
                rejected.append(Rejection(rec.memory_id, "NAMESPACE_BLOCKED"))
                continue
            reasons, score, rejection = self._anchor_reasons(rec, task, signals, now=now)
            if reasons:
                anchors[rec.memory_id] = reasons
                scores[rec.memory_id] = score
            else:
                rejected.append(Rejection(rec.memory_id, rejection or "BELOW_RELEVANCE_THRESHOLD"))

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

        accepted_ids = set(anchors) | set(expanded)
        items: list[RetrievedItem] = []
        for mid in accepted_ids:
            rec = by_id[mid]
            reasons = list(anchors.get(mid) or []) + list(expanded.get(mid) or [])
            if rec.domain == task.domain:
                reasons.append("same_domain")
                scores[mid] = scores.get(mid, 0) + SCORE_DOMAIN_BOOST
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
        )

    def _anchor_reasons(
        self,
        rec: MemoryRecord,
        task: CognitiveTask,
        signals: QuerySignals,
        *,
        now: float | None,
    ) -> tuple[list[str], int, str]:
        reasons: list[str] = []
        score = 0
        overlap = _lexical_overlap(rec, signals.tokens)

        if rec.memory_id in signals.wanted_ids:
            reasons.append("exact_id")
            score += SCORE_EXACT_ID
        if signals.hypothesis_id and rec.hypothesis_id == signals.hypothesis_id:
            reasons.append("same_hypothesis")
            score += SCORE_STRUCTURED_KEY
        if signals.experiment_id and rec.experiment_id == signals.experiment_id:
            reasons.append("same_experiment")
            score += SCORE_STRUCTURED_KEY
        if rec.source_id and rec.source_id.lower() in (task.question or "").lower():
            reasons.append("source_relationship")
            score += SCORE_SOURCE
        strong_lexical = len(overlap) >= MIN_STRONG_LEXICAL
        weak_same_domain = len(overlap) == 1 and rec.domain == task.domain
        if strong_lexical or weak_same_domain:
            reasons.append("task_keyword_match")
            score += min(SCORE_LEXICAL_CAP, SCORE_LEXICAL_PER_TOKEN * len(overlap))
            if rec.epistemic_kind == EpistemicKind.LESSON.value:
                reasons.append("lesson_keyword_match")
        if rec.memory_type == MemoryType.FAILURE.value:
            fail_overlap = _failure_keys(rec) & signals.tokens
            strong_fail = len(fail_overlap) >= MIN_STRONG_LEXICAL
            weak_fail_same_domain = len(fail_overlap) == 1 and rec.domain == task.domain
            if strong_fail or weak_fail_same_domain:
                reasons.append("failure_fingerprint")
                score += SCORE_FAILURE_FINGERPRINT

        if reasons:
            return reasons, score, ""

        # Rejection classification (not relevance).
        if rec.domain == task.domain:
            return [], 0, "DOMAIN_ONLY"
        if rec.memory_type == MemoryType.FAILURE.value:
            return [], 0, "UNRELATED_FAILURE"
        if rec.contradiction_state and rec.contradiction_state not in {"UNCONTESTED", "UNKNOWN"}:
            return [], 0, "UNRELATED_CONTRADICTION"
        if overlap:
            return [], 0, "WEAK_LEXICAL_OVERLAP"
        return [], 0, "BELOW_RELEVANCE_THRESHOLD"
