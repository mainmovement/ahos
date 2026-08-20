# AHOS — PROJECT STATE MAP (Forensic Audit) — 2026-08-11 (wave-4)
# Project: Artificial Hybrid Opportunity Scoring System (Early Crypto Opportunity Intelligence & Decision Support; NOT a trading bot).
# Status taxonomy (mandatory): A Designed · B Implemented · C Tested · D Verified · E Production Ready
# "Verified" = independently re-checked by automated tooling this session, not just claimed.

## 1. EXISTING FILES & COMPONENTS (status letters per new directive)
### Inherited (uploads/) — audited, read-only source of truth
| Component | Status | Note |
|---|---|---|
| TRADING_INTELLIGENCE_PLAN.md (354 lines) | D | master plan; honest-score methodology intact |
| PHASE_0_REDTEAM_REPORT.md (580 lines) | D | 18-section critique; consistent |
| COMPLIANCE_SCORECARD + phase scorecards | D | methodology sound; scores superseded by PHASE_STATE |
| Phase 1A/1B/2 report family (15+ docs) | D | multiple duplicate "Final" versions — debt documented |
| Phase-3 frameworks (Execution Protocol / Framework / Validation) | D | design docs; no executed 3yr run exists anywhere |
| 35 CSV datasets | D | 12-gate audited in-session; canonical = BTC 1997 + ETH/SOL 2000 |
| EXCHANGE_FACTS / $10_15_FEASIBILITY / assets_48 | D | honest UNKNOWN registry intact; assets count defect logged |

