# P5 Memory Authorization Boundary V2

**Kind:** Hardened pre-implementation architecture. Not a fix. Not code.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**AUDITED_SHA:** `38247d172319741f5df7bd6e01ba2817bf211def`  
**DESIGN_COMMIT:** `50cbe7e`  
**Threat model:** `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_THREAT_MODEL.md`  
**Prior design:** `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md`

`CODE_CHANGES_ALLOWED = NO`  
`IMPLEMENTATION_AUTHORIZED = NO`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
Not AGI, ACI, entailment, or NER. Lane A and soak are out of scope and untouched.

---

## 1. Executive conclusion

**True security boundary (ordinary API caller):**

> Factual authority exists only when bind/reason **recomputes** the canonical observation bytes from the **latest** store revision and **verifies** an `ObservationGrant` MAC under the **process ObservationAuthority secret**. A SQLite row with `epistemic_kind=OBSERVED_FACT` is **data**, not authority.

`remember()` is **not** that boundary. It is one write door. Every other production door must either refuse `OBSERVED_FACT` or persist a grant that **the same verifier** will accept at bind.

**Selected architecture: D — Hybrid** (smallest that closes the demonstrated surface):

- **Application-level** `ObservationAuthority` is the only mint (not a public `issue(statement=…)`).
- **Persistence verification at read/bind** (and at `remember` as defense-in-depth): MAC over latest canonical tuple. Fail-closed: no FACTUAL_PREMISE.
- **No new storage engine.** SQLite stays. Direct `INSERT` without a valid MAC cannot become FACTUAL_PREMISE.
- **Not claimed:** protection against an attacker who holds the process secret, patches `bind_item`, or replaces the Python verifier.

V1 Option B (grant at `remember` only) is **DISPROVEN** as sufficient (threat model). V2 keeps the grant family and moves the **authoritative check** to consumption of the latest row.

---

## 2. Complete write-surface inventory

Search included: `architecture/cognitive/**`, `architecture/knowledge/**`, `scripts/**`, `config/paths.py`, `engine/**` (no cognitive remember), Lane A (forbidden as cognitive DB). Data flow: only `INSERT INTO memories` in `store.py` persists cognitive rows. `epistemic_kind` is a column set by `remember` / `revise` (copies previous kind) / `supersede` (copies kind into new remember).

| Path | Can create OBSERVED_FACT? | Can bypass authority? | Trust zone | Required fix | Class (today) |
| --- | --- | --- | --- | --- | --- |
| `CognitiveMemoryStore.remember` | **YES** (caller kind) | **YES** | Z0 | Persist OBSERVED_FACT only with grant; bind verifies | **PROVEN BYPASS** |
| `revise(statement=)` | No new kind; **preserves** kind | **YES** (stale grant / no grant check) | Z0 | Authority-bearing revise invalidates grant; bind vs latest | **PROVEN BYPASS** |
| `supersede` | **YES** (copies kind) | **YES** | Z0 | New grant or demote | **PROVEN BYPASS** |
| `record_failure` | Kind OBSERVED_FACT + type FAILURE | **NO** as FACTUAL_PREMISE (`typed_class` FAILURE) | Z1 | Pin: refuse FACTUAL_PREMISE; prefer non-FACT kind later | **PROVEN SAFE** (role) |
| `record_world_model_object` | **YES** via `**kwargs` kind | **YES** | Z0 | Refuse OBSERVED_FACT | **PROVEN BYPASS** |
| `ingest_generic_observation` / domain wrappers | **YES** default | **YES** | Z0 | Remove FACT capability or inject IngestPort only in tests | **PROVEN BYPASS** |
| `ConsolidationGate.accept` | **NO** (veto) | **NO** | Z1 | None for facts | **PROVEN SAFE** |
| `HypothesisStore.propose` | **NO** (JSONL) | **NO** | Z0 | None | **PROVEN SAFE** |
| `CognitiveOrchestrator` write-back | HYP/LESSON/INFERENCE only | **NO** | Z5 | None | **PROVEN SAFE** |
| Benchmark corpus/evaluator/p5_eval | **YES** | **YES** if imported as prod ingest | Z0/eval | Test/eval IngestPort only; not in production `__all__` mint | **PROVEN BYPASS** (harness) |
| `MemoryRecord(...)` ctor | In-memory only | **NO** persist | Z0 | None | **PROVEN SAFE** |
| `sqlite3.connect(store.path)` INSERT/UPDATE | **YES** | **YES** vs API-only grant | Z0 + FS | Bind-time MAC fail-closed | **PROVEN BYPASS** of API-only |
| `get_cognitive_memory_db_path()` | Path only | Enables SQLite attack | Z0 | Encapsulate path; still assume FS attacker exists | **PROVEN** path is public |
| `scripts/sqlite_backup_restore.py` | Other DBs; no cognitive INSERT found | Restore of a forged file | admin | Bind verify | **UNRESOLVED** as script; **CLOSED** if bind verifies |
| `scripts/init_databases.py` | No cognitive schema | **NO** | — | None | **PROVEN SAFE** |
| `VersionedClaimStore` | Other DB | **NO** P5 retrieve | — | None | **PROVEN SAFE** |
| Lane A / soak INSERT | Other DBs; constructor `FORBIDDEN_DB_NAMES` | **NO** cognitive | Lane A | Do not touch | **PROVEN SAFE** |
| JSON/pickle of MemoryRecord | No loader in `architecture/cognitive` | **NO** found | — | Do not add a loader that sets kind from JSON | **PROVEN SAFE** (absence) |
| `apply_decay` / `contradict` | Status/edges only | **NO** kind mint | Z1 | None | **PROVEN SAFE** |

