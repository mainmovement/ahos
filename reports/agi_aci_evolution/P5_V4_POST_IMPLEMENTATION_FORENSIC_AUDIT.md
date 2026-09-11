# P5 V4-PIN post-implementation forensic audit

**Kind:** Independent read-only ordinary-caller attack on the V4-PIN implementation candidate.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT** (`isDraft=true`, `state=OPEN`)  
**This document does not trust** `P5_V4_IMPLEMENTATION_REPORT.md`. Claims were re-traced in production source and re-attacked at runtime.  
**This audit did not modify production code, tests, schemas, Lane A, or soak.** Temporary probes lived under `/tmp` only.  
**AUDIT_REPORT_COMMIT:** `6f1a4f95d58c85bcfded8e82a0c313e84949a441`

Not AGI. Not ACI. Not production-ready. Not live trading. `MERGE = NO`. `READY_FOR_REVIEW = NO`.

Proof language: **PROVEN** (this tree) / **RESIDUAL** (in or out of declared threat model).

```text
AUDIT_BASELINE = 24b2ab8244f41d9e78582ccfc41dc4b0cf490a83
IMPLEMENTATION_SHA = afdff2539943441244d05478a7004bc4bcc5976f
AUDIT_HEAD = ffde25a8693e9645fa85c9d979bd8771692c1b90
POST_IMPLEMENTATION_DELTA = reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md only
```

---

## 1. Audit target SHA

Audited working tree = `origin/cursor/agi-aci-p5-typed-evidence-reasoning-9500` at:

`ffde25a8693e9645fa85c9d979bd8771692c1b90`

PR headRefOid matches that commit. Untracked local noise (`next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt`) is **not** part of the candidate and was not added.

---

## 2. Implementation SHA

Last commit that changes production or test **code**:

`afdff2539943441244d05478a7004bc4bcc5976f`

(`bc49093` implement → `6377528` test fixtures → `afdff25` evaluate_reason order test.)

The implementation report’s `CODE_SHA` / `IMPLEMENTATION_SHA` of `afdff25` matches that code tip.

---

## 3. HEAD vs claimed implementation

`git diff afdff25..HEAD` is **one file**: `reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md` (record + SHA stamp: `404830b`, `ffde25a`).

Production/test Python at HEAD **equals** `afdff25`. The audit therefore attacks the reported implementation tree, plus an untrusted narrative document that was ignored except as a claim list.

---

## 4. Exact diff scope (`24b2ab8..HEAD`)

**Production**

- `architecture/cognitive/loop/orchestrator.py`
- `architecture/cognitive/memory/observation.py`
- `architecture/cognitive/loop/binding.py`
- `architecture/cognitive/loop/reason.py`

**Tests**

- `tests/observation_test_runtime.py`
- `tests/test_p5_v4_authority_boundary.py`
- `tests/test_p5_v3_authority_boundary.py`
- `tests/test_p5_observation_grant.py`
- `tests/test_p5_second_forensic.py`
- `tests/test_p5_episode_polarity.py`
- `tests/test_p5_negation_entity.py`
- `tests/test_typed_reasoning.py`
- `tests/test_cognitive_loop.py`

**Reports (not executed as authority)**

- `reports/agi_aci_evolution/P5_V3_IMPLEMENTATION_REPORT.md`
- `reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`
- `reports/agi_aci_evolution/P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md`
- `reports/agi_aci_evolution/P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md`
- `reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md`

`git diff 24b2ab8..HEAD -- discovery/** paper_trading/**` is empty. No soak paths in the delta.

---

## 5. Threat model (applied)

**Attacker:** ordinary in-process Python application code.

**Did:** import modules; construct `ObservationAuthority` / `BoundIngestPort` / grants / fake rows; `push_grant_verify_context`; public `bind_item` / `bind_context` / `reason` / `verify_observation_grant`; `retriever=` / `memory=` DI; nested `CognitiveOrchestrator`; direct SQLite; `revise` / `supersede`; field mutations; repeated `run()` under a live ContextVar.

