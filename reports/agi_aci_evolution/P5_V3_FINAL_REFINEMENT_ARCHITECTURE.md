# P5 V3 — final refinement: test authority isolation and orchestrator capability boundary

**Kind:** Final pre-implementation refinement architecture. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Family:** Hybrid-D + V3-A (bound ingest + episode clock)  
**Prior:** `P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md`, `P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md`  
**Implementation SHA:** `e93b3c07d83c4cebb599174fddbd7760b6a82cdd`

This document does **not** modify production code, tests, schemas, Lane A, or soak.  
It does **not** authorize implementation in this turn.

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
Not AGI, ACI, or production-ready.

---

## 1. Executive conclusion

The remaining hole is not Hybrid-D consumption (latest-row MAC). It is **who owns the key**, **who may mint**, and **what the public orchestrator is allowed to accept**.

**Current code (PROVEN):** `CognitiveOrchestrator` injects only `memory`, `hypotheses`, `ledger_path`, and optional `retriever`. It does **not** inject ingest, verifier, or a grant key. Grant mint and verify both use the **same module singleton** `_process_authority()`. `persist_observed_acquisition` / `IngestPort.persist_acquired` are a statement RPC on that singleton. `BoundIngestPort` does not exist. Tests mint by calling that RPC with a test-chosen `statement`.

**Final refinement (minimum):**

1. **Public orchestrator stays input-only.** Do **not** add `ingest=`, `verifier=`, `secret=`, or `grant_key=` to `CognitiveOrchestrator.__init__` or `run`. A matching issuer/verifier pair must not be a public constructor combination.
2. **Verify is a pure function of `(grant, fields, now, key)`.** Bind supplies `key` from an **internally owned** verify context, never from `CognitiveTask` and never from a public kwarg.
3. **Mint is not an orchestrator attribute.** The orchestrator must not hold `BoundIngestPort` / `_mint` as a reachable persist API. Ordinary `orch.run(task)` cannot sign.
4. **Production key ≠ test key.** Production: `os.urandom(32)` at composition-root construction, issuer_id `ahos.observation_authority`. Tests: published vector key **only under `tests/`**, issuer_id `ahos.observation_authority.test-vector-v1`. Production must not import `tests/` or load the vector. `test_key == production_key` is **prohibited**.
5. **Acquisition adapters take a typed result, not `statement=`.** Provider fields are observations; the MAC is AHOS authority over that representation.
6. **Until a designated production adapter is wired, production mint count is zero.** Positive FACTUAL_PREMISE tests use `tests/` composition only.

This is **VALID_AFTER_REFINEMENT**. It does not replace Hybrid-D. Python still cannot stop ACE/`gc`/reading `_grant_secret`. Ordinary application APIs must not recreate mint.

This report **does not** set `IMPLEMENTATION_AUTHORIZED = YES`. Design-only gate.

---

## 2. Current dependency injection (as implemented)

Followed constructors and call graphs, not names.

### 2.1 `CognitiveOrchestrator.__init__`

```text
keyword-only:
  memory: CognitiveMemoryStore          # store; not a grant issuer
  hypotheses: HypothesisStore           # JSONL; not FACT mint
  ledger_path: Path | str               # experiment ledger
  retriever: MemoryRetriever | None     # default MemoryRetriever(); retrieve only
```

**No** ingest port, **no** ObservationAuthority, **no** verifier, **no** secret.  
`BoundIngestPort` **does not exist** in the tree.

`run(now=)` injects episode `ts` into retrieve/context/write-back **timestamps**. It does **not** pass `ts` into `reason`/`bind_context`. Grant `now` is `task.created_at` (**PROVEN** HIGH).

Ordinary caller **can** inject a custom `MemoryRetriever`. That cannot mint an ObservationGrant.

### 2.2 Grant authority (bypasses the orchestrator)

