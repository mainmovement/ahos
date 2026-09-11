# P5 V4-PIN — final secret-boundary design gate

**Kind:** Adversarial design review. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Implementation baseline:** `24b2ab8244f41d9e78582ccfc41dc4b0cf490a83`  
**HEAD at analysis:** `9b83c6cfd7b44ee5ccc4fde6be385ec6299783ff` (report-only after baseline)  
**Code delta `24b2ab8..HEAD` (`*.py`, Lane A, soak):** empty  
**This document does not authorize implementation.**

Not AGI. Not ACI. Not production-ready. Not live trading.

Proof language: **PROVEN** (tree `24b2ab8`) / **DESIGN** (unimplemented V4-PIN) / **GATE**.

---

## 1. Executive conclusion

**Current tree:** a legitimate production `CognitiveOrchestrator` instance `O` **can** accept attacker-created evidence as `FACTUAL_PREMISE`. `run()` copies parent ContextVar `key`/`issuer_id`, then **places `O._grant_verify_secret` itself into `GrantVerifyContext` and pushes it** before calling the public `retriever=`. `push_grant_verify_context` is a public setter. `BoundIngestPort(ObservationAuthority(secret=k))` is a public mint. That join is **PROVEN**. `V4 IMPLEMENTATION = NOT PRESENT`.

**Rejected prior sketch:** putting `K_O` into a ContextVar “only inside `run()`” **fails Layer 3**. `retriever.retrieve` runs **after** that push, with `store` and `task` in hand, and can call `current_grant_verify_context()` / `push_grant_verify_context`. That is ordinary DI, not a debugger.

**This gate’s design is VALID** if and only if all of the following are true together:

1. **Layer 1** — HMAC-SHA256 over latest canonical observation (already **PROVEN**).
2. **Layer 2** — production `O.run()` accepts a grant only under `K_O + ISSUER_ID`; caller-minted grants are alien.
3. **Layer 3** — `K_O` exists only as `O` instance state and is read only inside `O`’s own verification method. It never enters ContextVar, `GrantVerifyContext`, bindings, tasks, retrieved items, retriever/memory arguments, logs, or `CognitiveResult`.

Same-process call-stack pinning **is** the minimum architecture under the stated threat model. Option E is not required. Frame-walking / `gc` / `sys._getframe` to steal `self` from a caller frame is classified with debugger/process-memory (out of scope). If a later reviewer brings those into scope, this design is **insufficient** and Option E becomes the minimum.

Central question — can any ordinary caller-controlled key, issuer, verifier, ContextVar, retriever, memory collaborator, authority object, acquisition object, persistence path, or injected dependency cause production `O` to accept attacker-created evidence as `FACTUAL_PREMISE`?

| State | Answer |
| --- | --- |
| Tree `24b2ab8` | **YES (PROVEN)** |
| V4-PIN as specified here | **NO (DESIGN)** |
| V4-PIN with `K_O` in ContextVar / `GrantVerifyContext` / public `key=` / `permits=` | **YES — reject** |

`IMPLEMENTATION_AUTHORIZED = NO`. Independent review of this report is required before any implementation turn.

---

## 2. Current-tree forensic status

| Item | Value |
| --- | --- |
| Baseline | `24b2ab8` |
| HEAD | `9b83c6c` report-only |
| PR #93 | **DRAFT** |
| Lane A / soak vs baseline | **UNTOUCHED** |
| Production mint call sites in `architecture/` | **none** (`BoundIngestPort(` only as the class) |
| Ctor `ingest=` / `verifier=` / `secret=` | **TypeError** — insufficient |
| `run()` parent copy | **PROVEN OPEN** |
| `K_O` in ContextVar during retrieve | **PROVEN OPEN** |
| Public `push_grant_verify_context` | **PROVEN OPEN** |
| `grant_verify_scope` + production `O.run` in tests | **same join as C1** |

`run()` (**PROVEN**, `orchestrator.py`):

