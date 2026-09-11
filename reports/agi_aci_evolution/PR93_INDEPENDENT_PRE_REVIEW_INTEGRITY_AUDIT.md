# PR #93 — independent pre-review integrity & readiness audit

**Kind:** Read-only architect / security / test / release-quality audit of the **entire** PR, not a P5 re-implementation.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT** (`isDraft=true`, `state=OPEN`)  
**Title (current):** `P5 ObservationGrant V4-PIN implementation (DRAFT — not ready for review)`  
**Base:** `origin/main` `976516123b0b682e99fcc6e9c6f0efabb91a9495`  
**Head:** `cursor/agi-aci-p5-typed-evidence-reasoning-9500` `311716fd0d06809c6c071e08bf988b65079ec27b`  
**V4-PIN code SHA:** `afdff2539943441244d05478a7004bc4bcc5976f`  
**Code vs V4-PIN:** `git diff --stat afdff25..HEAD -- architecture tests` → empty  

This audit does **not** reopen P5 unless contradictory evidence appears. None did.

This audit does **not** decide merge, Ready-for-Review, production release, live trading, or AGI/ACI.

```text
P5_SECURITY_EXIT (prior, independently established) = SECURITY-EXIT-CANDIDATE
This audit found no contradictory production-valid authority bypass.
```

Not AGI. Not ACI. Not production-ready. Not live trading.

---

## 1. Executive conclusion

**PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL**

The PR is a **coherent Lane-B P5 cognitive-stack evolution** (typed evidence → polarity → memory authorization → ObservationGrant V3 → V4-PIN). Production authority topology matches the security-exit record. This audit independently re-ran the full pytest suite on HEAD: **2065 passed, 3 skipped**. Lane A freeze **36/36**. Soak paths unchanged vs `origin/main`. Paper-only execution boundary intact.

It is **not** yet structurally ready for a *formal* review as currently packaged, for non-security reasons:

1. **Reviewer-facing scope mismatch.** The title names only V4-PIN. The diff vs `main` is the **entire P5 program** (65 files, +24670/−188, 57 commits), including typed reasoning, critic, polarity, memory authorization, and a large historical report corpus.
2. **Living evidence indexes lag the final tree.** `TEST_EVIDENCE.md` still records P5 as **28** tests / **195** envelope. `EVOLUTION_INDEX.md` stops at records 0008/0009 and does not point at V3/V4, residual review, or the closure gate. A reviewer who starts at those files would be misled about what this PR now is.

Neither item is a production authority bypass. Both **should be resolved before formal review** (title/body + index pointers). Do not split the stack into unrelated PRs; the commits tell one story.

**MERGE = NO. READY_FOR_REVIEW = NO.** This audit does not mark Ready and does not merge.

---

## 2. PR scope map

Classification of `origin/main...HEAD`. Untracked local noise (`next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt`) is **not** in the candidate.

| Class | Files | Keep in #93? |
| --- | --- | --- |
| **1. P5 security implementation** | `architecture/cognitive/loop/orchestrator.py`, `binding.py`, `reason.py`; `architecture/cognitive/memory/observation.py`; `store.py` (grant strip on revise/supersede; world-model refuses `OBSERVED_FACT`); `adapters.py` (cannot mint `OBSERVED_FACT`) | **Yes** — required |
| **2. P5 tests** | `tests/test_p5_*.py`, `tests/test_typed_reasoning.py`, `tests/test_evidence_support.py`, `tests/observation_test_runtime.py`, `tests/p5_grant_fixtures.py`, plus loop/benchmark test deltas | **Yes** |
| **3. P5 documentation** | `reports/agi_aci_evolution/P5_*.md` (typed-reasoning through V4-PIN + closure gate) | **Yes** as history; living index is stale (finding) |
| **4. Supporting architecture** | `loop/context.py`, `contracts.py`, `episode.py`, `inference.py`, `modes.py`, `support.py`; `benchmark/evaluator.py`, `p5_eval.py`, `thresholds.py`; `loop/benchmark.py` | **Yes** — P5 product, not V4-only |
| **5. Supporting infrastructure** | `scripts/doc_drift.py` (+2 lines: gitignored cognitive sqlite path explanation) | **Yes** — tiny, related |
| **6. Evidence/reporting** | `EVOLUTION_RECORD_0008..0010`, `CAPABILITY_MATRIX.md`, `GAP_REGISTER.md`, `TEST_EVIDENCE.md`, `EVOLUTION_INDEX.md`, `P4_4_COGNITIVE_STACK_FORENSIC_AUDIT.md` | **Yes** as history; **indexes need a current-law pointer** before formal review |
| **7. Unrelated change** | None in git vs `main` | n/a |
| **8. Generated artifact** | `p5_typed_evidence_reasoning_latest.json` (1699 lines) | **Yes** as dated synthetic-benchmark evidence, not as authority |
| **9. Suspicious / unclear** | None found | n/a |