```text
persist_observed_acquisition(store, AcquisitionRecord)
    → IngestPort().persist_acquired
    → _process_authority()._mint          # module singleton, os.urandom once
verify_observation_grant(...)
    → _process_authority()._verify_mac    # SAME singleton
```

| Question | Answer |
| --- | --- |
| What can be injected today? | Orchestrator: memory, hypotheses, ledger, retriever. Grant: **nothing** — global singleton. |
| By whom? | Any caller of those constructors / `persist_observed_acquisition`. |
| Where does the production key originate? | First `_process_authority()` call → `ObservationAuthority()` → `os.urandom(32)` on `_ProcessAuthority.instance`. |
| Can an ordinary caller provide both issuer and verifier? | **Not via orchestrator kwargs.** **Yes** via persist RPC: mint and verify share the singleton. That **is** a matching pair. |
| Matching pair without persist RPC? | `ObservationAuthority(secret=k)._mint` + bind still verifies with **process** secret, not `k`, unless they also replace the singleton. Alien instance ≠ process verify. |
| Default dependency exposing authority? | **Yes:** `IngestPort()` with no args mints under the process secret. `persist_observed_acquisition` is the public form. `retriever=` is not authority-bearing. |

### 2.3 Tests / eval

`tests/p5_grant_fixtures.persist_authorized(statement=…)` and `corpus.seed_corpus` call the production persist RPC. They do not inject orchestrator grant deps. They **are** the matching pair: production signer + production verifier in one process.

### 2.4 What must not be added

These public signatures would **open** Attack E (matching pair):

```text
CognitiveOrchestrator(..., ingest=BoundIngestPort, verifier=fn, secret=bytes)
CognitiveOrchestrator.run(..., grant_key=)
bind_context(..., verify_key=)
reason(..., observation_authority=)
```

The refinement **forbids** those public parameters.

---

## 3. Final production authority graph

```text
UNTRUSTED INPUT                          # remember, task, sqlite, generic ingest
      × statement= mint RPC
      × orchestrator ingest=/verifier=/secret=
      │
DESIGNATED ACQUISITION ADAPTER           # composition-root owned; typed result in
      ↓
TRUSTED ACQUISITION RESULT               # adapter-built canonical tuple
      ↓
BOUND INGEST PORT                        # not an orchestrator public attribute
      ↓
PRODUCTION OBSERVATION AUTHORITY         # os.urandom; issuer_id production
      ↓
OBSERVATION GRANT                        # HMAC-SHA256 over canonical bytes
      ↓
PERSISTED OBSERVED_FACT                  # label + grant JSON; not authority
      ↓
BIND-TIME MAC VERIFICATION               # latest row + pure verify(key=root)
      + trusted episode ts
      ↓
FACTUAL_PREMISE
```

### 3.1 Adapter contract

The adapter’s public method accepts a **typed acquired result** (production: provider-shaped object such as `NormalizedTokenCandidate` plus retrieval metadata; not a free string).

It **must not** accept as an authority request:

- `statement=`
- `source=` / `source_id=` / `source_type=` as caller overrides of provenance
- `observed_at=` as caller clock for the grant tuple
- entity / scope / domain as free-form grant fields

The adapter **fills** those from the result + fixed template + adapter policy:

| Field | Origin |
| --- | --- |
| statement | adapter template over result (e.g. symbol, price, retrieved fields) |
| source_type / source_id | adapter policy from `source_provider` |
| observed_at | result `retrieved_ts` (provider observation time) |
| domain | adapter constant (e.g. `finance`) |
| entity | tokens inside the templated statement; live support at bind |
| provenance | non-UNKNOWN; AI_MODEL/AGENT still vetoed |

**Provider observation** = bytes/fields the provider returned (`retrieved_ts`, `raw_payload_sha256`, metrics).  
**AHOS epistemic authority** = MAC that this exact canonical representation may be used as `OBSERVED_FACT` evidence.  
The adapter is **not** a truth oracle.