```text
parent = current_grant_verify_context()
if parent is not None:
    verify_ctx = GrantVerifyContext(parent.key, parent.issuer_id, ts)   # attacker key wins
else:
    verify_ctx = GrantVerifyContext(self._grant_verify_secret, ISSUER_ID, ts)  # K_O published
push_grant_verify_context(verify_ctx)
retriever.retrieve(self.memory, task, now=ts)   # DI window; ContextVar already live
assemble_context(retrieved, self.memory, ...)
reason(..., store=self.memory, now=ts)          # bind_item reads ContextVar key
bind_context(...) again for writeback
```

`verify_observation_grant` (**PROVEN**): `use_key = key or ctx.key`; `use_issuer = expected_issuer_id or ctx.issuer_id or ISSUER_ID`.

---

## 3. Threat model

**Attacker:** ordinary in-process Python application code.

**Can:** import modules; construct public classes; pass arguments; compose objects; create `ObservationAuthority` / `BoundIngestPort` / `ObservationGrant` / `AcquisitionRecord`; choose HMAC key and issuer; call public APIs including `push_grant_verify_context`, `verify_observation_grant`, `bind_item`, `reason`, `remember`; supply `retriever=` and `memory=`; observe values passed into those collaborators; catch exceptions; inspect return values (`CognitiveResult`, traces, records).

**Cannot:** modify source; debugger; process-memory dump; OS/filesystem admin; steal `K_O` by tampering with CPython internals.

**In-scope DI observation:** arguments, return values, ContextVars, objects attached to public DTOs, public getters/setters, module globals the application actually writes.

**Out of scope (implementation introspection):** `sys._getframe` / `inspect.stack` walking to `O` on a caller frame; `gc.get_referrers`; `ctypes`; assigning `O._grant_verify_secret` on a held production instance (composition-root / ACE). The composition root that constructs `O` already holds `O`. The threat is plugins and other ordinary code that are **not** handed `O` and must not **rekey** `O.run()`.

---

## 4. Formal V4-PIN invariant

For production instance `O = CognitiveOrchestrator(...)`:

```text
K_O              := bytes from os.urandom(32) in O.__init__
                    (retry while SHA-256 ∈ test-vector denylist)
PRODUCTION_ISSUER := "ahos.observation_authority"   # module ISSUER_ID
                    copied into O._verify_issuer_id in production __init__
                    (not a constructor argument)

ProductionVerifier(O) := (K_O, O._verify_issuer_id)

FACTUAL_PREMISE in O.run  ⇔
    Verify(
        grant     = latest_row.payload["observation_grant"],
        canonical = canonical_observation_bytes(latest_row fields),
        key       = K_O,
        issuer    = O._verify_issuer_id,
        now       = episode ts (run(now=) or time.time()),
        extras    = existing kind / temporal / entity / scope / polarity / status
    )
```

Forbidden verify inputs: `ContextVar.key`, `ContextVar.issuer_id`, caller `key=`, retriever-supplied key, grant-embedded “use this key”, injected `permits=` callback.

`K_O` constraints:

| | |
| --- | --- |
| Origin | `O.__init__` only (`os.urandom`) |
| Caller supply / select / replace via public API | **forbidden** |
| Public return values / DTOs | **forbidden** |
| ContextVar replace / copy | **forbidden** |
| Injected collaborator select | **forbidden** |

Object existence (`ObservationAuthority(secret=k)`) is **not** production authority. Production authority is **acceptance by `O.run()`** under `K_O`.

---

## 5. Actual authority graph (tree, then required V4 call direction)

### 5.1 Tree execution (PROVEN)

```text
O.run(task, now=?)
  ├─ ContextVar ← parent.key OR K_O          # Layer 3 leak + Layer 2 switch
  ├─ retriever.retrieve(memory, task, now)   # caller DI; sees ContextVar
  ├─ assemble_context(retrieved, memory)     # memory.find_contradictions
  ├─ reason() [module]
  │    └─ bind_context → bind_item
  │         └─ store.get (latest row)
  │         └─ observation_grant_permits_factual → ctx.key
  │         └─ EvidenceBinding; may()/live_grant_ok → ctx.key again
  │    ├─ MODE_FNS (uses may(FACTUAL_PREMISE))
  │    ├─ critique_result (uses may)
  │    └─ apply_episode_positive_policy
  ├─ bind_context again → reusable_writeback_permitted
  └─ hypotheses.propose / memory.remember (HYP/LESSON/INFERENCE/episode)
       # no ObservationGrant on writeback rows
```

