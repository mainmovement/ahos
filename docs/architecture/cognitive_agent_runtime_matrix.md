# AHOS — COGNITIVE AGENT RUNTIME MATRIX (corpus → runtime mapping)
W11 §8–§9 · machine-readable truth: config/cognitive_principles.yaml (63 principles, 6 domains,
schema v2). This document is the human view of the same table + corpus coverage audit. Law:
no personality simulation; no fictional quotes; uncertain attribution = UNVERIFIED/excluded.

## Corpus coverage audit (operator-supplied names → matrix fate)
| Supplied name(s) | Fate in matrix | Principle(s) | Status |
|---|---|---|---|
| Nakamoto | covered (W9) | CRYPTO-01/02 | PARTIAL (F1-corrected) |
| Buterin | covered | CRYPTO-03 | PARTIAL |
| Wood | covered | CRYPTO-04 | EXISTING |
| Yakovenko | added W11 | CRYPTO-07 | DEFINED |
| Nazarov | covered | CRYPTO-05 | DEFINED |
| "Heiden Adams" → normalized to **Hayden Adams** (documented name-variant) | covered | CRYPTO-06 | EXISTING |
| Kulechov | added W11 | CRYPTO-08 | DEFINED |
| CZ (operator school — thin corpus, kept narrow) | added W11 | CRYPTO-09 | DEFINED |
| Hoskinson | added W11 | CRYPTO-10 | DEFINED |
| McCaleb | added W11 | CRYPTO-11 | DEFINED |
| Armstrong | added W11 | CRYPTO-12 | DEFINED |
| Saylor (narrow) | added W11 | CRYPTO-13 | PARTIAL |
| Larsen | added W11 | CRYPTO-14 | PARTIAL |
| Mitnick | covered (school-level) | SEC-01 | EXISTING |
| McKinnon | added W11 | SEC-05 | DEFINED |
| Poulsen | covered (school-level) | SEC-03 | PARTIAL |
| Jonathan James | added W11 | SEC-06 | DEFINED |
| Albert Gonzalez | added W11 | SEC-07 | PARTIAL |
| Adrian Lamo | added W11 | SEC-08 | DEFINED |
| Robert T. Morris + "Astro / security research principles" (era-level ONLY — individual handles UNVERIFIED) | added W11 | SEC-09 | DEFINED |
| Assange (publication-integrity record) | folded | SEC-04 | EXISTING |
| GeoHot | added W11 | SEC-10 | PARTIAL |
| Euclid · Pythagoras/Archimedes · Al-Khwarizmi · Ibn al-Haytham · Euler/Gauss · Newton/Leibniz · Poincaré · Hilbert/Cantor · Gödel · Turing/von Neumann · Ramanujan · Tao | covered (W9) | MATH-01..12 | 10 EXISTING / 1 PARTIAL / 1 DEFINED |
| Omar Khayyam | added W11 | MATH-13 | DEFINED |
| Riemann | added W11 | MATH-14 | DEFINED |
| André Weil | added W11 | MATH-15 | DEFINED |
| Grothendieck | added W11 | MATH-16 | DEFINED |
| Ritchie/Thompson · Torvalds · Dijkstra · Knuth · Carmack · Hopper · Martin · Berners-Lee/Gosling/Stroustrup/Hejlsberg | covered (W9) | ENG-01..08 | 4 EXISTING / 4 PARTIAL |
| van Rossum | added W11 | ENG-09 | PARTIAL |
| Stallman | added W11 | ENG-10 | DEFINED |
| Margaret Hamilton | added W11 | ENG-11 | PARTIAL |
| da Vinci/Jobs · Kubrick/Spielberg/Disney · Tesla/Einstein · Musk · owner | covered (W9) | HUM-01..05 | 1 EXISTING / 4 PARTIAL |
| Tesla (notebook record) | added W11 | HUM-06 | PARTIAL |
| Jules Verne | added W11 | HUM-07 | DEFINED |
| Leonard Cohen | added W11 | HUM-08 | PARTIAL |
| Einstein (testability extension) | FOLDED into HUM-03 extension (pre-existing attribution) — 26 W10 drafts became 25 new ids + 1 fold; recorded openly | HUM-03 (extended) | PARTIAL |
| James Angleton (CI doctrine) | added W11 | SEC-11 | DEFINED |
| **Edward Pearson · LaVaughn Wright · G. R. McKie · Chad Davis** | **EXCLUDED — UNVERIFIED** (no publicly attributable method corpus; deriving = fabrication) | — | — |

## Totals (measured 2026-08-13, post-F1-S1; test-pinned by test_matrix_honest_counts)
**63 principles** · domains: crypto 14 / security 11 / mathematics 16 / engineering 11 /
falsification 3 / product 8 · statuses: **EXISTING 24 · PARTIAL 20 · DEFINED 19** · UNTESTED 0 ·
REFUTED 0 · SUPPORTED 0. History, recorded openly: W11's F1 correction moved CRYPTO-02
EXISTING→PARTIAL because W10A-02 measured triggers on ONLY the paper store (34/17 tables).
On 2026-08-13 the owner-authorized F1-S1 additive trigger migration executed — drill SAFE on
copies, then apply on live stores with row-count+sha256 census data_identical=true
(reports/f1_s1_{drill,apply}_20260813T025708Z.json; probe set W12A-F1S1-{BEFORE,DRILL,APPLY,
ENFORCE}; live UPDATE-abort enforcement probed). Guards now: e01 10 on 5 history tables,
ahos_local 2 on control_flags, paper 34/17 untouched ⇒ the trigger-guard claim is MEASURED-TRUE
in all three governed stores and CRYPTO-02 is promoted back to EXISTING with measured wording
(R-34; rollback = engine/f1_s1_migration.py rollback, drill-proven). Count drift vs W9 (38→63)
is the W11 expansion, logged R-33.

## Principle → behavior binding (mandatory chain)
Every row in the yaml carries: agent_capability (⇒ exists in registry, test-pinned) → probe →
contract → test → evidence_requirement → status → failure_mode. EXISTING requires a live anchor
(test file/probe id — lint-enforced); DEFINED honestly carries "none (spec)". The chain to runtime:
probe outputs feed control-plane health and red-team verdicts; contract bindings are listed per
agent ops.contract; runtime metrics (latency/failures/evidence counts) accrue to the run-ledger.
