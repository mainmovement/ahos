# P5 V4-PIN implementation report

**Kind:** Controlled implementation of the approved V4-PIN authority-construction boundary.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**BASELINE_SHA:** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**CODE_SHA:** `afdff2539943441244d05478a7004bc4bcc5976f`  
**IMPLEMENTATION_SHA:** `afdff2539943441244d05478a7004bc4bcc5976f`  
**REPORT_COMMIT:** `404830bc6dfab38e7f9b96c18b4f70d5dcf0c95d`  
**Architecture:** `P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md` (approved). Prior gate: `P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md`.

Not AGI. Not ACI. Not production-ready. Not live trading. Not autonomous truth acquisition.  
Lane A and soak were not modified. This PR remains draft. `MERGE = NO`. `READY_FOR_REVIEW = NO`.

Proof language: **PROVEN** (this tree) / **RESIDUAL** (documented, in or out of threat model).

---

## 1. Baseline SHA

Vulnerable production baseline (C1 open):

`24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`

On that tree, `CognitiveOrchestrator.run()` copied parent ContextVar `key`/`issuer_id` (or published `K_O` into `GrantVerifyContext`) before `retriever.retrieve`. An ordinary caller could mint with `BoundIngestPort(ObservationAuthority(secret=k))` and `push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, now))` so production treated attacker HMAC as `FACTUAL_PREMISE`.

---

## 2. Implementation SHA

Code complete (production + tests, before this report) at:

`afdff2539943441244d05478a7004bc4bcc5976f`

| SHA | Subject |
| --- | --- |
| `bc49093` | Implement V4-PIN instance-owned observation grant verification |
| `6377528` | Fix V4-PIN adversarial fixtures and isolate leftover ContextVar state |
| `afdff25` | Point the episode-policy order test at evaluate_reason |

This report’s commit SHA is stamped below after the report lands.

---

## 3. Exact files changed

Relative to design-only tip `2446099` (code delta for this implementation):

**Production**

- `architecture/cognitive/loop/orchestrator.py`
- `architecture/cognitive/memory/observation.py`
- `architecture/cognitive/loop/binding.py`
- `architecture/cognitive/loop/reason.py`

**Tests**

- `tests/observation_test_runtime.py`
- `tests/test_p5_v4_authority_boundary.py` (new)
- `tests/test_p5_v3_authority_boundary.py`
- `tests/test_p5_observation_grant.py`
- `tests/test_p5_second_forensic.py`
- `tests/test_p5_episode_polarity.py`
- `tests/test_p5_negation_entity.py`
- `tests/test_typed_reasoning.py`
- `tests/test_cognitive_loop.py`

**This report**

- `reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md`

**Not changed:** `discovery/**`, `paper_trading/**`, soak infrastructure, schemas, UI, unrelated workflows.

Relative to baseline `24b2ab8`, the same production/test files plus prior V4/V3 *report-only* documents already on the PR (`P5_V3_IMPLEMENTATION_REPORT.md`, `P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`, `P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md`, `P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md`).

---

## 4. Authority graph before (`24b2ab8`)

```text
O.run(task, now=?)
  ├─ ContextVar ← parent.key OR K_O          # Layer 3 leak + Layer 2 switch
  ├─ retriever.retrieve(memory, task, now)   # DI window; sees ContextVar
  ├─ assemble_context(retrieved, memory)
  ├─ reason() [module]
  │    └─ bind_item → observation_grant_permits_factual(ctx.key)
  ├─ bind_context again → reusable_writeback_permitted
  └─ hypotheses.propose / memory.remember
```

Production verifier = whatever key/issuer sat in the ContextVar at bind time.

---

## 5. Authority graph after (this tree)

