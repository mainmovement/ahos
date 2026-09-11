# P5 V4-PIN final residual-boundary review

**Kind:** Design + forensic classification of six LOW residuals. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**IMPLEMENTATION_PERFORMED = NO**

```text
AUDIT_BASELINE = 24b2ab8244f41d9e78582ccfc41dc4b0cf490a83
IMPLEMENTATION_SHA = afdff2539943441244d05478a7004bc4bcc5976f
AUDIT_HEAD = ffde25a8693e9645fa85c9d979bd8771692c1b90
CODE_TREE_CONFIRMED = git diff --stat afdff25..HEAD -- architecture tests  → empty
```

HEAD after later **report-only** commits still has the same production/test Python as `afdff25`. This review re-read that tree. The post-implementation forensic report was treated as an untrusted claim list, not as proof.

Not AGI. Not ACI. Not production-ready. Not live trading. `MERGE = NO`. `READY_FOR_REVIEW = NO`.

---

## Threat model (unchanged)

**Attacker may:** import; construct public classes; compose objects; pass arguments; inspect ordinary attributes; create HMAC keys/authorities/grants; supply `retriever=` / `memory=`; nest orchestrators.

**Attacker may not:** OS/filesystem admin; source modification; debugger/process memory; monkeypatching production source; interpreter compromise.

Holding a legitimate `O` is **composition-root capability**, not a plugin capability. Plugins receive `store`/`task`, not `O`.

---

## Production authority graph (re-traced)

```text
O.__init__: K_O = os.urandom(32); issuer = ISSUER_ID; no **kwargs
O.run(task, now=?)
  ts = now or time.time()          # not CognitiveTask.created_at
  retriever.retrieve(...)          # no ContextVar push
  O._reason_episode
       O._bind_item
            grant_ok = O._permits_observation_grant(...)  # key not a parameter
            assemble_evidence_binding(..., grant_ok=grant_ok)
       evaluate_reason(task, ctx, those bindings)
  writeback: reusable_writeback_permitted(verdict, O._bind_context(...))
             # rebind from store.get, not caller EvidenceBinding
```

`push_grant_verify_context(` call sites: definition + **tests only**.  
`assemble_evidence_binding` production callers: `O._bind_item` (computed `grant_ok`) and public `bind_item` (`grant_ok=False`).

---

## Residual 1 — `assemble_evidence_binding(grant_ok=True)`

### Reachability

Importable from `architecture.cognitive.loop.binding`. Not listed in `architecture.cognitive.loop.__all__`. `__all__` is not a security boundary. Any ordinary importer can call it.

Signature: `grant_ok: bool` is a **caller-supplied flag**. The function does not HMAC, does not read `K_O`, does not call `_permits_observation_grant`.

### What it returns

An in-memory `EvidenceBinding`. `live_grant_ok()` returns that frozen bool. `may(FACTUAL_PREMISE)` for `OBSERVED_FACT` follows `_roles(..., grant_ok=...)`. There is **no** field that marks “constructed by `O`” vs “constructed by caller.”

### Live probe (`/tmp`, this review)

Attacker-minted row (alien HMAC), then:

| Path | `may(FACTUAL_PREMISE)` | Verdict / writeback |
| --- | --- | --- |
| `assemble_evidence_binding(..., grant_ok=True)` | **True** | n/a (DTO) |
| public `bind_item` | **False** | n/a |
| `evaluate_reason([forged])` | uses forged roles | **WEAKLY_SUPPORTED** |
| public `reason()` | fail-closed bind | **INSUFFICIENT_EVIDENCE** |
| production `O.run` | instance verify | **INSUFFICIENT_EVIDENCE**, `reusable_writeback=False`, empty hyp/lesson |
| `CognitiveResult` bindings attr | **absent** | `run` has no `bindings=` |

### Checklist

