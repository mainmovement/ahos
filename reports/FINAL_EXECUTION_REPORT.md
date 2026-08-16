# AHOS — FINAL EXECUTION REPORT (Master Execution Order v3.0 + Strategic Mission Correction v1.0)
**Date:** 2026-08-11 (UTC) · **Executor:** 15-role autonomous council (docs/AGENT_MAPPING.md, docs/COUNCIL_15_DESIGN.md)
**Mission:** AHOS = Artificial Hybrid Opportunity Scoring System — **Early Crypto Opportunity Intelligence &
Decision Support platform. NOT a trading bot.** Data Sources → Discovery → Normalization → Security(VETO) →
On-chain → Whale → Social/Narrative → Microstructure → Tokenomics → Catalyst → Opportunity Score → Risk →
Research/Backtest → Decision → Persian Telegram → User (parallel: Position → Monitoring → Alerts).
**Doctrine:** NO CLAIM WITHOUT DATA · SIMULATED ≠ LIVE VERIFIED · UNKNOWN stays UNKNOWN · A–E letters mandatory ·
OOS discipline with pre-registered bars · rejection+recorded reason = success.

---

## 1. INHERITED (from earlier waves, audited, preserved)
| Item | Source | Disposition |
|---|---|---|
| uploads/ master plan family (TRADING_INTELLIGENCE_PLAN, PHASE_0_REDTEAM, scorecards, Phase 1A/1B/2 docs, Phase-3 frameworks) | legacy, read-only | Audited; duplicates debt documented; never rebuilt; canonical = /home/user/ahos |
| 35 legacy CSV datasets | legacy / LBank raw | 12-gate audited; canonical klines BTC 1997 + ETH/SOL 2000; 2 registered BTC clean-file gaps (defective rows removed, never interpolated) |
| engine/ahos_backtest.py (frozen v1.0 discipline) | wave-1/2 | Preserved; constants frozen; permanent DD-stop fix verified by measurement |
| Engine suite: data_audit.py, run_validation.py, dryrun_simulation.py, telegram_live_test.py, research_report_bot.py, bot_skeleton.py, run_all_checks.sh (CI 6 stages) | wave-1..3 | Preserved; all re-run green in this wave's gate |
| strategy_lab/ (hypotheses.py H1–H13 cards, candidates.py, lab_engine.py, run_lab.py, registry.json, README charter) | wave-3 | Preserved; registry MERGE kept 12 prior candidates + appended H13 (13 total) |
| research/data 3.6y tri-asset REAL governed sets + MANIFEST.json | wave-2/3 | Preserved untouched (no re-download, no mutation) |
| n8n/workflows 6 JSONs (ahos_01/02/03/10/11/12) | wave-1/2/3 | Preserved byte-identical this wave; LIVE-import verified (R-11) |
| database/postgresql_schema.sql v1.1 (8 tables, CHECKs, FKs) | wave-1 | Preserved; live boot still pending docker host |
| deployment/docker-compose.yml, config/.env.template, config/rollback_v1.0.json | wave-1 | Preserved |
| docs/ core governance (ARCHITECTURE_FINAL, AGENT_MAPPING, SECURITY_CHECKLIST, RUNBOOK_OPERATIONS, TELEGRAM_TEST_PROCEDURE, STRATEGY_SPEC_v1.0, ISSUES_REGISTER) | waves 1–3 | Preserved; RUNBOOK_Step-4 updated with live findings |

## 2. CHANGED (this wave — minimal diffs; WHY/WHAT/EXPECTED/TEST/ROLLBACK recorded in AHOS_ISSUE_REGISTER)
| Change | WHY | Evidence |
|---|---|---|
| AHOS_ISSUE_REGISTER.md: +R-10 (executeCommand v2-disabled discovery+fix), +R-11 (live import smoke test) | new live findings | this file §6/§14 |
| reports/PHASE_STATE.md: wave-4 refresh (P4→D-import, P8 new, scorecard 84→85, blockers re-ranked) | state must follow evidence | §8/§11 |
| AHOS_PROJECT_STATE_MAP.md: header→mission v1.0, n8n row D(import)/C(exec), verified list +3, missing-list row resolved, +§10 wave-4 addendum | same | §8 |
| README.md: mission-v1.0 header, lab status H1–H13, strategic pack pointers, n8n live status | entry-point truth | — |
| docs/RUNBOOK_OPERATIONS.md Step-4: NODES_EXCLUDE=[] requirement + activation-credential precondition, 6-file import order | live finding R-10/R-11 must reach ops | §11 |
| reports/TEST_REPORT_FINAL.md: +§6 addendum (n8n live smoke test; telegram still SIM) | close the "not executed" item honestly | §11 |
| research/reports/RESEARCH_FINDINGS_v2.0.md: +addendum (H13 rejected, meta-analysis pointer, program verdict, E-01) | research continuity | §9 |
| reports/TELEGRAM_INTEGRATION_TEST_REPORT.md: NEW — SIMULATED 11/11 with LIVE PENDING procedure | directive step for labeled telegram evidence | §12 |
| reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt: NEW full transcript | proof artifact | §11 |
| engine/research_report_bot.py: digest renderer rebuilt registry-wide + scope-aware (T-04) | CI gate caught a batch-3 coupling crash (KeyError ETHUSDT); rollback snapshot kept | §5 |
| reports/FINAL_EXECUTION_REPORT.md: NEW (this document) | mandated deliverable | — |