Collaborators **before** grant verify: `retriever`, `memory` (`recent`/`get`/`find_contradictions`).  
Collaborators **during** bind verify: `memory.get`.  
Collaborators **after** roles exist: `hypotheses`, `memory.remember`, experiment ledger.  
No async; `run` is synchronous. No hooks/callbacks beyond DI objects. No logging of `K_O` (**PROVEN** grep: secret only assigned and stuffed into `GrantVerifyContext`).

### 5.2 Required V4 call direction (DESIGN)

```text
O.run(task, *, budget, now, use_memory)     # public kwargs unchanged
  ts = now or time.time()
  # MUST NOT read or write grant ContextVar
  retrieved = retriever.retrieve(memory, task, now=ts)   # no K_O on stack as an argument
  ctx = assemble_context(retrieved, memory, now=ts)
  verdict, ... = O._reason_episode(task, ctx, retrieved_ids, ts)
      bindings = O._bind_context(ctx, task, now=ts)
          for item: O._bind_item(...)
              latest = memory.get(id)                   # data only
              grant_ok = O._permits_observation_grant(latest, now=ts)
                  verify_observation_grant(
                      ...,
                      key=self._grant_verify_secret,    # FIRST AND ONLY read of K_O for verify
                      expected_issuer_id=self._verify_issuer_id,
                  )
              EvidenceBinding(..., grant_ok=grant_ok)   # boolean, not K_O
      evaluate_reason(task, ctx, bindings, ...)         # no key/verifier/permits arguments
  reusable = reusable_writeback_permitted(verdict, O._bind_context(...))
  writeback remember() without OF grants
```

`K_O` first becomes available at `O.__init__`. It first becomes available to **verification** at `O._permits_observation_grant`. It is **never** an argument to `retrieve`, `assemble_context`, `remember`, or public `reason`/`bind_item`.

Public module `reason` / `bind_item` / `bind_context` remain fail-closed: they **must not** consult ContextVar keys and **must** set `grant_ok=False`. Production `O.run` **must not** call them to assign `FACTUAL_PREMISE`.

---

## 6. Secret data-flow graph

### Tree (PROVEN, illegal for V4)

```text
O.__init__  →  O._grant_verify_secret
O.run       →  GrantVerifyContext.key  →  ContextVar  →  retriever / bind / live_grant_ok
```

### V4 (DESIGN, only allowed flow)

```text
O.__init__  →  O._grant_verify_secret          # instance field
                 │
                 └── O._permits_observation_grant  →  verify_observation_grant(key=K_O)
                        └── boolean grant_ok       →  EvidenceBinding.grant_ok
```

No other arrow.

---

## 7. Secret non-observability matrix

| Location | Tree | V4 | Class |
| --- | --- | --- | --- |
| `O._grant_verify_secret` | present | **ALLOWED** — sole store | instance state |
| `O._permits_observation_grant` locals | n/a | **ALLOWED** — `key=self._grant_verify_secret` argument to `verify_observation_grant` only | trusted verify path |
| ContextVar | **FORBIDDEN (present)** | **FORBIDDEN** | — |
| `GrantVerifyContext` | **FORBIDDEN (present)** | **FORBIDDEN** for keys/issuers-as-authority | — |
| `EvidenceBinding` | no raw key; `live_grant_ok` uses ContextVar | boolean `grant_ok` only; **no K_O** | DTO |
| `RetrievedItem` / `CognitiveTask` / `CognitiveResult` / `ReasoningTrace` | no key | **FORBIDDEN** | — |
| `retriever.retrieve` args/return | ContextVar observable | args are `store, task, now` only — **FORBIDDEN** to add key | DI |
| `memory.get` / `remember` | rows may hold grant **MAC** (not `K_O`) | same; MAC is not `K_O` | persistence |
| Hypothesis store | unused before verify | unused for `K_O` | — |
| Logging / exceptions / repr | default `object` repr; no log of secret | **FORBIDDEN** to log/repr `K_O`; do not put it in `ValueError` text | — |
| Thread-local / async task-local | ContextVar (task-local) | **FORBIDDEN** for `K_O` | — |
| Globals | denylist SHA-256 only | keep denylist; **no raw K_O** | — |
| Serialization / sqlite | grant JSON MAC | MAC under `K_O` is not `K_O` | — |
| Public `current_grant_verify_context()` | returns `.key` | must not return `K_O`; production `run` must not set it | — |