### Built in consolidation wave (this project home /home/user/ahos/)
| Component | Status | Evidence |
|---|---|---|
| engine/ahos_backtest.py (exact engine + risk caps) | **D** | 11 pytest incl. no-look-ahead & determinism; DD-stop fix audited |
| engine/data_audit.py (12-gate auditor, 35 files) | **D** | reports/data_integrity_audit.json |
| engine/run_validation.py (OOS/WF/MC runner) | **D** | reports/validation_results.json |
| engine/dryrun_simulation.py (9 failure scenarios) | **D** | reports/dryrun_log.json, 9/9 |
| engine/telegram_live_test.py (Tests 1–4 harness) | **C** | SIMULATED 11/11 PASS; REAL pending env (blocking user item) |
| engine/bot_skeleton.py (Agent-05 local bot) | **C** | logic reviewed + simulated; needs live token for D |
| database/postgresql_schema.sql v1.1 | **C** | lint PASS (balanced, no destructive ops, 8 tables/25 CHECKs/4 FKs); D pending live Postgres boot |
| n8n/workflows ahos_01/02/03 (+10/11/12) (JSON) | **D (import)** / **C (execution)** | structural validation 6/6 + LIVE import 6/6 into real n8n 2.8.4 (wave-4, evidence R-11); activation credential-gated, execution pending env |
| deployment/docker-compose.yml | **B** | config reviewed; not booted here (no docker daemon) |
| engine/run_all_checks.sh (CI gate, 5 steps) | **D** | executed green end-to-end |
| docs/* (architecture, security, runbook, telegram test, spec, mapping) | **D** | consistent with evidence files |
| config/.env.template, config/rollback_v1.0.json | **D** | hygiene scanned; rollback enforced by test |

## 2. MISSING FILES (gaps vs final package spec)
| Missing | Impact | Plan |
|---|---|---|
| Live Postgres boot + psql run of schema | C→D for database | RUNBOOK step 2 (needs docker host) |
| ~~n8n instance import smoke-check~~ | ~~C→D~~ **DONE wave-4** | LIVE import 6/6 verified on n8n 2.8.4 (R-11) |
| n8n activation + execution tests | D→E blocker for workflows | activation correctly credential-gated (R-11); awaits Postgres env (user blocker ②) |
| REAL telegram test run (Tests 1–4) | C→D for Agent-05 | needs env vars (user item) |
| 3-year dataset (26k candles/symbol) | blocks Phase-3 validation for real | chunked loop plan + readiness proven |
| Strategy v2.0 hypothesis doc | blocks any edge claim | only after 3yr data |
| PDF report generator (Agent-06) | cosmetic (D-category score) | Phase-6 |
| Evolution layer modules (Phase-7) | not started by design | after Phase-6 |

## 3. VERIFIED COMPONENTS (independently re-proven this session)
- Data integrity of all 35 CSVs (12 gates each) — PASS / documented PASS(REVIEW)
- Engine determinism + no-look-ahead + frozen constants — test-proven
- Risk sizing/leverage/ddaily-halt/**permanent DD-stop** — unit + integrated proof
- Kill switch three enforcement points — dry-run proven
- Telegram protocol logic (auth, routing, audit) — harness-proven (SIM), live-pending
- Workflow JSON structure, connections, reachability, secret-free — validator-proven
- **Workflow JSON importability on LIVE n8n 2.8.4 — 6/6 runtime-proven (wave-4, reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt)**
- **n8n v2 executeCommand-disabled-by-default behavior + NODES_EXCLUDE=[] remediation — proven from source + live registry (R-10)**
- OOS/WF/MC pipeline executes and produces reproducible JSON (seed=42)
- **Strategy-lab gate integrity across 13 hypotheses incl. batch-3 raised bar — H13 REJECTED per pre-registered criteria (wave-4)**

## 4. UNVERIFIED CLAIMS (inherited — now labeled, never repeated as fact)
| Claim | Source | Disposition |
|---|---|---|
| "PF ~1.1, +0.09% PnL" (Phase 2 approx) | PHASE_2 reports | SUPERSEDED by exact run (PF 0.36–0.89, no edge) |
| "READY FOR PRODUCTION EXECUTION" | MASTERPIECE_FINAL_CONFIRMATION | Category error → relabeled per A–E taxonomy (artifacts C/D; system NOT E) |
| "3yr data via chunks" | FINAL_* files | Proven false (duplicate 21-day windows) |
| "48 assets" | assets_48.md | False (45) — corrected |
| "n8n pipeline 117 lines PASS" | QA reports | Artifact absent; rebuilt & validated structurally; live import pending |
| Telegram bot verified | Phase-1B notes | Only simulated now; REAL pending token rotation |

## 5. BROKEN COMPONENTS (found → fixed this session)
| Defect | Fix | Proof |
|---|---|---|
| MaxDD halt recorded but did NOT stop trading | permanent-stop flag | MaxDD now 20.4–21.7% (was 51–59%) |
| Dead code in close_pos / entry condition | removed | pytest green |
| data_audit crash on legacy/short files (KeyError verdict) | defensive defaults + alias mapping | 35/35 files audited clean run |
| Workflow 01 batch loop never continued (no loop-back) | loop-back edges added | validator reachability |
| Workflow 03 routing bug (kill→status) | full rewrite + /health /agents /reset + auth-first | validator + harness |
| AHOS lacking boot message (Test 2 requirement) | n8nTrigger "Workflow Activated" → boot frame | validator |

## 6. TECHNICAL DEBT (accepted, scheduled)
- Duplicate "Final/Final2/Verified" report versions in uploads → kept read-only (history), canonical = this package
- Schema lacks funding/OI tables (features unused anyway) → add at Phase-3-real if v2.0 needs them
- SQLite side-channel for bot flags (local) vs Postgres (server) → unify at P3 activation
- n8n IF/Switch use "loose" typeValidation → tighten after import smoke-check
- Report generator markdown-only (PDF pending Phase-6)

## 7. SECURITY RISKS (live register — detail in docs/SECURITY_CHECKLIST.md)
- ■ OPEN/BLOCKING: exposed Sun_sniperbot token (in old chat) — revoke before any production
- ■ OPEN: TELEGRAM_ADMIN_CHAT_ID unset — all high-risk commands inert until set (fail-safe)
- Exchange keys: none present anywhere (correct); creation protocol = trade-only + IP whitelist
- Residual: LBank availability/Iran jurisdiction — mitigated by CCXT-swap architecture

## 8. DEVELOPMENT PRIORITY (ranked queue)
1. Token rotation + chat id (unblocks REAL telegram tests) — USER
2. VPS provision + docker compose up + workflow import smoke-check — USER + ops
3. ~~3-year chunked acquisition~~ — **DONE 2026-08-10** (BinanceVision real 3.6y, sha-pinned per file)
4. H10-H12 research leads (OI-regime, composite robustness, vol-state regime gating) — NEW hypothesis cards first
5. Phase-6 paper environment live for 2 weeks — SYSTEM (after ≥1 candidate ACCEPTED)
6. Phase-7 evolution modules — POST-VALIDATION ONLY

## 9. ADDENDUM 2026-08-10 — STRATEGY RESEARCH LABORY v2.0 WAVE
| Component | Status | Evidence |
|---|---|---|
| engine/acquire_3yr.py (governance: source/checksum/dedupe/gap/OHLC) | **D** | research/data/MANIFEST.json (4,263 files, 9 documented CDN absences) |
| research/data 3.6y real sets (BTC/ETH/SOL 1h + funding + OI) | **D** | 31,608 rows/symbol continuity PASS |
| strategy_lab/ (9 hypothesis cards, causal generators, lab engine) | **D** | tests/test_strategy_lab.py 6/6 (prefix-causality proof per generator) |
| Battery run + verdicts + registry | **D** | research/experiments/exp_20260810_121055.json · RESEARCH_FINDINGS_v2.0.md |
| n8n research workflows 10/11/12 (lab, data update, report) | **C** | validator PASS ×6 total; live import pending |
| Telegram research digest path | **C** | SIMULATED dispatch transcript; REAL pending token rotation |
| **Scientific verdict** | **0/8 ACCEPTED** | all evidence reproducible; live gate CLOSED (unchanged, by measurement) |

## 10. ADDENDUM 2026-08-11 — WAVE-4 (MASTER EXECUTION ORDER v3.0 + MISSION CORRECTION v1.0)
| Component | Status | Evidence |
|---|---|---|
| Strategy-lab batch-3 extended BTC data (6.6y: 57,912 rows + funding 7,212 + OI 2,169) | **D** | research/data/*_ext.csv + MANIFEST_ext.json (383 absent files logged, none fabricated) |
| H13 card (pre-registered BEFORE run; batch-3 bar OOS PF>1.5; scope BTCUSDT) | **D — REJECTED** | research/experiments/exp_20260811_165329.json; train PF 1.214 / OOS PF 1.274 / stress 0.976 / WF 50% / MC 75.9% / 31 OOS trades |
| RESEARCH_META_ANALYSIS_v1.md (10 mandated questions + council disagreement log) | **D** | research/reports/RESEARCH_META_ANALYSIS_v1.md — next defensible experiment = E-01 forward paper event study (≥8w, 7 horizons) |
| Mission v1.0 strategic design pack (10 docs) | **A (council-reviewed)** | docs/STRATEGIC_GAP_ANALYSIS · TARGET_ARCHITECTURE_vNext · COMPONENT_REUSE_MAP · MISSING_COMPONENT_REGISTER · DATA_SOURCE_MATRIX · OPPORTUNITY_SCORE_DESIGN_v0.1 · SECURITY_SCORE_DESIGN_v0.1 · TELEGRAM_PERSIAN_UX_DESIGN · COUNCIL_15_DESIGN · DEVELOPMENT_ROADMAP |
| n8n LIVE import smoke test on real n8n 2.8.4 runtime | **D** | 6/6 imported + listed + persisted; node registry 12/12 types OK with NODES_EXCLUDE=[]; activation correctly credential-gated; execution PENDING env → reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt |
| FINAL_EXECUTION_REPORT.md (18 mandated sections) | **D** | reports/FINAL_EXECUTION_REPORT.md (this wave) |
| Compliance total (honest scorecard) | **85/100** | reports/PHASE_STATE.md — threshold met; LIVE still CLOSED by strategy gate (0/13) + user blockers ①② |

## Audited by: Lead Autonomous Engineer + 15-role council (docs/AGENT_MAPPING.md)
## One-command re-proof: bash engine/run_all_checks.sh (6 stages, all green as of 2026-08-11)

## 11. ADDENDUM 2026-08-11 — WAVE-5 (MISSION v1.1: EARLY OPPORTUNITY DISCOVERY CORE)
| Component | Status | Evidence |
|---|---|---|
| A–J mandated deliverables (Mission v1.1 §21) | **B (docs)** | docs/mission_v1_1/{A..J}*.md — 10 artifacts, council-reviewed (H §5) |
| PAL runtime + providers.yaml (14 providers, 9 capability chains) | **C Tested** | discovery/pal.py; envelope/breaker/rate/cache unit-proven (22 tests); 12 providers LIVE-probed |
| Canonical token identity (chain-aware, cross-provider) | **C Tested** | discovery/identity.py; dedupe 0 violations on real data |
| Timestamped observations + raw-payload archive | **C Tested** | discovery/observations.py; NULL-discipline + error-state + zero-is-not-NULL test-pinned |
| 72h lifecycle state machine (clock-injected) | **C Tested** | discovery/lifecycle.py; DISCOVERED→OBSERVING→DEAD→RESOLVED trail test-pinned |
| Feature store fs_v0.1 (16 features, L1–L4 leak-proof) | **C Tested** | discovery/feature_store.py; future-injection immunity test + DB CHECK L3 |
| Security gate (7 CRITICAL veto registry; fixtures 100% veto) | **C Tested** | discovery/security_gate.py; fixture-set labeled FIXTURE (never "real scam rate") |
| Outcome labeler (7 horizons × 4 classes, no-peeking) | **C Tested** | discovery/outcomes.py; horizon-closure enforced by test |
| Paper ranker (rank-first, NO numeric score) | **C Tested** | discovery/ranker.py; "NO OPPORTUNITY" first-class (empty-state test) |
| E-01 REAL collection (sandbox) | **C Tested / RUNNING** | data/e01_discovery.sqlite: 61 tokens, 75 obs, 15 raw payloads, coverage 92–100%; T0=2026-08-11 17:20Z; reports research/experiments/e01_collection_t0_20260811.json |
| Provider reachability ground truth | **D (sandbox)** | docs/mission_v1_1/G §probes: 12 OK, 5 degraded/failed recorded honestly; Iran=UNKNOWN |
| Schema v1.2 (sqlite canonical + pg twin) | **B Implemented** | discovery/schema_sqlite.sql + database/schema_v1_2.sql (additive; pg live boot pending blocker #2) |
| Live gate | CLOSED (unchanged) | 0/13 strategies + 0 promoted features (E-01 data < 8 weeks) — double lock stands |

## 12. ADDENDUM 2026-08-11 — WAVE-6 (KNOWLEDGE HYGIENE + RESEARCH INFRASTRUCTURE)
| Component | Status | Evidence |
|---|---|---|
| Deliverables A–L (§28) | **B–D per table** | docs/mission_v1_1/(A..L) · reports/WAVE6_EXECUTION_REPORT.md |
| Canonical knowledge set (12 docs) | **D** | docs/canonical/ — reference-not-copy; QA consistency spot-check (L/D5) |
| Document hygiene execution | **D** | 194-file sha inventory; 2 archives+stubs (docs/archive/); D_CLEANUP_MANIFEST hashes |
| fs_v0.2 (5 additive features) | **C** | feature_store v02 + registry⇄computed equality test |
| baseline_stats engine | **C** | research/baseline_stats.py + 4 tests; live scan → INSUFFICIENT_DATA (honest) |
| Holder source feasibility | **REFUTED (evidence)** | 5/5 RPC rejections (R-15); adapter shipped; features emit from real rows only |
| E-01 collection | RUNNING | 127 tokens / 155 obs at wave close; reports e01_collection_t3 |
| CI | 6-stage GREEN (45 tests) | unpiped exit=0 |

---
## §13 WAVE-7 ADDENDUM (2026-08-11) — knowledge compression + Telegram AI core + H14+ machinery
- NEW (B/C): engine/doc_hygiene.py (D Verified, manifested 45 actions) · engine/pal_probe.py (C) ·
  discovery/materialize.py (C) · research/baseline_stats.py +evaluate_conjunction (C) ·
  telegram_ai/{intent,providers,positions,alerts}.py + ai_providers.yaml (C, 25 tests).
- EVIDENCE: reports/WAVE7_EXECUTION_REPORT.md · PROJECT_DOCUMENT_INVENTORY_WAVE7.json ·
  CLEANUP_MANIFEST_WAVE7.json · pal_probe_20260811_184349_sandbox.json · ai_provider_probe_20260811.json.
- SUPERSESSIONS: none (reference-not-copy maintained). ARCHIVES: 4 byte-dupes → uploads/_archive_exact_dups_wave7/.
- REFUTED-NEW: pollinations keyless AI (402) · RE-VERIFIED-NEW: GoPlus EVM, CoinDesk RSS.
- TEST TOTAL: 80 (CI green exit 0, stages 3d/3e added).