Until a Lane-B provider adapter is wired, **do not** mint from `architecture/collector` into cognitive memory (discovery DB / Lane A freeze). Production mint = **zero** adapters. `remember` remains data.

### 3.2 BoundIngestPort

- Constructed only with a specific `ObservationAuthority` instance.
- `persist_acquired` is **not** a public package export and **not** a method on `CognitiveOrchestrator`.
- Adapter holds the port internally; `acquire(result)` returns `MemoryRecord` only.
- Default `IngestPort()` **must not** mint (raise or persist without grant). Remove `persist_observed_acquisition` as a minting function.

### 3.3 Orchestrator vs runtime

| Object | Public? | Holds mint? | Holds verify key? |
| --- | --- | --- | --- |
| `CognitiveOrchestrator` | yes (`loop.__all__`) | **NO** | verify-only, **internal**, not a ctor arg |
| Production composition root (new, **not** in `architecture.cognitive.__all__`) | importable but not advertised | yes, adapter only | installs verify-only into orchestrator internally |
| `tests/` test runtime | tests only | test adapter + test key | test verify |

Ordinary documented API remains: `CognitiveOrchestrator(memory=, hypotheses=, ledger_path=, retriever=)` + `run(task, now=, …)`.

---

## 4. Test authority model

```text
TypedFakeAcquisitionResult          # tests/ dataclass; not AcquisitionRecord(statement=)
        ↓
TestAcquisitionAdapter              # tests/ only; template → canonical tuple
        ↓
Test-only ObservationAuthority      # TEST_VECTOR_KEY, issuer_id test-vector-v1
        ↓
Test Credential (grant JSON)
        ↓
Pure verify_observation_grant(..., key=TEST_VECTOR_KEY)
        ↓
bind / orchestrator wired by tests/compose — not public ctor kwargs
```

### 4.1 Constraints (architecture, not path names)

File location under `tests/` is **insufficient**. Required properties:

1. Production packages must not import `tests/`.
2. Test vector key must not appear in `architecture/`, `config/`, or env (`AHOS_TEST_GRANT_KEY` **forbidden**).
3. Test issuer_id ≠ production issuer_id; production verify rejects the test issuer_id.
4. Production `ObservationAuthority()` / runtime **must refuse** the published test-vector key bytes (denylist of the committed vector) so a mis-wired runtime cannot treat test material as production.
5. Layer-4 test modules must not import the test compose/adapter.
6. Test adapter input is `TypedFakeAcquisitionResult`, not `statement=`.

### 4.2 Can bind use the same verifier logic with an injected test key without opening production DI?

**Yes**, if and only if the injection surface is **not** on the public orchestrator/bind API.

Allowed: `tests/compose_test_cognitive_runtime.py` builds `ObservationAuthority(secret=TEST_VECTOR_KEY)`, TestAdapter, and an orchestrator whose **internal** verify context is installed by the same tests-only builder (same pattern as production composition root, different key and issuer_id).

Forbidden: `CognitiveOrchestrator(secret=TEST_VECTOR_KEY)` or `bind_context(verify_key=…)`. That is Attack E for any caller who also constructs `ObservationAuthority(secret=same)`.

Layer 2/4: construct `CognitiveOrchestrator` **exactly as production public API**. Those instances get an **internal verify-only random key and no mint**. Remember/sqlite/forged grants fail. Tests never receive a matching ingest port.

---

## 5. Test signer vs production signer

### 5.1 `test_statement → production signer`

**NO.** That is the forensic CRITICAL path and the independence failure. It is not saved by living in `tests/`.

### 5.2 `TypedFakeAcquisitionResult → test-only authority → test key → test credential`

**YES**, under §4.1:

- Cryptographic separation from production key and issuer_id.
- Typed result + template (not a sign-this-claim RPC).
- Verifier **algorithm** may be the same function (`verify_observation_grant` with an explicit `key`).
- Production bind never uses the test key.
- Public orchestrator never accepts that key.
- Layer 4 does not hold the test runtime.

