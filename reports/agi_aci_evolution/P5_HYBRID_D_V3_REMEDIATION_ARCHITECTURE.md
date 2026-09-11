# P5 Hybrid-D V3 — grant issuance authority and trusted clock

**Kind:** Pre-implementation remediation architecture. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Audited implementation SHA:** `e93b3c07d83c4cebb599174fddbd7760b6a82cdd`  
**Forensic HEAD at audit:** `2bc447bb374cc956452e9b423f037f36b64d28cf`  
**Forensic result:** `FORENSIC_STATUS = FAIL` (CRITICAL=1, HIGH=1)  
**Approved family:** Hybrid-D  
**Consumption boundary retained:** bind-time ObservationGrant MAC against the **latest** canonical `OBSERVED_FACT`

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
Not AGI, ACI, entailment, production-ready, or OS-level security.

This document does **not** modify production code, tests, schemas, databases, Lane A, or soak.

`IMPLEMENTATION_AUTHORIZED = NO`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

---

## 1. Executive conclusion

Hybrid-D’s **consumption** boundary is working. HMAC verification against the latest store row is **PROVEN**. Ordinary `remember`, SQLite `INSERT` without a process MAC, revision inheritance, generic ingest, world-model FACT mint, and `DERIVED_FACT` grant reuse do **not** yield `FACTUAL_PREMISE`.

Hybrid-D’s **issuance** boundary is not. The implementation placed a production function in front of the process signer whose arguments **are** the observation:

```text
persist_observed_acquisition(store, AcquisitionRecord(statement=…, source=…, observed_at=…, domain=…))
        → IngestPort().persist_acquired
        → _process_authority()._mint
        → process-valid ObservationGrant
        → FACTUAL_PREMISE
```

That is a free-form “sign this claim” RPC. Underscore names, missing `issue()`, and absence from `__all__` are **not** a security boundary. **PROVEN** by the forensic audit.

Hybrid-D’s **temporal** decision is also not. Bind-time `now` is `CognitiveTask.created_at`. That field is caller-controlled task metadata. **PROVEN**.

**V3 does not replace Hybrid-D.** It keeps bind-time MAC verification and adds two missing authority inputs:

1. **Issuance:** only a composition-root **bound ingest capability**, used by a designated acquisition adapter that **builds** the observation from its own I/O (or a tests-only fixture), can cause a process-valid grant to be minted. No production function may accept attacker-selected observation fields and mint.
2. **Time:** factual `valid_until` / future `observed_at` checks use **episode authority time** supplied by the orchestrator/runtime clock (`time.time()` by default, already the `CognitiveOrchestrator.run` `ts`). `CognitiveTask.created_at` remains task metadata and MUST NOT be read for grant validity.

Python cannot enforce a true in-process boundary against arbitrary code in the same interpreter. V3 claims only the **ordinary application caller** threat model already used by V2 §22.

**Selected architecture: V3-A — bound ingest capability + episode clock.**  
Smallest change that closes CRITICAL and HIGH under that model. Not a separate issuer service.

`V3_ARCHITECTURE = VALID`  
`V3_SECURITY_REVIEW = PASS` under ordinary-API + forged-row-without-secret. Not ACE, not debugger, not stolen process secret.

---

## 2. CRITICAL finding reconstruction

Forensic SHA `e93b3c0`. Probe and code path:

```text
ordinary in-process caller
        ↓
from architecture.cognitive.memory.observation import (
    persist_observed_acquisition, AcquisitionRecord, IngestPort, _process_authority,
)
        ↓
persist_observed_acquisition(store, AcquisitionRecord(statement=<arbitrary SUPPORT>, …))
        ↓
IngestPort.persist_acquired          # new IngestPort(); uses process singleton
        ↓
_process_authority()._mint           # os.urandom(32) process secret
        ↓
payload.observation_grant.mac        # HMAC-SHA256 over canonical bytes
        ↓
store.remember(epistemic_kind=OBSERVED_FACT)
        ↓
fresh retrieve → bind_item → verify_observation_grant
        ↓
FACTUAL_PREMISE = True
        ↓
WEAKLY_SUPPORTED
        ↓
reusable_writeback_permitted = True → HYPOTHESIS
```

Also **PROVEN**:

- `IngestPort().persist_acquired` mints under the **process** secret, not a new `ObservationAuthority()`.
- `_process_authority()._secret` is readable (`bytes`, length 32).
- `_process_authority()._mint(acq)` returns a 64-hex MAC.
- `ObservationAuthority()` **without** that secret produces a different key; those MACs fail process verify (this part matches V2).
- `test_no_public_issue_or_grant_mint_export` only checks `__all__` and `hasattr(..., "issue")`. It never attacks persist. `ARBITRARY_GRANT_MINTING = BLOCKED` is **DISPROVEN**.

