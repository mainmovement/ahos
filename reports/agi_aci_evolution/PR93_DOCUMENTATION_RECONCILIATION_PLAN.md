# PR #93 — documentation & living-index reconciliation plan

**Kind:** Read-only documentation architecture. Not an implementation. Not a P5 reopen.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — remains **DRAFT** (this plan does not change title, body, or status).  
**Code tip (architecture/tests):** `afdff2539943441244d05478a7004bc4bcc5976f`  
**HEAD when planned:** `c36f771` (integrity-audit report; code tree unchanged vs `afdff25`)

This plan exists because `PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL` for **index/scope drift**, not a security defect.

**Do not implement this plan in the same step that produced it.**

```text
P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE
PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL
MERGE = NO
READY_FOR_REVIEW = NO
PRODUCTION_READY = NO
LIVE_TRADING = NO
```

---

## 1. Executive summary

PR #93’s **code and security-exit evidence are ahead of the living indexes**. Historical P5 reports are internally consistent **at their SHAs** and must stay that way. The drift is that a few **living / current-truth** surfaces still describe the **2026-09-09 typed-reasoning FIX_REQUIRED snapshot** (28 tests in `test_typed_reasoning.py`, 195-file envelope) as if it were HEAD.

**Do not replace “28” with “2065”.** Those numbers are different scopes (see §5).

**Three different “P5” names exist in this repository.** Reconciliation is possible only if living AGI/ACI indexes use an explicit qualifier:

| Namespace | Meaning | Closed by PR #93? |
| --- | --- | --- |
| **Lane-B evolution P5 (this PR)** | Typed evidence-bound reasoning → polarity → memory authorization → ObservationGrant → V4-PIN | **Security-exit candidate** for ObservationGrant authority. Not merge-ready. |
| **Charter P5** | World model / causal CF (`ACI-GAP-002`) | **No.** Still OPEN / NOT_IMPLEMENTED. |
| **Ops / wave P5** | n8n / Telegram in `docs/canonical/ROADMAP.md`, `reports/PHASE_STATE.md` | **No relation.** Do not edit those files for this PR. |

With that disambiguation, living indexes can be updated without rewriting history and without implying merge, production, live trading, or AGI/ACI.

**`DOCUMENTATION_RECONCILIATION = READY_FOR_IMPLEMENTATION`**

---

## 2. Documentation inventory

Edit column: **later, after this plan is approved.** This step does not edit.

### 2.1 Lane-B AGI/ACI evolution (PR #93 corpus)

