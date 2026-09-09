"""Metric definitions. No fabricated intelligence scores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricSpec:
    name: str
    definition: str
    method: str
    baseline: str
    limitations: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "definition": self.definition,
            "method": self.method,
            "baseline": self.baseline,
            "limitations": self.limitations,
        }


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        "retrieval_precision",
        "Fraction of retrieved items whose match_reasons are non-empty and domain matches the task, among retrieved items.",
        "count(domain==task.domain) / max(len(retrieved), 1) on a labeled synthetic set",
        "unmeasured outside tests; NO_MEMORY baseline has 0 retrieved",
        "Keyword/domain matching is not semantic precision; limitation: synthetic tasks only",
    ),
    MetricSpec(
        "retrieval_recall",
        "Fraction of seeded relevant memory_ids that appear in retrieve().",
        "count(seeded_ids ∩ retrieved_ids) / len(seeded_ids)",
        "unmeasured outside tests",
        "Relevance is the test seed list, not human judgment; limitation: small N",
    ),
    MetricSpec(
        "context_completeness",
        "1 if context_incomplete is False after assembly else 0",
        "not context.context_incomplete",
        "unmeasured; empty context is incomplete by design",
        "Budget truncation is completeness of the budget, not of the world; limitation: not soak coverage",
    ),
    MetricSpec(
        "contradiction_detection_rate",
        "1 if CONTRADICTION_PRESENT when a contradict() edge was seeded else 0",
        "context.contradiction_present on seeded pair",
        "undetected = 0",
        "Requires explicit contradict() edges; limitation: keyword opposition without an edge is a weaker CONTESTED path",
    ),
    MetricSpec(
        "unsupported_claim_rate",
        "1 if verdict SUPPORTED with zero non-stale facts else 0",
        "verdict==SUPPORTED and len(facts)==0",
        "target 0; P3 downgrades SUPPORTED",
        "Does not measure rhetorical overclaim in future LLM layers; limitation: deterministic modes only",
    ),
    MetricSpec(
        "unknown_calibration",
        "1 if empty-evidence tasks return INSUFFICIENT_EVIDENCE or UNKNOWN else 0",
        "verdict in {INSUFFICIENT_EVIDENCE, NOT_IMPLEMENTED} or epistemic in {UNKNOWN, INSUFFICIENT_EVIDENCE}",
        "unmeasured outside tests",
        "Not a probabilistic calibration curve; limitation: binary check",
    ),
    MetricSpec(
        "hypothesis_testability",
        "1 if generated hypothesis provenance includes a non-empty falsification_condition",
        "bool(hyp.provenance.get('falsification_condition'))",
        "unmeasured if no hypothesis written",
        "A string condition is not an executable test; limitation: analysis-only experiments",
    ),
    MetricSpec(
        "falsification_rate",
        "Fraction of hypotheses whose experiment result is not IMPROVED (P3 analysis results are INSUFFICIENT_DATA or NOT_COMPARABLE)",
        "count(result != IMPROVED) / count(experiments)",
        "P3 does not claim IMPROVED from synthetic analysis",
        "Not a scientific falsification rate; limitation: no live experiment runner",
    ),
    MetricSpec(
        "lesson_reuse_rate",
        "1 if a second episode retrieves a LESSON written by episode 1, else 0",
        "LESSON in retrieved epistemic kinds when use_memory=True",
        "NO_MEMORY baseline = 0.0",
        "Synthetic tasks only; not soak performance; limitation: one-task reuse, not population rate",
    ),
    MetricSpec(
        "failure_recurrence_rate",
        "1 if a later task retrieves a prior FAILURE memory else 0",
        "FAILURE type in assembled context.failures",
        "unmeasured if no failure recorded",
        "Retrieval of a failure is not prevention of recurrence; limitation: warning only",
    ),
    MetricSpec(
        "memory_write_integrity",
        "1 if store.integrity_check()==ok after loop writes",
        "CognitiveMemoryStore.integrity_check()",
        "1.0 expected after P3 writes",
        "Does not prove soak DB integrity; limitation: SQLite PRAGMA only",
    ),
    MetricSpec(
        "provenance_completeness",
        "Fraction of written loop memories with non-empty producer and source_id",
        "inspect store.recent() after loop write-back",
        "1.0 expected for loop writes",
        "Does not measure soak provenance; limitation: SYNTHETIC_TEST_DATA labeled separately",
    ),
)


def compute_lesson_reuse(retrieved_kinds: list[str], *, used_memory: bool) -> float:
    if not used_memory:
        return 0.0
    if not retrieved_kinds:
        return 0.0
    return 1.0 if "LESSON" in retrieved_kinds else 0.0
