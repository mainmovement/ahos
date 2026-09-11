# P5 V4 — authority construction boundary (pre-implementation security gate)

**Kind:** Read-only security gate of the V4-PIN design against the live tree. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Implementation baseline:** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**HEAD at analysis:** `7f26372da51205cc5d5d07115c20d0cc728240b0` (report-only after baseline).  
**Prior independent audit:** `reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` (`FORENSIC_STATUS = FAIL`)  
**This document does not authorize implementation.**

Not AGI. Not ACI. Not production-ready. Not live trading.  
Lane A and soak are not in scope. This turn does not modify production code, tests, schemas, Lane A, or soak.

Proof language:

- **PROVEN** — observed in tree `24b2ab8` (and unchanged in later report-only commits)
- **DESIGN** — required V4-PIN contract (unimplemented)
- **GATE** — whether that contract is precise enough to implement later

---

## 1. Executive conclusion

**Current tree:** a legitimate production `CognitiveOrchestrator` instance **can** be made to treat attacker-created evidence as `FACTUAL_PREMISE`. The join is ordinary import + constructors + `push_grant_verify_context` + `run()` copying the parent ContextVar key. That is **PROVEN**. `V4 IMPLEMENTATION = NOT PRESENT`.

**Prior V4 write-up (same filename, architecture-only):** conceptually aimed at the right invariant (instance-pinned verifier) but was **not** implementable as written. It offered two optional ContextVar strategies, one of which (`run()` still places `HMAC_SECRET(O)` in a ContextVar that collaborators can read or overwrite) **fails** Attacks C, D, and DI (`retriever=` / `memory=`).

**This gate:** V4-PIN is **sufficient** under the stated threat model **if and only if** implementation follows the **single** contract in §3 and §12, not the earlier optional fork.

Minimum architecture remains **same-process V4-PIN** (not Option E). Option E is stronger, not required, provided the secret never enters a caller-writable ContextVar and `run()` never copies parent key/issuer.

Central question:

> Can a caller-controlled key, issuer, verifier, context, authority object, acquisition object, or persistence path cause a legitimate production `CognitiveOrchestrator` instance `O` to accept attacker-created evidence as a `FACTUAL_PREMISE`?

| State | Answer |
| --- | --- |
| Tree `24b2ab8` | **YES (PROVEN)** |
| V4-PIN as specified in this gate | **NO (DESIGN)**, if every §12 precondition is implemented |
| V4-PIN if `run()` still copies parent context or still puts `O.secret` in a ContextVar | **YES — design fails** |

`IMPLEMENTATION_AUTHORIZED = NO`. Independent review of this report is required before any implementation turn.

---

## 2. Current-tree status

| Ref | Value |
| --- | --- |
| Mandated implementation SHA | `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83` |
| Current `HEAD` | recorded at report write; must be `24b2ab8` plus **report-only** commits |
| Delta `24b2ab8..HEAD` (code) | **empty** — no `*.py`, schema, Lane A, or soak |
| Files after baseline | `P5_V3_IMPLEMENTATION_REPORT.md`, `P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`, this report |
| PR #93 | **DRAFT**; base `main`; head `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| Lane A `discovery/**`, `paper_trading/**` vs `24b2ab8` | **UNTOUCHED** |
| Soak vs `24b2ab8` | **UNTOUCHED** |
| `persist_observed_acquisition` / `_process_authority` | **absent** |
| Production mint sites (`BoundIngestPort(` in `architecture/` besides the class) | **none** — mint count **0** on production call paths |
| Named ctor DI `ingest=` / `verifier=` / `secret=` | **rejected** (`TypeError`) — **PROVEN**, insufficient |

Security analysis below is of **`24b2ab8` behavior**. Report-only HEAD does not substitute another implementation SHA.

### 2.1 Proven production acceptance failure (tree)

Ordinary importer, **without** reading `O._grant_verify_secret`:

```text
k = os.urandom(32)
ObservationAuthority(secret=k, issuer_id=ISSUER_ID)
BoundIngestPort(authority).persist_acquired(store, AcquisitionRecord(statement=…, …))
push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, now))
O.run(task, now=now)   # O is a legitimate CognitiveOrchestrator
```

`run()` **PROVEN** (`architecture/cognitive/loop/orchestrator.py`):

