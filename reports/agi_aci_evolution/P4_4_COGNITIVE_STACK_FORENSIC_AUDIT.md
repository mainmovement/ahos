# P4.4 — Cognitive Stack Forensic Audit

**Phase:** P4.4 (audit only)  
**Classification of this document:** observational evidence report  
**Data label:** `SYNTHETIC` measurements are quoted from existing P4.1–P4.3 artifacts; implementation claims are from repository source  
**Date (UTC):** 2026-09-09  
**Auditor role:** read-only cognitive-architecture review  
**Implementation performed:** NO  

This report does not claim AGI, ACI, near-AGI, human-level intelligence, or any intelligence percentage.

Evidence labels used below:

| Label | Meaning |
|-------|---------|
| CONFIRMED | Direct repository evidence (source, test, or recorded metric) |
| LIKELY | Strong inference from multiple consistent sources |
| UNCONFIRMED | Plausible but not demonstrated in-repo |
| CONTRADICTED | Prior claim conflicts with inspected implementation or metric definition |
| MISSING | No meaningful implementation found |

Capability classes used below: `IMPLEMENTED` · `PARTIAL` · `INTERFACE_ONLY` · `BENCHMARK_ONLY` · `DOCUMENTED_ONLY` · `PLACEHOLDER` · `MISSING` · `CONTRADICTED` · `UNKNOWN`

---

## 1. EXECUTIVE SUMMARY

After P1 → P2 → P3 → P4.1 → P4.2 → P4.3, AHOS has a **real, tested, deterministic retrieval stack** on an isolated provenance-bearing memory store, wrapped by a Lane-B cognitive loop that can refuse unknown, preserve contradictions, and write lessons. That is not intelligence. It is a governed memory-and-retrieval machine with a labeled reasoning wrapper.

**Strongest current cognitive capability (CONFIRMED):**  
Governed retrieval with P4.2 hard gates and P4.3 lookalike discrimination. On the frozen P4.1 synthetic vector: precision 0.9091 (20/22), recall 1.0000, F1 0.9524, MATCH_REASON 1.0000, lookalike rejection 7/7, unknown refusal 1.0000, false failure application 0, contradiction pollution 0.

**Most important current weakness (CONFIRMED):**  
Operational reasoning does not consume retrieved memory *as typed evidence*. All seven “implemented” modes share one keyword-overlap verdict function (`_verdict_from_context`). The critic is a checklist that does not constrain that verdict. Lessons and failures are persisted and later retrieved; tests prove retrieval, not a change in future inference rules. Experiments are recorded as `INSUFFICIENT_DATA` / `NOT_COMPARABLE`.

**Is retrieval the dominant cognitive bottleneck?**  
**No (CONFIRMED).** Residual retrieval false positives are two labeled cases (`BM-SHARED` on `RET-KEYWORD-01`, `BM-SW-TIMEOUT-HYP` on `RET-TEMP-01`). That is incremental. The loop already delivers relevant memories to a reasoner that does not differentiate modes, does not apply lessons as constraints, and does not let the critic veto.

**Context coverage 0.5714 is not proof of broken assembly (CONFIRMED / CONTRADICTED vs P4.3 prose).**  
The evaluator averages `|selected ∩ TIMEOUT_RELEVANT| / |TIMEOUT_RELEVANT retrieved|` across budgets `{tiny:2, normal:8, large:40, zero:0}`. `TIMEOUT_RELEVANT` has **7** IDs. At `max_memories=8` the assembler selected all 7 relevant IDs (plus `BM-SHARED`). The 0.5714 figure equals `(2/7 + 7/7 + 7/7 + 0/7) / 4`. The P4.3 report gloss “budget 8 vs 14 labeled relevant” is **CONTRADICTED** by the evaluator and corpus (`architecture/cognitive/benchmark/evaluator.py`, `corpus.py`).

**Single highest-value next capability:**  
**Typed evidence-bound reasoning** — mode-differentiated inference that treats `OBSERVED_FACT`, `LESSON`, `FAILURE`, `HYPOTHESIS`, `PREDICTION`, and contradiction edges as different inputs, and that is constrained by the critic.

Implementation of that capability was **not** performed.

---

## 2. REPOSITORY STATE

| Item | Value | Label |
|------|-------|-------|
| Inspected workspace | `/workspace` (Cursor Cloud), repo `mainmovement/ahos` | CONFIRMED |
| Local branch (not switched) | `cursor/agi-aci-p4-3-semantic-lookalike-discrimination-9500` | CONFIRMED |
| Local HEAD | `6fe9b6a4b86283cfa00a722c3e91567df264f8eb` | CONFIRMED |
| `origin/main` tip | `976516123b0b682e99fcc6e9c6f0efabb91a9495` — `Merge pull request #92` | CONFIRMED |
| P4.3 merge | PR #92 merged; known SHA matches directive | CONFIRMED |
| Working tree | Untracked only: `next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt` | CONFIRMED |
| This audit | No `git checkout`, no branch create, no add/commit/push | CONFIRMED |
| Lane-A freeze | `python3 -B scripts/freeze_lane_a.py` → `Lane-A integrity OK (36 files pinned)` | CONFIRMED |
| Soak / runtime | Not started, not reset, not written | CONFIRMED |
| `PAPER_ONLY` | `SandboxPolicy.paper_only=True`; doctrine unchanged | CONFIRMED |
| Autonomy ceiling | `CURRENT_AUTONOMY_CEILING = L1_ANALYZE` | CONFIRMED |

Recent merged cognitive sequence on `origin/main` (CONFIRMED from `git log`):

| Phase | Merge / evidence | SHA (short) |
|-------|------------------|-------------|
| P1 | PR #87 | `1f4febb` |
| P2 | PR #88 | `606b6f2` |
| P3 | PR #89 | `6862c6f` |
| P4.1 | PR #90 | `6e65f15` |
| P4.2 | PR #91 | `eb1dbcf` |
| P4.3 | PR #92 | `9765161` |

Present governance / evolution surfaces (CONFIRMED by file existence): `.cursor/skills/ahos-governance-context/SKILL.md`, `AGENTS.md`, `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`, `reports/agi_aci_evolution/` (records 0001–0007, P4.1–P4.3 reports, `GAP_REGISTER.md`, `CAPABILITY_MATRIX.md`, `ARCHITECTURE_MAP.md`).

Filenames were not treated as proof. Claims below cite implementation.

---

## 3. P1–P4.3 IMPLEMENTATION MAP

| Phase | What actually exists | Class | Evidence |
|-------|----------------------|-------|----------|
| P1 | Domain-general vocabularies, hypothesis states, autonomy ceiling, capability-status enum, sandbox policy | IMPLEMENTED (contracts) | `architecture/cognitive/contracts.py`, `sandbox.py`; tests in `tests/test_cognitive_core.py` |
| P2 | Isolated SQLite memory store, provenance, revisions, edges, failure fingerprints, consolidation gate | IMPLEMENTED (substrate) / PARTIAL (not soak-wired) | `architecture/cognitive/memory/`; `tests/test_cognitive_memory.py`; ACI-GAP-001 |
| P3 | Retriever + context assembler + orchestrator + reason/critic wrappers + lesson write-back | PARTIAL | `architecture/cognitive/loop/`; `tests/test_cognitive_loop.py`; P3 audit |
| P4.1 | Labeled synthetic benchmark + numerator/denominator metrics | IMPLEMENTED (evaluator) / BENCHMARK_ONLY (cognition measured) | `architecture/cognitive/benchmark/`; ACI-GAP-010 |
| P4.2 | Query-time hard gates; empty query → `NO_RELEVANT_MEMORY` | IMPLEMENTED | `loop/retrieval.py`; P4.2 reports |
| P4.3 | Hard mismatch, generic-lookalike, intent typing, namespace gates, `RelevanceVector` | IMPLEMENTED | `loop/retrieval.py`; P4.3 reports; 167 targeted tests recorded |

