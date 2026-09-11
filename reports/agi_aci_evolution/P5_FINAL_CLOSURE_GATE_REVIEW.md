# P5 ObservationGrant — final closure gate & PR #93 security-exit review

**Kind:** Independent security-architect / forensic **gate**. Read-only. Not an implementer.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT** (`isDraft=true`, `state=OPEN`)  
**Question answered:** whether P5 V4-PIN has reached a legitimate **security-exit** boundary — **not** whether the PR may merge, be marked Ready, ship to production, or trade.

This document does **not** trust implementation reports, forensic reports, or the residual-boundary review merely because they say PASS. Those documents were treated as **claim lists**. Proof is production source at the V4-PIN code SHA, plus this gate’s re-trace, plus targeted re-execution of the P5 grant suites, plus the independently recorded full-pytest result on an **identical** `architecture/` + `tests/` tree.

**Not AGI. Not ACI. Not production-ready. Not live trading.**

```text
V3_BASELINE              = 24b2ab8244f41d9e78582ccfc41dc4b0cf490a83
V4_PIN_CODE              = afdff2539943441244d05478a7004bc4bcc5976f
FORENSIC_AUDIT_TREE      = ffde25a8693e9645fa85c9d979bd8771692c1b90
RESIDUAL_REVIEW_REPORT   = reports/agi_aci_evolution/P5_V4_FINAL_RESIDUAL_BOUNDARY_REVIEW.md
CODE_VS_V4_PIN           = git diff --stat afdff25..HEAD -- architecture tests  → empty
P5_GRANT_SUITES_THIS_GATE = 85 passed (V3 + V4 + observation_grant)
FULL_PYTEST_ON_SAME_TREE  = 2065 passed, 3 skipped (forensic-audit execution; tree identity confirmed)
```

---

## 1. Executive conclusion

**P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE**

The production authority topology of V4-PIN still enforces the central property: a caller-controlled ObservationGrant artifact does not become accepted production grant authority merely because the caller can construct, sign, bind, persist, retrieve, mutate, or replay it inside the legitimate process.

This gate found:

| Class | Count | Notes |
| --- | --- | --- |
| CRITICAL | **0** | No previously unknown production-valid bypass |
| HIGH | **0** | |
| MEDIUM | **0** | |
| LOW | **6** | Same six residuals already classified; none currently violate the central property |
| I1–I15 | **PASS** | Source re-trace + suite re-run; not copy-paste from older reports |
| Production `O.run` bypass | **None found** | |
| Hidden caller-controlled production authority path | **None found** | |
| Lane A | **Untouched** vs V3 baseline | |
| Soak infrastructure | **Untouched** vs V3 baseline | |

**This is not merge-ready, not Ready-for-Review, not production-ready, and not live-trading-ready.** Those are separate decisions. This gate only answers the security-exit question.

`P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS`

The two regression-prone residuals (R1 public `assemble_evidence_binding(grant_ok=True)`, R3 `push_grant_verify_context`) remain **documented and currently non-blocking**. Extra assembler tests would be **POST-P5-HARDENING**, not a security-exit block.

---

## 2. Security-chain reconstruction

### Stage A — V3 (`24b2ab8`)

| Element | Fact |
| --- | --- |
| Original threat | Same-process caller can mint HMAC keys / issuer strings / ContextVar tokens that production `verify_observation_grant` treats as authority. |
| Attempted mitigation | DI convention, `ISSUER_ID` / `ISSUER_ID_TEST` string split, private `_grant_verify_secret`, `grant_verify_scope` ContextVar, public `reason()` / `bind_*` fail-closed. |
| Discovered weakness (C1) | Production `CognitiveOrchestrator.__init__` accepted `secret=` / `issuer=` / `**kwargs`. Production `run()` copied those into `grant_verify_scope`. Production `verify_observation_grant(key=None)` **read the ContextVar**. Ordinary caller could therefore rekey production verification. |
| Architectural correction (design only at that time) | V4-PIN: production `O` owns `K_O`; production verify uses explicit `key=` only; ContextVar is not a production authority source. |
| Independent verification | V3 forensic audit + live C1 probe: `CognitiveOrchestrator(secret=attacker)` + `run()` accepted attacker HMAC as `FACTUAL_PREMISE`. |
| Remaining residual after V3 | **C1 open.** V3 was not a security exit. |