If `K_O` must be stored on a collaborator-visible object, **reject the design**. It does not.

---

## 8. Retriever attack

Public surface (**PROVEN**): `CognitiveOrchestrator(..., retriever=MemoryRetriever())`.  
`retrieve(self, store, task, *, now=...) -> list[RetrievedItem]`.

| Question | Tree | V4 |
| --- | --- | --- |
| 1. Inspect `K_O` via implemented data path? | **YES** — `current_grant_verify_context().key` after `run` push | **NO** — not in ContextVar, not in args |
| 2. Modify production verification state? | **YES** — `push_grant_verify_context(attacker)` | **NO** — `O._permits` ignores ContextVar |
| 3. Replace a verifier object? | ContextVar **is** the verifier | **NO** — verifier is `O._permits`, not passed in |
| 4. Inject attacker key? | **YES** (push) | **NO** |
| 5. Return attacker-controlled evidence? | **YES** | **YES** — **malicious data, expected** |
| 6. Call public `verify_observation_grant`? | **YES** | **YES** — cannot assign `O.run` roles |
| 7. Manipulate ContextVars? | **YES** | **YES** — **must not matter** to `O._permits` |
| 8. Influence `reason`/`bind_item` inputs? | **YES** (retrieved list) | **YES** — data only |
| 9. Cause attacker evidence to verify under `K_O`? | **YES** if they mint under the **injected** key, which `run` then uses | **NO** — they cannot MAC under `K_O`; alien MAC fails |

**Malicious data ≠ production authority.** A retriever may return any `memory_id` / statement. Bind loads **latest store row** and HMAC-checks under `K_O`. Forged grant JSON does not verify. Production mint count remains 0 until a later poll adapter; then mint is not a retriever capability.

`inspect.stack` from `retrieve` to steal `self` from `O._run_episode`: **out of threat model** (§3). If in-scoped later → Option E.

---

## 9. Memory attack

`memory=` is a `CognitiveMemoryStore` (or subclass). During `run` it is called as `recent`, `get`, `find_contradictions`, later `remember`.

| Capability | Production authority? |
| --- | --- |
| Return arbitrary rows from `get`/`recent` | data; MAC under `K_O` still required |
| `remember` ungranted `OBSERVED_FACT` | **TREE BLOCKED** for FACTUAL; keep |
| Write grant JSON into payload | alien MAC; **not** `K_O` |
| Retain row objects / mutate dict payloads | bind snapshots at `_bind_item`; `grant_ok` frozen boolean cannot be flipped by payload mutation after bind |
| Call `BoundIngestPort` / `push_grant_verify_context` | mint under attacker key; V4 `O` rejects |
| `memory → production authority` | **TREE:** yes, combined with ContextVar join. **V4:** **NO** |

Subclass `get()` using `gc.get_referrers` to find `O`: out of scope.

---

## 10. ContextVar attack

| | Tree | V4 |
| --- | --- | --- |
| What it carries | `key`, `issuer_id`, `trusted_now` | **must not** carry secret, issuer-as-authority, verifier, grant context |
| `run()` copies parent key/issuer | **YES** | **MUST NOT**; `run` must not read grant ContextVar |
| `run()` publishes `K_O` | **YES** (else branch) | **MUST NOT** push `K_O` |
| Public push | **YES** | may remain as a function; production verify **ignores** it |
| Nested `O2.run` during `O1.run` | inner copies outer key | each uses own `K_O` because neither reads ContextVar |
| Remaining legitimate use | clock fallback in `_trusted_now` | production always passes `now=ts`; ContextVar **not required**. Preferred: production `run` **does not touch** the grant ContextVar at all |

If any ContextVar still selects verify **key or issuer**, **reject**. Clock-only ContextVar is optional and not an authority bus (`run(now=)` is already public).

---

## 11. Authority construction attack