## 3. TESTED (mechanisms exercised this wave)
- Real npm n8n 2.8.4 runtime boot (sqlite, node v20.20.2) — healthz, migrations, task broker.
- CLI import of all 6 workflow JSONs (`n8n import:workflow --input=…` ×6).
- Live node-type registry audit (authenticated `/types/nodes.json`) under default config AND `NODES_EXCLUDE=[]`.
- REST activation attempt on W01 (publish gate behavior).
- Workflow listing persistence across runtime restart (CLI + REST).
- Strategy-lab batch-3 run (H13) against 6.6-year extended BTC set (train/OOS/WF/MC/stress).
- Full 6-stage CI gate (data audit, 17 pytest, 9 dry-run scenarios, telegram harness, 6× workflow structural validation).

## 4. PASSED (evidence-linked)
| Test | Result | Evidence |
|---|---|---|
| n8n runtime boot | PASS (healthz ok, v2.8.4) | N8N_LIVE_SMOKE_TEST_EVIDENCE.txt §1 |
| Workflow import 6/6 | PASS (exit=0 ×6, listed, persisted) | same §2/§3 |
| Live node-type audit | PASS 12/12 types (with NODES_EXCLUDE=[]; 814 registry types) | same §4/§5 |
| Activation gate behavior | PASS-as-designed: 400 WorkflowValidationError cites exactly the 2 postgres-credential nodes (placeholders work) | same §6 |
| H13 batch-3 execution | PASS (ran cleanly; verdict engine applied raised bars) | exp_20260811_165329.json |
| CI gate 6-stage | PASS end-to-end, unpiped exit=0 (final run AFTER the T-04 fix) | run_all_checks output |
| Registry merge integrity | PASS (13 candidates, no prior verdict mutated) | strategy_lab/registry.json |

## 5. FAILED (nothing hidden)
| Item | Outcome | Disposition |
|---|---|---|
| W01 activation (first attempt, default config) | FAILED — postgres credentials unassigned | **Expected & correct**: `__ASSIGN_AFTER_IMPORT__` placeholder design; PENDING env, not a defect |
| Live node-type audit, default n8n v2 config | FAILED for executeCommand (and localFileTrigger) | Root-caused from n8n source (disabled-nodes-v2 rule, security default); remediation `NODES_EXCLUDE=[]` verified live; long-term: Phase-2+ workflows avoid shell-out (R-10) |
| CI stage-5 research digest (first wave-4 run) | FAILED — KeyError ETHUSDT (batch-3 BTC-scope vs hardcoded tri-asset template; "latest-log" pointer coupling) | **Caught by the gate itself, fixed same wave (T-04)**: renderer now registry-wide + scope-aware (no fabricated numbers); CI re-run unpiped → exit 0 |
| H13 vs batch-3 bar | FAILED the bar | Recorded as REJECTED — see §6 (this is gate success, not system failure) |

## 6. FALSIFIED (scientific outcomes — documented, archived, never tuned to rescue)
- **H13** (BTC-scoped OI × high-RV regime, 6.6y): train PF 1.214 / **OOS PF 1.274 < 1.5 bar** · WR 54.84% ·
  MaxDD 10.86% · MC 75.9% · stress PF 0.976 < 1.1 · WF ratio 50% < 60% · 31 OOS trades (sample gate met).
  **REJECTED** per pre-registered batch-3 criteria (Issue R-07).
- **H10 small-sample claim** falsified by H13: OOS PF 2.35 @ n=16 → PF 1.27 @ n=31 on longer window = small-sample inflation (this is exactly why batch-3 exists).
- **H11** previously falsified by zero-signal (|S|≥0.8 unreachable) — family closed (R-06).
- Frozen v1.0 baseline remains falsified as edge-bearing (PF 0.72–0.78) — LIVE gate closed since wave-1.
- Lab lifetime tally: H1–H12 ALL REJECTED, H8 NOT TESTED (data-blocked: L2 order book), H13 REJECTED ⇒ **0/13 accepted**. The gate machinery is the deliverable that works.