**Non-P5-security items — required by P5 product?** Yes. Typed binding, modes, critic, polarity, and memory write APIs are the stack V4-PIN constrains. Removing them would leave ObservationGrant without its consumer.

**Risk of keeping them in #93?** Review cost and title mismatch, not a hidden trading or Lane A risk.

**Separate PR?** **No.** Splitting would orphan authority tests from the reasoning consumer. **Do** retitle/describe the PR as the full P5 stack before formal review.

---

## 3. Commit-history assessment

57 commits `origin/main..HEAD`. Pattern: design-only report → implement → stamp SHA. That is evidence discipline, not cleanup theater.

| Observation | Assessment |
| --- | --- |
| Accidental scope expansion | **No.** Growth is sequential P5: typed reasoning → precision → polarity → memory auth → ObservationGrant → V3 C1 → V4-PIN → audits. |
| Reverted security | V3 added constructor/ContextVar rekey; V4 **removed** it. Final tree is V4-PIN, not a mix. |
| Duplicate implementations | `reason()` (public fail-closed bind + evaluate) vs `evaluate_reason()` (orchestrator path) is an **intentional** split, not a fork. |
| Abandoned approaches | Design docs for Hybrid-D / V3 DI remain as history. Production `__init__` has no `secret=` / `**kwargs`. |
| Test-only fixes | `6377528` (fixtures + `clear_grant_verify_context` helper); `afdff25` (point order test at `evaluate_reason`). |
| Report-only after code tip | `404830b`…`311716f` — reports only; architecture/tests frozen at `afdff25`. |
| Commits contradicting later architecture | V3 reports describe V3. They are **historical**. Current code matches V4 reports. Living indexes do **not** yet say so. |
| Generated artifacts | One JSON benchmark dump, dated to early P5. |
| Hidden behavior in “test” commits | `6377528` added production `clear_grant_verify_context()` (ContextVar reset). **Not** an authority source. Documented as metadata-only. |

**Final tree tells one architectural story:** retrieved memory is not fact until instance-owned grant verification says so; write-back cannot launder caller DTOs.

---

## 4. Code / report consistency