```text
parent = current_grant_verify_context()
if parent is not None:
    verify_ctx = GrantVerifyContext(parent.key, parent.issuer_id, float(ts))
else:
    verify_ctx = GrantVerifyContext(self._grant_verify_secret, ISSUER_ID, float(ts))
token = push_grant_verify_context(verify_ctx)
try:
    return self._run_with_episode_clock(...)
finally:
    reset_grant_verify_context(token)
```

Bind then verifies with the ContextVar key (`verify_observation_grant`: `use_key = key or ctx.key`). Attacker `(k, ISSUER_ID)` becomes `FACTUAL_PREMISE` when other support gates pass.

This is ordinary API composition. In scope.

---

## 3. V4-PIN formal invariant

For a live production instance `O = CognitiveOrchestrator(...)`:

```text
HMAC_SECRET(O)     := bytes produced in O.__init__ by os.urandom(32)
                      (retry if SHA-256 ∈ test-vector denylist)
PRODUCTION_ISSUER  := module constant ISSUER_ID = "ahos.observation_authority"
ProductionVerifier(O) := (HMAC_SECRET(O), PRODUCTION_ISSUER)
```

Constraints on `HMAC_SECRET(O)`:

| Must | Must not |
| --- | --- |
| Generated inside `O.__init__` | Be a `__init__` / `run` argument (`secret=`, `verifier=`, `ingest=`, `authority=`, `issuer=`, `grant_verify_context=`, aliases) |
| Remain instance-local | Be copied from parent ContextVar |
| Be used for every production `FACTUAL_PREMISE` HMAC | Be selected by the evidence item, grant JSON, or caller `ObservationAuthority` |
| | Be placed in any ContextVar, `GrantVerifyContext.key`, or other object readable/writable by caller-supplied `retriever` / `memory` / `hypotheses` |
| | Be returned by `current_grant_verify_context()` |

### 3.1 Production acceptance rule

An `OBSERVED_FACT` row may become `FACTUAL_PREMISE` **inside `O.run()`** only if:

```text
Verify(
    grant              = latest_row.payload["observation_grant"],
    canonical          = canonical_observation_bytes(latest_row fields),
    key                = HMAC_SECRET(O),
    expected_issuer_id = PRODUCTION_ISSUER,
    trusted_now        = episode ts from run(now=) or time.time(),
    extra              = existing kind/temporal/entity/scope/polarity/status gates
) == PASS
```

A caller-created key is cryptographically irrelevant: `HMAC(k, canonical) ≠ HMAC(HMAC_SECRET(O), canonical)` except with negligible probability.

`CognitiveTask.created_at` is **not** `trusted_now` (**PROVEN** today; preserve).

### 3.2 What “production-valid” is not

Not: caller `issuer_id`, caller `GrantVerifyContext`, caller `ObservationAuthority` identity, package `__all__`, leading underscores, tests/ path, or a boolean `permits()` callback the caller can install.

### 3.3 Single implementation shape (not optional)

The previous report allowed either (a) delete ContextVar keys or (b) set ContextVar from `O.secret` inside `run()`. **(b) is REJECTED by this gate.**

Reason (**DESIGN attack, current code already exhibits the surfaces**):

1. `retriever=` is a public `CognitiveOrchestrator.__init__` argument (**PROVEN**). Threat model includes dependency injection.
2. `memory=` is a public store collaborator. `bind_item` calls `store.get`.
3. `run()` currently pushes a `GrantVerifyContext` **containing the key**, then calls `retriever.retrieve` **before** bind (**PROVEN** order).
4. `push_grant_verify_context` is a public setter of that ContextVar (**PROVEN**).
5. Therefore a caller-supplied retriever can `push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, ts))` during `retrieve()` and **rekey the episode** even if `run()` stopped copying the *parent* context.
6. `current_grant_verify_context()` would also **leak** `HMAC_SECRET(O)` to that retriever if `run()` pushed the instance secret.

**Required shape:**

```text
trusted composition root
        ↓
O = CognitiveOrchestrator(memory, hypotheses, ledger_path, retriever?)
        ↓  HMAC_SECRET(O) stays a Python local / instance field
O.run()
        ↓  instance method / nested call stack (not ContextVar, not public key=)
bind + reason using HMAC_SECRET(O) + ISSUER_ID + episode ts
        ↓
FACTUAL_PREMISE only if Verify(..., O.secret, ISSUER_ID, ts)
```