P4.3 remains **IMPLEMENTED / PARTIAL** as a *cognitive system*: retrieval discrimination is implemented; the surrounding loop is not AGI/ACI and was not claimed as such.

---

## 4. COGNITIVE STACK MAP

### 4.1 Mandated path

```text
OBSERVATION        PARTIAL — adapters can ingest typed observations; production/soak ingest MISSING
    ↓
EVIDENCE           PARTIAL — EpistemicKind + EvidenceClass exist; reasoning mostly ignores type
    ↓
MEMORY             IMPLEMENTED (isolated store) — ACI-GAP-001: not live-wired
    ↓
RETRIEVAL          IMPLEMENTED (P4.2+P4.3) — residual 2/22 FPs
    ↓
CONTEXT            PARTIAL — budgeted packing + buckets; no reserved contradiction slots
    ↓
REASONING          PARTIAL / label-heavy — 7 modes, one verdict function
    ↓
CRITIC             PARTIAL — checklist; does not constrain implemented verdicts
    ↓
HYPOTHESIS         PARTIAL — real lifecycle store; loop only proposes
    ↓
EXPERIMENT         PLACEHOLDER / PARTIAL — ledger rows; analysis codes only
    ↓
LEARNING           PARTIAL — persist + retrieve; not policy change
    ↓
MEMORY WRITE-BACK  IMPLEMENTED — LESSON + EPISODIC + optional HYP/EXP
    ↓
FUTURE RETRIEVAL   IMPLEMENTED — proven by tests; future *reasoning change* MISSING
```

### 4.2 Additional capabilities

| Capability | Status | Evidence |
|------------|--------|----------|
| WORLD MODEL | MISSING / INTERFACE_ONLY inventory | `world_model.py`, `loop/world_boundary.py` |
| CAUSAL MODEL | MISSING | `NOT_IMPLEMENTED` in world-model status and reasoning modes |
| COUNTERFACTUAL REASONING | MISSING (general); financial hindsight PARTIAL | `counterfactual.py`; mode `COUNTERFACTUAL` refuses |
| METACOGNITION | PARTIAL (recording) | `loop/metacognition.py`; METACOGNITIVE mode appends counts |
| GOAL FORMATION | MISSING | ACI-GAP-008; no goal module |
| TASK DECOMPOSITION | MISSING | `TaskType` enum only |
| TOOL SELECTION | INTERFACE_ONLY | `loop/tools.py` `plan_tools` |
| TOOL USE | MISSING | same |
| PLANNING | MISSING | inventory: multi_step = pipelines, not a planner |
| LONG-HORIZON MEMORY | PARTIAL | store persists; no long-horizon policy |
| AGENT MEMORY | PARTIAL | namespace fields; passports `memory_bearing=false` |
| MULTI-AGENT COLLABORATION | MISSING as cognition | council is advisory envelope compare |
| AGENT SPECIALIZATION | INTERFACE_ONLY / PARTIAL | registry + lenses, not independent reasoners |
| SELF-RESEARCH | PARTIAL (snapshot formatter) | `self_research.py` |
| SELF-EVALUATION | PARTIAL / BENCHMARK_ONLY | P4.1 evaluator; not a live self-model |
| FAILURE ANALYSIS | PARTIAL | fingerprint + retrieve; no policy change |
| CALIBRATION | PARTIAL (Lane B scoring/ledger, not cognitive loop) | charter; loop has no calibration curve |
| PREDICTION TRACKING | PARTIAL (fields exist) | `prediction_id` on records; loop does not score outcomes |
| MODEL SELECTION | MISSING | — |
| STRATEGY SELECTION | MISSING | — |
| SELF-IMPROVEMENT PROPOSALS | PARTIAL | `evolution_gate.py` → `SelfEvolutionEngine.create_proposal` |
| CONTROLLED EVOLUTION | PARTIAL | human gate; no auto-promote |
| SANDBOX EVALUATION | PARTIAL | `sandbox.py` policy asserts; not a full gauntlet runner |
| PROMOTION / REJECTION | PARTIAL | human approve path in `evolution/engine.py` |
| ROLLBACK | DOCUMENTED_ONLY / PARTIAL | `rollback_plan` dict on proposals; not an automatic rollback engine |

---

## 5. MEMORY AUDIT

**Implementation:** `architecture/cognitive/memory/store.py`, `record.py`, `types.py`, `consolidation.py`.  
**Isolation (CONFIRMED):** dedicated `ahos_cognitive_memory.sqlite`; constructor rejects `FORBIDDEN_DB_NAMES` (`e01_discovery.sqlite`, `paper_trading.sqlite`, `ahos_local.sqlite`, `ahos_knowledge.sqlite`).

| Topic | Status | Finding |
|-------|--------|---------|
| Memory types | IMPLEMENTED | `WORKING`, `EPISODIC`, `SEMANTIC`, `PROCEDURAL`, `HYPOTHESIS`, `EXPERIMENT`, `FAILURE`, `AGENT`, `WORLD_MODEL`, `SELF_MODEL` |
| Provenance | IMPLEMENTED | required `source_id`, `source_location`, `producer`, `producer_version`, `domain`, `context` |
| Integrity | IMPLEMENTED | SHA-256 `integrity_hash`; `integrity_check()` is SQLite `PRAGMA integrity_check` |
| Revision history | IMPLEMENTED | append-only revisions; existing id cannot be overwritten via `remember()` |
| Contradiction handling | IMPLEMENTED | `contradict()` edges; both rows marked `CONTESTED`; resolve does not delete |
| Support relationships | IMPLEMENTED | `support()` + `SUPPORTS` edge |
| Supersession | IMPLEMENTED | old remains queryable as `SUPERSEDED` |
| Temporal validity | IMPLEMENTED | `observed_at`, `valid_from`/`valid_until`, `apply_decay()` → AGING/STALE; no delete |
| Failure memory | IMPLEMENTED | `record_failure()` + `failure_stats` fingerprint recurrence |
| Agent namespace isolation | IMPLEMENTED (store + retrieval) | unscoped queries skip namespaced private rows (P4.3) |
| Hypothesis / experiment linkage | IMPLEMENTED (fields) | `hypothesis_id`, `experiment_id` on records |
| Lesson persistence | IMPLEMENTED | orchestrator write-back `EpistemicKind.LESSON` |
| Retrieval API | IMPLEMENTED | `MemoryRetriever.retrieve` / `retrieve_explained` |
| Storage isolation | IMPLEMENTED | see forbidden names |
| Consolidation rules | IMPLEMENTED (gate) | cannot write `OBSERVED_FACT`/`DERIVED_FACT`; AI episodes → OPINION |

### P2 questions