V2 required: mint is a **closure** on the composition-root Authority; adapters receive an injected `IngestPort`; `AcquisitionRecord` is built by the adapter from **its** acquisition; tests-only `TestIngestPort`; not a sign-this-claim RPC.

The implementation exported the RPC and used it from production modules (`corpus.py`, `evaluator.py`, `p5_eval.py`, `loop/benchmark.py`) and from `tests/p5_grant_fixtures.py`.

---

## 3. HIGH finding reconstruction

`architecture/cognitive/loop/binding.py` `bind_item`:

```text
now = float(task.created_at) if task.created_at else 0.0
grant_ok = observation_grant_permits_factual(..., now=now)
```

`EvidenceBinding.live_grant_ok()` repeats `self.task_created_at`.

`CognitiveOrchestrator.run(now=…)` computes `ts` for retrieve, context, write-back timestamps, and `reason()` — but `reason()` → `bind_context(ctx, task, store=store)` does **not** receive `ts`. Grant time is task metadata.

**PROVEN:**

| Manipulation | Result |
| --- | --- |
| Expired grant + `task.created_at = NOW-100` | `FACTUAL_PREMISE` + `WEAKLY_SUPPORTED` |
| Future `observed_at` + `task.created_at = NOW+6000` | `FACTUAL_PREMISE` + `WEAKLY_SUPPORTED` |
| Expired grant + `orch.run(now=far_future)` with `created_at=NOW` | still **not** FACTUAL (orchestrator `now` is unused for grants) |

`CognitiveTask.created_at` defaults to `time.time` at construction and is a public field. Any ordinary caller of `CognitiveOrchestrator.run(task)` can set it.

---

## 4. Complete grant issuance call graph

Classifications are behavioral, not names.

**UNTRUSTED** — ordinary caller may invoke with attacker-selected data.  
**VALIDATED** — enum/non-empty/UNKNOWN checks; not authorization.  
**TRUSTED** — designated acquisition / composition root.  
**AUTHORITY-BEARING** — can cause a process-valid MAC to exist.

### 4.1 Current production mint spine (AUTHORITY-BEARING)

```text
[UNTRUSTED] persist_observed_acquisition(store, acq)
        ↓
[UNTRUSTED] IngestPort.__init__ + persist_acquired(store, acq)
        ↓
[AUTHORITY-BEARING] _process_authority()          # module singleton getter
        ↓
[AUTHORITY-BEARING] ObservationAuthority._mint(acq)
        ↓
[VALIDATED] _validate_acquisition(acq)            # UNKNOWN / AI_MODEL veto only
        ↓
[AUTHORITY-BEARING] hmac.new(self._secret, canonical, sha256)
        ↓
[UNTRUSTED as data] ObservationGrant(...) + grant.to_dict()
        ↓
[UNTRUSTED persist] CognitiveMemoryStore.remember(..., OBSERVED_FACT, payload+grant)
```

`AcquisitionRecord` is a public dataclass. Every observation field is a constructor argument. Validation does **not** check that AHOS acquired the statement.

### 4.2 Other nodes that can reach mint / signer / HMAC / grant objects

| Node | Class | Reaches process-valid grant? |
| --- | --- | --- |
| `ObservationAuthority()` new instance | UNTRUSTED construct | **NO** (wrong secret) |
| `ObservationAuthority(secret=stolen)` | process compromise | **YES** if secret stolen; out of ordinary-API model |
| `ObservationAuthority._mint` on process singleton | AUTHORITY-BEARING | **YES** today via `_process_authority()` |
| `ObservationGrant(...)` / `from_dict` | UNTRUSTED data | **NO** without process MAC |
| `hmac.new` / `_mac_hex` | AUTHORITY-BEARING primitive | **YES** only with process secret |
| `verify_observation_grant` | TRUSTED verify, not mint | **NO** mint |
| `canonical_observation_bytes` | UNTRUSTED helper | **NO** mint |
| `grant_from_payload` | UNTRUSTED parse | **NO** mint |
| `remember` / `revise` / `supersede` | UNTRUSTED persist | **NO** mint (data / strip) |
| `ingest_generic_observation` | UNTRUSTED | **NO** (raises on OBSERVED_FACT); error **names** persist helper |
| `record_world_model_object` | UNTRUSTED | **NO** (raises on OBSERVED_FACT) |
| `record_failure` | UNTRUSTED | **NO** FACTUAL_PREMISE (FAILURE typed class) |
| `ConsolidationGate.accept` | UNTRUSTED | **NO** (veto OBSERVED_FACT) |
| `HypothesisStore.propose` | UNTRUSTED | **NO** (JSONL) |
| orchestrator write-back | TRUSTED loop | **NO** OBSERVED_FACT mint |
| `sqlite3.connect(store.path)` | UNTRUSTED FS | persist **YES**; process MAC **NO** |
| `corpus.seed_*` / `evaluator` / `p5_eval` / `loop.benchmark` | eval in production tree | **YES** today via persist helper |
| `tests/p5_grant_fixtures.persist_authorized` | tests | **YES** via persist helper |
| Lane A / collector `production_observations` | frozen / other DB | **NO** cognitive grant |
| Provider `NormalizedTokenCandidate` | Lane B provider data | **NO** cognitive grant today |