```text
O = CognitiveOrchestrator(memory, hypotheses, ledger_path, retriever?)
  K_O = os.urandom(32)          # denylist retry; not a ctor argument
  issuer = ISSUER_ID            # fixed; not a ctor argument

O.run(task, now=?)
  ts = now or time.time()       # trusted episode clock
  retriever.retrieve(memory, task, now=ts)   # ordinary data; no K_O
  assemble_context(...)
  O._reason_episode
       └─ O._bind_context
            └─ O._bind_item
                 ├─ load_bind_snapshot(store.get latest row)
                 ├─ O._permits_observation_grant(...)   # key is not an argument
                 │     key    = self._grant_verify_secret
                 │     issuer = self._verify_issuer_id == ISSUER_ID
                 │     now    = ts
                 └─ assemble_evidence_binding(grant_ok=bool)
       └─ evaluate_reason(task, ctx, bindings)   # no verifier callback
  O._bind_context again → reusable_writeback_permitted
  remember HYP/LESSON/INFERENCE/episode without ObservationGrant
```

Public `reason()` / `bind_item()` / `bind_context()` always `grant_ok=False`. They do not accept `key=` / `secret=` / `verifier=`.

Tests-only `TestCognitiveOrchestrator` (in `tests/`) may pin a distinct test secret and `ISSUER_ID_TEST` after `super().__init__`. Production code does not import it.

---

## 6. Secret data-flow before (`24b2ab8`)

```text
O._grant_verify_secret
  → GrantVerifyContext(key=K_O or parent.key, issuer, ts)
  → ContextVar  (push_grant_verify_context)
  → retriever / bind_item / live_grant_ok / verify_observation_grant
```

`K_O` was both published and replaceable on the production path.

---

## 7. Secret data-flow after (this tree)

```text
O.__init__
  → self._grant_verify_secret = os.urandom(32)   # private instance state
  → self._verify_issuer_id = ISSUER_ID

Read only by:
  O._permits_observation_grant → observation_grant_permits_factual(key=self._grant_verify_secret)

Does not enter:
  ContextVar, GrantVerifyContext, retriever args, memory args,
  EvidenceBinding fields as a key, CognitiveTask, RetrievedItem,
  CognitiveResult, logs, exceptions, public properties, persist.
```

`verify_observation_grant(..., key=None)` is fail-closed. It does not fall back to ContextVar.

---

## 8. ContextVar changes

| Surface | After |
| --- | --- |
| `GrantVerifyContext` | Still exists (key, issuer_id, trusted_now) |
| `push_grant_verify_context` | Still sets the ContextVar. **No production verify effect.** |
| `current_grant_verify_context` | Still returns the ContextVar. Production `run()` does not write `K_O` into it. |
| `clear_grant_verify_context` | Drops metadata. Not an authority setter. |
| Public `bind_item` | May read `trusted_now` from ContextVar for `authority_now` display. **`grant_ok` is always False.** |
| Production `O.run` | Does not call `current_grant_verify_context` / `push_grant_verify_context`. |

A caller may still push an attacker key. Production `_permits_observation_grant` ignores it. **PROVEN** by V4 tests C/D/E/F/G and the independent forensic script.

---

## 9. `push_grant_verify_context` disposition

**Not removed.** Neutralized for production authority:

- The function remains importable (ordinary Python).
- It still mutates a ContextVar.
- Production verification does not read that ContextVar.
- Closing it with `__all__`, renaming, or documentation-only would not have been sufficient; the verify path had to stop using it. That stop is in `verify_observation_grant` (explicit `key` only) and in `O.run` (no copy/push).

---

## 10. `_permits_observation_grant` implementation

`CognitiveOrchestrator._permits_observation_grant` is the instance-owned verification boundary. It has no `key=` / `secret=` / `verifier=` parameter. It calls `observation_grant_permits_factual(..., key=self._grant_verify_secret, expected_issuer_id=self._verify_issuer_id)`.

Checks retained from Hybrid-D / V3 (fail-closed):