**Did not:** edit source; debugger; `gc` / `sys._getframe` / `ctypes`; OS admin.

**Composition-root probe (labeled, not counted as a plugin bypass):** copying `O._grant_verify_secret` from an instance the auditor constructed, solely to test HMAC isolation `Grant(O1)→O1 / Grant(O1)→O2`. The declared V4 threat model treats assignment/theft of that field on a held instance as ACE / out of plugin scope. Ordinary attacks below **do not** use it except Attack 9 isolation ACCEPT legs.

---

## 6. Authority graph (traced, this tree)

```text
CognitiveOrchestrator.__init__
  K_O = os.urandom(32)   # retry while SHA-256 ∈ test-vector denylist
  self._verify_issuer_id = ISSUER_ID   # not a constructor argument
  no **kwargs; no secret=/verifier=/ingest=/issuer=

O.run(task, now=?)
  ts = now or time.time()          # not task.created_at
  retriever.retrieve(memory, task, now=ts)    # no ContextVar push
  assemble_context(...)
  O._reason_episode
       O._bind_context → O._bind_item
            load_bind_snapshot(store.get latest row)
            O._permits_observation_grant(...)   # no key argument
                 observation_grant_permits_factual(
                     key=self._grant_verify_secret,
                     expected_issuer_id=self._verify_issuer_id,
                     now=ts,
                 )
            assemble_evidence_binding(grant_ok=<bool>)
       evaluate_reason(task, ctx, bindings)   # no verifier
  O._bind_context again → reusable_writeback_permitted
```

`grep` of `push_grant_verify_context(` across the repo: **definition** in `observation.py` plus **tests only**. `O.run` does not call it.

`current_grant_verify_context()` production consumer: `binding._trusted_now` only. Public `bind_item` uses that for `authority_now` **after** forcing `grant_ok=False`. Production `_bind_item` passes `now=ts` into `_permits` and `assemble_evidence_binding`; it does not call `_trusted_now`.

---

## 7. Secret data-flow (traced)

```text
K_O exists as O._grant_verify_secret
Read in production only by O._permits_observation_grant → key= argument
  of observation_grant_permits_factual / verify_observation_grant
```

Runtime probes:

- After production `run()`, `current_grant_verify_context()` is `None` if it was `None` at entry (**PROVEN**, `PUSH_no_publish`).
- Malicious retriever at `retrieve()` saw ContextVar key `None` (**PROVEN**, A5).
- Malicious `store.get` first call saw ContextVar key `None` (**PROVEN**, A6).
- `repr(O)`, `str(O)`, `repr(CognitiveResult)`, pickle of `CognitiveResult` did not contain `K_O` bytes or the field name `_grant_verify_secret` (**PROVEN**, A15).
- `EvidenceBinding.as_dict()` did not contain `K_O` (**PROVEN**).

`verify_observation_grant(..., key=None)` returns `False` even when ContextVar holds an attacker key (**PROVEN**, A4). It does not read the ContextVar (source: `use_key = key`; `if use_key is None: return False`).

---

## 8. Attack matrix 1–15

Independent `/tmp` probe against live `CognitiveOrchestrator` (not pytest). Outcomes below are **production `O.run()` / `O._bind_context` `may(FACTUAL_PREMISE)`** unless noted.