This proves: adapter boundary + HMAC verify + latest-row bind + episode clock.  
It does **not** prove production `os.urandom` key ceremony. That ceremony is construction-only (`ObservationAuthority()` without test vector) and is checked by denylist + issuer_id, not by minting under production secret in pytest.

---

## 6. Orchestrator capability boundary

### 6.1 Smallest safe public API (unchanged surface)

```text
CognitiveOrchestrator(memory, hypotheses, ledger_path, retriever=None)
.run(task, *, budget=None, now=None, use_memory=True)
.record_failure(...)
.authorize_execution(...) → always raises
```

`now=` is **episode clock**, not a grant secret.

### 6.2 Forbidden public capabilities

| Mechanism | Rule |
| --- | --- |
| Constructor injection | no ingest/verifier/secret/grant_key |
| Setters | none for grant authority |
| `run(...)` extras | no grant_key |
| dict/provider kwargs | none |
| Duck-typed ingest | not accepted |
| Env | no grant key env |
| Module globals | no live BoundIngestPort; no `_process_authority` getter |
| `architecture.cognitive.__all__` | no ObservationAuthority, IngestPort, persist mint, runtime root |
| Serialization | grant JSON is data; Authority/port not a public reconstruct API |
| `retriever=` | remains; not mint |

### 6.3 Attack E (matching pair)

Ordinary caller supplies issuer + verifier + key:

- **Today:** persist RPC + singleton verify = **OPEN**.
- **After refinement:** public ctor cannot take the pair. `_mint` on a **new** `ObservationAuthority()` uses a different key than a public orchestrator’s internal verify secret. Bind **rejects**. **BLOCKED** as ordinary API.
- Residual: `orch._grant_secret` + `hmac.new` = ACE / out of model.

### 6.4 Test-scoped seam

Not a production public capability: `tests/compose_test_cognitive_runtime.py`. Production `architecture/` must not import it. Layer 4 must not import it.

---

## 7. Trusted clock

Preserve V3.

| | TASK TIME | AUTHORITY / EPISODE TIME |
| --- | --- | --- |
| Field | `CognitiveTask.created_at` | orchestrator `ts` |
| Source | caller / `default_factory=time.time` | `ts = time.time() if now is None else now` in `run` |
| Owner | task metadata | orchestrator episode |
| Grant validity | **MUST NOT** | **MUST** |

`reason` / `bind_context` / `bind_item` / `live_grant_ok` use `trusted_now=ts` stored as `authority_now`. Never `task.created_at`.

**Test freeze:** `run(now=NOW)` remains the episode freeze (existing AHOS pattern). That is **caller-provided episode time**, not task metadata. Production omits `now` → `time.time()`.

| Attack | Result |
| --- | --- |
| Past/future `created_at`, fixed `ts` | grant decision **unchanged** |
| Stale task object, new `run(now=ts)` | uses this episode `ts` |
| `run(now=past)` on expired grant | episode clock **can** revive expiry — residual test/API freeze, **not** H1; document; do not use `created_at` as the fix |
| Replayed episode timestamp | same as `run(now=)`; not task metadata |

Do not import `ProductionScheduler` into the cognitive loop. Do not add a new Clock type. Reuse `time.time()` unix epoch.

---

## 8. Cryptographic separation

### Production key

| | |
| --- | --- |
| Origin | `os.urandom(32)` at production composition-root / orchestrator internal verify context |
| Ownership | that root; not `__all__`; not env |
| Lifetime | process (or orchestrator instance); not serialized |
| Exposure | not logged, not in grant JSON, not in config |
| Use | mint **only** via BoundIngestPort held by designated adapter; verify at bind |
| Issuer | `ahos.observation_authority` |

### Test key