1. grant exists in latest-row payload  
2. version / purpose / kind  
3. issuer equals production `ISSUER_ID` (instance copy)  
4. HMAC-SHA256 against `self._grant_verify_secret`  
5. latest-row fields (statement, source, observed_at, domain) form the canonical tuple  
6. statement hash match  
7. UNKNOWN provenance rejected  
8. entity/scope/applicability remain in binding (`_applicability` / support class); they still gate `may(FACTUAL_PREMISE)` and positive support  
9. temporal: `observed_at <= now`, `valid_until` not expired, STALE/SUPERSEDED/ARCHIVED rejected  
10. `now` is the episode timestamp from `run(now=)` / `time.time()`, not `CognitiveTask.created_at`  
11. `load_bind_snapshot` uses `store.get` (latest revision); revise strips the grant payload  

---

## 11. Acquisition boundary

- No public `persist_observed_acquisition`.
- `IngestPort.persist_acquired` raises `RuntimeError` (cannot mint).
- `ingest_generic_observation` refuses `OBSERVED_FACT`.
- `CognitiveOrchestrator` has no `ingest=` / `ingest()`.
- `BoundIngestPort` remains constructible with a caller `ObservationAuthority`. That mints HMAC under the **caller** key. Production `O` does not accept it. **PROVEN**.
- Tests mint via `TestAcquisitionAdapter` / `persist_test_observation` using `TEST_VECTOR_KEY` + `ISSUER_ID_TEST`.
- Production mint under `K_O` remains **zero**. There is no production acquisition adapter bound to `K_O` in this task. That is issuance closure, not a bypass.

---

## 12. Retriever threat analysis

`retriever=` is ordinary DI. A malicious retriever can return attacker rows and call `current_grant_verify_context` / `push_grant_verify_context`.

It cannot:

- obtain `K_O` from production `run()` (production does not publish it);
- replace `K_O`;
- select production issuer/verifier;
- cause its own HMAC to become production `FACTUAL_PREMISE`.

**PROVEN:** `test_f_malicious_retriever_cannot_obtain_or_replace_production_authority` (seen ContextVar key is `None` at retrieve; attacker grant not factual). Independent forensic: same.

---

## 13. Memory threat analysis

Memory may hold attacker `OBSERVED_FACT` rows, copied grant blobs, or SQLite inserts. `store.get` during bind can also push ContextVar.

Production bind still verifies the latest row against `K_O`. Attacker rows fail HMAC or issuer/kind checks. **PROVEN:** V4 G/L/M/N and forensic `malicious_memory` / `direct_sqlite`.

---

## 14. Multi-orchestrator isolation

Each `CognitiveOrchestrator.__init__` draws a fresh `os.urandom(32)` (denylist retry). Tests do **not** read production `K_O`. Isolation is proven with tests-only keys:

```text
TestCognitiveOrchestrator(verify_secret=KEY_A)  accepts KEY_A grant
TestCognitiveOrchestrator(verify_secret=KEY_B)  rejects KEY_A grant
and the reverse
```

**PROVEN:** `test_k_o1_grant_not_valid_for_o2`. Nested: test-vector grant is factual on `TestCognitiveOrchestrator` and not on production `CognitiveOrchestrator` (`test_nested_orchestrators_do_not_share_parent_context`).

Two production instances both reject the same attacker grant (forensic `cross_instance_attacker_grant`). Uniqueness of production `K_O` is by construction (`os.urandom`); tests do not compare production secret bytes.

---

## 15. Test architecture

| Rule | Status |
| --- | --- |
| No `grant_verify_scope` as production rekey | **PROVEN** — V4 E asserts production `run` ignores it |
| Positive FACTUAL paths | `TestCognitiveOrchestrator` / `bind_with_test_authority` / `reason_with_test_authority` |
| Distinct test secret | `TEST_VECTOR_KEY`; production denylist SHA-256 retained |
| Distinct test issuer | `ISSUER_ID_TEST` |
| Layer 4 | still must not import `tests.p5_grant_fixtures`; C1 replay uses `BoundIngestPort` + `push_grant_verify_context` + production `run` → not FACTUAL |
| Production modules | do not import `tests.observation_test_runtime` / `TEST_VECTOR_KEY` |

`grant_verify_scope` remains as a ContextVar setter used to prove production **ignores** it.

---