| # | Attack | Production FACTUAL | Notes |
| --- | --- | --- | --- |
| 1 | `ObservationAuthority(secret=attacker_key)` + persist | **REJECTED** | `writeback=False`, verdict `INSUFFICIENT_EVIDENCE` |
| 2 | `BoundIngestPort(ObservationAuthority(...))` | **REJECTED** | Issuer defaulted to production `ISSUER_ID`; HMAC still alien |
| 3 | `push_grant_verify_context(attacker_key, ISSUER_ID)` then `run` twice + nested `O` | **REJECTED** | ContextVar still held attacker key; production ignored it. Exception `ValueError` text did not leak secrets. No `asyncio` in `architecture/cognitive`. |
| 4 | Public `verify_observation_grant` / `bind_item` / `bind_context` / `reason` | **FAIL-CLOSED** | Own HMAC under attacker key **True**; `key=None` **False**; public bind FACTUAL **False**. Signatures have no `key=`/`secret=`/`verifier=`. |
| 5 | Malicious retriever: return data, push ContextVar, mint via BoundIngestPort during `retrieve` | **REJECTED** | Data injection happened; production authority did not. Retriever did not observe `K_O`. |
| 6 | Malicious memory `get`: read ContextVar, push attacker context | **REJECTED** | First `get` ContextVar `None` |
| 7 | SQLite: no grant; forged MAC; copied MAC + other statement | **REJECTED** | Latest-row bind still requires `K_O` HMAC |
| 8 | Revise attacker statement; revise genuine statement; supersede | **STRIPPED / REJECTED** | Statement change pops `observation_grant`; supersede pops it. Genuine row was FACTUAL **before** revise (auditor mint under `K_O`) and not after. |
| 9 | Two production instances, shared store | **HOLD** | `K_O1 != K_O2`. `Grant(K_O1)→O1` ACCEPT, `→O2` REJECT; reverse. Attacker grant REJECT on both. ACCEPT legs used composition-root copy of instance secrets (see §5). |
| 10 | Attacker issuer + attacker key | **REJECTED** | |
| 11 | Ctor/run `secret=` `verifier=` `ingest=` `authority=` `issuer=` `grant_verify_context=` `config=` | **BLOCKED** (`TypeError`) | `__init__` params: `memory`, `hypotheses`, `ledger_path`, `retriever` only. No `**kwargs`. No env `AHOS_*` in orchestrator source. |
| 12 | `persist_observed_acquisition` / `O.ingest` | **ABSENT** | Fake dataclass is not an authority path |
| 13 | Attacker evidence → writeback hyp/lesson | **BLOCKED** | `reusable_writeback=False`, empty hyp/lesson ids. Mixed ungranted SUPPORT+CONTRA: `INSUFFICIENT_EVIDENCE`, no reusable writeback. |
| 14 | N-hop inference episode; `DERIVED_FACT` + copied grant blob | **REJECTED / BLOCKED** | |
| 15 | Secret via ContextVar, repr/str, pickle, binding dict | **CLEAN** | Collaborators were not handed `K_O` |

**Public `assemble_evidence_binding(..., grant_ok=True)`:** can assemble a binding with `may(FACTUAL_PREMISE)=True`, and `evaluate_reason` on that list can emit `WEAKLY_SUPPORTED`. **That is not `O.run()`.** Re-running production `O.run` on the same row stayed non-factual. Classified **LOW residual**, not a production-orchestrator bypass.

---

## 9. Cryptographic / canonicalization audit

Canonical bytes (**PROVEN** prefix `AHOS-OG-v1|FACTUAL_INGES…`):

`GRANT_VERSION|GRANT_PURPOSE|GRANT_KIND|statement_sha256|source_type|source_id|observed_at_us|valid_until_token|domain|issuer_id`

MAC: HMAC-SHA256 hex, `hmac.compare_digest`.

Mutating stored grant fields `issuer_id`, `mac`, `source_id`, `domain`, `statement_sha256`, `version`, `kind` each yielded production FACTUAL **False** (**PROVEN**). Copied MAC onto another statement: **False**. Forged all-zero MAC: **False**.

Entity/scope/applicability remain binding-layer gates (`_applicability`, support class, `may_support_task`). They were not stripped by V4. Ungranted mixed polarity did not write back.

---

## 10. TOCTOU audit

`load_bind_snapshot` prefers `store.get(memory_id)` over retrieved-item fields.