There is **no** other `INSERT INTO memories` than `store.py`. There is **no** other HMAC-SHA256 ObservationGrant issuer than `observation.py`.

---

## 5. Trust model

Three layers, not one:

| Layer | Meaning | Who decides |
| --- | --- | --- |
| DATA SUPPLIED BY CALLER | Any string/enum the caller passed into `remember`, adapters, SQLite, `AcquisitionRecord` | Untrusted |
| OBSERVATION ACQUIRED BY AHOS | Bytes/fields produced by a designated acquisition adapter from **its** I/O or a fixed template over **its** result object | Trusted adapter |
| AUTHORIZED FACTUAL OBSERVATION | Process MAC over the canonical tuple of that acquired observation, later verified at bind against the **latest** row + **authority time** | Bound ingest + bind |

Authorization still means: AHOS permitted this **exact representation** to be treated as observation-class evidence. **Not** that the statement is true. V3 is not a truth oracle.

Ordinary application caller (in scope):

- `CognitiveMemoryStore.remember` / `revise` / `supersede` / `record_*`
- `ingest_generic_observation` and domain wrappers
- `CognitiveOrchestrator.run(task, …)`
- `HypothesisStore.propose` / `ConsolidationGate.accept`
- constructing `CognitiveTask`, `AcquisitionRecord`, `ObservationGrant`, `ObservationAuthority()` with **no** stolen secret
- `sqlite3` on `store.path` **without** the process HMAC key
- package `__all__` of `architecture.cognitive`, `.memory`, `.loop`

Out of scope (unchanged from V2 §22):

- arbitrary code in the trusted interpreter with `gc.get_objects`, frame inspection, monkeypatched `verify_observation_grant`
- debugger / reading `_secret` / `hmac.new(stolen_secret, …)`
- filesystem admin who also holds the process secret
- replacing `bind_item`

---

## 6. Trusted acquisition architecture

### 6.1 Invalid (current)

```text
public API(statement=attacker)
        → ObservationAuthority / IngestPort
        → mint
```

`persist_acquired(AcquisitionRecord)` is invalid **even if** `IngestPort` is “trusted,” because the record **is** attacker-controlled observation data.

### 6.2 Required shape

```text
UNTRUSTED CALLER
        × cannot pass statement into mint
        × cannot construct BoundIngestPort with the process secret
        × cannot call persist_observed_acquisition (function removed or non-minting)

COMPOSITION ROOT (process start / test harness)
        → ObservationAuthority(secret=process)
        → BoundIngestPort(authority)     # capability; not a statement RPC
        → inject into designated AcquisitionAdapter only

ACQUISITION ADAPTER
        → performs I/O or receives a typed provider/collector result it owns
        → builds statement, source, observed_at, domain from THAT result
        → BoundIngestPort.persist_acquired(store, acq)
        → grant + remember
```

The trusted boundary is **before** mint: the adapter, not the dataclass.

### 6.3 Minimum legitimate acquisition contract

An observation is **acquired** iff all of the following hold:

1. A designated `AcquisitionAdapter` instance holds the BoundIngestPort (injected; not imported as a free function).
2. The adapter’s public method does **not** take a free-form `statement=` that is copied into the grant tuple. Input is a typed result the adapter produced, or no statement argument at all (internal probe).
3. `source_id` / `source_type` / `observed_at` / `domain` are filled from the adapter’s provenance rules, not from optional caller overrides that replace them.
4. UNKNOWN provenance and AI_MODEL/AGENT remain vetoed (`_validate_acquisition`).
5. Bind still verifies MAC on latest bytes. Acquisition is not a boolean `authorized=True`.

This is **not** a claim that CoinGecko (or any provider) told the truth.

### 6.4 Existing AHOS sources (reuse, do not invent)

| Source | Use in V3 |
| --- | --- |
| `architecture/providers/contracts.py` `NormalizedTokenCandidate` (`source_provider`, `retrieved_ts`, `raw_payload_sha256`) | **Future** Lane-B adapter input. Do not implement in this design phase. |
| `architecture/collector/engine.py` `CollectedObservationRecord` | Writes `production_observations` via `get_discovery_db_path()`. **Do not** mint cognitive grants from this path in V3 (Lane A DB / freeze). |
| `architecture/cognitive/loop/adapters.py` | Remains **untrusted generic ingest**. Continues to refuse `OBSERVED_FACT`. Must stop naming a mint helper in the error string. |
| Tests / eval synthetic “sensor” rows | **Tests-only** `TestAcquisitionAdapter` in `tests/`. Not a production RPC. |