### Stage B — V4-PIN implementation (`afdff25`)

| Element | Fact |
| --- | --- |
| Original threat | C1 plus the remaining V3 surface (issuer, ContextVar, retriever, memory, SQLite, revision, O1≠O2, mutation, clock, write-back). |
| Attempted mitigation | Production `__init__`: `K_O = os.urandom(32)` with test-vector denylist retry; `_verify_issuer_id = ISSUER_ID`; no `secret=` / `issuer=` / `ingest=` / `**kwargs`. `run()` does not copy/push grant ContextVar. `_permits_observation_grant` always passes `key=self._grant_verify_secret`. `verify_observation_grant`: `key is None` → False; **does not read ContextVar**. Public `reason` / `bind_*` always `grant_ok=False`. Tests use `TestCognitiveOrchestrator` (post-`super().__init__` overwrite), not production `run` wrapped in `grant_verify_scope`. |
| Discovered weakness | No new production-valid bypass in implementation. Six LOW residuals (public assembler flag, readable `K_O`, dead ContextVar helper, caller `BoundIngestPort`, no mint adapter, `run(now=)`). |
| Architectural correction | Production authority root moved from “whatever the constructor/ContextVar supplied” to “this instance’s `K_O`”. |
| Independent verification | Implementation report is **untrusted**. Forensic audit re-attacked the tree. |
| Remaining residual | Six LOW items; C1 closed on production `O.run`. |

### Stage C — Independent V4-PIN forensic audit (`ffde25a` tree; code = `afdff25`)

| Element | Fact |
| --- | --- |
| Original threat | Implementation claims might be fixture-only or report-only. |
| Attempted mitigation | Ordinary-caller `/tmp` probes against production `CognitiveOrchestrator`; source re-trace of verify / ContextVar / `O.run`. |
| Discovered weakness | None that reopen C1. Isolation ACCEPT legs in tests copy `_grant_verify_secret` at the composition root (out of plugin threat model). |
| Architectural correction | None (audit was read-only). |
| Independent verification | `FORENSIC_STATUS = PASS`. CRITICAL/HIGH/MEDIUM = 0. LOW = 6. Full pytest **2065 passed, 3 skipped** on that code tree. |
| Remaining residual | Same six LOWs, then sent to residual-boundary review. |

### Stage D — Final residual-boundary review (report-only)

| Element | Fact |
| --- | --- |
| Original threat | A documented LOW might actually be a live production bypass, or a regression hole without safeguards. |
| Attempted mitigation | Design classification of R1–R6; live `/tmp` probes for R1 (forged DTO vs `O.run`) and R6 (`now=` vs `created_at`). |
| Discovered weakness | R1 can mint an in-memory `EvidenceBinding` with `grant_ok=True`; that DTO is **not** `CognitiveResult` and is **not** consumed by `O.run`. R3 is dead for production verify but would be catastrophic if `ctx.key` were restored. |
| Architectural correction | None implemented (DOCUMENT-AND-TEST / KEEP-AS-IS / DEFER). |
| Independent verification | This closure gate re-read that report as a claim list and re-checked source + suites. |
| Remaining residual | R1–R6 still LOW; `P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS`; `MERGE = NO`; `READY_FOR_REVIEW = NO`. |

**Chain integrity:** `git diff --stat afdff25..HEAD -- architecture tests` is empty. Later commits are reports only. This gate reviews the same production/test Python the forensic audit attacked.

---

## 3. Central authority property

> A caller-controlled authority artifact must never become accepted production ObservationGrant authority merely because the caller can construct, sign, bind, persist, retrieve, mutate, or replay it inside the legitimate process.

**HOLDS** on production `CognitiveOrchestrator.run`.

### Production path (re-traced this gate)