| Question | Answer |
| --- | --- |
| Ordinary public API? | **Yes** (module import) |
| Authority-bearing? | **Yes for episode roles**; **No** for `ObservationGrant` / `K_O` |
| Create valid production grant? | **No** |
| Cause `FACTUAL_PREMISE` on an object? | **Yes**, on the returned DTO |
| Cause `FACTUAL_PREMISE` inside `O.run`? | **No** |
| Influence `O.run` write-back? | **No** (write-back rebinds via `_permits`) |
| Cross orchestrators? | **No** (ephemeral DTO; no HMAC) |
| Survive canonical mutation as a grant? | N/A — not a grant |
| Bypass latest-state MAC? | **No** for `O.run` (`load_bind_snapshot` + HMAC). Forged DTO skips MAC entirely **outside** `O.run`. |
| Reusable memory via `O.run`? | **No** |
| Indirect semantic change? | Only if a **future** API treats caller bindings as production input |

### Classification

- Current `O.run` invariant: **BOUNDARY-SAFE**
- Public boolean `grant_ok`: **ARCHITECTURALLY-DANGEROUS** as an unauthenticated role constructor
- Future wiring of `evaluate_reason` as a product API: **FUTURE-BYPASS-RISK**, **REGRESSION-PRONE**

This is **not** “merely a data constructor.” It is an **authority-bearing constructor for episode roles** that trusts the caller. It is compatible with V4-PIN **only because** production persistence and `O.run` ignore those objects. It is **not** compatible with a future design that treats `EvidenceBinding.grant_ok` as production truth.

**Decision: `DOCUMENT-AND-TEST`**

Do not treat as harmless hygiene. Document the invariant: *only `O._permits_observation_grant` may set `grant_ok=True` on the production path; public `bind_item`/`reason` stay fail-closed; `evaluate_reason` is not a production authority root.* Future hardening (module-private assembler, or a non-boolean capability) is optional and is **not** required to keep I1–I15. It is **not** `HARDEN-BEFORE-CLOSURE` under the hard-stop list (it does not mint a production-valid grant or rekey `O.run`).

---

## Residual 2 — `O._grant_verify_secret` observability

Python attribute access on a held instance returns `K_O`. Underscore naming is not a control.

### What holding `K_O` allows

With `BoundIngestPort(ObservationAuthority(secret=K_O, issuer_id=ISSUER_ID))`, the **same** instance accepts the grant (isolation probe on this tree). That is minting under the instance’s own key — the definition of genuine authorization.

It does **not** by itself:

- rekey another instance (`K_O1` ≠ `K_O2`; `Grant(O1)→O2` rejected);
- inject ContextVar authority into `O.run` (verify ignores ContextVar);
- let a retriever/memory collaborator that was **not** handed `O` obtain `K_O` (retrieve/get saw ContextVar `None` on production `run`).

### Distinction

| | |
| --- | --- |
| Ordinary attribute access on held `O` | **capability ownership** (composition root already has `O`) |
| Security-boundary compromise for plugins | **No** — plugins are not given `O` |

Correct architectural treatment under the **current** threat model: **acceptable capability ownership**. Opaque wrappers, a separate verifier object, or Option E (process isolation) are **not** required unless the threat model is expanded to “any code that can see `O` is untrusted.” Private-name mangling would be obscurity, not a boundary.

**Classification:** `ARCHITECTURALLY-ACCEPTABLE`, `REGRESSION-RESISTANT` (unless `K_O` is copied into ContextVar/DTOs again).  
**Decision: `KEEP-AS-IS`**

---

## Residual 3 — `push_grant_verify_context`

### Call graph

| Site | Role |
| --- | --- |
| `observation.push_grant_verify_context` | setter |
| `tests/**` | adversarial “must ignore” / leftover `grant_verify_scope` |
| `architecture/cognitive/loop/orchestrator.py` | **does not call** |
| `verify_observation_grant` | `use_key = key`; `if use_key is None: return False` — **no ContextVar read** |
| `binding._trusted_now` | may read `ctx.trusted_now` for public bind **clock only**; public `bind_item` still `grant_ok=False` |