Honest production fact: **today there is no production cognitive observation adapter that acquires statements such as “Retries after timeout reduced failures.”** V3 therefore requires **zero production mint entry points** until a designated adapter is injected. Tests keep a tests-only capability so the positive path remains exercisable.

Eval seeders in `architecture/cognitive/benchmark/*` and `loop/benchmark.py` must **not** import a production mint function. They receive an optional injected port from the test/eval composition root; default `None` means ungranted data (not FACTUAL_PREMISE).

---

## 7. Capability model

### Option 1 — Trusted capability object (selected)

Composition root constructs `ObservationAuthority` once and wraps it in `BoundIngestPort`. Only adapters receive that object.

- Ordinary `IngestPort()` / missing-authority persist: **fail closed** (raise or persist **without** grant — never process-mint).
- No module-level `_process_authority()` getter returning the live issuer.
- Verify uses the process key without exposing `_mint`.

### Option 2 — Closure/factory unavailable to ordinary callers

A nested `def persist_acquired` closed over the secret, never assigned to a module global.

Same ordinary-API strength as Option 1. Slightly harder to inject into several adapters. Not required if BoundIngestPort is the closure’s object form.

### Option 3 — Process-internal authority object (current, failed)

`_ProcessAuthority.instance` + public persist wrappers. **PROVEN insufficient.** Underscore + singleton is not a boundary when persist is a production function.

### Option 4 — Acquisition session/token

A token that authorizes one persist. Token **issuance** is another mint. Tokens serialize (Attack L/M). Extra surface, no gain for single-user local AHOS.

### Option 5 — Separate process/service issuer

Moves the same “does the API accept arbitrary statements?” question to IPC. Costs a daemon, ports, auth, Windows service. Violates minimum / $0 / local-first unless Option 1 is honestly insufficient. It is sufficient under the defined threat model.

**Private constructors, `__mint`, and module hiding are rejected as the boundary.**

---

## 8. Python threat-model limitation

**Can Python provide a true in-process security boundary against arbitrary code in the same trusted interpreter?**

**NO.**

Any object the process can reach, an in-process attacker who can execute unrestricted Python can reach: import, `gc.get_objects()`, `object.__setattr__`, reading module dicts, calling `hmac.new` with a stolen key, patching `verify_observation_grant` to return `True`.

V3 therefore does **not** claim protection against ACE, debugger memory, or an operator who replaces the tree.

V3 **does** claim: ordinary application callers cannot obtain factual authority through documented/normal production APIs, including the current persist helpers that the forensic probe used.

If a later gate redefines “ordinary” to include `hmac.new(observation._SECRET, …)`, then **no** in-process design is sufficient and V3-A would become **INSUFFICIENT**. That is not this threat model.

---

## 9. Acquisition proof

Not a truth proof. A **path** proof.

| Field | Trusted adapter (future provider) | Tests-only adapter | Untrusted remember/generic |
| --- | --- | --- | --- |
| origin | provider HTTP/result object | fixture I/O simulated | caller statement |
| provider | `source_provider` | `source_id="pytest"` etc. | caller |
| acquisition timestamp | `retrieved_ts` / adapter clock | test clock | caller `observed_at` |
| source identity | provider id | fixture source_id | caller |
| raw observation | payload + sha256 | fixture payload | caller payload |
| normalized observation | adapter template → statement | fixture statement **inside tests** | caller statement |
| provenance | non-UNKNOWN, not AI_MODEL/AGENT | same veto | may persist; no grant |
| validation | `_validate_acquisition` | same | `validate_new_record` |
| authorization | BoundIngestPort mint | TestIngestPort mint | none |

`TestAcquisitionAdapter.persist(statement=…)` is allowed **in `tests/`** because Level 3 tests are proving the trusted path, not the untrusted caller. Level 4 tests must not import it.

---

## 10. Trusted clock design

### 10.1 What exists (reuse)

AHOS has **no** shared `Clock` type used by the cognitive loop.

| Mechanism | Role | Use for grant `now`? |
| --- | --- | --- |
| `time.time()` | unix epoch everywhere (orchestrator `ts`, store, providers `retrieved_ts`) | **YES** — default authority time |
| `datetime.now(timezone.utc)` | ISO labels (self_research, collector `created_utc`, metrics) | not needed; grants already use unix µs |
| `CognitiveOrchestrator.run(now=)` | episode `ts`; retrieve/context/write-back | **YES** — pass `ts` into bind (existing test freeze pattern) |
| `CognitiveTask.created_at` | task metadata (`default_factory=time.time`) | **NO** |
| `ProductionScheduler.check_clock_drift` | wall vs monotonic for scheduler abort | do **not** import into cognitive loop; different subsystem |
| store `created_at` / `observed_at` | row metadata; `observed_at` is in the MAC | `observed_at` compared **to** authority time, not used **as** now |

