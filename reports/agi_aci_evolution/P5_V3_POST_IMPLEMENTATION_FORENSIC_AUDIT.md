# P5 V3 — independent post-implementation forensic audit

**Kind:** Read-only adversarial audit of the implementation tree. Not a fix.  
**Target SHA (mandated):** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Auditor mode:** independent of `P5_V3_IMPLEMENTATION_REPORT.md` (which claimed `IMPLEMENTATION_STATUS = PASS`)  
**AUDIT_COMMIT:** `037ca326f87c4bfb78bdb2fac5cd0679c0f1f7d6`

Not AGI. Not ACI. Not production-ready. Not live trading.  
This audit does **not** modify production code, tests, or schemas.

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.

---

## 0. HEAD discrepancy (mandatory stop)

| Ref | Value |
| --- | --- |
| Mandated implementation SHA | `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83` |
| Current `HEAD` | `8167cf8187b22444219dcdde64a8be313ccc70f3` |
| PR #93 base | `main` |
| PR #93 head | `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| PR draft | **YES** (`isDraft: true`) |
| Working tree (tracked) | clean; untracked `next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt` only |

`HEAD` **differs** from `24b2ab8`.

```text
git diff --stat 24b2ab8..HEAD
  reports/agi_aci_evolution/P5_V3_IMPLEMENTATION_REPORT.md  | 333 insertions
```

The two later commits (`f7cee47`, `8167cf8`) add **only** the self-PASS implementation report. They do not change `architecture/` or `tests/`.

```text
git diff --name-only 24b2ab8 -- architecture tests scripts discovery paper_trading
  (empty)
```

**Security conclusions below are taken from tree `24b2ab8`, not from the later PASS report.**  
The later report is treated as an **advocacy document**, not evidence.

---

## 1. Files in the implementation delta (`e05f31f..24b2ab8`)

Production:

- `architecture/cognitive/memory/observation.py`
- `architecture/cognitive/loop/binding.py`
- `architecture/cognitive/loop/reason.py`
- `architecture/cognitive/loop/orchestrator.py`
- `architecture/cognitive/loop/adapters.py`
- `architecture/cognitive/loop/benchmark.py`
- `architecture/cognitive/benchmark/corpus.py`
- `architecture/cognitive/benchmark/evaluator.py`
- `architecture/cognitive/benchmark/p5_eval.py`

Tests:

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

No `discovery/**`, `paper_trading/**`, soak DBs, or soak scripts.  
`UNRELATED_CHANGES = 0` relative to the authorized V3 implementation scope.

---

## 2. Reconstructed production authority graph

Traced callables, not names.

```text
[UNTRUSTED]
  remember() / sqlite INSERT / ingest_generic_observation / record_world_model_object
  module: architecture.cognitive.memory.store / loop.adapters
  trust: UNTRUSTED
  authority: NONE
  ↓
  OBSERVED_FACT or other kind as STORAGE
  ↓
[NO PRODUCTION DESIGNATED ACQUISITION ADAPTER]
  architecture/ contains zero BoundIngestPort(...) constructions
  production mint count from composition-root adapters = 0
  ↓
[MINT SURFACE THAT STILL EXISTS IN PRODUCTION MODULE]
  BoundIngestPort.persist_acquired(store, AcquisitionRecord)
  module: architecture.cognitive.memory.observation
  caller: anyone who imports the class (not in package __all__)
  input: AcquisitionRecord.statement/source_*/observed_at/domain/valid_until
  trust: CALLER
  authority: MINT (HMAC over those fields)
  ↓
  ObservationAuthority._mint
  ↓
  ObservationGrant JSON in payload["observation_grant"]
  ↓
  CognitiveMemoryStore.remember(epistemic_kind=OBSERVED_FACT)
  ↓
[BIND]
  CognitiveOrchestrator.run → reason → bind_context → bind_item
  latest_observation_fields(store.get)
  observation_grant_permits_factual → verify_observation_grant
  MAC key origin:
      1) explicit key= argument, else
      2) current_grant_verify_context().key, else
      3) fail closed (no key)
  CognitiveOrchestrator.run:
      if parent contextvar is set → USE PARENT KEY/ISSUER
      else → orch._grant_verify_secret + ISSUER_ID
  now origin: run(now=) or time.time(); NEVER task.created_at
  ↓
  FACTUAL_PREMISE iff grant_ok and typed OBSERVED_FACT
  ↓
  reason/critic + apply_episode_positive_policy
  ↓
  reusable_writeback_permitted(verdict, rebind)
  ↓
  HYPOTHESIS / LESSON / episode INFERENCE remember()
```