| Document | Matches `afdff25` production tree? |
| --- | --- |
| `P5_V4_IMPLEMENTATION_REPORT.md` | **Yes** for files and topology (treated as claim list; re-traced). |
| `P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | **Yes** (code identity). |
| `P5_V4_FINAL_RESIDUAL_BOUNDARY_REVIEW.md` | **Yes** for R1–R6 vs source. |
| `P5_FINAL_CLOSURE_GATE_REVIEW.md` | **Yes**; I1–I15 still hold; this audit found no contradictory bypass. |
| Tests | V4 suite attacks production `CognitiveOrchestrator`; positives that need a known key use `TestCognitiveOrchestrator` **after** `super().__init__()`. |
| `TEST_EVIDENCE.md` P5 section | **Stale vs HEAD.** Claims 28 P5 tests / 195 envelope. Current `test_typed_reasoning.py` has 37 `test_*`; P5 `test_p5_*.py` add 173 `test_*`; this audit’s full suite is **2065 passed**. |
| `EVOLUTION_INDEX.md` | **Incomplete.** Lists 0008/0009 typed-reasoning; omits 0010, ObservationGrant, V3/V4, closure gate. |
| Early P5 audits (`P5_TYPED_EVIDENCE_REASONING_AUDIT.md`, etc.) | Consistent **with their SHAs**, not with the V4-PIN tip. Must not be read as current law. |

No current V4 report claims production readiness, live trading, or AGI/ACI achieved.

---

## 5. Authority topology (reconstructed, not modified)

```text
Evidence (MemoryRecord / RetrievedItem)
  → Acquisition (caller ObservationAuthority / BoundIngestPort / tests-only adapter)
  → Persistence (payload["observation_grant"]; revise/supersede strips grant if statement changes)
  → Retrieval (ordinary evidence; no ContextVar push)
  → Binding
        public bind_item / reason()     → grant_ok=False always
        O._bind_item                    → grant_ok = verify(..., key=O._grant_verify_secret)
  → Grant verification (explicit key required; ContextVar ignored)
  → CognitiveOrchestrator.run (owns K_O = os.urandom(32); issuer = ISSUER_ID)
  → evaluate_reason (consumes O-produced bindings only on the run path)
  → Memory write-back (rebind via O._bind_context; reusable_writeback_permitted)
