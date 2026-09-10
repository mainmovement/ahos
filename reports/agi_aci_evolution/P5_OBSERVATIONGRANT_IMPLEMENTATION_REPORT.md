# P5 ObservationGrant implementation report

**Kind:** Controlled implementation of approved architecture D (Hybrid).  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**AUDITED_SHA:** `38247d172319741f5df7bd6e01ba2817bf211def`  
**DESIGN_COMMIT:** `50cbe7e`  
**V2 report:** `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md`  
**Threat model:** `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_THREAT_MODEL.md`

Not AGI. Not ACI. Not production-ready. Not a new cognitive architecture.  
Lane A and soak were not modified. `P5_FORENSIC_ARCHITECTURE_GATE.md` was not rewritten.

---

## 1. Problem being fixed

An ordinary in-process caller could persist `epistemic_kind=OBSERVED_FACT` through `remember()`, generic adapters, world-model kwargs, or a direct SQLite `INSERT`. Bind then treated that **label** as `FACTUAL_PREMISE` when temporal/applicability/support held.

Storage was write-authority. That is the gap this change closes.

## 2. Approved architecture

**D — Hybrid**, as specified in V2:

- Trusted `ObservationAuthority` mints an `ObservationGrant` MAC.
- Bind-time verification against the **latest** canonical observation is the security boundary.
- SQLite remains untrusted storage. Rows without a valid MAC may exist as data.

No redesign. No second issuer. No new storage engine.

## 3. Exact authority boundary

```text
OBSERVED_FACT
        +
valid ObservationGrant
        +
latest canonical observation
        +
valid MAC
        +
valid temporal state
        +
valid entity/scope
        ↓
FACTUAL_PREMISE
```

Without that chain:

```text
OBSERVED_FACT
        ↓
data only
        ↓
NOT FACTUAL_PREMISE
```

`remember()` may still persist an `OBSERVED_FACT` label. That is not factual consumption authority.

## 4. ObservationGrant design

Frozen dataclass `ObservationGrant` in `architecture/cognitive/memory/observation.py`.

Fields: version, purpose (`FACTUAL_INGEST`), kind (`OBSERVED_FACT` only), statement SHA-256, source_type, source_id, observed_at_us, valid_until (`NONE` or integer µs), domain, issuer_id, mac.

There is **no** trusted `authorized=True` flag. Authority is HMAC-SHA256 verification.

A grant does **not** authorize `DERIVED_FACT`.

## 5. Trusted issuer

`ObservationAuthority` holds a process-lifetime `os.urandom(32)` secret.

There is **no** public `issue(statement=...)`.

Minting is `ObservationAuthority._mint`, called only from `IngestPort.persist_acquired` / `persist_observed_acquisition`.

Those names are **not** exported from `architecture.cognitive`, `architecture.cognitive.memory`, or `architecture.cognitive.loop` `__all__`.

Constructing a **new** `ObservationAuthority()` yields a different secret; those grants fail process verify.

Python import of the observation module can still reach persist. That path **is** the trusted acquisition API, not a generic signing primitive.

## 6. Canonicalization

Deterministic UTF-8 bytes:

```text
AHOS-OG-v1|FACTUAL_INGEST|OBSERVED_FACT|{sha256}|{source_type}|{source_id}|{observed_at_us}|{valid_until}|{domain}|{issuer_id}
```

- Statement: Unicode NFC after **one** `strip()`. No case-fold. SHA-256 of those bytes.
- Times: integer microseconds UTC (`float` unix seconds × 1e6).
- `valid_until`: `NONE` or integer µs. Missing and null are the same token.
- Entity is **not** in the MAC (recomputed live from statement at bind).
- Domain **is** in the MAC.
- JSON object ordering is irrelevant; payload extras are not in the MAC.

Same logical tuple → same bytes. Changed authority-bearing field → different bytes.

## 7. Secret handling

- Process-held `os.urandom(32)`.
- Not hard-coded. Not committed. Not written into this report.
- Not placed in environment by default.
- Not serialized on the grant. Not logged.
- No external secret-management service.

**Operational requirement:** a process restart generates a new secret. Previously persisted grants will fail verify until re-acquired through the trusted persist path. That is accepted under the V2 process-held-secret model.

## 8. Bind-time verification

`bind_item` / `EvidenceBinding.may()`:

1. Load the latest store row when `store` is available (`store.get`). Integrity failure → fail-closed.
2. Reconstruct canonical bytes from **latest** statement, source_type, source_id, observed_at, valid_until, domain, kind.
3. Read grant material from latest payload.
4. HMAC-verify with the process secret (`hmac.compare_digest`).
5. Require grant kind `OBSERVED_FACT` and row kind `OBSERVED_FACT`.
6. Temporal: missing `observed_at`, `observed_at` after task `created_at`, expired `valid_until`, or STALE/SUPERSEDED/ARCHIVED → not `FACTUAL_PREMISE`.
7. Entity/scope remain live `classify_support` / applicability.
8. Only then `may(FACTUAL_PREMISE)`.

`may()` recomputes grant verification from current binding fields. Stored role tuples cannot escalate.