```text
O.__init__:
  K_O = os.urandom(32)   # denylist TEST_VECTOR_KEY / TEST_VECTOR_KEY_ALIEN
  issuer = ISSUER_ID     # not ISSUER_ID_TEST, not caller
  no secret= / verifier= / ingest= / issuer= / **kwargs

O.run(task, now=optional):
  ts = now or time.time()                    # NOT CognitiveTask.created_at
  items = retriever.retrieve(...)            # no grant ContextVar push
  O._reason_episode
      O._bind_item
          grant_ok = O._permits_observation_grant(...)
                     verify_observation_grant(..., key=self._grant_verify_secret)
          assemble_evidence_binding(..., grant_ok=grant_ok)
      evaluate_reason(task, ctx, those bindings)
  writeback: reusable_writeback_permitted(
               verdict,
               O._bind_context(store.get(...), ts)   # rebind; not caller DTO
             )
```

`CognitiveResult` has **no** `bindings=` field. Public `reason()` / `bind_item()` / `bind_context()` always pass `grant_ok=False`.

### Production grant verification (re-traced this gate)

```text
use_key = key
if use_key is None:
    return False
# ContextVar is not read
```

### Property vs surfaces

| Surface | Can mint / hold an artifact? | Becomes production `O.run` authority? |
| --- | --- | --- |
| Caller HMAC | Yes | **No** — verify uses `O._grant_verify_secret` |
| Caller issuer | Yes | **No** — production issuer is `ISSUER_ID` |
| ContextVar / `push_grant_verify_context` | Yes | **No** — production verify ignores it; `run` does not push |
| Retriever / memory / SQLite | Yes (rows) | **No** — retrieve is ordinary evidence; grant_ok from instance verify |
| Revision / write-back | Yes (store) | **No** — write-back rebinds via `O._bind_context` |
| Public assembler `grant_ok=True` | Yes (DTO) | **No** — not on `O.run` path; `CognitiveResult` has no bindings |
| `BoundIngestPort` | Yes (caller ingest) | **No** — production `O` has no ingest; `run` does not mint |

No previously unknown production-valid bypass was found. **Hard-stop condition not triggered.**

---

## 4. I1–I15 verification matrix

Legend: **PASS** = this gate re-traced production source and confirmed the matching adversarial suite still passes on HEAD. **FAIL** = live or source contradiction. **NOT-RETESTED** = would be used only if this gate could not reach the code; unused here.

| ID | Property | Result | Evidence this gate |
| --- | --- | --- | --- |
| I1 | Production O owns K_O | **PASS** | `__init__` urandom + denylist; no constructor injection |
| I2 | Production verification uses O-owned K_O | **PASS** | `_permits_observation_grant` → `key=self._grant_verify_secret` only |
| I3 | Caller-controlled HMAC ≠ production authority | **PASS** | `test_v4_a_forged_hmac_rejected`; `verify` with alien key |
| I4 | Caller-controlled issuer ≠ production authority | **PASS** | Production issuer frozen; `test_v4_d_issuer_test_rejected_in_production` |
| I5 | ContextVar cannot inject production grant authority | **PASS** | `verify` ignores ContextVar; `test_v4_c_contextvar_ignored_by_production_verify`; `run` has no push |
| I6 | Retriever cannot manufacture authority | **PASS** | Retrieve precedes bind; grant_ok from instance verify; `test_v4_h` |
| I7 | Memory cannot manufacture authority | **PASS** | Same bind path; `test_v4_i` |
| I8 | SQLite/DB state cannot manufacture authority | **PASS** | Rows are evidence; `test_v4_j` |
| I9 | Revision cannot inherit/recreate unauthorized authority | **PASS** | `test_v4_k`; write-back rebinds |
| I10 | O1 authority cannot authorize O2 | **PASS** | Distinct urandom keys; `test_v4_g` |
| I11 | Canonical evidence mutation invalidates stale authority | **PASS** | HMAC over canonical bytes; `test_v4_l` |
| I12 | Caller-controlled episode clock cannot authorize alien authority | **PASS** | `created_at` unused for verify; `test_v4_m`; R6 `now=` is episode clock only |
| I13 | Derived fact / evidence separation intact | **PASS** | Grant does not mint derived facts; `test_v4_n` |
| I14 | N-hop propagation cannot manufacture new authority | **PASS** | `test_v4_o`; no grant copy-forward |
| I15 | Write-back cannot manufacture new authority | **PASS** | `test_v4_p`; `reusable_writeback` uses `O._bind_context` |

**I1–I15 = PASS** (15/15). None FAIL. None NOT-RETESTED.

