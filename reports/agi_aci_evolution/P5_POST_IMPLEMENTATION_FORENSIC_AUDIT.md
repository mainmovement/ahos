# P5 ObservationGrant — post-implementation forensic audit

**Kind:** Independent post-implementation forensic audit. Not a fix. Not a redesign.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**Previous implementation report:** `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_IMPLEMENTATION_REPORT.md` (`IMPLEMENTATION_STATUS = PASS` is **not** trusted here)  
**Approved architecture:** Hybrid-D — `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md`  
**Threat model:** `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_THREAT_MODEL.md`

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
Not AGI, ACI, entailment, production-ready, or globally secure.

Production code and tests were **not** modified in this audit. Existing tests were executed. Additional in-process probes wrote only under `/tmp`.

---

## 1. Executive conclusion

Bind-time MAC verification against the latest store row **does** stop the originally proven bypasses:

- ordinary `remember(OBSERVED_FACT)`
- direct SQLite `INSERT`/`UPDATE` without a process-valid MAC
- `revise(statement=)` inheritance of an old grant
- generic ingest / world-model FACT mint
- `DERIVED_FACT` + copied grant
- `propose()` / `accept()` factification

Those paths were re-executed. They do **not** yield `FACTUAL_PREMISE`.

The implementation nevertheless **fails** Hybrid-D as specified.

**CRITICAL (PROVEN):** `persist_observed_acquisition` / `IngestPort.persist_acquired` / `_process_authority()._mint` are ordinary in-process callables in a production module. An attacker who imports them can supply an arbitrary `AcquisitionRecord.statement` and obtain a process-valid grant, then `FACTUAL_PREMISE`, a positive verdict, and reusable write-back. That is a free-form “sign this claim” mint. V2 required minting to be a composition-root closure and a **tests-only** `TestIngestPort`, not a production helper. Python import is not a security boundary (V2 §5, this audit’s rules).

**HIGH (PROVEN):** Bind-time `now` is `CognitiveTask.created_at`, which the caller sets. A still-cryptographically-valid grant that is expired at episode time becomes `FACTUAL_PREMISE` if `created_at` is rewound. A future `observed_at` becomes `FACTUAL_PREMISE` if `created_at` is advanced. `CognitiveOrchestrator.run(now=…)` does **not** drive this clock.

The implementation report’s `ARBITRARY_GRANT_MINTING = BLOCKED` is **DISPROVEN**. Its test only asserts that a function named `issue` is absent from package `__all__`.

`FORENSIC_STATUS = FAIL`

---

## 2. Exact audited SHA