| Edge | Callable | Module | Ordinary caller can invoke? | Authority |
| --- | --- | --- | --- | --- |
| Persist ungranted OF | `CognitiveMemoryStore.remember` | `memory/store.py` | YES | storage only |
| Generic ingest | `ingest_generic_observation` | `loop/adapters.py` | YES; **refuses** `OBSERVED_FACT` | none for OF |
| World-model | `record_world_model_object` | `memory/store.py` | YES; **refuses** OF | none for OF |
| Named persist RPC | `persist_observed_acquisition` | — | **NO — symbol absent** | — |
| Public IngestPort mint | `IngestPort.persist_acquired` | `observation.py:276` | YES; **raises RuntimeError** | none |
| Process singleton | `_process_authority` | — | **NO — symbol absent** | — |
| Bound mint | `BoundIngestPort.persist_acquired` | `observation.py:285` | **YES by import+construct** | **MINT** |
| Verify injection | `push_grant_verify_context` | `observation.py:201` | **YES by import** | **VERIFIER KEY** |
| Orchestrator ctor DI | `CognitiveOrchestrator(..., ingest=)` | `orchestrator.py:49` | **NO — TypeError** | — |
| Orchestrator parent key | `CognitiveOrchestrator.run` | `orchestrator.py:105-111` | **YES if contextvar preset** | **uses attacker key** |

---

## 3. Public mint removal — named paths

**PROVEN removed / closed:**

| Symbol | Evidence |
| --- | --- |
| `persist_observed_acquisition` | `hasattr(observation, name) is False` at `24b2ab8` |
| `_process_authority` | absent |
| `IngestPort.persist_acquired` | `observation.py:279-282` raises `RuntimeError("IngestPort cannot mint ObservationGrant")` |
| Package `__all__` mint exports | `architecture.cognitive`, `.memory`, `.loop` do not export `BoundIngestPort` / `ObservationAuthority` / `IngestPort` |

**PROVEN still present under other names:**

| Symbol | Role |
| --- | --- |
| `AcquisitionRecord` | caller-filled tuple including `statement`, `source_*`, `observed_at`, `domain`, `valid_until` |
| `ObservationAuthority.__init__(secret=, issuer_id=)` | public constructor; default `issuer_id=ISSUER_ID` |
| `ObservationAuthority._mint` | HMAC issuer; called from `BoundIngestPort` |
| `BoundIngestPort.__init__` / `.persist_acquired` | **this is a mint RPC** |
| `mac_hex` / `canonical_observation_bytes` | public MAC helpers |

`__all__` is not a Python import boundary.  
`from architecture.cognitive.memory.observation import BoundIngestPort` succeeds without package export.

---

## 4. CRITICAL finding C1 — reconstructable matching pair

This audit's threat model (audit brief §5, §14):

- **In scope:** ordinary import / constructor / API abuse.
- **Out of scope:** extracting process-held `orch._grant_verify_secret`, `gc`, sandbox escape.

The following does **not** read `_grant_verify_secret`. It uses only public (non-underscore, except `_mint` which `BoundIngestPort` already calls) production symbols:

```text
from architecture.cognitive.memory.observation import (
    AcquisitionRecord, BoundIngestPort, GrantVerifyContext,
    ObservationAuthority, ISSUER_ID, push_grant_verify_context,
)
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator

k = os.urandom(32)
auth = ObservationAuthority(secret=k, issuer_id=ISSUER_ID)   # production issuer id
BoundIngestPort(auth).persist_acquired(store, AcquisitionRecord(
    statement=<arbitrary>,
    source_type="SYSTEM",
    source_id=<arbitrary>,
    observed_at=<arbitrary>,
    domain=<arbitrary>,
    valid_until=<arbitrary>,
))
push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, now))
CognitiveOrchestrator(...).run(task, now=now)
```

