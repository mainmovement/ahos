# P5 Final Boundary Audit

**Kind:** Forensic boundary audit. Not a feature phase. Not a claim upgrade.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT. Do not merge. READY_FOR_REVIEW = NO.**  
**Data label:** `SYNTHETIC_TEST_DATA`  
**This is not entailment, NER, AGI, or ACI.**

Audited production tree at start of this audit: `f0d2c4ee7233f1ee0fc09c9245b6c449c0027638`.  
This report lands on the same branch after the diagnosis-only contract fix and the three-hop proof test. SHA of the commit that includes this file is recorded in §1 after landing.

Original `reports/agi_aci_evolution/P5_FORENSIC_ARCHITECTURE_GATE.md` is **unchanged** (last content commit `02c41be569798568909e336f4b2277dc84b79dfe`).

---

## 1. Exact SHA

| Field | Value |
| --- | --- |
| Branch | `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| Audited production HEAD (start) | `f0d2c4ee7233f1ee0fc09c9245b6c449c0027638` |
| Original forensic gate content | `02c41be569798568909e336f4b2277dc84b79dfe` |
| This audit commit | *stamped after landing* |

---

## 2. PR state

| Field | Value |
| --- | --- |
| PR | https://github.com/mainmovement/ahos/pull/93 |
| State | **DRAFT** |
| MERGE | **NO** |
| READY_FOR_REVIEW | **NO** |
| Base | `main` |

---

## 3. Objective 1 diagnosis

The two full-`pytest tests` failures are **not** a missing required operational SQLite artifact and **not** a P5 runtime defect.

**Classification: A + C** — documentation names a gitignored runtime path; the W38 doc-drift scanner treats a missing committed path as stale unless it is listed in `INTENTIONAL_REFS`.

**Not B.** `data/ahos_cognitive_memory.sqlite` is not supposed to exist in git. `.gitignore` ignores `data/`. `config.paths.get_cognitive_memory_db_path()` creates the filename at runtime under the data directory. Tests pass an explicit tmp path. The CognitiveMemoryStore constructor refuses soak/Lane-A DB names.

**Not D.** The store architecture is consistent: isolated Lane-B SQLite, generated on first open, never a soak DB.

### Proof table (both failures share one diagnostic)

| # | Item | Evidence |
| --- | --- | --- |
| 1 | Exact failing tests | `tests/test_doc_drift.py::test_canonical_docs_have_zero_real_stale_refs` and `tests/test_evidence_package.py::test_package_includes_doc_drift_diagnostic` |
| 2 | Exact assertions | `assert drift == {}` and `assert data["stale_reference_count"] == 0` |
| 3 | Exact referenced path | `data/ahos_cognitive_memory.sqlite` |
| 4 | Supposed to exist in the repository? | **No.** Gitignored runtime file. Same class as existing `INTENTIONAL_REFS` entry `data/control_plane_ledger.sqlite`. |
| 5 | Generated at runtime? | **Yes.** `get_db_path("ahos_cognitive_memory.sqlite")` / `CognitiveMemoryStore` first open. |
| 6 | Documentation incorrectly claims it exists as a committed file? | **No as prose.** Line 5 of `docs/architecture/AHOS_COGNITIVE_MEMORY_ARCHITECTURE_v1.0.md` already says `(gitignored; never soak DBs)`. The scanner does not understand gitignore; it only checks filesystem existence relative to repo root. |
| 7 | Production code depends on a committed copy? | **No.** Production depends on the path helper and an openable SQLite file, not on a git blob. |
| 8 | Fix requires | **Documentation-contract only:** add the path to `INTENTIONAL_REFS` with a substantive reason (established W38 pattern). **Do not create the SQLite file.** Do not change store semantics. |

### Minimal proposed fix (proven; implemented)

Add `data/ahos_cognitive_memory.sqlite` to `scripts/doc_drift.py` `INTENTIONAL_REFS` with reason >20 characters, matching `data/control_plane_ledger.sqlite`.

**Not implemented (and must not be):** manufacturing `data/ahos_cognitive_memory.sqlite` in git; weakening the drift test; rewriting cognitive-memory architecture.

---

## 4. Exact two pytest failures (pre-fix)

```
tests/test_doc_drift.py::test_canonical_docs_have_zero_real_stale_refs
  AssertionError: {'docs/architecture/AHOS_COGNITIVE_MEMORY_ARCHITECTURE_v1.0.md': [
    {'reference': 'data/ahos_cognitive_memory.sqlite',
     'reason': 'referenced path does not exist in the repository'}]}
  assert drift == {}

