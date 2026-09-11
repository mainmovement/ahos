# P5 V4 — authority construction boundary

**Kind:** Read-only architecture and threat model. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Audited implementation SHA:** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**Prior independent audit:** `reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` (`FORENSIC_STATUS = FAIL`)  
**This document does not authorize implementation.**

Not AGI. Not ACI. Not production-ready. Not live trading.  
Lane A and soak are not in scope. Production code, tests, and schemas are **not** modified in this turn.

Proof language: **PROVEN** (current tree) / **DESIGN** (V4, unimplemented).

---

## 1. Proven failure (current tree)

An ordinary importer, without reading `CognitiveOrchestrator._grant_verify_secret`, can:

1. Construct `ObservationAuthority(secret=k, issuer_id=ISSUER_ID)`  
   (`architecture/cognitive/memory/observation.py`, class at module scope, public `__init__`).
2. Construct `BoundIngestPort(authority)` and call `persist_acquired(store, AcquisitionRecord(statement=…, source_*=…, observed_at=…, domain=…, valid_until=…))`.
3. Call `push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, now))`.
4. Call `CognitiveOrchestrator.run(...)`.

`run()` does this (**PROVEN**):

```105:111:architecture/cognitive/loop/orchestrator.py
        parent = current_grant_verify_context()
        if parent is not None:
            verify_ctx = GrantVerifyContext(parent.key, parent.issuer_id, float(ts))
        else:
            verify_ctx = GrantVerifyContext(
                self._grant_verify_secret, ISSUER_ID, float(ts)
            )
```

The instance secret is dropped. Bind (`verify_observation_grant`) uses the contextvar key. The attacker-chosen pair becomes `FACTUAL_PREMISE` if the statement is otherwise supporting.

This is ordinary import + constructor + public function composition. It is **in scope**.

---

## 2. Critical Python answers

### 2.1 Is `ObservationAuthority(secret=k)` ordinary API usage?

**YES. IN SCOPE.**

Evidence, not naming:

| Fact | Evidence |
| --- | --- |
| Class is importable | defined at module top level in `architecture/cognitive/memory/observation.py` |
| Constructor is a normal `__init__` | keyword `secret=` accepts caller bytes |
| No capability token is required | `secret is not None` branch stores caller material |
| `__all__` of `architecture.cognitive.memory` does not list it | `from architecture.cognitive.memory.observation import ObservationAuthority` still works |

Package location, underscores on `_mint`, and comments (“not a public package export”) are not a boundary.

### 2.2 Is constructing `BoundIngestPort` ordinary API usage?

**YES.** Same module, public `__init__(authority)`, public `persist_acquired`. `_mint` is invoked inside that method; the attacker never needs to call `_mint` by name.

### 2.3 Is `push_grant_verify_context` ordinary API usage?

**YES.** Module-level public function. No token. Writes a process `ContextVar`.

### 2.4 What is a production-valid ObservationGrant?

**Current (broken) definition — PROVEN:**

A grant is treated as factual iff `verify_observation_grant` succeeds under **whatever key is in `current_grant_verify_context()`** (or an explicit `key=` argument on that function). `issuer_id` must match that context’s issuer (default `ISSUER_ID`). Object identity of `ObservationAuthority` is **not** checked. Composition-root identity is **not** checked.

So today validity is: **caller-configurable verifier key + MAC**. That is why a new `(k, k)` pair works.

**V4 required definition — DESIGN:**

```text
production-valid ObservationGrant
    = HMAC-SHA256 over the canonical observation tuple
      under the CognitiveOrchestrator *instance* verify secret
      that that instance generated at construction (os.urandom)
      and never replaced via public API
```

Validity is **not**:

- caller `issuer_id`
- caller `GrantVerifyContext`
- any `ObservationAuthority` the caller constructed
- any key other than **this** orchestrator instance’s `_grant_verify_secret`

A caller-controlled issuer/verifier pair must **never** define production authority.

### 2.5 Can same-process Python stop all HMAC objects from existing?

**NO**, if `mac_hex` / `canonical_observation_bytes` remain importable, or if the attacker reimplements HMAC-SHA256. Forbidding `ObservationAuthority(...)` by hiding the class does not forbid forging grant JSON.

Therefore V4 must close **production acceptance**, not the existence of attacker-HMAC bytes.

Hiding constructors, renaming, `__all__`, stack inspection, and filename checks are rejected (brief §3 A–O).