Call path that makes this production-episode-valid:

1. Mint: `BoundIngestPort.persist_acquired` → `ObservationAuthority._mint` (`observation.py:291-294`).
2. Inject verifier: `push_grant_verify_context` (`observation.py:201-202`).
3. Orchestrator **abandons** `_grant_verify_secret`:

```105:111:architecture/cognitive/loop/orchestrator.py
        parent = current_grant_verify_context()
        if parent is not None:
            verify_ctx = GrantVerifyContext(parent.key, parent.issuer_id, float(ts))
        else:
            verify_ctx = GrantVerifyContext(
                self._grant_verify_secret, ISSUER_ID, float(ts)
            )
```

4. Bind: `bind_item` → `observation_grant_permits_factual` → `verify_observation_grant` uses contextvar key (`observation.py:345-348`, `binding.py:538-551`).
5. If the minted statement is task-direct support, `reusable_writeback_permitted` can become true (`episode.py:87-100`) and the orchestrator persists HYPOTHESIS/LESSON (`orchestrator.py:158-163`).

**Attacker capability:** ordinary in-process importer of Lane-B cognitive modules. No tests/ import. No env secret. No reading `orch._grant_verify_secret`.

**Why `__all__` / “not a public package export” is not a block:** Python import of the defining module is a normal application capability. The removed `persist_observed_acquisition` was the same class of callable (a function on `observation.py`). Replacing it with `BoundIngestPort.persist_acquired` + `push_grant_verify_context` does not close issuance; it splits the old singleton matching pair into two importable pieces the caller can re-join.

**PROVEN:** an ordinary caller **can** choose `statement`, `source_*`, `observed_at`, `domain`, `valid_until` (entity/scope live in the statement string / bind support layer) and obtain a grant that `CognitiveOrchestrator.run` will treat as `FACTUAL_PREMISE` after contextvar injection.

`ARBITRARY_GRANT_MINTING = OPEN`  
`GRANT_ISSUANCE_AUTHORITY = OPEN`

Without the contextvar step, an alien `BoundIngestPort` grant is **not** accepted by a default `run()` (parent is `None` → production random key). That is **PROVEN** by `test_alien_bound_ingest_port_is_not_production_valid` and by `orchestrator.py:108-111`. The contextvar step is the missing attack in that test.

---

## 5. Acquisition adapter boundary

**Production designated adapters that mint ObservationGrant:** **none**.

Grep of `architecture/` at `24b2ab8`: `BoundIngestPort(` occurs only in `observation.py` (class body). Corpus, evaluator, p5_eval, loop benchmark, and `ingest_generic_observation` call `remember()`, not mint.

`ingest_generic_observation` (`adapters.py:25-28`) raises if `kind=OBSERVED_FACT`. Domain wrappers (`finance_observation`, …) inherit that.

**What exists instead of a designated adapter:**

`BoundIngestPort.persist_acquired(store, acq: AcquisitionRecord)` accepts a **caller-built** `AcquisitionRecord`. Fields are not taken from a provider result object. They are constructor arguments:

| Field | Origin on this path |
| --- | --- |
| statement | caller |
| source_type / source_id | caller |
| observed_at | caller |
| domain | caller |
| valid_until | caller |

That is option **B** in the audit brief (caller-controlled arbitrary claim), not option **A** (genuine provider output).

**Tests-only adapter** `TestAcquisitionAdapter.acquire` (`tests/observation_test_runtime.py:61-73`):

```text
statement = str(result.raw_reading).strip()
```

`persist_authorized(store, statement, source_id=, observed_at=, domain=, valid_until=)` (`tests/p5_grant_fixtures.py:22-54`) is still a statement RPC. It wraps `timeout_retry_reading(raw_reading=statement, ...)`. Sensor channel is a constant `"software.timeout_recovery"`. The “typed fake result” does not constrain the epistemic claim.