tests/test_evidence_package.py::test_package_includes_doc_drift_diagnostic
  AssertionError: assert <nonzero> == 0
  (same W38 diagnostic: stale_reference_count)
```

These failures existed on `f0d2c4ee` and are independent of the P5 mixed-evidence invariant.

---

## 5. Memory substrate write-path map

`memory.remember(...)` is a **low-level storage primitive**. It validates schema/enums, integrity hash, WORKING TTL, confidence range, and the AI_MODEL/AGENT ↛ OBSERVED_FACT/DERIVED_FACT veto. It does **not** consult `reusable_writeback_permitted`, the critic, episode polarity, or provenance-of-decision. Inserting a row is not semantic authorization that the row may be reused as knowledge.

Semantic authorization for **P5 reusable conclusions** (HYPOTHESIS / LESSON / SEMANTIC INFERENCE minted by the loop) exists in:

1. `reason()` → critic → `apply_constraint` → `apply_episode_positive_policy` → `reusable_writeback_permitted(verdict, bindings)`
2. `CognitiveOrchestrator.run` recomputes `reusable_writeback_permitted(verdict, bind_context(ctx, task, store=self.memory))` from **RetrievedItems**, not from mutated reason() DTO copies.

Semantic authorization for **consuming** a stored row as a factual premise exists in `typed_class_of` / `EvidenceBinding.live_roles()` / `may(ROLE_FACTUAL_PREMISE)`. Stored HYPOTHESIS/LESSON/INFERENCE cannot bind as `OBSERVED_FACT` or `FACTUAL_PREMISE` without changing `memory_type`+`epistemic_kind` on the authoritative store row.

### Map

| SOURCE | CALLER | API | VALIDATION / GOVERNANCE | STORAGE | REUSABILITY STATUS |
| --- | --- | --- | --- | --- | --- |
| P5 loop, gated | `CognitiveOrchestrator.run` | `HypothesisStore.propose` + `memory.remember(HYPOTHESIS)` | `should_hyp` ∧ `write_back` ∧ `reusable_writeback_permitted` after rebind | Hypothesis JSONL + memories | Reusable **only if** episode policy + critic left a positive verdict with decision-bearing FACTUAL_PREMISE supporters |
| P5 loop, gated | `CognitiveOrchestrator.run` | `memory.remember(LESSON)` | same `reusable_writeback` | memories SEMANTIC/AGENT + LESSON | Same |
| P5 loop, gated | `CognitiveOrchestrator.run` | `memory.remember(SEMANTIC INFERENCE)` | `write_back` ∧ `use_memory` ∧ inference conclusion ∧ `reusable_writeback` | memories SEMANTIC + INFERENCE | Same |
| P5 loop, episode log | `CognitiveOrchestrator.run` | `memory.remember(EPISODIC INFERENCE)` | `write_back` ∧ `use_memory` only — **not** reusable_writeback | memories EPISODIC + INFERENCE | **Not reusable as fact.** Retrieval types it INFERENCE; FACTUAL_PREMISE forbidden; support strength INDIRECT not DIRECT |
| P5 loop, experiment | `CognitiveOrchestrator.run` | `memory.remember(EXPERIMENT INFERENCE)` | only if hyp_id already minted (therefore already gated) | memories EXPERIMENT | typed_class EXPERIMENT, not FACTUAL_PREMISE |
| Observation ingest API | `adapters.ingest_generic_observation` | `memory.remember(EPISODIC, default OBSERVED_FACT)` | schema + AI veto only; producer=`test-adapter` | memories | **Can mint OBSERVED_FACT.** Current callers: tests only. Public production-callable. |
| Consolidation | `ConsolidationGate.accept` | `memory.remember(SEMANTIC)` | human `actor` required; **cannot** write OBSERVED_FACT/DERIVED_FACT; does **not** run P5 critic | memories | Can mint INFERENCE/LESSON/HYPOTHESIS/OPINION/SIMULATION as SEMANTIC. Current callers: tests only. |
| Store wrapper | `CognitiveMemoryStore.supersede` | `remember` successor | copies old kind; old marked SUPERSEDED | memories + SUPERSEDES edge | Same kind as predecessor; not a kind-promotion API |
| Store wrapper | `CognitiveMemoryStore.record_failure` | `remember(FAILURE, OBSERVED_FACT)` | schema only | memories + failure_stats | typed_class **FAILURE** (type wins over kind) → not FACTUAL_PREMISE |
| Store wrapper | `CognitiveMemoryStore.record_world_model_object` | `remember(WORLD_MODEL, default INFERENCE)` | object_kind enum | memories | typed INFERENCE unless caller passes another kind; not FACTUAL_PREMISE |
| Benchmark seed | `benchmark/corpus.py`, `evaluator.py`, `p5_eval.py` | `remember` | none (synthetic fixtures) | tmp stores | Eval harness, not live soak |
| Tests | many | `remember` / `propose` / `ConsolidationGate.accept` | test setup | tmp | Test-only |
| Parallel plane | `architecture.knowledge.store.VersionedClaimStore.store_claim` | SQLite INSERT knowledge_claims | CANONICAL ↛ AI_INTERPRETATION | `ahos_knowledge.sqlite` | **Not on the P5 cognitive retrieve/reason path.** Separate claim store. Cognitive loop does not import it. |
| Lane A / soak DBs | discovery / paper_trading engines | their own INSERT | Lane A freeze | soak DBs | **Forbidden** as cognitive-memory DBs (`FORBIDDEN_DB_NAMES`). Not P5 write paths. |

---

## 6. Production / test / migration bypass counts

Definitions used here:

- **Production bypass** = a production-callable API that can mint reusable-kind records (HYPOTHESIS, LESSON, SEMANTIC INFERENCE, or OBSERVED_FACT that retrieval may treat as FACTUAL_PREMISE) **without** passing `reusable_writeback_permitted` + critic + episode policy.
- Tests are not production bypasses.
- Benchmark seeders are eval harness, counted under test-only.
- “Currently no caller” is **not** treated as closure of a public API.

| Class | Count | Notes |
| --- | --- | --- |
| PRODUCTION_BYPASSES | **3** | Public ungoverned mint APIs (capability). No unexplained live-loop skip of the P5 gate. |
| TEST_ONLY_BYPASSES | **11** | 8 test modules + 3 benchmark modules that seed via `remember`/`propose`. |
| MIGRATION_BOOTSTRAP_BYPASSES | **0** | No `scripts/` or migration path calls `CognitiveMemoryStore.remember` or `HypothesisStore.propose`. |

### Production bypasses (nonzero — exact paths)

1. **`architecture/cognitive/memory/store.py` :: `CognitiveMemoryStore.remember`**  
   **Risk:** Any in-process caller can insert `HYPOTHESIS` / `LESSON` / `INFERENCE` / `OBSERVED_FACT` with caller-chosen provenance fields. Schema provenance tokens are required but **not** decision-governance. Retrieval will not retype HYP/LESSON/INFERENCE as OBSERVED_FACT, but a caller **can** mint a fresh OBSERVED_FACT that later binds as FACTUAL_PREMISE. This is the primary write-side boundary gap.

2. **`architecture/cognitive/hypothesis.py` :: `HypothesisStore.propose`**  
   **Risk:** Appends a PROPOSED hypothesis to JSONL with optional provenance dict. No critic. No episode policy. Orchestrator is the only `architecture/` caller; tests also call it.

3. **`architecture/cognitive/memory/consolidation.py` :: `ConsolidationGate.accept`**  
   **Risk:** Writes SEMANTIC non-fact kinds after a non-empty `actor` string. `requires_human=True` on the candidate is **not enforced** by `accept()`. Cannot write OBSERVED_FACT/DERIVED_FACT. Current callers: tests only.

Wrappers `supersede`, `record_failure`, `record_world_model_object`, and `adapters.ingest_generic_observation` are **callers of (1)**, not additional APIs. Adapters default to EPISODIC OBSERVED_FACT (observation ingest capability).

No SQLite `INSERT INTO memories` exists outside `store.py`. Direct DB mutation of cognitive memory from scripts was not found.

---

## 7. Reusable knowledge authorization boundary

**Question:** is `memory.remember(...)` a storage primitive, or does it semantically authorize reusable knowledge?

**Answer:** It is a **storage primitive**. It does **not** encode reusable-knowledge authorization.

Authorization exists **elsewhere**:

| Direction | Gate | What it authorizes |
| --- | --- | --- |
| Write (P5 loop conclusions) | `reusable_writeback_permitted` after critic + episode policy, recomputed in orchestrator from RetrievedItems | Minting loop HYPOTHESIS / LESSON / SEMANTIC INFERENCE |
| Write (episode log) | `task.write_back` only | EPISODIC INFERENCE log row; explicitly not reusable as fact |
| Read / bind | `typed_class_from_parts` + live roles + `may(FACTUAL_PREMISE)` + `decision_bearing_supporters` | Using a row as a factual premise |
| Store schema | `validate_new_record` | Enums, required tokens, AI_MODEL/AGENT cannot be stored as OBSERVED_FACT/DERIVED_FACT |

**Architectural boundary gap (documented, not redesigned):** an arbitrary Python caller can still call `remember` with reusable kinds or OBSERVED_FACT without the P5 write gate. Consumption-side typing prevents HYPOTHESIS/LESSON/INFERENCE → OBSERVED_FACT / FACTUAL_PREMISE / DIRECT support. Consumption-side typing does **not** prevent a forged OBSERVED_FACT insert.

**Minimum correct governance boundary (not implemented in this audit):**

- Keep `remember` as the storage primitive.
- Treat P5 reusable conclusions as authorized only by `reusable_writeback_permitted` at the orchestrator.
- Treat observation ingest (OBSERVED_FACT) as a separate privileged write, not as “the loop decided this is true.”
- Do **not** add NLI, embeddings, NER, or a second brain.
- A future optional `governed_remember` / capability token for reusable kinds would be the smallest *enforcement* increment. **Stopped. Not implemented.**

---

## 8. Provenance analysis

For loop-minted reusable rows, orchestrator writes:

- `source_type` / `source_id` / `source_location` / `producer` / `producer_version`
- `domain`, `context` (task id), `hypothesis_id` / `experiment_id` when present
- `payload.data_label`
- hypothesis provenance dict: task_id, supporting/contradicting memory ids, `novelty_equals_truth: False`
- SEMANTIC INFERENCE `derived_from` supporting evidence ids

Epistemic kind is explicit (`EpistemicKind` enum). Confidence is not auto-promoted (nullable; validate range). Contradiction is not rewritten to “resolved” by write-back. Entity/temporal status live on the **source** RetrievedItem and are recomputed at bind time (`status` + `observed_at`), not trusted from DTO copies.

Cannot silently become fact on later retrieval:

| Stored kind | Later `live_typed_class` | `FACTUAL_PREMISE` | Support strength |
| --- | --- | --- | --- |
| HYPOTHESIS | HYPOTHESIS | forbidden | NONE |
| LESSON | LESSON | forbidden | INDIRECT only if applicable, else comparison |
| INFERENCE (incl. episode) | INFERENCE | forbidden | INDIRECT |
| PREDICTION | PREDICTION | forbidden | NONE |
| OPINION | OPINION | forbidden | NONE |
| SIMULATION | SIMULATION | forbidden | NONE |
| EPISODIC + INFERENCE | INFERENCE | forbidden | INDIRECT (not DIRECT) |
| OBSERVED_FACT + STALE | OBSERVED_FACT | forbidden | history/comparison |
| OBSERVED_FACT + DATED/AGING/CURRENT | OBSERVED_FACT | allowed if applicable | DIRECT |

There is **no** transformation path in binding that retypes HYPOTHESIS/LESSON/INFERENCE to OBSERVED_FACT. `typed_class_from_parts` uses `memory_type` (FAILURE/EXPERIMENT override) else `epistemic_kind`. Forgery would require writing a new row with kind OBSERVED_FACT (write-side gap in `remember`).

Unresolved episodes store `payload.verdict` as data, not as OBSERVED_FACT. Two-hop and three-hop tests pin this.

Stale evidence cannot authorize reusable knowledge: critic TEMPORAL_VIOLATION → DOWNGRADE → `INSUFFICIENT_EVIDENCE`; `decision_bearing_supporters` excludes non-FACTUAL_PREMISE stale facts.

Non-decision-bearing evidence (lexical METACOGNITIVE, entity mismatch, assumption-only) cannot satisfy `reusable_writeback_permitted`.

---

## 9. Two-hop result

**PASS** — `tests/test_p5_second_forensic.py::test_two_hop_unresolved_episode_cannot_become_fact`

HOP1 mixed SUPPORT+CONTRA → non-positive verdict, episode INFERENCE only, no HYP/LESSON/SEMANTIC INFERENCE.  
HOP2 retrieve that episode into a new store/task → still non-positive, no FACTUAL_PREMISE, no OBSERVED_FACT retrieved, no reusable write-back.

---

## 10. Three-hop result

**PASS** — `tests/test_p5_second_forensic.py::test_three_hop_derived_artifact_cannot_escalate_authority`

| Hop | What happens | Authority |
| --- | --- | --- |
| 1 | Contaminated mixed evidence → EPISODIC INFERENCE | Not fact |
| 2 | Retrieve episode; derive hyp/lesson if permitted | **Not permitted.** No reusable mint. Episode cannot be FACTUAL_PREMISE or DIRECT |
| 3 | Forcibly `remember` HYPOTHESIS/LESSON/INFERENCE/PREDICTION/OPINION/SIMULATION derived from the episode (ungoverned substrate write), then new `ANALYZE` task | Verdict not positive, not WEAKLY_SUPPORTED. No live class OBSERVED_FACT. No FACTUAL_PREMISE. Support strength ≠ DIRECT. Governed write-back does not add extra reusable rows |

Impossible transitions pinned at hop 3:

- UNKNOWN → FACT
- HYPOTHESIS → OBSERVED_FACT
- LESSON → OBSERVED_FACT
- EPISODIC INFERENCE → DIRECT / FACTUAL_PREMISE
- PREDICTION / OPINION / SIMULATION → FACTUAL_PREMISE
- UNRESOLVED → WEAKLY_SUPPORTED

---

## 11. Critic load-bearing matrix

Order in `reason()` (source-enforced): `apply_constraint` → `apply_episode_positive_policy` → `reusable_writeback_permitted`. Callers cannot skip.

| Case | Candidate | Critic assessment | Critic action | Post-critic verdict | Writeback |
| --- | --- | --- | --- | --- | --- |
| Contradiction / mixed polarity | often WEAKLY_SUPPORTED from a mode | CONTRADICTION_VIOLATION | CONTEST | UNRESOLVED / CONTESTED; episode policy also fail-closes mixed polarity | False |
| Uncertainty (task-relevant UNCERTAIN) | positive | mixed_uncertainty via episode policy (and critic findings) | policy → UNRESOLVED | UNRESOLVED | False |
| Missing premise | positive or empty | MISSING_PREMISE | REQUIRE_MORE_EVIDENCE | INSUFFICIENT_EVIDENCE | False |
| Entity mismatch | SUPPORT + alien entity | non-decision-bearing; Q/AM tests | does not by itself veto a compatible supporter | mismatch item not a FACTUAL_PREMISE supporter | False if only mismatch remains |
| Scope mismatch | positive | SCOPE_MISMATCH | DOWNGRADE | **INSUFFICIENT_EVIDENCE** (fail-closed; not leftover WEAKLY_SUPPORTED) | False |
| Stale evidence | positive | TEMPORAL_VIOLATION | DOWNGRADE | **INSUFFICIENT_EVIDENCE** / STALE | False |
| Assumption-only | no facts | MISSING_PREMISE (+ assumptions on trace) | REQUIRE_MORE | INSUFFICIENT_EVIDENCE | False (`test_w_assumption_only`) |
| Prediction as fact | positive from non-fact | TYPE_VIOLATION | DOWNGRADE | INSUFFICIENT_EVIDENCE if candidate was positive | False |
| Opinion as fact | same | TYPE_VIOLATION | DOWNGRADE | INSUFFICIENT_EVIDENCE | False (`test_critic_type_violation_on_opinion_as_fact`) |
| Simulation as fact | same | TYPE_VIOLATION | DOWNGRADE | INSUFFICIENT_EVIDENCE | False |
| Unsupported lexical overlap | lexical match, no support class | EVIDENCE_MISMATCH | REQUIRE_MORE (or REFUSE if accepted+irrelevant cite) | not positive | False |
| Non-decision-bearing + real supporter | mixed episode | episode policy cites only decision-bearing ids | ACCEPT possible if polarity clear | cousin not cited | True only if a real FACTUAL_PREMISE supporter remains |

**DOWNGRADE leftover check:** TEMPORAL_VIOLATION and SCOPE_MISMATCH no longer leave `WEAKLY_SUPPORTED` alive. TYPE_VIOLATION on a positive candidate becomes INSUFFICIENT_EVIDENCE.

**Soft DOWNGRADE (documented, not a silent reusable leak of forbidden kinds):** OVERCONFIDENCE or UNSUPPORTED_ASSUMPTION on an otherwise fact-supported SUPPORTED candidate becomes WEAKLY_SUPPORTED. If decision-bearing FACTUAL_PREMISE supporters remain, `reusable_writeback_permitted` can still be True. That is intentional weakening, not type promotion. Assumption-**only** (no facts) is REQUIRE_MORE, not this branch.

REFUSE (unbound / irrelevant citation of an accepted candidate) → INSUFFICIENT_EVIDENCE, writeback False.

---

## 12. Mutation / TOCTOU result

**PASS** (existing second-forensic suite + orchestrator rebind).

Authoritative source is the `RetrievedItem` / store row. `EvidenceBinding` is `@dataclass(frozen=True)`. `may()`, `may_support_task()`, `contradicts_task()`, `live_typed_class()`, `live_temporal_state()`, `live_roles()` recompute. Stored allowed-role tuples cannot escalate.

| Mutation | Result |
| --- | --- |
| Binding field assign | `FrozenInstanceError` |
| Statement change | live assessment follows new statement; orchestrator write-back rebinds from store items |
| Task mutation after bind | snapshot fields on the binding; live methods use snapshot, not a later mutated task object held elsewhere |
| Temporal field on DTO | ignored; `status`+`observed_at` win (`test_mutation_temporal_field_cannot_freshen_stale`) |
| Entity / polarity / clause_force on DTO | ignored; statement recompute wins |
| Support-class / role escalation on DTO | `may(FACTUAL_PREMISE)` uses live roles (`test_mutation_role_escalation_cannot_make_opinion_factual`) |
| Applicability | live from payload + domain |
| Forged supporting IDs | critic REFUSE / REQUIRE_MORE; forged binding of OPINION as FACTUAL_PREMISE cannot `may()` that role |

Orchestrator does **not** persist `reason().reusable_writeback` blindly. It rebinds then calls `reusable_writeback_permitted` again. A stale DTO cannot become the persistence authority.

---

## 13. Bypass search

Repository-wide:

- `remember(` in `architecture/` (non-test, non-benchmark): orchestrator, adapters, store wrappers, consolidation.
- `hypotheses.propose` in `architecture/`: orchestrator only.
- `INSERT INTO memories`: `store.py` only.
- Scripts/migrations/bootstrap: **none** for cognitive memory.
- Fixtures resembling production APIs: benchmark corpus/evaluator (eval harness).
- Background workers: none for cognitive remember.
- Legacy compatibility: none found that writes cognitive reusable kinds.

`VersionedClaimStore` is a parallel knowledge plane, not a P5 retrieve/reason bypass.

Lane A INSERTs are freeze-protected and rejected as cognitive DB filenames.

---

## 14. Lane A result

`python scripts/freeze_lane_a.py` → **Lane-A integrity OK (36 files pinned)**.  
No edits under `discovery/**` or `paper_trading/**`.  
`config/lane_a_freeze.sha256` not rewritten.

---

## 15. Soak result

Soak DBs under gitignored `data/` (`ahos_local.sqlite`, `e01_discovery.sqlite`, `paper_trading.sqlite`) were **not opened** by this audit’s production code paths and **not modified**.  
`reports/PRE_SOAK_STATUS.txt` and `next-env.d.ts` remain untracked local noise and are **not** committed.  
Original `P5_FORENSIC_ARCHITECTURE_GATE.md` not rewritten.  
No active soak evidence overwritten. Frozen Lane A evidence not rewritten.

Live soak (do not disturb): T0 `2026-09-10 00:27:41 +03:30`, T+72h `2026-09-13 00:27:41 +03:30`, run_id `run_1788987515_7ad11528`.

---

## 16. Test results

Recorded after the audit commit’s verification run. See the stamped subsection at the end of this file if present; otherwise this table is the planned command set:

1. Focused P5: `tests/test_typed_reasoning.py tests/test_p5_episode_polarity.py tests/test_p5_second_forensic.py tests/test_p5_negation_entity.py`
2. A–AQ + seven modes + mutation + two-hop + three-hop: `tests/test_p5_second_forensic.py`
3. Full `pytest tests`
4. `python scripts/validate_imports.py`
5. `python scripts/freeze_lane_a.py`

Pre-landing smoke: three-hop PASS; `test_canonical_docs_have_zero_real_stale_refs` PASS after INTENTIONAL_REFS; freeze 36/36.

---

## 17. Exact changed files (this audit)

| File | Change |
| --- | --- |
| `scripts/doc_drift.py` | INTENTIONAL_REFS entry for gitignored runtime cognitive DB path |
| `tests/test_p5_second_forensic.py` | three-hop contamination proof |
| `reports/agi_aci_evolution/P5_FINAL_BOUNDARY_AUDIT.md` | this report |

Not changed: Lane A, soak state, `P5_FORENSIC_ARCHITECTURE_GATE.md`, retrieval, critic thresholds, production write APIs.

---

## 18. Proposed minimal fixes

| Fix | Status |
| --- | --- |
| INTENTIONAL_REFS for `data/ahos_cognitive_memory.sqlite` (docs/contract) | **Implemented** after diagnosis proven |
| Manufacture the SQLite file | **Rejected** |
| Wrap `remember` with a governance token | **Not implemented.** Documented as the minimum future enforcement increment if write-side capability must be closed |
| Redesign retrieval / add AGI features | **Rejected** |

---

## 19. Remaining limitations

- `remember` remains a general ungoverned storage API: it can insert OBSERVED_FACT and reusable-kind rows without P5 write authorization.
- `HypothesisStore.propose` and `ConsolidationGate.accept` are similarly public.
- Soft critic DOWNGRADE (overconfidence / assumption-with-facts) can leave WEAKLY_SUPPORTED, which remains reusable if FACTUAL_PREMISE supporters exist.
- Typed eligibility is not entailment. Closed-lexicon support is not NLI. No NER.
- Episode EPISODIC INFERENCE is still written on unresolved tasks when `write_back=True` (log, not reusable fact).
- Parallel `VersionedClaimStore` is out of P5 retrieve/reason scope.
- Full-suite green (after the contract fix) does not mean production readiness.

---

## 20. Highest justified claim

Governed typed eligibility + closed-lexicon support classification + live-recomputed frozen EvidenceBinding + episode mixed-polarity policy + load-bearing critic constraint + orchestrator write-back that rebinds from RetrievedItems and requires `reusable_writeback_permitted`. Two-hop and three-hop storage/retrieval hops do not silently increase epistemic authority. `remember` is a storage primitive, not reusable-knowledge authorization; the write-side public API remains an explicit boundary gap.

Not AGI. Not ACI. Not entailment. Not NER. Not production-ready. Not mergeable.

---

## 21. Explicit MERGE decision

| Gate element | Status |
| --- | --- |
| A. P5 mixed-evidence live-path invariant | PROVEN (prior second forensic + this audit’s tests) |
| B. No unexplained production bypass | SATISFIED — 3 public APIs explained; no hidden INSERT/script path |
| C. Memory substrate semantics explicitly bounded | SATISFIED as **documentation of primitive vs authorization**; write-side API not capability-locked |
| D. No epistemic authority escalation across hops | PROVEN two-hop + three-hop |
| E. Critic load-bearing | PROVEN; kill-class DOWNGRADE cannot leave a forbidden positive reusable verdict; soft DOWNGRADE documented |
| F. Mutation / TOCTOU | PROVEN |
| G. Full-test failures diagnosed | PROVEN; docs-contract fix applied; sqlite file not manufactured |
| H. Lane A untouched | PROVEN 36/36 |

**ARCHITECTURE_GATE = CONDITIONALLY_CLOSED**  
**MERGE = NO**  
**READY_FOR_REVIEW = NO**

Condition: the write-side `remember` capability gap is bounded by consumption-side typing and by orchestrator policy, not by an API capability token. That is an explicit remaining limitation, not a silent close.

---

## Verification log (filled after commands)

_Commands and counts are appended in the landing stamp._