| | |
| --- | --- |
| Origin | committed test vector (≥32 bytes) under `tests/` only |
| Scope | Layer 1 vectors + Layer 3 test runtime |
| Lifetime | repo fixture; not used at production runtime |
| Storage | `tests/` (e.g. vectors module). **Never** `architecture/` |
| Why production cannot use it | no import of `tests/`; denylist of vector bytes in production `ObservationAuthority`; distinct issuer_id |

`test_key == production_key` is **explicitly prohibited**. Production construction must reject the published vector. Tests must not call `_process_authority()` or read instance `_secret` of a production orchestrator.

---

## 9. Bind contract

Conceptual (do not implement in this task):

```text
bind(evidence, trusted_now, task_context)
```

`task_context` = question, domain, entities, support/polarity (informational + live classification).  
`authority_context` = `{key, issuer_id expected, trusted_now}` owned by composition root / test compose.

Steps:

1. Load **latest** `store.get(memory_id)` (fail-closed on integrity failure).
2. Recompute `canonical_observation_bytes` from latest fields.
3. `verify_observation_grant(..., now=trusted_now, key=authority_context.key)` — HMAC `compare_digest`.
4. Statement hash matches grant.
5. Source type/id match grant; UNKNOWN fails.
6. `observed_at` matches grant µs; `observed_at <= trusted_now`.
7. Domain in MAC; entity/scope via live `classify_support` / applicability (not a grant field).
8. `valid_until` vs `trusted_now` (not vs `created_at`).
9. STALE/SUPERSEDED/ARCHIVED fail; revise(statement=) already stripped grant / hash mismatch.
10. **Never** `task_context.created_at` for grant validity.

`bind_context` without `trusted_now`: **fail-closed** (`grant_ok=False`), no fallback to `created_at`.

---

## 10. Attack the final design

Ordinary application caller. Out of scope: OS, FS admin with secret, source edits, debugger, interpreter compromise.

| # | Attack | Result |
| --- | --- | --- |
| A | Arbitrary statement via remember / persist RPC / AcquisitionRecord | **BLOCKED** (RPC gone; remember is data; adapter has no `statement=`) |
| B | Arbitrary source on public APIs | **BLOCKED** for grants; adapter sets provenance from typed result |
| C | Arbitrary timestamp via `created_at` | **BLOCKED** for grants. `run(now=)` is episode clock (residual freeze). Adapter `observed_at` from result `retrieved_ts`, then compared to `ts` |
| D | Arbitrary entity/scope via grant fields | **BLOCKED**; entity is statement text + live support; domain in MAC |
| E | Matching issuer/verifier on public orchestrator | **BLOCKED** (no such kwargs). Singleton persist RPC **removed** |
| F | Test credential on production bind | **BLOCKED** (key + issuer_id + denylist) |
| G | Production imports test key | **BLOCKED** by layout + denylist; no env |
| H | Tests/ordinary code read production `_SECRET` | **BLOCKED** as ordinary API (no getter, no persist mint). ACE **OPEN** (out of model) |
| I | Extract BoundIngestPort from adapter/orch | **BLOCKED** as ordinary API (not returned; not orch attribute). `adapter.acquire` returns `MemoryRecord` |
| J | Serialize Authority/port | **BLOCKED** as ordinary API (not a public reconstruct). Grant JSON is data; still needs matching key |
| K | Factory `ObservationRuntime` | Typed-result mint only; no `statement=`. Software-domain FACT remains **unmintable** until a software adapter exists. Importable root is **not** a free signer |
| L | Globals / `_process_authority` | **BLOCKED** if getter and persist wrappers removed |
| M | Revision inherit | **BLOCKED** (strip + latest hash) |
| N | Direct SQLite | **BLOCKED** at bind (no process/test-runtime MAC) |
| O | N-hop HYP/LESSON/INFERENCE | **BLOCKED** (write-back kinds; no OBSERVED_FACT mint) |