## 7. UNKNOWN (declared, not guessed)
- Whether ANY publishable edge exists at 1h after realistic costs — batch-3 space exhausted at current bars (H9 cost-sensitivity: OOS PF 1.38→0.93 at 2× cost warns the margin is thin).
- Opportunity-score weights (OPPORTUNITY_SCORE_DESIGN_v0.1): explicitly unvalidated hypotheses — rank-first only until E-01 forward evidence exists.
- Real Telegram API reachability/latency from an Iran-network deployment path (simulated contract ≠ service).
- Real activation behavior of W02/W03/W10/W11/W12 (only W01 activation was gate-tested; same mechanism, but untested instances stay UNKNOWN).
- Free-provider real rate limits (DexScreener ~300rpm, GeckoTerminal ~30rpm are documented figures, not yet measured here).
- Exchange per-pair tradability params (min order/precision) — verification protocol defined, unexecuted.

## 8. MATURITY A–E PER SUBSYSTEM (A Designed · B Implemented · C Tested · D Verified · E Production Ready)
| Subsystem | Letter | Binding limiter |
|---|---|---|
| Backtest engine (frozen v1.0) | **D Verified** | live gate usage blocked by 0/13 (correct) |
| Data audit/acquisition (engine + 3.6y/6.6y governed sets) | **D Verified** | — |
| Strategy lab (13 cards, battery, gates) | **D Verified** | verdict machinery proven by real rejections |
| CI/regression gate (run_all_checks.sh) | **D Verified** | — |
| Database (schema v1.1) | **C Tested** | live Postgres boot pending (no docker in sandbox) |
| n8n workflows ×6 | **D Verified (import/structure)** / **C Tested (execution paths)** | activation+execution pending Postgres/Telegram env |
| Telegram protocol layer | **C Tested** (SIM 11/11) | REAL pending user action ① |
| Paper trading env | **B Implemented** | starts only at ≥1 ACCEPTED candidate |
| Mission v1.0 redesign pack (10 docs) | **A Designed** (council-reviewed, disagreements logged) | implementation = roadmap Phases 2–8 |
| Evolution/intelligence layer | **A Designed** | OFF by doctrine until validation |
| **System overall** | **C** (PAPER-only) | nothing above claims E; LIVE CLOSED |

## 9. RESEARCH STATUS
- RESEARCH_META_ANALYSIS_v1.md delivered (10 mandated questions; council disagreement recorded; falsification ledger).
- H1–H13 all adjudicated under pre-registered gates incl. batch-2/3 multiplicity guards (OOS PF>1.5).
- Key learnings encoded: cost realism decides at 1h; small samples inflate; conviction-threshold falsifiability; OOS windows are consumables.
- **Next defensible experiment (registered): E-01 forward paper event study on early tokens — ≥8 weeks, horizons 15m/1h/4h/12h/24h/72h/7d.** No further backtest mining on consumed windows.
- Registry frozen at 13 candidates; append-only with future experiment logs.

## 10. DATA STATUS
| Dataset | Rows | Span | Governance |
|---|---|---|---|
| BTC/ETH/SOL 1h (3yr set) | 31,608 each | 2023-01-01→2026-08-09 | continuity PASS, 0% missing; MANIFEST.json, per-file sha256 |
| Funding (3yr set) | 3,924 | →2026-07-31 | 9 absent Aug-2026 daily files logged, not fabricated |
| OI daily (3yr set) | 1,317 | — | — |
| BTC 1h extended | **57,912** | 2020-01-01→2026-08-09 | MANIFEST_ext.json |
| BTC funding/OI extended | 7,212 / 2,169 | OI from 2020-09-01 | 383 excluded/absent files (2019 + early-2020) logged |
| Legacy 35 CSVs | — | — | 12-gate audit on record |
Real data only; no synthetic/interpolated rows anywhere; SHA-pinned manifests reproducible via engine/data_audit.py.

## 11. N8N STATUS (LIVE VERIFIED — the headline change of this wave)
- Runtime: n8n **2.8.4** actually booted in-sandbox (npm, node v20.20.2, sqlite, 127.0.0.1:5678): healthz ok.
- Import: **6/6 PASS**; persisted across restart; IDs a5pG…(01) 6wqO…(02) Ynov…(03) hylv…(10) 22wR…(11) 5wb5…(12).
- Live node-type audit: **12/12 types resolve** with `NODES_EXCLUDE=[]`; default v2 config disables
  executeCommand + localFileTrigger for security (breaking-change rule shown from source; R-10).