## 16. Adversarial test results

`tests/test_p5_v4_authority_boundary.py` plus Layer 4 C1 replay.

| ID | Attack | Result |
| --- | --- | --- |
| A | Caller `ObservationAuthority(attacker_key)` | **BLOCKED** |
| B | Caller `BoundIngestPort` | **BLOCKED** |
| C | ContextVar key | **BLOCKED** (ignored) |
| D | ContextVar issuer | **BLOCKED** (ignored) |
| E | `grant_verify_scope` / public verify-context injection | **BLOCKED** |
| F | Malicious retriever | data possible; production authority **impossible** |
| G | Malicious memory | **BLOCKED** |
| H | Fake acquisition dataclass / no `ingest()` | **BLOCKED** |
| I | Attacker issuer | **BLOCKED** |
| J | Attacker key (valid own HMAC ≠ production) | **BLOCKED** |
| K | O1 grant → O2 | **BLOCKED** (tests-only keys) |
| L | SQLite row without production grant | **BLOCKED** |
| M | Revision inheritance | **BLOCKED** (grant stripped) |
| N | `DERIVED_FACT` + copied grant | **BLOCKED** |
| O | N-hop ungranted episode | **BLOCKED** |
| P | Writeback without production FACTUAL | **BLOCKED** (`reusable_writeback=False`) |

Existing suites also run: `test_p5_v3_authority_boundary.py`, `test_p5_observation_grant.py`, `test_p5_memory_authorization_boundary.py`, `test_p5_second_forensic.py`, polarity/negation/typed/loop.

---

## 17. Full pytest result

```text
2065 passed, 3 skipped in 226.04s
```

Interpreter: `/tmp/ahos-test-venv/bin/python -m pytest`.

Targeted V4 + P5 authority files were green before the full run. One order-source test was retargeted from public `reason()` to `evaluate_reason` after the V4 split (`afdff25`).

---

## 18. Lane A result

```text
python scripts/freeze_lane_a.py
Lane-A integrity OK (36 files pinned)
```

`git diff 24b2ab8..HEAD -- discovery/** paper_trading/**` is empty.

---

## 19. Soak status

Soak infrastructure was not modified. `git diff 24b2ab8..HEAD` has no soak paths. `reports/PRE_SOAK_STATUS.txt` is untracked local noise and was **not** committed.

---

## 20. Independent forensic audit

A separate ordinary-caller script (`/tmp/v4_forensic_audit.py`, not added to the repo) replayed the threat-model attacks against a live production `CognitiveOrchestrator`. It did not assert by reading `O._grant_verify_secret`.

| Attack | Outcome |
| --- | --- |
| Caller key / `ObservationAuthority` | **BLOCKED** (`factual=False`, `writeback=False`) |
| Caller `BoundIngestPort` | **BLOCKED** |
| ContextVar key + issuer | **BLOCKED** (attacker ContextVar still present; production ignored it) |
| Public `verify_observation_grant` / `bind_context` / `reason` | own HMAC **True**; `key=None` **False**; public FACTUAL **False** |
| Ctor/run `secret=` `verifier=` `ingest=` `authority=` `issuer=` `grant_verify_context=` | **TypeError**; signatures have no those params |
| Fake acquisition / `persist_observed_acquisition` / `O.ingest` | **absent** |
| Malicious retriever | **BLOCKED**; ContextVar key at retrieve **None** |
| Malicious memory `get` | **BLOCKED**; first `get` ContextVar **None** |
| Issuer substitution | **BLOCKED** |
| Second production instance + same attacker grant | both **BLOCKED** |
| Direct SQLite well-formed ungranted row | **BLOCKED** |
| Revision of a test-minted row | grant stripped; not FACTUAL |
| Nested test orch vs production | test grant FACTUAL on tests-only orch; **not** on production |
| `repr`/`str` | does not contain `_grant_verify_secret` |
| Production source import of tests runtime / `TEST_VECTOR_KEY` | **absent** |

`attacks=15 open=0`.