---

## 3. Current authority graph (actual callables)

| Who | File | Symbol | Input | Output | Authority |
| --- | --- | --- | --- | --- | --- |
| Ordinary app / tests | `observation.py` | `ObservationAuthority.__init__` | caller `secret`, `issuer_id` | issuer object | **MINT-capable** |
| Ordinary app / tests | `observation.py` | `BoundIngestPort.__init__` | any `ObservationAuthority` | port | **MINT-capable** |
| Ordinary app / tests | `observation.py` | `AcquisitionRecord(...)` | statement/source/time/domain | tuple | untrusted claim |
| Ordinary app / tests | `observation.py` | `BoundIngestPort.persist_acquired` | store + `AcquisitionRecord` | row + grant JSON | **MINT** |
| Production composition | **none** | no `BoundIngestPort(` in `architecture/` except the class | — | production mint count **0** | — |
| Tests | `tests/observation_test_runtime.py` | `TestAcquisitionAdapter` | `TypedFakeAcquisitionResult` (`raw_reading` → statement) | test grant | **TEST MINT** |
| Tests | `grant_verify_scope` | `push_grant_verify_context(TEST_VECTOR_KEY, …)` | test key | contextvar | **VERIFIER INJECTION** |
| Ordinary app | `push_grant_verify_context` | same function | attacker key | contextvar | **VERIFIER INJECTION** |
| Orchestrator | `CognitiveOrchestrator.__init__` | `os.urandom(32)` | none public | `_grant_verify_secret` | **VERIFY OWNER** (then discarded if parent set) |
| Orchestrator | `CognitiveOrchestrator.run` | parent contextvar **or** instance secret | `now=` | episode | **VERIFY SWITCH** |
| Bind | `bind_item` / `verify_observation_grant` | contextvar key or `key=` | latest row | `grant_ok` | **CONSUME** |
| Ordinary app | `CognitiveOrchestrator(...)` | memory, hypotheses, ledger, retriever | orch | no mint kwargs | input-only ctor **PROVEN** |

Verifier is not a separate object. It is `mac_hex(use_key, canonical)` inside `verify_observation_grant`.

Composition root for production cognitive loop today is **whoever constructs `CognitiveOrchestrator`**. That object owns a verify secret and **does not mint**. Tests join mint (test key) to verify (same test key via contextvar) across that hole.

---

## 4. Option analysis

Legend for later matrix: **R** = rejected as production-valid under that option; **O** = still open; **A** = ACE / out of threat model; **N** = not applicable.

### OPTION A — Composition-root-owned authority

Root constructs orchestrator (already true). Root would also hold the only mint port bound to **the same instance secret**.

Python still allows `ObservationAuthority(secret=k)` if that class remains at module scope. That is **not** automatically sufficient.

**A becomes sufficient for production-valid grants iff** the verifier used by `run`/`bind` **cannot** be switched to `k`. Then attacker HMAC is not a production credential (same as a JWT signed with a random key against a server that does not install that key).

A **without** pinning the verifier is the current failure mode.

### OPTION B — Capability without public constructor

Move issuer/port behind a factory / nested class.

Ordinary `ObservationAuthority(secret=k)` by import name may fail. Attackers still:

- call public `mac_hex` + build `ObservationGrant` dict (**ordinary API** if those helpers stay public);
- reconstruct via factory if the factory is importable and takes `secret=` / `statement=`;
- pickle/copy a returned port if the root **hands out** `BoundIngestPort`.

If the factory takes no caller key and returns nothing mint-capable to ordinary code, B **collapses to A + pin**. Hiding the class alone is brief §3 C/D.

### OPTION C — Closure factory

Root does `secret = os.urandom(32); def acquire(typed): mint(secret, adapter_fields(typed))` and never returns `secret`.

- If `acquire` accepts `statement=`, it **is** the old persist RPC (**O**).
- If `acquire` is never given to ordinary callers (mint count 0), mint is closed; verify pin still required.
- Closure cell extraction via `func.__closure__` is **ACE** (out of scope) if ordinary code never receives `acquire`.
- If ordinary code **does** receive `acquire` and it only accepts a typed adapter result, see D.

Closures are not a Python security boundary against ACE. They **are** a reasonable way to avoid a module-global singleton RPC.

### OPTION D — Acquisition-port capability (typed result only)

Public operation: not `persist(statement=)`.

Production (when an adapter exists):

