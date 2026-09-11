# P5 V3 — test independence and proof-boundary forensic design

**Kind:** Forensic design. Not implementation. Not a test rewrite.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**V3 report:** `reports/agi_aci_evolution/P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md`  
**Implementation SHA:** `e93b3c07d83c4cebb599174fddbd7760b6a82cdd`  
**V3 design SHA:** `c6373aabb1e5fe5623450b3844443784a2664423`

`PRODUCTION_CODE_MODIFIED = NO`  
`TEST_CODE_MODIFIED = NO`  
`IMPLEMENTATION_AUTHORIZED = NO`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
Not AGI, ACI, or production-ready.

---

## 1. Executive conclusion

Current `TEST_INDEPENDENCE = FAIL` is **PROVEN** and precise. It is not “HMAC is mocked.” HMAC is real. The failure is **issuance proof contamination**:

> Tests that claim an ordinary caller cannot mint a process-valid `ObservationGrant` obtain that mint by calling the same production function the forensic attacker used, with a test-chosen `statement`.

`tests/p5_grant_fixtures.persist_authorized` → `persist_observed_acquisition` → `_process_authority()._mint` is **production authority**, not a separate test authority. A tests-only filename does not change the callable.

V3-A (bound ingest + episode clock) remains the right **family**. Independent proofs **can** be constructed. They cannot be constructed from the current fixtures, and they cannot be constructed from V3 §9’s allowance that a tests-only adapter persist a fixture `statement=` into the production signer. That would still be:

```text
test_statement = "anything" → production MAC
```

which proves the signer works, not the acquisition boundary.

**Required refinement (design only):** do not share a process-wide mint singleton with a statement RPC. Bind/verify must use a **composition-root verifier**. Tests that need a valid grant use a **tests-only key and a typed fake acquisition result**, never production `_SECRET` and never `persist_observed_acquisition(statement=…)`. Layer-4 negative tests must not import mint helpers.

This is a test-seam / composition-root clarification, not a new issuer service and not a weakening of Hybrid-D consumption.

`TEST_INDEPENDENCE_ARCHITECTURE = PASS`  
`V3_ARCHITECTURE = REFINEMENT_REQUIRED`

---

## 2. CRITICAL finding reconstruction (test independence)

V3 already noted that `test_no_public_issue_or_grant_mint_export` checks `__all__`. This report traces **every minting test path**.

### 2.1 The contaminated spine (PROVEN)

```text
TEST (many P5 / loop / typed-reasoning tests)
    → TEST_HELPER tests.p5_grant_fixtures.persist_authorized(statement=…)
    → PRODUCTION_PUBLIC_API architecture.cognitive.memory.observation.persist_observed_acquisition
    → PRODUCTION_INTERNAL IngestPort.persist_acquired
    → AUTHORITY_BEARING _process_authority()._mint
    → hmac.new(process _secret, canonical, sha256)
    → STORAGE_ONLY CognitiveMemoryStore.remember(OBSERVED_FACT, payload.observation_grant)
    → PRODUCTION_PUBLIC_API retrieve / bind_item / reason / CognitiveOrchestrator.run
    → CRYPTOGRAPHIC_VERIFIER verify_observation_grant (same process secret)
    → ASSERTION_ONLY may(FACTUAL_PREMISE) / verdict / write-back
```

`authorize_retrieved_items(*RetrievedItem)` is the same spine: it copies `item.statement` into `persist_authorized`.

Eval production modules are a second spine:

```text
TEST test_cognitive_benchmark / test_retrieval_* / test_cognitive_loop.test_*benchmark
    → PRODUCTION_INTERNAL seed_corpus / evaluator / p5_eval / loop.benchmark.run_memory_vs_no_memory
    → persist_observed_acquisition(AcquisitionRecord(statement=…))
    → same _mint
```

### 2.2 Answers to the ten questions