Do not invent a clock subsystem. Do not use `datetime.now` naive local time.

### 10.2 Smallest change

Conceptual contract (do not implement in this task):

```text
bind(evidence, trusted_now, task_context)
```

Compatible mapping onto current functions:

1. `bind_item(..., now: float)` — **required** for any FACTUAL grant success. Do **not** default `now` from `task.created_at`.
2. `bind_context(..., now: float)` — pass through.
3. `reason(..., now: float)` — pass through (currently omits it).
4. `CognitiveOrchestrator.run`: `ts = time.time() if now is None else now`; pass `ts` into `reason` and into the write-back `bind_context`.
5. `EvidenceBinding` stores `authority_now=ts` (not as a trust flag). `live_grant_ok()` uses `authority_now`, never `task.created_at`.
6. Direct `bind_context` without `now`: **fail-closed** (`grant_ok=False`). No silent fallback to task time or to a second wall-clock read that disagrees with the episode.

`run(now=)` remains the AHOS test freeze for the **episode**. That is **authority time**, not task metadata. Production callers omit it and get `time.time()`.

### 10.3 TASK TIME vs AUTHORITY TIME

| Clock | Field | May control FACTUAL_PREMISE? |
| --- | --- | --- |
| TASK TIME | `CognitiveTask.created_at` | **NO** |
| AUTHORITY / EPISODE TIME | orchestrator `ts` (`time.time()` or `run(now=)`) | **YES** — this is the designated runtime clock |
| OBSERVATION TIME | row `observed_at` / `valid_until` | compared to authority time; in MAC |

Residual (honest): an ordinary caller of `CognitiveOrchestrator.run(now=past)` can still shift episode time, as every other AHOS `now=` API can. That is **not** the HIGH finding. HIGH is task metadata driving bind. Closing `run(now=)` would break deterministic tests and is not minimum. Composition-root `clock=lambda: NOW` on the orchestrator is an optional later hardening; not required to close H1.

---

## 11. Clock attack analysis

Designed outcomes after V3 (not executed — no code change):

| Attack | Setup | Expected |
| --- | --- | --- |
| A | Expired grant + old `created_at`; episode `ts` = real/frozen NOW | **INVALID** (created_at ignored) |
| B | Expired grant + future `created_at`; episode `ts` = NOW | **INVALID** |
| C | Future `observed_at` + old `created_at`; episode `ts` = NOW | **INVALID** |
| D | Future `observed_at` + future `created_at`; episode `ts` = NOW | **INVALID** |
| E | Malformed `task.created_at` | must **not** control grant; fail-closed or ignore |
| F | Timezone on timestamps | unix seconds; offset-normalized equal (already **PROVEN** canonical) |

`orch.run(now=NOW-100)` on an expired grant is episode-clock injection (test/API `now=`), classified separately in §21, not Attacks A–D.

Malformed `now` passed into bind: fail-closed (no FACTUAL_PREMISE), no fallback to `created_at`.

---

## 12. Bind contract

Current (invalid):

```text
bind_item(item, task, store)
now = task.created_at
```

V3 (minimum compatible):

```text
bind_item(item, task, store, now=trusted_now)
verify_observation_grant(..., now=trusted_now)
EvidenceBinding.authority_now = trusted_now
EvidenceBinding.task_created_at = task.created_at   # metadata only
```

`task` remains for question/domain/entity/support. `trusted_now` is authority-bearing. `created_at` is informational.

Orchestrator is the supplier of `trusted_now` on the production path. Tests that call `bind_context` directly must pass the test episode clock explicitly (Level 5).

Do not implement this signature in this task.

---

## 13. Existing protection preservation

V3 MUST NOT redesign these **PROVEN** controls:

| Control | Keep |
| --- | --- |
| Latest-state MAC | `bind_item` → `store.get`; HMAC over latest fields |
| Canonical tuple | `AHOS-OG-v1\|FACTUAL_INGEST\|OBSERVED_FACT\|sha256\|…` NFC+strip, µs, `NONE` |
| Direct SQLite | row may exist; no FACTUAL_PREMISE without process MAC |
| Revision | `revise(statement=)` strips grant; bind vs latest hash |
| Generic ingest | refuse OBSERVED_FACT |
| World-model | refuse OBSERVED_FACT |
| DERIVED_FACT | grant kind OBSERVED_FACT only; verify rejects other kinds |
| propose / accept | JSONL / veto unchanged |
| TOCTOU | rebind from store; orchestrator rebinds before write-back |
| N-hop | HYP/LESSON/INFERENCE cannot become FACTUAL_PREMISE |
| Positive path | tests-only acquisition adapter still yields FACTUAL_PREMISE |
| HMAC-SHA256 + `compare_digest` | unchanged algorithm |
| `authorized=True` | still forbidden |
| Lane A / soak | untouched |
| memories schema | grant stays in `payload_json` |