No cognitive memory migration/import/deserialize production API was found.

---

## 3. Trust model

**Invariant:** Storage is never epistemic authorization. `kind=OBSERVED_FACT` is a **label**. Authority is a **verifiable grant** bound to the latest canonical observation.

| Concept | Meaning |
| --- | --- |
| DATA ACCEPTANCE | `validate_new_record`: enums, non-empty tokens, AI veto, confidence range |
| PERSISTENCE | Append-only SQLite row |
| EPISTEMIC AUTHORIZATION | MAC verify + temporal + live support/entity at bind |

Authoritative artifact: **`ObservationGrant` HMAC** under the process secret, over the canonical tuple of the **latest revision**. Not a boolean `authorized=True` column (forgeable by SQLite).

---

## 4. ObservationAuthority model

```
TRUSTED ACQUISITION (collector/adapter with injected IngestPort)
        → validate (VALID DATA, not truth)
        → provenance bind (non-UNKNOWN source, observed_at, domain)
        → ObservationAuthority._mint (not a public issue(statement=))
        → ObservationGrant
        → remember (stores row + grant material in payload)
        → later: bind recomputes canonical bytes from latest row, verifies MAC
```

**Authorization means:** AHOS permitted this **exact representation** to be treated as an observation-class record. **Not** that the statement is true.

`issue(statement=…)` **MUST NOT** exist as an ordinary public function. Minting is a **closure** inside the Authority instance held by the composition root. Adapters receive `IngestPort.persist_acquired(AcquisitionRecord)` where `AcquisitionRecord` is built by the adapter from **its** acquisition (probe payload, sensor read), not a free-form “sign this claim” RPC.

Tests: a `tests/`-only `TestIngestPort` fixture. Not exported from `architecture.cognitive.__init__`.

---

## 5. Trusted issuer — can import reach Z3?

**PROVEN:** Python import is not a security boundary (`_issue` is not a lock).

**Smallest mechanism that still works for “ordinary API caller”:**

1. **One** `ObservationAuthority` constructed at process start with `os.urandom(32)`.
2. Secret and `_mint` are attributes of that instance, **not** module-level functions.
3. `architecture.cognitive` public API exports `IngestPort` **protocol** and `verify_observation_grant(row, secret)` used by bind — verify is not mint.
4. Ordinary callers can call `remember` without a grant → persist **rejected** for OBSERVED_FACT **or** persist as non-fact. They cannot call `_mint` without the root instance.
5. Attacker who **constructs a new** `ObservationAuthority()` gets a **different** secret; those grants **fail** process verify.

**Remaining hole (honest):** if the attacker obtains the **live** Authority instance (debugger, leaked singleton). That is **trusted-process compromise**, out of ordinary-API scope (§22).