**Do not accept “the adapter is internal.”** `BoundIngestPort` lives in production `observation.py`. The tests-only adapter is a client of that class, not a replacement for it.

`ACQUISITION_ADAPTER_BOUNDARY = OPEN`

---

## 6. BoundIngestPort capability

| Question | Answer at `24b2ab8` |
| --- | --- |
| How created? | `BoundIngestPort(ObservationAuthority(...))` public `__init__` |
| Who can create it? | Any importer of `architecture.cognitive.memory.observation` |
| Who receives it in production? | No composition-root owner. Tests hold `_ADAPTER` |
| Returned from public orch API? | **NO** |
| Extracted from adapter? | Tests: `TestAcquisitionAdapter._port` (underscore). Production: N/A |
| Copied? | Instance holds `self._authority`; `copy.copy` keeps mint capability (language residual) |
| Serialized? | No dedicated serializer; pickle/ACE out of ordinary-API if used |
| Reconstructed? | **YES** — `ObservationAuthority(secret=k)` + `BoundIngestPort` |
| Module global (production)? | **NO** live instance in `observation.py` |
| Factory? | No extra factory; the class **is** the factory |
| Injected into orch constructor? | **NO** (`ingest=` TypeError) |
| Reused to mint arbitrary observations? | **YES** — `persist_acquired` takes a new `AcquisitionRecord` each call |

Ordinary API vs ACE:

- Constructing `BoundIngestPort` and calling `persist_acquired` = **ordinary import/constructor** = **IN SCOPE**.
- Reading `orch._grant_verify_secret` = process-held secret extraction = **OUT OF SCOPE** for C1 (this audit does not need it).

`BOUND_INGEST_CAPABILITY_BOUNDARY = OPEN`

---

## 7. CognitiveOrchestrator injection

Constructor (`orchestrator.py:49-56`): keyword-only `memory`, `hypotheses`, `ledger_path`, `retriever`.  
`inspect.signature` has no `ingest`, `verifier`, `secret`, `issuer`, `authority`.

Setters: none.  
Env: `AHOS_OBSERVATION_GRANT_SECRET` is **not** read (grep of `architecture/` empty).  
Module global issuer: none.

**Still OPEN as an episode-level verifier injection:**

`run()` copies **parent** `GrantVerifyContext.key` / `issuer_id` (`orchestrator.py:105-107`).  
`push_grant_verify_context` is a public function on the production module. That is matching-verifier injection without constructor kwargs.

`bind_context` / `verify_observation_grant` also honor the same contextvar even without `run()`.

Constructor DI tests (`test_cognitive_orchestrator_rejects_*`) are **true** and **insufficient**.

`ORCHESTRATOR_AUTHORITY_INJECTION = OPEN`

---

## 8. Production / test key separation

| Check | Result |
| --- | --- |
| Test key origin | `tests/observation_test_runtime.py:29` `bytes.fromhex("a1"*32)` |
| Test issuer | `ISSUER_ID_TEST = "ahos.observation_authority.test-vector-v1"` |
| Production issuer | `ISSUER_ID = "ahos.observation_authority"` |
| Production key origin | `CognitiveOrchestrator.__init__`: `os.urandom(32)` looping while denylisted (`orchestrator.py:61-64`) |
| Production stores raw test key? | **NO** — SHA-256 denylist only (`observation.py:36-38`) |
| Production issuer + test key | `ValueError` (`observation.py:221-222`) |
| `architecture/` imports `tests.` | **NONE** (grep empty) |
| Test runtime imports production `_SECRET` / `_process_authority` | **NONE** (those symbols absent). It **does** import production `BoundIngestPort`, `ObservationAuthority`, `push_grant_verify_context` |
| Test credentials accepted as production default `run()`? | **NO** unless parent contextvar is the test scope (which tests set on purpose) |

`TEST_KEY != PRODUCTION_KEY` **PROVEN**.  
`PRODUCTION_SECRET ∉ TEST_RUNTIME` **PROVEN** (raw production `os.urandom` bytes are not in fixtures).  
`TEST_RUNTIME ∉ PRODUCTION_IMPORT_GRAPH` **PROVEN**.