| Constructor | May exist? | Implies production authority? |
| --- | --- | --- |
| `ObservationAuthority(secret=k)` | yes (ordinary API) | **NO** after pin — wrong HMAC vs `K_O` |
| `BoundIngestPort(authority)` | yes | **NO** — mints under `k`, not `K_O` |
| `ObservationGrant(...)` / `mac_hex(k, bytes)` | yes | **NO** — bytes in JSON; verify uses `K_O` |
| `AcquisitionRecord(statement=...)` | yes | **NO** — not a production mint input under `K_O` |
| `GrantVerifyContext(k, issuer, now)` | yes | **NO** — `O._permits` ignores it |
| `IngestPort.persist_acquired` | exists | raises; cannot mint |

**Object validity ≠ production authority.** Production authority is `O._permits_observation_grant` succeeding. Attacker objects are cryptographically irrelevant unless they collide with `K_O` (negligible).

Do not hide constructors as the security core. Do not add `O.ingest=`.

---

## 12. Issuer substitution attack

| | Tree | V4 |
| --- | --- | --- |
| Source | `ISSUER_ID` **or parent.issuer_id** | `O._verify_issuer_id` set to `ISSUER_ID` in production `__init__` |
| Caller ctor replace | no | **no ctor kwarg** |
| ContextVar replace | **YES** | **ignored** |
| Collaborator replace | via ContextVar | **NO** |
| Attacker `issuer_id="attacker"` on grant | accepted if parent issuer matches | `grant.issuer_id != O._verify_issuer_id` → fail |
| Bound into MAC? | yes (`canonical_observation_bytes` includes issuer) | **yes** — `K_O + issuer` both checked |

String `ISSUER_ID` alone is not the boundary. Boundary is **HMAC under `K_O` over canonical bytes that include issuer**, plus equality to `O._verify_issuer_id`. Test issuer `ISSUER_ID_TEST` is used only by `TestCognitiveOrchestrator._verify_issuer_id`.

---

## 13. Fake acquisition attack

```text
TypedFakeAcquisitionResult.raw_reading
    → tests TestAcquisitionAdapter
    → AcquisitionRecord(statement=raw_reading)
    → BoundIngestPort.persist_acquired
    → MAC(TEST_VECTOR_KEY)
    → grant_verify_scope
    → production O.run          # TREE: accepted
```

Dataclass instantiation is ordinary and **not** by itself a vulnerability.

**Production crossing:** there is **no** production function `ingest(TypedFakeAcquisitionResult)`. Ordinary attackers skip the dataclass and call `BoundIngestPort` + `AcquisitionRecord` directly (**PROVEN**).

**V4 capability boundary (not naming):**

- Production code in `architecture/` must not mint under `K_O` via any function whose parameters include `statement=`, `AcquisitionRecord`, or a caller-built “typed result”.
- Until a poll/fetch adapter is **separately** authorized, production mint stays **0**. Then `FACTUAL_PREMISE` never occurs in production `O.run` — fail-closed, not a bypass.
- Future adapter public API: `poll()`/`fetch()` with **no result argument**. Provider I/O stays inside the adapter object owned by the composition root. That object must not be handed to ordinary `run()` callers as a `statement=` RPC.

Tests mint under **test instance** `K_test`, not by pushing `TEST_VECTOR_KEY` into production `O`.

---

## 14. Multi-orchestrator analysis

| | Tree | V4 |
| --- | --- | --- |
| Distinct `K_O`? | **YES** (`os.urandom` per `__init__`) | **YES** |
| `Grant(O1)` valid for `O2`? | no if both have empty parent; **yes** if shared ContextVar copied | **NO** — each `_permits` uses own `K_O` |
| Cause `O2` to use `O1`’s secret via public API? | ContextVar copy | **NO** |
| Nested `O2.run` inside `O1.run` | inner inherits outer key | each instance isolated |

Required: `Grant(O1)` is not automatically valid for `O2`. No transfer mechanism exists; do not add one.

---

## 15. Writeback escalation analysis

Writeback of HYPOTHESIS / LESSON / INFERENCE requires `reusable_writeback_permitted` → positive verdict **and** `decision_bearing_supporters` → `may_support_task()` **and** `may(FACTUAL_PREMISE)`.

```text
attacker evidence
    → FACTUAL_PREMISE        # TREE: yes via ContextVar join; V4: no without K_O MAC
        → positive verdict   # requires FACTUAL supporters + polarity/entity gates
            → reusable writeback
```