Public `reason()` / `bind_item()` / `bind_context()` **must not** accept `key=` / `secret=` / `verifier=` and **must ignore** ContextVar **keys**. Without the instance stack, `grant_ok = False`.

ContextVar may carry **clock metadata only** (`trusted_now`), and even that is redundant when `now=` is already passed. It must **never select production authority**.

---

## 4. Complete authority graph (tree `24b2ab8`)

External acquisition → production mint is **unwired** (count 0). The **open** mint is the importable class, not a designated adapter.

```text
[ordinary importer]
    ObservationAuthority.__init__(secret=k, issuer_id=…)     observation.py
        → HMAC issuer object                                 MINT-capable
    BoundIngestPort.__init__(authority)                      observation.py
        → persist_acquired(store, AcquisitionRecord)         MINT RPC
            → ObservationAuthority._mint                     HMAC grant
            → store.remember(payload.observation_grant=…)    row + JSON

    mac_hex(k, canonical) + ObservationGrant(...)            forge grant JSON
    GrantVerifyContext(k, issuer, now)                       verify material
    push_grant_verify_context(ctx)                           ContextVar SET
    current_grant_verify_context()                           ContextVar GET
    verify_observation_grant(..., key=? )                    CONSUME
    observation_grant_permits_factual(...)                   CONSUME

[composition: whoever constructs O]
    CognitiveOrchestrator.__init__
        kwargs: memory, hypotheses, ledger_path, retriever
        os.urandom → O._grant_verify_secret                  VERIFY OWNER
    CognitiveOrchestrator.run
        COPY parent key/issuer if ContextVar set             VERIFY SWITCH (OPEN)
        push GrantVerifyContext(key, issuer, ts)
        retriever.retrieve(...)                              DI window (OPEN)
        reason(..., now=ts) → bind_context → bind_item
            observation_grant_permits_factual (ctx.key)
            _roles(..., grant_ok) → FACTUAL_PREMISE
        verdict / critique / reusable_writeback_permitted
        remember() HYPOTHESIS / LESSON / INFERENCE / episode (no OF grant)

[public persist without mint]
    store.remember / sqlite INSERT / ingest_generic_observation
    record_world_model_object (refuses OBSERVED_FACT)
    IngestPort.persist_acquired → RuntimeError

[tests-only]
    TestAcquisitionAdapter → BoundIngestPort(TEST_VECTOR_KEY, ISSUER_ID_TEST)
    grant_verify_scope → push_grant_verify_context(TEST_VECTOR_KEY, …)
    production CognitiveOrchestrator.run under that scope     SAME JOIN AS C1
```

| Who | File | Symbol | Input | Output | Authority level |
| --- | --- | --- | --- | --- | --- |
| Ordinary caller | `observation.py` | `ObservationAuthority.__init__` | caller `secret`, `issuer_id` | issuer | **MINT-capable** |
| Ordinary caller | `observation.py` | `BoundIngestPort.persist_acquired` | `AcquisitionRecord` (free-form statement/source/time/domain) | granted row | **MINT** |
| Ordinary caller | `observation.py` | `push_grant_verify_context` | `GrantVerifyContext` | ContextVar | **VERIFIER INJECTION** |
| Ordinary caller | `observation.py` | `verify_observation_grant(..., key=)` | caller key | bool | verify oracle; not role assignment by itself |
| Ordinary caller | `orchestrator.py` | `CognitiveOrchestrator.__init__` | store/hyp/ledger/retriever | `O` | owns secret; **no mint** |
| Ordinary caller | `orchestrator.py` | `run` | task, `now=` | `CognitiveResult` | **VERIFY SWITCH** if parent set |
| Bind | `binding.py` | `bind_item` | retrieved item, `now=` | `EvidenceBinding` | **CONSUME** via ContextVar |
| Bind | `binding.py` | `EvidenceBinding.live_grant_ok` / `may` | frozen snapshot + ContextVar | roles | **CONSUME again** |
| Reason | `reason.py` | `reason` | context, `now=` | verdict | uses bind roles |
| Writeback | `orchestrator.py` / `episode.py` | `reusable_writeback_permitted` | bindings | lesson/hyp persist | requires FACTUAL supporters |
| Tests | `tests/observation_test_runtime.py` | `grant_verify_scope` | test key | ContextVar | **same injection as C1** |
| Production adapters | `adapters.py` | `ingest_generic_observation` | refuses `OBSERVED_FACT` | ungranted other kinds | no mint |

