"""Deterministic evidence-support assessment. Not entailment. Not embeddings.

Layer:
    retrieval relevance → evidence eligibility → task-support assessment → reasoning

This module answers: does this statement give deterministic *support* for the
task proposition, or only a lexical candidate?

It does not:
    - embed text, call an LLM, or use an external semantic API
    - hardcode case IDs or fixture-specific phrases
    - claim formal entailment or a world model

Rules enforced by callers:
    LEXICAL_MATCH != EVIDENCE_SUPPORT
    RELEVANCE != ENTAILMENT
    ELIGIBLE_EVIDENCE != SUFFICIENT_EVIDENCE

If support cannot be proven from closed lexicons + structural cues, the
class is UNKNOWN_SUPPORT and positive verdicts must be refused (P6 gap).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from architecture.cognitive.loop.contracts import CognitiveTask
from architecture.cognitive.loop.retrieval import (
    SCHEMA_LABELS,
    STOPWORDS,
    canonical_set,
    content_tokens,
    tokens,
)

SUPPORT_DIRECT = "DIRECT_SUPPORT"
SUPPORT_INDIRECT = "INDIRECT_SUPPORT"
SUPPORT_CONTEXT = "CONTEXT_ONLY"
SUPPORT_NON = "NON_SUPPORTING_MATCH"
SUPPORT_UNKNOWN = "UNKNOWN_SUPPORT"

POLARITY_SUPPORTS = "SUPPORTS"
POLARITY_CONTRADICTS = "CONTRADICTS"
POLARITY_NEGATED = "NEGATED"
POLARITY_UNCERTAIN = "UNCERTAIN"
POLARITY_NEUTRAL = "NEUTRAL"
POLARITY_UNKNOWN = "UNKNOWN"

ENTITY_NONE = "NONE"
ENTITY_MATCH = "MATCH"
ENTITY_MISMATCH = "MISMATCH"
ENTITY_AMBIGUOUS = "AMBIGUOUS"
ENTITY_SCOPED = "SCOPED"

CLAUSE_AFFIRMED = "AFFIRMED"
CLAUSE_NEGATED = "NEGATED"
CLAUSE_UNCERTAIN = "UNCERTAIN"

# Clause-level cues scanned on raw text. Independent of the 4+ retrieval tokenizer
# so "not" / "no" / "never" cannot be deleted before polarity is decided.
_UNCERTAIN_RE = re.compile(
    r"\b("
    r"unknown whether|it is unknown|uncertain whether|"
    r"no evidence that|there is no evidence|not known whether|"
    r"unclear whether|no evidence"
    r")\b",
    re.IGNORECASE,
)
_NEGATION_RE = re.compile(
    r"\b("
    r"did not|does not|do not|didn't|doesn't|don't|"
    r"never|failed to|fail to|fails to|"
    r"cannot|can't|unable to|without|"
    r"not"
    r")\b",
    re.IGNORECASE,
)

# Identity markers kept even when length < 4. Not a named-entity ontology.
_SINGLE_ID = re.compile(r"(?<![A-Za-z0-9])([A-Z])(?![A-Za-z0-9])")
_ALNUM_ID = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]+[0-9]+)(?![A-Za-z0-9])")
_COMPOUND_ID = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+)(?![A-Za-z0-9])"
)
_TITLE_ID = re.compile(r"(?<![A-Za-z0-9])([A-Z][a-z]{2,})(?![A-Za-z0-9])")

# Domain-general evaluative tokens. Not a sentiment model; composition is closed.
_POSITIVE_EVAL = frozenset(
    {
        "benefit",
        "beneficial",
        "effective",
        "help",
        "helped",
        "helpful",
        "helps",
        "improve",
        "improved",
        "improvement",
        "recover",
        "recovered",
        "recovers",
        "recovery",
        "reduce",
        "reduced",
        "reduction",
        "success",
        "successful",
        "support",
        "supported",
        "supports",
        "worked",
    }
)
_NEGATIVE_EVAL = frozenset(
    {
        "contradict",
        "contradicted",
        "contradicts",
        "fail",
        "failed",
        "failure",
        "failures",
        "harm",
        "harmed",
        "increase",
        "increased",
        "increases",
        "ineffective",
        "useless",
        "worse",
        "worsened",
    }
)
_EVALUATIVE = _POSITIVE_EVAL | _NEGATIVE_EVAL

_REDUCE = frozenset({"reduce", "reduced", "reduction", "fewer"})
_INCREASE = frozenset({"increase", "increased", "increases"})
_FAIL = frozenset({"fail", "failed", "failure", "failures"})
_HELP = frozenset(_POSITIVE_EVAL - _REDUCE)
_HARM = frozenset(
    {
        "contradict",
        "contradicted",
        "contradicts",
        "harm",
        "harmed",
        "ineffective",
        "useless",
        "worse",
        "worsened",
    }
)

# Closed technical / in-family vocabulary. Unexpected nouns stay alien.
# The set is not expanded to recover recall on out-of-family wording.
_IN_FAMILY = frozenset(
    {
        "api",
        "availability",
        "cache",
        "calibration",
        "client",
        "cluster",
        "component",
        "connection",
        "database",
        "deploy",
        "depth",
        "disk",
        "dns",
        "endpoint",
        "error",
        "finance",
        "format",
        "http",
        "https",
        "latency",
        "logging",
        "measurement",
        "node",
        "observation",
        "operations",
        "packet",
        "page",
        "policy",
        "process",
        "production",
        "queue",
        "reliability",
        "replica",
        "request",
        "requests",
        "response",
        "revision",
        "rollback",
        "science",
        "server",
        "service",
        "session",
        "socket",
        "software",
        "sql",
        "system",
        "tcp",
        "thread",
        "token",
        "udp",
        "worker",
        "write",
    }
)

_ACTION = frozenset({"retry", "retries", "retried"})
_PROBLEM = frozenset({"error", "fail", "failed", "failure", "failures", "timeout", "timeouts"})
_DOMAIN_QUALIFIERS = frozenset({"dns", "http", "https", "sql", "tcp", "udp"})
_ABOUT_MARKERS = (" about ", " regarding ", " concerning ")
_POLARITY_SURFACE = frozenset(
    {
        "cannot",
        "unable",
        "without",
        "never",
        "dont",
        "didnt",
        "doesnt",
        "unknown",
        "uncertain",
        "unclear",
    }
)
_AGENT_BEFORE_REDUCE_FAIL = re.compile(
    r"\b(?:retry|retries|retried)\b.{0,160}"
    r"\b(?:reduce|reduced|reduction|reducing)\b.{0,160}"
    r"\b(?:fail|failed|failure|failures)\b",
    re.IGNORECASE,
)

# Interrogative/auxiliary surface forms. Title-case sentence starts ("Did",
# "Can") are not identity assertions. Not a fixture list.
_IDENTITY_FUNCTION_WORDS = frozenset(
    {
        "are",
        "be",
        "been",
        "being",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "had",
        "has",
        "have",
        "having",
        "how",
        "is",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "was",
        "were",
        "what",
        "when",
        "which",
        "who",
        "whom",
        "whose",
        "why",
        "will",
        "would",
    }
)

# Identity tokens that are synthetic-corpus labels, not subjects.
_IDENTITY_BLOCKLIST = (
    frozenset({"synthetic_test_data"})
    | SCHEMA_LABELS
    | STOPWORDS
    | _ACTION
    | _PROBLEM
    | _EVALUATIVE
    | _IN_FAMILY
    | _DOMAIN_QUALIFIERS
    | _IDENTITY_FUNCTION_WORDS
)


@dataclass(frozen=True)
class SupportAssessment:
    support_class: str
    polarity: str
    clause_force: str
    entity_state: str
    evidence_entities: tuple[str, ...]
    task_entities: tuple[str, ...]
    reason: str
    subject_overlap: tuple[str, ...]
    object_overlap: tuple[str, ...]
    alien_tokens: tuple[str, ...]
    lexical_match: bool = False

    def may_support_positive(self) -> bool:
        return positive_support_eligible(self)

    def blocks_positive(self) -> bool:
        return not self.may_support_positive()

    def as_dict(self) -> dict[str, object]:
        return {
            "support_class": self.support_class,
            "polarity": self.polarity,
            "clause_force": self.clause_force,
            "entity_state": self.entity_state,
            "evidence_entities": list(self.evidence_entities),
            "task_entities": list(self.task_entities),
            "reason": self.reason,
            "subject_overlap": list(self.subject_overlap),
            "object_overlap": list(self.object_overlap),
            "alien_tokens": list(self.alien_tokens),
            "lexical_match": self.lexical_match,
        }


def positive_support_eligible(assessment: SupportAssessment) -> bool:
    """NEGATED / UNCERTAIN / MISMATCH / AMBIGUOUS / SCOPED cannot satisfy positives."""
    if assessment.support_class != SUPPORT_DIRECT:
        return False
    if assessment.polarity != POLARITY_SUPPORTS:
        return False
    if assessment.clause_force in {CLAUSE_NEGATED, CLAUSE_UNCERTAIN}:
        return False
    if assessment.entity_state in {ENTITY_MISMATCH, ENTITY_AMBIGUOUS, ENTITY_SCOPED}:
        return False
    return True


def _clause_force(raw: str) -> str:
    if _UNCERTAIN_RE.search(raw or ""):
        return CLAUSE_UNCERTAIN
    if _NEGATION_RE.search(raw or ""):
        return CLAUSE_NEGATED
    return CLAUSE_AFFIRMED


def _bag_polarity(evidence_tok: set[str], raw: str = "") -> str:
    has_reduce = bool(evidence_tok & _REDUCE)
    has_increase = bool(evidence_tok & _INCREASE)
    has_fail = bool(evidence_tok & _FAIL)
    has_help = bool(evidence_tok & _HELP)
    has_harm = bool(evidence_tok & _HARM)
    if has_reduce and has_fail:
        if has_increase or has_harm:
            return POLARITY_UNKNOWN
        if not _AGENT_BEFORE_REDUCE_FAIL.search(raw or ""):
            return POLARITY_UNKNOWN
        return POLARITY_SUPPORTS
    if has_help:
        if has_increase or has_harm:
            return POLARITY_UNKNOWN
        return POLARITY_SUPPORTS
    if has_increase or has_harm:
        return POLARITY_CONTRADICTS
    return POLARITY_NEUTRAL


def _combine_polarity(force: str, bag: str) -> str:
    if force == CLAUSE_UNCERTAIN:
        return POLARITY_UNCERTAIN
    if force == CLAUSE_NEGATED:
        if bag == POLARITY_CONTRADICTS:
            return POLARITY_UNKNOWN
        return POLARITY_NEGATED
    return bag


def identity_tokens(text: str) -> frozenset[str]:
    """Extract short/compound IDs the 4+ tokenizer would drop. Not NER."""
    found: set[str] = set()
    for match in _SINGLE_ID.finditer(text or ""):
        found.add(match.group(1).lower())
    for match in _ALNUM_ID.finditer(text or ""):
        found.add(match.group(1).lower())
    for match in _COMPOUND_ID.finditer(text or ""):
        found.add(match.group(1).lower())
    for match in _TITLE_ID.finditer(text or ""):
        found.add(match.group(1).lower())
    return frozenset(t for t in found if t not in _IDENTITY_BLOCKLIST)


def entity_alignment(evidence_ids: frozenset[str], task_ids: frozenset[str]) -> str:
    """Compatibility of identity markers. Not NER.

    NONE: neither side carries markers (genuinely unscoped / global).
    SCOPED: evidence is entity-specific, task is not — not automatic support.
    AMBIGUOUS: task asks about an ID the evidence does not carry.
    MATCH / MISMATCH: both sides carry markers.
    """
    if not task_ids and not evidence_ids:
        return ENTITY_NONE
    if not task_ids and evidence_ids:
        return ENTITY_SCOPED
    if task_ids and not evidence_ids:
        return ENTITY_AMBIGUOUS
    if evidence_ids & task_ids:
        return ENTITY_MATCH
    return ENTITY_MISMATCH


def _pack(
    support_class: str,
    polarity: str,
    force: str,
    entity_state: str,
    evidence_ids: frozenset[str],
    task_ids: frozenset[str],
    reason: str,
    subject: set[str],
    obj: set[str],
    alien: set[str],
    lexical_match: bool,
) -> SupportAssessment:
    assessment = SupportAssessment(
        support_class=support_class,
        polarity=polarity,
        clause_force=force,
        entity_state=entity_state,
        evidence_entities=tuple(sorted(evidence_ids)),
        task_entities=tuple(sorted(task_ids)),
        reason=reason,
        subject_overlap=tuple(sorted(subject)),
        object_overlap=tuple(sorted(obj)),
        alien_tokens=tuple(sorted(alien)),
        lexical_match=lexical_match,
    )
    if (
        assessment.support_class == SUPPORT_DIRECT
        and assessment.polarity == POLARITY_SUPPORTS
        and not positive_support_eligible(assessment)
    ):
        return SupportAssessment(
            support_class=SUPPORT_UNKNOWN,
            polarity=POLARITY_UNKNOWN,
            clause_force=force,
            entity_state=entity_state,
            evidence_entities=tuple(sorted(evidence_ids)),
            task_entities=tuple(sorted(task_ids)),
            reason="positive_support_blocked:" + reason,
            subject_overlap=tuple(sorted(subject)),
            object_overlap=tuple(sorted(obj)),
            alien_tokens=tuple(sorted(alien)),
            lexical_match=lexical_match,
        )
    return assessment


def classify_support(evidence_text: str, task: CognitiveTask) -> SupportAssessment:
    ev_raw = evidence_text or ""
    ev = tokens(ev_raw)
    q = tokens(task.question)
    ev_c = canonical_set(ev)
    q_c = canonical_set(q)
    ev_content = content_tokens(ev_raw)
    q_content = content_tokens(task.question)
    overlap = ev_c & q_c
    subject = overlap & (_ACTION | _PROBLEM)
    obj = overlap & _EVALUATIVE
    alien = {
        t
        for t in ev_content
        if t not in _IN_FAMILY
        and t not in _ACTION
        and t not in _PROBLEM
        and t not in _EVALUATIVE
        and t not in _POLARITY_SURFACE
        and t not in q_content
    }

    evidence_ids = identity_tokens(ev_raw)
    task_ids = identity_tokens(task.question)
    entity_state = entity_alignment(evidence_ids, task_ids)
    force = _clause_force(ev_raw)
    bag = _bag_polarity(ev, ev_raw)
    polarity = _combine_polarity(force, bag)

    def _out(support_class: str, pol: str, reason: str) -> SupportAssessment:
        return _pack(
            support_class,
            pol,
            force,
            entity_state,
            evidence_ids,
            task_ids,
            reason,
            subject,
            obj,
            alien,
            bool(overlap),
        )

    if not overlap:
        return _out(SUPPORT_UNKNOWN, POLARITY_UNKNOWN, "no_lexical_overlap")

    if entity_state == ENTITY_MISMATCH:
        return _out(SUPPORT_NON, POLARITY_UNKNOWN, "entity_mismatch")

    if entity_state == ENTITY_AMBIGUOUS:
        return _out(SUPPORT_UNKNOWN, POLARITY_UNKNOWN, "ambiguous_entity")

    if entity_state == ENTITY_SCOPED:
        return _out(SUPPORT_UNKNOWN, POLARITY_UNKNOWN, "entity_scoped_unscoped_task")

    about_redirect = any(m in ev_raw.lower() for m in _ABOUT_MARKERS)
    q_qual = q & _DOMAIN_QUALIFIERS
    ev_qual = ev & _DOMAIN_QUALIFIERS
    domain_miss = bool(q_qual) and not (q_qual & ev_qual)

    if about_redirect:
        return _out(SUPPORT_NON, POLARITY_NEUTRAL, "about_redirect")
    if domain_miss:
        return _out(SUPPORT_NON, POLARITY_NEUTRAL, "domain_mismatch")

    if force == CLAUSE_UNCERTAIN:
        return _out(SUPPORT_UNKNOWN, POLARITY_UNCERTAIN, "uncertain_clause")

    if force == CLAUSE_NEGATED and subject and not alien:
        return _out(SUPPORT_DIRECT, POLARITY_NEGATED, "negated_direct")
    if force == CLAUSE_NEGATED and subject:
        return _out(SUPPORT_UNKNOWN, POLARITY_NEGATED, "negated_with_alien")

    polar_eval = polarity in {POLARITY_SUPPORTS, POLARITY_CONTRADICTS, POLARITY_NEGATED}
    if subject and polar_eval and not alien:
        if polarity == POLARITY_SUPPORTS:
            return _out(SUPPORT_DIRECT, POLARITY_SUPPORTS, "direct_support")
        if polarity == POLARITY_CONTRADICTS:
            return _out(SUPPORT_DIRECT, POLARITY_CONTRADICTS, "direct_contradiction")
        return _out(SUPPORT_DIRECT, polarity, "direct_mixed")
    if subject and polar_eval and alien:
        return _out(SUPPORT_UNKNOWN, POLARITY_UNKNOWN, "evaluative_plus_alien")

    problem_only = bool(subject & _PROBLEM) and not (ev & _ACTION)
    if subject and polarity == POLARITY_NEUTRAL and problem_only:
        return _out(SUPPORT_CONTEXT, POLARITY_NEUTRAL, "context_only")
    if subject and polarity == POLARITY_NEUTRAL and not alien:
        return _out(SUPPORT_INDIRECT, POLARITY_NEUTRAL, "related_without_outcome")
    if subject and polarity == POLARITY_NEUTRAL and alien:
        return _out(SUPPORT_NON, POLARITY_NEUTRAL, "lexical_with_alien")

    if (ev & _EVALUATIVE) and not subject:
        return _out(SUPPORT_INDIRECT, POLARITY_NEUTRAL, "evaluative_without_subject")

    if overlap and not (ev & _EVALUATIVE) and not subject:
        return _out(SUPPORT_NON, POLARITY_NEUTRAL, "lexical_only")

    return _out(SUPPORT_UNKNOWN, POLARITY_UNKNOWN, "unresolved")


def raw_token_overlap(evidence_text: str, question: str) -> int:
    return len(canonical_set(tokens(evidence_text)) & canonical_set(tokens(question)))