| # | Answer | Evidence |
| --- | --- | --- |
| 1. Which tests mint? | Every caller of `persist_authorized`, `authorize_retrieved_items`, `persist_observed_acquisition`, or `seed_corpus` / eval seeders that take the grant branch. Listed in §3. | call graph |
| 2. Through which callable? | **Production** `persist_observed_acquisition` → `IngestPort.persist_acquired` → `ObservationAuthority._mint`. Not a tests-only signer. | `tests/p5_grant_fixtures.py:39-58`, `observation.py:237-271` |
| 3. Who supplies statement/source/time/entity/scope/provenance? | **The test.** `persist_authorized(store, statement, source_id=, source_type=, observed_at=, domain=, …)`. Entity lives in the statement string. Scope/domain is a kwarg. | `p5_grant_fixtures.py:23-57` |
| 4. May tests invoke production acquisition authority? | **Not as a Layer-4 security proof.** They currently do. Layer-3 may use a **tests-only** compose path, not this RPC. | this design |
| 5. Access `_SECRET`? | **No test file reads `_secret` or `_process_authority`.** They do not need to: they call `_mint` indirectly. Equivalent to using the production key. | grep of `tests/` |
| 6. Fixture construct `BoundIngestPort`? | **NO.** That type does not exist in the tree. Fixtures construct `AcquisitionRecord` and call production persist. | code |
| 7. Fixture construct `_process_authority()`? | **Not directly.** Production persist does. | `observation.py:240` |
| 8. Helper reproduce HMAC? | **NO.** Helpers call production `_mint`. That is worse for independence than a separate test HMAC: it **is** production signing. | fixtures |
| 9. Arbitrary statement → production-valid grant? | **YES.** `persist_authorized(mem, SUPPORT)` or any other string that passes `_validate_acquisition`. **PROVEN** by forensic Attack D and by `test_positive_trusted_acquisition_path`. | |
| 10. Security assert using attacker-forbidden capability? | **YES.** `test_no_public_issue_or_grant_mint_export` **imports** `persist_observed_acquisition` (`test_p5_observation_grant.py:47`) and only asserts it is missing from `__all__`. Positive and mutation tests import `persist_authorized` then assert attackers cannot mint via `remember` — they already minted via persist. | |

`BoundIngestPort` is V3 design, not current code. Current tests cannot construct it because it is absent; they construct something strictly more dangerous: the production persist RPC.

---

## 3. Complete test authority graph

Classifications follow call paths, not names.

### 3.1 Shared nodes

| Symbol | Class |
| --- | --- |
| `CognitiveTask(question=, created_at=)` | UNTRUSTED_TEST_INPUT |
| `SUPPORT` / matrix statements in P5 tests | UNTRUSTED_TEST_INPUT |
| `tests.p5_grant_fixtures.persist_authorized` | TEST_HELPER **and** AUTHORITY_BEARING (wraps production mint) |
| `tests.p5_grant_fixtures.authorize_retrieved_items` | TEST_FIXTURE **and** AUTHORITY_BEARING (for OBSERVED_FACT items) |
| `persist_observed_acquisition` / `IngestPort.persist_acquired` / `_mint` | PRODUCTION_INTERNAL / AUTHORITY_BEARING |
| `CognitiveMemoryStore.remember` without grant | PRODUCTION_PUBLIC_API / STORAGE_ONLY |
| `sqlite3` `_insert_row` | UNTRUSTED_TEST_INPUT / STORAGE_ONLY |
| `ingest_generic_observation` | PRODUCTION_PUBLIC_API |
| `record_world_model_object` | PRODUCTION_PUBLIC_API |
| `verify_observation_grant` | CRYPTOGRAPHIC_VERIFIER |
| `bind_item` / `bind_context` / `reason` / `CognitiveOrchestrator.run` | PRODUCTION_PUBLIC_API |
| `canonical_observation_bytes` / `statement_sha256` | PRODUCTION_INTERNAL (no mint) |
| `ObservationAuthority()` new instance | TEST_HELPER / not process authority |
| `pytest.raises` / `assert not b.may(FACTUAL_PREMISE)` | ASSERTION_ONLY |
| `architecture.cognitive.benchmark.corpus.seed_corpus` | PRODUCTION_INTERNAL / AUTHORITY_BEARING |
| `loop.benchmark.run_memory_vs_no_memory` | PRODUCTION_INTERNAL / AUTHORITY_BEARING |

No node is a `TRUSTED_ACQUISITION_ADAPTER`. Nothing builds an observation from a provider/result object. Every granted row starts as a Python string chosen by the test.