`TEST_KEY_SEPARATION = PASS`  
`PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED`

This does **not** imply issuance is closed. Tests mint with a distinct key; ordinary callers mint with a **third** key of their choosing (C1).

---

## 9. Clock forensics

Factual `now` for grants:

```471:479:architecture/cognitive/loop/binding.py
def _trusted_now(task: CognitiveTask, now: float | None) -> float | None:
    """Episode authority time. Never CognitiveTask.created_at."""
    del task
    if now is not None:
        return float(now)
    ctx = current_grant_verify_context()
    if ctx is not None:
        return float(ctx.trusted_now)
    return None
```

`task.created_at` is stored on `EvidenceBinding.task_created_at` (`binding.py:601`) and **deleted** from the clock function. `live_grant_ok()` uses `authority_now`, not `task_created_at` (`binding.py:361-362`).

`CognitiveOrchestrator.run`: `ts = time.time() if now is None else now` (`orchestrator.py:102`), passed to `reason(..., now=ts)` and write-back `bind_context(..., now=ts)`.

| Attack | Result |
| --- | --- |
| Ancient `created_at` + current `run(now=)` | validity uses episode ts (**PROVEN** in tests; matches `_trusted_now`) |
| Future `created_at` | cannot extend `valid_until` |
| Missing trusted now | `grant_ok` stays False (`binding.py:539-540`) |
| Expired vs trusted ts | `verify_observation_grant` `valid_until <= now` → False |
| Future `observed_at` vs trusted ts | `observed_at > now` → False |
| Public `run(now=...)` | **YES**, this is a public freeze of factual `now` |

`created_at` as H1: **CLOSED**.  
`run(now=)` is an ordinary public clock input. It cannot **create** a grant. It can evaluate an already-minted grant against a caller-chosen timestamp. Combined with C1, the caller also chooses `valid_until`. Residual, not the original H1.

`CALLER_CONTROLLED_TIME = CLOSED` (for `CognitiveTask.created_at`)  
`CLOCK_AUTHORITY = TRUSTED_RUNTIME` with documented public `run(now=)` freeze.

---

## 10. Latest-state MAC / TOCTOU / revision

Bind always reloads `store.get(memory_id)` when `store` is passed (`binding.py:491-502`). Orchestrator bind passes `store=self.memory`.

Canonical bytes include statement hash, source_type, source_id, observed_at_us, valid_until, domain, issuer (`observation.py:75-98`). Any latest-row field change that is in that tuple fails `hmac.compare_digest`.

`revise()` pops `observation_grant` when **statement** changes (`store.py:518-519`). Latest row then has no grant → `grant_from_payload` None → False.

`supersede()` pops grant on the successor (`store.py:844`) and marks old `SUPERSEDED`. Verify rejects `SUPERSEDED` status (`observation.py:364-369`).

Copied grant onto another statement: statement SHA mismatch.

Status-only revise **keeps** the grant JSON. `STALE`/`SUPERSEDED`/`ARCHIVED` still fail verify. That is correct.

`LATEST_STATE_MAC = PASS`  
`REVISION_AUTHORITY_REUSE = BLOCKED`  
`TOCTOU = PASS`

These consumption properties **do not** close C1 (attacker mints a fresh matching latest row).

---

## 11. Direct SQLite / generic / world-model

Ungranted `remember`, direct `INSERT INTO memories`, generic ingest, world-model object: no verifying MAC under the episode key → `grant_ok=False` → `_roles` forbids `FACTUAL_PREMISE` (`binding.py:211-214`).

Copied MAC JSON without matching fields / matching key: verify fails.

Test-vector grant under **default** `run()` (no parent context): issuer/key mismatch with `orch._grant_verify_secret` → fail. Under parent test/attacker context: can pass (C1 / tests).

`DIRECT_SQLITE_ESCALATION = BLOCKED`

---

## 12. DERIVED_FACT

`verify_observation_grant` requires `epistemic_kind == OBSERVED_FACT` (`observation.py:354-355`).  
`_roles` for `DERIVED_FACT` always forbids `FACTUAL_PREMISE` (`binding.py:218-220`).  
`may()` recomputes via `live_roles()` / `live_grant_ok()`.