Ordinary Python can: construct authority/port/record; choose HMAC secret and issuer; mint; replace verification context; pass objects; influence which key **and** issuer `run()` uses (parent copy); influence `FACTUAL_PREMISE` via that join.

Leading underscores, `__all__`, comments, and `tests/` location are not boundaries.

---

## 5. Trust-root analysis

| Root | Origin today (PROVEN) | V4 required (DESIGN) | Class |
| --- | --- | --- | --- |
| Production HMAC secret | `O.__init__` `os.urandom`, then **abandoned if parent ContextVar set** | `O.__init__` `os.urandom` only; used on every production verify | composition-root / instance |
| Production issuer | `ISSUER_ID` **or parent.issuer_id** | always `ISSUER_ID` on production `O.run` bind path | application constant |
| Trusted clock | `run(now=)` else `time.time()`; `_trusted_now` ignores `task.created_at`; ContextVar `trusted_now` fallback | preserve; do not put **keys** in that fallback | runtime / caller episode freeze (`now=` residual) |
| Acquisition capability | importable `BoundIngestPort` + `AcquisitionRecord` | production mint 0 until poll-only adapter owned by root, minting under `HMAC_SECRET(O)` without `statement=` RPC | today: caller-controlled mint class; V4: composition-root-only, unwired |
| Verification context | process ContextVar, public push/get | must not select key/issuer; production verify is stack-local to `O` | today: **caller-controlled**; V4: **composition-root-controlled** |

There is **not** one authoritative production verifier root on the current tree: instance secret **and** ContextVar parent are equivalent roots. That is why V4 is not closed **in the tree**.

V4 must leave **exactly one** production verifier root: `ProductionVerifier(O)`.

Cross-instance: `HMAC_SECRET(O1) ≠ HMAC_SECRET(O2)` (independent `os.urandom`). A grant minted under `O1` must not verify under `O2`. True today **only when** ContextVar is empty; **false** when a shared parent context is copied into both. V4 must make it **always** true.

---

## 6. Attack matrix A–K

Cells: **TREE** = `24b2ab8`. **V4** = this gate’s contract if implemented.  
OPEN = production `O.run()` can yield `FACTUAL_PREMISE` for attacker evidence.  
BLOCKED = cannot. ACE = out of threat model (debugger / `gc` / `__closure__` / assigning `O._grant_verify_secret` on a held production instance).

| Attack | TREE | V4-PIN (this contract) | Why V4 |
| --- | --- | --- | --- |
| **A** `ObservationAuthority(secret=k)` | OPEN (with D) | BLOCKED as production-valid | MAC under `k` ≠ `HMAC_SECRET(O)` |
| **B** `BoundIngestPort(ObservationAuthority(k))` | OPEN (with D) | BLOCKED as production-valid | same; persist still exists as a class but grant is alien |
| **C** Parent ContextVar contamination | **OPEN (PROVEN)** | BLOCKED | `run()` must **not** copy parent key/issuer; bind must **not** read ContextVar keys |
| **D** `push_grant_verify_context(k, issuer)` | **OPEN (PROVEN)** | BLOCKED | production bind ignores ContextVar keys; DI overwrite of ContextVar cannot rekey `O` |
| **E** ctor `secret=`/`verifier=`/`ingest=`/`authority=`/`issuer=`/`grant_verify_context=` | BLOCKED today | BLOCKED | do not add kwargs |
| **F** look-alike verifier/authority object passed in | OPEN via ContextVar, not via ctor | BLOCKED | no object identity check needed if HMAC key cannot be switched; class names irrelevant |
| **G** `TypedFakeAcquisitionResult` / `AcquisitionRecord` | OPEN via B | BLOCKED for production `O` | dataclass forgery is ordinary; production mint must not accept caller dataclasses; until adapter exists, mint 0 |
| **H** sqlite / `remember` / generic ingest / world-model / revise | BLOCKED for FACTUAL without matching MAC | BLOCKED | preserve latest-row MAC; ingest/world-model refuse OF mint |
| **I** `issuer_id = attacker` | OPEN if parent issuer copied | BLOCKED | production expected issuer is `ISSUER_ID`, not parent |
| **J** `O._grant_verify_secret = k` via public API | no setter, no ctor | no setter, no ctor | direct attribute write on held `O` is ACE-shaped (same as reading the secret); not a supported API |
| **K** nested attacker `O_att` + authority + port + context → production `O` | OPEN if shared ContextVar copied into `O.run` | BLOCKED | `O` verifies only `HMAC_SECRET(O)`; attacker graph is a different instance |