V4 does not weaken: episode mixed-polarity policy, critic, latest-row MAC, revision/supersede grant strip, DERIVED_FACT ≠ FACTUAL, ungranted N-hop, `task.write_back` still required. Ungranted OF remains data.

Writeback rows themselves are not `OBSERVED_FACT` grants (**PROVEN**).

---

## 16. Test architecture (coherence; not implemented here)

| Piece | Rule |
| --- | --- |
| `TEST_VECTOR_KEY` | tests-only; SHA-256 denylisted for production issuer |
| `ISSUER_ID_TEST` | tests-only |
| `TestCognitiveOrchestrator` | `tests/` only; `super().__init__` then `self._grant_verify_secret = TEST_VECTOR_KEY` and `self._verify_issuer_id = ISSUER_ID_TEST` |
| Production `__init__` | no test hook, no `secret=` kwarg |
| Production imports of tests | **forbidden** |
| `grant_verify_scope` wrapping production `CognitiveOrchestrator.run` | **forbidden** (that **is** C1) |
| Fake acquisition | `tests/observation_test_runtime.py` only |
| Layer 4 | production `O` + `BoundIngestPort` + `push_grant_verify_context` → **not** FACTUAL |
| `verify_test_grant` | may pass `key=TEST_VECTOR_KEY` into public `verify_observation_grant`; that is not `O.run` |

Production `K_O` is per-instance urandom, never imported by tests. Reading `orch._grant_verify_secret` on an orchestrator a test constructed is that instance’s key, not a shared production secret file. Keep it out of Layer 4 mint proofs.

---

## 17. Option E comparison

| | Stack-local V4-PIN | Option E (local issuer process) |
| --- | --- | --- |
| Stops ContextVar join / retriever rekey | yes if `K_O` never in ContextVar | yes |
| Stops caller `ObservationAuthority(k)` as production-valid | yes (acceptance) | yes |
| Stops `inspect.stack` / `gc` steal of `O` | **no** | yes |
| Stops held-`O` `__dict__` | **no** | yes |
| In declared threat model? | stack/gc/held-O out of scope | stronger than needed |
| Windows-first / local / $0 | yes | possible, extra process |

**Same-process pin is sufficient** because the in-scope C1 path is **API composition + ContextVar + DI overwrite**, not frame introspection. Option E is the fallback if implementation reintroduces ContextVar keys, public `key=`/`permits=`/`secret=`, or a persist RPC that mints under `K_O` from `statement=`.

---

## 18. Implementability specification

An implementer must not invent a fourth place to put `K_O`. Exact contract:

### Ownership

| Thing | Owner | Written | Read |
| --- | --- | --- | --- |
| `K_O` | `CognitiveOrchestrator._grant_verify_secret` | `__init__` only (tests subclass after `super`) | `O._permits_observation_grant` only |
| Production issuer | `O._verify_issuer_id` | production `__init__` := `ISSUER_ID` | `_permits_observation_grant` |
| Episode clock | local `ts` in `run` | `now=` or `time.time()` | passed as `now=` into bind/reason; **not** `task.created_at` |
| Verification | `O._permits_observation_grant` | — | called only from `O._bind_item` |

### Public signatures (forbidden additions)

`CognitiveOrchestrator.__init__(memory, hypotheses, ledger_path, retriever=None)` — **do not add** `secret`, `verifier`, `ingest`, `authority`, `issuer`, `grant_verify_context`, `permits`.

`CognitiveOrchestrator.run(task, budget=None, now=None, use_memory=True)` — **do not add** those either.

Public `reason` / `bind_item` / `bind_context` — **do not add** `key=`, `secret=`, `verifier=`, `permits_factual=`, `grant_ok=`.

### Required new/changed internal symbols (names illustrative; behavior mandatory)