This is **not** a claim that frame-walking, `gc.get_referrers`, or assignment to `O._grant_verify_secret` on a held instance are blocked. Those remain out of the declared threat model (same-process pinning / composition-root ACE).

---

## 21. Residual risks

| Residual | In threat model? | Notes |
| --- | --- | --- |
| Holder of `O` can read `O._grant_verify_secret` | **No** (composition root already holds `O`) | Documented in the V4 design |
| `sys._getframe` / `gc` / `ctypes` | **No** | Design: if brought in scope, Option E is required |
| Public `assemble_evidence_binding(grant_ok=True)` + `evaluate_reason` | Synthesizes a binding **outside** `O.run` | Does not make production `O` accept attacker evidence |
| `BoundIngestPort` still mints caller HMAC | Yes as mint, no as production authority | Attacker-valid HMAC ≠ production `FACTUAL_PREMISE` |
| `push_grant_verify_context` still exists | Yes as API, no as production verifier | Neutralized, not deleted |
| No production mint under `K_O` | Intentional | Until a trusted production adapter is bound, production `FACTUAL_PREMISE` stays unreachable by ordinary callers **and** by ungranted corpus `remember()` |
| Subclass overwrite of `_grant_verify_secret` | Tests-only `TestCognitiveOrchestrator` does this | Composition root must instantiate `CognitiveOrchestrator`, not a caller subclass, if that root is production |

None of these re-open C1 (ContextVar / caller verifier selecting production `O.run()`).

---

## 22. Final status matrix

```text
V4_ARCHITECTURE = VALID
V4_SECURITY_REVIEW = PASS
IMPLEMENTATION_STATUS = PASS
SECRET_BOUNDARY = CLOSED
SECRET_NON_OBSERVABILITY = PASS
AUTHORITY_CONSTRUCTION_BOUNDARY = CLOSED
GRANT_ISSUANCE_AUTHORITY = CLOSED
ARBITRARY_GRANT_MINTING = BLOCKED
BOUND_INGEST_CAPABILITY_BOUNDARY = CLOSED
ACQUISITION_ADAPTER_BOUNDARY = CLOSED
VERIFICATION_CONTEXT_AUTHORITY = TRUSTED
ORCHESTRATOR_AUTHORITY_INJECTION = BLOCKED
FAKE_ACQUISITION_SUBSTITUTION = BLOCKED
RETRIEVER_AUTHORITY_ESCALATION = BLOCKED
MEMORY_AUTHORITY_ESCALATION = BLOCKED
CONTEXTVAR_AUTHORITY_ESCALATION = BLOCKED
ISSUER_SUBSTITUTION = BLOCKED
MULTI_ORCHESTRATOR_ISOLATION = PASS
TEST_AUTHORITY_SEPARATION = PASS
PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED
TEST_KEY_SEPARATION = PASS
CLOCK_AUTHORITY = TRUSTED_RUNTIME
LATEST_STATE_MAC = PASS
DIRECT_SQLITE_ESCALATION = BLOCKED
REVISION_AUTHORITY_REUSE = BLOCKED
DERIVED_FACT_SEPARATION = PASS
TOCTOU = PASS
N_HOP_ESCALATION = BLOCKED
WRITEBACK_AUTHORITY = PASS
LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED
PRODUCTION_CODE_MODIFIED = YES
TEST_CODE_MODIFIED = YES
FORENSIC_AUDIT = PASS
IMPLEMENTATION_AUTHORIZED = YES
MERGE = NO
READY_FOR_REVIEW = NO
REPORT = reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md
```

---

## Import validation

After clearing pytest `__pycache__` / `.pytest_cache`:

```text
python scripts/validate_imports.py
VALIDATION PASSED — repository wiring is clean.
```

(`232` modules imported; Lane-A 36/36 inside the same script.) Dirty `reports/*.json` from the validator was restored and not committed.

---

## Stop

Implementation candidate only. Do not merge. Do not mark Ready for Review. Production-ready requires a separate independent decision after inspecting this report and the forensic results.