Probe: retrieve (old statement still `SUPPORT`) → `revise` statement to `CONTRA` (grant popped) → production `run`/`_bind_context` FACTUAL **False** (**PROVEN**). Verification and role decision use the latest row, not the retrieved snapshot.

Writeback rebinds via `O._bind_context` from `RetrievedItem`s + `store.get`, not from caller-mutated `EvidenceBinding` objects.

---

## 11. Clock audit

`O.run` sets `ts = time.time() if now is None else now` and passes `ts` into `_permits_observation_grant`. `CognitiveTask.created_at` is stored on bindings as `task_created_at` and is **not** the HMAC `now` (**PROVEN**: expired grant stayed non-factual when `created_at` was set far in the future and `run(now=NOW)`).

Expired grant (`valid_until=NOW-60`) at `now=NOW`: non-factual. Future `observed_at`: non-factual. `run(now=NOW-120)` on that expired **genuine** grant became temporally valid — that is composition-root `now=`, the declared trusted episode clock, not `created_at`. `CLOCK_AUTHORITY = TRUSTED_RUNTIME`.

Public `_trusted_now` may read ContextVar `trusted_now` only when `now is None`; public bind still forces `grant_ok=False`.

---

## 12. Test independence audit

| Surface | Evidence |
| --- | --- |
| Test key | `TEST_VECTOR_KEY = bytes.fromhex("a1"*32)` in `tests/observation_test_runtime.py` |
| Test issuer | `ISSUER_ID_TEST` |
| Test composition | `TestCognitiveOrchestrator` overwrites `_grant_verify_secret` / `_verify_issuer_id` **after** `super().__init__` |
| Production ctor | no `verify_secret=` |
| Production denylist | `ObservationAuthority(secret=TEST_VECTOR_KEY, issuer_id=ISSUER_ID)` raises |
| Production modules | do not import `tests.observation_test_runtime` / `TEST_VECTOR_KEY` (Layer 4 asserts this) |
| Layer 4 | must not import `tests.p5_grant_fixtures` |
| `grant_verify_scope` | still **sets** ContextVar; V4 tests use it to prove production **ignores** it. Positive FACTUAL paths use `TestCognitiveOrchestrator` / `bind_with_test_authority`, not production `run` + scope |
| Production `CognitiveOrchestrator` in Layer 4 / V4 | negative C1 replay: BoundIngestPort + push + `O.run` → not FACTUAL |

Tests do not call a production signer to mint expected evidence. Auditor isolation ACCEPT used instance secrets only in `/tmp` probes, not in the test suite.

`TEST_INDEPENDENCE = PASS`. `TEST_AUTHORITY_SEPARATION = PASS`. `PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED` (tests never read production `K_O`).

---

## 13. Lane A verification

```text
python scripts/freeze_lane_a.py
Lane-A integrity OK (36 files pinned)
```

No `discovery/**` or `paper_trading/**` in `24b2ab8..HEAD`.

---

## 14. Soak verification

No soak paths in `24b2ab8..HEAD`. `reports/PRE_SOAK_STATUS.txt` is untracked local noise, not in the candidate. Soak infrastructure **UNTOUCHED**.

---

## 15. Findings

**CRITICAL:** none.  
**HIGH:** none.  
**MEDIUM:** none.  
**LOW residuals (not production `O.run` bypasses):**