| Symbol | Behavior |
| --- | --- |
| `O._permits_observation_grant(...)` | `verify_observation_grant(..., key=self._grant_verify_secret, expected_issuer_id=self._verify_issuer_id, now=ts)`; never reads ContextVar |
| `O._bind_item` / `O._bind_context` | latest-row load; `grant_ok = O._permits_observation_grant`; freeze `grant_ok` on `EvidenceBinding` |
| `O._reason_episode` | bind via `O._bind_*` then existing mode/critic/episode policy on those bindings |
| `evaluate_reason` (or inline) | takes **already bound** list; no verifier callback |
| Public `bind_item` | `grant_ok=False`; ignore ContextVar keys |
| `EvidenceBinding.live_grant_ok` | return frozen `grant_ok`; **do not** HMAC via ContextVar |
| `verify_observation_grant` | `use_key` **only** from explicit `key=` argument; if `key is None` → `False`; **do not** default to `ctx.key`. `use_issuer` from `expected_issuer_id` or `ISSUER_ID`, **not** `ctx.issuer_id` |
| `O.run` | **do not** call `current_grant_verify_context` / `push_grant_verify_context` / `GrantVerifyContext` |

### Collaborators

Must not receive `K_O`, issuer authority, or verifier callables. `retrieve(store, task, now=ts)` unchanged. `memory.get` returns rows only.

### ContextVar

Must not carry `K_O`, production issuer authority, verifier, or authority-bearing grant context. Production `run` should not set the grant ContextVar. If the ContextVar remains for unused clock fallback, production bind must ignore it for keys **and** issuers.

### Tests

`TestCognitiveOrchestrator` in `tests/` as in §16. Production must not import it. Layer 4 C1 replay stays non-FACTUAL.

### Acceptance condition (production `O.run`)

```text
FACTUAL_PREMISE ⇔ HMAC(K_O, canonical(latest OBSERVED_FACT)) succeeds
                 ∧ grant.issuer_id == O._verify_issuer_id == ISSUER_ID
                 ∧ temporal/entity/scope/polarity/status gates
                 ∧ trusted now = episode ts
```

If an engineer cannot implement this without putting `K_O` in ContextVar or adding `key=` to public `reason`, they must stop and re-read this section — not improvise.

### Files (future authorized turn only)

`orchestrator.py`, `observation.py` (verify default; stop using ContextVar as key bus), `binding.py` (`grant_ok` freeze; `live_grant_ok`), `reason.py` (split bind vs evaluate **or** only call from `O._reason_episode`), `tests/observation_test_runtime.py`, P5 tests, `tests/test_p5_v3_authority_boundary.py`. Lane A / soak / schema untouched. No migration (process `K_O` already ephemeral).

---

## 19. Residual risks

1. HMAC bytes with random `k` can still be computed (`mac_hex` public). Not production-valid after pin.
2. Held `O.__dict__['_grant_verify_secret']`: composition root / ACE.
3. `inspect.stack` / `gc` from a DI collaborator: out of declared threat model; Option E if in-scoped.
4. `run(now=)` remains a public episode clock freeze.
5. Production mint 0 until a later poll-only adapter — fail-closed FACTUAL.
6. Frozen `grant_ok` means `may()` does not re-HMAC; payload dict mutation cannot escalate False→True; bind snapshots latest row (existing TOCTOU model).
7. Public `reason`/`bind_item` fail-closed: callers can still obtain `CognitiveResult`-like tuples only if they use `evaluate_reason` with **forged bindings**. That is not `O.run()`. Do not route production writeback through attacker-supplied binding lists.
8. Reintroducing ContextVar keys, `secret=` on `O`, or `persist(statement=)` under `K_O` reopens C1.

Preserved: trusted runtime clock (`created_at` not grant time); latest-state MAC; sqlite ≠ FACTUAL; revision/supersede grant strip; DERIVED_FACT separation; N-hop; writeback policy; Lane A freeze; soak isolation.

---

## 20. Three layers (do not collapse)

| Layer | Tree | V4 design |
| --- | --- | --- |
| **1 Cryptographic correctness** | HMAC-SHA256 + `compare_digest` + canonical bytes **PASS** | unchanged |
| **2 Authority provenance** | **OPEN** — caller `k` + ContextVar becomes production verifier | **CLOSED** — only `K_O` |
| **3 Secret confidentiality** | **FAIL** — `K_O` copied into ContextVar before `retrieve` | **CLOSED** — instance field + `_permits` only |