### Attack A — caller-created authority

**TREE:** YES, after Attack D.  
**V4 expected NO:** constructing `ObservationAuthority` does not install `k` as `ProductionVerifier(O)`. The object can still HMAC bytes; those bytes are not a production credential.

### Attack B — caller-created BoundIngestPort

**TREE:** YES, after Attack D. The port is a statement RPC (`AcquisitionRecord.statement` is a constructor field).  
**V4 expected NO:** the row is stored; bind HMAC fails under `O.secret`. Remaining constructibility is not production authority.

### Attack C — parent context contamination

**TREE: YES (PROVEN).** `run()` copies `parent.key` and `parent.issuer_id`.  
**V4 expected NO:** `run()` always uses `(self._grant_verify_secret, ISSUER_ID, ts)`. Nested `O2.run()` during `O1.run()` uses `O2`’s secret, not `O1`’s.

### Attack D — verification-context replacement

**TREE: YES (PROVEN).** Public `push_grant_verify_context`.  
**V4 expected NO.** If implementation still honors ContextVar **keys** inside `bind_item` / `live_grant_ok` / `verify_observation_grant` on the `O.run` path, **classify V4 as FAILED** — including overwrite from `retriever.retrieve` after `run()`’s own push.

Public `verify_observation_grant(key=k)` may remain as a pure function. It must not be on the `O.run` bind path and cannot assign roles by itself.

### Attack E — constructor injection

**TREE: NO** for those kwargs (`inspect.signature` + TypeError tests). `retriever=` and `memory=` **are** public and are the DI window for Attack D unless ContextVar keys die.  
**V4:** do not add authority kwargs. Treat `retriever=`/`memory=` as hostile for secret leakage.

### Attack F — object substitution

Not naming: any object that causes `verify_observation_grant` to use `k` is a verifier. Today that object is `GrantVerifyContext` in a ContextVar, not a class name. V4: no such substitution channel into `O.run()`.

### Attack G — fake acquisition result

Do not ask only whether the dataclass instantiates. Path:

```text
TypedFakeAcquisitionResult.raw_reading
    → TestAcquisitionAdapter.acquire
    → AcquisitionRecord(statement=raw_reading)
    → BoundIngestPort.persist_acquired
    → grant under TEST_VECTOR_KEY
    → grant_verify_scope
    → production O.run   # TREE: production-valid under copied context
```

Production `architecture/` does not import `TypedFakeAcquisitionResult`. Ordinary callers instead build `AcquisitionRecord` and `BoundIngestPort` directly (same mint).

**V4:** no production function `ingest(result: Typed*)`. Future adapter public API is poll/fetch with **no result argument**. Tests mint only under `TestCognitiveOrchestrator`’s instance secret (test vector), never by pushing that vector into production `CognitiveOrchestrator.run`.

### Attack H — persistence shortcut

**TREE: BLOCKED** for ungranted OF (remember, sqlite, generic ingest, world-model). Latest-row canonical MAC still required. Revision/supersede pops `observation_grant` on statement change / successor.  
**V4:** preserve. Ungranted or alien-MAC rows stay non-FACTUAL.

### Attack I — issuer substitution

**TREE:** parent `issuer_id` copied; attacker can mint with that issuer and matching `k`.  
**V4:** production expected issuer is `ISSUER_ID`. Grant `issuer_id != ISSUER_ID` fails even if MAC matches some other key. Test issuer `ISSUER_ID_TEST` must not be accepted by production `O`.

### Attack J — key substitution on `O`

No public setter or ctor. `run()` does not assign `self._grant_verify_secret` from arguments.  
Ordinary `O._grant_verify_secret = k` requires a held instance and ignores the leading underscore; classified **ACE / held composition-root**, same class as reading the field. Do not add a getter/setter.