| # | Question | Answer | Label |
|---|----------|--------|-------|
| A | Can AHOS remember? | Yes, in the isolated Lane-B store. Not as a live soak self-model. | CONFIRMED |
| B | Distinguish known vs inferred? | Kinds exist and are stored. Reasoning mostly keyword-scores all included items. | CONFIRMED / PARTIAL use |
| C | Preserve contradictory knowledge? | Yes — edges, no overwrite. Loop surfaces `UNRESOLVED`. | CONFIRMED |
| D | Understand temporal validity? | Decay and stale≠current in reasoner. Not a temporal world model. | CONFIRMED / PARTIAL |
| E | Remember failure? | Yes, with fingerprint recurrence counts. | CONFIRMED |
| F | Remember lessons? | Yes, write-back LESSON + payload. | CONFIRMED |
| G | Later cognition use those lessons? | Later retrieval yes. Use as a *constraint* no. | CONFIRMED retrieve / MISSING apply |
| H | Distinguish agent-specific knowledge? | Namespace isolation yes. Not memory-bearing agents. | CONFIRMED / PARTIAL |
| I | Prevent derived knowledge becoming fake observed fact? | Blocked for AI_MODEL/AGENT sources and consolidation. `remember()` still accepts caller-supplied kinds for SYSTEM/HUMAN. Failures are stored as `OBSERVED_FACT`. | CONFIRMED partial guard |

**FAILURE + OBSERVED_FACT (CONFIRMED):** `record_failure()` writes `MemoryType.FAILURE` and `EpistemicKind.OBSERVED_FACT`. Context then buckets the same row into both `facts` and `failures`. That is a typed-evidence confusion the reasoner does not resolve.

---

## 6. RETRIEVAL AUDIT

**Implementation:** `architecture/cognitive/loop/retrieval.py` (P4.2 gates + P4.3 discrimination).

| Mechanism | Status | What it actually does |
|-----------|--------|------------------------|
| Candidate generation | IMPLEMENTED | Store scan + two-stage anchors then one-hop expansion (P4.2) |
| Hard gates | IMPLEMENTED | Domain / unanchored edges / mere FAILURE / recency are not relevance by themselves |
| Structured matching | IMPLEMENTED | Exact memory id, hypothesis_id, experiment_id |
| Lexical matching | IMPLEMENTED | Token overlap with DF / domain-span / generic-lookalike rules |
| Domain handling | IMPLEMENTED | Cross-domain lexical needs ≥3 overlap tokens or domain-span 1 |
| Relationship expansion | IMPLEMENTED | One-hop after anchors; not a sufficient gate alone |
| Temporal handling | IMPLEMENTED | Stale queryable; stale ≠ false |
| Namespace handling | IMPLEMENTED | Unscoped query skips private namespaces; shared empty-ns needs structured key |
| Stale handling | IMPLEMENTED | History intent; reasoner refuses stale-only facts as current |
| Unknown handling | IMPLEMENTED | Empty / no anchors → no relevant memory → loop `INSUFFICIENT_EVIDENCE` |
| Ranking | IMPLEMENTED | Integer scores; deterministic |
| Relevance vector | IMPLEMENTED | `RelevanceVector` on `retrieve_explained()` |
| Lookalike discrimination | IMPLEMENTED | `HARD_MISMATCH_*`, `GENERIC_LOOKALIKE`, intent-type filters |
| MATCH_REASON | IMPLEMENTED | Benchmark correctness 1.0000 (22/22) |
| Bounded retrieval | IMPLEMENTED | Ranked list; context budget applied later |

**Residual weaknesses (CONFIRMED, P4.3 audit + this inspection):**

1. `RET-KEYWORD-01` still retrieves `BM-SHARED` (`{retry, timeout}`).
2. `RET-TEMP-01` still retrieves `BM-SW-TIMEOUT-HYP` (`{rate, timeout}`).
3. Many memories lack structured `component`/`operation`; unknown fields are neutral (not mismatch).
4. Population is synthetic, N small (41 corpus memories; 11 retrieval cases).
5. ACI-GAP-010 remains open (not a six-baseline AGI suite).

**Is retrieval the dominant bottleneck?**  
**No (CONFIRMED).** Precision 0.9091 and recall 1.0000 on the frozen vector. The remaining 2/22 unrelated inclusions are real and should stay on the register. They do not dominate competence relative to a reasoner that keyword-scores whatever arrives.

---

## 7. CONTEXT AUDIT

**Implementation:** `architecture/cognitive/loop/context.py`.  
**Default budget:** `ContextBudget(max_memories=20, max_tokens_estimate=4000, max_per_type=8, max_per_source=8)`.

| Property | Status | Finding |
|----------|--------|---------|
| Context budget | IMPLEMENTED | Memory count, tokens, per-type, per-source, optional max_age |
| Truncation | IMPLEMENTED | First-fit over already-ranked list; `context_incomplete` set |
| Ranking preservation | IMPLEMENTED | Walks retrieval order; no re-rank |
| Provenance preservation | IMPLEMENTED | Items keep source/epistemic fields; benchmark provenance 1.0 |
| Contradiction preservation | PARTIAL | Edges collected only among *selected* IDs; no reserved contradiction slots |
| Relevance preservation | PARTIAL | Depends on rank + budget; at normal=8, all 7 timeout-relevant IDs kept |
| Memory diversity | PARTIAL | `max_per_type` / `max_per_source` caps |
| Redundancy handling | PARTIAL | Duplicate `memory_id` excluded only |
| Temporal ordering | MISSING | No sort by `observed_at`; rank order only |
| Failure/lesson inclusion | PARTIAL | Bucketed if selected; not reserved |
| Incompleteness handling | IMPLEMENTED | Flag + unknowns; reasoner may downgrade epistemic to UNCERTAIN |

**Can AHOS retrieve the correct memory but still fail because context is incomplete?**  
**Yes, under tiny/zero budgets (CONFIRMED).** Under the evaluator’s `normal` budget of 8, `CTX-NORMAL` selected all 7 `TIMEOUT_RELEVANT` IDs plus `BM-SHARED`. Operational default is 20.  

**Quantified coverage (CONFIRMED):**

| Budget | max_memories | Selected relevant / 7 | incomplete |
|--------|-------------:|----------------------:|------------|
| zero | 0 | 0 | true |
| tiny | 2 | 2 (`FACT`, `FAIL`) | true |
| normal | 8 | 7 | false |
| large | 40 | 7 | false |

Mean 0.5714 is the average of those four ratios. It is **not** “8 of 14 relevant memories dropped at operating budget.”

P4.3 prose “budget 8 vs 14 labeled relevant”: **CONTRADICTED** by `TIMEOUT_RELEVANT` length 7 and evaluator definition.

---

## 8. EVIDENCE HIERARCHY AUDIT

**Vocabularies (CONFIRMED):**  
`EpistemicKind`: `OBSERVED_FACT`, `DERIVED_FACT`, `INFERENCE`, `HYPOTHESIS`, `PREDICTION`, `SIMULATION`, `OPINION`, `PROCEDURE`, `LESSON`.  
`MemoryType` separately includes `FAILURE`, `EXPERIMENT`, `HYPOTHESIS`, etc.  
There is **no** `EpistemicKind.FAILURE` or `EpistemicKind.EXPERIMENT`.

| Silent upgrade | Can it happen automatically in the loop? | Mechanism / vulnerability |
|----------------|------------------------------------------|---------------------------|
| prediction → fact | No automatic | Predictions skipped in `_keyword_hits`; empty-facts+predictions → `INSUFFICIENT_EVIDENCE`. Caller `remember()` can still store a prediction as `OBSERVED_FACT` if source is not AI_MODEL/AGENT. |
| hypothesis → fact | No automatic | Hypothesis write-back uses `EpistemicKind.HYPOTHESIS`. Store `SUPPORTED` state requires an experiment_id; that is not a fact write. |
| opinion → fact | No automatic for AI | `validate_new_record` raises `EpistemicViolation` for AI_MODEL/AGENT + FACT kinds. SYSTEM caller can mis-label. |
| simulation → fact | No automatic in consolidation | Consolidation proposes SIMULATION/OPINION; accept() forbids FACT kinds. |
| lesson → fact | No automatic | Lessons written as `LESSON`; reasoner says “not treated as OBSERVED_FACT” then still returns `WEAKLY_SUPPORTED`. |