Type substitution on the row is visible to `store.get` latest fields. Serialization copy of grant onto a DERIVED_FACT row fails the kind check.

`DERIVED_FACT_SEPARATION = PASS`

---

## 13. Write-back and N-hop without C1

Storage APIs:

- `remember` / `propose` / consolidation: consolidation **cannot** write OF or DERIVED_FACT (`consolidation.py:78-80`).
- Orchestrator write-back requires `reusable_writeback_permitted` after **rebind** (`orchestrator.py:158-160`).
- That requires a positive verdict, no mixed polarity/uncertainty, and `decision_bearing_supporters` (`episode.py:87-100`).
- Supporters require `may_support_task()` which requires `FACTUAL_PREMISE` + direct support (existing P5 polarity/entity gates).

Ungranted OF → not FACTUAL → not decision-bearing supporter → no reusable HYP/LESSON/INFERENCE from that path. Mixed/contradict/mismatch/uncertain still fail closed.

**With C1**, the attacker supplies a granted supporting OF and **can** pass those gates. That is issuance, not an extra N-hop bypass of critic/episode policy.

N-hop **without** a verifying grant: **BLOCKED**.  
N-hop **given C1 forged grant**: write-back works as the positive path.

Classification below uses ungranted/storage escalation, which is what §12 asked to prove independently of a legitimate adapter: `N_HOP_ESCALATION = BLOCKED` for storage/label escalation; C1 is counted separately as issuance.

`WRITEBACK_AUTHORITY = PASS` (storage ≠ authority)

---

## 14. Test-independence forensics

Failures (report only; not fixed):

1. **Layer 4 file imports the mint helper.** `tests/test_p5_v3_authority_boundary.py` docstring says it must not import `p5_grant_fixtures`, then imports `persist_test_observation` for clock and several authority cases. Independent Layer 4 is **not** mint-free.

2. **`persist_authorized(statement=)`** still feeds an arbitrary statement into production `BoundIngestPort._mint` (via `TestAcquisitionAdapter`). Positive P5 tests (`test_p5_observation_grant.py`, polarity, typed reasoning, cognitive loop) use that helper. That is “arbitrary statement to production mint class,” even though the **key** is the test vector.

3. **Same test key** (`TEST_VECTOR_KEY`) is used for positive FACTUAL proofs and for Layer 4 cases that mint then expect reject-on-mutation. Negative remember/sqlite tests in that file do not mint; the module as a whole is mixed.

4. **`test_env_observation_grant_secret_is_not_read`** reads `orch._grant_verify_secret` (instance attribute). That is ACE-shaped access used as a test oracle, not used to mint.

5. Constructor TypeError tests do **not** attempt `push_grant_verify_context` + `BoundIngestPort` (the surviving matching pair). Green orchestrator-DI tests do not cover C1.

6. `__all__` checks exist but are not the only assertions (hasattr / RuntimeError / TypeError also exist). Not a sole-reliance fail.

`TEST_INDEPENDENCE = FAIL`

Key separation can still PASS while independence of **proof** fails.

---

## 15. Python threat-model boundary

| Path | Ordinary API? | In this threat model? |
| --- | --- | --- |
| `from observation import BoundIngestPort` + construct | YES | **IN SCOPE** (C1) |
| `push_grant_verify_context(...)` | YES | **IN SCOPE** (C1) |
| `CognitiveOrchestrator(..., ingest=)` | constructor rejects | blocked |
| `orch._grant_verify_secret` read | instance attribute | **OUT OF SCOPE** (ACE) |
| `gc.get_objects` / pickle of authority | runtime compromise | **OUT OF SCOPE** |
| Direct sqlite INSERT | storage API | in scope; **blocked** at bind |

Limitation A (fully privileged in-process secret extraction) remains valid **and is not required for C1**.  
C1 is **not** an expansion of the ACE caveat. It is ordinary import/constructor/API.

Python is not a sandbox. This audit does not claim otherwise.

---

## 16. Lane A / soak / artifacts