```

| Where | What |
| --- | --- |
| Created | `ObservationAuthority._mint` / `BoundIngestPort` (caller mint). Production `O` has **no** mint adapter (R5). |
| Verified | `verify_observation_grant(key=...)`; production only via `O._permits_observation_grant`. |
| Transformed | Bind-time `grant_ok` → roles. Public assembler can set the **flag** (R1) but `O.run` does not consume caller bindings. `CognitiveResult` has **no** `bindings` field. |
| Persisted | Grant dict in payload. SQLite cannot satisfy production HMAC without `K_O`. |
| Replayed | Rows / retrieve / n-hop lessons. Re-verified or fail-closed. |
| Rejected | `key is None`; alien HMAC/issuer; ContextVar; public `reason`/`bind_*`; adapters minting `OBSERVED_FACT`; world-model `OBSERVED_FACT`. |

**No new caller-controlled production authority path** appeared in the non-V4 files (`modes`, `support`, `p5_eval`, contracts). Benchmarks call public `reason()` (fail-closed) or a fresh `CognitiveOrchestrator()` (instance `K_O`, no caller secret).

P5 is **not reopened.**

---

## 6. Public API / trust-boundary assessment

`architecture.cognitive.loop.__all__` exports `CognitiveOrchestrator` and contracts, not bind/grant helpers. `__all__` is **not** a security boundary.

| Surface | Class |
| --- | --- |
| `CognitiveOrchestrator.__init__` (no `secret=` / `issuer=` / `**kwargs`) | **SAFE** |
| `O.run` / `O._permits_observation_grant` | **SAFE** |
| `verify_observation_grant` (explicit `key`; ignores ContextVar) | **SAFE** |
| public `reason()` / `bind_item` / `bind_context` (`grant_ok=False`) | **SAFE** |
| `assemble_evidence_binding(grant_ok=True)` | **DOCUMENTED-RESIDUAL** + **REGRESSION-PRONE** (R1) |
| `push_grant_verify_context` / `GrantVerifyContext` | **DOCUMENTED-RESIDUAL** + **REGRESSION-PRONE** (R3) |
| `clear_grant_verify_context` | **SAFE** (reset only) |
| `O._grant_verify_secret` readability | **DOCUMENTED-RESIDUAL** (R2) |
| `BoundIngestPort` / `ObservationAuthority(secret=)` | **DOCUMENTED-RESIDUAL** (R4) — caller mint ≠ `O.run` accept |
| `run(now=)` | **DOCUMENTED-RESIDUAL** (R6) — episode clock |
| `ingest_generic_observation` | **SAFE** (refuses `OBSERVED_FACT`) |
| `store.remember` still allows `OBSERVED_FACT` rows | **SAFE** for production authority (I7/I8: label ≠ HMAC) |
| `evaluate_reason(bindings=)` | **REGRESSION-PRONE** if a future `run` forwarded caller bindings; **currently** only `O._reason_episode` supplies them on the production path |
| tests-only `TestCognitiveOrchestrator` / `grant_verify_scope` | **SAFE** if they stay out of `architecture/` (they do) |

No API upgraded from residual to **SECURITY-CONCERN** without new evidence.

---

## 7. Test integrity

This audit re-ran P5 grant suites earlier in the security-exit work and **re-ran the full suite on this HEAD** (below).

| Category | Genuine? | Notes |
| --- | --- | --- |
| Positive authorization | **Yes, with declared fixture** | `TestCognitiveOrchestrator` pins `K_O` **after** production `__init__`. Same `run()` / `_permits_observation_grant`. Not a production mint adapter (R5). |
| Negative / adversarial vs production `CognitiveOrchestrator` | **Yes** | `tests/test_p5_v4_authority_boundary.py` constructs production `O` and forges HMAC/issuer/ContextVar/retriever/memory. |
| Cross-orchestrator | **Yes** | `test_k_o1_grant_not_valid_for_o2` |
| Caller HMAC / issuer / ContextVar | **Yes** | V4 `test_a`, `test_i`, `test_cde`, `test_e`, `test_j` |
| Malicious retriever / memory / SQLite | **Yes** | `test_f`, `test_g`, `test_l` |
| Revision / TOCTOU / canonical mutation | **Yes** | V4 `test_m`; V3 `test_toctou_mutate_after_issuance`; grant tests revise+hash |
| Clock / `created_at` | **Yes** | V3 clock cases; some **positives** use `bind_with_test_authority` (known test key), not production `O.run`. Production clock independence is still covered by V4 fail-closed `O.run` + design (I12). |
| N-hop / write-back / derived-fact | **Yes** | V4 `test_o`, `test_p`, `test_n` |
| Fixture leakage into production | **None** | `architecture/` does not import `tests.*` |

**Not fixture-only confirmation** for the central property: negatives hit production `CognitiveOrchestrator`. Positives that must mint under a known key cannot use production urandom `K_O` without a mint adapter; the subclass is the honest test composition root.

POST-P5-HARDENING (already classified; not a new blocker): dedicated public-assembler ≠ `O.run` test.

---

## 8. Regression analysis

| Vector | Likelihood | Guarded by tests/docs? |
| --- | --- | --- |
| Restore ContextVar in `verify_observation_grant` | **HIGH** | Yes — V4 ContextVar tests + R3 docs |
| Trust caller `grant_ok` inside `O.run` | **HIGH** | Partial — `O.run` has no `bindings=`; R1 docs; extra assembler test is hardening |
| Production mint adapter taking caller `secret=` | **HIGH** if ingestion is added carelessly | R5 docs; no adapter yet |
| Authority through memory / SQLite | **MEDIUM** | I6–I8 tests |
| Cross-orchestrator trust | **MEDIUM** | `test_k` |
| `created_at` as verify clock | **MEDIUM** | V3 clock tests + I12 |
| Implicit authority-bearing serializer | **MEDIUM** | Grant in payload is verified, not trusted as JSON |
| Test helper imported as production | **MEDIUM** | `observation_test_runtime` docstring + no architecture import |
| `evaluate_reason` of caller DTOs from `run` | **HIGH** if wired later | Currently only `_reason_episode` |

Existing documentation/tests **sufficient to guard current behavior**. High-likelihood vectors are the same R1/R3 residuals, not new holes.

---

## 9. Compatibility analysis

Vs **`main`** (not vs intermediate V3):

| Change | Kind |
| --- | --- |
| `CognitiveOrchestrator` mints instance `K_O`; no new required kwargs | Additive; existing `memory=` / `hypotheses=` / `ledger_path=` callers still construct |
| `reason()` now fail-closed for grants | **INTENTIONAL SECURITY BREAK** vs pre-grant `OBSERVED_FACT` → `FACTUAL_PREMISE` |
| Default `ingest_generic_observation(kind=)` `OBSERVED_FACT` → `INFERENCE`; `OBSERVED_FACT` raises | **INTENTIONAL SECURITY BREAK** |
| `record_world_model_object` refuses `OBSERVED_FACT` | **INTENTIONAL SECURITY BREAK** |
| Lesson/hypothesis write-back gated by `reusable_writeback_permitted` | **INTENTIONAL SECURITY BREAK** (anti-escalation) |
| `store.revise` / supersede drops `observation_grant` on statement change | **INTENTIONAL SECURITY BREAK** |
| Critique / `CognitiveResult` new fields with defaults | Compatible additive |
| V3 `secret=` constructor | Never existed on `main`; V4 does not reintroduce it |

Do **not** weaken these for compatibility.

Plugins/adapters: loop adapters are synthetic and now cannot label facts. No production plugin receives `O` in this diff.

Future ingestion must be a new, explicit composition-root mint — not caller `secret=`.

---

## 10. Architecture quality

V4-PIN is integrated as a **production authority root** on the existing P3/P5 loop, not a parallel brain.

| Criterion | Verdict |
| --- | --- |
| Separation of concerns | Bind vs evaluate vs persist vs mint is explicit |
| Authority ownership | Production `O` owns `K_O`; tests subclass after `super()` |
| Dependency direction | `architecture/` does not import tests; loop imports observation verify |
| Composition-root discipline | Mint stays out of `O.run`; adapters refuse fact mint |
| Naming / discoverability | Residuals remain importable; documented |
| Maintainability | Large historical report set without a current-law index **hurts discoverability** (conditional finding) |
| Future ingestion / automation | R5 correctly deferred; danger is a casual mint API |

Cosmetic claims (`__all__`, underscores) are not treated as the boundary.

---

## 11. Evidence integrity

| Artifact | Present | Overclaim? |
| --- | --- | --- |
| V4 implementation report | Yes | No AGI/ACI/production/live-trading claim |
| Independent forensic audit | Yes | `FORENSIC_STATUS = PASS` refers to V4-PIN code, not PR merge |
| Residual-boundary review | Yes | `CLOSED_WITH_DOCUMENTED_RESIDUALS`; MERGE NO |
| Closure gate | Yes | `SECURITY-EXIT-CANDIDATE`; MERGE NO |
| This audit’s pytest | **2065 passed, 3 skipped** on HEAD | Does not claim AGI |
| `TEST_EVIDENCE.md` / `EVOLUTION_INDEX.md` | Yes | **Under-claim / stale** relative to V4-PIN — integrity issue for reviewers, not an overclaim of autonomy |
| `EVOLUTION_RECORD_0008` “187 targeted tests” vs later 28 in TEST_EVIDENCE | Historical snapshot drift between early P5 commits | Dated records; do not treat as HEAD |

No report in the P5 V4/closure set claims AGI, ACI, production readiness, live trading, or unsupported autonomy.

---

## 12. Lane A / soak status

| Check | Result |
| --- | --- |
| `python3 -B scripts/freeze_lane_a.py` | **Lane-A integrity OK (36 files pinned)** |
| `git diff origin/main...HEAD -- discovery paper_trading` | **empty** |
| Soak scripts/reports/tests vs `main` | **empty** |
| Historical soak JSON rewritten? | **No** |
| Lane A evidence rewritten to flatter P5? | **No** |

`scripts/doc_drift.py` only explains a **gitignored** cognitive sqlite path. Not a soak DB.

---

## 13. Windows / local-first assessment

Classified **separately from P5 security**.

| Risk | Found in PR #93 production code? |
| --- | --- |
| Linux-only paths | **No** in `architecture/cognitive` (pathlib) |
| Hardcoded `/workspace`, `/tmp/ahos`, `G:\robat` | **No** in production cognitive code |
| Cloud-only / VPS mandatory services | **No** |
| Hidden credentials | **No** |
| Non-free runtime | **No** (`os.urandom`, SQLite, stdlib HMAC) |

`TEST_EVIDENCE.md` records a **Cloud Linux** pytest interpreter (`/tmp/ahos-test-venv`). That is evidence-environment documentation, not a runtime dependency of the product.

No Windows-first blocker in this PR’s code.

---

## 14. Financial / execution safety

| Capability | Introduced? |
| --- | --- |
| Live trading | **No** |
| Wallet signing / Trust Wallet / broker / exchange execution | **No** in cognitive diff |
| Autonomous fund movement | **No** |
| `authorize_execution` | Still raises `MemoryAuthorizationError` |
| `CognitiveResult.authorized_execution` | Default **False**; not set True on `run` |

PAPER_ONLY remains intact. **Not a release blocker.**

---

## 15. Current evidence / test status

**Strongest evidence on this tree (this audit, not copied):**

```text
/tmp/ahos-test-venv/bin/python -m pytest -q --tb=no -p no:cacheprovider
# 2065 passed, 3 skipped in 224.57s
# HEAD 311716f; architecture/tests identical to afdff25
```

| Item | Status |
| --- | --- |
| 2065 / 3 skipped still applicable? | **Yes — re-executed on HEAD** |
| P5 tests present? | **Yes** (222 `test_*` across `test_p5_*.py` + typed reasoning + evidence support) |
| Lane A | **36/36 freeze** |
| Soak | **untouched** |
| Import validation | Not re-run here (would dirty `reports/*.json`). Prior PASS on identical Python remains applicable; not used as a substitute for pytest. |

Prior “195 passed / 28 P5 tests” in `TEST_EVIDENCE.md` is **stale documentation**, not the current suite.

---

## 16. Findings

### Security / release

| ID | Severity | Finding |
| --- | --- | --- |
| S0 | — | **No new production-valid ObservationGrant bypass.** P5 security-exit stands. |
| R1–R6 | LOW (pre-existing) | Unchanged documented residuals. Not re-filed as new defects. |

### PR integrity (non-security)

| ID | Severity | Finding |
| --- | --- | --- |
| I-SCOPE | Medium (process) | Title/body emphasize V4-PIN; vs `main` the PR is the full P5 stack. Formal review under the current title would under-scope the diff. |
| I-INDEX | Medium (process) | Living `TEST_EVIDENCE.md` / `EVOLUTION_INDEX.md` / early CAPABILITY_MATRIX P5 row do not point at V4-PIN or 2065. Historical P5 reports must not be rewritten; indexes should. |
| I-HIST | Low | Many superseded design docs in one folder. Harmless if a current-law pointer exists; harmful without one. |
| I-JSON | Low | Generated `p5_typed_evidence_reasoning_latest.json` is dated synthetic evidence. Keep; do not treat as soak. |
| I-HARDEN | Low | POST-P5-HARDENING assembler/ContextVar tests still absent (already classified). |

No **PR-INTEGRITY-FAIL** trigger (no material security contradiction, no Lane A/soak contamination, no live execution, no unexplained test failure).

---

## 17. Remediation recommendations (do not implement in this audit)

1. **Before formal review:** retitle and rewrite the PR summary to name the **full P5 Lane-B stack** (typed evidence, polarity, memory authorization, ObservationGrant V4-PIN) and state that V4-PIN is the authority capstone, not the only diff vs `main`. Keep **DRAFT** until a human Ready gate.
2. **Before formal review:** add a **current-law pointer** to `EVOLUTION_INDEX.md` and a dated P5 V4 section in `TEST_EVIDENCE.md` (2065/3, V4 SHA, closure-gate path). Do **not** rewrite historical reports.
3. Optional POST-P5-HARDENING tests for R1/R3 (already deferred).
4. Optional: move or clearly banner V3 design docs as superseded so reviewers do not implement V3 DI.
5. Do **not** split P5 product files into a second PR.
6. Do **not** merge; do **not** mark Ready as part of this audit.

---

## 18. Final classification

The PR **deserves to proceed to a documentation/packaging pass**, then a separate human Ready-for-Review gate. It does **not** deserve to be called Ready now. It is **not** a fail.

P5 remains a security-exit candidate with documented residuals. This audit did not manufacture a new bypass and did not manufacture merge readiness.

```text
PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL
P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE
MERGE = NO
READY_FOR_REVIEW = NO
PRODUCTION_READY = NO
LIVE_TRADING = NO
```