```text
adapter.poll_or_fetch()           # adapter talks to provider; no result argument
        → internal typed result     # not a caller-supplied dataclass
        → internal canonical tuple
        → mint under orch instance secret
```

Caller-constructed `TypedProviderResult(...)` or `AcquisitionRecord(statement=...)` must **not** be a parameter of any production mint function.

Forgery of a dataclass is **ordinary API**. Therefore the production method must **not accept** that dataclass from the caller. The adapter must obtain fields from its own I/O. Until a provider adapter is wired, production mint stays **zero**.

Tests may have `TypedFakeAcquisitionResult` only inside `tests/`, minted under the **test orchestrator instance secret**, never installed into production `run()` via contextvar.

### OPTION E — Separate process issuer

A local child process holds the production HMAC key; the app process only sends adapter-attested bytes and receives a grant blob. Ordinary `ObservationAuthority(secret=k)` in the app cannot match the child key; the child must not accept a caller key.

This **does** close in-process construction of the **production** issuer. It is **not** the minimum: Windows-first / local / $0 allows it, but verifier pinning already stops attacker-`k` from becoming production-valid **without** IPC, if no public API installs `k` as the verifier.

E is the fallback if V4 later reintroduces a public “set verify key” or a persist RPC on a process singleton.

---

## 5. Attack matrix (production-valid FACTUAL_PREMISE)

Rows = ordinary-API attacks. Cells = whether that option, **implemented as specified in §6**, yields production-valid authority.  
R = rejected; O = open; A = ACE only.

| Attack | A pin-only | B hide ctor | C closure no-RPC | D poll-only adapter | E child process |
| --- | --- | --- | --- | --- | --- |
| Construct issuer `ObservationAuthority(k)` | R (grant not accepted) | R by name; O via `mac_hex` unless helpers removed | R if no verify switch | R | R vs child key |
| Construct verifier / `GrantVerifyContext(k)` | R if `run` ignores parent | O if contextvar remains | R if ignored | R | R |
| Construct authority + own key | R | O via MAC helpers | R | R | R |
| Construct `BoundIngestPort` | R (wrong MAC vs orch) | O if class found | R if port not returned | R | R |
| Arbitrary statement on public mint | R if no persist RPC | O if hidden class still callable | O if closure takes statement | R | R if child refuses |
| Arbitrary source / timestamp | same as statement | same | same | R (adapter-owned fields) | R |
| Fake acquisition result dataclass | N (mint 0) / O if `ingest(result)` | O | O if closure takes it | **R** (`poll` only) | R if child binds adapter |
| Matching key/verifier | **R** (core close) | O if parent still copied | R | R | R |
| Extract capability from returned port | N if not returned | O if returned | O if `acquire` returned with statement | O if `poll` returned? poll is fetch not mint | A |
| Serialize / reconstruct port | A / O if reconstructed with `k` then verify switch | O | A | A | R |
| Replay grant after revise | R (existing latest-row MAC) | R | R | R | R |
| Module global issuer | R if none | R | R | R | R |
| Factory `secret=` / `statement=` | must not exist | O if exists | O if exists | R | R |
| Orch `ingest=`/`verifier=`/`secret=` | must not add | must not add | must not add | must not add | must not add |
| Direct SQLite OF | R (existing) | R | R | R | R |
| N-hop from ungranted OF | R (existing) | R | R | R | R |

**Minimum that actually closes C1:** **A with verifier pin** (ignore parent contextvar; never take `key=` from public bind/run).  
**Required for a future production mint:** **D** (`poll` / fetch, not `ingest(result=)` / `statement=`).  
**B/C alone:** insufficient or superficial.  
**E:** stronger, not minimum.

---

## 6. Selected V4 architecture (minimum safe)

**Name:** V4-PIN — instance-pinned verifier + no caller verify context + poll-only future mint + tests-only compose.

Not E. Not orch kwargs. Not `__all__`. Not filename checks.

### 6.1 Production-valid credential

```text
FACTUAL_PREMISE
  ⇐ latest OBSERVED_FACT row
  ⇐ ObservationGrant MAC
  ⇐ hmac(orch._grant_verify_secret, canonical(latest fields))
  ⇐ issuer_id == production ISSUER_ID
  ⇐ trusted episode now from run(now=) | time.time()
  ⇐ not STALE/SUPERSEDED/ARCHIVED, observed_at ≤ now, valid_until
```