No store and no valid grant → data only.

## 9. Revision behavior

`revise(statement=)` on an authorized observation **strips** `observation_grant` from the new revision payload.

Even if a grant copy remained, bind verifies the latest statement hash; the old MAC cannot authorize the new text.

`supersede` copies the old kind via `remember` but **does not** copy the grant. The successor is a new observation and needs a new grant.

## 10. Generic ingestion behavior

`ingest_generic_observation` (and domain wrappers):

- Default kind is now `INFERENCE` (non-factual).
- Explicit `kind=OBSERVED_FACT` raises `ValueError`.

Legitimate non-factual ingest continues to persist.

## 11. SQLite threat-model handling

SQLite is not cryptographically locked.

An ordinary caller may `INSERT`/`UPDATE`/`DELETE`+reinsert `OBSERVED_FACT` at `store.path`. Those rows may retrieve.

Without a MAC that verifies under the process secret against the latest canonical tuple, they **cannot** become `FACTUAL_PREMISE`.

Integrity-hash can be recomputed by anyone; it is not authority.

## 12. DERIVED_FACT separation

ObservationGrant kind is hard-coded `OBSERVED_FACT`.

`verify_observation_grant` refuses any other `epistemic_kind`, including `DERIVED_FACT`.

Attaching a copied grant to a `DERIVED_FACT` row does not create factual observation authority.

Derived knowledge remains under existing reasoning/write-back rules.

## 13. Test matrix

| Area | Tests | Result |
| --- | --- | --- |
| Direct `remember(OBSERVED_FACT)` | `test_ordinary_remember_observed_fact_is_not_factual`, inverted boundary tests | PASS |
| No public `issue()` | `test_no_public_issue_or_grant_mint_export` | PASS |
| Forged / modified MAC | `test_forged_and_modified_grant_fail` | PASS |
| Copied / replayed grant | `test_copied_grant_does_not_authorize_other_statement`, `test_replayed_grant_on_mutated_authority_fields` | PASS |
| Alien Authority mint | `test_new_authority_instance_cannot_mint_process_valid_grant` | PASS |
| Statement / source / time / domain mutation | grant suite + SQLite UPDATE | PASS |
| Unicode / timezone canonical | `test_unicode_nfc_canonical`, `test_timezone_canonical_equivalence` | PASS |
| Expired / future | `test_expired_and_future_observation_not_factual` | PASS |
| Generic ingest | `test_generic_ingestion_cannot_mint_factual` | PASS |
| World-model | `test_world_model_cannot_mint_observed_fact` | PASS |
| Direct SQLite INSERT / delete-reinsert | `test_direct_sqlite_insert_is_not_factual`, `test_direct_sqlite_delete_reinsert_without_grant` | PASS |
| Serialized grant reuse | `test_serialized_grant_without_secret_is_not_authority` | PASS |
| DERIVED_FACT / HYP/LESSON/INF/PRED/OPINION/SIM | grant suite parametrize | PASS |
| Revision inherit | `test_revision_cannot_inherit_stale_authority` | PASS |
| TOCTOU revise after retrieve | `test_toctou_revise_after_grant_latest_hash_wins` | PASS |
| Existing P5 A–AQ, polarity, hops, critic | `test_p5_second_forensic.py`, polarity, negation | PASS |
| propose / accept | unchanged boundary tests | PASS |

## 14. Positive-path validation

`test_positive_trusted_acquisition_path`:

trusted acquisition → grant → persist → retrieve → bind → `FACTUAL_PREMISE` → legitimate positive verdict.

P3/P5 seeders that represent **legitimate** observations now persist through `persist_observed_acquisition` (corpus, evaluator, p5_eval, loop benchmark, authorized test fixtures). That is required so fail-closed verify does not destroy valid ingestion.

## 15. Full regression results

| Gate | Result |
| --- | --- |
| Focused ObservationGrant + boundary | **51 passed** |
| Focused P5 + loop + memory + retrieval lookalike | **292 passed** |
| Full `pytest tests` | **2008 passed, 3 skipped** |
| Mutation / TOCTOU (second forensic + grant suite) | **PASS** (included in full run) |
| `scripts/validate_imports.py` | **PASS** (232 modules; Lane-A freeze 36 files) |
| `scripts/freeze_lane_a.py` | **Lane-A integrity OK (36 files pinned)** |
| Soak paths | **no diff** |

`.pytest_cache` was removed before import validation. `validate_imports` side-effect report files were restored and not committed.

## 16. Changed files

All classified **REQUIRED FOR P5 AUTHORIZATION BOUNDARY**:

| File | Why |
| --- | --- |
| `architecture/cognitive/memory/observation.py` | Grant, authority, canonical bytes, persist, verify |
| `architecture/cognitive/loop/binding.py` | Bind-time latest-row MAC + live `may()` |
| `architecture/cognitive/memory/store.py` | Revise/supersede grant invalidation; world-model refuse FACT |
| `architecture/cognitive/loop/adapters.py` | Strip generic FACT mint |
| `architecture/cognitive/loop/benchmark.py` | Trusted ingest for legitimate benchmark observation |
| `architecture/cognitive/benchmark/corpus.py` | Authorized OBSERVED_FACT seeds |
| `architecture/cognitive/benchmark/evaluator.py` | Authorized eval seeds |
| `architecture/cognitive/benchmark/p5_eval.py` | Authorized P5 eval observations |
| `tests/p5_grant_fixtures.py` | Test-only trusted persist helpers |
| `tests/test_p5_observation_grant.py` | Adversarial + positive proofs |
| `tests/test_p5_memory_authorization_boundary.py` | Invert ungranted remember→FACT gap |
| `tests/test_p5_*` / `test_typed_reasoning.py` / `test_cognitive_loop.py` | Seed legitimate facts through trusted ingest |

**UNRELATED:** none. `next-env.d.ts` and `reports/PRE_SOAK_STATUS.txt` remain untracked and uncommitted.

## 17. Scope audit

```text
git diff --stat f50cba4
16 files changed
```

- Lane A (`discovery/**`, `paper_trading/**`): **untouched**
- Soak evidence / soak DB: **untouched**
- `P5_FORENSIC_ARCHITECTURE_GATE.md`: **untouched**
- Retrieval ranking (P4.3): **untouched**
- `propose` / `accept`: **untouched**
- No autonomous behavior. No real trading. No AGI/ACI features.

## 18. Remaining limitations

In scope and accepted by the threat model:

- Direct SQLite rows **may exist** as `OBSERVED_FACT` data.
- Process restart rotates the secret; old grants fail until re-acquired.
- A caller who imports and uses `persist_observed_acquisition` **is** using the trusted issuer.
- `remember()` still stores the label.

Out of scope (not claimed):

- Filesystem administrator who also possesses the process secret.
- Patching `bind_item` / the verifier inside the trusted process.
- Database tamper-proofing, OS lockdown, or globally secure deployment.

## 19. Security claims

Under the defined AHOS threat model, factual authority is no longer created merely by storing an OBSERVED_FACT label. Factual consumption requires successful bind-time verification of a valid ObservationGrant against the latest canonical observation, with temporal and scope constraints, while alternate ingestion paths cannot mint factual authority without the trusted observation boundary.

This is proven by the test matrix in §13–§15.

## 20. Non-claims

This work does **not** claim:

- AGI
- ACI
- autonomous cognition
- production-ready
- globally secure
- database tamper-proof
- filesystem-admin resistant
- cryptographically unbreakable

---

## Final security proofs (mandatory)

### A. Ordinary `remember(OBSERVED_FACT)` → fresh reasoning task

`test_ordinary_remember_observed_fact_is_not_factual`  
`test_consumption_remembered_observed_fact_is_factual_premise` (inverted)

```text
OBSERVED_FACT row
→ grant verification FAIL
→ not FACTUAL_PREMISE
→ no positive factual support
→ no reusable factual escalation
```

### B. Direct SQLite INSERT

`test_direct_sqlite_insert_is_not_factual`

```text
direct SQLite INSERT
→ OBSERVED_FACT row
→ bind-time verification FAIL
→ not FACTUAL_PREMISE
```

### C. Revision cannot inherit authority

`test_revision_cannot_inherit_stale_authority`

```text
valid observation A
→ revise to B
→ old grant verification FAIL
→ no inherited authority
```

---

## Regression gates

| Gate | Status |
| --- | --- |
| A Direct OBSERVED_FACT bypass | CLOSED |
| B Arbitrary grant minting | CLOSED |
| C Latest-statement MAC | ENFORCED |
| D Revision stale authority | CLOSED |
| E Generic ingest fact mint | CLOSED |
| F World-model fact mint | CLOSED |
| G Direct SQLite without grant | CLOSED for FACTUAL_PREMISE |
| H DERIVED_FACT separate | PASS |
| I propose()/accept() | SAFE (unchanged) |
| J Two-hop / three-hop | PASS |
| K TOCTOU | PASS |
| L Legitimate trusted observations | PASS |
| M Lane A | UNCHANGED 36/36 |
| N Soak | UNTOUCHED |

---

`IMPLEMENTATION_STATUS = PASS`

`SECURITY_BOUNDARY = BIND_TIME_OBSERVATION_GRANT_VERIFICATION`

`OBSERVATION_GRANT_SCOPE = OBSERVED_FACT_ONLY`

`ARBITRARY_GRANT_MINTING = BLOCKED`

`DIRECT_SQLITE_FACT_ESCALATION = BLOCKED`

`REVISION_AUTHORITY_REUSE = BLOCKED`

`GENERIC_INGEST_FACT_ESCALATION = BLOCKED`

`WORLD_MODEL_FACT_ESCALATION = BLOCKED`

`DERIVED_FACT_SEPARATION = PASS`

`PROPOSE_ACCEPT_FACTIFICATION = SAFE`

`TOCTOU = PASS`

`POSITIVE_PATH = PASS`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`IMPLEMENTATION_AUTHORIZED = YES`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`REPORT = reports/agi_aci_evolution/P5_OBSERVATIONGRANT_IMPLEMENTATION_REPORT.md`