Ordinary `from architecture.cognitive.memory.store import CognitiveMemoryStore` does **not** reach mint.

---

## 6. Persistence boundary

| Question | Answer |
| --- | --- |
| Is direct DB access in the threat model? | **Yes as a path** (`store.path` is public **PROVEN**). |
| Can ordinary caller get the path? | **YES** (`CognitiveMemoryStore.path`, `get_cognitive_memory_db_path()`). |
| Open SQLite and INSERT/UPDATE/DELETE? | **YES** (stdlib + file). |
| Alter grant metadata? | **YES** at filesystem layer. |
| Bypass application `remember` checks? | **YES**. |

**MODEL A** (API-only): **DISPROVEN** (SQLite, revise).  
**MODEL B** (SQLite triggers / new engine): not minimum; Lane B is local SQLite by design; triggers can be dropped by the same attacker.  
**AHOS can realistically guarantee:** **MODEL A+read-verify** = Hybrid D.

> Application-level authorization cannot defend against a caller with arbitrary filesystem/database write access **and** the ability to forge a valid MAC (needs the secret) **or** replace the verifier.

**AHOS threat classes:**

| Class | Protected by V2? |
| --- | --- |
| Ordinary API caller (remember, revise, adapters, propose, accept, public helpers) | **YES** |
| Trusted local process / composition root | Trusted, not an attacker |
| Filesystem/DB admin **without** HMAC secret | INSERT/UPDATE **persists** but **cannot** obtain FACTUAL_PREMISE (bind fail-closed) |
| Arbitrary code in the trusted process **with** secret or patched bind | **NO** |

---

## 7. Direct SQLite threat

```
caller → store.path → sqlite3.connect → INSERT OBSERVED_FACT
     → orchestrator.run → retrieve → bind → ?
```

**Without bind MAC:** FACTUAL_PREMISE (**PROVEN** today).  
**With V2 bind MAC:** verification fails → **NOT FACTUAL_AUTHORITY**. Row may still retrieve as a labeled OBSERVED_FACT for display; **roles forbid FACTUAL_PREMISE**. Fail-closed.

Does not require a new storage engine. Optional encapsulation of `store.path` reduces accidental use; it is **not** the security boundary.

SQLite triggers / connection factory: optional hardening, not required for ordinary-API + forged-row-without-secret.

---

## 8. Bind-time verification

Mandatory pipeline (fail-closed):

```
latest MemoryRecord
  + stored grant fields (payload)
  → canonical bytes from LATEST statement, source_type, source_id,
    observed_at, valid_until, domain, kind
  → HMAC-SHA256 verify (process secret)
  → valid_until/expires_at vs now
  → live entity/scope/support from statement+task
  → FACTUAL_PREMISE only if all pass
```

Forbidden as authority: original-only statement, `authorized=True` flag, cached roles, copied DTO temporal_state.

If verify fails: treat as **not** FACTUAL_PREMISE (same as UNKNOWN_AGE / STALE). Do not fail-open.

`RetrievedItem` today lacks `valid_until` (**PROVEN**). Bind already has optional `store`; **must** `store.get` for grant + valid_until (same pattern as payload).

---

## 9. Revision model

Authority-bearing fields = MAC tuple: `kind, statement, source_type, source_id, observed_at, valid_until, domain`.

| Case | What changes | Grant |
| --- | --- | --- |
| A Statement | `revise(statement=)` | **invalidated**; demote off OBSERVED_FACT **or** new grant required. Inherit **forbidden**. |
| B Source | `revise` cannot set source (**PROVEN**). New remember | **new grant required** |
| C observed_at | not on `revise` | **new grant required** if ever added; else **revision forbidden** for that field |
| D Entity | via statement text | same as A |
| E Scope/domain | `revise` cannot set domain | **new grant required** / **revision forbidden** on domain |
| F Validity (`valid_until`) | not on `revise` | bind still applies expiry; extending validity **new grant required** if API added |
| G Metadata only (confidence, correction_reason, status STALE, contradiction) | allowed | **grant remains valid** for identity tuple; STALE/expiry still **deny FACTUAL_PREMISE** |