This gate re-ran `tests/test_p5_v4_authority_boundary.py`, `tests/test_p5_v3_authority_boundary.py`, and `tests/test_p5_observation_grant.py`: **85 passed**.

---

## 5. Six residual analysis

Questions for each: (1) currently violate central property? (2) currently bypass `O.run()`? (3) can become a production authority source *as currently wired*? (4) regression-prone? (5) adequately documented? (6) require implementation before security exit?

### R1 — `assemble_evidence_binding(grant_ok=True)`

| Q | Answer |
| --- | --- |
| 1 Central property now? | **No.** The function mints a **DTO role flag**, not production `O` verification. `O.run` does not accept caller bindings. |
| 2 Bypass `O.run`? | **No.** `CognitiveResult` has no `bindings`. Write-back rebinds from store via `O._bind_context`. |
| 3 Production authority source now? | **No.** Production `grant_ok` is computed only in `O._bind_item`. |
| 4 Regression-prone? | **Yes.** A future `run(..., bindings=)` or `evaluate_reason` of caller DTOs inside `run` would change this. |
| 5 Documented? | **Yes.** Residual review §R1; V4 design docs; this gate. |
| 6 Implement before security exit? | **No.** DOCUMENT-AND-TEST already chosen. Extra dedicated assembler tests = **POST-P5-HARDENING**. |

### R2 — `O._grant_verify_secret` readable

| Q | Answer |
| --- | --- |
| 1 | **No.** Holding `O` is composition-root capability, in-scope as “ordinary caller with the orchestrator object,” out of plugin scope (`store`/`task` only). |
| 2 | **No.** Readability does not rekey a *different* `O`. Same-instance copy is possession of that `O`. |
| 3 | Only for **that** instance — equivalent to holding the process’s orchestrator, not a hidden second root. |
| 4 | Moderate (future public getter / constructor). |
| 5 | **Yes.** |
| 6 | **No.** KEEP-AS-IS. Leading underscore is **not** the security boundary; instance ownership is. |

### R3 — `push_grant_verify_context`

| Q | Answer |
| --- | --- |
| 1 | **No.** Production `verify_observation_grant` does not read the ContextVar. |
| 2 | **No.** Production `run` does not call it. Call sites: definition + **tests only**. |
| 3 | **Not currently.** Would become one if `use_key = key or ctx.key` returned. |
| 4 | **Yes — highest remaining regression risk.** |
| 5 | **Yes**, including explicit “do not restore `ctx.key`” warning in prior reports. Tests: `test_v4_c_*`. |
| 6 | **No.** Removing the helper is cleanup, not a gate. |

### R4 — `BoundIngestPort`

| Q | Answer |
| --- | --- |
| 1 | **No.** Caller mint ≠ production accept. |
| 2 | **No.** Production `O` has no ingest adapter; `run` does not mint. |
| 3 | **Not currently.** |
| 4 | Low unless a future production mint adapter is added carelessly. |
| 5 | **Yes.** |
| 6 | **No.** KEEP-AS-IS. |

### R5 — No production K_O mint adapter

| Q | Answer |
| --- | --- |
| 1 | **No.** Absence of mint is fail-closed for production issuance, not a bypass. |
| 2 | **No.** |
| 3 | **No** (there is no production mint path). |
| 4 | Future ingestion must not take caller `secret=` / `issuer=`. |
| 5 | **Yes.** DEFER-TO-FUTURE-INGESTION. |
| 6 | **No.** Out of P5 security-exit scope. |

### R6 — `run(now=)`

| Q | Answer |
| --- | --- |
| 1 | **No.** Episode clock for bind/reason timestamps; HMAC `created_at` attack remains closed (I12). |
| 2 | **No** as an authority bypass. |
| 3 | **No.** |
| 4 | Low (do not wire `now=` from `task.created_at`). |
| 5 | **Yes.** |
| 6 | **No.** KEEP-AS-IS. |

**No residual was upgraded to a vulnerability.** None currently require implementation before security exit.

---

## 6. Regression-boundary analysis

### `assemble_evidence_binding(grant_ok=True)`