- `scripts/freeze_lane_a.py` at implementation time: 36/36. Delta `e05f31f..24b2ab8` has no `discovery/**` or `paper_trading/**`.
- Soak scripts/DBs not in that delta. Untracked `reports/PRE_SOAK_STATUS.txt` is **not** committed.
- No test helper imported by `architecture/`.
- No raw test key in production; denylist is SHA-256.
- No second production signer module; `ObservationAuthority` is the single HMAC issuer class (usable with any caller-supplied key).

`LANE_A_STATUS = UNTOUCHED`  
`SOAK_STATUS = UNTOUCHED`

---

## 17. Disagreement with the implementation report

`P5_V3_IMPLEMENTATION_REPORT.md` at `HEAD` claims `ARBITRARY_GRANT_MINTING = BLOCKED` and `FORENSIC_AUDIT = PASS`.

That report treats “not in `__all__`” and “no orchestrator kwargs” as closure of issuance. This independent audit follows **actual callables**:

- the mint RPC was renamed/split, not removed as a capability;
- `run()` was given a parent-context verifier override so tests could inject the test key;
- that same override is the matching-pair join for an ordinary importer.

Regression counts (2042 passed / imports PASS / Lane A 36/36) are **not re-executed here** and are **not** treated as security closure.

---

## 18. Finding tally

| ID | Sev | Summary |
| --- | --- | --- |
| C1 | CRITICAL | Ordinary import of `BoundIngestPort` + `push_grant_verify_context` reconstructs arbitrary FACTUAL mint+verify without stealing `orch._grant_verify_secret` |
| H1 | HIGH | `BoundIngestPort.persist_acquired(AcquisitionRecord)` is a caller-controlled statement/source/time mint API in a production module |
| H2 | HIGH | `CognitiveOrchestrator.run` prefers parent contextvar key/issuer over instance production secret |
| H3 | HIGH | No designated production acquisition adapter; mint surface is generic `AcquisitionRecord` |
| M1 | MEDIUM | `persist_authorized(statement=)` / `raw_reading` is still an arbitrary-claim path (test key) |
| M2 | MEDIUM | Layer 4 “independent” tests import `persist_test_observation` |
| M3 | MEDIUM | Orchestrator DI tests never attack the contextvar join |
| L1 | LOW | Public `run(now=)` freezes factual validity (approved residual, not `created_at`) |
| L2 | LOW | One test reads `orch._grant_verify_secret` |

---

## 19. Explicit non-claims

This audit does not claim AGI, ACI, production readiness, live trading, autonomous truth acquisition, or that Python sandboxes imports.  
It does not claim the Hybrid-D **consumption** MAC/latest-row design failed. That layer still rejects ungranted storage.

---

## 20. Final classification

```text
FORENSIC_STATUS = FAIL
CRITICAL_FINDINGS = 1
HIGH_FINDINGS = 3
MEDIUM_FINDINGS = 3
LOW_FINDINGS = 2
GRANT_ISSUANCE_AUTHORITY = OPEN
ARBITRARY_GRANT_MINTING = OPEN
ACQUISITION_ADAPTER_BOUNDARY = OPEN
BOUND_INGEST_CAPABILITY_BOUNDARY = OPEN
ORCHESTRATOR_AUTHORITY_INJECTION = OPEN
TEST_AUTHORITY_SEPARATION = PASS
PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED
TEST_KEY_SEPARATION = PASS
CALLER_CONTROLLED_TIME = CLOSED
CLOCK_AUTHORITY = TRUSTED_RUNTIME
LATEST_STATE_MAC = PASS
DIRECT_SQLITE_ESCALATION = BLOCKED
REVISION_AUTHORITY_REUSE = BLOCKED
DERIVED_FACT_SEPARATION = PASS
TOCTOU = PASS
WRITEBACK_AUTHORITY = PASS
N_HOP_ESCALATION = BLOCKED
TEST_INDEPENDENCE = FAIL
LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED
UNRELATED_CHANGES = 0
IMPLEMENTATION_SHA = 24b2ab8
MERGE = NO
READY_FOR_REVIEW = NO
REPORT = reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md
```

STOP.