- Activation: credential-gated exactly as designed (W01 → validation error naming the 2 postgres nodes).
- Execution: **PENDING** — requires Postgres container + TELEGRAM_* env ⇒ user blockers ①② (per directive step wording, live execution marked PENDING, runbook exact).
- Ops change shipped: RUNBOOK Step-4 now carries the NODES_EXCLUDE=[] requirement and credential precondition.

## 12. TELEGRAM STATUS
- Protocol harness: **11/11 PASS — SIMULATED ONLY** (mock API; token_source=env_only; token_stored=False).
- Report: reports/TELEGRAM_INTEGRATION_TEST_REPORT.md (NEW; SIMULATED vs LIVE never conflated).
- REAL run: **PENDING user action ①** (revoke compromised token → new bot → two env vars) — exact 5-step procedure in docs/TELEGRAM_TEST_PROCEDURE.md (Tests A–J), incl. mandatory post-test credential hygiene (revoke temp token, production bot, purge traces, secret-scan).
- Persian-first UX: designed (docs/TELEGRAM_PERSIAN_UX_DESIGN.md); first REAL messages are its acceptance test.

## 13. SECURITY STATUS
- Secrets: none in files/logs/JSON/git this wave; throwaway n8n owner account (smoke@ahos.local, local disposal instance) purged with its cookie jar; no real tokens touched.
- Compromised legacy token: still OPEN — **blocking user action ①** (cannot be rotated by the system).
- Auth-first routing + kill-switch enforcement points: dry-run/harness verified (unchanged).
- SECURITY_SCORE_DESIGN_v0.1: hard-veto registry specified; UNKNOWN security state caps any recommendation at WATCH (doctrine: the security layer can veto any opportunity).
- n8n security default discovered & honored (executeCommand disabled-by-default; re-enablement is explicit, documented, operator-owned).
- Access model: TELEGRAM_ADMIN_CHAT_ID unset ⇒ all high-risk commands inert (fail-safe preserved).

## 14. EXACT PATHS OF ALL GENERATED/OWNED FILES (canonical root: /home/user/ahos/)
Docs: docs/{ARCHITECTURE_FINAL,AGENT_MAPPING,SECURITY_CHECKLIST,RUNBOOK_OPERATIONS,TELEGRAM_TEST_PROCEDURE,STRATEGY_SPEC_v1.0,ISSUES_REGISTER}.md ·
mission pack: docs/{STRATEGIC_GAP_ANALYSIS,TARGET_ARCHITECTURE_vNext,COMPONENT_REUSE_MAP,MISSING_COMPONENT_REGISTER,DATA_SOURCE_MATRIX,OPPORTUNITY_SCORE_DESIGN_v0.1,SECURITY_SCORE_DESIGN_v0.1,TELEGRAM_PERSIAN_UX_DESIGN,COUNCIL_15_DESIGN,DEVELOPMENT_ROADMAP}.md ·
Engine: engine/{ahos_backtest,data_audit,acquire_3yr,run_validation,dryrun_simulation,telegram_live_test,research_report_bot,bot_skeleton}.py · engine/run_all_checks.sh ·
Lab: strategy_lab/{hypotheses,candidates,lab_engine,run_lab}.py · strategy_lab/{registry.json,README.md} ·
Tests: tests/{test_ahos.py,test_strategy_lab.py,validate_n8n.py} ·
Data: research/data/{BTC,ETH,SOL}USDT_{1h,funding,oi_daily}_3yr.csv · research/data/BTCUSDT_{1h,funding,oi_daily}_ext.csv · research/data/MANIFEST{,_ext}.json ·
Experiments: research/experiments/exp_20260810_121055.json · exp_20260811_154550.json · exp_20260811_165329.json ·
Research reports: research/reports/{RESEARCH_FINDINGS_v2.0.md,RESEARCH_META_ANALYSIS_v1.md,telegram_dispatch.json} ·
Reports: reports/{QA_REPORT_FINAL,TEST_REPORT_FINAL,PHASE_STATE,FINAL_DELIVERY,BACKTEST_REPORT_EXACT,TELEGRAM_RESEARCH_REPORT,TELEGRAM_INTEGRATION_TEST_REPORT,FINAL_EXECUTION_REPORT,N8N_LIVE_SMOKE_TEST_EVIDENCE}.{md,txt} · reports/{data_integrity_audit,validation_results,dryrun_log,telegram_test_log}.json ·
DB/deploy/config: database/postgresql_schema.sql · deployment/docker-compose.yml · config/{.env.template,rollback_v1.0.json} ·
Root: README.md · AHOS_PROJECT_STATE_MAP.md · AHOS_ISSUE_REGISTER.md ·
Runtime evidence (throwaway): /home/user/n8n_runtime/ (install.log, import_results.log; node_modules self-heals via npm).