---

## 11. Test independence final standard

**INVALID proof** if the test:

- uses production `_SECRET` or `_process_authority()._mint`
- calls production persist with attacker/test-chosen `statement=`
- imports a production signer RPC
- constructs a **public** matching issuer/verifier pair
- holds `persist_authorized` / test compose while claiming the attacker cannot
- monkeypatches `verify_observation_grant`
- relies only on `__all__` or on `tests/` as a directory

**VALID proof** if:

- Layer 2/4 use only public orchestrator/store/adapter APIs and do not import test compose
- Layer 3 uses typed fake results + test key + test issuer_id
- Layer 1 uses vector key only
- verifier is the real HMAC function with an explicit key
- `created_at` is swept with `trusted_now` fixed
- fresh `store.get` / `run` after persist

---

## 12. Implementation gate (this document)

All refinement properties below are **specified**. They are **not** implemented.

Per this design-only mission: **do not implement now.** `IMPLEMENTATION_AUTHORIZED = NO`.

A later implementation task may proceed only after this refinement is executed **and** a gate re-checks the status keys against code.

---

## 13. MUST CHANGE / MUST NOT CHANGE (future implementation)

### MUST CHANGE (minimum)

- `architecture/cognitive/memory/observation.py` — remove minting persist RPC / singleton getter; pure verify(key=); denylist test vector; BoundIngestPort not default-minting; distinct issuer_ids
- `architecture/cognitive/loop/binding.py`, `reason.py`, `orchestrator.py` — `trusted_now=ts`; no public grant DI; no mint attribute; pass `ts` into reason/bind
- `architecture/cognitive/loop/adapters.py` — do not name a mint helper
- `architecture/cognitive/benchmark/*`, `loop/benchmark.py` — no production persist mint; inject nothing from public API
- New **unexported** production composition root (adapter-owned port) when a real adapter exists; until then mint = 0
- `tests/` — test vector, typed fake result, compose runtime, split Layer 2/4 vs 3; delete use of production persist as fixture
- `CognitiveOrchestrator.__init__` public signature **unchanged** except it must **not** grow grant kwargs

### MUST NOT CHANGE

- Lane A, soak, HMAC-SHA256 algorithm, canonical `AHOS-OG-v1` field set (issuer_id value may gain a test sibling)
- `remember` as data; SQLite engine; grant in `payload_json`
- critic / hop / propose / accept / world-model refuse
- historical forensic reports
- PR draft/merge state in this task

---

`FINAL_REFINEMENT = VALID`

`V3_ARCHITECTURE = VALID_AFTER_REFINEMENT`

`V3_SECURITY_REVIEW = PASS`

`GRANT_ISSUANCE_AUTHORITY = CLOSED`

`CALLER_CONTROLLED_TIME = CLOSED`

`PRODUCTION_BOUNDARY_PROOF = INDEPENDENT`

`TEST_AUTHORITY_SEPARATION = PASS`

`ORCHESTRATOR_AUTHORITY_INJECTION = BLOCKED`

`PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED`

`TEST_KEY_SEPARATION = PASS`

`ARBITRARY_GRANT_MINTING = BLOCKED`

`DIRECT_SQLITE_ESCALATION = BLOCKED`

`REVISION_AUTHORITY_REUSE = BLOCKED`

`LATEST_STATE_MAC = PASS`

`DERIVED_FACT_SEPARATION = PASS`

`TOCTOU = PASS`

`N_HOP_ESCALATION = BLOCKED`

`CLOCK_AUTHORITY = TRUSTED_RUNTIME`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`PRODUCTION_CODE_MODIFIED = NO`

`TEST_CODE_MODIFIED = NO`

`IMPLEMENTATION_AUTHORIZED = NO`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`REPORT = reports/agi_aci_evolution/P5_V3_FINAL_REFINEMENT_ARCHITECTURE.md`
