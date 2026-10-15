# AHOS Full-History Alignment Audit — 2026-10-12
Written 2026-10-12 ~00:20 Tehran by Soltan (Grok Bot executor). READ-ONLY apart from this file: no code changed, nothing committed, Claude's staged work untouched.
Companion to `2026-10-12_ALIGNMENT_AUDIT.md` (10-08..10-11 window). Context: the owner has now decided the gold paper soak and the dashboard run **in parallel**.

## 0. Method and sources
- Repo `G:\robat\ahos`: 709 commits, first `86ebbc0` 2026-08-16 15:17 "AHOS initial production architecture snapshot". The earliest md files (DEVELOPMENT_ROADMAP, canonical/MISSION, canonical/ROADMAP, STRATEGY_SPEC, TARGET_ARCHITECTURE_vNext, MISSING_COMPONENT_REGISTER, MASTER_DIRECTIVE_v1, ...) all arrived in that first commit.
- Planning/vision docs read (oldest first, date = first git add or stated date):
  - `docs/DEVELOPMENT_ROADMAP.md` (states 2026-08-11; in 86ebbc0): Phases 1–8.
  - `docs/canonical/MISSION.md`, `docs/canonical/ROADMAP.md` (86ebbc0, 2026-08-16): mission + 7 absolute laws.
  - `AHOS_ROADMAP_v3.md` (3eb9964, 2026-08-18): 6-month plan.
  - `docs/supervision/OWNER_VISION_REGISTRY.md` (b04d85e, 2026-09-12): North Star, trading stages 1–8, P0–P4 priorities, constraints.
  - `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md` (acc5e02, 2026-10-03; synced to vision v1.8): M9–M52.
  - `reports/grok/AHOS_AUTONOMOUS_VISION.md` (v1.2–v1.8, 2026-10-03/04; commits 5ca05a2, 068dea9, 14f2165, d2a6fc4, 0b2f274).
  - `reports/grok/CLAUDE_AUTOPILOT_QUEUE.md` (8eb552d, 2026-10-04; edited 10-11): the master mission table with statuses.
  - `حافظه_ادامه/ahos-continuity.md` (2026-10-08 decision brief), Soltan logs 10-09..10-11, `00_SOLTAN_HANDOFF.md`.
  - `reports/grok/queue_2050/` (README_FOR_CLAUDE v1.14–v1.47, TEAM_QUEUE_2026-10-11, DEDUP_MERGE_MAP to v1.47, M80/AGI/M57-M59 addenda).
- Other folders under `G:\robat`: ahos-agent-org (09-14), ahos-push-staging (09-14), ahos-transfer (09-14), ahos022 (09-09, older copy of the same docs), ahos_backups (10-03), ahos_runtime (10-03), ahos_gemini (10-11 worktree, same docs), web (09-09). I only listed file names for these. Their planning docs duplicate the repo's (same names and sizes). `ahos_gemini/docs/archive/consolidation_2026-09-26/booklet_strategic_specs/` holds older vision texts (`AHOS Ultimate Vision v1.0.txt` 195 KB, `Strategic Master Plan v10.0.txt`, `Roadmap.txt`, `System_Vision_and_Functional_Objectives_v1.0.txt`) that I did **not** read: UNVERIFIED content, recommended for a follow-up pass.
- Evidence: `git log --all --grep=<ID>`, `Test-Path` on the promised modules, file contents. Status keys: DONE (commit) · PARTIAL · NOT STARTED · DROPPED · CONTRADICTED · UNVERIFIED.