**Critic check `prediction_confused_with_fact`:** true only if a PREDICTION appears in `ctx.facts`. Facts are bucketed by kind, so a correctly labeled prediction is not in `facts`. The check is structural, not semantic.

**Vulnerability (CONFIRMED):** hierarchy is enforced at *write* for AI sources and consolidation, not at *inference* for SYSTEM-labeled rows. Failures stored as `OBSERVED_FACT` enter the fact bucket.

---

## 9. REASONING AUDIT

**Implementation:** `architecture/cognitive/loop/reason.py`.  
**Inventory (broader Lane B):** `architecture/cognitive/reasoning.py` (FSMs/scoring/hindsight — not the P3 loop).

All seven listed modes call the **same** `_verdict_from_context`:

1. If contradiction edge present → `UNRESOLVED` / `CONTESTED`.
2. If only stale facts → `INSUFFICIENT_EVIDENCE` / `STALE`.
3. Else keyword overlap of statements vs question/objective; skip PREDICTION/OPINION/SIMULATION; crude negation words → opposing.
4. Facts + supporting → `WEAKLY_SUPPORTED` / `PROBABLE` (same for 1 or many supports).
5. Else if lessons present → `WEAKLY_SUPPORTED` / `UNCERTAIN`.
6. Else if predictions and no facts → `INSUFFICIENT_EVIDENCE` / `UNKNOWN`.
7. Else `INSUFFICIENT_EVIDENCE`.

Any `SUPPORTED` result is immediately downgraded to `WEAKLY_SUPPORTED` (“P3 never upgrades to certainty”).

Mode-specific code only **rewrites the conclusion string** (and appends a step). `CAUSAL_HYPOTHESIS` and `COUNTERFACTUAL` return `NOT_IMPLEMENTED` and refuse.

| Mode | Real or label? | Input | Output | Deterministic | Evidence attached | Assumptions | Uncertainty | Refuse | Self-contradict | Learn from prior reasoning |
|------|----------------|-------|--------|---------------|-------------------|-------------|-------------|--------|-----------------|----------------------------|
| DEDUCTIVE | Label on shared verdict | Context + task | Same verdict + text | Yes | selected_ids | One hardcoded ASM | EpistemicAnswer | Empty/unknown/unimplemented | Via contest/unresolved | No |
| INDUCTIVE | Label + count lessons/failures in text | Same | Same verdict | Yes | Same | Same | Same | Same | Same | No |
| ABDUCTIVE | Label (“best explanation candidate”) | Same | Same verdict | Yes | Same | Same | Same | Same | Same | No |
| COMPARATIVE | Label | Same | Same verdict | Yes | Same | Same | Same | Same | Same | No |
| TEMPORAL | Label + stale sentence | Same | Same verdict | Yes | Same | Same | STALE path exists | Same | Same | No |
| ADVERSARIAL | Label (“defers to critic”) | Same | Same verdict | Yes | Same | Same | Same | Same | Same | Critic does not change it |
| METACOGNITIVE | Label + counts | Same | Same verdict | Yes | Same | Same | Same | Same | Same | Recording only |
| CAUSAL_HYPOTHESIS | NOT_IMPLEMENTED | — | Refuse | Yes | — | — | UNKNOWN | Yes | — | — |
| COUNTERFACTUAL | NOT_IMPLEMENTED | — | Refuse | Yes | — | — | UNKNOWN | Yes | — | — |

**Benchmark `reasoning_mode_structure_rate` = 1.0 (CONFIRMED):** passes if `trace.mode` matches, `mode_status==IMPLEMENTED`, and verdict ≠ `SUPPORTED`. It does **not** require modes to produce different verdicts. That metric is structural, not cognitive differentiation.

**Adversarial loop verdicts (CONFIRMED, `p4_3_retrieval_benchmark_latest.json`):**  
`ADV-FIN-OPINION`, `ADV-HYP`, `ADV-LOOKALIKE`, `ADV-SUPERSEDED` → `WEAKLY_SUPPORTED` / `PROBABLE`.  
`ADV-OPINION`, `ADV-PRED` → `INSUFFICIENT_EVIDENCE`.  
So some opinion/hypothesis/lookalike/superseded probes still get a positive-leaning weak verdict.

---

## 10. CRITIC AUDIT

**Implementation:** `critique_result()` in `reason.py`.

Mandated questions (CONFIRMED):

1. What evidence contradicts this?  
2. What evidence is missing?  
3. Which assumption is weakest?  
4. Could another explanation fit?  
5. Is the conclusion too strong?  
6. Is retrieved context biased?  
7. Is there stale evidence?  
8. Did we confuse prediction with fact?  

**What the critic is:** a deterministic checklist over assembled context + the already-computed verdict.  
**What it is not:** an independent challenge process, a second decider, or a second retrieval.

| Detection | Real mechanism? |
|-----------|-----------------|
| Unsupported assumptions | Reports first hardcoded assumption or “none recorded” |
| Evidence mismatch | `missing_evidence = ctx.unknowns` only |
| Contradiction | Alternative explanation string if `contradiction_present` |
| Overconfidence | `too_strong = (verdict == SUPPORTED)` |
| Stale evidence | any STALE in `ctx.facts` |
| Scope mismatch | **not implemented** as a critic flag (`critic_scope_mismatch` is a separate benchmark probe) |
| Hypothesis weakness | **not** a dedicated check |
| Experiment weakness | **not** a dedicated check |

**Does the critic change the final result?**  
**No on the implemented path (CONFIRMED).** `too_strong` is the only verdict mutation. It fires only when `verdict == SUPPORTED`. The reasoner downgrades `SUPPORTED` → `WEAKLY_SUPPORTED` *before* `critique_result()` is called. Therefore `too_strong` is always false after that downgrade. Adversarial mode’s comment “defers to critic before any upgrade” is commentary.

Classification: **PARTIAL** (real flags exist) / functionally **commentary**.

---

## 11. HYPOTHESIS AUDIT

**Store:** `architecture/cognitive/hypothesis.py` — JSONL, sequential `HYP-` IDs, fail-closed transitions.  
**Loop use:** orchestrator `propose()` when task type is HYPOTHESIZE/INVESTIGATE/TEST/ANALYZE and mode is implemented and `write_back`.

| Question | Finding | Label |
|----------|---------|-------|
| How created? | `HypothesisStore.propose` from task question + data_label | CONFIRMED |
| Novelty ≠ truth? | `novelty_equals_truth: False` in provenance; `classify_novelty` | CONFIRMED |
| Falsification conditions? | String in provenance, default generic sentence | CONFIRMED / weak |
| Link to evidence? | `supporting_memory_ids` / contradicting ids copied | CONFIRMED |
| Link to failures? | Optional via later `record_failure(hypothesis_id=...)` | PARTIAL |
| Can be rejected? | Transition table includes REJECTED | CONFIRMED |
| Rejected remain? | JSONL rewrite keeps the row | CONFIRMED |
| Future retrieve? | Memory copy written as `MemoryType.HYPOTHESIS` | CONFIRMED |
| Influence experiments? | Loop attaches experiment after propose; result not a real test | PARTIAL |

`SUPPORTED` requires a linked `experiment_id` (CONFIRMED). The loop never transitions to `SUPPORTED` from analysis placeholders.

