# AHOS Cognitive Loop Architecture v1.0

**Status:** Lane-B P3 loop IMPLEMENTED_AND_VERIFIED (unit tests). **Not AGI. Not ACI. Not a world model.**  
**Code:** `architecture/cognitive/loop/`  
**Memory:** `architecture/cognitive/memory/` (P2 substrate; not replaced)  
**Tests:** `tests/test_cognitive_loop.py`  
**Base:** main `606b6f282318d48e287873aaf0f3ad4c9def4321` (post PR #88)

This document describes a governed, domain-general, provenance-aware cognitive loop.
It does **not** authorize soak ingest, Lane-A edits, live execution, or autonomous promotion.

## Placement

```text
             COGNITIVE CORE (architecture/cognitive/loop)
                  ↑
       ┌──────────┼──────────┐
       │          │          │
    Finance    Science    Software / Operations
    Adapter     Adapter    Adapters
```

Finance is a proving domain, not the definition of cognition. The loop must not import
`discovery`, `paper_trading`, `telegram_ai`, or `engine`.

## Loop

```text
QUESTION / TASK
      ↓
TASK INTERPRETATION (CognitiveTask)
      ↓
MEMORY RETRIEVAL (MemoryRetriever — deterministic MATCH_REASON)
      ↓
EVIDENCE FILTER + CONTEXT ASSEMBLY (CognitiveContext buckets + budget)
      ↓
REASONING (named modes; unimplemented modes return NOT_IMPLEMENTED)
      ↓
COUNTERARGUMENT / CRITICISM (Critique)
      ↓
UNCERTAINTY (EpistemicAnswer)
      ↓
HYPOTHESIS (existing HypothesisStore; novelty ≠ truth)
      ↓
TEST / EXPERIMENT (existing ExperimentLedger via record_cognitive_experiment)
      ↓
RESULT (INSUFFICIENT_DATA / NOT_COMPARABLE — analysis only)
      ↓
LESSON (EpistemicKind.LESSON, not OBSERVED_FACT)
      ↓
MEMORY write-back (isolated ahos_cognitive_memory.sqlite)
```

Every transition is explicit. The second episode can retrieve the first episode's lesson.

## Task model

`CognitiveTask`: task_id, task_type, objective, question, domain, constraints,
requested_evidence, created_at, deadline/TTL, requester, context_id, provenance,
reasoning_mode, agent_id, write_back, data_label.

Task types: ANALYZE, COMPARE, EXPLAIN, INVESTIGATE, PREDICT, CRITIQUE,
HYPOTHESIZE, TEST, LEARN, SELF_RESEARCH. Extensible strings; not finance-only.

## Retrieval

`MemoryRetriever` scans `store.recent()` and attaches MATCH_REASON strings.

P4.2 (query-time): `same_domain`, unanchored contradiction/failure edges,
mere FAILURE type, and recency are **not** sufficient alone. Anchors are
exact id, structured keys, strong lexical overlap (≥2 canonical tokens), or
a rare in-domain token. Relationships expand one hop from those anchors.
Empty / signal-less queries return `NO_RELEVANT_MEMORY`.

Ranking is documented integer scores (exact id > structured key > fingerprint
> lexical > expansion > domain/temporal boosts), then `memory_id`.

No embeddings. No vector database. No LLM relevance judge.

Agent namespaces: if the task has `agent_id` and a memory has a different
non-empty `agent_namespace`, it is skipped. Empty namespace is shared.

## Context assembly

Pipeline: retrieved → dedupe → max_age → max_per_type → max_per_source →
token estimate → max_memories → CognitiveContext.

Buckets (never collapsed into one bag):

facts · inferences · hypotheses · predictions · experiments · outcomes ·
contradictions · failures · procedures · lessons · unknowns

If the budget drops items, `context_incomplete=True` (CONTEXT_INCOMPLETE).
Empty context is incomplete. Stale observations are queryable and labelled
"not current".

## Evidence hierarchy

Mapped from P2 `EpistemicKind` to P3 `EvidenceClass`:

| EpistemicKind | EvidenceClass |
|---------------|---------------|
| OBSERVED_FACT | DIRECT_OBSERVATION |
| DERIVED_FACT | DERIVED_RESULT |
| INFERENCE | MODEL_INFERENCE |
| HYPOTHESIS | HYPOTHESIS |
| PREDICTION | PREDICTION |
| SIMULATION | SIMULATION |
| OPINION | OPINION |
| PROCEDURE | VERIFIED_RECORD |
| LESSON | DERIVED_RESULT |
| other | UNKNOWN |

P3 never silently upgrades OPINION/PREDICTION/SIMULATION/HYPOTHESIS to FACT.
Verdict SUPPORTED is downgraded to WEAKLY_SUPPORTED.

## Contradiction

If `store.contradict()` edges are present among selected items:

- `contradiction_present=True`
- both memories remain
- verdict `UNRESOLVED`, epistemic `CONTESTED`

Reasoning does not pick a winner.

Keyword-level support vs opposition without an edge can yield `CONTESTED`.
Otherwise: WEAKLY_SUPPORTED / INSUFFICIENT_EVIDENCE / STALE / UNKNOWN.

## Unknown handling

`EpistemicAnswer`: KNOWN, PROBABLE, UNCERTAIN, CONTESTED, UNKNOWN,
INSUFFICIENT_EVIDENCE, STALE.

"I don't know" is a valid result (`INSUFFICIENT_EVIDENCE` / `UNKNOWN` /
`NOT_IMPLEMENTED`).

## Reasoning modes

| Mode | P3 status |
|------|-----------|
| DEDUCTIVE, INDUCTIVE, ABDUCTIVE, COMPARATIVE, TEMPORAL, ADVERSARIAL, METACOGNITIVE | IMPLEMENTED (deterministic, LLM-free) |
| CAUSAL_HYPOTHESIS, COUNTERFACTUAL | NOT_IMPLEMENTED (explicit) |

Traces store auditable metadata (ids, assumptions, steps, verdict). They are
not private chain-of-thought.

## Assumptions

Every episode records at least one `Assumption` (id, statement, basis,
confidence, impact, origin=ASSUMED). Origins: OBSERVED, RETRIEVED, INFERRED,
ASSUMED, UNKNOWN.

## Criticism

Bounded critic asks the eight mandated questions and flags: weakest assumption,
alternative explanation, too-strong conclusion, prediction-as-fact, stale-as-current,
missing evidence. Output is `Critique`, not a second decision-maker.

## Hypothesis and falsification

Uses existing `HypothesisStore`. Provenance includes `falsification_condition`,
supporting/contradicting memory ids, and `novelty_equals_truth: false`.
NOVEL ≠ TRUE.

## Experiment

Uses existing `ExperimentLedger` via `record_cognitive_experiment`.
P3 results are analysis-only: `INSUFFICIENT_DATA` or `NOT_COMPARABLE`.
Does not authorize trading, deployment, autonomous code modification, or live execution.
`CognitiveOrchestrator.authorize_execution` raises.

## Learning and write-back

A LESSON carries: source experiment/hypothesis ids, observed verdict, what_worked,
what_failed, applicability, boundary_conditions, data_label, provenance.

The loop may write EPISODIC INFERENCE, HYPOTHESIS, EXPERIMENT, LESSON, FAILURE.
It must not write OBSERVED_FACT unless an adapter/source is a real observation
with provenance (test adapters label SYNTHETIC_TEST_DATA).

## Failure learning

`CognitiveOrchestrator.record_failure` → P2 `record_failure` (fingerprint +
recurrence). Later retrieval tags `failure_relationship`. Context surfaces
failures; it does not auto-prevent recurrence.

## Domain adapters

Thin functions: `finance_observation`, `science_observation`,
`software_observation`, `operations_observation`. Same `ingest_generic_observation`.
Synthetic rows: `data_label=SYNTHETIC_TEST_DATA`. Never mixed with soak evidence.

## Tool intelligence

`plan_tools` returns INTERFACE_ONLY / NOT_IMPLEMENTED. No autonomous tool
selection or execution.

## Metacognition preparation

`metacognitive_state(result)` exposes: what I know / don't know / why I believe
it / supporting evidence / contradictions / assumptions / prior failures /
experiment that should resolve uncertainty. Not a metacognitive agent.

## World-model boundary

`current_world_model_boundary()` is NOT_IMPLEMENTED. Compatible object kinds
(ENTITY, STATE, EVENT, RELATION, CAUSE, EFFECT, TIME, UNCERTAINTY,
COUNTERFACTUAL, …) may be stored as P2 payloads later. That is not a world model.

## Metrics

Definitions live in `architecture/cognitive/loop/metrics.py` (`METRIC_SPECS`).
No fabricated intelligence score. Measured in tests: lesson_reuse_rate
(NO_MEMORY=0 vs MEMORY+LOOP=1 on a synthetic pair), unsupported_claim_rate=0,
integrity=ok. Other metrics have methods and limitations but are unmeasured
outside their unit scenarios.

## Performance

Local SQLite, no GPU, no vector DB, no paid API required for core correctness.
Tests assert one e2e cycle completes in under 5 seconds on the Cloud Linux host.
No premature optimization.

## Security / soak

- No secrets, no `.env`, no Permission Layer bypass, no Risk Governor bypass
- No Lane A edits, no soak DB open, no runtime restart, no T0 reset
- PAPER_ONLY, autonomy ceiling L1_ANALYZE
- Memory and reasoning are not authorization

## Limitations (honest)

- Not wired to production soak or observation daemon
- Causal and counterfactual modes are NOT_IMPLEMENTED
- Retrieval is keyword/domain/id/edge — not semantic embeddings
- Experiments are analysis records, not live trials
- Tool selection is INTERFACE_ONLY
- World model is a boundary, not an engine
- Four adapters are synthetic test helpers, not market integrations
- Metacognition is structured state, not self-modification
- AGI/ACI is not achieved

## Future

P4 candidates must be chosen from measured gaps, not the original roadmap
automatically. Highest-value after P3 measurement: expand the deterministic
benchmark and/or metacognition over real traces — **not** soak ingest while
the Windows soak is active.