## 1. Master goal list
| # | Goal | Source (date) | Status | Evidence |
|---|---|---|---|---|
| 1 | Phase 1 architecture stabilization | DEVELOPMENT_ROADMAP (08-11) | DONE | doc marks DONE; base snapshot 86ebbc0 |
| 2 | Phase 2 multi-source token discovery, 72h log | DEVELOPMENT_ROADMAP (08-11) | PARTIAL | `discovery/` exists; 72h log not verified |
| 3 | Phase 3 on-chain + security (GoPlus/RugCheck, veto) | DEVELOPMENT_ROADMAP (08-11) | PARTIAL | adapters.py GoPlus/RugCheck URLs; 711bcd3 Lane B security overlay (09-08) |
| 4 | Phase 4 scoring + E-01 ≥8-week scientific validation | DEVELOPMENT_ROADMAP / canonical ROADMAP (≈10-06 target) | PARTIAL | last E-01 commit 72f4e6f 08-19; no validation report found [UNVERIFIED] |
| 5 | Phase 5 n8n workflows 20/21/22 | DEVELOPMENT_ROADMAP | DROPPED | M10 retired Docker/n8n (73279bf, f6a3bb9) |
| 6 | Phase 6 Persian Telegram interface | DEVELOPMENT_ROADMAP | PARTIAL | `telegram_ai/bot.py`; live use blocked on token rotation (M35.3 BLOCKED_OWNER) |
| 7 | Phase 7 paper-position monitoring | DEVELOPMENT_ROADMAP | PARTIAL | `paper_trading/position_monitor.py`; last paper_trading commit 0563469 08-19 |
| 8 | Phase 8 evolution / continuous research | DEVELOPMENT_ROADMAP | PARTIAL | `architecture/evolution/`, `evolution_gate.py` exist; not wired [UNVERIFIED] |
| 9 | Production VPS 24/7 | DEVELOPMENT_ROADMAP + canonical ROADMAP blockers | CONTRADICTED | OWNER_VISION_REGISTRY §4: "no VPS (owner)" |
| 10 | Roadmap v3 M1: daemon soak ≥7 days | AHOS_ROADMAP_v3 (08-18) | PARTIAL | 92 soak commits; `reports/PRE_SOAK_STATUS.txt` pre_soak_entry_ok=False |
| 11 | Roadmap v3 M2: CoinGecko/explorer/multi-chain adapters | AHOS_ROADMAP_v3 | UNVERIFIED | not checked |
| 12 | Roadmap v3 M3: calibration harness + weight governance | AHOS_ROADMAP_v3 | PARTIAL | 25 calibration commits, latest d2aa09b 10-03; docs/CALIBRATION_LIFECYCLE.md |
| 13 | Roadmap v3 M4: Telegram product, alert hygiene | AHOS_ROADMAP_v3 | PARTIAL | same blocker as #6 |
| 14 | P0 verified contract addresses (identity) | OWNER_VISION_REGISTRY (09-12) | DONE | 373516e, b5929a7 (two-source identity) |
| 15 | P1 web chat FA/EN | OWNER_VISION_REGISTRY | UNVERIFIED | not checked |
| 16 | P1 loud alerts (Telegram + on-site) | OWNER_VISION_REGISTRY | UNVERIFIED | not checked |
| 17 | P1 Command Center dashboard | OWNER_VISION_REGISTRY | DONE | CommandCenter.tsx; e73ff7b; now superseded by Dashi shell (54dcd3c) |
| 18 | P2 3D/audio/real-time environment engine, tree metaphor | OWNER_VISION_REGISTRY | PARTIAL | Dashi stage 54dcd3c; globe M-D6.1 staged, uncommitted; weather/audio not built |
| 19 | P3 10-team AI council | OWNER_VISION_REGISTRY | PARTIAL | AUTONOMOUS_VISION table: anti-echo code exists, not run on live decisions |
| 20 | P3 learn from paper wins/losses | OWNER_VISION_REGISTRY | PARTIAL | `paper_trading/lessons.py` exists; no M49 ledger |
| 21 | P4 world model | OWNER_VISION_REGISTRY | NOT STARTED | registry itself: "NOT IMPLEMENTED" |
| 22 | Goal #1 = low-latency crypto scanning | OWNER_VISION_REGISTRY §2 | CONTRADICTED | current direction: gold first (M13), crypto later (M13.3/M55) |
| 23 | Mission "NOT a trading bot", early-token intelligence via Persian Telegram | canonical/MISSION.md (08-16) | CONTRADICTED | today: "self-evolving trading system", gold paper cycle, dashboard-first |
| 24 | Trading stage 7 "limited live (tiny capital)" | OWNER_VISION_REGISTRY §2 | CONTRADICTED | today's hard rule PAPER_ONLY + Handoff §6 "real-money bots always rejected" |
| 25 | M9 evidence ordering / scheduler fix | MISSION_PLAN (10-03) | DONE | 3710288 |
| 26 | M10 native PostgreSQL/PGlite, retire Docker/n8n | MISSION_PLAN | PARTIAL | stages 1-3,5 done (fb94082, 73279bf, f6a3bb9); stage 4 BLOCKED_OWNER (.env flip) |
| 27 | M10.1 PGlite empty-store init | AUTOPILOT_QUEUE | DONE | by Grok 10-07 (queue row) |
| 28 | M11.1–M11.4 one-click launcher | MISSION_PLAN | DONE | 33 commits, latest f6c4f20 10-07 |
| 29 | M48.1 Next security update | AUTOPILOT_QUEUE | DONE | queue row DONE |
| 30 | M48 safe dependency updates | AUTOPILOT_QUEUE | PARTIAL | 9 commits (c7fbfc5 10-08); source-map-js bump blocked |
| 31 | M54 AHOS_DATA_DIR paths | AUTOPILOT_QUEUE | DONE | 28bf810 |
| 32 | BL QA blockers | AUTOPILOT_QUEUE | DONE | b9eba89, 2a1f6d4, 7436aca |
| 33 | M12 agent organisation | AUTOPILOT_QUEUE | DONE | a2715ba |
| 34 | M34 coherence audit | AUTOPILOT_QUEUE | DONE | ac6eafe (merges M34.3 not executed) |
| 35 | M13 gold paper trading T0→T1 | MISSION_PLAN / vision 11.0 | PARTIAL | 95d4618, 5988620, judge CLEAN with 3 cycles / 0 trades; queue row still says PENDING; 7-day soak never run |
| 36 | M42 single hash-chained ledger + nightly reconcile | AUTOPILOT_QUEUE | PARTIAL | judge.py on mission ledger (5988620); M34 measured 6 ledger stores; paper_trading/ledger.py still separate |
| 37 | M43 decision records + per-market tier state | AUTOPILOT_QUEUE | PARTIAL | `architecture/markets/tier_gate.py` (5988620) |
| 38 | M39 kill switch + monthly fault injection | AUTOPILOT_QUEUE | PARTIAL | PaperBreaker in risk.py (5988620); monthly fault injection absent |
| 39 | M35.1–M35.5 Kian leader (core, chat, Telegram, nightly report, routing) | MISSION_PLAN v1.6 | NOT STARTED | no kian module; 35.3 BLOCKED_OWNER |
| 40 | M37 frontier model slots | MISSION_PLAN v1.6 | NOT STARTED | doc only (14f2165) |
| 41 | M38 execution gateway (paper) | MISSION_PLAN | NOT STARTED | no architecture/execution |
| 42 | M40 treasury request flow | MISSION_PLAN | NOT STARTED | no architecture/treasury |
| 43 | M41 broker key self-check | MISSION_PLAN | NOT STARTED | no commits |
| 44 | M44 Science Radar | MISSION_PLAN v1.7 | NOT STARTED | only a cadence entry in f6a3bb9 [UNVERIFIED] |
| 45 | M45 Auto Lab | MISSION_PLAN | NOT STARTED | BLOCKED_OWNER |
| 46 | M46 Self-Debug | MISSION_PLAN | NOT STARTED | no commits |
| 47 | M47 Health Monitor | MISSION_PLAN | NOT STARTED | no architecture/health |
| 48 | M49 Lessons Ledger | MISSION_PLAN | NOT STARTED | no commits |
| 49 | M50 Weekly Intelligence Exam | MISSION_PLAN | NOT STARTED | no commits |
| 50 | M51 Self-Improvement Loop | MISSION_PLAN | NOT STARTED | doc only d2a6fc4 |
| 51 | M52 Skill & Plugin Marketplace | MISSION_PLAN v1.8 | NOT STARTED | doc only 0b2f274; Asi vetting is the manual form |
| 52 | M14 Mission Controller / autonomous engineering core | MISSION_PLAN | PARTIAL | `architecture/mission/ledger.py` (d1571c4) exists; controller not built |
| 53 | M15 council/University v1 | MISSION_PLAN | PARTIAL | council code; 3eea757 discovery report |
| 54 | M16 University + GitHub R&D, world model | MISSION_PLAN | NOT STARTED | `self_research/oss_pipeline` missing; knowledge store 0 claims (vision) |
| 55 | M17 dashboard: memory/evolution views, North Star scorecard, wealth panel | MISSION_PLAN | PARTIAL | Dashi M-D1..M-D5 (see #77-#86) |
| 56 | M18 gold research/accounting, news + daily report | MISSION_PLAN | PARTIAL | gold paper only; no news/accounting |
| 57 | M19 multi-market + low-latency | MISSION_PLAN | NOT STARTED | re-cut as M13.1-13.6 |
| 58 | M20 BrokerAdapter + OMS ("no parallel engine") | MISSION_PLAN | NOT STARTED | no architecture/brokers; gold_paper.py reuses paper_trading.exit_rules but has its own risk.py |
| 59 | M21 risk engine v2 (fractional Kelly, vol targeting) | MISSION_PLAN | NOT STARTED | gold risk.py scope vs spec [UNVERIFIED] |
| 60 | M22–M24 testnet treasury, compliance/venue eligibility, capital allocator | MISSION_PLAN | NOT STARTED | no commits |
| 61 | M25 paper marathon + G-L2 (DSR, PBO, walk-forward) | MISSION_PLAN | NOT STARTED | no commits |
| 62 | M26/M27 real-pilot readiness, withdrawal (human gate) | MISSION_PLAN | NOT STARTED | correctly gated |
| 63 | M28 Strategy Arena | AUTONOMOUS_VISION v1.3 | NOT STARTED | no commits |
| 64 | M29 Crisis simulator | AUTONOMOUS_VISION v1.3 | NOT STARTED | no commits |
| 65 | M30 memory consolidation | MISSION_PLAN | NOT STARTED | M34: canonical memory store EMPTY |
| 66 | M31 nightly report | MISSION_PLAN | NOT STARTED | no commits [UNVERIFIED: NIGHT_RUN_REPORT is Claude's, not AHOS's] |
| 67 | M32 (mother-house / wealth items; exact title not read) | MISSION_PLAN M14-M33 row | UNVERIFIED | |
| 68 | M33.1–M33.24 Token Hunter | AUTONOMOUS_VISION v1.4/1.5 | NOT STARTED | docs only (068dea9) |
| 69 | M55 Token Hunter v2 | AUTOPILOT_QUEUE | NOT STARTED | no commits; uses DEXTools (paid) → must stay free |
| 70 | M56 Arena skill | AUTOPILOT_QUEUE | NOT STARTED | |
| 71 | M57 sub-team org v3 / University org | AUTOPILOT_QUEUE | NOT STARTED | |
| 72 | M58.1–M58.6 operational AGI loops | AUTOPILOT_QUEUE | NOT STARTED | |
| 73 | M59.1–M59.5 University Saturday exam | AUTOPILOT_QUEUE | NOT STARTED | no config/university |
| 74 | M36 autonomous world orchestration | AUTOPILOT_QUEUE | NOT STARTED | last by design |
| 75 | M53 quarantine dead trees (tests2b, slills, run_ahos.sh) | AUTOPILOT_QUEUE | NOT STARTED | no commits |
| 76 | M-D1 app window | TEAM_QUEUE / Dashi | DONE | e9d2ddf |
| 77 | M-D3 tokens + truth badge | Dashi | DONE | a2803dd |
| 78 | M-D4 snapshot vocabulary | Dashi | DONE | e73ff7b |
| 79 | M-D5.1 prototype review + packages | TEAM_QUEUE (10-11) | DONE | 73a03e4 |
| 80 | M-D5.2/5.3 stage + quality probe | TEAM_QUEUE | DONE | 54dcd3c, e6cd514, b827cb0 |
| 81 | M-D5.4 context-loss fallback | TEAM_QUEUE | DONE | 6b06185 |
| 82 | M-D5.5 Hardware Tier Panel | TEAM_QUEUE | PARTIAL | 2f0646c; owner QA 19:26 "not wow yet" |
| 83 | M-D5.6 perf overlay | TEAM_QUEUE | NOT STARTED | |
| 84 | M-D6 globe | TEAM_QUEUE | PARTIAL | staged uncommitted (Globe.tsx, M-D6.1 screens) |
| 85 | M-D7 pipeline graph + telemetry | TEAM_QUEUE | NOT STARTED | |
| 86 | M-D8 agents tower / council room | TEAM_QUEUE | NOT STARTED | |
| 87 | M59.S idea shelf + RAM guard + tiers | TEAM_QUEUE / Aji v1.1 | PARTIAL | only config/idea_shelf.json seed (f0f201f); no core/idea_shelf |
| 88 | M57.T trend hunter | TEAM_QUEUE | NOT STARTED | no institute/trend_hunter |
| 89 | Asi approvals as addenda (Laya, light-ocr, Codebase Memory MCP...) | TEAM_QUEUE | NOT STARTED | shelf entries only |
| 90 | M13.1–M13.6 multi-market | README v1.20 (10-10) | NOT STARTED | waits on gold soak |
| 91 | Pump Hunter v1.44 | DEDUP v1.44 (10-11) | NOT STARTED | not in TEAM_QUEUE |
| 92 | M58 AGI ideas v1.47 | DEDUP v1.47 (10-11) | NOT STARTED | "NOT in Claude's queue yet" |
| 93 | bitnet.cpp T8 helper v1.46 / Kev v1.42 | DEDUP | NOT STARTED | not in TEAM_QUEUE |
| 94 | University tracks T-A..T-F | README L109 (10-11) | NOT STARTED | "(later)" |
| 95 | M-PORT Windows installer | Handoff §1 | NOT STARTED | not in any queue |
| 96 | M80 OSINT white-hat team | queue_2050 M80 v2 (10-09) | NOT STARTED | not in TEAM_QUEUE |
| 97 | M70 AGI research | queue_2050 / reports/grok/CLAUDE_MISSION_AGI_RESEARCH_M70.md (untracked) | NOT STARTED | |
| 98 | Secrets never committed (S-01) | OWNER_VISION_REGISTRY §4 | UNVERIFIED | not scanned this pass |

## 2. Counts
Total goals: 98. NOT STARTED: 46 · PARTIAL: 25 · DONE: 17 · UNVERIFIED: 5 · CONTRADICTED: 4 · DROPPED: 1

## 3. Promised but missing from the current queue (TEAM_QUEUE_2026-10-11)
The current queue contains only M-D5..M-D8, "finish gold", M59.S, M57.T and the Asi verdicts. Missing from it: the **gold 7-day soak** (#10, #35), M42 single-ledger reconcile (#36), M47 Health Monitor, M49 Lessons Ledger, M35 Kian, M58.1-6 and the v1.47 ideas, M59.1-5 University exam, Pump Hunter v1.44, bitnet/Kev, M13.1-13.6, M-PORT, M80, M53 cleanup, M10 stage 4 (owner act), Telegram token rotation (owner act), and the whole crypto token-intelligence line (Phases 2-4, M33/M55) that was the original mission. CLAUDE_AUTOPILOT_QUEUE.md still lists most of them as PENDING, but the handoff says Claude builds only from TEAM_QUEUE, so in practice they are invisible.

## 4. Contradictions between the old vision and today's direction
1. **Product identity.** canonical/MISSION.md (08-16) says "NOT a trading bot. NOT a pump oracle": early-token intelligence and decision support over Persian Telegram. Today: "self-evolving trading system", gold paper cycle, plus a "Pump Hunter". The pump hunter is defined as white-hat public-data alerts, which is compatible in spirit, but the wording conflicts with the mission's law. Needs an owner ruling.
2. **Goal #1.** OWNER_VISION_REGISTRY (09-12): "Yes goal #1: low-latency crypto scanning". Today: gold first, crypto at M13.3.
3. **Live trading.** Registry stage 7 plans "limited live (tiny capital)", and M26/M27 plan a real-pilot gate. Today's rule is strict PAPER_ONLY, with real-money bots always rejected. These are compatible only if stage 7 stays human-gated and far off. The owner should confirm whether stage 7 is still the goal.
4. **VPS.** The August roadmaps make a VPS a top blocker; the registry says no VPS. The portable-laptop direction (M-PORT, 8 GB floor) follows the newer rule.
5. **Priority law.** D-P01 in the 10-08 continuity brief ranks aesthetics last, and the 09-12 registry says "P2 experience incremental, not one giant PR". Today the dashboard is item 1. A recent owner order overrides, but this is the biggest re-prioritisation in the history.
6. **"No parallel engine" (M20).** The new `architecture/markets/gold_paper.py` + `risk.py` sit beside the older `paper_trading/` engine (engine.py, engine_v2.py, engine_v3.py, risk.py, ledger.py). It reuses `paper_trading.exit_rules`, but its risk and ledger are separate, which adds to the ledger fragmentation M34 measured. PARTIAL conflict.
7. **Paid source in plan.** M55 Token Hunter v2 names DEXTools/GMGN/Birdeye/Photon. DEXTools v2 is paid (adapters.py:603), so M55 needs a free-only re-cut.

## 5. Top 5 to re-queue (priority order; all PAPER_ONLY, $0, fit 8 GB)
1. **M13-SOAK: gold 7-day paper soak + daily M42 judge.** This is now the owner's decision (parallel with the dashboard). Add M42 nightly reconcile onto the mission ledger so the soak has one ledger. Unblocks M13.1-6 and Pump Hunter.
2. **M59.S core + RAM guard** (`core/idea_shelf/` registry, hardware, flags, ram_guard + tests). This is the 8 GB rule, and it is needed before any shelf item turns on.
3. **M47 Health Monitor + M39 monthly fault injection.** A 7-day unattended soak on a laptop needs READ/DOWNGRADE/HALT watching. Small, and builds on the existing breaker.
4. **M49 Lessons Ledger + M58.1 decision self-evaluation**, fed by the soak's paper trades. This is the first real "self-evolving" loop (owner North Star) and the core of the v1.47 M58 ideas.
5. **Crypto token-intelligence line, revived free-only:** re-cut M55/M33 with free sources (DexScreener, GeckoTerminal, GoPlus, RugCheck, already in adapters.py) into the M13.3 crypto adapter, with Pump Hunter v1.44 as its alert layer. This is the original mission and the identity work (373516e/b5929a7) is already built for it.
Honourable mentions: M53 dead-tree cleanup (cheap); M10 stage 4 and the Telegram token rotation are **owner acts**, so raise them with the owner instead of queueing them for Claude.

## 6. Unverified / not done in this pass
- The older booklet visions under `ahos_gemini/docs/archive/consolidation_2026-09-26/` (Ultimate Vision v1.0, Strategic Master Plan v10.0, Roadmap.txt) were not read.
- Rows marked UNVERIFIED were not checked against code.
- Statuses from `CLAUDE_AUTOPILOT_QUEUE.md` (M10.1, M48.1) are taken from the queue row, not re-tested.
- `git log --grep` counts only commits whose message names the ID, so unlabelled work may be missed.

## 7. Addendum (2026-10-12 ~00:50 Tehran): old booklet visions
Scope: `G:\robat\ahos_gemini\docs\archive\consolidation_2026-09-26\` (read-only), plus `G:\robat\ahos\docs\archive\` (subfolders: consolidation_2026-09-26, oss_research, quarantine_2026-10; quarantine has no vision/plan md files).
Read in full: `booklet_strategic_specs\آرشیو\AHOS Strategic Master Plan v10.0.txt` (undated), `booklet_strategic_specs\AHOS_System_Objectives_v1.0.txt` (undated), `booklet_strategic_specs\AHOS_System_Vision_and_Functional_Objectives_v1.0.txt` (undated).
Read by section headings + §17: `AHOS Ultimate Vision v1.0.txt` (doc states "Date: 2025", "Final Reviewed Edition"); `Roadmap.txt` = "Engineering Transition & Documentation Roadmap v1.2.1" (2026-07-10); `docs/archive/oss_research/OSS_BACKTEST_UPGRADE_PLAN.md` (header only).
NOT read (UNVERIFIED): the Architecture Bible Season 3 / v4.0 / v4.1 (≈730 KB), Technical Architecture Spec v1.1, Data Architecture Spec v1.0, Engine Specifications, AHOS_Universal_Market_Object_Standard_v1.0 (85 KB), the WF-001..WF-005 n8n workflow specs, the July 2026 daily reports in `booklet_daily_reports\`, and `booklet_chats\project_constitution_v1_frozen.txt`. The 9 `booklet_standards\*.md` files are 0 bytes.
Status evidence is a crude grep of `architecture, engine, paper_trading, strategy_lab, discovery, research, telegram_ai` .py files + `git log --grep`. "PARTIAL" here means the code mentions the concept; depth is UNVERIFIED.

| # | Goal | Source | Status | Evidence |
|---|---|---|---|---|
| 99 | Strict layer constitution: Data→Event→Feature→Score→Decision→Risk→Simulation→Execution Firewall→Action→Learning; no layer may skip | Master Plan v10 §4 | UNVERIFIED | not checked against code |
| 100 | AHOS Composite Score 0–100 from 10 sub-scores (opportunity, risk, confidence, momentum, liquidity, volume, whale, social, security, narrative) | Master Plan v10 §8 | NOT STARTED | 0 .py files match composite_score; docs/OPPORTUNITY_SCORE_DESIGN_v0.1.md exists (design) |
| 101 | Macro intelligence: Fear & Greed, stablecoin flows, BTC dominance, ETF flows, economic calendar | Master Plan v10 §6 | NOT STARTED | 0 files match fear/greed |
| 102 | Extra security sources: TokenSniffer, honeypot, rug-pull, liquidity-lock checks | Master Plan v10 §6; Objectives 6–7 | PARTIAL | 26 .py files, 3 commits |
| 103 | Detect upcoming launches before public awareness (Pump.fun, Moonshot, Raydium LaunchLab) | System Objectives #3; Functional Vision §4 | PARTIAL | 3 .py files, 5 commits |
| 104 | Continuous developer-credibility analysis | System Objectives #8 | PARTIAL | 18 files mention deployer/dev credibility |
| 105 | Scenario simulation of each candidate before recommending (Continuous Simulation Universe) | Functional Vision §5.7; Ultimate Vision §7 | PARTIAL | 28 files mention simulation; no per-candidate gate verified |
| 106 | Portfolio-context recommendations (allocation, diversification, cash management) | Functional §5.9; Objectives §6 | PARTIAL | 6 files mention portfolio; overlaps M24 |
| 107 | Autonomous attention allocation (compute/data as a finite budget) | Ultimate Vision §4 | NOT STARTED | 0 files |
| 108 | Hypothesis engine: generate / validate / evolve / retire hypotheses | Ultimate Vision §6 | PARTIAL | 41 files, 9 commits (H14 hypothesis work) |
| 109 | Source-trust evolution + evidence-conflict resolution + provenance annotation | Ultimate Vision §13 | PARTIAL | two-source witness exists (95d4618, 373516e); no source_trust module (0 files) |
| 110 | Knowledge lifecycle: confidence decay, versioning, pruning, knowledge graph | Ultimate Vision §12 | PARTIAL | decay in 18 files; knowledge_graph in 1 |
| 111 | Telegram approval requests whose human answers feed back into learning | Ultimate Vision §10.4–10.6 | PARTIAL | human_gate in 2 files; Telegram blocked (M35.3) |
| 112 | Four-question recommendation law, incl. "why better than competing alternatives" | Functional Vision §6 | UNVERIFIED | MISSION.md covers why/evidence/invalidation; the "alternatives" question not checked |
| 113 | 23-spec engineering documentation roadmap + ADRs + 5 implementation-readiness gates | Roadmap v1.2.1 (2026-07-10) | PARTIAL | ADR_ACI_001, many docs/architecture specs; mapping to the 23 not done |
| 114 | Tech stack Docker + n8n + PostgreSQL + Redis + Grafana/Prometheus + vector DB | Master Plan v10 §12 | CONTRADICTED | M10 retired Docker/n8n (73279bf); native PGlite; 8 GB floor |
| 115 | Dev workflow: Claude prompt → ChatGPT review → implement in n8n | Master Plan v10 §13 | DROPPED | replaced by Claude Code builder + Soltan supervisor |
| 116 | Institutional-grade dual-mode backtest + microstructure engine | OSS_BACKTEST_UPGRADE_PLAN | PARTIAL | 16 files mention backtest, 2 commits; overlaps M25 G-L2 |
| 117 | Universal Market Object Standard (one market object for all assets) | booklet_standards (85 KB) | UNVERIFIED | not read; highly relevant to M13.1–13.6 |
| 118 | Scope law: "not a general crypto platform; large caps only as context", DEX tokens only | Functional Vision §4; Ultimate Vision §17.1, §18.1 | CONTRADICTED | today: gold first, then oil/US/EU/Asia equities (M13.1–13.6) |

New goals: 20 (#99–#118): PARTIAL 11 · NOT STARTED 3 · UNVERIFIED 3 · CONTRADICTED 2 · DROPPED 1. The combined total is now 118.

### New contradictions
1. **Scope.** The booklets restrict AHOS to early decentralized tokens ("not intended to operate as a general cryptocurrency analysis platform"; Ultimate Vision: identity is "Autonomous Cryptocurrency Intelligence Platform"). Today's gold-first and multi-market plan (gold, oil, equities) is outside that scope. The 09-12 OWNER_VISION_REGISTRY already widened it ("future markets: gold, forex, equities… via Domain Adapters"), so the newer owner text wins, but the booklets were never formally superseded.
2. **Not a trading system.** Master Plan v10 says "AHOS یک ربات معامله‌گر نیست" ("AHOS is not a trading bot"), and Ultimate Vision §18.1 says "AHOS is not an autonomous trading system". Both match canonical/MISSION.md and conflict with today's "self-evolving trading system" label.
3. **Live trading in the roadmap.** Master Plan v10 Phase 9 "Limited Live Trading" (same as registry stage 7, #24) conflicts with today's strict PAPER_ONLY.
4. **Tech stack** (#114): Docker, n8n, Redis and Grafana conflict with the native, portable 8 GB direction.
5. **Data sources.** The booklets list DEXTools, Birdeye, Moralis, Alchemy, Infura, Covalent and ETF flows. Several of these are paid or key-gated (DEXTools v2 paid per adapters.py:603; others UNVERIFIED), which conflicts with the $0 rule.

### Top 3 forgotten items worth re-queueing (all fit PAPER_ONLY, $0, 8 GB)
1. **#100 Composite Score with explainable sub-scores**, plus #112 "why better than alternatives". This is the core ranking output every booklet centres on, and no code exists under that name. It can reuse the identity, security and two-source work already built.
2. **#109 Source-trust evolution**: per-source reliability that learns over time. It is the natural upgrade of the two-source rule, small, and it helps both gold and crypto.
3. **#103 + #102 early-launch detection with honeypot / liquidity-lock checks**: the booklets' "primary objective", and the free-data basis for Pump Hunter v1.44.
Also worth reading before M13.1: #117 Universal Market Object Standard, because it may already define the multi-market adapter shape.
