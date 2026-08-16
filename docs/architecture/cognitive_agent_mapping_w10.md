# AHOS W10 — COGNITIVE AGENT MAPPING (audit-companion, DRAFT-proposals only)
Status: AUDIT ARTIFACT under W10 scope · 2026-08-13 · Lane-B only · NOTHING in this file is
registered architecture until it passes the normal governance path (registration + version bump +
owner approval). W10 created zero runtime agents and changed zero config.

## 0. Derivation standard (binding for this document)
- Named persons are **intellectual provenance only** (`source_inspiration`). No personality
  imitation, no role-play, no voting members, no claim to reproduce private thinking.
- Every derivation follows the W9 pipeline: **PRINCIPLE → CAPABILITY → CONSTRAINT → PROBE →
  EVIDENCE → IMPLEMENTATION.**
- Status enum for this file:
  - **MAPPED** — already operationalized in W9 (`config/cognitive_principles.yaml`, 38 principles).
  - **DRAFT-W10** — new engineering derivation proposed here; NOT registered; carries a failure
    mode and an evidence requirement; requires governance registration before any use.
  - **EXCLUDED** — no publicly verifiable method corpus documented; deriving a principle would be
    fabrication (violates DATA > MODEL OPINION / no-claim-without-evidence law).
- Deriving from a documented **school/era** is allowed when individual attribution is unsafe
  (the era's public record carries the method, not the person).

## A. Audit of the existing W9 matrix (measured, not asserted)
| Measured (W10A-12) | Value | W9 docs claim | Verdict |
|---|---|---|---|
| principle count | **38** | "35 principles" | DOC DRIFT (low) — docs/R-31 say 35; yaml holds 38 |
| probe_status EXISTING | 24 | — | sampled below |
| probe_status PARTIAL | 12 | — | honest (mechanism partial) |
| probe_status DEFINED | 2 (CRYPTO-05, MATH-07) | — | honest (spec only) |
| domains | 6 (crypto 6, security 4, math 12, eng 8, falsification 3, product 5) | 6 | OK |

### A.1 EXISTING-claim spot verification (probe-anchored)
| Claim | Result | Evidence (audit probe) |
|---|---|---|
| CRYPTO-02 "UPDATE/DELETE-abort triggers **on all stores**" (probe_status EXISTING) | **CONTRADICTED** | W10A-02: paper_trading 34 triggers/17 tables = full; e01_discovery = **0**; ahos_local = **0**. Claim true for 1/3 stores. |
| CRYPTO-06 / AG-07 realizable-vs-displayed EXISTING | VERIFIED | W10A-05: latest sweep displayed 17.8759 vs realizable 14.5329, 11/11 EXECUTABLE_FULL, model PT-REALIZABLE-v1 |
| MATH-02 conservation invariant EXISTING | VERIFIED | W10A-04: cash 1.8984375 + allocated 18.1015625 = 20.0000000 exact |
| MATH-03/10 replay & determinism pins EXISTING | VERIFIED | test suite 145/145 incl. future-pollution replay + determinism pins (W10A-11) |
| MATH-04 observation-over-authority (pre-registration) EXISTING | VERIFIED | research/SEARCH_SPACE_REGISTRY.json = 9 locked cells; test-pinned guards |
| SEC-01 secret boundary EXISTING | VERIFIED | env-only token law in code; R-28 compromise protocol executed; no secret in repo (spot scan) |
| AG-21 sha-linked provenance EXISTING | VERIFIED (number stale) | W10A-03: obs→raw join **646/646 (100%)**; yaml text says 585/585 (stale count, structure true) |
| STALE_DATA law (PT-X3-v2) EXISTING | VERIFIED | W10A-16/18: latest live cycle `paper_cycle_20260813_012214.json` decisions {NO_DATA: 11}; decide_v1 byte-frozen as `decide_v1` |
| AG-09 security vetoes EXISTING | VERIFIED | W10A-14: learning block `honeypots_avoided: 3`; live rejects in every cycle file |
| PROVENANCE/TRUST probe battery EXISTING | VERIFIED but **STALE** | W10A-06: PRB-20260811-001..017 exist; battery age ≈31h vs daily cadence ⇒ OVERDUE (finding F8) |

**Consequence:** exactly one EXISTING-claim in the matrix is contradicted by measurement
(CRYPTO-02 trigger coverage) and two `evidence` strings in the registry carry stale counters
(AG-02, AG-21). No other overclaim detected. Everything else the matrix calls EXISTING that this
audit probed was confirmed against files/stores/tests.

## B. W10 named-list expansion (schools → engineering abstractions)
Format per row: `Documented public method → Operational principle → Capability (target agent) —
Constraint — Probe — Evidence requirement — Possible implementation — Status`.

### B.1 Protocol / decentralization school
| Inspiration | Derivation (compressed) | Status |
|---|---|---|
| Nakamoto | trust-minimization; public verifiable append-only history → claim⇔evidence linkage; adversarial ordering of records — no claim without linked artifact — TRUST_ASSUMPTION_PROBE — every claim carries evidence ids — already: raw_payload sha chain + register | **MAPPED** CRYPTO-01/02 (CRYPTO-02 overclaims coverage ⇒ F1) |
| Buterin | modularity with explicit tradeoffs; governance boundaries written down → lane/track isolation; every change card carries a tradeoff note — no silent boundary crossing — INTERFACE_PROBE — contract tests per module — already: two-lane law + versioned cards | **MAPPED** CRYPTO-03 |
| Wood | deterministic state transitions behind formal interfaces → FSM/event-sourced lifecycles — nondeterminism = INVALID — STATE_TRANSITION_PROBE — replay-parity — lifecycle FSM + position events | **MAPPED** CRYPTO-04 |
| Yakovenko | verifiable time-ordering as a first-class artifact; measure, never assume, throughput → event timestamp integrity checks; measured per-cycle cost accounting — timestamps must survive audit — TIMESTAMP_INTEGRITY_PROBE + PERF_MEASUREMENT — monotonic-source audit + runtime rows per cycle — add obs-age/ordering assertions to collector diagnostics; timing rows already in cycle reports | **DRAFT-W10** (probe DEFINED only) |
| Nazarov | oracle integrity; never one feed → ≥2 sources or confidence-capped single-source — uncorroborated flip capped — SOURCE_DISAGREEMENT_PROBE — per-source availability matrix — providers.yaml chains exist; disagreement probe DEFINED | **MAPPED** CRYPTO-05 (probe DEFINED ⇒ F-adjacent honesty) |
| Adams | liquidity is the only executable truth → realizable-before-displayed law — displayed-only claim = REJECT — LIQUIDITY_ILLUSION_CHECK — per-position realizable/displayed ratio — PT-REALIZABLE-v1 live | **MAPPED** CRYPTO-06 |
| Kulechov | risk parameters are governance objects; liquidation rules explicit ex-ante → every risk threshold lives in a versioned card with failure criteria — no threshold outside cards — RISK_PARAMETER_CARD_CHECK — card↔code constant diff = empty — cards already hold PT constants; diff-lint is the candidate probe | **DRAFT-W10** (target AG-08/AG-23) |
| CZ (operator school) | incident-response reserves and user-protection accounting are designed, not improvised → FAILURE_RESERVE concept: pre-declared loss/contingency classes — no retrospective relabeling of losses — RESERVE_CARD_CHECK — loss classes enumerated before incidents — trapped-capital taxonomy already implements the spirit (TRAPPED/TOTAL_LOSS law) | **DRAFT-W10** (thin engineering corpus; kept narrow) |
| Hoskinson | formal specification and staged, review-gated rollout → spec-before-code for governance-touching modules; promotion only after external review chain — unreviewed promotion blocked — SPEC_BEFORE_CODE + REVIEW_CHAIN_CHECK — review log links — council doc-loop exists; runtime pending | **DRAFT-W10** (maps AG-11/AG-23) |
| McCaleb | simple robust protocols survive; federation tradeoffs stated → prefer boring mechanisms; document trust topology of each data path — undocumented trust path = UNSUPPORTED — TRUST_TOPOLOGY_DOC_CHECK — topology note per PAL capability — providers.yaml carries chains; topology notes candidate | **DRAFT-W10** |
| Armstrong | regulatory/compliance boundary is a design constraint → legal constraints compile into the architecture (LIVE TRADING CLOSED is law in code/docs) — compliance breach = SAFE HALT — LEGAL_BOUNDARY_LINT — forbidden-action tests — live-trading ban exists as policy + absent exchange glue | **DRAFT-W10** |
| Saylor | treasury claims need public, mark-to-market-honest accounting → realized/unrealized separation everywhere; thesis statements versioned — mark-price fiction banned (already law) — ACCOUNTING_HONESTY_CHECK — equity reported on both bases — realizable sweep already does this for paper equity | **DRAFT-W10** (narrow; overlaps PT-REALIZABLE law) |
| Larsen | settlement/finality semantics must be explicit → distinguish observed/executable/settled states in every value claim — unpriced settlement forbidden (PT-X3-v2 law) — FINALITY_SEMANTICS_CHECK — state fields separate obs vs settled — position_state_event + settle guards exist | **DRAFT-W10** |

### B.2 Adversarial / security school (defensive lessons only — no technique reproduction)
| Inspiration | Derivation | Status |
|---|---|---|
| Mitnick / social-engineering record | the human and the interface are attack surfaces → secret-handling law, chat-injection distrust — pasted secret = COMPROMISED — SECRET_BOUNDARY scan — no secret in files/logs/git — R-28 protocol executed | **MAPPED** SEC-01 |
| Poulsen (journalistic/security verification) | claims about systems must be independently reproduced → auditor ≠ producer; reproduction before acceptance — self-certified claim REJECT — REPRODUCTION_CHECK — second-run parity — run_all_checks replay culture | **MAPPED** SEC-01/MATH-09 area |
| McKinnon case (defensive lesson) | default credentials / flat trust are the classic hole → default-state and exposed-surface audit — no unauthenticated surface by default — DEFAULT_STATE_SCAN — config census vs defaults — env-only secrets law; candidate scan probe | **DRAFT-W10** |
| Jonathan James case (defensive lesson) | weak auth on high-value systems is fatal → credential-strength + access-minimization audit — shared/weak tokens forbidden — CREDENTIAL_AUDIT — rotation/scope records — R-28 rotation demand stands | **DRAFT-W10** |
| Albert Gonzalez case (defensive lesson) | injection-class input discipline at every boundary → parameterized queries only; conjunction evaluator injection-proof — string-built SQL forbidden — INJECTION_REGRESSION — fuzz/edge fixtures pass — evaluate_conjunction is injection-proof (test-pinned) | **DRAFT-W10**, partially EXISTING (SEC-02) |
| Adrian Lamo cases (defensive lesson) | misconfiguration is the quiet breach → misconfiguration/open-proxy audit of services — unknown exposure = UNKNOWN reported — MISCONFIG_SCAN — service/config diff review — VPS/n8n activation gate documents this | **DRAFT-W10** |
| Morris-worm era (1988; incl. era handles treated at ERA level — "Astro/Zap/R0bert" individual methods not publicly verifiable) | monoculture + unattended trust fail at scale; institutions needed (CERT emerged) → correlated-failure modeling; incident-response runbook as artifact — single-source dependence recorded — CORRELATED_FAILURE probe + INCIDENT_RUNBOOK_CHECK — diversity/accounting rows — SEC-03 partial; runbook = candidate | **DRAFT-W10** (era-level, SEC-03 adjacent) |
| Assange / publication-integrity record | cryptographic timestamping + source protection for disclosures → provenance manifests; tamper-evident publication — unprovenanced artifact excluded from claims — PROVENANCE_PROBE — manifest sha chains — MANIFEST.json + sha-join 646/646 | **MAPPED** SEC-04/CRYPTO-01 area |
| GeoHot (boundary-testing record) | systems reveal truth at their edges → fault-injection as standard proof — untested edge = UNSUPPORTED — FAULT_INJECTION_SUITE — 6h/16h stale-injection tests exist — tests/test_paper_trading_v32.py (10 tests) | **DRAFT-W10**, partially EXISTING (SEC-02/R-30 method) |
| Angleton (counterintelligence doctrine) | wilderness-of-mirrors: deception is possible at every layer; double-check the checker → provenance cross-examination; corroboration before confidence upgrade — single-channel anomaly ≠ truth — DECEPTION_LINT + SOURCE_DISAGREEMENT — anomaly register with independent confirmation — R-23/R-29 register discipline is the seed | **DRAFT-W10** |

### B.3 Mathematics / formal school
| Inspiration | Derivation | Status |
|---|---|---|
| Euclid / Pythagoras / Archimedes | definitions before use; invariants; measurement honesty | **MAPPED** MATH-01/02 |
| Al-Khwarizmi | named, reproducible procedures end-to-end | **MAPPED** MATH-03 |
| Omar Khayyam | exhaustive classification of cases; calendar-grade measurement calibration → every enum case reachable+documented; periodic recalibration of constants — unclassifiable input ⇒ UNKNOWN case required — CLASSIFICATION_COVERAGE + CALIBRATION_SCHEDULE — enum-coverage tests; recalibration dates on MODEL constants (gas table) — partially present (MATH-08, gas MODEL tags) | **DRAFT-W10** |
| Ibn al-Haytham | experiment over authority; forward observation | **MAPPED** MATH-04 |
| Euler / Gauss | structural reasoning; error distributions; sufficiency gates | **MAPPED** MATH-05 |
| Riemann | unproven premises are labeled premises, not facts → PREMISE registry: every model assumption (fee/slip/gas classes) registered as measured-hypothesis with owner + review date — hidden premise = defect — PREMISE_REGISTRY_CHECK — premise table diff review — PT-COST-v1/PT-REALIZABLE-v1 headers partially do this; registry candidate | **DRAFT-W10** (MATH-06 adjacent) |
| Poincaré | regimes/nonlinearity; single-window claims capped | **MAPPED** MATH-07 (probe DEFINED) |
| Hilbert / Cantor | formal classification structures; decidability of states | **MAPPED** MATH-08 |
| Gödel | no system certifies itself; external review chain | **MAPPED** MATH-09 |
| Turing / von Neumann | computable, deterministic, architecture-conscious engines | **MAPPED** MATH-10 |
| Ramanujan | pattern is hypothesis, never proof | **MAPPED** MATH-11 |
| André Weil | structural correspondences must be total → every bridge between representations (SQLite⇄PG, raw⇄normalized) is a total, tested function — partial mapping = defect list — BRIDGE_TOTALITY_CHECK — unmapped cases enumerated — PG parity audit (33/33 drift) is the honest exemplar | **DRAFT-W10** |
| Grothendieck | rebuild foundations until obstruction dissolves ("rising sea"); but unbounded abstraction burns resources → abstraction only with deletion pressure and measured obstruction — architecture-for-itself = STOP (owner law) — ABSTRACTION_DEBT_REVIEW — each new layer names the obstruction it removes — two-lane evolution discipline | **DRAFT-W10** (constrained by HUM-03/04) |
| Terence Tao | multi-step rigor; uncertainty explicit end-to-end | **MAPPED** MATH-12 |

### B.4 Software / systems engineering school
| Inspiration | Derivation | Status |
|---|---|---|
| Ritchie / Thompson | small composable primitives; stdlib discipline | **MAPPED** ENG-01 |
| Torvalds | transparent change history; regression gates | **MAPPED** ENG-02 |
| Dijkstra | correctness before convenience | **MAPPED** ENG-03 |
| Knuth | measurable algorithmic rigor; cost accounting | **MAPPED** ENG-04 |
| Carmack | deterministic performance; bounded retries | **MAPPED** ENG-05 |
| Hopper | abstraction that stays operator-readable | **MAPPED** ENG-06 |
| Robert C. Martin | clean boundaries; acyclic per-lane imports | **MAPPED** ENG-07 |
| Berners-Lee / Gosling / Stroustrup / Hejlsberg | interoperable protocols; typed contracts | **MAPPED** ENG-08 |
| Guido van Rossum | readability is governance; explicit > clever → operator-auditable reports; plain-language verdicts — unreadable status = redesign — READABILITY_LINT — one-screen status review — periodic_report_*.txt present | **DRAFT-W10** (ENG-06 adjacent) |
| Stallman | user sovereignty over tools; license/dependency discipline → dependency census incl. license class; $0-stack audit — hidden proprietary dep = defect — DEPENDENCY_LICENSE_AUDIT — census artifact updated per wave — stdlib+pandas+pytest+PyYAML stack | **DRAFT-W10** |
| Margaret Hamilton | fault tolerance designed pre-flight; priority-ordered asynchronous work; "what-if" budgets → FAULT_TREE per agent; priority classes in run-ledger (P3 input) — unbudgeted failure path = CRITICAL gap — FAULT_TREE_COVERAGE — each CRITICAL agent names failure_behavior (registry already requires it) — registry `failure_behavior` field is the seed | **DRAFT-W10**, partially EXISTING |
| Tim Berners-Lee | (see above, ENG-08) open, inspectable protocols | **MAPPED** ENG-08 |
| James Gosling / Stroustrup / Hejlsberg | (see above) | **MAPPED** ENG-08 |

### B.5 Science / product / communication school
| Inspiration | Derivation | Status |
|---|---|---|
| da Vinci / Jobs | simplicity as a feature; one-screen truth | **MAPPED** HUM-01 |
| Kubrick / Spielberg / Disney | coherent, honest narrative to the human (no certainty theater) | **MAPPED** HUM-02 |
| Tesla | experiment notebook discipline: iterate, log, publish failures → per-experiment journals with negative results first-class — unpublished negative = survivorship violation — EXPERIMENT_JOURNAL_CHECK — t0..t11 collection journals exist — research/experiments/e01_collection_t* | **DRAFT-W10**, partially EXISTING |
| Einstein | thought experiments must land as testable consequences; humility about what is proven — untestable speculation marked PERSPECTIVE, not claim — TESTABILITY_LINT — every vision doc ends in probes — phased architecture behind evidence gates | **DRAFT-W10** (HUM-03 extended) |
| Jules Verne | disciplined imagination: scenarios as labeled fiction that generate requirements → FUTURE_SCENARIO tag; a scenario is never evidence — scenario text quarantined from evidence — SCENARIO_QUARANTINE_LINT — tag-present check — roadmap docs as labeled scenarios | **DRAFT-W10** |
| Leonard Cohen | economy and precision of language → report language lint extended: fewer, exact words — inflated wording = REJECT — LANGUAGE_ECONOMY_LINT — Persian confidence-inflation lint exists (PARTIAL) — HUM-02 extension | **DRAFT-W10** |
| Steve Jobs / Elon Musk | delete-first; iterate against constraints | **MAPPED** HUM-01/04 |
| Walt Disney / Spielberg / Kubrick | (see above) | **MAPPED** HUM-02 |

## C. Exclusions (the honest table — applying CRYPTO-01/MATH-04 to the request itself)
| Name supplied | Audit result | Verdict | What would change it |
|---|---|---|---|
| Edward Pearson | No publicly verifiable engineering/scientific method corpus attributable to this name was identifiable to this audit | **EXCLUDED** (UNVERIFIABLE_PROVENANCE) | A citable public record of methods (papers, code, documented doctrine) |
| LaVaughn Wright | Same — no identifiable public method corpus | **EXCLUDED** (UNVERIFIABLE_PROVENANCE) | Same |
| G. R. McKie | Same; supplied "where relevant" — no documented corpus found; relevance not establishable | **EXCLUDED** (UNVERIFIABLE_PROVENANCE) | Same |
| "Astro/Zap/R0bert" era handles | Individual method corpora not publicly verifiable; the **era** (1988 Morris worm → CERT; disclosure culture) is documented | **DERIVED AT ERA LEVEL ONLY** (B.2 Morris-era row) | Verifiable individual records |
No principle was invented for these names. Inventing one would be exactly the "fake evidence
reference" failure W10 §6 is hunting.

## D. Agent-of-agents execution chain (design audit — not built)
Binding order (W9 §1 extended to runtime shape):

```
Problem card (human-authored)
  → AG-01 Orchestrator            [authority: OBSERVE only; routes; may not alter content;
                                    MISSING today ⇒ no runtime chain exists — designed absence]
  → Specialist selection          [registry-driven; EXECUTABLE = EXISTS, or PARTIAL whose
                                    evidence is executable; PLANNED/MISSING ⇒ skipped, recorded
                                    UNAVAILABLE — never simulated]
  → Independent analysis          [ANALYZE-class agents; isolated invocations; no cross-talk;
                                    each returns contract v1 envelope or error envelope]
  → Evidence collection/check     [AG-21: every evidence id must resolve to a real artifact;
                                    unresolvable ⇒ envelope error=CONTRACT_BREAK, claim void]
  → Disagreement detection        [AG-13: conflicting envelopes ⇒ DISAGREEMENT record;
                                    NEVER silent averaging; single-agent answers labeled
                                    SINGLE_SOURCE]
  → Red Team                      [AG-14: CHALLENGE + VETO over CLAIMS/promotions only;
                                    verdicts REJECT / INVALID / INSUFFICIENT_EVIDENCE /
                                    NEEDS_MORE_DATA — each with probe_id; may never edit data]
  → Deterministic validation      [AG-15-class deterministic engine replays/validates; only
                                    deterministic engines DECIDE; AI envelopes are advisory]
  → Verdict                       [categorical; carries confidence enum + evidence ids;
                                    DISAGREEMENT surfaces to human; numbers from AI never
                                    authoritative]
```

### D.1 Authority audit (who may do what)
| Class | Agents | W10 check |
|---|---|---|
| May ADVISE | AG-11, AG-12, AG-18, AG-20 (+ ANALYZE-class PARTIALs) | consistent with W9 law (AI ⊂ {ANALYZE, ADVISE, CHALLENGE}) |
| May VETO | AG-09 (deterministic security gate), AG-14 (claims), AG-23 (governance; human-gated) | **ambiguity flagged F5**: W9 doc §2 names Red Team as VETO holder but is silent on deterministic VETO (AG-09 already vetoes live in Lane A — the law text should be amended to acknowledge deterministic safety vetoes explicitly) |
| OBSERVE-only | AG-01, AG-02, AG-06, AG-17, AG-19, AG-22 | consistent |
| May produce HYPOTHESES | AG-18, AG-20, AG-11 | none may promote (forbidden_authority correct) |
| May NEVER generate authoritative numbers | every AI-form agent (AG-11/AG-12 + any future AI) | contract note exists; runtime enforcement pending (F4) |
| May NEVER alter frozen governance | all except the human via AG-23 path | AG-23 holds PROMOTE — acceptable ONLY as documented human gateway (F5); require `human_gate: true` marker in a future contract version |
| Human approval MANDATORY at | PROMOTE transitions; frozen-card changes; contract/schema changes; Lane-A store migrations; new paid providers | unchanged; W10 changed none of these |

### D.2 Chain-level failure audit
| Risk | Where | Current design answer | W10 verdict |
|---|---|---|---|
| Orchestrator absent | AG-01 MISSING | SAFE HALT / DEGRADED policy stated | sound (designed absence; no fake runtime claimed) |
| Council/router dead (no keys) | AG-11/AG-12 | DETERMINISTIC_ONLY floor (live-verified PRB-20260811-AI-001) | sound |
| Single-source data | AG-06/AG-09 chains | single-source ⇒ confidence capped (CRYPTO-05) | sound, probe only DEFINED |
| Disagreement suppressed | AG-13 | DISAGREEMENT record mandated | sound in design; runtime absent (PARTIAL honest) |
| Circular invocation | AG-11↔AG-13 dependency cycle (W10A-07) | none — registry does not validate acyclicity | **F2: must be resolved before any runtime** |
| AI numeric leakage | any AI agent | contract note + footer law; no runtime check yet | F4 additive contract field needed |
| Evidence-id forgery | any producer | AG-21 resolution step (D chain) | designed; runtime enforcement = P3+ |

## E. What this mapping deliberately does NOT do
- No runtime agents, no orchestrator, no orchestration code created.
- No principles registered; the yaml is untouched (38 principles stand; the 26 DRAFT-W10 rows
  above — 8 in B.1, 7 in B.2, 4 in B.3, 3 in B.4, 4 in B.5 — are proposals awaiting governance).
- No probes invented "to look complete": every proposed probe is marked DEFINED (spec) or mapped
  to measured EXISTING behavior.
- No capability claimed without a measured anchor; every MAPPED row names its artifact.
