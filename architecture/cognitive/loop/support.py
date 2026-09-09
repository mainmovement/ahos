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
POLARITY_NEUTRAL = "NEUTRAL"
POLARITY_UNKNOWN = "UNKNOWN"

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
# Intentionally excludes cafeteria/kitchen/seating/lunch and other fixture nouns.
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


@dataclass(frozen=True)
class SupportAssessment:
    support_class: str
    polarity: str
    reason: str
    lexical_match: bool
    subject_overlap: tuple[str, ...]
    alien_tokens: tuple[str, ...]

    def may_support_positive(self) -> bool:
        return self.support_class == SUPPORT_DIRECT and self.polarity == POLARITY_SUPPORTS

    def blocks_positive(self) -> bool:
        return self.support_class in {SUPPORT_NON, SUPPORT_UNKNOWN}


def _task_tokens(task: CognitiveTask) -> set[str]:
    return canonical_set(content_tokens(task.question) | content_tokens(task.objective))


def _polarity(toks: set[str]) -> str:
    has_reduce = bool(toks & _REDUCE)
    has_increase = bool(toks & _INCREASE)
    has_fail = bool(toks & _FAIL)
    has_help = bool(toks & _HELP)
    has_harm = bool(toks & _HARM)
    pos = 0
    neg = 0
    if has_reduce and has_fail:
        pos += 1
    if has_increase and has_fail:
        neg += 1
    if has_help and not has_harm:
        pos += 1
    if has_harm:
        neg += 1
    if has_fail and not has_reduce and not has_help:
        neg += 1
    if pos and neg:
        return POLARITY_UNKNOWN
    if pos:
        return POLARITY_SUPPORTS
    if neg:
        return POLARITY_CONTRADICTS
    return POLARITY_NEUTRAL


def _about_redirect(statement: str, task_toks: set[str]) -> bool:
    blob = f" {(statement or '').lower()} "
    for marker in _ABOUT_MARKERS:
        if marker not in blob:
            continue
        after = blob.split(marker, 1)[1]
        after_toks = canonical_set(content_tokens(after)) - task_toks - SCHEMA_LABELS
        if after_toks:
            return True
    return False


def classify_support(statement: str, task: CognitiveTask) -> SupportAssessment:
    """Classify whether a statement supports the task proposition.

    Lexical overlap only creates a candidate. DIRECT_SUPPORT additionally
    requires subject overlap, a closed evaluative/outcome cue, no about-
    redirect, no missing task-domain qualifier, and no alien nouns.
    Anything short of that is INDIRECT, CONTEXT_ONLY, NON_SUPPORTING_MATCH,
    or UNKNOWN_SUPPORT — never pretended entailment.
    """
    task_toks = _task_tokens(task)
    evid_raw = content_tokens(statement)
    evid_toks = canonical_set(evid_raw)
    overlap = evid_toks & task_toks
    subject_task = task_toks - canonical_set(_EVALUATIVE)
    subject_overlap = overlap & (subject_task | canonical_set(_ACTION | _PROBLEM))
    polarity = _polarity(evid_toks)
    unique = evid_toks - task_toks
    alien = tuple(
        sorted(
            unique
            - canonical_set(_EVALUATIVE)
            - canonical_set(_IN_FAMILY)
            - canonical_set(STOPWORDS)
            - SCHEMA_LABELS
        )
    )
    redirect = _about_redirect(statement, task_toks)
    task_qual = _DOMAIN_QUALIFIERS & task_toks
    evid_qual = _DOMAIN_QUALIFIERS & evid_toks
    domain_miss = bool(task_qual) and not bool(task_qual & evid_qual)
    lexical = bool(overlap)

    if not lexical:
        return SupportAssessment(
            SUPPORT_UNKNOWN,
            POLARITY_NEUTRAL,
            "no lexical overlap; not a support candidate",
            False,
            (),
            alien,
        )
    if redirect:
        return SupportAssessment(
            SUPPORT_NON,
            POLARITY_NEUTRAL,
            "about-redirect: overlap is a different subject, not support",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    if domain_miss:
        return SupportAssessment(
            SUPPORT_NON,
            POLARITY_NEUTRAL,
            "task domain qualifier absent from evidence; lexical cousin",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    if subject_overlap and polarity in {POLARITY_SUPPORTS, POLARITY_CONTRADICTS} and not alien:
        return SupportAssessment(
            SUPPORT_DIRECT,
            polarity,
            "subject overlap plus closed evaluative cue; not formal entailment",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    if subject_overlap and polarity in {POLARITY_SUPPORTS, POLARITY_CONTRADICTS} and alien:
        return SupportAssessment(
            SUPPORT_UNKNOWN,
            POLARITY_UNKNOWN,
            "evaluative cue plus alien nouns; cannot prove same proposition",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    problem_only = bool(subject_overlap & canonical_set(_PROBLEM)) and not (
        evid_toks & canonical_set(_ACTION)
    )
    if subject_overlap and polarity == POLARITY_NEUTRAL and problem_only:
        return SupportAssessment(
            SUPPORT_CONTEXT,
            POLARITY_NEUTRAL,
            "problem context only; no action+outcome support",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    if subject_overlap and polarity == POLARITY_NEUTRAL and not alien:
        return SupportAssessment(
            SUPPORT_INDIRECT,
            POLARITY_NEUTRAL,
            "related mention without an evaluative outcome",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    if subject_overlap and polarity == POLARITY_NEUTRAL and alien:
        return SupportAssessment(
            SUPPORT_NON,
            POLARITY_NEUTRAL,
            "lexical overlap with alien content and no evaluative support",
            True,
            tuple(sorted(subject_overlap)),
            alien,
        )
    return SupportAssessment(
        SUPPORT_UNKNOWN,
        POLARITY_UNKNOWN,
        "lexical candidate; deterministic support not established",
        True,
        tuple(sorted(subject_overlap or overlap)),
        alien,
    )


def raw_token_overlap(statement: str, task: CognitiveTask) -> set[str]:
    return tokens(statement) & (tokens(task.question) | tokens(task.objective))