Subclass that assigns the field is a **different instance** (Attack K), not rekeying the composition-root object.

### Attack K — nested attacker graph

Attacker `O_att` has its own `os.urandom` secret. Grants valid for `O_att.run()` must fail `O.run()` after pin. Shared ContextVar is the cross-instance bridge **today**. Remove it as a key channel.

---

## 7. ContextVar analysis

| Operation | Today | V4 |
| --- | --- | --- |
| Create | `ContextVar("ahos_og_verify", default=None)` | must not hold `key` / issuer-as-authority |
| Public set | `push_grant_verify_context` | must not change `ProductionVerifier(O)` |
| Public get | `current_grant_verify_context()` returns `.key` | must not return HMAC secret |
| Inheritance | `run()` **copies parent key/issuer**, keeps episode `ts` | **forbidden** for key/issuer |
| Nested `run()` | inner copies outer key | each instance uses **its** secret |
| `try/finally` reset | **PROVEN** on `run()` | keep for any remaining clock token |
| Async task copy | `run` is sync; ContextVar copies into asyncio tasks if created during `run` | irrelevant if secret is not in the ContextVar |
| Threads | ContextVar is per-thread; another thread does not see the token | do not use ContextVar as the authority bus |
| Retriever/store during `run` | can get/set ContextVar | cannot select HMAC key |

**Design rule:** Context may carry execution metadata (episode `ts` is already a `now=` argument). It must never select production authority.

`_trusted_now`: `now=` wins; else ContextVar `trusted_now`; never `task.created_at`. V4: production `O.run` always passes `now=ts` into `reason`/`bind_context` (**already PROVEN**). Public bind without `now=` stays fail-closed for grants (`trusted_now is None` → `grant_ok False`).

---

## 8. Instance-lifetime analysis

| Question | Tree | V4 |
| --- | --- | --- |
| When generated? | `O.__init__` | same |
| Lifetime? | process lifetime of `O` | same |
| Replaced? | not via public API; **functionally replaced** by parent context at `run()` | never replaced; context cannot override |
| Copied into ContextVar? | **YES every `run()`** | **NO** |
| Child components receive secret? | yes, via ContextVar (`reason`/`bind`/`live_grant_ok`) | only as stack locals inside `O`’s episode methods; not on `EvidenceBinding`; not on `CognitiveResult` |
| Public getter? | no | no |
| `O1` grant valid for `O2`? | no if both have empty parent; **yes** if shared parent context | **no** |

Process restart: new `os.urandom` → prior grants unverifiable. Already true. No schema migration.

Do not serialize `O._grant_verify_secret`. Do not put it on frozen bindings (DTO leak to result consumers who did not construct `O`… callers of `run()` already hold `O`; still do not put the secret on exported DTOs).

---

## 9. Test architecture (coherence only)

Today, positive FACTUAL tests do:

```text
grant_verify_scope(TEST_VECTOR_KEY, ISSUER_ID_TEST)
    + production CognitiveOrchestrator.run()
```

That **is** Attack C/D. Tests must not keep that bypass.

Coherent V4 test model (**DESIGN**, not implemented):

| Piece | Location | Rule |
| --- | --- | --- |
| Test secret | `tests/observation_test_runtime.py` `TEST_VECTOR_KEY` | denylist SHA-256 remains in production; production issuer cannot use it |
| Test issuer | `ISSUER_ID_TEST` | production `O` must not accept it |
| `TestCognitiveOrchestrator` | `tests/` only | `super().__init__` then set **instance** verify material to test key + test issuer; **not** a production ctor kwarg |
| Test acquisition | `TypedFakeAcquisitionResult` + `TestAcquisitionAdapter` | mint under test key; production must not import |
| Production `CognitiveOrchestrator` in Layer 4 | `tests/test_p5_v3_authority_boundary.py` | C1 replay: BoundIngestPort + `push_grant_verify_context` + production `run()` → **not** FACTUAL; do not import mint helpers for that case |
| `grant_verify_scope` | tests only | must **not** wrap production `CognitiveOrchestrator.run` |

Subclass assignment of `_grant_verify_secret` in tests models the instance pin; it does not rekey a production instance the test did not construct.