| Item | Value |
| --- | --- |
| **Audited implementation SHA** | `e93b3c07d83c4cebb599174fddbd7760b6a82cdd` |
| **Forensic report commit / HEAD** | `48693caced74865805b0620411a0b703239eb7cb` |
| PR branch | `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| Merge-base with `origin/main` / base SHA | `976516123b0b682e99fcc6e9c6f0efabb91a9495` |
| Previous memory-authorization audit pin | `38247d172319741f5df7bd6e01ba2817bf211def` |
| Architecture design commit | `50cbe7e01b8583aae85eccb7b230c3ca787919d1` |
| V2 architecture commit | `f50cba4ec16f9ed7b1337f79e96aaf94daecc8e1` |
| Implementation code commit | `730b354141917c15914ce751a3840572345aac05` |
| Seeder follow-up commit | `4f9cd000ee6129bae59d6a6a4a59fb6d8c8f3887` |
| Implementation report commit | `e93b3c07d83c4cebb599174fddbd7760b6a82cdd` |

Implementation files (vs V2 `f50cba4`):

`architecture/cognitive/memory/observation.py`, `loop/binding.py`, `memory/store.py`, `loop/adapters.py`, `loop/benchmark.py`, `benchmark/corpus.py`, `benchmark/evaluator.py`, `benchmark/p5_eval.py`, tests listed in §31, and the implementation report.

---

## 3. Architecture compliance matrix

Against `P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md`. Judged by behavior, not names.

| V2 requirement | Class | Evidence |
| --- | --- | --- |
| Bind verifies HMAC over **latest** canonical OBSERVED_FACT | **IMPLEMENTED EXACTLY** | `bind_item` → `store.get`; MAC over latest fields |
| No trusted `authorized=True` flag | **IMPLEMENTED EXACTLY** | grant dict has no such field; `may()` recomputes |
| Fail-closed: no grant / bad MAC → not FACTUAL_PREMISE | **IMPLEMENTED EXACTLY** | probes A/B/C/E/F/G |
| Grant kind OBSERVED_FACT only | **IMPLEMENTED EXACTLY** | `GRANT_KIND`; `verify_observation_grant` rejects other kinds |
| Canonical `AHOS-OG-v1\|FACTUAL_INGEST\|…` NFC+strip, µs, `NONE` | **IMPLEMENTED EXACTLY** | `canonical_observation_bytes` |
| HMAC-SHA256 + `compare_digest` | **IMPLEMENTED EXACTLY** | `ObservationAuthority._mac_hex` / `_verify_mac` |
| Process `os.urandom(32)` secret; new Authority ≠ process secret | **IMPLEMENTED EXACTLY** | probe 8 |
| `remember` may persist OBSERVED_FACT as data | **IMPLEMENTED EXACTLY** | probe 6 |
| SQLite row without MAC is data, not FACTUAL | **IMPLEMENTED EXACTLY** | probe sqlite INSERT |
| `revise(statement=)` invalidates / bind vs latest hash | **IMPLEMENTED EXACTLY** | payload strip + hash mismatch |
| `record_world_model_object` refuse OBSERVED_FACT | **IMPLEMENTED EXACTLY** | raises `ValueError` |
| `ingest_generic_observation` strip FACT | **IMPLEMENTED EXACTLY** | default INFERENCE; explicit FACT raises |
| `propose` / `accept` unchanged, no FACT | **IMPLEMENTED EXACTLY** | JSONL-only propose; accept veto |
| Entity not in MAC; live support at bind | **IMPLEMENTED EXACTLY** | domain in MAC; entity from statement |
| `issue(statement=…)` must not exist as ordinary public function | **IMPLEMENTED DIFFERENTLY** | no `issue()` **name**; `persist_observed_acquisition(AcquisitionRecord(statement=…))` is the same capability |
| Mint is closure in composition-root Authority; adapters get injected IngestPort | **CONTRADICTED** | no injection; production free functions mint |
| Tests-only `TestIngestPort`; not in `architecture.cognitive.__init__` | **CONTRADICTED** | production `IngestPort` + `persist_observed_acquisition`; eval modules call them |
| Ordinary caller cannot call `_mint` without root instance | **CONTRADICTED** | `_process_authority()._mint` and persist wrappers are importable |
| Public API exports IngestPort **protocol** and verify, not mint | **MISSING** / **CONTRADICTED** | protocol unused; concrete `IngestPort` and persist are mint |
| Temporal `valid_until` / future `observed_at` vs **now** | **IMPLEMENTED DIFFERENTLY** | `now` = `task.created_at` (caller-controlled), not orchestrator `now` / wall clock |
| Persist uniqueness `(statement_sha256, source_id, observed_at, kind)` | **MISSING** | second persist of same tuple creates another granted row (not an escalation) |
| Benchmark seeders: TestIngestPort, not prod mint | **IMPLEMENTED DIFFERENTLY** | corpus/evaluator/p5_eval/loop.benchmark mint in production tree |

---

## 4. Complete OBSERVED_FACT write-surface

Search: `architecture/**`, `scripts/**`, constructors, `INSERT INTO memories`, `remember`, revise/supersede, adapters, consolidation, world-model, eval seeders. Cognitive `INSERT INTO memories` exists only in `store.py`.

| Path | Create OBSERVED_FACT | Create authority | Preserve old authority | Bypass grant |
| --- | --- | --- | --- | --- |
| `CognitiveMemoryStore.remember` | **YES** (caller kind) | **NO** at bind | n/a | **NO** (data only) |
| `revise(statement=)` | no new kind; keeps label | **NO** | **NO** (strip + hash) | **NO** |
| `supersede` | **YES** (copies kind, strips grant) | **NO** | **NO** | **NO** |
| `record_failure` | kind YES + type FAILURE | **NO** (typed_class FAILURE) | n/a | **NO** |
| `record_world_model_object` | **NO** (raises) | **NO** | n/a | **NO** |
| `ingest_generic_observation` / domain wrappers | **NO** (raises if FACT; default INFERENCE) | **NO** | n/a | **NO** |
| `persist_observed_acquisition` / `IngestPort.persist_acquired` | **YES** | **YES** | n/a | **N/A — this IS mint** |
| `ObservationAuthority._mint` via `_process_authority()` | grant material | **YES** | n/a | **N/A — this IS mint** |
| `ConsolidationGate.accept` | **NO** (raises) | **NO** | n/a | **NO** |
| `HypothesisStore.propose` | **NO** (JSONL; retriever empty) | **NO** | n/a | **NO** |
| Orchestrator write-back | HYP/LESSON/INFERENCE only | **NO** | n/a | **NO** |
| corpus / evaluator / p5_eval / loop.benchmark | **YES** via persist | **YES** | n/a | eval mint in prod tree |
| `sqlite3.connect(store.path)` INSERT/UPDATE | **YES** as data | **NO** without process MAC | UPDATE statement **NO** | **NO** for FACTUAL_PREMISE |
| JSON/pickle MemoryRecord | no cognitive loader found | **NO** | reconstructed grant still needs process MAC | **NO** |
| Other SQLite engines (knowledge, scheduler, paper positions) | other schemas | **NO** P5 retrieve | n/a | **NO** |
| Lane A / soak DBs | forbidden names | **NO** | n/a | **NO** |

---

## 5. Grant issuer audit

**PROVEN reachable mint:**

```text
from architecture.cognitive.memory.observation import (
    persist_observed_acquisition, AcquisitionRecord, IngestPort, _process_authority,
)
persist_observed_acquisition(store, AcquisitionRecord(statement=<arbitrary>, ...))
```

Probe 1 (`/tmp/og_forensic_probe.py`): arbitrary `SUPPORT` statement → `may(FACTUAL_PREMISE)=True`, verdict `WEAKLY_SUPPORTED`, `reusable_writeback_permitted=True`.

Also **PROVEN**:

- `IngestPort().persist_acquired` mints with the **process** secret (not a new Authority).
- `_process_authority()._secret` is a readable `bytes` of length 32.
- `_process_authority()._mint(acq)` returns a 64-hex MAC.
- `ObservationAuthority()` without the leaked secret produces a **different** secret; those MACs fail process verify (**PROVEN** probe 8; matches V2 §5.5).
- No function named `issue` on packages or `ObservationAuthority` (**PROVEN** `test_no_public_issue_or_grant_mint_export`).
- Not in `architecture.cognitive` / `.memory` / `.loop` `__all__`. Absence from `__all__` is **not** a boundary.

V2 remaining hole (“leaked singleton / debugger”) is out of ordinary-API scope. This mint does **not** require reading `_secret`: the public persist function calls `_mint` internally. That is **not** the documented residual hole. It is an ordinary import of a production helper.

`AcquisitionRecord.statement` is an unconstrained string. Source, timestamps, domain, and entity-bearing text are caller-chosen. That **is** “sign arbitrary statement”.

**Attack D result: OPEN**, not BLOCKED.

---

## 6. MAC audit

| Item | Actual |
| --- | --- |
| Algorithm | HMAC-SHA256 |
| Key | process `os.urandom(32)` singleton |
| Canonicalization | NFC + one `strip`; SHA-256 of statement; integer µs; `valid_until` `NONE` or int; `\|`-separated |
| Compare | `hmac.compare_digest`; length mismatch → `False` (caught) |
| Failure | return `False` → roles omit FACTUAL_PREMISE (fail-closed, not crash) |
| Serialization | grant dict in `payload_json`; secret never serialized |

Attacks (existing tests + probes):

| Attack | Result |
| --- | --- |
| Forged / modified MAC | **FAIL-CLOSED** |
| Truncated MAC | **FAIL-CLOSED** (`compare_digest` / parse) |
| Copied MAC onto other statement | **FAIL-CLOSED** |
| MAC from other source / domain / time / validity | **FAIL-CLOSED** |
| Alien `ObservationAuthority` MAC | **FAIL-CLOSED** |

No claim of cryptographic unbreakability. SHA-256-HMAC is standard. Security reduces to **who can mint under the process key**.

---

## 7. Latest-state verification

`bind_item` loads `store.get(memory_id)` (latest revision) and verifies MAC over **those** fields, not the RetrievedItem copy.

**PROVEN** (`test_toctou_revise_after_grant_latest_hash_wins`, probe 5 rebind): authorize A → persist → retrieve → revise A→B → bind → **not** FACTUAL_PREMISE.

`EvidenceBinding.may()` / `live_grant_ok()` recompute from **binding fields**, not from a stored bool. They do **not** re-query SQLite. A **held** binding object remains FACTUAL after a later store revise (**PROVEN** probe 5). Production `reason()` binds inside the call; production orchestrator **rebinds** before write-back (**PROVEN** probe 4: fresh `orch.run` after revise → `INSUFFICIENT_EVIDENCE`, no HYP/LESSON).

`LATEST_STATE_MAC_VERIFICATION = PASS` for bind/orchestrator consumption of latest row. Held-DTO snapshot is a **MEDIUM** robustness note, not a production write-back bypass.

---

## 8. Revision audit

`revise(statement=)` copies the row, strips `observation_grant` when the statement changes, recomputes integrity hash.

Bind against latest statement vs old MAC → fail.

`revise` cannot set source / domain / observed_at / valid_until (API). SQLite UPDATE of those fields while keeping the grant fails MAC (**PROVEN** grant mutation tests / sqlite statement UPDATE probe).

Status-only revise (STALE) keeps grant material; STALE is denied FACTUAL by verify + roles (**PROVEN**).

`REVISION_AUTHORITY_REUSE = BLOCKED` for the latest-row bind path.

---

## 9. Direct SQLite audit

`store.path` is public. `sqlite3.connect` INSERT of OBSERVED_FACT with a valid **integrity** hash (not a secret) retrieves.

Probe: INSERT `SQL1` OBSERVED_FACT without grant → retrieved kind OBSERVED_FACT, `may(FACTUAL_PREMISE)=False`, verdict `INSUFFICIENT_EVIDENCE`.

UPDATE statement keeping grant → not FACTUAL. DELETE+reinsert without grant → not FACTUAL (`test_direct_sqlite_delete_reinsert_without_grant`).

Database does **not** reject the write. Consumption rejects authority. Matches Hybrid-D.

`DIRECT_SQLITE_ESCALATION = BLOCKED`

---

## 10. Alternate ingestion audit

| API | OBSERVED_FACT accepted? | Grant required for FACTUAL? | Kind selectable? | Reach issuer? |
| --- | --- | --- | --- | --- |
| `remember` | YES as data | YES at bind; ungranted → no FACTUAL | YES | NO |
| `ingest_generic_observation` | NO (raises) | n/a | non-FACT only | error text **names** persist helper; does not call it |
| domain wrappers | same | same | same | same |
| `record_world_model_object` | NO (raises) | n/a | non-FACT | NO |
| `persist_observed_acquisition` | YES | mints grant | forced OBSERVED_FACT | **YES** |
| corpus/eval/benchmark | YES via persist | minted | OBSERVED_FACT seeds | **YES** (eval) |

Generic ingest without valid authority: **BLOCKED**.

---

## 11. DERIVED_FACT separation

Isolated store: `DERIVED_FACT` row carrying a copied ObservationGrant → `live_typed_class=DERIVED_FACT`, `may(FACTUAL_PREMISE)=False`, verdict `INSUFFICIENT_EVIDENCE` (**PROVEN** probe 3). Prior mixed-store probe was contaminated by a sibling granted OBSERVED_FACT — not a derived-role bypass.

`verify_observation_grant` requires `epistemic_kind == OBSERVED_FACT`. Relabel would need a new persist/remember as OBSERVED_FACT; remember-without-grant still fails bind; persist-with-grant is the mint finding, not DERIVED_FACT confusion.

`DERIVED_FACT_SEPARATION = PASS`

---

## 12. propose / accept audit

`HypothesisStore.propose` appends JSONL. `MemoryRetriever.retrieve` on an empty memory after propose → `[]` (**PROVEN**).

`ConsolidationGate.accept(..., OBSERVED_FACT)` raises `EpistemicViolation` (**PROVEN**). LESSON accept still works and is not FACTUAL_PREMISE (existing boundary tests).

Independent verification agrees with prior `PROPOSE_ACCEPT_FACTIFICATION = SAFE`. Not modified.

---

## 13. Provenance audit

Trusted persist **rejects** UNKNOWN `source_type` / `source_id` / domain (**PROVEN**).

`remember(OBSERVED_FACT, source_id=UNKNOWN)` **persists** (**PROVEN**). Bind: UNKNOWN source → not FACTUAL even if a grant were present (`_unknown_token` in verify).

Non-factual UNKNOWN provenance remains usable via `remember` of INFERENCE/HYP/etc. (existing store tests).

SQLite change of source on a granted row fails MAC (source in canonical bytes).

---

## 14. Temporal audit

| Case | Bind result |
| --- | --- |
| `valid_until` < `task.created_at` | not FACTUAL (**PROVEN** tests + probe 3 at `created_at=NOW`) |
| `observed_at` > `task.created_at` | not FACTUAL (**PROVEN**) |
| Newly inserted old `observed_at` with valid grant and unexpired `valid_until` | DATED + FACTUAL if grant verifies (intended; DATED ≠ CURRENT) |
| Timezone: same unix instant, different offsets | identical canonical bytes (**PROVEN** `test_timezone_canonical_equivalence`) |
| Orchestrator `run(now=far_future)` with `task.created_at=NOW` on expired grant | still not FACTUAL (**PROVEN** probe 3) |
| **Caller sets `task.created_at = NOW-100` on expired grant** | **FACTUAL + WEAKLY_SUPPORTED** (**PROVEN** probe 3) |
| **Caller sets `task.created_at = NOW+6000` on future `observed_at`** | **FACTUAL + WEAKLY_SUPPORTED** (**PROVEN** probe 4) |

V2: expired / future observations must not become current factual premises merely because they were inserted or reloaded recently. The check uses an **attacker-controlled task clock**, not episode `now`. That **weakens** temporal authority (**HIGH**).

Malformed timestamps: `float()` / `int(round(...))` throw or coerce; uncaught exceptions fail the call (not fail-open to stored roles). **UNRESOLVED** as a dedicated malformed-timestamp suite (no existing test).

---

## 15. Entity / scope audit

Entity is not a grant field. Changing entity requires changing statement → hash/MAC fail, or live `classify_support` mismatch.

`grant` for “Service A …” vs task “Service B …” → not positive (`test_entity_scope_still_live_after_grant`, P5 negation/entity suite).

Domain is in the MAC. Domain mismatch → applicability `NOT_APPLICABLE` → no FACTUAL_PREMISE (existing `test_ao_task_domain_mismatch` after authorized seed).

Unscoped observation vs entity-specific task: live entity alignment; no payload entity override. **PROVEN** by existing P5 entity tests (authorized fixtures).

---

## 16. Canonicalization audit

| Variation | Behavior |
| --- | --- |
| Leading/trailing whitespace | stripped; equivalent (**PROVEN**) |
| Unicode NFC vs NFD | equivalent SHA (**PROVEN**) |
| Case (`Cafe` vs `cafe`) | **different** hash; not equivalent (**PROVEN**) |
| Internal whitespace | different |
| JSON key order | not in MAC |
| `valid_until` null vs missing | both `NONE` |
| Timestamp float → µs round | same instant → same bytes |
| Timezone representation | unix seconds; offset-normalized equal (**PROVEN**) |
| Entity/scope | via statement + domain strings |

Does not accept modified authority-bearing observations as the same grant. May reject legitimate case-only variants (strict; **LOW**, not a bypass).

---

## 17. Replay audit

| Replay | Classification |
| --- | --- |
| Valid grant A on unchanged observation A (same process) | **SAFE REUSE** (V2: no nonce; identical tuple is not escalation) |
| Grant A on observation B | **UNAUTHORIZED REUSE blocked** |
| Grant A on revised A' | **UNAUTHORIZED REUSE blocked** |
| Grant A on different source/domain/time | **UNAUTHORIZED REUSE blocked** |
| Second persist of identical tuple | new row, new persist, same MAC content; **SAFE REUSE**, uniqueness **MISSING** (not authority widening) |

---

## 18. Serialization audit

Grant JSON in SQLite payload **survives persistence**. Authority still requires process HMAC verify against latest bytes.

Copying serialized grant onto a **different** statement fails (**PROVEN** `test_serialized_grant_without_secret_is_not_authority`).

Process restart: new `os.urandom` secret → old grants fail verify. **PROVEN by code**; not process-restarted in this audit (**UNRESOLVED** as live restart, **PROVEN** as design).

No cognitive import/export loader found.

---

## 19. TOCTOU audit

| Attack | Result |
| --- | --- |
| 1 retrieve → mutate store → bind | **PASS** (latest MAC fail) |
| 2 bind/reason as one `reason()` call, then later mutate | next `reason()`/`orch.run` rebinds; **PASS** on production path |
| 2 held binding after mutate | `may()` still True on snapshot (**PROVEN**); not used by orchestrator write-back |
| 3 authorize → revise → write-back | orch rebind; no HYP/LESSON (**PROVEN** probe 4) |
| 4 mutate copied metadata on frozen binding | `may()` live recompute; existing mutation tests **PASS** |

`TOCTOU = PASS` for production retrieve/bind/orchestrator. Snapshot `may()` without store re-fetch is **MEDIUM**, not a HIGH write-back bypass.

---

## 20. Write-back audit

Ungranted `remember(OBSERVED_FACT)` → not FACTUAL → `reusable_writeback_permitted=False` → no HYP/LESSON/INFERENCE mint (**PROVEN** probe 6 + inverted boundary tests).

Granted arbitrary persist (the mint finding) **can** write back. That is mint success, not critic override of **invalid** evidence.

Orchestrator write-back kinds remain HYP/LESSON/INFERENCE, never OBSERVED_FACT (**PROVEN** source + hop tests).

`WRITEBACK_AUTHORITY = PASS` for **invalid** factual evidence. Reusable write-back from **arbitrarily minted** grants is the CRITICAL mint finding.

---

## 21. Critic audit

Existing P5 critic/polarity/uncertainty/scope/entity/temporal/contradiction/stale/mixed/downgrade/REQUIRE_MORE/CONTEST/REFUSE tests: **239 passed** in the focused P5+grant run (includes second forensic A–AQ).

Critic cannot restore FACTUAL_PREMISE: roles come from live grant verify. Mixed polarity still fail-closed at episode. Kill-class downgrade still INSUFFICIENT.

No critic override of missing/invalid grant was found.

---

## 22. N-hop audit

Existing `test_two_hop_unresolved_episode_cannot_become_fact` and `test_three_hop_derived_artifact_cannot_escalate_authority`: **PASS**.

HYP/LESSON/INFERENCE/EPISODIC INFERENCE cannot bind as FACTUAL_PREMISE. UNKNOWN remember is data. DERIVED_FACT cannot.

No hop chain manufactures observation authority without the mint helper.

`N_HOP_ESCALATION = BLOCKED`

---

## 23. Public API audit

| Callable | Verdict |
| --- | --- |
| `CognitiveMemoryStore.remember` | **SAFE** (data; bind fail-closed) |
| `revise` / `supersede` / `apply_decay` / `contradict` | **SAFE** for FACTUAL |
| `record_failure` | **SAFE** (FAILURE wins) |
| `record_world_model_object` | **SAFE** (refuses FACT) |
| `ingest_generic_observation` + wrappers | **SAFE** (refuses FACT) |
| `HypothesisStore.propose` | **SAFE** |
| `ConsolidationGate.accept` | **SAFE** |
| `CognitiveOrchestrator.run` write-back | **SAFE** for FACT mint |
| `persist_observed_acquisition` | **BYPASS** of “no arbitrary issuance” (trusted mint unconstrained) |
| `IngestPort.persist_acquired` | **BYPASS** same |
| `_process_authority` / `_mint` | **BYPASS** same |
| `verify_observation_grant` | **SAFE** (verify, not mint) |
| `sqlite3.connect(store.path)` | **SAFE** for FACTUAL_PREMISE (Hybrid-D) |
| corpus `seed_corpus` / evaluator / p5_eval / `run_memory_vs_no_memory` | **UNRESOLVED** as “ordinary caller” vs eval harness; they **do** mint in the production tree |

---

## 24. Static trust-boundary audit

Reachable and authority-relevant:

- Production `INSERT INTO memories` only via `store.py` (and tests/probes using same SQL). Not a grant bypass.
- Direct `epistemic_kind=OBSERVED_FACT` assignments exist on remember/failure/persist. Only persist attaches a verifying MAC.
- No `authorized=True`.
- Cached `allowed_reasoning_roles` ignored by `may()`.
- Secret not logged or committed (**validate_imports SECRETS PASS**).
- Verify failures return `False` (fail-closed), do not fall back to stored roles.
- `_payload` after swallowed `IntegrityError` may raise on second `get` (crash, not trust-metadata). **LOW**.
- **Issuer leak:** module-level persist + singleton `_mint` (CRITICAL, §5).

---

## 25. Failure-mode audit

Grant missing / MAC fail / kind mismatch / UNKNOWN source / expiry (relative to `task.created_at`) / STALE → `grant_ok=False` → HISTORY/COMPARISON only, `SUPPORT_UNKNOWN`, not FACTUAL_PREMISE.

No path of the form `verification failed → trust stored metadata anyway` was found on `may(FACTUAL_PREMISE)`.

Expired grants **do** become FACTUAL if the caller lies about `created_at` (HIGH, §14) — that is a successful verify against a chosen clock, not ignore-verify.

---

## 26. Test-independence audit

**PASS (production path) for A, B, C, E, F, G:**

- Boundary/grant tests call real `remember`, real `sqlite3`, real `bind_context(..., store=mem)`, real `CognitiveOrchestrator.run`.
- No mocks of `verify_observation_grant` or HMAC.
- `tests/p5_grant_fixtures.py` calls real `persist_observed_acquisition` (positive path / authorized P5 fixtures). That is the real issuer, not a fake verifier skip.

**FAIL for Attack D:**

`test_no_public_issue_or_grant_mint_export` only checks `__all__` and `hasattr(..., "issue")`. It never attempts `persist_observed_acquisition` / `IngestPort` / `_mint` as an **attack**. Green result does not prove issuance is blocked.

`TEST_INDEPENDENCE = FAIL` (mint claim). Other mandatory attacks are independently exercised.

---

## 27. Positive-path validation

Trusted persist → grant in payload → retrieve → bind MAC → FACTUAL_PREMISE → `WEAKLY_SUPPORTED` → write-back permitted: **PROVEN** (`test_positive_trusted_acquisition_path`, probe 1, corpus/eval still green in full pytest).

Legitimate observations still work. The same path is what the unconstrained caller uses.

`POSITIVE_PATH = PASS`

---

## 28. Lane-A validation

`scripts/freeze_lane_a.py`: **Lane-A integrity OK (36 files pinned)**.  
`git diff 38247d1..HEAD -- discovery paper_trading`: empty.  
This audit created no Lane-A edits.

`LANE_A_STATUS = UNTOUCHED`

---

## 29. Soak validation

No tracked soak DB/evidence files in implementation or this audit. Untracked `reports/PRE_SOAK_STATUS.txt` / `next-env.d.ts` were not committed and not used as soak proof. Soak was not restarted, rewritten, or fabricated.

`SOAK_STATUS = UNTOUCHED`

---

## 30. Regression results

| Run | Result |
| --- | --- |
| Focused P5 + ObservationGrant + polarity + negation + typed + second forensic | **239 passed** |
| ObservationGrant + boundary (subset of above) | included; previously **51 passed** on grant+boundary files |
| Full `pytest tests` | **2008 passed, 3 skipped** (223.31s) |
| `scripts/validate_imports.py` | **VALIDATION PASSED** (232 modules; Lane A 36/36; secrets scan 3019 files) |
| `scripts/freeze_lane_a.py` | **36/36** |

Existing tests are green. Green tests did **not** cover unconstrained persist-as-attack or `task.created_at` clock control.

---

## 31. Diff forensics

This audit: **one new file** (this report). Working tree otherwise only pre-existing untracked `next-env.d.ts` and `reports/PRE_SOAK_STATUS.txt` (not from this audit’s implementation).

Implementation vs V2 (`f50cba4..e93b3c0`): 17 files, all **REQUIRED** for the ObservationGrant change or its report. **UNRELATED = 0**.

`git status` after tests: those two untracked files only; validate_imports side-effect reports restored.

---

## 32. Claim calibration

| Claim from implementation report | This audit |
| --- | --- |
| Direct remember bypass closed | **PROVEN** |
| SQLite without MAC cannot FACTUAL | **PROVEN** |
| Revision cannot inherit | **PROVEN** |
| Generic / world-model cannot FACT | **PROVEN** |
| DERIVED_FACT separate | **PROVEN** |
| propose/accept safe | **PROVEN** |
| Two/three-hop blocked | **PROVEN** |
| Positive path works | **PROVEN** |
| `ARBITRARY_GRANT_MINTING = BLOCKED` | **DISPROVEN** |
| Temporal expiry enforced vs “now” | **DISPROVEN** as wall/episode `now`; **PROVEN** only vs `task.created_at` |
| Hybrid-D composition-root mint | **DISPROVEN** |

---

## 33. Mandatory attack proofs

### Attack A — ordinary `remember(OBSERVED_FACT)` → retrieve → bind

**NO FACTUAL_PREMISE.** Verdict `INSUFFICIENT_EVIDENCE`. Write-back false.  
Tests: `test_ordinary_remember_observed_fact_is_not_factual`, inverted `test_consumption_remembered_observed_fact_is_factual_premise`. Probe 6.

### Attack B — SQLite INSERT OBSERVED_FACT → retrieve → bind

**NO FACTUAL_PREMISE.** Verdict `INSUFFICIENT_EVIDENCE`.  
Tests: `test_direct_sqlite_insert_is_not_factual`. Probe sqlite INSERT.

### Attack C — valid A → revise B → old grant → bind B

**NO FACTUAL_PREMISE.** Kind may remain OBSERVED_FACT (label).  
Test: `test_revision_cannot_inherit_stale_authority`. Probe revise.

### Attack D — arbitrary caller → grant issuance

**NOT BLOCKED.**  
`persist_observed_acquisition` / `IngestPort` / `_mint` issue process-valid grants for arbitrary statements → FACTUAL_PREMISE + positive + write-back.  
Existing `test_no_public_issue_*` does **not** attempt this. Probe 1.

### Attack E — valid grant → mutate latest observation → bind

**BLOCKED** on fresh bind/orchestrator.  
Test: `test_toctou_revise_after_grant_latest_hash_wins`. Probe 5 rebind.

### Attack F — DERIVED_FACT → factual authority

**BLOCKED** on an isolated derived row.  
Test: `test_derived_fact_cannot_use_observation_grant`. Probe 3 isolated store.

### Attack G — generic ingestion → OBSERVED_FACT → bind

**BLOCKED WITHOUT VALID AUTHORITY.** Explicit FACT raises; default INFERENCE is not FACTUAL.  
Test: `test_generic_ingestion_cannot_mint_factual`. Probe generic ingest.

---

## 34. Severity classification

### CRITICAL (1)

**C1 — Unconstrained production ObservationGrant mint.**  
Ordinary in-process import of `persist_observed_acquisition` / `IngestPort.persist_acquired` / `_process_authority()._mint` manufactures factual authority for attacker-chosen statements (source, time, domain also chosen). Violates Hybrid-D composition-root / tests-only IngestPort / “not a free-form sign this claim RPC”. **PROVEN** (probe 1).

### HIGH (1)

**H1 — Caller-controlled bind clock (`task.created_at`).**  
Expired granted observations and future `observed_at` become `FACTUAL_PREMISE` / `WEAKLY_SUPPORTED` when the caller sets `CognitiveTask.created_at`. Orchestrator `now` is not used. Weakens V2 temporal authority. **PROVEN** (probes 3–4).

### MEDIUM (2)

**M1 — Held `EvidenceBinding.may()` does not re-fetch latest SQLite.** Snapshot stays FACTUAL after store revise. Production orchestrator rebinds. **PROVEN** (probe 5) / production write-back **PASS** (probe 4).  
**M2 — Eval/benchmark production modules mint grants** (`corpus.py`, `evaluator.py`, `p5_eval.py`, `loop/benchmark.py`), contrary to V2 “not prod mint / TestIngestPort”. Not an ungranted remember bypass.

### LOW (2)

**L1 — Case-sensitive canonical statements** (strict; may reject case-only equivalents).  
**L2 — `_payload` may raise `IntegrityError` after latest-row integrity failure** (crash, not fail-open).

Do not downgrade C1. It manufactures factual authority.

---

## 35. Final decision

Existing regression is green. That is insufficient.

Mandatory proofs A, B, C, E, F, G **pass**.  
Mandatory proof **D fails**.  
Temporal HIGH **H1** is an unresolved-by-tests authority-boundary defect.

Therefore:

### FORENSIC-FAIL

Not FORENSIC-PASS: CRITICAL > 0, HIGH > 0, Attack D open, mint test-independence fail.

Do not merge. Do not mark ready. Do not treat the previous `IMPLEMENTATION_STATUS = PASS` as a security proof.

---

`FORENSIC_STATUS = FAIL`

`CRITICAL_FINDINGS = 1`

`HIGH_FINDINGS = 1`

`OBSERVED_FACT_AUTHORITY = GRANT_VERIFIED`

`LATEST_STATE_MAC_VERIFICATION = PASS`

`DIRECT_SQLITE_ESCALATION = BLOCKED`

`REVISION_AUTHORITY_REUSE = BLOCKED`

`ARBITRARY_GRANT_MINTING = OPEN`

`GENERIC_INGEST_ESCALATION = BLOCKED`

`WORLD_MODEL_ESCALATION = BLOCKED`

`DERIVED_FACT_SEPARATION = PASS`

`TOCTOU = PASS`

`N_HOP_ESCALATION = BLOCKED`

`WRITEBACK_AUTHORITY = PASS`

`POSITIVE_PATH = PASS`

`TEST_INDEPENDENCE = FAIL`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`UNRELATED_CHANGES = 0`

`IMPLEMENTATION_AUTHORIZED = NO`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`REPORT = reports/agi_aci_evolution/P5_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`