### 3.2 `tests/test_p5_observation_grant.py`

| Test | Path | Independent as claimed? |
| --- | --- | --- |
| `test_no_public_issue_or_grant_mint_export` | imports mint module; `__all__` / `issue` name | **NO** — does not attack persist |
| `test_ordinary_remember_observed_fact_is_not_factual` | `remember` only | **YES** as Layer 2 consumption |
| `test_positive_trusted_acquisition_path` | `persist_authorized(SUPPORT)` | **NO** as acquisition proof; **YES** as “signer + bind work” |
| `test_forged_and_modified_grant_fail` | mint then forge MAC / `remember` forged payload | Layer 2 negative **after** using Layer-3 mint; verifier path real |
| `test_copied_grant_does_not_authorize_other_statement` | mint A, copy grant onto B via `remember` | same |
| `test_replayed_grant_on_mutated_authority_fields` | mint then copy grant | same |
| `test_new_authority_instance_cannot_mint_process_valid_grant` | `ObservationAuthority()._mint` alien MAC + `remember` | **YES** as Layer 2 (alien key); uses `_mint` on **new** instance |
| `test_revision_cannot_inherit_stale_authority` | mint then `revise` | consumption **YES**; mint via persist |
| `test_observation_field_mutations_break_mac` | mint then SQLite UPDATE | consumption **YES** |
| `test_expired_and_future_observation_not_factual` | mint expired/future; `_task(created_at=NOW)`; `run(now=NOW+1)` | clock vs **task** time, not independent of `created_at` |
| `test_timezone_canonical_equivalence` | `canonical_observation_bytes` only | Layer 1-ish, **no mint** |
| `test_unicode_nfc_canonical` | `statement_sha256` only | **no mint** |
| `test_generic_ingestion_cannot_mint_factual` | `ingest_generic_observation` | **YES** Layer 2 |
| `test_world_model_cannot_mint_observed_fact` | `record_world_model_object` | **YES** Layer 2 |
| `test_direct_sqlite_insert_is_not_factual` | `_insert_row` | **YES** Layer 2 |
| `test_direct_sqlite_delete_reinsert_without_grant` | mint, SQL delete+insert without grant | mixed |
| `test_derived_fact_cannot_use_observation_grant` | mint, copy grant onto DERIVED_FACT | mixed |
| `test_non_fact_kinds_cannot_become_factual_via_grant` | mint, copy onto other kinds | mixed |
| `test_stale_and_unknown_not_factual` | mint then STALE; UNKNOWN remember | mixed / remember |
| `test_serialized_grant_without_secret_is_not_authority` | mint, JSON roundtrip grant dict | mixed |
| `test_toctou_revise_after_grant_latest_hash_wins` | mint, revise, `bind_context` | consumption **YES** |
| `test_entity_scope_still_live_after_grant` | mint OTHER entity statement | mixed |

### 3.3 Other test modules that mint

| File | How |
| --- | --- |
| `tests/test_p5_episode_polarity.py` | `_live` → `authorize_retrieved_items`; `_run_orch` → `persist_authorized` |
| `tests/test_p5_negation_entity.py` | `_eval_item` → `authorize_retrieved_items` |
| `tests/test_p5_second_forensic.py` | `_live` / orch setup → `authorize_retrieved_items` / `persist_authorized` |
| `tests/test_typed_reasoning.py` | `persist_authorized` / `authorize_retrieved_items` (lines 142, 334, 410, 503, 620, 656, 692) |
| `tests/test_cognitive_loop.py` | `persist_authorized` (~96); `run_memory_vs_no_memory` → production persist |
| `tests/test_cognitive_benchmark.py` | `seed_corpus` → persist |
| `tests/test_retrieval_relevance.py` | `seed_corpus` |
| `tests/test_retrieval_lookalike.py` | `seed_corpus` |

### 3.4 Tests that do **not** mint (Layer-2-like)

`tests/test_p5_memory_authorization_boundary.py` uses `remember` / propose / accept / bind. Inverted tests expect **no** FACTUAL_PREMISE from remembered OBSERVED_FACT. Those consumption negatives are independent of the persist RPC.