**Invariant:** No revision inherits factual authority from a grant bound to a different canonical observation.

`supersede`: new row = new observation = **new grant** or demote.

---

## 10. OBSERVED_FACT only / DERIVED_FACT

| | OBSERVED_FACT | DERIVED_FACT |
| --- | --- | --- |
| Grant | ObservationGrant only | **Not** ObservationGrant |
| FACTUAL_PREMISE | After MAC+temporal+support | **FORBIDDEN** (**PROVEN** roles) |
| Retrieval class | DIRECT_OBSERVATION | DERIVED_RESULT |
| Persist | Only with grant | Prefer refuse or store as INFERENCE until a separate derived-authority exists |
| → OBSERVED_FACT | n/a | **FORBIDDEN** without a new trusted acquisition + grant |

`ctx.facts` currently buckets both (**PROVEN** `context.py`). V2: do not treat that bucket as FACTUAL_PREMISE (modes already use `may(FACTUAL_PREMISE)`). Implementation must not add DERIVED_FACT to ObservationGrant.

---

## 11. Generic ingestion

### `ingest_generic_observation` (`adapters.py`)

| | |
| --- | --- |
| Callers today | Tests (`test_cognitive_loop.py`); exported from `architecture.cognitive.loop` |
| Write | `remember(EPISODIC, kind default OBSERVED_FACT)` |
| Kind selectable | **YES** |
| Grant | **NO** |
| Bypass Authority | **YES** |

**V2 status:** remove factual capability from the public function: default/require non-FACT kind, **or** function deleted from production exports and tests use `TestIngestPort`.

### `record_world_model_object`

| | |
| --- | --- |
| Callers | Tests / API on store |
| Write | `remember(WORLD_MODEL, kind default INFERENCE, **kwargs)` |
| OBSERVED_FACT | **YES** if kwargs pass kind |
| Bypass | **YES** |

**V2 status:** `epistemic_kind` must not be FACT; reject OBSERVED_FACT.

---

## 12. Provenance

Grant proves authorization of a representation, not truth.

UNKNOWN provenance tokens: **forbidden** for OBSERVED_FACT persist and for FACTUAL_PREMISE. Allowed for non-facts.

No source registry. `source_id` is an attribution string.

---

## 13. Temporal authority

| Field | In MAC? | At bind |
| --- | --- | --- |
| `observed_at` | **YES** (integer µs UTC) | Required; missing → not FACTUAL_PREMISE; `> now` → fail-closed |
| `created_at` / ingested_at | **NO** (AHOS-derived) | Not freshness proof |
| `valid_until` | **YES** (`NONE` or µs) | `≤ now` → not FACTUAL_PREMISE |
| `status` STALE | **NO** (derived) | not FACTUAL_PREMISE |
| TEMP_CURRENT | unused today | Insert of old data remains **DATED**, never CURRENT (**PROVEN**) |

Do not depend on insert-only checks. Do not require `apply_decay` (orchestrator does not call it).

---

## 14. Entity / scope

Entity is **not** a grant field (caller-forged entities would override live recompute). MAC binds **statement** (entity computed at bind) and **domain** (applicability).

`ENTITY_A` grant reused for `ENTITY_B`: different statement hash or live mismatch.  
Scoped vs unscoped: live `entity_alignment` + domain HMAC; no payload/domain `revise`.

---

## 15. Canonicalization

UTF-8 NFC statement after **one** specified `strip()`. No case-fold.  
Times: integer microseconds UTC.  
Enums: `.value` strings.  
`valid_until`: `NONE` or integer, never omitted.  
MAC input (sorted, `|`-separated, version-prefixed):

`AHOS-OG-v1|FACTUAL_INGEST|OBSERVED_FACT|{sha256}|{source_type}|{source_id}|{observed_at_us}|{valid_until}|{domain}|{issuer_id}`

Same tuple → same bytes. Different tuple → different bytes.

Nonce: **not** in the minimum MAC (see §16).

---

## 16. Replay

**Minimum:** grant is **reusable only for the exact immutable observation tuple**. Persist uniqueness: `(statement_sha256, source_id, observed_at, kind)` — second insert is idempotent get-or-reject, not a second authority.

