"""Governance thresholds. Not fitted to the current implementation.

PROVISIONAL = justified as a first governance floor, not a measured SLA.
GOVERNANCE = integrity invariant (leakage / fabricated certainty / nondeterminism).
"""

from __future__ import annotations

BENCHMARK_VERSION = "p4.1.0"
DATA_LABEL = "SYNTHETIC_TEST_DATA"

# Threshold kind: MIN (value >= t), MAX (value <= t), ZERO (numerator == 0).
THRESHOLDS: dict[str, dict] = {
    "namespace_leakage_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Cross-agent private leakage is an integrity failure.",
    },
    "unsupported_claim_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Opinion/prediction/hypothesis must not become SUPPORTED facts.",
    },
    "reproducibility_rate": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Identical inputs must yield identical benchmark output.",
    },
    "contradiction_false_resolution_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "A seeded contradiction must not be silently declared true.",
    },
    "retrieval_precision": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Half of retrieved items should be labeled relevant. Broad same_domain matching may fail this; failure is evidence, not a reason to lower the floor.",
    },
    "retrieval_recall": {
        "kind": "MIN",
        "threshold": 0.7,
        "class": "PROVISIONAL",
        "why": "Most labeled-relevant memories should appear in retrieve().",
    },
    "retrieval_f1": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Harmonic mean floor matching precision governance.",
    },
    "match_reason_correctness": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "A MATCH_REASON must correspond to the mechanism that retrieved the item.",
    },
    "contradiction_detection_rate": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Seeded contradict() edges must surface CONTRADICTION_PRESENT.",
    },
    "unknown_refusal_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Empty or unimplemented cases must refuse, not invent certainty.",
    },
    "false_certainty_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "INSUFFICIENT/UNKNOWN/NOT_IMPLEMENTED cases must not yield SUPPORTED.",
    },
    "namespace_isolation_rate": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Private namespaces must not leak.",
    },
    "lesson_reuse_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Applicable later episodes should retrieve a prior lesson more often than not.",
    },
    "correct_lesson_reuse_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Reuse on labeled-applicable episodes.",
    },
    "incorrect_lesson_application_rate": {
        "kind": "MAX",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Lessons should not blindly generalize. 0.5 is a weak first floor; same_domain retrieval may exceed it.",
    },
    "failure_recall": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Similar later failures should retrieve the prior FAILURE.",
    },
    "false_failure_application_rate": {
        "kind": "MAX",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Unrelated episodes should not treat every FAILURE as applicable.",
    },
    "adversarial_resistance": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Misleading evidence must not produce SUPPORTED certainty.",
    },
    "cross_domain_consistency": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Structurally equivalent tasks should share verdict class across domains.",
    },
    "evidence_class_integrity": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Retrieved evidence_class must match the stored epistemic kind mapping.",
    },
    "temporal_classification_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "STALE/SUPERSEDED/fresh labels must match store status; STALE is not FALSE.",
    },
    "context_coverage": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Under a normal budget, at least half of labeled-relevant retrieved items should remain.",
    },
    "critic_detection_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Seeded critic-trigger cases should raise the corresponding Critique flag more often than not.",
    },
    "recall_at_1": {
        "kind": "MIN",
        "threshold": 0.2,
        "class": "PROVISIONAL",
        "why": "Top-1 should catch some labeled-relevant items; rank is match_reason count.",
    },
    "recall_at_3": {
        "kind": "MIN",
        "threshold": 0.4,
        "class": "PROVISIONAL",
        "why": "Top-3 provisional floor.",
    },
    "recall_at_5": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Top-5 provisional floor.",
    },
    "recall_at_10": {
        "kind": "MIN",
        "threshold": 0.6,
        "class": "PROVISIONAL",
        "why": "Top-10 provisional floor.",
    },
    "no_memory_lesson_reuse": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "NO_MEMORY baseline must not retrieve a lesson that was never read.",
    },
    "stale_not_false": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "STALE historical records remain queryable and are not treated as false.",
    },
    "unrelated_retrieval_rate": {
        "kind": "MAX",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "At most half of retrieved items should be unlabeled for the case. Not fitted to P4.2.",
    },
    "same_domain_false_inclusion_rate": {
        "kind": "MAX",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Same-domain distractors should not dominate labeled retrieval.",
    },
    "contradiction_pollution_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "PROVISIONAL",
        "why": "Contradiction-linked records must not appear on queries that do not expect them.",
    },
    "empty_query_pollution_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Empty/unknown queries must not retrieve unrelated memories.",
    },
    "irrelevant_relationship_expansion_rate": {
        "kind": "MAX",
        "threshold": 0.25,
        "class": "PROVISIONAL",
        "why": "Relationship expansion should stay anchored to labeled-relevant memories.",
    },
    "lookalike_rejection_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Labeled structural cousins on RET-KEYWORD-01 should usually be rejected.",
    },
    "hard_mismatch_rejection_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Explicit component mismatch must suppress the incompatible FAILURE.",
    },
    "generic_overlap_false_inclusion_rate": {
        "kind": "MAX",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Retrieved items whose overlap is only multi-domain operation tokens should be rare.",
    },
    "structured_mismatch_false_inclusion_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "PROVISIONAL",
        "why": "A hard-mismatch probe must not retrieve the mismatched FAILURE.",
    },
    "relevant_lookalike_recall": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Labeled-relevant timeout cluster on RET-KEYWORD-01 must remain retrievable.",
    },
    "task_compatibility_accuracy": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "LEARN cases should not retrieve non-LESSON rows as a majority.",
    },
    "typed_evidence_compliance": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Bindings must preserve the source typed class.",
    },
    "p5_unsupported_claim_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "P5 must not emit SUPPORTED certainty.",
    },
    "evidence_type_violation_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Hypothesis/opinion must not be treated as established fact.",
    },
    "p5_critic_detection_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Seeded P5 critic probes should fire an action or flag.",
    },
    "critic_constraint_rate": {
        "kind": "MIN",
        "threshold": 0.5,
        "class": "PROVISIONAL",
        "why": "Critic must change structured state, not only comment.",
    },
    "missing_premise_refusal_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Empty deduction must refuse.",
    },
    "p5_contradiction_preservation": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Contradictions must remain UNRESOLVED/CONTESTED.",
    },
    "temporal_scope_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Stale-only temporal reading must not treat history as current.",
    },
    "lesson_application_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Applicable lessons must constrain.",
    },
    "false_lesson_application_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Out-of-domain lessons must not constrain.",
    },
    "failure_application_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Matching failure fingerprints may caution.",
    },
    "p5_false_failure_application_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Mismatched failures must not apply as cautions.",
    },
    "mode_specificity": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "DEDUCTIVE and INDUCTIVE must not collapse on the one-fact probe.",
    },
    "reasoning_mode_confusion_rate": {
        "kind": "ZERO",
        "threshold": 0.0,
        "class": "GOVERNANCE",
        "why": "Mode collapse is a failure.",
    },
    "p5_unknown_refusal_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Empty P5 context must refuse.",
    },
    "assumption_binding_accuracy": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Every P5 mode episode should record an assumption id.",
    },
    "p5_cross_domain_invariance": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "PROVISIONAL",
        "why": "Same one-fact deduction should share a verdict class across adapters.",
    },
    "deterministic_reproducibility": {
        "kind": "MIN",
        "threshold": 1.0,
        "class": "GOVERNANCE",
        "why": "Two isolated P5-inclusive benchmark runs must match.",
    },
}
