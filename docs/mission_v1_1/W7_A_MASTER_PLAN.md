# WAVE-7 MASTER PLAN (Deliverable A) — 2026-08-11
# Supersedes only implementation priorities; Wave-6 evidence, H1–H13 rejections, and audit trail stand.
# Status letters: A Designed · B Implemented · C Tested · D Verified · E Production Ready.

## 0. Non-negotiables carried into Wave-7 (unchanged)
PAPER ONLY · LIVE TRADING CLOSED · $0/month · rank-first (no numeric pump score until the research
gate E-01 ≈2026-10-06) · UNKNOWN stays NULL · no capability claim without a probe id (now permanent
law) · negative evidence never deleted · deterministic systems own all numbers; AI is advisory.

## 1. True objective (directive §1)
Early-movement intelligence: discover emerging tokens as early as reasonably possible; establish,
with pre-registered statistics, which BEFORE-event signal combinations carry real lift over a
defined baseline; separate organic from manipulative movement; monitor the thesis continuously;
serve the user in Persian via Telegram.

## 2. Wave-7 scope executed THIS wave (all with evidence pointers)
| # | Item | State | Evidence |
|---|---|---|---|
| 1 | Document inventory v2 + 194-baseline delta | D Verified | reports/PROJECT_DOCUMENT_INVENTORY_WAVE7.json (230 files: +45/−9/Δ16) |
| 2 | Hygiene classification A–G engine + policy v2 | C Tested | engine/doc_hygiene.py + W7_F policy; idempotency verified (2nd run plan=0) |
| 3 | Safe cleanup (E/G only) | D Verified | reports/CLEANUP_MANIFEST_WAVE7.json — 11/11 OK, sha-verified, reversible |
| 4 | E-01 pass t4 + lifecycle sweep | C Tested (LIVE) | research/experiments/e01_collection_t4_20260811.json; 158 tok / 217 obs |
| 5 | Provider re-probe battery with probe ids | D Verified | reports/pal_probe_20260811_184349_sandbox.json (engine/pal_probe.py, new) |
| 6 | H14–H20 registration + B2 cells | C Tested (machinery) | research/SEARCH_SPACE_REGISTRY.json; report-mode run = INSUFFICIENT_DATA (honest) |
| 7 | Conjunctive research cells (composites) | C Tested | research/baseline_stats.py::evaluate_conjunction; 10 tests in test_wave7_research.py |
| 8 | Batch materializer (frozen features + outcomes) | C Tested | discovery/materialize.py; as_of-exactness + horizon-closure test-pinned |
| 9 | Telegram AI: intent + AI-PAL + ledger + alerts | C Tested | telegram_ai/{intent,providers,positions,alerts}.py; 25 tests |
| 10 | Free AI provider matrix (probe-backed) | C Tested (fallback LIVE VERIFIED) | reports/ai_provider_probe_20260811.json (PRB-20260811-AI-001) |
| 11 | CI extended | D Verified | engine/run_all_checks.sh stages 3d/3e; 80 tests green, exit 0 |

## 3. Sequenced next (directive §29 order continues)
1. E-01 passes every session; **first 72H COHORT EXIT REPORT ≥2026-08-14 UTC** (materializer ready).
2. First real B2 scan when ≥200 resolved (≈ week of 2026-08-17 at current intake 30–60/day).
3. User-side probes: engine/pal_probe.py --site user-iran (AI + data providers; no keys needed for data side).
4. Phase-3 depth: EVM Transfer-log holder scanner design→impl (publicnode LIVE VERIFIED); GoPlus re-enabled (probe OK) — EVM security coverage upgrade.
5. n8n workflows 20/21/22 only after PAL stability ≥1 week.
6. User blockers ① (Telegram token rotation) ② (VPS) unchanged — nothing architectural blocks them.

## 4. What Wave-7 did NOT do (explicit anti-overclaim)
- No pump score created. No predictive probability claimed. No live trading path touched.
- No hypothesis tested against real data (cohort immature — the correct verdict is recorded, not mined).
- No F-class (redundant) cleanup executed — flag-only policy pending council sign-off workflow.
- n8n_runtime deletion is REGENERABLE-only (npm i n8n@2.8.4); workflow JSONs remain canonical in ahos/n8n/.
