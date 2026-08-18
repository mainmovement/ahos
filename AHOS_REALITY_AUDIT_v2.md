# AHOS Reality Audit v2 — Phase 7 Entry Point

**Audit Date:** 2026-08-18
**Auditor:** Senior Software Architect + Crypto Intelligence System Engineer (Arena Agent)
**Standard:** Truth-to-Code (Evidence > Claims). Every claim below is backed by a command
executed this session against `main @ 95f5e14`.
**Scope:** Read-only audit of the full repository. No source files were modified (Step 1 rule).

---

## 0. Verification Baseline (executed this session)

| Check | Command | Result |
|---|---|---|
| Import & architecture gate | `python scripts/validate_imports.py` | **PASS** — 138 modules import cleanly; evidence-boundary 17 files OK; Lane-A freeze 36 files OK; secrets scan 2,111 files clean |
| Test suite | `pytest tests/ -q` | **947 passed / 0 failed** in 70.2s (Python 3.11.2) |
| Frozen scientific surface | `config/lane_a_freeze.sha256` | 36 files pinned — all of `discovery/` + `paper_trading/` |

Repo shape: 223 Python files; `architecture/` = 78 files / 12,314 LOC (the real core);
`tests/` = 77 files / ~12,100 LOC; `engine/` = legacy wave scripts; `database/` = SQL schemas only.

**Status taxonomy (project-standard):** A Designed · B Implemented · C Tested · D Verified · E Production Ready.

---

## 1. Existing Modules (verified inventory)

### Lane A — Runtime Intelligence (`architecture/`, `telegram_ai/`)

| Module | Status | Evidence / Notes |
|---|---|---|
| `architecture/providers/` (contracts, adapters, registry) | **C** | 6 adapters: DexScreener, GeckoTerminal, GoPlus, RugCheck, DEXTools (key-gated, inert without `DEXTOOLS_API_KEY`), DexScreenerBoosts. `NormalizedTokenCandidate` enforces UNKNOWN discipline (None sentinel + `identify_unknowns()`); provenance via `source_provider` + `raw_payload_sha256`. Tests: `test_provider_abstraction.py`, `test_provider_failure_resilience.py`. |
| `architecture/collector/` (engine, circuit_breaker, retry) | **C** | 3-state circuit breakers; `CollectorEngine.collect_candidates()` persists observations. |
| `architecture/scheduling/engine.py` (`ProductionScheduler`) | **B/C** | SQLite lease locks (`scheduler_locks`), heartbeats + downtime detection, missed-window audit (no backfill), run history. **One stub found — see §3.** |
| `architecture/runtime/` (`__main__`, observation_loop, lifecycle, metrics, logging, observability_snapshot) | **C** | `python3 -m architecture.runtime --daemon --interval-sec 60` exists; `RuntimeSafetyGate` + freeze check; graceful shutdown via signal. `ObservationRuntime` is the frozen-Lane-A E-01 poller (clock-injected, tested). |
| `architecture/pipeline/orchestrator.py` | **C** | Full-pipeline orchestration (collect → intelligence → scoring). |
| `architecture/scoring/` (engine, calculator) + `intelligence/`, `risk/`, `features/`, `explanations/`, `decision/` | **C** | Evidence-first scorer: `OpportunityScoreReport` carries WHY, evidence list, missing fields, risks, invalidation conditions. 8-stage pipeline (DATA→…→INVALIDATION) per ARCHITECTURE.md. **Calibration on real accumulated data not yet proven (needs ≥8 weeks of E-01 history; see §5-G).** |
| `architecture/alerts/engine.py` | **C** | Deterministic alert engine with mandated WHY law. |
| `telegram_ai/` (intent, service, response_contract, bot, adapter, positions, alerts, providers) | **C** | Persian NLU (9 canonical intents), Persian Section-X response cards, admin gating, `MockTelegramAdapter` vs `ProductionTelegramAdapter`. **No live run evidence in repo — token-gated, pending env (user blocker).** |
| `architecture/positions/`, `architecture/knowledge/`, `architecture/evolution/`, `architecture/council/`, `architecture/intel/` (news, viral, whales) | **B/C** | Lane-B intelligence surface; evidence-boundary (no raw-data imports) is test-pinned by the import gate. |

### Lane A — Frozen Scientific Surface (do-not-touch)