**Verdict:** genuine **lifecycle store**, **structured record creation** from the loop — not a scientific hypothesis engine.

---

## 12. EXPERIMENT AUDIT

**Bridge:** `architecture/cognitive/experiment_bridge.py` → existing `ExperimentLedger`.  
**Loop results (CONFIRMED):** `INSUFFICIENT_DATA` normally; `NOT_COMPARABLE` if verdict is `UNRESOLVED`. Memory statement: `experiment {id} result={code}` with `EpistemicKind.INFERENCE`.

| Topic | Status |
|-------|--------|
| Creation | IMPLEMENTED (ledger row) |
| Linkage | IMPLEMENTED (hypothesis attach + memory fields) |
| Status / result codes | Constrained to ledger `RESULTS` |
| Falsification | String only |
| Evidence requirements | `evidence_refs=retrieved_ids` copied |
| Analysis / comparison | Placeholder codes |
| Outcome / failure / lesson extraction | `reusable_lesson=trace.conclusion` copied into ledger |

**Classification:** `STRUCTURED PLACEHOLDERS` / analysis-only.  
`test_record_cognitive_experiment_still_analysis_only` exists.  
Not `REAL ANALYTICAL EXPERIMENTS`.

---

## 13. LEARNING AUDIT

Traced path:

```text
EPISODE (orchestrator.run)
  → RESULT (verdict + critique + trace)
  → ERROR / SUCCESS (not classified beyond verdict string)
  → LESSON (write-back; applicability = task.domain only)
  → MEMORY (LESSON + EPISODIC INFERENCE)
  → RETRIEVAL (P4.2/P4.3)
  → FUTURE EPISODE (lesson may appear in context.lessons)
```

| Level | Supported? | Evidence |
|-------|------------|----------|
| Memory persistence | YES | store + tests |
| Cognitive learning (policy/inference change) | NO | `_verdict_from_context` unchanged by lesson content/applicability |
| Parameter/model improvement | NO | no weights, no calibration update in the loop |
| Architectural improvement | NO | evolution proposals only, human-gated |
| Autonomous self-improvement | NO / FORBIDDEN | sandbox + evolution engine |

`compute_lesson_reuse` returns 1.0 if any retrieved kind is `LESSON` (CONFIRMED). That is **retrieval of a lesson**, not learning.

Lesson payload `what_worked` is hardcoded `"structured retrieval+critique"` (CONFIRMED).

---

## 14. FAILURE LEARNING AUDIT

| Topic | Status | Evidence |
|-------|--------|----------|
| Fingerprinting | IMPLEMENTED | SHA-256 of `failure_type|component|observed_failure` |
| Recurrence | IMPLEMENTED | `failure_stats.recurrence_count` |
| Similarity | PARTIAL | lexical/failure-intent retrieval, not a similarity model |
| Applicability | WEAK | domain `COGNITIVE_CORE` hardcoded in `store.record_failure` |
| False failure application prevention | IMPLEMENTED at retrieval | P4.2/P4.3; benchmark false_failure_application = 0 |
| Failure retrieval | IMPLEMENTED | `test_failure_learning_next_task_retrieves_failure` |
| Failure→lesson | PARTIAL | later lesson may mention `failures_seen=N` |
| Failure→hypothesis | OPTIONAL field | not automatic |
| Failure→experiment | OPTIONAL field | not automatic |

**Can AHOS recognize the same class of mistake and alter future reasoning?**  
**Retrieve: yes (CONFIRMED).**  
**Alter reasoning: no (CONFIRMED).** Inductive mode only interpolates `failures+lessons` into the conclusion sentence. Verdict still comes from keyword overlap / contradiction / stale / lesson-presence.

---

## 15. METACOGNITION AUDIT

`metacognitive_state()` records: what I know (fact IDs), don’t know (`unknowns`), why (`trace.steps`), supports, contradictions, assumptions, prior failures, experiment id, verdict, epistemic.

| Layer | Status |
|-------|--------|
| Metacognitive RECORDING | PARTIAL / IMPLEMENTED as a dict |
| Metacognitive REASONING | LABEL ONLY (mode appends counts; same verdict) |
| Metacognitive CONTROL | MISSING (cannot change retrieval, budget, tools, or stop/go except hardcoded refuse paths) |

Capability gaps and evaluation results are **not** fed back as control signals. `CapabilityRegister` is a file-backed gap list, not a metacognitive controller.

---

## 16. WORLD MODEL AUDIT

`current_world_model_status()` (CONFIRMED):

| Layer | Declared status |
|-------|-----------------|
| knowledge_graph | NOT_IMPLEMENTED |
| temporal_model | NOT_IMPLEMENTED |
| causal_model | NOT_IMPLEMENTED |
| probabilistic_relationships | PARTIAL (scoring/calibration elsewhere — not this layer) |
| counterfactual_reasoning | NOT_IMPLEMENTED |

`record_world_model_object()` may store payload kinds `ENTITY|RELATION|EVENT|STATE|CAUSE|EFFECT|UNCERTAINTY|TIME|OBSERVATION|COUNTERFACTUAL`. **Storing keys is not a world model** (module docstring and `WorldModelBoundary`).

| Class | Status |
|-------|--------|
| WORLD MODEL | MISSING (inventory + optional payload) |
| CAUSAL MODEL | MISSING |
| COUNTERFACTUAL ENGINE | MISSING generally; financial hindsight PARTIAL and domain-bound |

Not built in this audit.

---

## 17. TOOL INTELLIGENCE AUDIT

`plan_tools(_task)` returns `ToolSelectionPlan(status=NOT_IMPLEMENTED)` with a note that P3 does not select or execute tools.

| Layer | Status |
|-------|--------|
| TOOL INTERFACE | INTERFACE_ONLY (`plan_tools`) |
| TOOL SELECTION | MISSING |
| TOOL EXECUTION | MISSING (and forbidden here) |
| TOOL LEARNING | MISSING |

Broader repo has `architecture/tools/sandbox.py` (not inspected as a cognitive selector). Registry/capability discovery/cost/risk/reliability: **MISSING** in the cognitive loop.

`test_tool_selection_interface_only` exists.

---

## 18. AGENT ARCHITECTURE AUDIT

`architecture/cognitive/agents.py` builds **passports** from `config/agent_registry.yaml` and `PANEL_LENSES`. Every passport sets `memory_bearing=false`, `independent_tools=false`, `performance_tracked=false`.

| Feature | Status |
|---------|--------|
| Persistent agents | MISSING as cognitive processes |
| Agent identities | PARTIAL (registry ids + lens ids) |
| Agent memory | PARTIAL (namespace on memories; not agent-owned stores) |
| Specialization | PARTIAL (roles/lenses) |
| Goals / tool permissions | MISSING |
| Reliability / prediction / error history / calibration | MISSING (`performance_tracked=false`) |
| Debate / delegation / creation | MISSING (creation ACI-GAP-009) |

Agent passport ≠ autonomous agent (CONFIRMED by module docstring).

---

## 19. AI COUNCIL AUDIT

**What it is (CONFIRMED):** `architecture/council.py` — advisory, offline-capable, **no majority vote**, pairwise categorical disagreement on **injected** provider envelopes. Deterministic simulation of a protocol (`contracts/ai_council_contract_v1.json`).

**Classification:** advisory framework + deterministic simulation of injected claims.  
**Not:** a real multi-agent society, not 100 operating agents, not memory-bearing reasoners.

