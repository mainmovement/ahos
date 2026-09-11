# P5 V3 implementation report

**Kind:** Controlled implementation of the approved V3 refinement.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**IMPLEMENTATION_SHA:** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**Architecture:** `P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md`, `P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md`, `P5_V3_FINAL_REFINEMENT_ARCHITECTURE.md`

Not AGI. Not ACI. Not production-ready. Not live trading. Not autonomous truth acquisition.  
Lane A and soak were not modified. This PR remains draft. `MERGE = NO`. `READY_FOR_REVIEW = NO`.

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.

---

## 1. Implementation SHA

Code complete at:

`24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`

Commits on this implementation:

| SHA | Subject |
| --- | --- |
| `f38d142` | Implement P5 V3 ObservationGrant issuance closure and trusted episode clock |
| `79f07fe` | Fix V3 test scope naming and live-grant assertions |
| `24b2ab8` | Record experiment_analysis_only as NOT_MEASURED without a grant |

---

## 2. Files changed

Relative to the V3 design-only tip `e05f31f`:

**Production**

- `architecture/cognitive/memory/observation.py`
- `architecture/cognitive/loop/binding.py`
- `architecture/cognitive/loop/reason.py`
- `architecture/cognitive/loop/orchestrator.py`
- `architecture/cognitive/loop/adapters.py`
- `architecture/cognitive/loop/benchmark.py`
- `architecture/cognitive/benchmark/corpus.py`
- `architecture/cognitive/benchmark/evaluator.py`
- `architecture/cognitive/benchmark/p5_eval.py`

**Tests-only**

- `tests/observation_test_runtime.py` (new)
- `tests/p5_grant_fixtures.py`
- `tests/test_p5_v3_authority_boundary.py` (new)
- `tests/test_p5_observation_grant.py`
- `tests/test_p5_episode_polarity.py`
- `tests/test_p5_negation_entity.py`
- `tests/test_p5_second_forensic.py`
- `tests/test_p5_memory_authorization_boundary.py`
- `tests/test_typed_reasoning.py`
- `tests/test_cognitive_loop.py`
- `tests/test_cognitive_benchmark.py`

No `discovery/**`, `paper_trading/**`, soak databases, or soak scripts.

---

## 3. Architecture mapping

Approved V3 path vs this tree:

```text
UNTRUSTED INPUT                         # remember, sqlite, generic ingest, world-model
      × persist_observed_acquisition    # ABSENT (PROVEN)
      × IngestPort.persist_acquired mint# RuntimeError (PROVEN)
      × CognitiveOrchestrator ingest=/verifier=/secret=
      │
DESIGNATED ACQUISITION ADAPTER          # production: none wired (mint count = 0)
      │                                 # tests: TestAcquisitionAdapter
TRUSTED ACQUISITION RESULT              # TypedFakeAcquisitionResult → AcquisitionRecord
      ↓
BOUND INGEST PORT                       # not a public package export; not an orch kwarg
      ↓
OBSERVATION AUTHORITY                   # production: os.urandom, issuer ahos.observation_authority
                                        # tests: vector key, issuer …test-vector-v1
      ↓
OBSERVATION GRANT                       # HMAC-SHA256 over canonical observation bytes
      ↓
OBSERVED_FACT row                       # storage; not authority
      ↓
BIND-TIME VERIFICATION                  # latest row + MAC + kind + temporal vs trusted_now
      ↓
FACTUAL_PREMISE
```

Hybrid-D consumption is preserved: latest canonical row, MAC match, `OBSERVED_FACT` only, revision/supersession strip the grant, SQLite without MAC is data.

---

## 4. Authority graph

```text
ordinary caller
    × CognitiveOrchestrator(..., ingest=, verifier=, secret=)
    × persist_observed_acquisition(...)
    × IngestPort().persist_acquired(...)  → RuntimeError
    × _process_authority()                → ABSENT
    remember / sqlite / generic / world-model → OBSERVED_FACT label only

CognitiveOrchestrator
    owns _grant_verify_secret = os.urandom(32)   # verify material, not a mint API
    run() pushes GrantVerifyContext(prod_key, ISSUER_ID, episode_ts)
    does not hold BoundIngestPort
    does not expose _mint

BoundIngestPort(ObservationAuthority)
    persist_acquired → authority._mint(AcquisitionRecord)
    not in architecture.cognitive / memory / loop __all__
    production tree has no caller (corpus/eval/benchmark use remember())

tests/observation_test_runtime.py
    TEST_VECTOR_KEY = bytes.fromhex("a1"*32)
    issuer ISSUER_ID_TEST
    TestAcquisitionAdapter → BoundIngestPort(test authority)
    grant_verify_scope() sets tests-only verify context
    production modules do not import this file (PROVEN)
```