1. **Public `assemble_evidence_binding(grant_ok=True)` + `evaluate_reason`** can synthesize `FACTUAL_PREMISE` / `WEAKLY_SUPPORTED` **outside** `O.run`. Production `run` recomputes bind via `_permits_observation_grant` and stayed non-factual on the same attacker row.
2. **Holder of `O` can read `O._grant_verify_secret`** (ordinary attribute). Declared out of plugin threat model. Used only to prove HMAC isolation. Plugins given `retriever=` / `memory=` without `O` did not obtain `K_O`.
3. **`push_grant_verify_context` remains importable** and still writes a ContextVar. Production verify does not read it. Public bind may read `trusted_now` from it while `grant_ok` stays False.
4. **`BoundIngestPort` still mints caller HMAC.** Attacker-valid MAC ≠ production FACTUAL (**PROVEN**).
5. **No production mint adapter bound to `K_O`.** Ordinary callers cannot create `Grant(O)` without the instance secret. That is issuance closure, not a bypass.
6. **`run(now=)` is the episode clock.** A caller of `run` can rewind/advance `now` for grants that already verify under `K_O`. They cannot make an alien HMAC factual.

No untested composition path was found that lets an ordinary caller manufacture a credential `CognitiveOrchestrator.run` trusts without `K_O`.

---

## 16. Residual risks

Same-process ACE (`O._grant_verify_secret = …`, replacing `_permits_observation_grant`, module monkeypatch of `verify_observation_grant`) remains possible in Python and remains **out of** the declared plugin threat model. Frame-walking / `gc` / process memory remain out of scope; if brought in, Option E is required (prior design gate).

---

## 17. Final status matrix

```text
FORENSIC_STATUS = PASS
CRITICAL_FINDINGS = 0
HIGH_FINDINGS = 0
MEDIUM_FINDINGS = 0
LOW_FINDINGS = 6

IMPLEMENTATION_SHA = afdff2539943441244d05478a7004bc4bcc5976f
AUDIT_HEAD = ffde25a8693e9645fa85c9d979bd8771692c1b90

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
LATEST_STATE_MAC = PASS
DIRECT_SQLITE_ESCALATION = BLOCKED
REVISION_AUTHORITY_REUSE = BLOCKED
DERIVED_FACT_SEPARATION = PASS
TOCTOU = PASS
CLOCK_AUTHORITY = TRUSTED_RUNTIME
N_HOP_ESCALATION = BLOCKED
WRITEBACK_AUTHORITY = PASS
TEST_INDEPENDENCE = PASS
TEST_AUTHORITY_SEPARATION = PASS

LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED

PRODUCTION_CODE_MODIFIED_DURING_AUDIT = NO
TEST_CODE_MODIFIED_DURING_AUDIT = NO

MERGE = NO
READY_FOR_REVIEW = NO

REPORT = reports/agi_aci_evolution/P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md
```

---

## Validation independently re-run (existing tests only)

| Check | Result |
| --- | --- |
| `tests/test_p5_v4_authority_boundary.py` + v3 + observation grant + memory boundary + second forensic | **150 passed** |
| Full pytest | **2065 passed, 3 skipped** (223.93s) |
| `scripts/validate_imports.py` (pycache cleaned; JSON restore) | **VALIDATION PASSED** |
| Lane A | **36/36** |

Pytest passing is **not** the closure proof. Closure is from the traced production path plus the `/tmp` ordinary-caller matrix (34 probe rows, 0 production bypasses).

---

## Claim checks (implementation report vs tree)

| Claim | Independent result |
| --- | --- |
| `K_O` generated in `O.__init__` via `os.urandom(32)` | **PROVEN** (source) |
| Caller cannot supply it via ctor/run | **PROVEN** (signature + TypeError) |
| `O.run` does not copy ContextVar keys | **PROVEN** (source; no `push`/`current` in orchestrator; retriever saw `None`) |
| `_permits_observation_grant` is the production verifier | **PROVEN** (`_bind_item` is the only production caller) |
| Public reason/bind fail-closed | **PROVEN** (`grant_ok=False`; runtime) |
| `push_grant_verify_context` has no production-verify effect | **PROVEN** (no production call; `verify_observation_grant` ignores ContextVar; runtime A3) |

---

## Stop

Audit complete. No implementation changes. No test changes. Do not merge. Do not mark Ready for Review. Release-readiness is a separate decision.