---

## 14. Test-independence analysis

`TEST_INDEPENDENCE = FAIL` is **not** “mocks bypass HMAC.” HMAC is real. The failure is **issuance**:

1. `test_no_public_issue_or_grant_mint_export` asserts naming/`__all__`. It does not call `persist_observed_acquisition` / `IngestPort` / `_mint` as an **attack**. Green ≠ blocked issuance.
2. `tests/p5_grant_fixtures.py` is a tests helper but it calls the **production** mint RPC. Positive-path and P5 polarity fixtures therefore possess the same capability the forensic attacker used. That is valid for **Level 3**. It is invalid as proof of **Level 4**.
3. Production eval modules mint without a tests-only port, so “trusted ingest” is not confined to `tests/`.
4. Temporal tests freeze time via `CognitiveTask.created_at` / fixture `NOW`, which **is** the production grant clock. They do not prove expiry against an orchestrator clock.
5. No monkeypatch of `verify_observation_grant` was found in P5 grant tests. Forged-MAC tests hit the real verifier. **PROVEN** independent for consumption.
6. `authorize_retrieved_items` persists granted rows for in-memory `RetrievedItem`s. Bind with `store=` still verifies latest SQLite. Not a verifier skip. It **is** a fixture that bypasses acquisition (Level 3 vs 4 mix).

Future tests must split levels. Do not modify tests in this task.

---

## 15. Test architecture

| Level | What it proves | Must not do |
| --- | --- | --- |
| **1 Unit crypto** | canonical bytes, compare_digest, alien `ObservationAuthority` MAC fails | mint via production RPC |
| **2 Grant binding** | latest-row MAC, revise/SQLite fail-closed, DERIVED_FACT, forged grant | claim issuance is closed |
| **3 Trusted acquisition** | TestAcquisitionAdapter + BoundIngestPort → retrieve → bind → FACTUAL_PREMISE → write-back | live in production `__all__` |
| **4 Untrusted caller** | remember, generic ingest, `IngestPort()` without capability, missing persist RPC, `ObservationGrant(...)`, `ObservationAuthority()`, sqlite INSERT → **no** FACTUAL_PREMISE | import `tests.p5_grant_fixtures` or eval seed mint |
| **5 Fresh process/retrieval** | persist (level 3) → new `store.get` / new orchestrator.run → bind uses **episode** `now`, not `created_at` | reuse a held binding as the only check |
| **6 Full regression** | pytest, Lane A 36/36, import validation | fabricate soak |

A Level 4 test that calls `persist_authorized` is **invalid** as an issuance proof.

---

## 16. Threat-model limitation (restated)

If an attacker can execute arbitrary Python inside the trusted process with unrestricted access to internal objects and memory, **no** purely in-process capability can be a true security boundary.

Intended guarantee:

> Ordinary application callers cannot obtain factual authority through documented/normal production APIs.

Not claimed: ACE, debugger, filesystem admin with secret, process memory compromise, `hmac.new(stolen_key)`.

---

## 17. Alternative architectures

| | A Bound ingest capability | B Acquisition session/token | C Separate issuer process |
| --- | --- | --- | --- |
| Closes persist RPC under ordinary API | **YES** if persist function removed and adapters don’t take `statement=` | only if token factory isn’t another RPC | only if IPC refuses arbitrary statements |
| Closes `_process_authority()._mint` as ordinary API | **YES** if getter removed | same | secret not in-process |
| Closes stolen `_SECRET` + hmac | **NO** (Python) | **NO** | **NO** vs local admin; maybe vs in-process import |
| Complexity | small | medium (token lifecycle, replay) | large (IPC, Windows service, auth) |
| Compatibility | keep SQLite, MAC, bind | extra payload | new ops surface |
| Local Windows / $0 | yes | yes | extra process, not $0-minimum |
| Testability | TestIngestPort in `tests/` | tokens in tests leak | integration tax |
| Attack surface | capability object leak = residual ACE | serialized tokens | network/pipe |
| Migration | delete/relocate persist helper; inject eval seeders | more than A | largest |
| Cognitive Core | composition-root inject | sessions in core | second brain risk if it reasons |

**C is not selected.** Local-first single-user AHOS. A is sufficient under §8/§16.

**B is not selected.** Token issuance duplicates mint.

---

## 18. Recommended architecture

**V3-A: Bound ingest capability + episode authority clock.** Family remains Hybrid-D.

### Issuance