| Property | Status |
|----------|--------|
| Independent reasoning | NO — injected envelopes |
| Agent memory | NO |
| Distinct expertise | PARTIAL — lenses/registry labels |
| Can disagree | YES — CONFLICT in agreement matrix |
| Disagreement measured | YES — pairwise matrix |
| Historical accuracy / calibration | NO |
| Promote/demote | NO |
| Learn from disagreements | NO |

Do not claim a “100-agent Council.” No such runtime roster exists in the inspected code.

---

## 20. SELF-RESEARCH AUDIT

`build_self_research_report()` copies caller snapshot fields and emits typed unknowns/gaps. It **never** opens the soak DB.

| Stage | Status |
|-------|--------|
| 1 Identify knowledge gap | PARTIAL — hardcoded missing_capabilities + snapshot zeros |
| 2 Formulate research question | MISSING as a generator (`test_next` strings) |
| 3 Search for evidence | MISSING |
| 4 Evaluate sources | MISSING |
| 5 Compare explanations | MISSING |
| 6 Store findings | PARTIAL — report dataclass only |
| 7 Test findings | MISSING |
| 8 Detect uncertainty | PARTIAL — copied/flagged |
| 9 Propose improvement | MISSING here (evolution gate is separate) |
| 10 Evaluate whether improvement worked | MISSING |

Classification: **PARTIAL** snapshot formatter, not a research loop.

---

## 21. CONTROLLED EVOLUTION AUDIT

```text
WEAKNESS DETECTED          PARTIAL — human/tests/benchmarks; no autonomous detector
        ↓
IMPROVEMENT HYPOTHESIS     PARTIAL — diagnosis string on proposal
        ↓
CANDIDATE CHANGE           PARTIAL — candidate_diff_ref pointer
        ↓
SANDBOX                    PARTIAL — SandboxPolicy asserts; not an isolated exec harness
        ↓
TEST                       DOCUMENTED / caller-supplied test_battery list
        ↓
BENCHMARK                  EXISTING P4 evaluator; not auto-invoked by the gate
        ↓
ADVERSARIAL TEST           EXISTING benchmark family; not auto-invoked
        ↓
REGRESSION                 EXISTING pytest suites; not auto-invoked
        ↓
SECURITY                   EXISTING security overlay; not auto-invoked
        ↓
PERFORMANCE                UNCONFIRMED as a promotion gate
        ↓
GOVERNANCE                 IMPLEMENTED — B_ONLY only; LaneAChangeRequired otherwise
        ↓
PROMOTE / REJECT           IMPLEMENTED human approve; AI cannot approve
```

`propose_lane_b_evolution` never self-approves (CONFIRMED). `SelfEvolutionEngine` rejects AI approvers. Doctrine: Evolution A OFF / ACI-GAP-004.

Do not describe this as an operational closed evolution machine. It is a **proposal ledger + human gate**.

---

## 22. EVALUATION AUDIT

**What P4.1–P4.3 measure (CONFIRMED):** retrieval precision/recall/F1/@k, MATCH_REASON, lookalike/hard-mismatch/generic-overlap, namespace isolation, unknown refusal, false failure, contradiction pollution, critic *flag* rates, hypothesis falsification *string* present, lesson *retrieval* reuse, context coverage **averaged across four budgets**, reasoning *structure* rate.

**What they do not measure:** mode-differentiated inference, lesson application as constraint, experiment scientific quality, calibration curves, prediction accuracy over time, long-horizon improvement, tool selection, goal decomposition, world-model quality, counterfactual quality, self-correction as control, cross-domain transfer beyond thin adapters.

| Measurable today? | Status |
|-------------------|--------|
| retrieval quality | YES — synthetic labeled |
| reasoning quality | NO — structure/refusal only |
| hypothesis quality | NO — string falsification only |
| experiment quality | NO — placeholder codes |
| lesson reuse | YES as retrieval; NO as learning |
| failure reuse | YES as retrieval; NO as prevention |
| calibration | NO (loop); Lane B ledgers exist separately |
| prediction accuracy | NO in this vector |
| long-horizon improvement | NO |
| tool selection | NO |
| goal decomposition | NO |
| world-model quality | NO |
| counterfactual quality | NO |
| self-correction | NO (critic commentary) |
| cross-domain transfer | WEAK — four synthetic adapters |

**Limitations (CONFIRMED):** synthetic-only; small N (41 memories; 11 retrieval cases; 7 lookalike cases; 7 mode cases); deterministic reproducibility yes; ACI-GAP-010 open; benchmarks mix capability tests with fixture tests (`reasoning_mode_structure_rate`).

---

## 23. DOMAIN-GENERALITY AUDIT

| Component | Generality | Notes |
|-----------|------------|-------|
| Memory store / kinds / edges | DOMAIN-GENERAL | domain is a string field |
| Retrieval gates | DOMAIN-GENERAL | crypto not hardcoded in retriever |
| Context assembler | DOMAIN-GENERAL | |
| Reason/critic | DOMAIN-GENERAL mechanism; keyword-bound | |
| Hypothesis / experiment ledger | DOMAIN-GENERAL IDs | classification `COGNITIVE` |
| Loop adapters | DOMAIN-GENERAL thin wrappers | `finance/science/software/operations` set `domain=` only |
| Financial scoring / hindsight / paper_trading | DOMAIN-BOUND | adapters / frozen Lane A |
| Council protocol | DOMAIN-GENERAL | envelopes not market-specific |
| World-model inventory | DOMAIN-GENERAL (absent) | |
| Soak / discovery collectors | DOMAIN-BOUND | must stay adapters |

`test_domain_generality_four_adapters` exists. Core must remain import-free of `discovery` / `paper_trading` / `telegram_ai` (P3 test `test_p3_loop_must_not_import_lane_a_or_telegram`).

---

## 24. AGI/ACI GAP MATRIX

| Capability | Status | Evidence | Strongest implementation | Largest limitation | Critical blocker? |
|------------|--------|----------|--------------------------|--------------------|-------------------|
| PERCEPTION | PARTIAL | adapters + frozen collectors | observation daemon / adapters | no soak ingest into cognitive memory | No for isolated cognition; yes for live self-model |
| MEMORY | PARTIAL | P2 store | provenance + contradictions | not production-wired | No (substrate exists) |
| GROUNDING | PARTIAL | kinds + MATCH_REASON | refuse unknown; no silent AI facts | SYSTEM mis-label possible; failures as FACT | Yes for trustworthy inference |
| WORLD MODEL | MISSING | world_model.py | honest inventory | no entities/relations engine | Yes for causal/CF later; not today’s consumer |
| REASONING | PARTIAL | reason.py | refuse + contradiction + stale | one keyword verdict for 7 modes | **Yes — current competence ceiling** |
| CAUSALITY | MISSING | NOT_IMPLEMENTED modes | refuse pretended inference | no causal graph | Future blocker |
| COUNTERFACTUALS | MISSING | mode refuse; hindsight financial | refuse + no overwrite policy | no general engine | Future blocker |
| PLANNING | MISSING | no planner | — | TaskType labels only | No for current loop |
| GOALS | MISSING | ACI-GAP-008 | — | — | No for current loop |
| METACOGNITION | PARTIAL | state dict | recording | no control | Yes for self-correction |
| LEARNING | PARTIAL | write-back + retrieve | persistence | no policy change | Yes for ACI |
| SELF-CORRECTION | PARTIAL | critic flags | questions exist | does not constrain | Yes |
| TOOL USE | INTERFACE_ONLY | plan_tools | honest NOT_IMPLEMENTED | — | No until reasoner can choose |
| AGENT MEMORY | PARTIAL | namespaces | isolation | passports not agents | No |
| MULTI-AGENT SOCIETY | MISSING / PARTIAL protocol | council.py | disagreement matrix | injected envelopes | No |
| SELF-RESEARCH | PARTIAL | snapshot builder | typed unknowns | no search/test | No |
| CONTROLLED EVOLUTION | PARTIAL | engine + gate | human gate | not a closed gauntlet | Safety-critical to keep partial |
| GENERALIZATION | PARTIAL | domain string + adapters | four synthetic domains | synthetic only | Measurement gap |
| TRANSFER | UNCONFIRMED | no transfer benchmark | — | — | Measurement gap |
| CALIBRATION | PARTIAL elsewhere | scoring/ledger | Lane B calibration | not in cognitive loop | Not today’s loop bottleneck |
| LONG-HORIZON ADAPTATION | MISSING | no multi-episode policy | persistence only | synthetic two-step tests | Yes for ACI later |