Polarity tests that only `bind_context` on in-memory items **without** store still go through `authorize_retrieved_items` when `_live(..., store)` is used. Direct `bind_context(_ctx(item), task)` without store skips latest-row MAC (grant_ok false unless payload already has a grant). Those are not issuance proofs.

---

## 4. Three authorities (must not be conflated)

### A. Production authority

What production runtime is allowed to use: composition-root `ObservationAuthority` (process `os.urandom` key) + designated acquisition adapter + bind-time verify of **that** key against latest canonical bytes + orchestrator episode `ts`.

Today this is implemented as a **module singleton plus public persist RPC**. That is why A collapsed into a caller-facing signer.

### B. Test authority

A **deliberate** tests-only way to create controlled positive observations for Layer 3 / critic / polarity. Allowed **only** if:

- it does not call production `persist_observed_acquisition`
- it does not read production `_SECRET`
- it does not accept a free-form `statement=` that is copied into the MAC tuple
- Layer 4 modules do not import it

V3 §9’s “fixture statement inside tests” is **B as specified** and is **invalid as an acquisition-boundary proof**. It is a signer smoke test.

### C. Test forgery

Reproducing production MAC with the production key (`hmac.new(_SECRET, …)` or `_process_authority()._mint`). Current `persist_authorized` is **C disguised as B**: it does not copy the algorithm in the test file; it **invokes** production `_mint`. That is forgery-by-delegation.

`ObservationAuthority()._mint` with a **new** random key is not C. Those grants fail process verify. `test_new_authority_instance_cannot_mint_process_valid_grant` is legitimate Layer 2.

---

## 5. Required test hierarchy

### Layer 1 — Pure verifier

**No** production mint, **no** process secret, **no** acquisition adapter, **no** `persist_authorized`.

Inputs: canonical bytes; `ObservationGrant` dicts; MAC under a **published test-vector key** that never appears in production runtime.

Exercises: valid vector; truncated/modified MAC; statement/source/`observed_at`/domain mismatch; expired `valid_until`; future `observed_at`; kind ≠ OBSERVED_FACT.

The verifier answers: is this credential valid **under the supplied key and now**?

Current `test_timezone_canonical_equivalence` / `test_unicode_nfc_canonical` are Layer 1 fragments without MAC. `verify_observation_grant` today **cannot** serve Layer 1: it always uses `_process_authority()` (§7).

### Layer 2 — Production-boundary negatives

Ordinary caller. **Must not import** `p5_grant_fixtures`, `persist_observed_acquisition`, eval seeders, or a tests compose helper.

Attempts: `remember(OBSERVED_FACT, statement=…)`, generic ingest, world-model, `IngestPort()` / persist RPC / `_process_authority()._mint` **as attacks**, sqlite INSERT, `ObservationGrant(...)` with forged MAC, `ObservationAuthority()._mint` alien key, `CognitiveTask.created_at` rewind/advance.

Expected: `CANNOT_OBTAIN_VALID_FACT_AUTHORITY`.

No monkeypatch of `verify_observation_grant`.

Current remember/generic/world-model/sqlite tests already fit **if moved or isolated** so the module does not import mint helpers (today `test_p5_observation_grant.py` imports both).

### Layer 3 — Trusted acquisition positives

```text
UNTRUSTED CALLER
    → cannot pass statement into mint
DESIGNATED ACQUISITION ADAPTER (tests fake provider result, not statement=)
    → builds canonical observation from typed result + fixed template
BoundIngestPort (tests-only key; see §7)
    → persist OBSERVED_FACT + grant
fresh store.get / new orchestrator.run(now=episode_ts)
    → bind(trusted_now=episode_ts)
    → FACTUAL_PREMISE → critic → write-back
```

Forbidden as Layer 3 proof: `persist_authorized(mem, "Retries after timeout reduced failures.")`.

### Layer 4 — Adversarial issuance

Import, construct, call, kwargs, replay, serialize grant, extract objects from `remember`/`run` return values, DI on **public** orchestrator ctor, module globals, env, stale grant, revise, copy grant, copy port if any.

Question: can an ordinary caller turn attacker data into a grant that **this** composition root’s verifier accepts?