| Question | Answer |
| --- | --- |
| CURRENTLY SAFE? | **Yes** relative to production `O.run`. |
| REGRESSION-PRONE? | **Yes.** |
| SECURITY-BLOCKING? | **No.** |
| DOCUMENTATION SUFFICIENT? | **Yes** for a security exit (topology + explicit non-`CognitiveResult` fact). |
| TEST COVERAGE SUFFICIENT? | **Sufficient to exit:** `O.run` fail-closed vs forged HMAC; public `bind_item` / `reason` fail-closed. **Not exhaustive** of a standalone “public assembler ≠ `O.run`” test. That gap is **POST-P5-HARDENING**, not unexplained and not critical: the production consumer of `grant_ok=True` is only `O._bind_item` after instance verify. |

### `push_grant_verify_context`

| Question | Answer |
| --- | --- |
| CURRENTLY SAFE? | **Yes** (ignored by production verify; unused by `run`). |
| REGRESSION-PRONE? | **Yes.** |
| SECURITY-BLOCKING? | **No.** |
| DOCUMENTATION SUFFICIENT? | **Yes.** |
| TEST COVERAGE SUFFICIENT? | **Yes** — `test_v4_c_contextvar_ignored_by_production_verify` and related V4 ContextVar cases. Restoring `ctx.key` would fail those tests **if** they remain mandatory. |

**POST-P5-HARDENING** (do not implement in this gate): a dedicated test that `assemble_evidence_binding(..., grant_ok=True)` never appears on `CognitiveResult` / `O.run`; optional deletion or test-only move of `push_grant_verify_context`.

---

## 7. Threat-model verification

**In scope (unchanged):** ordinary same-process Python caller; malicious plugin/component; caller-controlled constructor arguments, evidence, HMAC, issuer, ContextVar, database state; malicious retriever/memory; replay; revision; TOCTOU; clock manipulation.

**Out of scope (unchanged):** OS compromise; source-code modification; debugger / process-memory compromise; filesystem administrator compromise.

| In-scope threat | Still consistent? |
| --- | --- |
| Constructor rekey | Closed (no `secret=` / `**kwargs`) |
| HMAC / issuer mint | Closed for production verify |
| ContextVar | Closed for production verify |
| Retriever / memory / SQLite | Closed (ordinary evidence) |
| Replay / revision / TOCTOU | Closed by instance verify + rebind |
| Clock (`created_at`) | Closed; `now=` is episode clock only |
| Plugin without `O` | Cannot read `K_O` |

This gate **does not** expand the model to “any holder of `O` is an attacker” in the plugin sense, and **does not** shrink it to “tests are honest.” Ordinary caller **with** a legitimate `O` can read `_grant_verify_secret` (R2); that is documented, in-model for composition-root possession, and not a second authority root.

---

## 8. Architectural authority analysis

V4-PIN is a **genuine production authority topology**, not a fixture-only patch.

Rejected as security mechanisms (they may exist but are not the proof):

- private naming (`_grant_verify_secret`)
- `__all__` omission of `assemble_evidence_binding`
- hidden attributes
- stack inspection (not used)
- secret **values** alone / issuer **strings** alone
- DI conventions
- test fixtures (`TestCognitiveOrchestrator`, `grant_verify_scope`)
- caller cooperation

**What actually enforces the property:**

1. Production `CognitiveOrchestrator` is the only object that mints production `K_O` and the only production path that sets `grant_ok` from `verify_observation_grant(..., key=K_O)`.
2. Production `verify_observation_grant` requires an explicit key and does not consult ContextVar.
3. `O.run` never accepts caller `EvidenceBinding` objects; it binds internally and returns a `CognitiveResult` without bindings.
4. Write-back rebinds through `O._bind_context`.
5. Tests that need a known key subclass after `super().__init__()` rather than wrapping production `run` in `grant_verify_scope`.

That is architecture, not naming.

---

## 9. Test / evidence verification