| Module | Status | Notes |
|---|---|---|
| `discovery/` (14 files, 1,846 LOC) | **C/D** | PAL runtime + `providers.yaml` (14 providers, 9 capability chains, reachability-probed 2026-08-11), identity, observations, lifecycle (72h state machine), feature store fs_v0.2 (21 features, leak-proof), security gate, outcome labeler, ranker. **Hash-pinned — any edit invalidates recorded observations.** |
| `paper_trading/` (17 files, 2,911 LOC) | **C/D** | Event-sourced ledger v3, decision_v3, cost model, risk, realizable PnL. 100% PAPER. **Hash-pinned.** |

### Infrastructure

| Component | Status | Notes |
|---|---|---|
| `deployment/` (Dockerfile, compose ×4, healthcheck.py, entrypoint.sh) | **B** | `docker-compose.production.yml` has `restart: unless-stopped` + healthcheck. **Never booted in evidence trail; no systemd unit; no external watchdog.** |
| `n8n/workflows/` (6 JSONs) | **C** | Live-imported 6/6 into n8n 2.8.4 (2026-08-11); activation credential-gated. |
| `database/` (postgresql_schema.sql, v1_2, v1_3) | **B** | Schema only — **Postgres never booted**. |
| `scripts/` (validate_imports, freeze_lane_a, init_databases) | **C** | Validation gate proven this session. |
| CI (GitHub Actions) | **A/B** | **No workflow exists.** Creation blocked: GitHub App lacks `workflows` permission (push rejected 2026-08-18, exact error in AHOS_PHASE7_REPORT §1). Local equivalent (`validate_imports` + `pytest`) is green. |

---

## 2. Directive-Requirement vs Reality Mapping

The directive lists 5 items as "NOT FULLY COMPLETED". Verified truth:

| # | Directive item | Verified reality | Delta to target |
|---|---|---|---|
| 1 | Continuous Scheduler (24/7) | **~70% exists.** Daemon runtime + lease-locked scheduler + heartbeat + missed-window audit + docker restart policy. | (a) `check_clock_drift()` is a **stub** (§3.1); (b) no stale-heartbeat watchdog query; (c) no systemd/ops unit for VPS; (d) **zero long-run soak evidence** in repo — no 24h+ daemon run report anywhere; (e) `data/` DBs are gitignored → fresh-clone first-run path unproven on VPS. |
| 2 | Real Data Provider Layer (DexScreener, GeckoTerminal, CoinGecko, CoinMarketCap, DEXTools, chain explorers, launchpads) | **~50%.** DexScreener ✓, GeckoTerminal ✓, DEXTools ✓ (inert w/o key), GoPlus ✓, RugCheck ✓. PAL side-channels exist for RSS + public RPC. | **Missing adapters: CoinGecko, CoinMarketCap (free-tier, keyless-capable), chain explorers, launchpads.** No unified `collect(token)` facade — registry exposes per-provider `fetch_*` only. |
| 3 | Multi-chain (ETH, BSC, Base, Arbitrum, Polygon, Avalanche) | **~30%.** Adapters take `chain` param; GoPlus maps 5 EVM chains; GeckoTerminal/DexScreener accept network ids. | Solana-only is the tested path (all tests + E-01 data are solana). **Avalanche unmapped everywhere.** No non-solana end-to-end test or collection evidence. |
| 4 | Real Opportunity Scoring Engine | **~80% (code), ~40% (validation).** Scoring pipeline with explanations exists and is tested. | Weights/calibration unvalidated on real accumulated observations; no backfilled scoring accuracy report. Formula in directive (liquidity/holders/smart-money/dev-risk/timing/narrative − penalties) maps to existing stages but narrative & smart-money inputs are partial (`intel/news`, `intel/viral`, `whales` = B/C). |
| 5 | Telegram Persian Interface | **~70% (code), 0% (live).** Persian cards, intents, gating all tested. | Never run against real Telegram (token rotation pending — user blocker). |

---

## 3. Fake / Stub Implementations Found (honest register)

1. **`architecture/scheduling/engine.py:88-94` — `check_clock_drift()` is a stub.**
   It returns `0.0` whenever system time is after 2023 (`if t_sys < 1_700_000_000: return 9999.0; return 0.0`).
   It measures nothing. The "clock drift detection" claimed in the v1 readiness report (94% READY)
   **does not exist**. → Fixed in Phase 7 Step 3 (real NTP-free drift measurement, §Phase 7 report).
2. **`AHOS_PRODUCTION_READINESS_REPORT.md` (2026-08-16) — overclaim.** "95.5/100 READY_FOR_DEPLOYMENT"
   and "481 tests" are stale/unsupported: suite is now 947 (still green), but readiness cannot be claimed
   while (a) the drift stub above shipped, (b) no soak run exists, (c) Telegram live = 0 runs,
   (d) Postgres never booted. Verdict: **code-hardened, NOT operationally proven.**