If a Layer 4 test imports `persist_authorized`, the answer is predetermined and the proof is invalid.

### Layer 5 — Fresh retrieval / clock

New `CognitiveOrchestrator.run` after persist; bind uses episode `ts`; `created_at` swept independently (§9).

### Layer 6 — Full regression

Existing pytest, Lane A 36/36, no soak fabrication.

---

## 6. Positive-test credentials (Layer 1)

| Option | Security | Realism | Independence | Accidental prod activation | MAC / latest-state / TOCTOU | Complexity |
| --- | --- | --- | --- | --- | --- | --- |
| **A Static precomputed fixtures** | High if key never in production | Low vs process `urandom` | High | Low if vectors live only in `tests/` | MAC yes; latest-state/TOCTOU need a store + **some** key | Low |
| **B Tests-only signer, separate key** | High if key ≠ production | Medium | High vs production `_SECRET` | Low if module is `tests/` only | All three if bind uses **injected** test verifier | Low |
| **C Production test-mode authority** | **Poor** — env/flag can mint in prod | High | Low | **HIGH** | All three | Low, unsafe |
| **D DI verifier + fixture credentials** | High if production default cannot be “skip HMAC” | High if DI is compose-root only | High | Medium if `CognitiveOrchestrator(verifier=)` is public | All three | Medium |

**Rejected:** C (activation risk).  

**Rejected as sole path:** A with current `verify_observation_grant`, because that function ignores fixtures and uses the process singleton — static MACs **will not verify**.

**Selected minimum:** **B + a narrow D seam**.

- Layer 1: published `TEST_VECTOR_SECRET` in `tests/` + `ObservationAuthority(secret=TEST_VECTOR_SECRET)._verify_mac` / a **pure** `verify_grant(grant, fields, now, key)` used by production bind.
- Layer 3: same test vector **or** a per-test key, injected only by `tests/` composition helper; adapter consumes a **typed fake result**.
- Production runtime: `os.urandom(32)`, never `TEST_VECTOR_SECRET`, never `AHOS_TEST_GRANT_KEY`.
- Public `CognitiveOrchestrator.__init__` must **not** take `ingest=` / `verifier=` that let an ordinary caller install a matching mint+verify pair (Attack P). Wiring lives in a composition root. Tests duplicate wiring under `tests/`, not via a production kwarg.

This does **not** implement a second brain. It splits **key ownership** so tests never need production `_SECRET`.

---

## 7. Critical question

**Can a valid production ObservationGrant be created inside a test process without weakening the production threat model?**

**YES, but only as Test Authority B under a test key, or as production compose-root mint that ordinary Layer-4 tests do not hold.**

**NO, not by calling today’s `persist_observed_acquisition`.** That **is** the weakened model: any in-process caller who imports the helper mints process-valid grants. Pytest doing so does not make it “not production.”

If bind continues to use a **process-wide** `_process_authority()` secret, then any in-process mint (including a tests-only wrapper that still calls `_mint`) produces grants that **every** bind in that process accepts. Layer 3 and Layer 4 then share one key. Layer 4 cannot honestly claim it lacks the capability while the helper sits one import away **and** is the same singleton.

Therefore independent positive tests require **one** of:

1. **Per-composition-root verifier** (refinement): Layer 3 injects test key; Layer 4 orchestrator has a different random key and no ingest. Same pytest process, different roots. Ordinary `CognitiveOrchestrator(memory, hyp, ledger)` does not accept an ingest port.
2. **Tests read `_SECRET` and mint** (forgery C): independence **FAIL**.
3. **Keep persist RPC for tests:** independence **FAIL** (current).

Do not hide behind “tests are trusted.” Developers are trusted; **callables** are the boundary.

---

## 8. Attack the V3 design (ordinary application caller)

In scope: public APIs, constructors, DI on public types, factories, defaults, imported symbols, module globals, return values, serialization of **grants**, env/config, revise, sqlite without secret.

Out of scope: OS, FS admin with secret, source edits, debugger, interpreter compromise.