`persist_authorized(statement=)` in `tests/p5_grant_fixtures.py` remains tests-only. `architecture/` must not import it.

Production secret is not a module global and is not imported by tests. A test that reads `orch._grant_verify_secret` on an orchestrator **it constructed** is reading that instance’s urandom, not a shared production key file. Keep that out of Layer 4 mint tests.

---

## 10. V4-PIN vs Option E (separate local issuer process)

| | V4-PIN (stack-local instance secret) | Option E |
| --- | --- | --- |
| Stops caller `ObservationAuthority(k)` from being production-valid | yes (acceptance pin) | yes (different process key) |
| Stops ContextVar join | yes if keys never in ContextVar | yes |
| Stops DI overwrite of ContextVar | yes if keys never in ContextVar | yes |
| Stops held-instance `O._grant_verify_secret = k` | no (ACE / composition root) | yes, if child process ignores app-process writes |
| Windows-first / local / $0 | yes | possible, more moving parts |
| Minimum for stated threat model | **yes** | stronger than needed |

Threat model: ordinary import, constructors, public functions, DI, composition — **not** OS compromise, debugger, or source modification.

Held-instance underscore assignment is the same privilege as owning `O`. Option E is **not** selected merely because it is stronger.

If implementation reintroduces parent-key copy, `secret=` on `O`, persist RPC using `HMAC_SECRET(O)` with `statement=`, or ContextVar **keys**, then **this gate’s V4-PIN is no longer sufficient** and Option E becomes the next minimum.

---

## 11. Residual risks (honest)

1. Same-process Python can still compute HMAC with a random key (`mac_hex` is public). Irrelevant after pin.
2. Held `O._grant_verify_secret` read/write: ACE-shaped; out of scope; do not add public accessors.
3. `__closure__` / `gc` extraction of a nested verifier: ACE; V4 must not need closures as the security core — stack locals on `O` methods are enough.
4. `run(now=)` remains a public episode clock freeze (not `created_at`). Preserve; do not mix keys into it.
5. Production still cannot acquire provider truth (mint 0) until a later poll-only adapter is separately authorized.
6. Public module `reason`/`bind_item` fail-closed for grants: tests that called them under `grant_verify_scope` must move to `TestCognitiveOrchestrator`.
7. Cross-process persistence of grants: already unbound to a restarted `O`; not a new V4 issue.

Preserved properties (do not weaken): trusted runtime clock; latest-state MAC; SQLite ≠ FACTUAL; revision/supersede grant strip; DERIVED_FACT cannot use OF grant; TOCTOU via latest-row bind; N-hop from ungranted OF; write-back `reusable_writeback_permitted`; Lane A freeze; soak isolation.

---

## 12. Explicit implementation preconditions

Implementation is **not** authorized by this document. When a later turn is authorized, it is authorized **only** if it does all of the following. Any omitted item fails the gate.

### 12.1 Must change

1. `CognitiveOrchestrator.run`: **never** copy parent `GrantVerifyContext.key` or `.issuer_id`. Always verify with `self._grant_verify_secret` and `ISSUER_ID`. Keep `now=ts` into `reason`/`bind_context`. Keep `try/finally` if any token remains.
2. **Do not** place `HMAC_SECRET(O)` in a ContextVar, in `GrantVerifyContext`, or in any object `retriever` / `memory` can read or `push_grant_verify_context` can replace.
3. Production bind used by `run()` must be instance-stack (method or nested call) so the HMAC key is `self._grant_verify_secret`. Public `bind_item` / `bind_context` / `reason` signatures stay without `key=` / `secret=` / `verifier=` / `ingest=`.
4. `observation_grant_permits_factual` / `verify_observation_grant` on the production bind path must use that instance key and `ISSUER_ID`, not ContextVar keys. Public `verify_observation_grant(key=)` must not be invoked from `bind_item`.
5. `EvidenceBinding.live_grant_ok` / `may()` must not re-select a caller ContextVar key. Bind-time `grant_ok` is computed under `O.secret`; frozen snapshot fields remain the DTO-immutability source. Do not store the raw secret on `EvidenceBinding`.
6. Public `CognitiveOrchestrator.__init__` kwargs remain only `memory`, `hypotheses`, `ledger_path`, `retriever`.
7. No new persist RPC: do not restore `persist_observed_acquisition`; do not add `O.ingest(statement=)` or `ingest(TypedResult)`.
8. Tests: `TestCognitiveOrchestrator` in `tests/`; mint with test key + `ISSUER_ID_TEST`; **remove** production `run()` dependence on `grant_verify_scope`. Layer 4 C1 replay against **production** `CognitiveOrchestrator` must stay non-FACTUAL.
9. Keep test-vector SHA-256 denylist on production issuer; keep Hybrid-D consumption; keep clock rule; keep Lane A / soak / schema untouched.