V4 is valid only with all three. Layer 1 alone already existed. The rejected ContextVar sketch broke Layer 3 while claiming to fix Layer 2.

---

## 21. Final status matrices

### Current tree (`24b2ab8`) — what the code does

```text
V4_ARCHITECTURE = VALID
V4_SECURITY_REVIEW = PASS
SECRET_BOUNDARY = OPEN
SECRET_NON_OBSERVABILITY = FAIL
AUTHORITY_CONSTRUCTION_BOUNDARY = OPEN
GRANT_ISSUANCE_AUTHORITY = OPEN
ARBITRARY_GRANT_MINTING = OPEN
BOUND_INGEST_CAPABILITY_BOUNDARY = OPEN
ACQUISITION_ADAPTER_BOUNDARY = OPEN
VERIFICATION_CONTEXT_AUTHORITY = CALLER_CONTROLLED
ORCHESTRATOR_AUTHORITY_INJECTION = OPEN
FAKE_ACQUISITION_SUBSTITUTION = OPEN
RETRIEVER_AUTHORITY_ESCALATION = OPEN
MEMORY_AUTHORITY_ESCALATION = OPEN
CONTEXTVAR_AUTHORITY_ESCALATION = OPEN
ISSUER_SUBSTITUTION = OPEN
MULTI_ORCHESTRATOR_ISOLATION = FAIL
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
WRITEBACK_AUTHORITY = OPEN
LANE_A_STATUS = UNTOUCHED
SOAK_STATUS = UNTOUCHED
PRODUCTION_CODE_MODIFIED = NO
TEST_CODE_MODIFIED = NO
IMPLEMENTATION_AUTHORIZED = NO
MERGE = NO
READY_FOR_REVIEW = NO
REPORT = reports/agi_aci_evolution/P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md
```

`V4_ARCHITECTURE` / `V4_SECURITY_REVIEW` in this block are the **design gate** of **this document**, not a claim that the tree is patched. Every other security token above is the **tree**.

`WRITEBACK_AUTHORITY = OPEN` on the tree because FACTUAL can be attacker-granted, which then unlocks reusable writeback. Clock/MAC/sqlite/revision/DERIVED/TOCTOU/N-hop remain as previously proven Hybrid-D consumption properties.

`MULTI_ORCHESTRATOR_ISOLATION = FAIL` because a shared parent ContextVar makes `O2.run` use `O1`’s (or the attacker’s) key.

`MEMORY_AUTHORITY_ESCALATION = OPEN` on the tree only **together with** ContextVar join (store alone still cannot satisfy HMAC under a **non-injected** `K_O`).

### V4 design target (unimplemented)

| Token | Target after a future implementation that matches §18 |
| --- | --- |
| SECRET_BOUNDARY | CLOSED |
| SECRET_NON_OBSERVABILITY | PASS |
| AUTHORITY_CONSTRUCTION_BOUNDARY | CLOSED (objects may exist; not production-valid) |
| GRANT_ISSUANCE_AUTHORITY | CLOSED |
| ARBITRARY_GRANT_MINTING | BLOCKED |
| BOUND_INGEST_CAPABILITY_BOUNDARY | CLOSED (alien MAC) |
| ACQUISITION_ADAPTER_BOUNDARY | CLOSED (no `statement=` mint under `K_O`; mint 0) |
| VERIFICATION_CONTEXT_AUTHORITY | TRUSTED |
| ORCHESTRATOR_AUTHORITY_INJECTION | BLOCKED |
| FAKE_ACQUISITION_SUBSTITUTION | BLOCKED |
| RETRIEVER_AUTHORITY_ESCALATION | BLOCKED |
| MEMORY_AUTHORITY_ESCALATION | BLOCKED |
| CONTEXTVAR_AUTHORITY_ESCALATION | BLOCKED |
| ISSUER_SUBSTITUTION | BLOCKED |
| MULTI_ORCHESTRATOR_ISOLATION | PASS |
| TEST_AUTHORITY_SEPARATION | PASS |
| WRITEBACK_AUTHORITY | BLOCKED without `K_O` MAC |

Those targets are **not** current-tree status.

---

STOP.

No implementation. No production/test/schema/Lane A/soak changes. No merge. Not ready for review. Independent review of this design is required before any implementation authorization.