| Evidence | Status |
| --- | --- |
| Targeted V4/P5 adversarial suites | **This gate:** 85 passed (`v4` + `v3` + `observation_grant`) |
| Complete pytest | **2065 passed, 3 skipped** recorded on the forensic-audit execution of **this same** `architecture/` + `tests/` tree (`afdff25`). This gate confirmed `git diff --stat afdff25..HEAD -- architecture tests` is empty, so that result is not stale relative to code. This gate did **not** re-execute the full 2065 (would be redundant given identity; not an unexplained security-test gap). |
| Import validation | Previously PASS on that tree after pycache clean. Not re-run this gate (would rewrite `reports/*.json`; this gate must not modify reports except this file). Prior result still applies to identical Python. |
| Lane A | `git diff --stat 24b2ab8..HEAD -- discovery paper_trading` empty |
| Soak | Soak paths not in the V4-PIN / P5 grant delta |
| Production / test separation | Production `CognitiveOrchestrator` vs `TestCognitiveOrchestrator`; production verify ignores ContextVar |

**No unexplained critical security-test gap.** Desired extra assembler tests = POST-P5-HARDENING.

---

## 10. Scope-contamination analysis

Classification of PR #93 (`main`…`HEAD`) — **no cleanup performed**.

| Class | What |
| --- | --- |
| P5 security implementation | `architecture/cognitive/loop/orchestrator.py`, `binding.py`, `reason.py`, `architecture/cognitive/memory/observation.py` (V4-PIN delta vs `24b2ab8`); plus the broader P5 typed-reasoning / ObservationGrant stack vs `main` that this PR was opened to land |
| P5 tests | `tests/test_p5_v4_authority_boundary.py`, V3 grant tests, observation grant tests, `observation_test_runtime.py`, related typed-reasoning / polarity / forensic tests |
| P5 documentation | `reports/agi_aci_evolution/P5_*` including V3/V4 design, implementation, forensic, residual, and this closure gate |
| Historical evidence | Earlier P5/P4 reports on the same branch (audit/design history). Not executed as authority. |
| Generated artifacts | Not in the candidate. |
| Unrelated changes | **Working-tree noise not in git:** `next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt`. Must not be added. **Lane A / soak:** not in the V3→HEAD code delta. |

Vs `main`, PR #93 is the **entire P5 ObservationGrant / typed-reasoning PR**, not a V4-PIN-only diff. That is **PR product scope**, not random UI/trading contamination. Vs the V3 security baseline, the **security** delta is the four production files + grant tests + P5 reports.

**Does not prevent a security exit.** It **does** prevent treating this PR as a tiny V4-only merge unit — which is a **merge-process** concern, not a security-exit fail. Merge remains **NO** regardless.

---

## 11. Remaining non-blocking work

Explicitly **not** required for `SECURITY-EXIT-CANDIDATE`:

1. Dedicated test: public `assemble_evidence_binding(grant_ok=True)` is not consumed by `O.run` / `CognitiveResult` — **POST-P5-HARDENING**.
2. Delete or test-gate `push_grant_verify_context` — cleanup / hardening.
3. Production K_O mint adapter — **DEFER-TO-FUTURE-INGESTION** (must not take caller secrets).
4. Merge review, Ready-for-Review, production rollout, live trading — **separate gates**.
5. Full 2065 re-run at this report’s commit — optional hygiene; code tree unchanged since the recorded 2065.

---

## 12. Explicit security decision

**SECURITY-EXIT-CANDIDATE**

Criteria check:

- no Critical / High / Medium — **met**
- central authority property holds — **met**
- I1–I15 hold — **met** (PASS × 15)
- no production bypass — **met**
- no hidden caller-controlled production authority path — **met**
- residuals documented and non-blocking — **met**
- regression-prone residuals have explicit safeguards/documentation — **met** (docs + V4 tests; extra assembler tests hardening-only)
- no unexplained security-test gap — **met**
- Lane A untouched — **met**
- soak infrastructure untouched — **met**

No hard-stop unknown bypass.

---

## 13. Explicit merge decision

**MERGE = NO**

Security exit ≠ merge. PR #93 remains a draft with a large P5 stack vs `main`. Merge is a separate human/process decision. This gate does not merge and does not recommend merging.

---

## 14. Explicit Ready-for-Review decision

**READY_FOR_REVIEW = NO**

This gate does not mark the PR Ready. Draft status must remain.

---

## Decision block

```text
P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE
P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS
MERGE = NO
READY_FOR_REVIEW = NO
PRODUCTION_READY = NO
LIVE_TRADING = NO
```