### 12.2 Must not

Rename-only, `_` prefix, `__all__`, other module, filename/stack checks, extra caller tokens, `issuer_id` supplied by ordinary callers as production authority, orch authority kwargs, documenting “don’t import this.”

### 12.3 Files (future turn only)

| Area | Change |
| --- | --- |
| `architecture/cognitive/loop/orchestrator.py` | pin verifier; stack-local secret; no parent copy |
| `architecture/cognitive/memory/observation.py` | ContextVar must not be a key bus; no new mint RPC |
| `architecture/cognitive/loop/binding.py` | no ContextVar key; no public `key=`; keep `_trusted_now` ignoring `created_at` |
| `architecture/cognitive/loop/reason.py` | `now=` pass-through; no authority kwargs |
| `tests/observation_test_runtime.py` | `TestCognitiveOrchestrator`; stop wrapping production `run` |
| `tests/p5_grant_fixtures.py` | compose through test orchestrator |
| `tests/test_p5_v3_authority_boundary.py` | explicit C1: port + push + production `run` → not FACTUAL |
| Other P5 tests | switch to `TestCognitiveOrchestrator` |
| Lane A / soak / schema | untouched |
| Migration | none; process secrets already ephemeral |

---

## 13. Distinguishing design validity from the tree

| | Design (this gate) | Tree `24b2ab8` |
| --- | --- | --- |
| V4-PIN specified tightly enough to implement later? | **YES**, via §12 (not the old optional ContextVar fork) | n/a |
| Protected today? | n/a | **NO** |
| `GRANT_ISSUANCE_AUTHORITY` | CLOSED after a future implementation that passes independent audit | **OPEN** |
| Implementation present? | no | no |

Do not read the design column as a repository fix.

---

## 14. Final status matrix

**How to read this block:** `V4_ARCHITECTURE` and `V4_SECURITY_REVIEW` are the **design gate**. Every other security token is the **current tree** unless noted. OPEN/FAIL/CALLER_CONTROLLED here are **not** claims that V4 is already implemented.

```text
V4_ARCHITECTURE = VALID
V4_SECURITY_REVIEW = PASS
AUTHORITY_CONSTRUCTION_BOUNDARY = OPEN
GRANT_ISSUANCE_AUTHORITY = OPEN
ARBITRARY_GRANT_MINTING = OPEN
BOUND_INGEST_CAPABILITY_BOUNDARY = OPEN
ACQUISITION_ADAPTER_BOUNDARY = OPEN
VERIFICATION_CONTEXT_AUTHORITY = CALLER_CONTROLLED
ORCHESTRATOR_AUTHORITY_INJECTION = OPEN
FAKE_ACQUISITION_SUBSTITUTION = OPEN
TEST_AUTHORITY_SEPARATION = FAIL
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

Notes on selected tokens:

- `V4_ARCHITECTURE = VALID` means the **tightened** stack-local pin is the minimum closed design. The earlier “set ContextVar from instance secret” option is **not** valid.
- `V4_SECURITY_REVIEW = PASS` is a **design** review, not a code review of a V4 patch.
- `ORCHESTRATOR_AUTHORITY_INJECTION = OPEN` on the tree: not ctor kwargs; **ContextVar parent copy** is the injection path.
- `TEST_AUTHORITY_SEPARATION = FAIL` on the tree: `grant_verify_scope` + production `CognitiveOrchestrator`.
- `TEST_KEY_SEPARATION = PASS` on the tree: distinct test vector + test issuer + production denylist.
- Clock / MAC / sqlite / revision / DERIVED / TOCTOU / N-hop: **PROVEN preserved** on `24b2ab8`; V4 must not weaken them.

STOP.

No implementation. No production/test/schema/Lane A/soak changes. No merge. Not ready for review. Independent review of this report is required before any implementation authorization.