| Attack | V3-A as written | After independence refinement |
| --- | --- | --- |
| `remember(OBSERVED_FACT, statement=)` | BLOCKED at bind | BLOCKED |
| `persist_observed_acquisition` | BLOCKED if removed | BLOCKED |
| `IngestPort().persist_acquired` | BLOCKED if default cannot mint | BLOCKED |
| `_process_authority()._mint` | BLOCKED if getter removed; OPEN as ACE | same |
| `ObservationAuthority()._mint` | alien key, bind fail | same |
| `hmac.new(_SECRET, …)` | out of scope | same |
| Generic / world-model FACT | BLOCKED | BLOCKED |
| sqlite INSERT | BLOCKED at bind | BLOCKED |
| Return value extraction | `MemoryRecord` has grant **data**, not BoundIngestPort | same |
| Serialize grant JSON | data; verify still required | same |
| `CognitiveOrchestrator(ingest=, verifier=)` | **UNRESOLVED in V3 text** — if added as public kwargs, **OPEN** (matching pair = mint) | **must not exist** on public ctor |
| `tests.p5_grant_fixtures` imported from production | must never happen | BLOCKED |
| `seed_corpus` production mint | V3 said inject or ungranted; if default still persist RPC, **OPEN** | default ungranted / injected only from tests compose |
| Env `AHOS_TEST_GRANT_KEY` | not in V3 | **must not exist** (Option C) |
| Adapter `ingest(statement=)` | V3 §6.3 forbids; §9 allowed fixture statement | **§9 invalid**; typed result only |
| Replay grant on other tuple | BLOCKED | BLOCKED |
| Revise inherit | BLOCKED | BLOCKED |
| `created_at` rewind | BLOCKED if bind uses episode `ts` | BLOCKED; tests must prove it (§9) |

V3 does **not** need Option C (separate process). It **does** need the public-ctor / §9 / singleton clarifications or Layer 3/4 proofs collapse again.

---

## 9. Clock tests (must not reintroduce H1)

Current `test_expired_and_future_observation_not_factual`:

- mints with `valid_until=NOW-10` / `observed_at=NOW+5000`
- `_task()` sets `created_at=NOW`
- `orch.run(..., now=NOW+1)`
- bind still uses **`task.created_at`** (production bug)

It does **not** set `created_at` to the past or future. It cannot prove `TASK_METADATA_TIME != FACTUAL_VALIDITY_CLOCK`.

Required Layer 5 contract (design, not implemented):

| Case | `created_at` | episode `ts` (`run(now=)` / bind `now`) | Grant | Expected FACTUAL |
| --- | --- | --- | --- | --- |
| Past task time | NOW-100 | NOW | expired `valid_until=NOW-10` | NO |
| Future task time | NOW+6000 | NOW | expired | NO |
| Past task time | NOW-100 | NOW | valid current | YES (Layer 3 grant) |
| Future task time | NOW+6000 | NOW | valid current | YES |
| Explicit `run(now=NOW)` | arbitrary | NOW | future `observed_at=NOW+5000` | NO |
| Explicit `run(now=NOW)` | arbitrary | NOW | expired | NO |
| Valid current | arbitrary | NOW | unexpired, past `observed_at` | YES |

Invariant: sweeping `CognitiveTask.created_at` must not change grant validity when episode `ts` is fixed.

Residual: `run(now=)` **is** the episode clock (test freeze). That is architecturally identical to production omitting `now` and using `time.time()`. It is not task metadata.

---

## 10. Security-proof requirements