**Nonce not required** for v2 minimum: a copied grant cannot authorize a **different** tuple; bind rejects hash mismatch. Nonce would only block **double persist of the identical observation**, which is not an authority escalation.

Revocable: not v2 (process restart keeps rows; bind still verifies). Version-bound: `AHOS-OG-v1` prefix.

---

## 17. API trust table

| API | Caller trust | Mint OBSERVED_FACT? | Mutate fact? | Requires grant? | Future status |
| --- | --- | --- | --- | --- | --- |
| `remember` | untrusted | today YES | no | **YES** for OBSERVED_FACT | persist+store grant; bind verifies |
| `revise` | untrusted | preserves | statement/status/confidence | n/a | A–F invalidate or forbid; G ok |
| `supersede` | untrusted | copies | new row | **YES** or demote | |
| `record_failure` | untrusted | kind only | no | no FACTUAL_PREMISE | keep FAILURE type-win |
| `record_world_model_object` | untrusted | via kwargs | no | refuse FACT | restrict kind |
| `ingest_generic_observation` | untrusted | YES | no | — | strip FACT or TestIngestPort |
| `accept` | untrusted | NO | no | no | unchanged |
| `propose` | untrusted | NO | no | no | unchanged |
| `orchestrator.run` WB | loop | NO | no | no | unchanged |
| `apply_decay` / `contradict` | untrusted | NO | status/edges | no | unchanged |
| `IngestPort.persist_acquired` | trusted inject | YES | no | mint inside | only composition root |
| sqlite INSERT/UPDATE | FS | YES | YES | bind verify | fail-closed FACTUAL_PREMISE |
| benchmark seeders | eval | YES | no | TestIngestPort | not prod mint |

---

## 18. Authority graph

```
UNTRUSTED INPUT                         ← no authority
      ↓
VALIDATED DATA                          ← not evidence
      ↓
TRUSTED OBSERVATION ACQUISITION         ← IngestPort only
      ↓
OBSERVATION AUTHORITY                   ← mint; NOT public issue()
      ↓
OBSERVATION GRANT                       ← MAC
      ↓
PERSISTED OBSERVATION                   ← label only; NOT authority
      ↓
BIND-TIME MAC VERIFICATION              ← TRUE boundary (latest row)
      ↓
FACTUAL EVIDENCE                        ← role FACTUAL_PREMISE
      ↓
P5 REASONING / CRITIC / EPISODE
      ↓
REUSABLE WRITE-BACK                     ← HYP/LESSON/INF only; NOT OBSERVED_FACT
```

**MUST NOT create authority:** remember without grant; public issue; revise inherit; sqlite label; accept/propose; hop-2 labels; DERIVED_FACT; `authorized=True` flags; DTO roles.

---

## 19. Bypass closure matrix

Against **ordinary API caller + sqlite without secret**. Architecture as specified (not yet code).

| Attack | Status |
| --- | --- |
| direct remember without grant | **CLOSED** (reject persist or non-fact; bind fail-closed) |
| public issue(statement=) | **CLOSED** (does not exist; mint not exported) |
| revise statement inherit | **CLOSED** (invalidate + bind latest hash) |
| direct SQLite INSERT | **CLOSED** for FACTUAL_PREMISE (MAC fail); row may exist |
| generic ingestion | **CLOSED** (no FACT capability / TestIngestPort) |
| world-model ingestion | **CLOSED** (refuse OBSERVED_FACT) |
| JSON restore / deserialize | **CLOSED** (no loader; bind would fail without MAC) |
| migration | **CLOSED** (none found; bind fail-closed) |
| replay different tuple | **CLOSED** (hash) |
| replay identical tuple | **CLOSED** (not escalation; uniqueness) |
| mutation of binding DTO | **CLOSED** (existing P5 freeze/live) |
| stale / expired valid_until | **CLOSED** (bind vs now) |
| entity / scope mismatch | **CLOSED** (live + domain MAC) |
| forged grant / HMAC | **CLOSED** (no secret) |
| forged source string | **CLOSED** as truth oracle (not claimed); persist allowed if grant minted by IngestPort |
| UNKNOWN provenance | **CLOSED** for FACT |
| DERIVED_FACT as observation | **CLOSED** (no grant; no FACTUAL_PREMISE) |
| propose / accept | **CLOSED** (PROVEN SAFE) |