---

## 25. COGNITIVE BOTTLENECK ANALYSIS

Scale (ordinal, not a fake precision score): **H / M / L** for Impact, Dependency, Current Weakness, Evidence strength, Safety (high = safe to improve in Lane B), Measurability, Reusability, AGI/ACI leverage.

| Candidate | Imp | Dep | Weak | Ev | Safe | Meas | Reuse | Leverage | Notes |
|-----------|-----|-----|------|----|------|------|-------|----------|-------|
| Residual retrieval cousins | L | L | L | H | H | H | M | L | 2/22 FPs; do not ignore, do not prioritize |
| Context intelligence | M | H | L–M | H | H | H | H | M | 0.5714 is budget-average artifact; normal=8 keeps 7/7 |
| **Typed evidence-bound reasoning** | **H** | **H** | **H** | **H** | **H** | **M** | **H** | **H** | Shared verdict; critic inert; ADV weak-supports |
| Critic-as-constraint alone | M | M | H | H | H | M | H | M | Subset of reasoning competence |
| Closed-loop learning | H | H | H | H | H | L | H | H | Blocked until reasoning consumes LESSON/FAILURE |
| World / causal / CF | H | future | H | H | H | L | H | H | No consumer; would be unused substrate |
| Evaluation expansion | M | M | M | H | H | H | M | M | ACI-GAP-010; does not raise competence |
| Tool intelligence | M | M | H | H | H | M | H | M | INTERFACE_ONLY; nothing to select toward |
| Agents / Council society | M | L now | H | H | H | L | M | H | Passports ≠ agents |
| Self-research loop | M | M | H | H | H | M | H | H | Snapshot only |
| Metacognitive control | M | H | H | H | H | M | H | H | Recording exists; control needs typed reasoning |

**Is retrieval the dominant bottleneck?** **No.** Proof: P4.3 precision/recall; residual FPs are two cousins; context at operating budget already includes the labeled relevant timeout set; the reasoner then applies one keyword rule.

---

## 26. SINGLE HIGHEST-VALUE NEXT CAPABILITY

### NEXT_CAPABILITY_PROPOSAL

1. **Capability name:** Typed evidence-bound reasoning  
   (mode-differentiated, critic-constrained inference over retrieved context)

2. **Exact current weakness:**  
   Seven modes share `_verdict_from_context`. Memory class is used as a skip-list (PREDICTION/OPINION/SIMULATION) and as display buckets. LESSON presence yields `WEAKLY_SUPPORTED` without applying applicability. FAILURE rows are also `OBSERVED_FACT` and can score as facts. Critic cannot veto. Certainty never reaches `SUPPORTED`, but `WEAKLY_SUPPORTED` still issues on several adversarial probes.

3. **Evidence:**  
   - `architecture/cognitive/loop/reason.py` (`IMPLEMENTED_MODES`, `_verdict_from_context`, downgrade, `critique_result` order)  
   - `tests/test_cognitive_loop.py` (lesson/failure *retrieval*, not verdict change)  
   - `architecture/cognitive/benchmark/evaluator.py` `reasoning_mode_structure_rate` definition  
   - `p4_3_retrieval_benchmark_latest.json` ADV-* verdicts  
   - Orchestrator lesson `applicability: task.domain`  
   - `record_failure` → `EpistemicKind.OBSERVED_FACT`

4. **Why current architecture cannot solve it:**  
   More retrieval gates add better bags of text. Context packing at budget 8 already delivers the labeled relevant set. Write-back already persists lessons. None of those change the inference rule.

5. **Why higher-value than alternatives:**  
   See §25 and §27.

6. **Dependencies:**  
   P2 kinds/edges, P3 loop, P4.2/P4.3 retrieval (good enough to feed). No new store, no embeddings, no soak ingest, no Lane A.

7. **Expected cognitive leverage:**  
   Same memories can produce different, inspectable conclusions by type; lessons/failures can constrain rather than merely appear; critic can block weak support; learning and experiments become testable instead of decorative.

8. **Measurable success criteria (for a later implementation phase — not done here):**  
   - Mode-differentiation metric: same context, different modes, *different required properties* (not just labels).  
   - Lesson-application metric: applicable lesson changes verdict or blocks an action class; inapplicable lesson does not.  
   - Failure-application metric: same-class failure constrains; false-class failure does not (keep P4.3 false-failure = 0).  
   - Critic-constraint metric: at least one seeded overclaim is downgraded *by critic flags*, not by the blanket SUPPORTED ban.  
   - Adversarial: `ADV-HYP` / `ADV-FIN-OPINION` / `ADV-LOOKALIKE` must not be `WEAKLY_SUPPORTED` without typed support.  
   - Retrieval P4.1–P4.3 recall/precision floors must not regress.  
   - No LLM judge, no threshold gaming, no corpus weakening.

9. **Safety boundaries:**  
   Lane B only. `PAPER_ONLY`. Autonomy ≤ `L1_ANALYZE`. No soak DB, no Lane A, no live execution, no auto-evolution, no production ingest.

10. **What MUST NOT be built yet:**  
    World-model/causal/CF engines; multi-agent society; tool execution; embeddings/vector DB; LLM semantic judges; residual-retrieval-only phase as the main bet; benchmark floor lowering; autonomous promotion.

---

## 27. WHY THIS CAPABILITY WINS

1. **Retrieval is no longer the ceiling.** P4.3 precision 0.91 / recall 1.0. Residual cousins are real but incremental.  
2. **Context is not the measured failure at operating budget.** `CTX-NORMAL` kept 7/7 relevant IDs. The 0.5714 coverage mean includes zero and tiny budgets by construction.  
3. **Learning is blocked by reasoning.** Lessons are already written and retrieved. They cannot change future inference until inference has typed slots.  
4. **World model would be unused substrate.** The current reasoner would ignore relations the same way it ignores lesson applicability.  
5. **Evaluation expansion without a new reasoning contract would keep passing `reasoning_mode_structure_rate` while modes stay labels.**  
6. **Domain-general:** typed consumption of evidence classes is not crypto-specific.  
7. **Safe and isolated:** changes belong in `loop/reason.py` (and tests/benchmarks), not soak or Lane A.

---

## 28. WHAT MUST NOT BE BUILT YET

- Another retrieval-only phase as the primary program (record residual FPs; do not make them the strategy).  
- Knowledge graph / causal / counterfactual engines (no consumer).  
- Memory-bearing multi-agent Council / agent creation.  
- Tool execution or tool-learning loops.  
- Vector databases, embeddings, LLM judges, RL.  
- Production cognitive ingest into the soak.  
- Live trading, autonomy above L1, self-approving evolution.  
- Silent class upgrades to make lessons look like facts.  
- Benchmark gaming (threshold cuts, deleting hard cases, fitting labels).  
- Parallel implementation of “ten missing capabilities.”