| Path | Role (1–8) | Historical / current | Authority | Stale vs HEAD? | Current fact if any | Edit later? | Why |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `reports/agi_aci_evolution/EVOLUTION_INDEX.md` | **2 LIVING / CURRENT-TRUTH** + **8** (incomplete related list) | Current index; rows 0008–0009 are historical decisions | High for *navigation*, not for pytest counts | Table stops at 0009; Related list omits V3/V4/closure/integrity; **0010 file exists but is unlisted** | Should point at current-law P5 reports + 0010 | **YES — append only** | This is the evolution table of contents |
| `reports/agi_aci_evolution/TEST_EVIDENCE.md` | **2 LIVING** (append-only log) + **6 EVIDENCE** | Living file; **each section is a dated snapshot** | High for *recorded runs*, not for substituting scopes | Top P5 section is the **early** snapshot (28 / 195 at base `9765161`) | Integrity audit: full suite **2065 passed, 3 skipped** on HEAD | **YES — new section on top; do not rewrite 28/195** | Living log whose newest section must match HEAD |
| `reports/agi_aci_evolution/CAPABILITY_MATRIX.md` | **2 LIVING** | Current measurement table | High for *status letters*; must stay PARTIAL | Cognitive Core Test Status `(28)`; Implementation Status stops at typed eligibility/critic | V4-PIN exists; still not soak-wired | **YES — update that row’s evidence pointers, not charter world-model row** | Claims to be “source of progress measurement” |
| `reports/agi_aci_evolution/GAP_REGISTER.md` | **2 LIVING** | Current ACI gaps | High | ACI-GAP-006/010 evidence is FIX_CORRECTED / typed-reasoning benchmark only | ObservationGrant V4-PIN + security-exit reports exist; ACI-GAP-002 still OPEN | **YES — evidence columns only; do not close world-model P5** | Living gap register |
| `reports/agi_aci_evolution/ARCHITECTURE_MAP.md` | **2 LIVING** (diagram) | Current map | Medium | Cognitive box still “P3 loop” | Loop now includes bind/grant/V4-PIN | **YES — one-line Lane-B evolution P5 note** | Map of actual repo |
| `docs/DOC_TRUTH_MAP.md` | **2 LIVING / CURRENT-TRUTH** (repo-wide) | Current authority map | **Highest** navigation | Section A ends at P4.3; no evolution-P5 pointer | P5 reports + closure gate exist on this branch | **YES — add one Section A row + P5-name disambiguation** | Explicitly “start here” |
| `P5_TYPED_EVIDENCE_REASONING_AUDIT.md` | **1 HISTORICAL** + **4 P5-SPECIFIC** | Snapshot at `9765161` | Historical | 195 / 28 are **correct for that SHA** | n/a | **NO** | Historical audit |
| `P5_TYPED_EVIDENCE_REASONING_BENCHMARK.md` | **1** + **6** | Snapshot | Historical | Dated synthetic metrics | n/a | **NO** | |
| `P5_FIX_CORRECTION_REPORT.md` | **1** | Snapshot (0009) | Historical | 28 tests cited | n/a | **NO** | |
| `P5_PRECISION_REMEDIATION_REPORT.md` | **1** | Snapshot (0010) | Historical | | n/a | **NO** | |
| `P5_FORENSIC_ARCHITECTURE_GATE.md` | **1** + **7 OBSOLETE-BUT-IMPORTANT** | Pre-polarity leak diagnosis | Historical | Findings later remediated | n/a | **NO** | Must not be “fixed” to look closed |
| `P5_NEGATION_ENTITY_REMEDIATION_REPORT.md` | **1** | Snapshot | Historical | | n/a | **NO** | |
| `P5_EPISODE_POLARITY_ARCHITECTURE_REPORT.md` | **1** | Snapshot | Historical | | n/a | **NO** | |
| `P5_SECOND_FORENSIC_VERIFICATION.md` | **1** + **6** | Snapshot (1954 passed, 2 failed at that tip) | Historical | Failures later addressed | n/a | **NO** | Preserve the fail |
| `P5_FINAL_BOUNDARY_AUDIT.md` | **1** | Snapshot (1957/3) | Historical | | n/a | **NO** | |
| `P5_MEMORY_AUTHORIZATION_BOUNDARY_AUDIT.md` | **1** | Snapshot (1980/3) | Historical | | n/a | **NO** | |
| `P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md` | **1** + **7** | Design at its SHA | Historical | Later ObservationGrant | n/a | **NO** | |
| `P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md` | **1** + **7** | Design; process-secret model **superseded by V4-PIN** | Historical | Describes V2/V3-era process key | n/a | **NO** | Current law is V4 reports |
| `P5_OBSERVATIONGRANT_THREAT_MODEL.md` | **1** | Threat model snapshot | Historical | | n/a | **NO** | |
| `P5_OBSERVATIONGRANT_IMPLEMENTATION_REPORT.md` | **1** + **6** | Snapshot (2008/3) | Historical | C1 later found | n/a | **NO** | |
| `P5_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | **1** | Snapshot; records C1 | Historical | C1 later closed by V4 | n/a | **NO** | Preserve C1 |
| `P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md` | **1** + **7** | Unimplemented-at-the-time design | Historical | Implemented then replaced | n/a | **NO** | |
| `P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md` | **1** + **7** | Design snapshot | Historical | | n/a | **NO** | |
| `P5_V3_FINAL_REFINEMENT_ARCHITECTURE.md` | **1** + **7** | Design; constructor DI **superseded** | Historical | V4 removed `secret=` | n/a | **NO** | |
| `P5_V3_IMPLEMENTATION_REPORT.md` | **1** + **6** | Snapshot (2042/3) | Historical | C1 still open then | n/a | **NO** | |
| `P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | **1** | Snapshot of C1 | Historical | | n/a | **NO** | |
| `P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md` | **1** + **7** | Design gate; text says V4 **unimplemented** | Historical | Later implemented | n/a | **NO** | “unimplemented” is true of that gate |
| `P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md` | **1** + **7** | Approved design | Historical | | n/a | **NO** | |
| `P5_V4_IMPLEMENTATION_REPORT.md` | **1** + **6** | Snapshot (2065/3 at implementation) | Historical of **code SHA `afdff25`** | Counts still match identical code tree | n/a | **NO** | |
| `P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | **1** | Forensic of `afdff25` | Historical | 2065/3 | n/a | **NO** | |
| `P5_V4_FINAL_RESIDUAL_BOUNDARY_REVIEW.md` | **1** | Residual classification | Historical | R1–R6 still valid | n/a | **NO** | |
| `P5_FINAL_CLOSURE_GATE_REVIEW.md` | **1** + **6** | Security-exit decision | Historical of the gate | `SECURITY-EXIT-CANDIDATE` | n/a | **NO** | Living indexes *point here*; they do not copy-rewrite it |
| `PR93_INDEPENDENT_PRE_REVIEW_INTEGRITY_AUDIT.md` | **1** + **6** | Integrity decision | Historical of that audit | `PR-INTEGRITY-CONDITIONAL` | n/a | **NO** | This plan does not rewrite it |
| `EVOLUTION_RECORD_0008.md` | **6** | Dated ACCEPT | Historical | “187 targeted tests” at that commit | n/a | **NO** | |
| `EVOLUTION_RECORD_0009.md` | **6** | Dated ACCEPT | Historical | “28 P5-specific” | n/a | **NO** | |
| `EVOLUTION_RECORD_0010.md` | **6** | Dated ACCEPT | Historical | Missing from index table only | n/a | **NO file edit**; **YES index row** | |
| `P4_4_COGNITIVE_STACK_FORENSIC_AUDIT.md` | **1** (pre-P5 justification) | Historical | | n/a | **NO** | Keep; it is why P5 started |
| `p5_typed_evidence_reasoning_latest.json` | **3 GENERATED** | Early-P5 benchmark dump | None as pytest authority | Dated vector | n/a | **NO** | Do not regenerate to “look current” |
| `P4_*` reports + `p4_*.json` | **1** / **3** | P4.1–P4.3 | Historical | Unrelated to this drift | n/a | **NO** | |
| `EVOLUTION_RECORD_0001`–`0007` | **6** | P1–P4.3 | Historical | | n/a | **NO** | |
| `CAPABILITY_MATRIX` world-model row | **2** | Current | High | Still NOT_IMPLEMENTED (correct) | Charter P5 open | **NO change to close it** | Must stay OPEN |

### 2.2 Repo-wide living / operational (mostly out of PR #93 edit set)

| Path | Role | P5 namespace | Edit later for PR #93? |
| --- | --- | --- | --- |
| `docs/DOC_TRUTH_MAP.md` | Living current-authority map | Missing evolution-P5 | **YES** (narrow pointer) |
| `README.md` | Operator surface | No cognitive P5 | **NO** — would mix operator truth with a draft Lane-B PR |
| `docs/CURRENT_TRUTH_SNAPSHOT.md` | **6** snapshot 2026-08-27 / PR #19 | Unrelated | **NO** — name says “current” but it is a **frozen transfer snapshot** |
| `docs/FINAL_TRUTH_AUDIT.md` | **6** 2026-08-27 classification | Unrelated | **NO** |
| `docs/NEXT_DEVELOPMENT_BACKLOG.md` | Living ops backlog | “not new P5 features” = **ops P5**, not this PR | **NO** |
| `docs/canonical/PROJECT_STATE.md` | Pointer to phase state | Wave numbering | **NO** |
| `reports/PHASE_STATE.md` | Wave scorecard | **P5 = Telegram** | **NO** |
| `docs/canonical/ROADMAP.md` | Ops roadmap | **P5 = n8n** | **NO** |
| `docs/architecture/AHOS_COGNITIVE_LOOP_ARCHITECTURE_v1.0.md` | P3 architecture snapshot (base PR #88) | Loop charter | **NO rewrite**; truth-map points at evolution-P5 reports instead |
| `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` | Charter | Charter P5 = world model | **NO** |
| `AHOS_GAP_REGISTER.md` | Operational gaps | No ObservationGrant | **NO** |
| `AGENTS.md` | Dev contract | Points at DOC_TRUTH_MAP | **NO** unless truth-map gains P5 (indirect) |
| `scripts/doc_drift.py` | Scanner allow-list | Already notes cognitive sqlite | **NO** unless a new living path fails drift |
| GitHub PR #93 title/body | **5 RELEASE/PR METADATA** | Title under-scopes | **YES later, separate step** — not in the living-index patch |

Untracked `next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt`: **not documentation surfaces**; must not be added.

---

## 3. Historical evidence protection map

**MUST NOT rewrite** (PROHIBITED). Preserve original test counts, FAIL/C1 findings, and “unimplemented” design-gate language.

| Class | Paths |
| --- | --- |
| Implementation reports | `P5_OBSERVATIONGRANT_IMPLEMENTATION_REPORT.md`, `P5_V3_IMPLEMENTATION_REPORT.md`, `P5_V4_IMPLEMENTATION_REPORT.md` |
| Forensic / residual / closure / integrity | `P5_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`, `P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`, `P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md`, `P5_V4_FINAL_RESIDUAL_BOUNDARY_REVIEW.md`, `P5_FINAL_CLOSURE_GATE_REVIEW.md`, `PR93_INDEPENDENT_PRE_REVIEW_INTEGRITY_AUDIT.md`, plus earlier polarity/memory forensics |
| Design gates (including superseded) | V2/V3/V4 `*_ARCHITECTURE.md`, `*_DESIGN.md`, `P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md` |
| Dated evolution records | `EVOLUTION_RECORD_0008.md`, `0009.md`, `0010.md` (and 0001–0007) |
| Early P5 measurement | `P5_TYPED_EVIDENCE_REASONING_AUDIT.md`, `P5_TYPED_EVIDENCE_REASONING_BENCHMARK.md`, `P5_FIX_CORRECTION_REPORT.md` |
| Generated JSON | `p5_typed_evidence_reasoning_latest.json` and P4 JSON |
| Lane A / soak / freeze | `discovery/**`, `paper_trading/**`, soak reports/scripts, `config/lane_a_freeze.sha256` |
| Frozen transfer snapshots | `docs/CURRENT_TRUTH_SNAPSHOT.md`, `docs/FINAL_TRUTH_AUDIT.md` |
| Ops “P5” pages | `reports/PHASE_STATE.md`, `docs/canonical/ROADMAP.md`, `docs/NEXT_DEVELOPMENT_BACKLOG.md` |

A historical report that says **28** or **1954 passed, 2 failed** is **not stale**. It is a snapshot. Living indexes must **cite** later reports rather than “correct” the old ones.

---

## 4. Living index map

Intended **current repository truth** for Lane-B evolution (inspecting purpose, not filename alone):

| File | Purpose actually served | Required later update |
| --- | --- | --- |
| `docs/DOC_TRUTH_MAP.md` §A | Repo-wide “start here” | Add Lane-B **evolution P5** row; note it is **not** charter world-model P5 and **not** ops/n8n P5 |
| `reports/agi_aci_evolution/EVOLUTION_INDEX.md` | Sequential evolution ToC | Add 0010 row from existing file; extend Related to V4 + closure + integrity; optional new records 0011+ **only if created as new files**, never by editing 0008–0010 |
| `reports/agi_aci_evolution/TEST_EVIDENCE.md` | Append-only pytest log | New **HEAD** section with scoped labels; keep the 28/195 section as the FIX_CORRECTED snapshot |
| `reports/agi_aci_evolution/CAPABILITY_MATRIX.md` | Capability status | Cognitive Core row: point at V4-PIN + security-exit; keep PARTIAL; keep world-model NOT_IMPLEMENTED |
| `reports/agi_aci_evolution/GAP_REGISTER.md` | ACI gaps | ACI-GAP-006 evidence → include ObservationGrant V4-PIN reports; do **not** close ACI-GAP-002 |
| `reports/agi_aci_evolution/ARCHITECTURE_MAP.md` | Structural cartoon | Mention bind / ObservationGrant / instance `K_O` on the cognitive box |

**Not** living P5 truth despite the word “current”: `docs/CURRENT_TRUTH_SNAPSHOT.md` (PR #19 / 2026-08-27).

**Not** the place to announce a draft PR: operator `README.md`.

---

## 5. Test-count semantic analysis

Independently verified on this tree (collect-only + prior full run).

| Number | What it actually was | Scope | Same as 2065? | How to label later |
| --- | --- | --- | --- | --- |
| **28** | Collected tests in `tests/test_typed_reasoning.py` at FIX_CORRECTED / record 0009 (`EVOLUTION_RECORD_0009.md`, `TEST_EVIDENCE.md` P5 section, capability matrix) | **P5 typed-reasoning file only**, early SHA | **No** | `P5 typed-reasoning file count (FIX_CORRECTED snapshot)` |
| **195** | Explicit **regression envelope**: typed_reasoning + lookalike + relevance + cognitive_benchmark + cognitive_loop + cognitive_memory + cognitive_core + self_evolution + multi_mind_council + evolution_validate + cognitive_panel | Listed files at base `9765161` | **No** | `P5 FIX_CORRECTED regression envelope (listed files)` |
| **195 today** | Same file list now collects **204** tests | Envelope files **grew** (typed_reasoning 28→ more; loop tests added) | **No** | Do not silently refresh 195 to 204 inside the old section |
| **308** | Collect-only of `test_typed_reasoning.py` + `test_evidence_support.py` + all `tests/test_p5_*.py` | **Lane-B evolution P5-named test modules on HEAD** | **No** | `Lane-B evolution P5-named modules (collected)` |
| **85** | Prior targeted run of V3 + V4 + `test_p5_observation_grant.py` | Grant/authority subset | **No** | `ObservationGrant adversarial subset` |
| **2065 passed, 3 skipped** | Full `pytest` of the **repository test suite** on HEAD (integrity audit, 224.57s). Same count recorded at V4 implementation/forensic on identical `architecture/`+`tests/` | **Total repository test suite** | **This is 2065** | `total repository pytest (HEAD)` |
| **36/36** | `scripts/freeze_lane_a.py` | Frozen Lane A files | Unrelated to pytest | `Lane A freeze` |
| Historical 187 / 2008 / 2042 / 1954 / 1957 / 1980 | Full or focused counts **at those report SHAs** | Whatever that report listed | **No** | Leave inside those reports |

**Rule for the future living section:** always pair a number with a **scope label** and a **SHA**. Never write “P5 has 2065 tests.”

Recommended HEAD block (to be written later, not now):

```text
total repository pytest (HEAD c36f771 / code afdff25): 2065 passed, 3 skipped
Lane-B evolution P5-named modules (collected on HEAD): 308
ObservationGrant V3+V4+grant files (prior targeted run): 85 passed
Lane A freeze: 36/36
soak: untouched vs origin/main
```

Keep the existing 28/195 block underneath, retitled as a snapshot (title tweak of the living file’s **new** heading is OK; changing the numbers inside the old block is **PROHIBITED**).

---

## 6. P5 scope recommendation

Evidence (commit sequence `b77d617` → `311716f`, diff vs `origin/main`): PR #93 is **one Lane-B product**, not a V4-only hotfix.

Recommended concise definition for living indexes and (later) PR metadata:

> **Lane-B evolution P5 (PR #93):** typed evidence-bound reasoning, episode polarity, memory authorization, ObservationGrant, and V4-PIN instance-owned verification — isolated from soak and Lane A; not charter world-model P5; not ops/n8n P5.

The progression in the integrity audit is **evidence-based** and should be used in the PR **body** Scope section:

`typed reasoning` → `polarity` → `memory authorization` → `ObservationGrant` → `V4-PIN`

V4-PIN is the **authority capstone**, not the entire diff vs `main`. Do not describe the PR as “world model” (charter P5) or “Telegram/n8n” (ops P5).

---

## 7. Current-truth consistency matrix

| Living surface | Contradiction vs tree / tests / closure / PR | Later fix |
| --- | --- | --- |
| `TEST_EVIDENCE.md` top P5 section | Presents 28/195 without saying it is a 0009-era snapshot; HEAD is 2065/3 + 308 P5-named | Append HEAD section; snapshot-title the old section |
| `EVOLUTION_INDEX.md` | No 0010; no V4/closure/integrity; Related stops at typed-reasoning JSON | Append |
| `CAPABILITY_MATRIX.md` Cognitive Core | `(28)` as if current; no ObservationGrant/V4-PIN | Replace test pointer with scoped HEAD labels; keep PARTIAL / isolated PR |
| `GAP_REGISTER.md` ACI-GAP-006 | Stops at FIX_CORRECTED | Add V4-PIN + closure-gate evidence; keep not-soak-wired |
| `GAP_REGISTER.md` ACI-GAP-002 | None — still OPEN | **Leave OPEN** |
| `DOC_TRUTH_MAP.md` | No evolution-P5; P3 loop looks like the last cognitive word | Add row |
| `ARCHITECTURE_MAP.md` | “P3 loop” only | One-line update |
| V4 design docs “unimplemented” | True historically; false as living law | Do not edit; indexes point at implementation/closure |
| Closure gate | Matches code + `SECURITY-EXIT-CANDIDATE` | Pointer only |
| Integrity audit | `PR-INTEGRITY-CONDITIONAL` still correct until indexes/PR metadata move | Pointer only |
| Accidental production-ready / AGI claims on living P5 surfaces | **Not found** in V4/closure/integrity reports | Preserve MERGE/READY/PRODUCTION/LIVE = NO |

---

## 8. Security-status wording recommendation

Living indexes should copy **exactly** these tokens, with a one-line gloss:

```text
P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE
P5_BOUNDARY_STATUS = CLOSED_WITH_DOCUMENTED_RESIDUALS
PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL   # until living indexes + PR metadata are updated
MERGE = NO
READY_FOR_REVIEW = NO
PRODUCTION_READY = NO
LIVE_TRADING = NO
```

**Gloss (allowed):** ObservationGrant production `O.run` verification has an independent security-exit **candidate** with six documented LOW residuals. That is **not** a merge decision, **not** Ready-for-Review, **not** production deployment, **not** live trading, **not** autonomous execution, **not** AGI, **not** ACI.

**Forbidden glosses:** “P5 is done”; “P5 passed so merge”; “security closed means production-ready”; “2065 tests means intelligence”; “charter P5 complete”.

After living indexes are updated, a **later** integrity re-audit may change `PR93_INTEGRITY`; this plan does not.

---

## 9. PR title recommendation

**Do not change the title in this step.**

| | Text |
| --- | --- |
| **Current** | `P5 ObservationGrant V4-PIN implementation (DRAFT — not ready for review)` |
| **Proposed (later)** | `P5 typed evidence-bound reasoning and ObservationGrant V4-PIN (DRAFT — not ready for review)` |

**Rationale:** Names the full Lane-B product (typed evidence-bound reasoning) and the authority capstone (ObservationGrant V4-PIN). Keeps DRAFT / not-ready. Avoids listing every intermediate (polarity, memory auth — those belong in the body). Avoids “world model” and ops-P5 language.

The proposed title **does** represent the PR vs `main` at professional length. The body must still spell the progression.

---

## 10. PR description structure recommendation

**Do not edit the description in this step.** It currently summarizes only the closure/integrity tokens. It **should** be restructured **later** (still draft) into:

1. **Executive summary** — Lane-B evolution P5; draft; not merge; not Ready; not production; not live trading; not AGI/ACI; not charter world-model P5.
2. **Scope** — typed reasoning → polarity → memory authorization → ObservationGrant → V4-PIN; vs `main` vs vs V3 SHA.
3. **Security evolution** — C1 at V3; V4-PIN instance `K_O`; pointer to closure gate.
4. **Evidence** — pointers to implementation, forensic, residual, closure, integrity reports (links, no pasted rewrites of conclusions).
5. **Tests** — scoped counts from §5 (2065 total repo; 308 P5-named collected; do not say “2065 P5 tests”).
6. **Residuals** — R1–R6; POST-P5-HARDENING; not blocking security-exit.
7. **Known non-goals** — soak ingest, production mint adapter, world model, live execution, Ready/merge.
8. **Current readiness** — `SECURITY-EXIT-CANDIDATE`; `PR-INTEGRITY-CONDITIONAL` until this plan is implemented.
9. **Merge / Ready status** — `MERGE = NO`; `READY_FOR_REVIEW = NO`; remain draft.

---

## 11. Prohibited modifications

| Action | Mark |
| --- | --- |
| Rewrite any historical audit/implementation/forensic conclusion | **PROHIBITED** |
| Change 28, 195, 187, 1954, 2008, 2042, etc. inside historical reports or inside the existing TEST_EVIDENCE snapshot block | **PROHIBITED** |
| Replace “28 tests” with “2065 tests” as if the same scope | **PROHIBITED** |
| Delete or rename evidence files / JSON | **PROHIBITED** |
| Close ACI-GAP-002 (charter world model) because evolution P5 advanced | **PROHIBITED** |
| Edit Lane A, soak, freeze hashes | **PROHIBITED** |
| Edit `PHASE_STATE` / ops `ROADMAP` “P5 Telegram/n8n” to mean ObservationGrant | **PROHIBITED** |
| Rewrite `AHOS_COGNITIVE_LOOP_ARCHITECTURE_v1.0.md` into a V4-PIN spec | **PROHIBITED** (pointer from truth map instead) |
| Claim merge, Ready, production, live trading, AGI, ACI | **PROHIBITED** |
| Modify production code, tests, architecture, PR title/body **in the documentation-index implementation step without a separate explicit metadata task** | **PROHIBITED** for the index patch; PR metadata is a **later separate** step |
| Implement this plan in the same commit as the plan itself | **PROHIBITED** (this file is plan-only) |

---

## 12. Safe future implementation sequence

1. **Approve this reconciliation plan** (human). Do not treat the plan file as having updated the indexes.
2. **Update only living indexes** listed in §4: `EVOLUTION_INDEX.md` (append 0010 + Related), `TEST_EVIDENCE.md` (new HEAD section), `CAPABILITY_MATRIX.md` (Cognitive Core row), `GAP_REGISTER.md` (ACI-GAP-006/010 evidence, not ACI-GAP-002 close), `ARCHITECTURE_MAP.md` (one line), `docs/DOC_TRUTH_MAP.md` (one Section A row + namespace note).
3. **Do not** create a new `CURRENT_TRUTH_SNAPSHOT` for P5; that filename is an ops transfer snapshot. If a P5 current-law blurb is needed, it belongs in `EVOLUTION_INDEX.md` and `DOC_TRUTH_MAP.md`.
4. **Update PR metadata separately** (title §9, body §10). Remain draft. `MERGE = NO`. `READY_FOR_REVIEW = NO`.
5. **Documentation consistency audit** (read-only): living files vs HEAD counts vs “do not imply merge”; confirm historical files unchanged (`git diff` should not touch `P5_V3_*`, forensics, records 0008–0010 bodies, JSON).
6. **Re-run pre-review integrity audit** (read-only). Only then may `PR93_INTEGRITY` be reconsidered.
7. **Only then** consider a human Ready-for-Review gate. This plan does not authorize that gate.

---

## 13. Final recommendation

Proceed with a **narrow living-index patch** after approval. The architecture and test evidence are **not** ambiguous once counts are scoped and the three “P5” names are kept apart. Historical evidence stays immutable. PR stays draft.

```text
DOCUMENTATION_RECONCILIATION = READY_FOR_IMPLEMENTATION
P5_SECURITY_EXIT = SECURITY-EXIT-CANDIDATE
PR93_INTEGRITY = PR-INTEGRITY-CONDITIONAL
MERGE = NO
READY_FOR_REVIEW = NO
PRODUCTION_READY = NO
LIVE_TRADING = NO
```