No OPEN. Residual **UNRESOLVED** only for trusted-process compromise / secret theft — excluded from pass criterion for ordinary-API model (§22).

---

## 20. Implementation boundary (future; not now)

**MUST CHANGE (Lane B only, later authorized task):**

- `remember` OBSERVED_FACT path + payload grant material  
- `revise` / `supersede` rules  
- `bind_item` / `may(FACTUAL_PREMISE)` grant+expiry verify via `store.get`  
- `record_world_model_object` kind lock  
- `ingest_generic_observation` FACT removal or test-only port  
- New `ObservationAuthority` + `IngestPort` + verify helper  
- Invert gap-documentation tests that assert ungranted remember authorizes  

**MUST NOT CHANGE:**

- Lane A, soak, `P5_FORENSIC_ARCHITECTURE_GATE.md`  
- Retrieval ranking (P4.3)  
- Critic / episode / hop-2/3 policy  
- `propose` / `accept` fact veto  
- Frozen EvidenceBinding live recompute  
- Schema of `memories` **if** grant fits in `payload_json` (avoid migration)  
- SQLite engine  

Minimal, isolated, reversible (revert modules + bind check), test-first, soak-safe.

---

## 21. Required security tests (before implementation complete)

| # | Test | Expected invariant |
| --- | --- | --- |
| 1 | Forged grant | remember reject and/or bind not FACTUAL_PREMISE |
| 2 | Arbitrary public issue() | **AttributeError / not exported**; cannot mint |
| 3 | Direct remember OBSERVED_FACT no grant | reject or not FACTUAL_PREMISE |
| 4 | SQLite INSERT OBSERVED_FACT | retrieve possible; **not** FACTUAL_PREMISE; no positive/write-back |
| 5 | SQLite UPDATE statement | bind hash fail; not FACTUAL_PREMISE |
| 6 | Stale/expired valid_until | not FACTUAL_PREMISE |
| 7 | revise statement | grant invalid; not FACTUAL_PREMISE |
| 8 | revise source (if API) | forbidden or new grant |
| 9–10 | entity/scope via statement/domain | live mismatch / MAC domain |
| 11 | temporal field swap | MAC fail |
| 12 | UNKNOWN provenance | no OBSERVED_FACT persist/role |
| 13 | DERIVED_FACT | no ObservationGrant; no FACTUAL_PREMISE |
| 14–15 | generic / world-model | cannot persist OBSERVED_FACT |
| 16 | replay other tuple | reject |
| 17–18 | serialize grant / pickle Authority | verify still required; no secret in JSON |
| 19–21 | two/three/n-hop | no factification |
| 22 | TOCTOU revise after grant | latest hash wins |
| 23 | critic | still load-bearing |
| 24 | write-back | no OBSERVED_FACT mint |

Plus existing P5 A–AQ, freeze 36/36, soak untouched.

---

## 22. Threat-model limitations

V2 **does not** protect:

- Arbitrary filesystem write **plus** HMAC secret  
- Replacing `bind_item` / verifier in-process  
- Debugger reading `Authority._secret`  
- Operator who swaps the Python tree  

V2 **does** protect ordinary use of public cognitive APIs and forged DB rows **without** the secret.

Do not claim OS-level SQLite lockdown.

---

## 23. Final architectural decision

**D — Hybrid:** ObservationAuthority (non-public mint) **+** bind-time MAC verification of the latest canonical observation.

Smaller than a new storage engine (C). Stronger than V1 remember-only (A/B-as-written). Closes the threat-model FAIL list under the **ordinary API caller** (and forged-row-without-secret) model.

---

`ARCHITECTURE-V2 = VALID`

`SECURITY-REVIEW-V2 = PASS`

`IMPLEMENTATION_AUTHORIZED = NO`

`CODE_CHANGES_ALLOWED = NO`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`AUDITED_SHA = 38247d172319741f5df7bd6e01ba2817bf211def`

`DESIGN_COMMIT = 50cbe7e`

`REPORT = reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md`