`orch._grant_verify_secret` is created in `CognitiveOrchestrator.__init__` via `os.urandom(32)` (keep test-vector denylist). No public getter, setter, or constructor kwarg.

### 6.2 Close the join (the actual C1 fix)

```text
CognitiveOrchestrator.run
      MUST NOT read current_grant_verify_context() to choose the key
      MUST always verify with self._grant_verify_secret + ISSUER_ID
      MAY pass trusted_now=ts into bind as now= (already does)
```

`push_grant_verify_context` must **not** be a production API that bind honors for **keys**. Options (implementation later, pick one):

- Delete it from `architecture/` and pass `(key, issuer, now)` only as internals of `run` → `reason` → `bind_context` **without** a public `key=` on those functions; **or**
- Keep a contextvar **set only inside `run` from instance secret**, never copied from parent.

Public `verify_observation_grant(..., key=)` if it remains must not be on the `run` path. Ordinary callers invoking it cannot assign `FACTUAL_PREMISE` roles; only `bind_item` can. `bind_item` must not take `key=` / `verifier=` / `secret=`.

### 6.3 BoundIngestPort / ObservationAuthority

After 6.2, `BoundIngestPort(ObservationAuthority(secret=k)).persist_acquired(AcquisitionRecord(statement=…))` produces a row whose MAC **does not** match `orch._grant_verify_secret`. Bind rejects. That is the same shape as today’s alien-port test, **without** the missing contextvar join.

Residual: the classes remain constructible (**ordinary API**). That does **not** manufacture **production** authority. Removing them from the module is optional hygiene, not the security core. A future production mint must **not** be `persist_acquired(AcquisitionRecord)` on a type ordinary code can construct **and** that uses the orchestrator secret. It must be a non-exported closure held only by a designated adapter object that ordinary `run()` callers never receive.

Until that adapter exists, **production mint count stays 0** (current corpus/eval/benchmark `remember()` without grant — keep).

### 6.4 Fake acquisition substitution

Do not add `ingest(TypedResult)`. When an adapter is added, public methods are fetch/poll/subscribe on the adapter instance owned by the composition root. Caller-built dataclasses are not inputs to mint.

Tests: `TypedFakeAcquisitionResult` stays in `tests/`. Production must not import it.

### 6.5 CognitiveOrchestrator constructor

Unchanged public kwargs: `memory`, `hypotheses`, `ledger_path`, `retriever`.  
**Do not** add `ingest=`, `verifier=`, `secret=`, `grant_key=`.

### 6.6 Clock

Unchanged: `_trusted_now` ignores `task.created_at`; `run(now=)` is the episode freeze. Do not put the **key** in that freeze mechanism.

### 6.7 Hybrid-D consumption

Keep latest-row load, canonical recompute, MAC, revision/supersession grant strip, SQLite ≠ FACTUAL, DERIVED_FACT kind check, write-back `reusable_writeback_permitted`.

### 6.8 Tests-only composition (must model the boundary)

Today tests mint with `TEST_VECTOR_KEY` and then `grant_verify_scope` so **production** `run()` adopts that key. That **is** the C1 pattern. V4 tests must not use it against `CognitiveOrchestrator`.

```text
tests/observation_test_runtime.py
    TestCognitiveOrchestrator(CognitiveOrchestrator)
        after super().__init__, set instance verify material to TEST_VECTOR_KEY
        + ISSUER_ID_TEST
        (underscore assignment in tests-only subclass — not a production ctor kwarg)
    TestAcquisitionAdapter mints with the same TEST_VECTOR_KEY
    no push_grant_verify_context into production run()
```

Ordinary attackers can also subclass and assign `_grant_verify_secret`. That produces a **different instance**. It does not rekey the composition-root instance. Reading/writing another object’s underscore secret remains the ACE class already out of scope (prior audit: extracting `orch._grant_verify_secret`).

Positive FACTUAL tests construct `TestCognitiveOrchestrator`, not `grant_verify_scope` + production `CognitiveOrchestrator`.

Layer 4 independent tests must not import mint helpers; they call production `CognitiveOrchestrator` + `remember`/sqlite and expect non-FACTUAL.

Denylist of the test-vector SHA-256 on production issuer remains.

---

## 7. Why this is not a superficial fix

