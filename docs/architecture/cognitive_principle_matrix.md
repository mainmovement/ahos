# AHOS — COGNITIVE PRINCIPLE MATRIX (W9/P0 → W11 schema v2)
Machine-readable source of truth: `config/cognitive_principles.yaml` (**63 principles, 6 domains,
schema v2** — W10 §14 fields: principle_id, source_thinker_or_school, domain, principle,
agent_capability, probe, contract, test, evidence_requirement, status + W9 law fields kept).
Human runtime view: docs/architecture/cognitive_agent_runtime_matrix.md (full corpus table,
exclusions, measured totals: EXISTING 23 / PARTIAL 21 / DEFINED 19).
`source_thinker_or_school` is historical-intellectual provenance ONLY — never impersonation,
never authority, no fabricated quotes; uncertain attribution = UNVERIFIED/excluded
(Edward Pearson · LaVaughn Wright · G. R. McKie · Chad Davis).
Rule: principle → capability → probe → contract → test → evidence.

> SUPERSESSION NOTE (W11, 2026-08-13): the domain paragraphs and the W9-era audit table below are
> retained as HISTORY. Ranges and counts changed (CRYPTO-01..14, SEC-01..11, MATH-01..16,
> ENG-01..11, SCI-01..03, HUM-01..08); the W9 table's "585/585", trigger and count claims are
> superseded by measured values (716/716 via W11A-01; trigger census W10A-02 → F1). Current
> per-principle truth lives in the yaml + cognitive_agent_runtime_matrix.md.

## Domain A — Cryptography/Decentralization (CRYPTO-01..06)
Nakamoto (trust-minimization, append-only adversarial history) · Buterin (modularity, explicit
tradeoffs, governance boundaries) · Wood (deterministic state transitions, formal interfaces) ·
Nazarov (oracle integrity, never one feed) · Adams (liquidity = truth of markets).
Probes: TRUST_ASSUMPTION, PROVENANCE, SOURCE_DISAGREEMENT, STATE_TRANSITION, LIQUIDITY_ILLUSION.

## Domain B — Security/Adversarial (SEC-01..04)
Defensive-research tradecraft generalized: attack-surface thinking, malicious-input default,
provider-compromise/correlated-failure realism, data-poisoning awareness.
Probes: SECRET_BOUNDARY, ADVERSARIAL_INPUT, PROVIDER_COMPROMISE, CORRELATED_FAILURE, DATA_POISONING.
(Anti-impersonation note: no offensive technique is reproduced; lenses only.)

## Domain C — Mathematics/Formal (MATH-01..12)
Euclid (definitions) · Pythagoras/Archimedes (invariants, measurement honesty) · Al-Khwarizmi
(procedure) · Ibn al-Haytham (observation) · Euler/Gauss (structure, error distributions) ·
Newton/Leibniz (models serve observation) · Poincaré (regimes) · Hilbert/Cantor (formal
classification) · Gödel (self-limitation) · Turing/von Neumann (deterministic computation) ·
Ramanujan (pattern ≠ proof) · Tao (multi-step rigor, explicit uncertainty).
CRITICAL LAW: pattern alone never proves; AI confidence is not evidence.

## Domain D — Engineering (ENG-01..08)
Ritchie/Thompson (simple primitives) · Torvalds (transparent history) · Dijkstra (correctness
first) · Knuth (measurable rigor) · Carmack (deterministic performance) · Hopper (operable
abstraction) · Martin (clean boundaries) · Berners-Lee/Gosling/Stroustrup/Hejlsberg (protocols,
typed interfaces).
Probes: COMPLEXITY, DEPENDENCY, INTERFACE, DETERMINISM, REGRESSION, REPLAY.

## Domain E — Falsification (SCI-01..03)
Every hypothesis ships with kill-criteria, minimum evidence, stopping conditions; negative
evidence is first-class (kept, never repaired silently).

## Domain F — Product/Human (HUM-01..05)
da Vinci/Jobs (simplicity), Kubrick/Spielberg/Disney (coherent honest narrative), Tesla/Einstein
(vision + humility), Musk (delete first), Ghodrati/owner (capital preservation, evidence over
appearance, $0 constraint, UNKNOWN stays UNKNOWN).

## CURRENT ARCHITECTURE AUDIT AGAINST THE MATRIX (evidence-based, 2026-08-13)
| Matrix item | Status | Workspace evidence |
|---|---|---|
| PROVENANCE/append-only | EXISTING | 585/585 obs→raw sha join OK; DB triggers; manifests sha-pinned |
| STALE_DATA law | EXISTING | PT-X3-v2; fired LIVE (t9/t10: 11× NO_DATA(STALE_OBSERVATION)); R-30 |
| Trust assumptions | EXISTING | UNKNOWN≠PASS gates; no-claim-without-probe law (pal_probe ids) |
| Conservation/invariants | EXISTING | cash+alloc==20.0000 exact each cycle; test-pinned |
| Replay/determinism | EXISTING | future-pollution replay tests; idempotent lesson builder |
| Falsification culture | EXISTING | H1–H13/baseline negative evidence preserved; cards pre-registered |
| Statistical sufficiency gates | EXISTING | MIN_N=200/MIN_POS=20/30-closed bars enforced in code+reports |
| Survivorship retention | EXISTING | losing/trapped cohorts kept; R-23/R-29 anomalies preserved unpatched |
| Confidence-inflation lint | PARTIAL | auditor rule documented; Persian runtime lint = telegram_ai (untested live) |
| Source-disagreement probe | DEFINED only | single security source per chain = KNOWN RISK (recorded) |
| Complexity/dependency probes | PARTIAL | no automated import/coupling lint yet |
| Red-team runtime lints | DEFINED | verdict enum specced (REJECT/INVALID/INSUFFICIENT_EVIDENCE/NEEDS_MORE_DATA) |
| Model-router probes | DEFERRED | all keyless AI tiers probed dead/key-gated; DETERMINISTIC_ONLY floor holds |

## Internal-consistency check (P0 exit criterion)
No conflicts found between matrix and frozen governance. One recorded tension: matrix wants
multi-source security probes; reality is one source per chain (free-tier) — resolved HONESTLY
by confidence-capping single-source claims (probe DEFINED, risk logged), not by pretending
coverage. P0 CONSISTENT → P1 authorized by W9 §19.