---

## 5. Clock graph

```text
CognitiveOrchestrator.run(now=...)
        → episode ts = now or time.time()
        → GrantVerifyContext.trusted_now = ts
        → reason(..., now=ts) → bind_context(..., now=ts)
        → write-back bind_context(..., now=ts)

bind_item / _trusted_now(task, now)
        → uses explicit now, else contextvar trusted_now
        → NEVER CognitiveTask.created_at   (del task; PROVEN)

task.created_at
        → stored on EvidenceBinding.task_created_at as metadata only
        → does not enter valid_until / observed_at / MAC now
```

`run(now=)` remains the approved test freeze. That is episode-clock control, not `created_at` control.

---

## 6. Test authority graph

```text
TypedFakeAcquisitionResult
        ↓
TestAcquisitionAdapter                 # tests/observation_test_runtime.py
        ↓
BoundIngestPort(ObservationAuthority(TEST_VECTOR_KEY, ISSUER_ID_TEST))
        ↓
Test ObservationGrant
        ↓
grant_verify_scope() / orch.run() parent-context preserve
        ↓
verify_observation_grant(key=TEST_VECTOR_KEY, expected_issuer_id=ISSUER_ID_TEST)
```

Production issuer **rejects** the published test-vector key (`ValueError`).  
Production denylist stores SHA-256 of the vector, not the raw key.  
`tests/p5_grant_fixtures.persist_authorized` calls the tests-only adapter, not a production persist RPC.

---

## 7. Adversarial tests

Independent Layer-4 module: `tests/test_p5_v3_authority_boundary.py` (does not import `p5_grant_fixtures`).

Retained Hybrid-D matrix: `tests/test_p5_observation_grant.py` plus polarity / negation / second-forensic / memory-authorization files.

| # | Attack | Result |
| --- | --- | --- |
| 1 | arbitrary statement minting | `persist_observed_acquisition` absent; `IngestPort` cannot mint |
| 2–5 | arbitrary source / observed_at / entity / scope | replay/copy of grant fields fails MAC / live support |
| 6 | direct invocation of closed APIs | AttributeError / RuntimeError |
| 7 | direct import of persist RPC | AttributeError |
| 8 | direct `ObservationGrant` construction | not FACTUAL |
| 9 | alternate factory (`issue`/`mint`/`sign`) | absent |
| 10–11 | orchestrator DI / matching pair | TypeError; signature has no authority kwargs |
| 12 | alien BoundIngestPort | production `run()` does not accept those grants |
| 13 | copied grant onto other statement | target id not FACTUAL |
| 14 | serialization reconstruction | copy without matching fields not FACTUAL |
| 15 | module-global issuer/secret | no `_process_authority`, no live global authority |
| 16 | `AHOS_OBSERVATION_GRANT_SECRET` | unused; orch secret ≠ env bytes |
| 17 | revision authority reuse | grant stripped; latest row fails MAC |
| 18 | direct SQLite INSERT | data, not FACTUAL_PREMISE |
| 19 | generic ingest | cannot persist OBSERVED_FACT; not FACTUAL |
| 20 | world-model insertion | cannot persist OBSERVED_FACT; not FACTUAL |
| 21 | DERIVED_FACT grant reuse | kind check + role forbid FACTUAL_PREMISE |
| 22 | N-hop ungranted OF write-back | reusable_writeback False; no hyp/lesson |

Clock cases A–E in the same V3 file: old `created_at` does not starve current trusted now; future `created_at` cannot extend expiry; `run(now=)` freeze; expired grant; future observation.

---

## 8. Positive acquisition path

Until a designated production provider adapter is wired, **production mint count = 0**.

Positive FACTUAL_PREMISE tests use `tests/observation_test_runtime.py` only:

1. `timeout_retry_reading(...)` builds a typed fake acquisition result.
2. `TestAcquisitionAdapter` fills `AcquisitionRecord` from that result.
3. Tests-only `BoundIngestPort` mints under `ISSUER_ID_TEST`.
4. `grant_verify_scope` / parent-preserving `CognitiveOrchestrator.run` verifies with the test key.
5. Bind against trusted episode `now` yields `FACTUAL_PREMISE` when latest state, MAC, kind, and time hold.

Corpus, evaluator, p5_eval, and `run_memory_vs_no_memory` seed `OBSERVED_FACT` via `remember()` **without** a grant.