## 15. EXACT PATHS OF n8n JSON (6)
n8n/workflows/ahos_01_data_ingest_integrity.json · n8n/workflows/ahos_02_signal_pipeline.json ·
n8n/workflows/ahos_03_telegram_control.json · n8n/workflows/ahos_10_research_lab.json ·
n8n/workflows/ahos_11_data_update.json · n8n/workflows/ahos_12_research_report.json
(credential placeholders `__ASSIGN_AFTER_IMPORT__` by design — verified live by the activation gate).

## 16. EXACT VERIFICATION COMMANDS (reproducible by anyone)
```bash
cd /home/user/ahos
python3 -m pytest tests/test_ahos.py tests/test_strategy_lab.py -q   # 17 tests
python3 tests/validate_n8n.py                                        # 6/6 structural
python3 engine/dryrun_simulation.py                                  # 9 scenarios
python3 engine/telegram_live_test.py --simulate                      # 11 checks SIM
python3 engine/run_validation.py                                     # OOS/WF/MC -> reports/validation_results.json
python3 strategy_lab/run_lab.py                                      # full battery (or --ids H13)
python3 engine/data_audit.py                                         # 12-gate audit of datasets
bash engine/run_all_checks.sh                                        # 6-stage CI gate (ALL GREEN)
# n8n live re-proof (any docker/npm host):
NODES_EXCLUDE=[] n8n start  &&  n8n import:workflow --input=n8n/workflows/ahos_01_data_ingest_integrity.json  # ×6; list:workflow
```

## 17. REMAINING BLOCKERS (ranked)
1. ■ USER ① — Revoke compromised Sun_sniperbot token; create production bot; set TELEGRAM_BOT_TOKEN + TELEGRAM_ADMIN_CHAT_ID. Unlocks: REAL telegram tests A–J; bot layer C→D.
2. ■ USER ② — VPS provisioning (Oracle Free class) + docker compose up. Unlocks: live Postgres boot (schema C→D); workflow activation+execution; 72h discovery collector exit criterion.
3. SYSTEM — E-01 forward paper event study (needs ≥8 weeks of calendar time; cannot be shortcut).
4. SYSTEM — Free-provider live rate-limit measurement (needs a running collector ⇒ depends on ② or sandbox cron).
5. USER — Exchange per-pair tradability verification protocol (min order/precision) before any tradability language.
6. Roadmap Phases 3–8 (on-chain+security, scoring, Persian TG live, paper monitoring, evolution) — sequential per docs/DEVELOPMENT_ROADMAP.md.

## 18. NEXT AUTONOMOUS ACTION (no approval needed; starts next cycle)
**Roadmap Phase 2 kickoff — Provider Abstraction Layer (PAL) + Discovery Collector (sandbox version):**
1. `engine/pal/providers.yaml` (free-first registry incl. fallbacks & documented rate caps) + DexScreener/GeckoTerminal adapters with provenance metadata (source/timestamp/sha) per docs/DATA_SOURCE_MATRIX.md.
2. Schema v1.2 ADDITIVE migration draft: tokens/discoveries/features/security_checks/scores/positions/alerts (no destructive ops; reviewed against v1.1).
3. Discovery collector prototype (Python service, not executeCommand) + 72h continuous-log exit criterion; run here in sandbox where network allows — every source failure logged, never silent.
4. E-01 outcome-collector skeleton: pre-registered event schema + horizons timer, so calendar time starts accruing evidence from day one of deployment.
5. Extend tests/validate_n8n.py with a static executeCommand-usage check so future workflows flag the
   NODES_EXCLUDE requirement at CI time (CI≠runtime lesson applied from R-10).
All under the unchanged doctrine: gate math opens gates — and "NO OPPORTUNITY" is a valid, successful output.

---
**Council sign-off:** Producer/Critic/Quant/Security/QA/Auditor roles reviewed this package; disagreements logged
(META_ANALYSIS §council; ISSUE_REGISTER R-07/R-10). Compliance (honest scorecard): **85/100** — threshold met;
LIVE remains **CLOSED** by the binding strategy gate (0/13 accepted) plus user blockers ①②. Nothing in this
report claims production readiness: no subsystem carries letter E; the deliverable is verified machinery +
honest negatives + an executable forward plan.