- Remove or gut production `persist_observed_acquisition` so it **cannot** mint.
- `IngestPort` as a Protocol only (already sketched as `_IngestPortProtocol`). Concrete `BoundIngestPort` constructed at composition root with the process `ObservationAuthority`.
- Delete `_process_authority()` as a live-issuer getter. Verify must not require calling `_mint`.
- `ObservationAuthority()` without the process secret still fails verify (keep).
- Generic ingest / world-model / remember unchanged as non-minting.
- Eval seeders: injected port or ungranted data.
- Tests-only adapter in `tests/` for Level 3 / positive path.

### Clock

- Orchestrator `ts` → `reason` → `bind_context` → `bind_item` → `verify_observation_grant(now=ts)`.
- `live_grant_ok` uses stored `authority_now`.
- `task.created_at` never read for grant validity.

### Attacks on V3-A (design classification)

| # | Attack | Result |
| --- | --- | --- |
| A | Import issuer class | **BLOCKED** for process-valid mint (class ≠ live secret) |
| B | Instantiate `ObservationAuthority()` | **BLOCKED** (alien secret) |
| C | Construct capability `BoundIngestPort()` with no authority | **BLOCKED** (fail closed) |
| D | Call `_mint` on new instance | **BLOCKED**; on process instance **BLOCKED** as ordinary API if getter removed; **OPEN** as ACE/secret theft |
| E | Call mint through remember/generic/world-model/propose/accept | **BLOCKED** |
| F | Attacker-controlled statement on production persist RPC | **BLOCKED** (RPC gone); on TestAdapter **OPEN** by design (Level 3 only) |
| G–J | Attacker source / timestamp / entity / scope on production mint RPC | **BLOCKED**; live support/MAC still apply at bind for granted rows |
| K | Replay capability object | **UNRESOLVED** vs ACE holding the port; **BLOCKED** as ordinary API (port not returned from remember/run) |
| L/M | Serialize/deserialize capability | **BLOCKED** (must not pickle secret; grant JSON is data, still needs verify) |
| N | Obtain capability from return values | **BLOCKED** (`remember` returns `MemoryRecord`, not BoundIngestPort) |
| O | Globals/singletons | **BLOCKED** if `_process_authority` removed; **OPEN** today |
| P | DI | **BLOCKED** for callers not given the port; composition root **TRUSTED** |
| Q | Configuration | **BLOCKED** (no secret in config/env for mint) |

---

## 19. Authority graph

```text
UNTRUSTED CALLER
       × persist_observed_acquisition
       × IngestPort().persist_acquired
       × _process_authority()._mint
       × remember(OBSERVED_FACT) as FACTUAL_PREMISE
       × sqlite INSERT as FACTUAL_PREMISE
       × ingest_generic / world-model FACT
       × task.created_at as grant now
       × DERIVED_FACT + copied grant
       × propose / accept factification
       × HYP/LESSON/INFERENCE → OBSERVED_FACT
       │
       │ cannot mint
       ▼
TRUSTED ACQUISITION PATH          (injected adapter only)
       ↓
ACQUISITION AUTHORITY             (BoundIngestPort + process ObservationAuthority)
       ↓
ObservationGrant                  (HMAC over canonical tuple)
       ↓
PERSISTENCE                       (label OBSERVED_FACT + grant material)
       ↓
LATEST-STATE MAC VERIFICATION
       +
TRUSTED RUNTIME CLOCK             (orchestrator ts; NOT task.created_at)
       ↓
FACTUAL_PREMISE
       ↓
P5 REASONING
       ↓
CRITIC
       ↓
REUSABLE WRITE-BACK               (HYP/LESSON/INFERENCE only)
```

---

## 20. Attack matrix

Status = **V3 design** vs ordinary API. Current code in parentheses where different.

| Attack | V3 | Current (forensic) |
| --- | --- | --- |
| direct remember | **BLOCKED** | BLOCKED |
| public `issue()` | **BLOCKED** | BLOCKED (name only) |
| `persist_observed_acquisition` | **BLOCKED** | **OPEN** |
| `persist_acquired` on default IngestPort | **BLOCKED** | **OPEN** |
| `_mint` via module getter | **BLOCKED** | **OPEN** |
| `_mint` via stolen secret / ACE | OPEN (out of model) | OPEN |
| generic ingest | **BLOCKED** | BLOCKED |
| world-model ingest | **BLOCKED** | BLOCKED |
| direct SQLite | **BLOCKED** for FACTUAL | BLOCKED |
| revision inherit | **BLOCKED** | BLOCKED |
| grant replay other tuple | **BLOCKED** | BLOCKED |
| grant replay identical tuple | SAFE REUSE | SAFE REUSE |
| grant serialization | data only; verify required | same |
| capability construction without root | **BLOCKED** | N/A (persist is the capability) |
| capability extraction from APIs | **BLOCKED** | persist **is** extracted |
| arbitrary statement on production mint | **BLOCKED** | **OPEN** |
| arbitrary source/timestamp/entity/scope on production mint | **BLOCKED** | **OPEN** |
| caller-controlled `created_at` | **BLOCKED** | **OPEN** |
| `run(now=)` episode shift | OPEN (test clock; not H1) | unused for grants |
| clock skew / timezone canonical | BLOCKED as bypass | BLOCKED |
| future timestamp vs authority now | **BLOCKED** | OPEN via created_at |
| expired grant vs authority now | **BLOCKED** | OPEN via created_at |
| DERIVED_FACT | **BLOCKED** | BLOCKED |
| propose | **BLOCKED** | BLOCKED |
| accept | **BLOCKED** | BLOCKED |