---

## 29. SAFETY / GOVERNANCE STATUS

| Control | Status | Label |
|---------|--------|-------|
| PAPER_ONLY | Unchanged | CONFIRMED |
| Autonomy ceiling L1_ANALYZE | Unchanged | CONFIRMED |
| Lane A freeze 36/36 | OK after read-only check | CONFIRMED |
| Soak untouched | This audit issued no soak I/O | CONFIRMED |
| Cognitive loop cannot authorize execution | `MemoryAuthorizationError` | CONFIRMED |
| Evolution B_ONLY / human gate | `LaneAChangeRequired`; AI cannot approve | CONFIRMED |
| One Python brain | Unchanged; TS/Telegram non-authoritative | CONFIRMED |
| This audit git policy | No branch, commit, push, reset, rebase | CONFIRMED |
| New dependencies | None added | CONFIRMED |

---

## 30. TEST / EVIDENCE SUMMARY

Do not equate “tests pass” with cognitive competence.

| Suite | Kind | What it proves | What it does not prove |
|-------|------|----------------|------------------------|
| `tests/test_cognitive_memory.py` (~16) | Unit | Store provenance, edges, isolation, consolidation bans | Live soak memory |
| `tests/test_cognitive_loop.py` (18) | Unit/integration (temp SQLite) | Retrieve lesson/failure; contradiction unresolved; adapters; refuses CF/causal; no Lane A import | Policy learning; production data |
| `tests/test_cognitive_core.py` (~13) | Unit | Contracts, ceiling, inventories | Operational cognition |
| `tests/test_cognitive_benchmark.py` | Synthetic benchmark | Metric wiring / thresholds | AGI; soak |
| `tests/test_retrieval_relevance.py` | Synthetic | P4.2 gates | Production retrieval |
| `tests/test_retrieval_lookalike.py` | Synthetic | P4.3 discrimination | Residual cousins gone |
| `tests/test_cognitive_panel.py` | Unit | Lenses | Agents |
| `tests/test_self_evolution_engine.py` etc. | Unit | Human gate | Closed evolution |
| P4.3 recorded 167 targeted tests | Mixed | Code correctness of the above | Cognitive capability beyond fixtures |

| Distinction | This audit |
|-------------|------------|
| CODE CORRECTNESS | Demonstrated in recorded P4.3 pytest (167 passed) — not re-run as a mutating audit |
| COGNITIVE CAPABILITY | Retrieval discrimination demonstrated; reasoning/learning not demonstrated as competence |
| PRODUCTION EVIDENCE | None from this phase; soak not used |

No production data, no long-horizon soak cognition, no real-runtime cognitive path in production.

---

## 31. ACTIVE SOAK / LANE-A STATUS

| Check | Result |
|-------|--------|
| Lane A modified? | NO — freeze 36/36 |
| Soak DB touched? | NO |
| Cognitive ingest into soak? | NO |
| Runtime restart? | NO |
| T0 reset? | NO |
| Audit actions | Read source, existing reports, `git` read-only, `freeze_lane_a.py` verify |

Active soak remains the owner’s Windows process (T0 / run_id as previously recorded in operational docs). This Cloud workspace did not attach to it.

---

## 32. LIMITATIONS

- Local checkout is the P4.3 feature branch, not `main`; `origin/main` contains merge `9765161`. Cognitive sources inspected match the P4.3 implementation line.  
- Benchmark numbers are quoted from committed P4.3 JSON, not re-executed in this audit (avoided new writes / package installs).  
- Did not inspect every Lane B scoring/calibration module in depth; those are outside the cognitive loop.  
- Council member *count* in YAML/lenses was not enumerated to a “100 agents” claim; passports are metadata.  
- Context-coverage mis-explanation in P4.3 report is documented here; that report was not edited.  
- Residual retrieval FPs remain real.  
- Synthetic, small-N, deterministic fixtures throughout.  
- No claim that typed reasoning is easy or complete AGI work.

---

## 33. FINAL RECOMMENDATION

**AUDIT BEFORE ARCHITECTURE.**  
Measure first: the stack can remember and retrieve with governed relevance. It cannot yet *reason by evidence class*.

**If exactly one major cognitive improvement is allowed next, it should be typed evidence-bound reasoning** — not another retrieval patch, not a world model, not a Council, not evaluation theater.

Human review is required before any implementation directive.

---

## Distinctions preserved

```text
DATA ≠ EVIDENCE ≠ MEMORY ≠ RETRIEVAL ≠ CONTEXT ≠ REASONING ≠ DECISION ≠ LEARNING ≠ IMPROVEMENT ≠ AUTONOMY

SIMILARITY ≠ RELEVANCE
RELEVANCE ≠ APPLICABILITY
APPLICABILITY ≠ TRUTH
MEMORY ≠ LEARNING
LEARNING ≠ IMPROVEMENT
IMPROVEMENT ≠ AUTONOMY
RETRIEVAL ≠ REASONING
REASONING ≠ INTELLIGENCE
BENCHMARK PASS ≠ AGI
```

P4.3 benchmark pass is evidence of **retrieval discrimination on a synthetic vector**, not intelligence.

---

## Capability matrix (audit §27 condensed)

| Capability | Status | Evidence | Current strength | Limitation | Cognitive importance |
|------------|--------|----------|------------------|------------|----------------------|
| Memory | PARTIAL | P2 store + tests | High (substrate) | Not soak-wired; FAILURE as FACT | High |
| Retrieval | IMPLEMENTED | P4.2/P4.3 | Highest demonstrated | 2 FPs; synthetic | High but not the bottleneck |
| Context | PARTIAL | context.py + CTX-* | Adequate at budget 8–20 | No reserved contradiction slots; 0.57 metric artifact | Medium |
| Evidence hierarchy | PARTIAL | kinds + write guards | Write-time AI block | Inference ignores types | High |
| Reasoning | PARTIAL | reason.py | Refuse/contradiction/stale | Shared keyword verdict | **Highest now** |
| Critic | PARTIAL | critique_result | Questions + flags | Commentary | High (as constraint) |
| Hypothesis | PARTIAL | HypothesisStore | Lifecycle + no silent SUPPORTED | Loop only proposes | Medium |
| Experiment | PLACEHOLDER | bridge + INSUFFICIENT_DATA | Provenance row | Not an experiment | Medium |
| Learning | PARTIAL | write-back | Persistence | No policy change | High |
| Failure learning | PARTIAL | fingerprint + retrieve | Recurrence counts | No reasoning change | High |
| Metacognition | PARTIAL | state dict | Recording | No control | Medium-high |
| World model | MISSING | inventory | Honesty | Absent | Future high |
| Causality | MISSING | NOT_IMPLEMENTED | Honest refuse | Absent | Future high |
| Counterfactuals | MISSING | mode refuse | Honest refuse | Financial hindsight ≠ engine | Future high |
| Tool intelligence | INTERFACE_ONLY | plan_tools | Honest stub | Absent | Medium |
| Agents | INTERFACE_ONLY | passports | Isolation fields | Not agents | Medium |
| Council | PARTIAL | council.py | Disagreement matrix | Injected envelopes | Medium |
| Self-research | PARTIAL | snapshot builder | Typed unknowns | No research loop | Medium |
| Controlled evolution | PARTIAL | gate + engine | Human gate | Not closed-loop | Safety-high |
| Evaluation | PARTIAL | P4.1–P4.3 | Retrieval measured | Reasoning quality unmeasured | High (instrument) |