Live probe: ContextVar held attacker key after `push`; `verify(..., key=None)` **False**; `O.run` FACTUAL **False**; ContextVar still attacker key (production did not overwrite with `K_O`).

```text
caller ContextVar ↛ grant verification ↛ FACTUAL_PREMISE in O.run
```

Impossible today because production verify never consumes that ContextVar.

### Future regression

If a later change restores `use_key = key or ctx.key` (the `24b2ab8` C1 join), this API becomes a bypass **without** any new ctor kwarg. **REGRESSION-PRONE**.

**Classification:** current effect `DOCUMENTATION-ONLY` / `BOUNDARY-SAFE`; retention `FUTURE-BYPASS-RISK`.  
**Decision: `DOCUMENT-AND-TEST`**

Invariant to keep tested: *production `O.run` + `push_grant_verify_context(attacker_key)` ⇏ FACTUAL_PREMISE; `verify_observation_grant` ignores ContextVar.*

---

## Residual 4 — `BoundIngestPort`

Ordinary caller **can**:

1. `ObservationAuthority(secret=attacker_key)`
2. `BoundIngestPort(authority)`
3. `AcquisitionRecord(...)`
4. mint an HMAC-valid grant **under that key**
5. `store.remember` via `persist_acquired`
6. submit to production `O`

Step 6 acceptance: **NO**. Production HMAC is `K_O`, not the caller key. Live: `O.run` FACTUAL **False**, writeback **False**.

```text
can mint a grant          = YES (caller-keyed)
can mint a production-authoritative grant = NO
```

`BoundIngestPort` is a minting adapter for **whatever `ObservationAuthority` it is bound to**. Production authority is **acceptance by `O._permits_observation_grant`**, not object construction. Package `__all__` omission is not a block.

Conceptual existence: compatible with Hybrid-D (stored grant is data until instance verify). It is **not** tests-only infrastructure (tests wrap it; production module defines it). It is **not** a current bypass.

**Classification:** `ARCHITECTURALLY-ACCEPTABLE`; **REGRESSION-PRONE** if future code treats “payload has `observation_grant`” as sufficient.  
**Decision: `KEEP-AS-IS`**

Invariant: *caller mint ≠ production FACTUAL; tests must keep BoundIngestPort+`O.run` negative.*

---

## Residual 5 — no production adapter bound to `K_O`

Production `architecture/` has **zero** `BoundIngestPort(` construction sites. Mint in-tree is tests (`TestAcquisitionAdapter`) or caller-constructed ports.

This is **both**:

- **B** — security boundary correctly closed (no public `persist_observed_acquisition(statement=)`, no `O.ingest`, generic adapter refuses `OBSERVED_FACT`);
- **A** — operational acquisition of production `FACTUAL_PREMISE` is **not** wired (ordinary corpus `remember()` stays data).

Not a weakness of V4-PIN verification. It is incomplete **ingestion productization**.

Future adapter contract (not implemented here):

- Constructed only at the composition root that already owns `O` (or a dedicated mint handle derived from `O`, never from caller `secret=`/`issuer=`/`verifier=`/`grant=`).
- Input: typed acquisition results (sensor/channel/raw reading), **not** `statement=` as a public signing oracle.
- Internally maps to `AcquisitionRecord`, mints under `K_O` + `ISSUER_ID`, persists.
- Must not accept caller HMAC material or ContextVar keys.

**Classification:** `ARCHITECTURALLY-ACCEPTABLE` for the security freeze; operational gap deferred.  
**Decision: `DEFER-TO-FUTURE-INGESTION`**

---

## Residual 6 — `run(now=)` episode clock

`ts = time.time() if now is None else now` is passed into `_permits_observation_grant` as `now`. It is **not** `CognitiveTask.created_at`.