---

## 9. Regression results

| Gate | Result |
| --- | --- |
| Focused P5 (+ loop/typed) | 291 passed |
| Full `pytest tests` | **2042 passed, 3 skipped, 0 failed** |
| `scripts/validate_imports.py` | **PASSED** (232 modules; Lane-A 36 pinned). Re-run after deleting `.pytest_cache/` from the pytest working tree. |
| P5 adversarial matrix | Hybrid-D file + V3 Layer-4 file green |

`experiment_analysis_only` is `NOT_MEASURED` when the ungranted hyp-probe cannot write an experiment. That is fail-closed, not a mint restoration.

---

## 10. Lane A result

`scripts/freeze_lane_a.py` → **Lane-A integrity OK (36 files pinned)**.

`git diff origin/main...HEAD` contains no `discovery/**` or `paper_trading/**`.

`LANE_A_STATUS = UNTOUCHED`

---

## 11. Soak result

No soak databases, soak scripts, or `reports/PRE_SOAK_STATUS.txt` in the implementation commits.

`SOAK_STATUS = UNTOUCHED`

---

## 12. Forensic audit result

Read-only inspection of SHA `24b2ab8` (this report does not modify production code).

| Search | Finding |
| --- | --- |
| Public mint (`persist_observed_acquisition`, `issue`) | **ABSENT** |
| Hidden getter `_process_authority` | **ABSENT** |
| `IngestPort.persist_acquired` | **raises; cannot mint** |
| Public orchestrator DI | **params = memory, hypotheses, ledger_path, retriever only** |
| Matching issuer/verifier kwargs | **TypeError** |
| Caller-controlled `task.created_at` as grant now | **not used** (`_trusted_now` deletes `task`) |
| Production secret in tests fixtures | **no**; tests use `TEST_VECTOR_KEY` under `tests/` |
| Production imports of `tests/` | **none** |
| Seeders calling production `_mint` | **none**; `remember()` only |
| Signer logged / env-loaded | **no**; `os.urandom`; env key unused |
| Direct SQLite → FACTUAL | **rejected** |
| Revision / TOCTOU / copied grant | **rejected** |
| DERIVED_FACT using OF grant | **rejected** |
| N-hop write-back from ungranted OF | **blocked** |

**FORENSIC_AUDIT = PASS** against the ordinary-API threat model in the approved V3 reports.

---

## 13. Remaining limitations

Python cannot sandbox in-process imports. The following remain possible for a caller who already executes inside the process and imports internals:

- Construct `BoundIngestPort(ObservationAuthority(secret=k))` and mint.
- Read `CognitiveOrchestrator._grant_verify_secret`.
- Call `push_grant_verify_context` with an attacker key (verify seam, not a public orchestrator kwarg).
- Direct SQLite writes of rows (storage, not `FACTUAL_PREMISE` without a verifying MAC).

Those are **ACE / language-level** residual risks, documented in V3. They are **not** ordinary application APIs.

`run(now=)` still lets the episode caller freeze trusted time. That is the approved test/runtime clock, not `CognitiveTask.created_at`.

No production designated acquisition adapter is wired. The system does not autonomously acquire external truth.

---

## 14. Explicit non-claims

This work does **not** claim:

- AGI or ACI
- production-ready operation
- live trading or execution authority
- autonomous truth acquisition
- unrestricted epistemic authority
- a sandbox against in-process Python `gc` / attribute reads
- that `BoundIngestPort` is unimportable

---

## 15. Final status

```text
IMPLEMENTATION_STATUS = PASS
GRANT_ISSUANCE_AUTHORITY = CLOSED
CALLER_CONTROLLED_TIME = CLOSED
TEST_AUTHORITY_SEPARATION = PASS
ORCHESTRATOR_AUTHORITY_INJECTION = BLOCKED
PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED
TEST_KEY_SEPARATION = PASS
ARBITRARY_GRANT_MINTING = BLOCKED
DIRECT_SQLITE_ESCALATION = BLOCKED
REVISION_AUTHORITY_REUSE = BLOCKED
LATEST_STATE_MAC = PASS
DERIVED_FACT_SEPARATION = PASS
TOCTOU = PASS
N_HOP_ESCALATION = BLOCKED
CLOCK_AUTHORITY = TRUSTED_RUNTIME
LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED
FORENSIC_AUDIT = PASS
MERGE = NO
READY_FOR_REVIEW = NO
REPORT = reports/agi_aci_evolution/P5_V3_IMPLEMENTATION_REPORT.md
```

STOP.