| Security Claim | Attacker Control | Required Capability | Authority Origin | Independent Proof | Invalid Proof |
| --- | --- | --- | --- | --- | --- |
| Ordinary remember is not FACTUAL | statement, kind, payload | none | n/a | Layer 2 `remember` → bind | `persist_authorized` then remember |
| No public mint RPC | import/call persist / IngestPort / `_mint` getter | those callables | production observation.py | Layer 4: call them, bind fail or AttributeError, **module must not be pre-minted** | `__all__` / `hasattr issue` |
| SQLite not FACTUAL | SQL INSERT | FS path | none | Layer 2 sqlite → bind | mint then delete grant only |
| Revision drops authority | `revise(statement=)` | persist of a **Layer 3** row | test compose key | Layer 3 persist + Layer 2 revise + fresh bind | same helper mints the revision |
| Latest-state MAC / TOCTOU | mutate store after grant | Layer 3 grant | test compose | fresh `store.get` / `run` | held `EvidenceBinding.may` only |
| DERIVED_FACT separation | kind label + copied grant dict | none beyond data | n/a | Layer 2 copy grant onto DERIVED | using FACT sibling in same retrieve |
| No arbitrary statement mint | statement/source/time/domain | BoundIngestPort / persist RPC | production | Layer 4 without fixtures | `persist_authorized(statement=)` |
| Acquisition boundary | provider-shaped input | designated adapter | compose root | Layer 3 typed fake result → template → bind | `signer(test_statement)` |
| Task time ≠ grant time | `created_at` | none | episode `ts` | Layer 5 matrix §9 | expiry test with `created_at=NOW` only |
| Forged MAC | grant JSON | none | n/a | Layer 1 vector key or Layer 2 alien Authority | monkeypatch verify |
| N-hop | write-back kinds | loop | n/a | Layer 2/5 hop tests without minting FACT | granting hop artifacts |
| Positive path | fake provider result | Test Authority B | tests compose + test key | Layer 3 | production persist RPC |

---

## 11. Does V3 need an architectural change?

**V3 remains VALID as a family** (Hybrid-D, bound ingest, episode clock, no persist RPC, no separate issuer process).

**V3 needs refinement** before implementation, not a new family:

1. **§9 test adapter must not take `statement=`.** Layer 3 uses a typed acquired result + fixed template. Otherwise GRANT issuance proofs stay signer tests.
2. **No process-wide mint singleton shared with tests.** Bind verifies with a composition-root key. Tests inject a **test vector key** via `tests/` wiring. Public `CognitiveOrchestrator` must not accept a matching ingest+verifier pair.
3. **`verify_observation_grant` must be a pure function of `(grant, fields, now, key)`** (or equivalent) so Layer 1 never calls `_mint` and never uses production `_SECRET`. Production bind supplies the root key.
4. **Eval seeders** default to ungranted data; tests compose injects Test Authority B if a benchmark needs FACTUAL_PREMISE.
5. **Split test modules** so Layer 4 files cannot import `p5_grant_fixtures`.
6. **Clock matrix** in Layer 5 (§9).

These refinements **do not** reopen ordinary-caller mint if persist RPC stays gone and adapters stay non-`statement=`. They make the boundary **provable**.

Without them, a future implementation could delete `issue` from `__all__`, add `TestAcquisitionAdapter(statement=)`, and `TEST_INDEPENDENCE` would remain **FAIL**.

Not insufficient: independent proofs exist (Layers 1–4 with B+D). Not a separate process.

---

## 12. Future test specification (do not implement now)

Layer 1: vector MAC files; no `persist_authorized`.  
Layer 2: remember, ingest, world-model, sqlite, alien `ObservationAuthority`, forged grant JSON; **no** grant fixtures import.  
Layer 3: fake `NormalizedTokenCandidate`-shaped (or software-domain equivalent) result → test adapter template → FACTUAL_PREMISE on fresh `run(now=ts)`.  
Layer 4: persist RPC absent or non-minting; default IngestPort fail-closed; no port on orchestrator return; no env key.  
Layer 5: §9 clock table; TOCTOU revise after Layer 3 persist.  
Layer 6: full pytest; Lane A 36/36; soak untouched.

Existing polarity/critic tests may keep **Test Authority B** once it is a typed adapter, not `persist_authorized`. Until then they are not issuance proofs; they remain critic/polarity proofs **conditional on already-granted rows**.

---

`TEST_INDEPENDENCE_ARCHITECTURE = PASS`

`V3_ARCHITECTURE = REFINEMENT_REQUIRED`

`V3_SECURITY_REVIEW = PASS`

`GRANT_ISSUANCE_AUTHORITY = CLOSED`

`CALLER_CONTROLLED_TIME = CLOSED`

`PRODUCTION_BOUNDARY_PROOF = INDEPENDENT`

`TEST_AUTHORITY_SEPARATION = PASS`

`PRODUCTION_SECRET_EXPOSURE_TO_TESTS = BLOCKED`

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

`REPORT = reports/agi_aci_evolution/P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md`