| Control | Effect |
| --- | --- |
| `now` vs `observed_at` | future observations rejected (`observed_at > now`) |
| `now` vs `valid_until` | expiry (`valid_until <= now`) |
| HMAC key/issuer | **none** |
| Row `observed_at` / canonical fields | **unchanged** |
| `created_at` far future + `run(now=NOW)` | expired genuine grant stayed **non-factual**, writeback **False** (live) |
| `run(now=NOW-120)` on expired **K_O** grant | temporal window re-opens → FACTUAL + writeback **True** (live, composition-root mint) |

Alien HMAC remains rejected at any `now`. Clock cannot mint or steal `K_O`.

This is **legitimate deterministic episode-clock injection** (replay, tests, frozen episode time), not the closed V3 `created_at` attack. Separating a tests-only clock would be convenience, not a current security requirement.

**Classification:** `ARCHITECTURALLY-ACCEPTABLE` / `BOUNDARY-SAFE` for I12.  
**Decision: `KEEP-AS-IS`**

I12 remains: *caller-controlled **task timestamps** cannot restore expiry.* `run(now=)` is explicitly the trusted episode clock by design.

---

## Future regression analysis

| Residual | Regression class | Accidental bypass pattern | Invariant to document/test |
| --- | --- | --- | --- |
| 1 assemble `grant_ok` | **REGRESSION-PRONE** | New API feeds caller bindings into persist/write-back | `O.run` never accepts bindings; write-back rebinds via `_permits` |
| 2 `_grant_verify_secret` | **REGRESSION-RESISTANT** | Only if copied into ContextVar/DTO/logs | `K_O` not in ContextVar, `CognitiveResult`, retriever args |
| 3 ContextVar setter | **REGRESSION-PRONE** | `verify_observation_grant` reads `ctx.key` again | ContextVar ⇏ production verify |
| 4 `BoundIngestPort` | **REGRESSION-PRONE** | Verify “grant present” without HMAC against `K_O` | HMAC+issuer+latest row required |
| 5 no K_O adapter | **REGRESSION-PRONE** (future ingest) | Adapter takes `secret=`/`statement=` oracle | Adapter bound to `O`, typed acquisition only |
| 6 `run(now=)` | **REGRESSION-RESISTANT** | Using `created_at` as `now` | Episode `ts` ≠ `task.created_at` |

---

## Invariants I1–I15 (this tree)

| ID | Statement | Status | Evidence |
| --- | --- | --- | --- |
| I1 | Production `O` owns `K_O` | **HOLD** | `os.urandom(32)` in `__init__`; not a ctor arg |
| I2 | Production verify uses that `K_O` | **HOLD** | `_permits` → `key=self._grant_verify_secret` |
| I3 | Caller HMAC cannot authorize for `O` | **HOLD** | live `O.run` FACTUAL False |
| I4 | Caller issuer cannot authorize for `O` | **HOLD** | `expected_issuer_id=ISSUER_ID`; mismatch rejected |
| I5 | ContextVar cannot inject production verify | **HOLD** | verify ignores ContextVar; live probe |
| I6 | Retriever cannot inject production verify | **HOLD** | no `K_O` at retrieve; attacker mint rejected |
| I7 | Memory cannot inject production verify | **HOLD** | `get` first ContextVar None; HMAC still `K_O` |
| I8 | Direct SQLite ≠ authoritative | **HOLD** | ungranted/forged MAC rows non-factual |
| I9 | Revision cannot inherit stale authority | **HOLD** | statement revise / supersede pop grant |
| I10 | Cross-orchestrator grants do not transfer | **HOLD** | `Grant(K_O1)→O2` rejected |
| I11 | Canonical mutation invalidates | **HOLD** | field mutations non-factual |
| I12 | Expired grants not restored by **task** timestamps | **HOLD** | `created_at` ignored; `run(now=)` is episode clock |
| I13 | Derived facts ≠ observed-fact authority | **HOLD** | kind check + copied grant rejected |
| I14 | N-hop cannot amplify | **HOLD** | inference episode non-factual; no writeback |
| I15 | Write-back cannot manufacture authority | **HOLD** | attacker path `reusable_writeback=False`; write-back rows have no grant |