| Rejected move | Why V4-PIN is different |
| --- | --- |
| Rename / `_` / `__all__` / other module | Verifier still would accept caller `k` |
| `secret == production _SECRET` check | Attacker never uses production secret; they install `k` |
| Add orch `secret=` / `verifier=` | **Re-opens** matching pair as public constructor |
| tests/ path as boundary | Production `run` must not honor test contextvar at all |
| Hide `BoundIngestPort` only | `mac_hex(k, bytes)` still forges grant JSON if verifier is switchable |

The closed capability is: **install a caller key as the production episode verifier**, and **have mint under that same key accepted as FACTUAL**.

---

## 8. Future implementation scope (do not implement now)

| Area | Change |
| --- | --- |
| `architecture/cognitive/loop/orchestrator.py` | `run()`: never copy parent `GrantVerifyContext.key` / `issuer_id`. Always instance secret + `ISSUER_ID`. Keep `now=ts` into `reason`/`bind_context`. |
| `architecture/cognitive/memory/observation.py` | Stop using caller-set contextvar as verify **key**. Keep HMAC helpers. No new persist RPC. Optional: stop exporting `push_grant_verify_context` as a key-install API. |
| `architecture/cognitive/loop/binding.py` | Verify key only from orchestrator-supplied internal path / `now=` already passed. No public `key=`. Keep `_trusted_now` ignoring `created_at`. |
| `architecture/cognitive/loop/reason.py` | Keep `now=` pass-through. No authority kwargs. |
| Adapters / corpus / eval / benchmark | Remain non-minting until a poll-only adapter is a later, separately authorized design. |
| `tests/observation_test_runtime.py` | `TestCognitiveOrchestrator`; mint with test key; **remove** production `run()` dependence on `grant_verify_scope`. |
| `tests/p5_grant_fixtures.py` | Compose through test orchestrator; `persist_authorized(statement=)` stays tests-only and must not be importable by `architecture/`. |
| `tests/test_p5_v3_authority_boundary.py` | Add explicit C1 replay: `BoundIngestPort` + `push_grant_verify_context` + production `CognitiveOrchestrator.run` → **not** FACTUAL. Do not use mint helper for that case. |
| Other P5 tests | Switch `CognitiveOrchestrator` + `grant_verify_scope` to `TestCognitiveOrchestrator`. |
| Lane A / soak / schema | Untouched. |
| Migration | Existing granted rows minted under vanished process secrets are already unverifiable across process restart (current `os.urandom` per instance). No schema migration. Test DBs are ephemeral. |

Composition root (production app, later): construct `CognitiveOrchestrator`; do not return mint ports; do not call `push_grant_verify_context` with a non-instance key.

---

## 9. Residual limitations (honest)

- Same-process Python can still build HMAC bytes with a random key. Those bytes are not production credentials after verifier pin.
- Assigning `production_orch._grant_verify_secret = k` on a **held instance** is ACE-shaped (underscore instance field), same class as reading it; out of threat model. Do not add a public setter.
- `run(now=)` remains a public episode clock freeze (not `created_at`).
- Production still cannot autonomously acquire provider truth (mint 0).
- Nested-class / closure hiding is **not** relied on as the security core.

If a later change reintroduces parent-key copy, `secret=` on `run`/`__init__`, or `persist(statement=)` using the instance secret, C1 returns. Then E (child process) becomes the next minimum.

---

## 10. Final status

```text
V4_ARCHITECTURE = VALID
V4_SECURITY_REVIEW = PASS
AUTHORITY_CONSTRUCTION_BOUNDARY = CLOSED
GRANT_ISSUANCE_AUTHORITY = CLOSED
ARBITRARY_GRANT_MINTING = BLOCKED
BOUND_INGEST_CAPABILITY_BOUNDARY = CLOSED
ACQUISITION_ADAPTER_BOUNDARY = CLOSED
VERIFICATION_CONTEXT_AUTHORITY = TRUSTED
ORCHESTRATOR_AUTHORITY_INJECTION = BLOCKED
FAKE_ACQUISITION_SUBSTITUTION = BLOCKED
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
LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED
PRODUCTION_CODE_MODIFIED = NO
TEST_CODE_MODIFIED = NO
IMPLEMENTATION_AUTHORIZED = NO
MERGE = NO
READY_FOR_REVIEW = NO
REPORT = reports/agi_aci_evolution/P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md
```

Status tokens above are **design claims for unimplemented V4**, not claims about tree `24b2ab8`. Tree `24b2ab8` remains `GRANT_ISSUANCE_AUTHORITY = OPEN` until V4 is implemented and independently audited.

STOP.