3. **`engine/telegram_live_test.py`** — SIMULATED 11/11 PASS (labeled honestly in-file, state map §2);
   real run pending env. Not a defect — a documented pending item.
4. **`MockTelegramAdapter` (telegram_ai/adapter.py)** — test double by design, clearly named; fine.
5. **DEXToolsAdapter** — honest inert-by-design without key (returns `NO_KEY` envelope, never guesses).
6. **No other `NotImplementedError`/stub markers** in `architecture/`, `telegram_ai/`, `discovery/`,
   `paper_trading/` (grep-verified). The codebase's "never fake data" discipline is real and test-pinned.

## 4. Broken Flows

**None found at import/unit level** (138 modules import cleanly; 947/947 tests pass). Structural concerns:

1. **Dual Telegram stacks:** legacy `engine/bot_skeleton.py` (+ `engine/telegram_live_test.py`) vs
   production `telegram_ai/bot.py` + `architecture/runtime`. Legacy is documented as Agent-05 skeleton;
   risk of confusion. → Consolidation candidate (Month 4, roadmap).
2. **Two schedulers:** frozen `discovery/observation_scheduler.py` (E-01 Lane-A poller) and
   `architecture/scheduling/engine.py` (production coordinator). Intentional separation (freeze law),
   but the production scheduler currently coordinates tasks it is handed — no canonical wiring doc
   for "which tasks run in the daemon loop" beyond `architecture/runtime/__main__.py`. → Ops runbook (Month 1).
3. **Fresh-clone bootstrap:** `data/` is gitignored (correct — no DBs in git), so first VPS run must
   `scripts/init_databases.py`; path is implemented but not covered by a runbook proof.

## 5. Production Gaps (ranked, evidence-based)

| # | Gap | Severity | Blocking for |
|---|---|---|---|
| A | GitHub Actions CI absent (App lacks `workflows` permission) | Medium | Regression safety on PRs; local gate exists as substitute |
| B | Clock-drift stub in scheduler | **High** | Any long-run scheduling correctness claim |
| C | No stale-heartbeat watchdog / external monitor | High | 24/7 operation ("silent death" undetected) |
| D | No soak evidence (≥24h daemon run report) | **High** | Month 6 deployment gate |
| E | Missing providers: CoinGecko, CoinMarketCap, chain explorers, launchpads | Medium | Coverage/quality of enrichment ( UNKNOWN-heavy candidates) |
| F | No unified `collect(token)` registry facade | Medium | Step 4 of directive; consumer simplicity |
| G | Scoring calibration unvalidated on real obs history | **High** | Any "Opportunity Score" trust claim |
| H | Multi-chain untested beyond solana; Avalanche unmapped | Medium | Month 2 target |
| I | Telegram never run live (token blocker — user) | High | Month 4 product |
| J | Postgres never booted; n8n activation pending creds | Low/Med | VPS full-stack deployment |
| K | No SQLite backup/rotation strategy for `data/*.sqlite` | Medium | Data durability on VPS |

## 6. What Is Real (credit where due)

- UNKNOWN-discipline contracts with per-field provenance & raw-payload hashing — real, tested.
- Circuit breakers + fail-closed error envelopes — real, tested (`test_provider_failure_resilience.py`).
- 72h lifecycle, gap register (missed ≠ backfilled), no-look-ahead feature store — real, test-pinned, frozen.
- Evidence-boundary (intelligence never imports raw-data lanes) — enforced by the import gate this session.
- Paper-only trading with event-sourced ledger — real; zero exchange keys/wallets anywhere (secrets scan clean).
- 947 green tests + deterministic validation gate — reproduced independently this session.

## 7. Phase 7 Actions Authorized by Directive (mapping)

| Directive step | This audit's disposition |
|---|---|
| Step 3 Scheduler | Retain + harden in-house scheduler (decision matrix in AHOS_ROADMAP_v3 §2); fix drift stub; add heartbeat watchdog + VPS unit. Lane-A freeze untouched. |
| Step 4 Provider Registry | Extend **existing** `architecture/providers/` (the canonical home since Phase XX — a new top-level `providers/` would fork the architecture, violating the "no architecture modification" rule). Add CoinGecko + ChainExplorer adapters and a unified `collect(token)` facade over `ProviderRouter`. |

**Audit verdict:** The platform is a genuinely tested, honestly-disciplined codebase that has never
been *operated*. Phase 7 = make it run, watch itself, and gather more real evidence — not rebuild.