No hard-stop exploit path found.

---

## Per-residual decisions

```text
RESIDUAL_1_ASSEMBLE_BINDING = DOCUMENT-AND-TEST
RESIDUAL_2_SECRET_OBSERVABILITY = KEEP-AS-IS
RESIDUAL_3_CONTEXTVAR = DOCUMENT-AND-TEST
RESIDUAL_4_BOUND_INGEST = KEEP-AS-IS
RESIDUAL_5_PRODUCTION_MINT_ADAPTER = DEFER-TO-FUTURE-INGESTION
RESIDUAL_6_EPISODE_CLOCK = KEEP-AS-IS
```

None of the six is a current production `FACTUAL_PREMISE` bypass. Residual 1 is the only one that is **authority-bearing outside `O.run`**. Residuals 1 and 3 are the ones a future developer is most likely to re-link into a bypass. Residual 5 is operational incompleteness, not a hole.

---

## Global decision

```text
P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS
```

Not `CLOSED` (residuals 1/3 remain regression-prone public surfaces).  
Not `REQUIRES_HARDENING` (hard-stop list not met; `O.run` invariant holds).

P5 verification/issuance **security freeze** is closed under the declared threat model. P5 **product** ingestion under `K_O` is not started. Do not call this production-ready.

---

## Required matrix

```text
FINAL_RESIDUAL_REVIEW = PASS

RESIDUAL_1_ASSEMBLE_BINDING = DOCUMENT-AND-TEST
RESIDUAL_2_SECRET_OBSERVABILITY = KEEP-AS-IS
RESIDUAL_3_CONTEXTVAR = DOCUMENT-AND-TEST
RESIDUAL_4_BOUND_INGEST = KEEP-AS-IS
RESIDUAL_5_PRODUCTION_MINT_ADAPTER = DEFER-TO-FUTURE-INGESTION
RESIDUAL_6_EPISODE_CLOCK = KEEP-AS-IS

I1_PRODUCTION_OWNS_KO = HOLD
I2_PRODUCTION_VERIFY_USES_KO = HOLD
I3_CALLER_HMAC_BLOCKED = HOLD
I4_CALLER_ISSUER_BLOCKED = HOLD
I5_CONTEXTVAR_BLOCKED = HOLD
I6_RETRIEVER_BLOCKED = HOLD
I7_MEMORY_BLOCKED = HOLD
I8_SQLITE_BLOCKED = HOLD
I9_REVISION_BLOCKED = HOLD
I10_CROSS_ORCHESTRATOR_BLOCKED = HOLD
I11_CANONICAL_MUTATION_INVALIDATES = HOLD
I12_CLOCK_ATTACK_BLOCKED = HOLD
I13_DERIVED_FACT_SEPARATION = HOLD
I14_N_HOP_BLOCKED = HOLD
I15_WRITEBACK_AUTHORITY_BLOCKED = HOLD

REGRESSION_RISK = PRESENT
TEST_COVERAGE_STATUS = V4_MATRIX_COVERS_O_RUN; RESIDUAL_1_PUBLIC_ASSEMBLER_PARTIAL

P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS

IMPLEMENTATION_PERFORMED = NO
TESTS_MODIFIED = NO
SCHEMAS_MODIFIED = NO
LANE_A_MODIFIED = NO
SOAK_MODIFIED = NO
MERGE = NO
READY_FOR_REVIEW = NO
```

`REGRESSION_RISK = PRESENT` because residuals 1 and 3 can be turned into bypasses by **future** production code, not because they bypass `O.run` now.

---

## Explicit statement

No production code, tests, schemas, Lane A, or soak infrastructure were modified for this review. No implementation commit was created. Temporary probes used `/tmp` only.

STOP. Do not merge. Do not mark Ready for Review.