---

## 21. Future implementation scope

Do **not** implement in this task.

### MUST CHANGE (minimum)

1. Close arbitrary grant minting  
   - `architecture/cognitive/memory/observation.py` — persist RPC, `IngestPort` default mint, `_process_authority` getter, BoundIngestPort  
   - `architecture/cognitive/loop/adapters.py` — error text must not instruct callers to mint  
   - `architecture/cognitive/loop/benchmark.py`  
   - `architecture/cognitive/benchmark/corpus.py`  
   - `architecture/cognitive/benchmark/evaluator.py`  
   - `architecture/cognitive/benchmark/p5_eval.py`  
   - `tests/p5_grant_fixtures.py` — tests-only adapter; stop calling production persist RPC  
   - `tests/test_p5_observation_grant.py` — Level 4 issuance attacks

2. Remove caller control from factual temporal validation  
   - `architecture/cognitive/loop/binding.py` — `bind_item` / `live_grant_ok`  
   - `architecture/cognitive/loop/reason.py` — pass `now`  
   - `architecture/cognitive/loop/orchestrator.py` — pass `ts` into reason/bind  
   - tests that `bind_context` without `now` while expecting FACTUAL_PREMISE

3. Tests that genuinely exercise the production trust boundary  
   - Level 4 must not use fixtures that mint  
   - Attacks A–D on `created_at` with frozen episode `now`

### MUST NOT CHANGE

- Lane A (`discovery/**`, `paper_trading/**`), soak DBs/evidence  
- HMAC algorithm, canonical version string, grant-in-payload schema  
- `remember` as data; SQLite engine  
- critic / polarity / hop / propose / accept / world-model refuse  
- collector → discovery DB path (do not mint from Lane A)  
- historical forensic reports  
- PR #93 draft/merge state

No new files are created in this design task except this report.

---

## 22. Future test specification

Add during implementation (not now):

1. Attacker cannot obtain BoundIngestPort / process `ObservationAuthority` from package `__all__` or store/orchestrator return values.  
2. Attacker cannot invoke grant issuance with an arbitrary statement on any production function.  
3. `persist_observed_acquisition` is absent **or** does not mint process-valid grants (Level 4 bind check, not `hasattr` only).  
4. `IngestPort().persist_acquired` / default constructor does not mint.  
5. Direct SQLite remains non-authoritative.  
6. Revised observation invalidates old grant.  
7. Latest-state MAC remains mandatory (TOCTOU revise then bind).  
8. Expired grant remains invalid regardless of `task.created_at` (episode `now` current).  
9. Future `observed_at` cannot become factual via `created_at` manipulation.  
10. Legitimate tests-only trusted acquisition still works (fresh retrieve/bind).  
11. Tests exercise fresh retrieval/bind (`store.get` / new `run`).  
12. No Level 4 fixture bypasses issuer (`p5_grant_fixtures` not imported).  
13. No mock/monkeypatch of `verify_observation_grant` in grant tests.  
14. Two-hop and three-hop remain blocked.

---

## Final architectural decision

V3-A is the smallest architecture that closes the two **PROVEN** findings under the ordinary application-caller model without replacing Hybrid-D consumption, without a second process, and without treating Python visibility as authority.

It is **VALID** as a design. It is **not** implemented. Implementation remains unauthorized.

---

`V3_ARCHITECTURE = VALID`

`V3_SECURITY_REVIEW = PASS`

`GRANT_ISSUANCE_AUTHORITY = CLOSED`

`CALLER_CONTROLLED_TIME = CLOSED`

`PERSIST_OBSERVED_ACQUISITION_BYPASS = CLOSED`

`PERSIST_ACQUIRED_BYPASS = CLOSED`

`TEST_INDEPENDENCE = FAIL`

`DIRECT_SQLITE_ESCALATION = BLOCKED`

`REVISION_AUTHORITY_REUSE = BLOCKED`

`LATEST_STATE_MAC = PASS`

`DERIVED_FACT_SEPARATION = PASS`

`TOCTOU = PASS`

`N_HOP_ESCALATION = BLOCKED`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`IMPLEMENTATION_AUTHORIZED = NO`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`REPORT = reports/agi_aci_evolution/P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md`
