# AHOS — ISSUE REGISTER (Forensic, failure-format mandated: WHY/WHERE/WHEN/HOW/SOLUTION)
# Supersedes & extends docs/ISSUES_REGISTER.md (kept for history).
# Status: OPEN / FIXED(date) / DOCUMENTED (accepted risk) / SUPERSEDED

## FAILURES OF PROCESS (learned — the "never again" list)

### F-01 Category confusion: "Framework Ready" ≠ "Production Ready" — FIXED(08-10)
- WHY: inherited reports used "READY FOR PRODUCTION" while no component had live evidence
- WHERE: MASTERPIECE_FINAL_CONFIRMATION.md, AHOS_Phase1_QA_* family
- WHEN: throughout Phase-1 closure wave
- HOW: single-agent self-approval, no taxonomy
- SOLUTION: mandatory A–E status letters for every component (AHOS_PROJECT_STATE_MAP §1);
  the word "ready" without a letter is banned from all future reports. Pre-fix docs labeled.

### F-02 Confidence without evidence — FIXED(08-10)
- WHY: approximate backtest wins ("PF ~1.1") published without reproducible engine output
- WHERE: PHASE_2_BACKTEST_REPORT*.md, PHASE_1B_BACKTEST_REPORT.md
- WHEN: 2026-08-09
- HOW: script that produced numbers was never itself delivered → non-reproducible
- SOLUTION: NO CLAIM WITHOUT DATA rule; exact engine + validation_results.json is now the
  only numeric source; contradiction logged as C-01 below.

### F-03 Failure hiding (artifact absence claimed as verified) — FIXED(08-10)
- WHY: QA reports asserted PASS for postgresql_schema/n8n JSON/event-system that weren't delivered
- WHERE: AHOS_PHASE_1_PRODUCTION_VERIFICATION_REPORT.md etc.
- WHEN: Phase-1 closure
- HOW: verification reported against local files never handed over
- SOLUTION: artifacts rebuilt from their verified specs, then re-validated with automated checks;
  every PASS now requires a machine-checkable evidence file in reports/.

## TECHNICAL ISSUES (found by audit)

### C-01 Approximate vs exact backtest contradiction — SUPERSEDED
- WHY: prior engine unknown + omitted cost modeling
- WHERE: Phase-2 reports vs engine/ahos_backtest.py run
- WHEN: found 08-10 during exact recomputation
- HOW: 54-trade/PPF~1.1 figures vs 85/26/30-trade PF 0.36–0.89 with full cost model
- SOLUTION: exact reproducible numbers ARE the record; baseline v1.0 has NO EDGE → gate CLOSED;
  strategy redesign mandated (P3 roadmap item 4)

### C-02 MaxDD halt didn't halt — FIXED(08-10)
- WHY: breach appended to halts[] but entries kept opening
- WHERE: engine/ahos_backtest.py close_pos/entry loop
- WHEN: found in code audit this takeover
- HOW: flagged by reading code against documented 20% rule (mismatch rule=bug)
- SOLUTION: halted_permanent flag; effect proven (MaxDD 51–59% → 20.4–21.7%)

### D-01 "FINAL_3YR" data files are duplicated 21-day windows — DOCUMENTED
- WHY: chunked downloader collided with session caps; each chunk re-fetched same window
- WHERE: uploads/FINAL_* (16 files); SOL chunk4==chunk5 (md5-identical)
- WHEN: found in forensic audit (md5 + timestamp-diff analysis)
- HOW: naming implied 3-year depth that content doesn't have
- SOLUTION: excluded from canonical set; real depth = 83 days honestly restated everywhere;
  3yr acquisition re-planned as priority 3

### D-02 assets_48.md lists 45 symbols (not 48) — FIXED(08-10) in docs
### D-03 BTC clean file has 2 registered gaps (bad-row removals) — DOCUMENTED (no interpolation per rules)
### D-04 dual CSV schemas (t,o,h,l,c,v vs standard) — FIXED(08-10, alias-mapped in auditor)

### W-01 Workflow 01 batch loop dead-ended after first symbol — FIXED(08-10)
- WHY/WHERE/HOW: SplitInBatches had no loop-back edges — only BTC would ever ingest
- SOLUTION: loop-back edges on all terminal branches; validator reachability proof

### W-02 Workflow 03 routing bug + missing protocol commands — FIXED(08-10)
- WHY/WHERE: Command Switch fed Authorized? which only reached /status handler (kill/approve dead-ended)
- HOW: cmd→handler mismatch found in graph review
- SOLUTION: full rewrite; auth-guard BEFORE switch; added /health /agents /reset (directive §11);
  reset writes KILL_RESET + clears halt flags in audit trail

### S-01 Exposed temporary bot token — OPEN (user action, blocking)
### S-02 Exchange per-pair specs UNKNOWN (min order/contract/precision) — OPEN (verification protocol pending)

### T-01 pytest import of validator executed sys.exit — FIXED(08-10, __main__ guard)
### T-02 close_pos UnboundLocalError after DD-fix — FIXED(08-10, nonlocal) 
### T-03 W2 connection typo introduced during edit ("&&" fragment) — FIXED(08-10, validator caught pre-delivery)

### R-01 "3-year dataset" blocker — RESOLVED(08-10)
- WHERE: ISSUES D-01 & priority item 3
- HOW: LBank chunked path capped — architecture swap per plan (exchange/source-agnostic rule)
- SOLUTION: engine/acquire_3yr.py → BinanceVision public archive (USDT-M klines+funding+metrics);
  31,608 h-candles/symbol, per-file sha256, dedupe+gap+OHLC gates; 9 missing funding files (Aug 2026)
  documented in manifest, never fabricated.
### R-02 funding fractional-second timestamps crashed loader — FIXED(08-10, format='mixed')
### R-03 research_report_bot import side-effect risk — FIXED(08-10, independent transport)
### R-04 naive/aware datetime crash in acquisition — FIXED(08-10)
- note: all four found by running the code against reality, not by reading docs.

### R-05 Batch-2 statistical discipline — MULTIPLICITY GUARD registered(08-10)
- WHY: batch-1 consumed the OOS window; a second evaluation round on the same OOS would be
  selection-biased without correction
- SOLUTION: batch-2 candidates (H10–H12) judged at raised bar OOS PF>1.5, pre-registered in cards;
  enforced in run_lab.verdict(gates_override) and pytest (test_hypothesis_cards_complete)
### R-06 H11 falsified by zero-signal (learning value, not defect) — DOCUMENTED
- WHERE: |S|≥0.8 conviction extreme never occurs within composite feature scale
- SOLUTION: falsification recorded; H11 family closed. Leads L1/L2 exhausted; L3 partially falsified.

### R-07 H13 batch-3 verdict — REJECTED at raised bar (2026-08-11)
- WHAT: instrument-scoped BTC OI×high-vol on 6.6y — train PF 1.214 / OOS PF 1.274 (bar 1.5),
  stress 0.976, WF 50%, MC 75.9%, 31 OOS trades (sample gate now met)
- LEARNED: H10's PF 2.35 was small-sample inflation (n=16 → n=31, 24m → PF 1.27). Documented, archived.
- STATUS: rejected per pre-registered criteria; council disagreement logged in META_ANALYSIS §council.
### R-08 Strategic mission correction absorbed (2026-08-11)
- AHOS re-scoped: Early Crypto Opportunity Intelligence & Decision Support (discovery→security-veto→
  scoring→monitoring, Persian UX). Trading-bot framing retired; 10 design docs delivered;
  implementation starts per ROADMAP; E-01 forward study is the minimum defensible next experiment.
### R-09 v3.0 directive's "83-day data" premise — SUPERSEDED
- The directive text predates wave-2 acquisition; 3.6y/6.6y real governed datasets already exist.
  Recorded to prevent stale claims from re-entering reports.

## STANDING RULES GOING FORWARD
1. Every report item carries a status letter. 2. Every number links to a reproducible artifact.
3. Every failure gets a WHY/WHERE/WHEN/HOW/SOLUTION entry. 4. Gate math, not wording, opens gates.

### R-10 n8n v2 disables executeCommand by default — FOUND by live smoke test, RESOLVED (2026-08-11)
- WHERE: workflows 10/11/12 use n8n-nodes-base.executeCommand (research lab shell-out).
- WHEN FOUND: live import smoke test on real n8n 2.8.4 runtime (npm install, sqlite, 127.0.0.1:5678).
- HOW FOUND: live node-type registry audit (/types/nodes.json, authenticated) — 811 types, executeCommand MISSING.
- ROOT CAUSE (n8n source, modules/breaking-changes/rules/v2/disabled-nodes.rule.js): "ExecuteCommand and
  LocalFileTrigger nodes are now disabled by default for security reasons" (v2 breaking change).
- SOLUTION (deployment): NODES_EXCLUDE=[] env re-enables (verified live: 814 types, executeCommand OK).
- LONG-TERM (roadmap): Phase-2 discovery collectors run as Python services; n8n calls them via httpRequest,
  so workflows 20/21/22 will NOT depend on executeCommand; 10/11/12 keep the env-var escape hatch documented
  in RUNBOOK_OPERATIONS. Structural validator extended? No — validator is static; live audit is now a runbook step.

### R-11 n8n live import smoke test — EXECUTED, 6/6 PASS (2026-08-11)
- WHAT: n8n 2.8.4 booted in sandbox (node v20.20.2, sqlite); CLI import of all 6 ahos_*.json → exit=0 ×6;
  list:workflow + REST confirm persistence across restart; healthz ok.
- ACTIVATION GATE: POST /rest/workflows/<W01>/activate → 400 WorkflowValidationError citing exactly the 2
  postgres-credential nodes ("__ASSIGN_AFTER_IMPORT__" by design). Engine-level validation of our files CONFIRMED;
  activation/execution remain PENDING (Postgres + TELEGRAM env — user blockers 1+2), per directive STEP 10–12.
- EVIDENCE: reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt (full transcript incl. healthz, import log, node audit).
- HYGIENE: no real secrets used; throwaway owner account + cookie jar purged after test.

### T-04 research_report_bot digest crash (KeyError ETHUSDT) — FIXED(08-11)
- WHY: digest read only the LATEST experiment log (batch-3 ⇒ H13 only) and hardcoded a tri-asset symbol loop;
  batch-3's BTC-scoped scope broke the assumption. Found by the CI gate (stage-5), not by reading code.
- WHAT: digest now renders the FULL registry (13 cards), each from its own evidence log; scoped candidates
  render only tested symbols + explicit scope note; zero-signal PF renders "—"; accepted ratio is dynamic (0/12).
- EXPECTED: stage-5 digest prints 13 truthful lines, zero exceptions. ROLLBACK: /tmp/research_report_bot.py.pre_t04_fix
- TEST: engine/research_report_bot.py --simulate prints H1..H13; full CI re-ran to ALL CHECKS GREEN (unpiped exit 0).
- LESSON ENCODED: registry MERGE across batches changed a global pointer's semantics — any "latest log" pointer
  is a coupling hazard; render from the registry, not from a single experiment file.

### R-12 Mission v1.1 adopted + Discovery Core implemented (2026-08-11, wave-5)
- WHAT: §21 deliverables A–J produced (docs/mission_v1_1/); STEPs 1–9 implemented as REAL code:
  discovery/{pal,identity,observations,lifecycle,feature_store,security_gate,outcomes,ranker,collect}.py
  + providers.yaml (14 providers, 9 capability chains) + schema v1.2 (sqlite canonical + pg twin) + 22 tests.
- EVIDENCE: tests/test_discovery.py 22/22; CI 6-stage green (incl. new stage 3b); first REAL E-01 cohort
  collecting LIVE from sandbox (T0=2026-08-11 17:20Z; 61 tokens / 75 obs after 2 passes; 0 dedupe violations).
- DISCIPLINE: rank-first only (no numeric score/probability); UNKNOWN=NULL; raw payloads sha256-pinned.

### R-13 Provider reachability ground truth from sandbox (2026-08-11) — replaces assumptions
- LIVE VERIFIED OK: DexScreener (profiles/boosts/tokens-v1), GeckoTerminal (networks/new_pools/pool),
  RugCheck, DefiLlama, Solana RPC ×2, publicnode EVM ×3 (ETH/BSC/Base), GitHub API, CoinTelegraph+TheBlock RSS.
- FAILED/DEGRADED: GoPlus timeout ×3 (adapter ships DEGRADED, RugCheck+coverage-cap compensates);
  LlamaRPC 521 (dropped); Ankr now requires key (reclassified); Cloudflare ETH -32046; CryptoPanic 404 ×2
  (endpoint changed — re-verify before Phase-7); CoinDesk RSS 308-chain (secondary).
- Iran-network columns remain UNKNOWN (user-side probe script to ship engine/pal_probe.py).

### R-14 Lifecycle dead-path semantics captured by test (2026-08-11)
- Test-first assumption said OBSERVING→RESOLVED; machine rule (F §3: DEAD after 24h silence) fired first —
  RESOLVED-from-DEAD is now test-pinned as the intended semantic. Doc F §3 consistent; no code change.

### T-05 YAML hand-parser abandoned for PyYAML (2026-08-11)
- WHY: mini-parser broke on flow-maps with braces (fail-loud as designed, caught on first load).
- FIX: PyYAML 6.0.3 + strict shape validation (unknown provider refs in capability chains raise).

### R-15 Holder-source refutation + Wave-6 discipline case (2026-08-11)
- WHAT: drafted expectation "getTokenLargestAccounts LIVE VERIFIED" was REFUTED by probe battery
  (5/5 free public SOL RPC rejections: 429×3, 403, timeout, 401). Docs E/I corrected with visible
  standing-correction notes; adapter+schema shipped; fs_v0.2 holder features emit ONLY from real rows.
- STANDING RULE ENACTED (Council D2): no capability claim without a probe id in the record.
- fs_v0.2 (5 features) + research/baseline_stats.py (Wilson CI, MIN_N=200/MIN_POS=20 locked) +
  SEARCH_SPACE_REGISTRY (batch B1) shipped; live report-mode scan: INSUFFICIENT_DATA — honest by construction.

### R-16 Document hygiene wave (Part XIX–XXIV executed, 2026-08-11)
- 194 files inventoried with sha/title/category (reports/PROJECT_DOCUMENT_INVENTORY.json).
- 3 exact-dup groups in uploads LEFT INTACT (user-decision list); 6 near-dup pairs documented.
- 2 supersessions resolved: docs/ISSUES_REGISTER.md, reports/FINAL_DELIVERY.md → docs/archive/ with
  sha256 pre-move + redirect stubs; council sign-off recorded (L/D1). Zero failures hidden; fully reversible.
- Canonical knowledge set created: docs/canonical/ (12 compact docs; reference-not-copy law).

### R-17 Wave-7 hygiene engine + autonomous safe cleanup (2026-08-11)
- WHAT: engine/doc_hygiene.py (inventory→diff vs 194-baseline→A–G classify→plan→execute, sha-verified,
  manifested). Executed: 4 exact-dup ARCHIVES (uploads → uploads/_archive_exact_dups_wave7/),
  6 bytecode DELETES, n8n_runtime TREE DELETE (regenerable; evidence preserved; recipe in manifest).
- EVIDENCE: reports/PROJECT_DOCUMENT_INVENTORY_WAVE7.json (230 files; +45/−9/Δ16);
  reports/CLEANUP_MANIFEST_WAVE7.json (11/11 OK); idempotency gate met (2nd dry-run plans 0).
- COUNCIL: D4 (reversibility demanded by Security; Auditor caught re-planning bug — fixed same-wave).

### R-18 pal_probe.py — permanent probe tooling; GoPlus UPGRADED, pollinations REFUTED (2026-08-11)
- WHAT: engine/pal_probe.py emits probe-id records for every PAL capability + degraded extras list.
- FINDINGS: security_evm GoPlus OK 361ms (PRB-20260811-004; was FAILED-timeout earlier same day —
  providers.yaml upgraded with probe id); coindesk RSS OK → added as narrative 3rd fallback (017);
  still DOWN: LlamaRPC 521 (012), Helius-public 401 (015), CryptoPanic 404 (016), Cloudflare -32046
  (013), Ankr key-required (014). AI probe PRB-20260811-AI-001: pollinations HTTP 402 (keyless tier
  gone) → removed from AI chains; chain verified in DETERMINISTIC_ONLY mode (by design).
- LAW EXTENDED: no capability claim without a probe id — now machine-enforceable via reports/pal_probe_*.

### R-19 H14–H20 registered + research engine extended (2026-08-11)
- WHAT: H14–H20 cards with full pre-registration payloads in research/SEARCH_SPACE_REGISTRY.json
  (B2 batch, 7 cells: H14/H15/H18 ×{24h+50,72h+100} + H20 ×{24h+50}; statuses COMPUTABLE vs
  DATA-BLOCKED explicitly). baseline_stats.evaluate_conjunction (parameterized, op-whitelist,
  injection-proof) + discovery/materialize.py (features frozen at exact as_of=first_seen+3600;
  outcomes only after resolution+horizon closure; idempotent).
- EVIDENCE: tests/test_wave7_research.py 10/10; report-mode scan 7/7 INSUFFICIENT_DATA
  (research/reports/baseline_stats_b2_reportmode_20260811.json — honest, 0 resolved tokens yet).
- COUNCIL: D3 (H20 strict conjunction; ≥3-of-4 relaxation = future H21 only, pre-hoc relax banned).

### R-20 Telegram AI core implemented (C Tested) (2026-08-11)
- WHAT: telegram_ai/{intent,providers,positions,alerts}.py + ai_providers.yaml; 25 tests.
  All 15 mandated Persian examples parse (rule ids probed); amount/unit/digit normalization pinned;
  anaphora needs-context honest; UNKNOWN never guessed; AI never on ledger path (construction);
  alerts WHY-mandated (no reason/evidence → ValueError); footer law pinned.
- LIMITS (honest): live bot glue blocked on ①token ②VPS; keyless free LLM API does not currently
  exist (402 finding R-18); AI assist = free-tier keys (user) or local ollama (VPS) — both documented.
- COUNCIL: D1 (deterministic-first; AI/ML dissent recorded), security veto on LLM-first routing.

### R-21 Canonical knowledge map v2 + entry node (2026-08-11)
- WHAT: docs/canonical/KNOWLEDGE_MAP.md created; README points to it as THE entry point;
  W7_H doc holds the human view; duplication rule: reference-not-copy, collapse-on-sight.

### R-22 E-01 pass t4 + sweep (2026-08-11)
- WHAT: pass t4 → 158 tokens / 217 observations (74 SOL·36 BSC·29 BASE·19 ETH); sweep: 158 OBSERVING,
  0 DEAD, 0 RESOLVED (72h barrier not yet reached); 0 errors all streams; report
  research/experiments/e01_collection_t4_20260811.json. Next: t5+ passes this week;
  72H COHORT EXIT REPORT scheduled ≥2026-08-14 via discovery/materialize.py (machinery C Tested).

### R-23 E-01 pass t5 + data-quality sweep (2026-08-11, observation mode)
- EXECUTED: collect t5 (75 ingested, 0 errors, 5/5 streams OK) → 223 tokens / 292 obs / 241 pairs;
  lifecycle sweep: 223 OBSERVING · 0 DEAD · 0 RESOLVED; dedupe collisions 0; error_state rows 0.
- COVERAGE: price 100% · volume_24h 100% · txns_1h 100% · liquidity 91% · mcap 26% (mcap NULLs are
  provider-side absence for newborn pools — honest NULL, not imputed).
- ANOMALY (documented, NOT patched — directive §11): 17/292 rows show liquidity_usd ≈ −1e-14
  (floating-point dust from provider arithmetic on ultra-low-cap EVM tokens; price≤0: 0 rows).
  Severity: EPS-level noise; research impact assessment deferred to Quant at cohort-report time;
  no filter/tuning applied now (no silent workaround).
- GATES: earliest 72h closure 2026-08-14 18:00Z (70.5h remaining) — materialize + first cohort exit
  report are WALL-CLOCK GATED. B2 scan gated at ≥200 RESOLVED (currently 0). Probe battery: not due
  (daily cadence; last run 2026-08-11 18:43Z).

### R-24 Paper Trading Lab — isolated Track-B online (2026-08-12)
- WHAT: paper_trading/ subsystem (engine/ledger/entry_rules/exit_rules/position_monitor/cost_model/
  reports/schema.sql/strategies.json) — event-sourced append-only store (UPDATE/DELETE triggers),
  discovery opened READ-ONLY (uri mode=ro, verified: Track-A counters unchanged by cycle 001).
- LAWS TEST-PINNED (tests/test_paper_trading.py 14/14): as_of leakage impossibility (future-pollution
  replay identical), one-trade-per-token dedupe, invalid/negative/EPS-dust data rejected honestly,
  UNKNOWN never guessed, security veto blocks, SL-before-TP gap rule, stale-price exits forbidden
  (INVALID_DATA_UNAVAILABLE instead), chronology violations → invalidation+evidence, gross-win/
  net-loss = LOSS, append-only triggers fire.
- CARDS: PT-BASELINE-v1 / PT-X1-v1 / PT-COST-v1 locked pre-result (strategies.json + code constants);
  any change = new version. fee 100bps/side; impact slippage linear on notional/liquidity (floor 25bps).
- FIRST LIVE CYCLE (paper_trading/runs/cycle_001_20260812.json): 295 scanned → 233 snapshots →
  218 NOT_QUALIFIED (dominant: liquidity < min / liq UNKNOWN / dust) → 15 PAPER ENTRIES
  (3 SOL live-RugCheck PASS_WITH_UNKNOWN cov 0.143; 12 EVM cov 0.0 NO_EVM_NORMALIZER recorded);
  62 budget-deferred (PAL discipline, retry next cycles); exposure $15,000 notional; 0 exits yet.
- HONEST LIMITS: EVM security normalization absent (cov 0.0 flagged everywhere — wave-8 council item);
  exit pricing is pass-cadence-limited (6h staleness law enforced, not interpolated).
- REPORTS: report rows distinguish GROSS/SLIPPAGE/COST/NET; 30-closed-trade gate blocks any
  expectancy language (periodic report: reports/periodic_report_20260812.txt).

### R-25 Wave-8: Track-B realistic 24h $20 experiment — STARTED (2026-08-12)
- WHAT (added, all versioned; v1 untouched): paper_trading/{schema_v2.sql, security_multi.py
  (GoPlus→VETO_REGISTRY normalizer + rugcheck path + coverage law), risk.py (§N classifier,
  §E escalation, §B trapped/total-loss + recoverable model), bankroll.py (append-only portfolio),
  engine_v2.py, cycle.py (budget-split runner), cards PT-BANKROLL-v2/PT-X2-v2 locked in
  strategies.json + code constants. Numeric opportunity scores deliberately REPLACED by categorical
  bands (defense of the pre-gate no-score law) — council note recorded.
- TESTS: tests/test_paper_trading_v2.py 12/12 (normalizer UNKNOWN law, coverage gates, classifier
  reasons, trapped math, bankroll exactness+immutability, EVM honeypot/tax gate, honeypot-flip ⇒
  TOTAL_LOSS capital_loss=alloc, liq-halving ⇒ EXIT_RISK, sell-tax accounting, no-cash ⇒
  QUALIFIED_SKIPPED_NO_CASH evidence). CI: 106 tests, exit 0.
- FIRST LIVE CYCLE (evidence reports/paper_cycle_20260812_080522.json): 7 PAPER entries ($2 each,
  cash $20→$6): TOADER(SOL, PARTIAL-cost taxes-UNKNOWN) + PRISM/V4/SMA/ALIEN/QQQB/TLI (EVM, FULL
  cost, sell_tax=0 known). Rejects: 201 liquidity / 3 security. All entries NEW_LAUNCH; classes
  recorded (MEDIUM_RISK — token is never declared "safe"). v1: 15 open monitored (budget 5).
- HONEST LIMITS: true sell-simulation API not freely available (GoPlus is_honeypot documented as
  EVM proxy; SOL sell-sim UNKNOWN); holder/deployer checks UNKNOWN (source refutation stands).
  24h experiment clock ends ≥2026-08-13 08:05Z; sandbox continuity caveat applies (VPS blocker).

### R-26 Wave-8 CONTINUATION: autonomous management + realizable truth + learning (2026-08-12)
- WHAT (Track-B only, all additive, all versioned; v1/v2 tables & cards untouched):
  paper_trading/{schema_v3.sql, realizable.py (PT-REALIZABLE-v1), decision_v3.py (PT-X3-v1),
  lessons.py (§10 post-trade lessons + §11 learning stats), engine_v3.py}; cycle.py now routes
  management through engine_v3 (entries unchanged = PT-BANKROLL-v2 card verbatim);
  reports.py += experiment_equity/render_autonomous_status; strategies.json += PT-REALIZABLE-v1,
  PT-X3-v1 cards (locked pre-result, effective 2026-08-12T08:20Z FORWARD-ONLY for all open v2
  positions — owner-mandated upgrade per continuation directive §12; prior X2 rows unmodified).
- DIRECTIVE→LAW MAPPING (recorded, not silently bent): §5 "PROBABILITY_OF_*" ⇒ recorded as
  NOT_ESTIMABLE (frozen no-probability law stands); momentum/news/etc ⇒ categorical evidence
  classes (IMPROVING/FLAT/DETERIORATING/UNKNOWN; news_risk=UNAVAILABLE_NO_FEED). Gas has no free
  live oracle ⇒ PT-REALIZABLE-v1 MODEL constants per chain, honestly tagged (never live-claimed).
  True sell-simulation API remains absent-free ⇒ GoPlus honeypot stays the documented EVM proxy.
- TESTS: tests/test_paper_trading_v3.py 18/18 — cap math exact (PARTIAL at impact cap), gas-trap
  TOTAL_LOSS exact, UNKNOWN-liquidity⇒NO_DATA-never-TRAP (v2 law mirrored), divergence & decay
  profit-locks, security-flip RISK_EXIT, partial→full settlement with EXACT cash conservation
  (cash_end == start + Σrealized), lesson schema+content, learning counters, no-look-ahead replay
  identical, append-only triggers on all v3 tables. CI: **124/124 green** (106 prior + 18 new).
- NEW STATE: PARTIAL_EXIT appended to §M usage (schema has no CHECK constraint; documented here).
  Decision evidence row per position per cycle (position_decision_event) incl. HOLD — the
  "no hold-by-default inertia" record the directive demands.

### R-27 E-01 t7 + first PT-X3-v1 live cycle (2026-08-12 08:42Z)
- TRACK A (read-only for lab; verified unchanged BY the lab): tokens 295→358, observations
  367→442, lifecycle 800, RESOLVED=0 (wall-clock gate ≥2026-08-14 18:00Z stands).
- CYCLE (evidence reports/paper_cycle_20260812_084219.json + periodic_report_20260812_084219.txt):
  4 new PT-BANKROLL-v2 entries from remaining cash (MOMO eth $1.50 / COMM💯 bsc $1.125 /
  BabyMonkey bsc $0.8438 / TOAD bsc $0.6328 — shrinking per alloc rule min(2,25%·cash);
  4 further qualifiers QUALIFIED_SKIPPED_NO_CASH). Cash $6.00→$1.898438; open alloc $18.101562;
  **conservation exact: 1.898438+18.101562=20.0000**. 11 v2 positions monitored: 11 HOLD,
  0 escalations, 0 exits, 0 trapped; 15 realizable snapshots; v1 legacy: 15 monitored, 0 exits.
- FIRST REALIZABLE-TRUTH EVIDENCE (the directive's core point, live): open DISPLAYED $17.8759 vs
  REALIZABLE $14.5329 ⇒ **$3.34 phantom gap** on $20 in <40min; net equity displayed $19.7743 vs
  realizable $16.4313. Largest divergence = ETHEREUM positions (MODEL gas $0.80 ≈ 40–53% of the
  ticket at $1.5–2 allocations): PRISM/V4 realizable $1.1504 of $1.9751 displayed (58%).
  Pre-registered hypothesis material alive: fixed exit costs vs micro-tickets (H-PT-DRAG).
- LEARNING: 0 closed trades ⇒ no lessons yet (idempotent generator armed); §11 counters live
  (honeypots_avoided=1 from wave-8 rejects; rejected_outcome review: 244 not-yet-reviewable —
  honest). 24h §O report still due ≥2026-08-13 08:05Z.

### R-28 SECURITY EVENT — Telegram credentials pasted in chat; env injection still failing (2026-08-12)
- WHAT: user pasted TWO bot tokens + usernames directly into chat across the last two attempts.
  Per SECURITY law (token lives ONLY in TELEGRAM_BOT_TOKEN env; chat-shared = compromised),
  both tokens are now classed COMPROMISED. They were never echoed into files/logs/git/reports
  by the assistant; no API call was made with them (any call would persist the secret in the
  session transcript — forbidden).
- RUNTIME TRUTH (probed 4×, incl. /proc & secret mounts): TELEGRAM_BOT_TOKEN /
  TELEGRAM_ADMIN_CHAT_ID / TELEGRAM_GROUP_CHAT_ID are NOT injected into the agent execution
  sandbox (no /run/secrets, no /etc/secrets; env empty). Platform secret store is not plumbed
  into this runtime, or saved under a different context, or requires a runtime restart.
- GOVERNANCE NOTE: two distinct bots are implied by the pasted material vs the earlier
  "do NOT create a second bot" rule — single canonical bot must be confirmed by the user.
- REQUIRED USER ACTIONS (none delegable — no platform-config tool exists in this sandbox):
  1) /revoke BOTH tokens in @BotFather NOW, 2) issue one new token for the single canonical bot,
  3) save TELEGRAM_BOT_TOKEN (+ numeric TELEGRAM_ADMIN_CHAT_ID / TELEGRAM_GROUP_CHAT_ID) in the
  platform Secret manager FOR THIS RUNTIME, 4) restart the runtime/session so injection happens
  at boot, 5) then say "run the Telegram test" — my staged sequence (getMe→getChat→one test
  message→delivery→getWebhookInfo) executes in seconds without any value ever being displayed.
- STATUS: Telegram = NOT OPERATIONAL (BLOCKED on secure injection). Telegram API itself is
  reachable from the sandbox (302/404 probes) — the failure is credential delivery only.

### R-29 Cycle t8 + stale-observation monitor anomaly + provider negative-liq growth (2026-08-13 00:59Z)
- CYCLE (reports/paper_cycle_20260813_005513.json): 400 scanned, 56 new decision snapshots,
  0 entries (cash gate: 25%×$1.8984=$0.4746 < $0.50 min ticket), 85 budget defers, 11 monitored,
  0 exits/partials/traps/invalidations; v1 legacy 15 monitored 0 exits. Conservation intact.
- ANOMALY A (observed, NOT repaired): all 11 tracked tokens had NO discovery observation newer
  than 2026-08-12T08:41:48Z (t8 ingested 75 rows but refreshed none of the tracked set); the
  00:55Z management pass therefore decided HOLD on obs aged 16.2–17.65h for ALL positions.
  No exit/escalation fired; every decision row carries obs_ref+obs_ts evidence (staleness is
  transparent in-row, not hidden). R-C3 (v3 trapped/divergence/decay branches lack obs-age gate)
  had ZERO misuse (nothing crossed a threshold) but was one stale print away from it — severity
  of the queued PT-X3-v2 fix note raised from LATENT to ADJACENT. Unchanged verdicts.
- ANOMALY B (observed, NOT repaired): negative liquidity_usd rows grew to 25 (window
  2026-08-11→2026-08-13 incl. t8), of which 15 are MATERIALLY negative (min −50.12 USD) — beyond
  the R-23 float-dust class (≈−1e-14). Entry gate already rejects them as invalid data
  (4 rejections this cycle, evidence preserved). Provider-side data-quality issue; fair policy:
  keep rows, keep rejecting at decision time, count in integrity reports.
- INTEGRITY: 0 error_state rows; dedupe clean; Track-A RO isolation re-verified (paper store has
  no tokens table; A-counters move only via collector); 442→517 obs, 358→430 tokens appended (t8 pass).

### R-30 R-C3 CLOSED via versioned card PT-X3-v2 (owner-authorized, 2026-08-13 ~01:1xZ)
- WHY: R-29 stale-monitor ADJACENT anomaly — 16–17.7h obs reached v3 decisions; zero contamination
  measured, hole structural. User mandated exactly this fix and nothing else.
- WHAT (versioned, forward-only; PT-X3-v1 immutable): decision_v3.py keeps v1 logic byte-frozen
  as decide_v1 (reachable only behind the gate); new decide() = PT-X3-v2: stale() gate first
  (inherited 21600s constant REFERENCED from exit_rules.EXIT_V1, not duplicated) ⇒ stale obs can
  never ground exit/settlement/realizable realization → NO_DATA(STALE_OBSERVATION) or INVALID
  (inherited base law when a hard obligation is unpriceable). Price-INDEPENDENT closes remain:
  CONFIRMED_HONEYPOT/CONFIRMED_UNEXITSABLE ⇒ TOTAL_LOSS with exit_price_observed NULL (no price
  consulted). Belt in engine_v3._settle: refuses stale-priced settlement independently (price
  independent write-offs settle with price NULL, net 0, loss=alloc). risk_escalation market inputs
  suppressed on stale obs (security classifications — provider-fresh — still act). strategies.json
  += PT-X3-v2 card; entry card/cost/realizable models untouched; v1 historical rows keep
  rule_version PT-X3-v1 (queryable provenance forever).
- PROCESS TRANSPARENCY (no silent repair): first test run FAILED 1/10 — my test misstated the
  FROZEN X1 law (stale SL-looking print is no signal at all; INVALID only for un-priceable hard
  obligations). Code behavior was already the frozen-law behavior; the TEST was corrected openly
  (this note is the record). Rerun: 10/10.
- EVIDENCE: tests/test_paper_trading_v32.py — 6h+1s & 16h fault injection; boundary 21600/21601;
  stale-divergence/decay/trap-value blocking; honeypot price-independent close; recovery-after-gap
  settlement carries rule_version PT-X3-v2 with v1-identical math; card immutability pins.
  FULL SUITE: **134/134 green** (exit 0).
- NOTHING else changed: no thresholds/features/entry/risk/decision rules touched; no trades;
  experiment continues under PT-X3-v2 from the same state.

### R-31 W9/EXECUTION-01 — Lane-B P0+P1 built; experiment untouched; P2 audited (2026-08-13)
- TWO-LANE LAW honored: zero edits to Lane-A execution path; architecture package statically
  forbidden from importing experiment packages (test-pinned lane isolation).
- P0 (VERIFIED): docs/mission_v1_1/W9_COGNITIVE_ARCHITECTURE.md + docs/architecture/
  cognitive_principle_matrix.md + config/cognitive_principles.yaml (35 principles, 6 domains;
  falsifiable fields mandatory; source_inspiration = provenance, never authority).
- P1 (VERIFIED): contracts/agent_contract_v1.json (10-field envelope + spec fields + enums incl.
  full hard-verdict set); architecture/{contracts.py,registry.py}; config/agent_registry.yaml
  (24 agents; totals EIGHT exists/13 partial/2 planned/1 missing — evidence-based; EXISTS entries
  linted to real on-disk artifacts); isolated append-only store support data/architecture_registry.sqlite.
- PROCESS TRANSPARENCY: three test failures during build were surfaced and corrected openly —
  (i) my own syntax slip, (ii) test's brace-pattern evidence parsing vs yaml text, (iii) registry
  honesty lint caught a WRONG evidence citation (AG-03 pointed at a nonexistent
  research/evaluate_conjunction.py — function actually lives inside research/baseline_stats.py;
  yaml corrected). No silent repairs; this note is the record.
- P2 AUDIT (no migration): docs/architecture/pg_parity_audit_w9.md — measured drift 33/33 live
  SQLite tables absent from PG DDL; PG 'agent_registry' name collision with W9 registry flagged;
  execution blocked on host (Docker/VPS), $0 constraint.
- TESTS: 134 → **145 green** (+11: matrix completeness/domains, contract rules, no-claim-without-
  evidence envelope law, authority model pins, registry build idempotent+append-only+isolated,
  lane isolation static scan, violation reporting, enum coverage).

### R-32 W10 — architecture readiness + cognitive intelligence AUDIT (read-only; zero config/code changes) (2026-08-13)
- WHY: owner directive W10 — verify whether the W9 cognitive architecture is genuinely capable of
  becoming the specialist-agent system or is documentation-only; red-team it; grade P3 readiness.
  Lane A ordered untouched; no P3/P4 implementation.
- WHAT: two audit docs written — docs/mission_v1_1/W10_ARCHITECTURE_READINESS.md (24-agent audit,
  principle audit, chain/router/contract audits, red-team register F1–F16, P3 verdict
  READY_WITH_BLOCKERS with 6 blockers, Lane-A integrity proof) + docs/architecture/
  cognitive_agent_mapping_w10.md (26 DRAFT-W10 principle derivations; 3 names EXCLUDED as
  UNVERIFIABLE_PROVENANCE — Edward Pearson / LaVaughn Wright / G. R. McKie — because no public
  method corpus is attributable; era-handles derived at era level only; anti-impersonation law held).
- KEY MEASUREMENTS (audit probes W10A-01..18, all read-only/RO): append-only triggers guard ONLY
  the paper store (34 triggers / 17 tables); e01 + ahos_local have ZERO triggers ⇒ CRYPTO-02 text
  and AG-17 evidence overclaim (F1, HIGH, remediation = owner choice: text-truth or approved
  additive migration). Dependency cycle AG-11↔AG-13 measured (F2). Contract has no dependency
  validation (dangling-dep injection PROVEN to pass, W10A-08). Router lacks circuit breaker/health
  persistence/schema+evidence validation (F9). Stale registry counters AG-02/21/23 and principle
  count 35-vs-38 doc drift (F6/F14, LOW). Verified TRUE: 646/646 sha join; conservation
  20.0000000 exact; realizable sweep 17.8759→14.5329; decide_v1 frozen; 11/11 NO_DATA stale
  conversions in latest cycle; only AG-15/16 hold DECIDE (test-pinned); AI floor DETERMINISTIC_ONLY
  live-verified.
- PROCESS TRANSPARENCY: one intermediate audit probe (trigger-coverage tally) mis-aggregated due
  to a bug in MY OWN probe script; corrected by direct re-query and recorded in the report —
  no silent repair of audit work.
- INTEGRITY: 0 Lane-A/Lane-B/config/contract/code changes; 0 trades; snapshot hashes before/after
  identical; tests 145/145 ⇒ 145/145. P3 NOT started (awaiting explicit instruction + F-blockers).

### R-33 W10+W11 build — control plane / AI council / router / registry-extension / P3 (2026-08-13 ~02:2xZ)
- WHY: owner master directives W10(build)+W11 — convert audited architecture into contracts +
  isolated runtime engine; Lane A uninterrupted (t11 landed before build: 569 tok/716 obs/0 resolved/
  0 exits; join re-verified 716/716 probe W11A-01; provider battery re-run PRB-20260813-001..017).
- WHAT: 4 new contracts (control_plane/ai_provider/ai_council/improvement_proposal) + additive
  ops-fields in agent_contract_v1 (old pins intact); architecture/{control_plane,provider_router,
  council}.py (Lane-B isolated); config/control_plane.yaml + ai_provider_registry.yaml;
  cognitive_principles.yaml schema v2 (38→63; CRYPTO-02 honestly downgraded EXISTING→PARTIAL per
  F1 measurement); agent_registry.yaml ops blocks (4-axis operability; F2 cycle repaired AG-13→∅;
  counters refreshed; orchestrated=0 pinned honest); 9 docs incl. F1_RESOLUTION_PLAN +
  orchestration_comparison (Temporal: RECOMMEND-AS-TARGET/DEFER-INSTALL; n8n edge-only);
  docker-compose.target.yml (design-only).
- PROCESS TRANSPARENCY (no silent repair): first W11 test run FAILED 21/46 — three root causes all
  mine: (i) locks INSERT binding count slip; (ii) provider_id required vs mapping-key convention
  (contract note + validator aligned); (iii) council PARTIAL positions semantics + missing
  evidence_conflicts field. Second run 190/191 — remaining failure was MY TEST name mismatch
  ('postgres' vs actual component 'postgresql'), test corrected openly. Final: **191/191 green**
  (145 → 191). Also surfaced earlier this wave: TARGET_UNPROBED enum violation in my own registry
  draft (fixed before first run, noted here for the record) and an initially-mispinned operability
  totals block (caught by my own recount before commit; totals now CI-computed truthful: 21/6/0/15).
- CONTRADICTIONS RESOLVED OPENLY: F1 (claim→measured truth + plan; stores untouched, owner decision),
  F2 (cycle removed; acyclic CI-pinned), F5 (AG-23 = human gateway, never-software law), F6/F14
  (counters/count refreshed), F9 (breaker+health gating implemented), F10/F11 noted in docs.
  W10-vs-W11 Temporal tension resolved: target-adopted, install-deferred (no host; $0 law).
- LANE A: 0 changes to logic/thresholds/cards; 0 trades by architecture; isolation pins extended
  to 3 new modules; hashes before/after identical except the declared Lane-B file set.
- EXPERIMENT: NOT YET VALIDATED (unchanged; 72h closures begin ≥2026-08-14 18:00Z).

### R-34 W12 — F1-S1 conservative execution + Lane-A t12 + runtime architecture v1 + OSS capability intelligence (2026-08-13)
- WHY: owner W12 directives (PART B: F1 → S1 conservative resolution, conditions: append-only
  compatible, zero historical manipulation, additive migration, replay identical, regression
  tests before/after, nothing silent; PART A: standing Lane-A trigger on schedule; PART C/D/L:
  production runtime architecture v1 doc; PART E: OSS capability discovery pipeline spec + first
  read-only audit; PART O: Temporal/PG/Redis/NATS/K8s/live-AI-keys/prod-GitHub stay DESIGN-ONLY
  until VPS+host, E-01 materialization, and the experimental gate report; PART P: execution
  order 1→14).
- WHAT-1 (F1-S1, EXECUTED + VERIFIED): engine/f1_s1_migration.py written with three modes +
  probe sets W12A-F1S1-{BEFORE,DRILL,APPLY,ENFORCE}. Drill on copies ⇒ SAFE (update blocked,
  insert path open, rollback clean). Apply on live stores ⇒ OK with **zero row changes**
  (census before==after incl. sha, data_identical=true): e01_discovery 10 f1s1_guard_* triggers
  on 5 classified history tables (discovery_observations, raw_payloads, gap_register,
  lifecycle_events, gate_summary); ahos_local 2 guards on control_flags; paper store 34 triggers
  /17 tables untouched (CI-pinned regression). Mutable upsert-by-design tables deliberately
  unguarded + documented (blocking them would falsify the pipeline). Live enforcement probed:
  UPDATE aborts, INSERT appends. Pipeline-safety proof: t12 cycle completed WITH guards
  (research/experiments/e01_collection_t12_20260813.json; reports/paper_cycle_20260813_025748.json;
  638 tokens / 791 observations appended, 0 resolved / 0 exits unchanged, conservation
  20.0000000 exact, latest mgmt decisions 11/11 NO_DATA(STALE_OBSERVATION) — F12 freshness gap
  inert-but-safe by PT-X3-v2 design, owner-open F12 ticket). Rollback = script rollback mode,
  drill-proven (drops the 12 named triggers).
- WHAT-2 (claims repaired to measured truth, no silent fix): CRYPTO-02 restored EXISTING with
  measured wording ("S1" in ahos_application, CI-pinned); AG-17 promoted PARTIAL→EXISTS with
  evidence text citing drill/apply reports + probe refs; matrix/fabric/dependency-graph/registry
  counters refreshed — 25 agents (9 EXISTS/12 PARTIAL/3 PLANNED/1 MISSING), principles
  EXISTING 24/PARTIAL 20/DEFINED 19 (63), boot classes 10/9/6/0, operability 21/6/0/15 unchanged
  (machine-recomputed, test-pinned).
- WHAT-3 (PART C/D/L): docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md — production topology
  per owner diagram, per-component statuses (IMPLEMENTED/TESTED/DESIGNED/BLOCKED/UNVERIFIED),
  single-start contract summary, observability stack (interim run-ledger+probe reports
  IMPLEMENTED; OTel/Prometheus/Grafana DESIGN), rollback paths per change class. F1 plan doc now
  carries EXECUTION ADDENDUM §7 (S1 done via path (i); S2–S5 DESIGN-ONLY, host-gated).
- WHAT-4 (PART E): AG-25 OSS Capability Intelligence registered (PLANNED/ADVISORY;
  DISCOVERY→ANALYSIS→PROPOSAL only, no integration right; ImprovementProposal → human gate).
  Spec docs/architecture/OSS_CAPABILITY_DISCOVERY.md (15-stage pipeline, 3-tier evidence law).
  First read-only audit executed (probe W12A-OSS-1, GitHub public API metadata only):
  temporalio/sdk-python (MIT, active) ⇒ NO_INTEGRATION (host-gated, aligned with target
  decision); promptfoo/promptfoo (MIT, TypeScript) ⇒ CANDIDATE_HELD_UNVERIFIED; crewAI (MIT,
  Python) ⇒ CANDIDATE_HELD_UNVERIFIED. reports/oss_capability_audit_1.json.
- PROCESS TRANSPARENCY (openly logged): tests/test_f1_s1.py was written test-first — the text
  pin test_registry_and_matrix_text_now_measured FAILED as designed until registry + matrix
  wording were updated to the measured truth (recorded here, not hidden). One earlier wording
  slip in my own F1-S1 report header ("trigger addition on Lane-A evidence stores") was
  corrected in this wave's docs to "governance-touching ... owner authorization" phrasing.
  Compaction note: exact sub-letter wording of W12 parts F/I/J/K/M/N was not preserved in the
  working context — the final report marks those UNVERIFIED rather than guessing.
- LANES: Lane A logic/thresholds/cards untouched (0 changes; guards are DDL-only and
  append-compatible — append paths verified live). Lane B work isolated under
  architecture/, engine/, config/, contracts/, docs/. Architecture NEVER issued trades.
- TESTS: 191 → **198 green** (+7 test_f1_s1: drill-safe-on-copies, apply idempotent + rollback
  clean, mutable tables unblocked, live guard census exact-match, apply report zero-data-change,
  paper-store 34-trigger regression, registry/matrix measured-text pin).
- EXPERIMENT STATUS: NOT YET VALIDATED (unchanged — 0 resolved / 0 closed; first 72h closures
  ≥2026-08-14 18:00Z ⇒ then discovery.materialize → cohort report → baseline comparison →
  sufficiency audit per PART P §3–4). §O 24h report clock-gated (≥2026-08-13 08:05Z).
- BLOCKERS UNCHANGED (user): Telegram token revocation (R-28), VPS/Docker host, AI provider keys.

### R-35 W12 re-issue closure — Lane-A t13 + PART J/K/N + canonical alignment (2026-08-13 ~03:3xZ)
- WHY: owner re-issued the full W12 directive verbatim; letters previously marked UNVERIFIED in
  the interim report (I/J/K/M/N wording lost to context compaction) are now closed with real
  work. PART A trigger law: each user trigger runs the standing cycle ⇒ t13.
- WHAT-1 (Lane A t13, PART A): discovery.collect (68 new tokens, 0 errors, all sources OK —
  fresh probe battery PRB-20260813-001..017 re-run: same posture — LlamaRPC 521 / Helius 401 /
  CryptoPanic 404 DOWN, cloudflare/ankr DEGRADED) → paper_trading.cycle (11/11
  NO_DATA(STALE_OBSERVATION) per stale-observation law; 0 closed; cash $1.8984375 unchanged;
  conservation holds; entry gate still QUALIFIED_SKIPPED_NO_CASH by design) → pal_probe evidence
  (reports/pal_probe_20260813_*_sandbox.json). F1-S1 guards did not interfere (INSERT paths open).
  Files: research/experiments/e01_collection_t13_20260813.json · reports/paper_cycle_20260813_032731.json.
- WHAT-2 (PART J): engine/agent_matrix_v2.py — deterministic generator (byte-identical, no
  clock) producing docs/architecture/agent_matrix_v2.md: all 25 agents × the 16 mandated fields
  (identity/version/status/capabilities/owner/dependencies/inputs/outputs/authority/
  evidence_requirements/probes/health/circuit/failure_mode/fallback/runtime/cadence). Typed
  payload-level IO is honestly NOT in the registry ⇒ shown as DEFINED marker with F3 queue
  reference (no invented IO; CI-pinned). tests/test_agent_matrix_v2.py (5 tests).
- WHAT-3 (PART K): docs/architecture/SELF_EVOLUTION_LOOP.md — the 15-stage owner loop mapped
  onto improvement_proposal_v1 (contract law: AI never self-approves/never touches Lane A/never
  promotes itself; AI never approver; governance-touching ⇒ forced human).
- WHAT-4 (PART C/D/L/N alignment): runtime v1 doc now carries the owner-canonical PART C diagram
  verbatim (§1), the PART D boot chain verbatim (§3), the full PART L enumeration with interim
  vs target mapping (§4), and the PART N master loop registered as §7 with node→component
  statuses and the governing property (self-reinforcing in OBSERVATION only).
- WHAT-5 (PART I, now attributable): cognitive matrix schema v2 already implements the mandated
  chain thinker→verified principle→engineering capability→agent responsibility→probe→test→
  evidence (63 rows, lint-pinned; no-persona test-pinned; UNVERIFIED exclusions retained).
- PROCESS TRANSPARENCY: one slip of mine caught pre-commit — a non-English token ("仕様") landed
  in the PART K doc draft; corrected openly before any test ran; recorded here per law 13.
- TESTS: 198 → **203 green** (+5 agent-matrix pins). Lane A logic files: zero changes.
- EXPERIMENT: NOT YET VALIDATED (unchanged). §O 24h report clock-gated ≥08-13 08:05Z;
  materialization + cohort + baseline + sufficiency audit at ≥2026-08-14 18:00Z.

### R-36 W13 — MASTER ROADMAP audit-first wave: reality reconciliation + t13/t14 + OSS Tier-1 tool versioned (2026-08-13 ~04:0xZ)
- WHY: owner issued MASTER ROADMAP/OPERATING DOCTRINE (§1–§37) + CONTINUATION directive:
  AUDIT FIRST → reality map → gap analysis → priority plan → execute only what is truly ready.
  Workspace/tests/evidence = source of truth; the W12 report text treated as reference only.
- REALITY RECONCILIATION (rule 10): every W12-vs-workspace drift resolved as TEMPORAL ADVANCE,
  not contradiction — tokens 569(F1-S1 apply)→638(t12)→686(t13)→**722(t14)**; observations
  716→791→859→**924**; resolved **0** unchanged; cash $1.8984375 unchanged; v2 open 11 / exits 0 /
  v1 monitored 15 unchanged; triggers 34/10/2 live; suite 203/203 green at wave start.
  Full table in docs/mission_v1_1/W13_REALITY_AUDIT.md §0.
- WHAT-1 (executed, PART A standing law): t13 (68 ingested, 0 errors) + t14 (65 ingested,
  0 errors) cycles with per-cycle evidence (e01_collection_t1{3,4}_20260813.json,
  paper_cycle_20260813_{032731,034259}.json, pal_probe_20260813_032824_sandbox.json);
  both cycles: 11/11 NO_DATA(STALE_OBSERVATION) — stale-law firing correctly; no fake pricing.
- WHAT-2 (executed, §32 audit): docs/mission_v1_1/W13_REALITY_AUDIT.md — all 20 mandated
  sections answered from measurement (architecture/agents/files=281/tests=203/experiment/
  blockers/host/deps/GitHub=8 candidates/AI all-need-key/missing/dupes/deprecated/security/
  self-heal/self-learn/single-start/observability/iran-cost/next-actions). Gaps surfaced
  honestly: G-SCHED (no autonomous scheduler without host — cycles fire per trigger),
  AG-01 MISSING, typed-IO v2 (F3), live self-heal repair chain absent, OTel target-only.
- WHAT-3 (executed, PART E/§12): second Tier-1 OSS audit batch → reports/oss_capability_audit_2.json
  (probe W12A-OSS-2; apscheduler MIT · prometheus client_python Apache-2.0 · opentelemetry-python
  Apache-2.0 · tenacity Apache-2.0 · prefect Apache-2.0 ⇒ ALL CANDIDATE_HELD_UNVERIFIED).
- WHAT-4 (executed, P2-ready per PART-35): engine/oss_audit.py — versioned deterministic
  Tier-1 executor (AG-25 duties #1/#10; never assigns final verdict; API error ⇒ UNVERIFIED
  record, never fabrication; archived ⇒ REJECT; rate cap 20/run; network-free testability via
  injected fetcher) + tests/test_oss_audit.py (5).
- PROCESS TRANSPARENCY: one syntax error of mine in an ad-hoc ledger probe (mismatched paren) —
  fixed and re-run immediately, no repo impact; recorded here per no-silent-repair discipline.
  New tests green on first run; one numeric slip in a draft of THIS entry (an off-by text "219"
  for the suite total) was caught and corrected to the measured 208 before commit.
- TESTS: 203 → **208 green** (17.8s→~18s). Manifest: /home/user/ahos_snap_w13_after.txt.
- EXPERIMENT: NOT YET VALIDATED (0 resolved / 0 closed; gates: §O ≥08-13 08:05Z clock-pending;
  E-01 materialization ≥08-14 18:00Z). DESIGN-ONLY freeze intact: no Docker/PG/Temporal/Redis/
  NATS/K8s/live-AI/prod-GitHub — nothing installed, zero external side effects beyond free
  read-only API GETs (GitHub metadata, provider probes).

### R-37 W13b — control-plane soak + fault-injection battery (PART P #13 in-repo executable slice) (2026-08-13 ~04:2xZ)
- WHY: reference order says §O/materialization are CLOCK-GATED; the highest-value READY action
  from the W13 plan (P1) was the in-repo soak/fault-injection battery for the Python control
  plane. Lane A untouched; Lane B additive-only.
- WHAT: tests/test_control_plane_soak.py (8 tests, deterministic injected clock/probers):
  exhaustive single-fault property over the REAL config (per-component boot-class semantics);
  seed-pinned 64-combo multi-fault fuzz; 150-op interleaved soak with ledger invariants;
  crash-injection at state_verify + resume; ledger-unavailable fail-fast; 25-attempt lock
  flood; recovery history non-rewrite; prober-exception honesty. Runtime v1 §3 annex updated.
- PROCESS TRANSPARENCY (no silent repair — full failure log): first run FAILED 5/8. Root
  causes, all in MY tests, none in the engine:
  (i) shared in-memory-per-file ledger + frozen clock across parametrized iterations made
  attempts collide into one run stream (harness isolation bug — fixed with per-iteration
  ledger files; engine behavior was correct in direct reproduction);
  (ii) getattr-dispatch bug in the soak loop (test-only);
  (iii) crash target phase name wrong in my test ('config_verification' vs real
  'state_verify' — read from cfg instead of assuming);
  (iv) lock-flood premise wrong: a COMPLETED start releases its lock by design, so an 'active
  holder' must be injected as a locks row (fixed; flood then behaved: 25/25 refused, exactly
  one STALE_LOCK_STOLEN after TTL);
  (v) run-id derives from (idempotency-key, ts) — with my frozen clock the post-HALT attempt
  reused the same id and appended to the old run stream (append-only held; no rewrite). Fixed
  by advancing the injected clock + asserting distinct run ids; recorded as a documented
  design boundary in AHOS_RUNTIME_ARCHITECTURE_v1.md §3 (production clock advances).
  Engine code changes: ZERO. Test-file-side fixes only, all itemized above.
- RESULT: 208 → **216 green** (25.4s). Evidence of fault tolerance now test-proven at the
  control-plane layer (still NOT a production soak claim — no host; PART O law intact).
- EXPERIMENT: NOT YET VALIDATED (unchanged; 722 tok / 924 obs / 0 resolved / 0 closed).

### R-38 W13c — doctrine re-issue: verify-only gate check + t16 consciously skipped + F12 OWNER MEMO with new measured evidence (2026-08-13 ~04:2xZ)
- WHY: MASTER ROADMAP doctrine re-issued (identical text). Per audit-first law: workspace
  re-verified (suite 216/216, counters 762/987/0, triggers 34/10/2, cash unchanged — zero drift
  since W13b) → §O still CLOCK-GATED (≥08:05Z) → materialization CLOCK-GATED (≥08-14 18:00Z).
- WHAT-1 (deliberate non-action, disclosed): t16 standing cycle NOT fired — t15 ran 04:01Z, this
  session verify at 04:05Z; a 4-minute re-fire adds near-duplicate observation rows and degrades
  cohort sampling hygiene (capability-per-complexity law). Next session resumes cadence (t16).
  Recorded openly here; no data touched.
- WHAT-2 (major measured finding, NEW evidence): F12 deepened from "11 tracked tokens not
  refreshed" to cohort-wide measured starvation: only 1/762 tokens has a ≥12h observation span;
  222 tokens' latest obs >24h old; gap_register honestly records 826 missed scheduled snapshots
  (s+15m/1h/4h/12h); both outcomes.py (Track A labels) and PT-X3-v2 (Track B exits) read stored
  series ONLY. Root architecture cause: no autonomous scheduler (G-SCHED) + collector is
  new-listings-only. Consequence, stated truthfully in advance: 08-14 materialization will
  resolve states on time but horizon labels will be thin/none; sufficiency audit should read
  INSUFFICIENT_DATA for meaningful cells; ≥200 "resolved" by state-count alone is flagged as
  potentially hollow unless interpreted with outcome coverage.
- WHAT-3 (owner artifact): docs/mission_v1_1/F12_DECISION_MEMO.md — options O1 accept / O2
  versioned append-only observation-poller amendment (with mandatory disclosure protocol) /
  O3 next-cohort-only; measured consequences; permanent-loss note for past windows; no
  execution without explicit owner order (Lane A frozen).
- PROCESS TRANSPARENCY: two probe-script slips of mine this wave (wrong column t.id; and a
  deprecated utcfromtimestamp warning) — corrected on re-run, zero repo impact.
- TESTS: 216/216 green before AND after (docs/ledger-only wave). EXPERIMENT: NOT YET VALIDATED.

### R-39 W13d — E-01 gate-day protocol PRE-REGISTERED before any outcome exists (2026-08-13 04:2xZ)
- WHY: anti-post-result-tuning law (doctrine §7/§23; MASTER CONTRACT §17 ADR): the judgment
  rules for the 2026-08-14 18:00Z gate must be frozen BEFORE the gate's numbers are known.
  This is the primary ready action of the wave (§20 STEP 7); all clock gates remain gated.
- WHAT: docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md with binding rules R1..R8 — R1 resolved=
  RESOLVED **with** 72h-outcome coverage (dual-count, hollow-coverage law); R2 F12 starvation
  context + cohort segmentation; R3 INSUFFICIENT_DATA is lawful; R4 baseline stays per
  G_BASELINE_LIFT_DESIGN + multiplicity budget; R5 Track B gate is arithmetic (0 closed = NOT
  MET); R6 deviations recorded as evidence; R7 verdict alphabet {SUFFICIENT_FOR_EVALUATION /
  INSUFFICIENT_DATA / INVALID_PROTOCOL}; R8 artifact chain.
- PRE-REGISTRATION PROOF: sha256 of the protocol at registration time:
  16b86b86e89392c3f84d82a1c2c6d87534fea988c4dff5a1454fcc137a168101
  Any later change requires E01_GATE_PROTOCOL_v2 + a register entry stating the diff reason.
- CI: tests/test_e01_gate_protocol.py pins the file hash + R1..R8 sections (sha-bearing edit =
  deliberate versioned act).
- PROCESS: t16 cycle again intentionally not fired 13 min after t15 (sampling hygiene, R-38
  policy stands; next session resumes cadence). Suite re-verified this wave.
- TESTS: 216 → **219 green**. EXPERIMENT: NOT YET VALIDATED (unchanged).

### R-40 W14 — F12-O2 EXECUTED: supplemental observation poller live + coverage guardrail (2026-08-13 04:3xZ)
- WHY (owner directive): O2 approved with strict evidence boundaries — poller may only improve
  FUTURE observation coverage; 9 immutables listed by owner; 13-step build order mandated.
- THE 13 STEPS, AS EXECUTED (each evidenced): (1-2) collector architecture inspected in code —
  exact failure reason PROVEN: lifecycle.due_snapshots/sweep existed but had NO fetch-side
  consumer; collector ingests new listings only; (3) existing components repaired-by-completing
  the loop — no duplicated fetch/normalize code (collect.normalize_dex_pairs + pal client +
  obs.record_observation + lifecycle.reused); (4) smallest intervention = ONE new file
  (discovery/observe_active.py), ZERO edits to existing Lane-A files; (5) tests BEFORE behavior
  (tests/test_observe_active.py written first, initially red); (6) failure modes: provider_down/
  no_valid_price/wrong_token/unsupported_provider/mid-run-crash — each recorded EXPLICITLY as
  error_state rows + report failures[]; rollback = stop invoking (no deletions ever; its rows
  are real future observations = valid POST_FIX evidence); (7) isolation run on LIVE COPY with
  real network: 6 recorded / 14 failures (reports/observe_active_isolation_20260813.json);
  (8) full regression 219 → 234 green; (9) red-team set: stale-as-fresh substitution structurally
  impossible (retrieved_ts == run-now always, pinned), crash-resume duplicate-safety (+changes()
  based recording), gap_register never touched, wrong-pair never cross-wired, census invariants;
  (10-11) Lane-A integrity + historical census: tokens/pairs/lifecycle_events/gap_register/
  outcome_label sha-IDENTICAL pre⇒post activation; obs 987→1027 (pure appends, all ts ≥
  activation 1786595433.489443); raw 224→239; (12) thresholds/cards/decision files byte-identical
  (manifest diff shows only additive files); (13) FUTURE observations proven produced: 14 real
  priced rows + 26 explicit failure rows with true retrieved_ts at 2026-08-13T04:30Z
  (reports/observe_active_20260813_activation.json).
- COHORT SEPARATION (owner-mandated): PRE_FIX = retrieved_ts < activation_ts (byte-verified: all
  987 pre rows predate activation); POST_FIX = ≥ activation. Disclosure fields for the gate
  validation report (owner list) recorded HERE as the binding addendum to E01_GATE_PROTOCOL
  artifacts: collector version, poller version (observe_active:v1), activation timestamp,
  pre-fix coverage, post-fix coverage, missing observations, stale observations, provider
  failures, collection failures, coverage by horizon — never merged into one misleading metric.
- LANE-B LESSON ENFORCED (OBSERVATION COVERAGE = first-class invariant): engine/coverage_audit.py
  computes the 5-block bundle (collection health + freshness + horizon coverage + gap detection +
  recovery status) with a frozen HEALTHY/DEGRADED/STARVING classifier; "healthy progress via
  token/resolved counts only" is now structurally impossible to publish (tests/test_coverage_audit.py).
  Live activation verdict: DEGRADED (fresh share 0.727; gaps 826 total / 580 in 24h — expected to
  FALL as poller cadence serves due slots; horizon coverage honestly NULL at 0 resolved).
- NO SILENT REPAIR — full disclosure: WHAT failed: cohort-wide observation starvation (only 1/762
  tokens ≥12h span; 826 missed snapshots); WHY: no fetch-side consumer of the existing schedule +
  no autonomous scheduler (G-SCHED); HOW detected: W13c live RO queries + gap_register counts;
  WHY existing components did not recover: gap recording was designed to RECORD, never to FETCH;
  WHY O2: restores the protocol's own data requirement without touching any frozen artifact;
  WHAT changed: +observe_active.py, +2 test files, +coverage_audit.py, activation run;
  WHAT NOT changed: every existing Lane-A file, all thresholds/cards/definitions, all history;
  TESTS added: 15 (11 poller + 4 guardrail) + 3 pre-registered hash pins from W13d retained;
  EVIDENCE of recovery: activation report + isolation report + coverage_audit activation JSON +
  census diffs; RISKS remaining: poller cadence is trigger-driven (no daemon without host — the
  24h/48h/72h slots of TODAY's cohorts will only be served if sessions fire roughly daily);
  DexScreener coverage of ancient dead pools is thin (no_valid_price rows are the honest answer);
  classifier thresholds are v1-frozen — tuning only via versioned change.
- CYCLES: no separate collect fired this wave (t15 stood 30 min old at activation — sampling
  hygiene); poller ran as the scheduled-snapshot servant it is.
- TESTS: 219 → **234 green**. EXPERIMENT: NOT YET VALIDATED (0 resolved / 0 closed unchanged).
  F12 status: **MITIGATED** (not "solved forever") — monitoring loop = coverage_audit.

### R-41 W14-close + t17 standing cycle — poller limitation MEASURED live; s+24h salvage windows mapped (2026-08-13 04:39–05:1xZ)
- WHY (standing law): per-trigger Lane-A cycle (collect → observe_active → paper cycle → probes →
  evidence registration) + W14 deferred closure (KMAP, manifest). Gap since t15 collect: ~38 min —
  disclosed; not a near-instant re-fire; t16 skip policy (R-38/39) unchanged.
- CYCLE FACTS (t17, live, all reports sha-registered on disk):
  collect: 67 ingested / 0 errors (tokens table 762→818 net; GT base page OK, dex_profiles OK).
  poller run #2: due_total 751 → attempted 40 → recorded 14 priced + 26 explicit failure rows
  (no_valid_price/provider_unavailable) — reports/observe_active_20260813_t17.json.
  paper cycle: 400 scanned, 43 snapshot_v2, 10 security_calls, 0 entries (all rejections =
  liquidity < $5k floor or insufficient security coverage; 8 qualified skipped=no_cash),
  11 v2 monitored ⇒ 11 decisions NO_DATA, 0 exits/partials/trapped, cash_state CASH_AVAILABLE,
  scams_avoided_validated 4 — reports/paper_cycle_20260813_043935.json.
  probes PRB-20260813: 17 total, 12 OK / 5 down-or-degraded (llamarpc 521, helius-public 401,
  cryptopanic 404, cloudflare + ankr degraded) — identical known set, provider reality stable.
- MEASURED FINDING (not assumed — live RO queries + report diffs):
  F-POLLER-HEAD: poller selection = ORDER BY first_seen_ts × cap 40 ⇒ activation & t17 attempted
  the IDENTICAL 40 tokens (overlap 40/40; recorded-overlap 14/14). Old head slots' tolerance
  windows have passed ⇒ those slots are permanently uncoverable by new obs ⇒ head tokens stay
  due ⇒ queue re-attempts the same head every run. Drain mechanism: head reaches RESOLVED at
  t0+72h only (observation_state: OBSERVING 818, DEAD 0, RESOLVED 0 at 04:46Z).
  CONSEQUENCE (PT-STARVATION-LINK): all 11 open PT v2 positions rank 235–321 in the due order ⇒
  unreached by poller ⇒ their latest obs stay 20.0–21.4h old ⇒ decision_v3's 6h stale law keeps
  returning NO_DATA. This is why the fresh poller obs did NOT reach the paper engine this cycle.
  KNOWN REMAINING SALVAGE: s+24h slots of the 11 with ±30min tolerance (frozen
  SNAPSHOT_SCHEDULE): 07:15Z-entry cohort ×7 needs obs within 2026-08-13T06:45:57–07:45:57Z;
  08:41Z-entry cohort ×4 needs 08:11:48–09:11:48Z. A fresh obs inside a window = lawful slot
  coverage (REAL future observation, not backfill — obs happens now for a slot due now);
  any fresh obs also un-stales PT management regardless of slot.
- DECISION DISCIPLINE (freeze honored): NO code/param change shipped. Poller is Lane-A
  experiment surface (built under owner order F12-O2) ⇒ behavior/selection changes need owner.
  Options written for owner decision: O2a (select tokens with COVERABLE due slots — skip slots
  whose tolerance window has passed; those stays honestly registered as missed in gap_register;
  9 immutables untouched), O2b (one windowed ops run with larger --max-tokens ≈330 inside a
  salvage window — crude, ~4 min of rate-limited calls, also re-attempts 234 dead head slots),
  O0 (accept the gaps; they register honestly; PT NO_DATA streak continues to horizon 08-15).
  Project-Lead recommendation: O2a design-ready, zero-risk to history, highest coverage yield.
- COVERAGE GUARDRAIL TREND (engine/coverage_audit.py, frozen v1 classifier):
  activation 04:33Z: DEGRADED fresh-share 0.727, gaps 826/580; t17 04:46Z: DEGRADED fresh-share
  0.746, gaps 826/580 static (sweeps register gaps, not the poller), horizon coverage NULL @ 0
  resolved (honest). recovery_status now tracks poller reports (2 runs, last 14 rec/26 fail).
  F12 status: MITIGATED, monitored — trajectory EARLY; verdict must improve over cadence.
- W14 CLOSURE: KNOWLEDGE_MAP W14 section written; sha-manifest ahos_snap_w14_after.txt
  reconciled vs w13d (added = poller+guardrail+2 test files+cycle/probe reports+e01 collect
  report; changed = REGISTER, PHASE_STATE, F12 memo addendum, 2 live stores, .pytest_cache
  nodeids; removed = none; EVERY Lane-A logic file hash-identical w13d⇒w14).
- §O 24h PT REPORT: clock-gated ≥2026-08-13 08:05Z — checked at session start 04:37Z: NOT DUE.
  When due it must carry: 11/11 NO_DATA streak + this entry's root cause + 0 exits + cash
  conservation + cost reconciliation n/a (0 closed) + guard trend — per PT-X3 §O contract.
- TESTS: 234/234 re-verified green post-cycle (25.6s). EXPERIMENT: NOT YET VALIDATED
  (0 resolved / 0 closed; 818 tracked; gate 2026-08-14 18:00Z per pre-registered protocol).

### R-42 W15-0 — MASTER DIRECTIVE v1 (PERMANENT OPERATING STATUS) codified, hash-pinned, CI-enforced (2026-08-13 04:55Z)
- WHY (owner act): owner ratified the PERMANENT OPERATING STATUS Master Directive — doctrine is
  permanent, versioned, supersedes only via newer version; never silently change/weaken; 12-step
  wave-opening protocol mandatory. Conversational doctrine alone is not tamper-evident ⇒ the
  FIRST duty under the directive is to make it structurally enforceable.
- MASTER VERSION STATE (verified this wave, step 2): MASTER_DIRECTIVE_v1 ACTIVE; Master Operating
  Contract ACTIVE (reinforced, not superseded — no rule weakened); E01_GATE_PROTOCOL_v1 ACTIVE
  (sha re-verified 16b86b86e89392c3f84d82a1c2c6d87534fea988c4dff5a1454fcc137a168101).
- ARTIFACTS: docs/canonical/MASTER_DIRECTIVE_v1.md (verbatim owner text + registration wrapper;
  IMMUTABLE-per-version law in-file) · docs/canonical/master_directive_registry.json (schema 1:
  exactly one ACTIVE = highest version) · tests/test_master_directive.py (5 governance pins:
  v1 sha immutability · required invariants + ordered 12-step protocol in every version ·
  registry shape · no orphan doctrine files · every version's sha256 must appear in this register).
- MASTER_DIRECTIVE_v1 sha256: e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79
- CHANGE LAW (structural): any future MASTER_DIRECTIVE_v2 requires (a) new immutable file,
  (b) registry transition v1→SUPERSEDED / v2→ACTIVE, (c) R-series entry carrying both hashes —
  else CI fails. Silent doctrine change is now a test failure, not merely a review failure.
- RED TEAM of the mechanism (step 9, disclosed honestly): CI pins cannot judge SEMANTIC weakening
  of future doctrine text — that remains owner-review + Red-Team duty per transition (stated in
  test docstring-adjacent law); register-sha presence proves trace, not intent. Acceptable: the
  law now forces every transition into the open, which is precisely what the directive demands.
- 12-STEP VERIFICATION FACTS (steps 1–5, this wave's opening): workspace 309/309 sha-identical vs
  w14-close manifest; experiment 818 tok / 1134 obs / 0 resolved / 0 labels / PT 11 open / 0
  exits / cash $1.8984375 conserved; governance E01 hash ✓, freeze intact (Lane-A logic inside
  the 309-verified set, zero drift); open risks unchanged (R-28 telegram, VPS, AI keys — USER;
  F12 MITIGATED-monitored; O2a/O2b/O0 owner-pending; G-SCHED; §O gate ≥08:05Z; E-01 gate
  2026-08-14 18:00Z).
- ORDERING DISCLOSURE (tests-before-behavior honored in substance): directive + registry +
  tests written; register entry then completed BEFORE the first full-suite run; any initial
  red would have been the registration-presence pin by design (docs land before CI can pass).
- TESTS: 234 → 239 expected green (5 new governance pins). EXPERIMENT: NOT YET VALIDATED
  (unchanged — no Lane-A touch this wave, by law).

### R-43 W15b — F12-O2a EXECUTED: coverage-aware observation scheduler deployed (observe_active:v2) (2026-08-13 05:0x–05:4xZ)
- WHY (owner directive): O2a approved as a VERSIONED Observation-Layer amendment — build/fix a
  COVERAGE-AWARE OBSERVATION SCHEDULER targeting only legal, still-salvageable slots; selection
  must stop being ORDER BY first_seen + LIMIT; 9 slot/operational states mandatory
  (COVERABLE/WINDOW_OPEN/WINDOW_CLOSED/ALREADY_OBSERVED/STALE/MISSED/UNRECOVERABLE/
  PROVIDER_FAILED/RATE_LIMITED); 12 mandated tests; tests BEFORE code; F12 =
  MITIGATION DEPLOYED (never "SOLVED").
- PRE-CODE AUDIT (facts): defect root pinned in code — lifecycle.due_snapshots stays non-empty
  for windows CLOSED past tolerance while v1 _due_tokens selected oldest-first over that set;
  PAL rate-limit surface = envelope error_state.kind=="rate_starved" (bucket); gap rows are
  written ONLY by lifecycle.sweep via materialize (poller never touches — pinned by test);
  coverage_audit reads report keys ts/recorded/failures/version only (v2 keeps them);
  last_obs_ts is success-driven (failures don't move it) ⇒ v2 cooldown tightened to ANY-row
  basis (anti retry-storm, disclosed).
- RED-STATE EVIDENCE (tests-first): 15 scheduler tests ran against the v1 engine ⇒ 7 red,
  each mapped 1:1 to the documented defect (starvation, repeated-head, expired-window attempts,
  same-instant re-attempt, no rate abort, over-resume, fairness rotation collapse).
- BUILD: NEW discovery/observation_scheduler.py (pure, clock-injected, read-only; mirrors the
  FROZEN SNAPSHOT_SCHEDULE + coverage rule; property test proves classification ≡
  lifecycle.due_snapshots over 200 seeded random cases) + observe_active.py → v2 (scheduler
  selection; tiers ① near-expiry open windows (close−now ≤ 1800s) ② injected tracked positions
  with legal open window (RO loader on paper store; missing store ⇒ degrade+note) ③ others;
  within tier: soonest close, then cohort age, then token_id; RATE_LIMITED ⇒ explicit row +
  clean abort (no storm); report schema v2 with full by_state census + per-attempt tier/slots).
- DISCLOSED TEST EDITS (laws preserved): in tests/test_observe_active.py — dry-run probe moved
  NOW+1000 → NOW+240 (old ts sat after window close; that is the ordered behavior) and the
  stale-substitution RT runs re-pinned to legal s+1h/s+4h/s+12h windows (same law, stronger
  form). v1 byte archives (rollback path): docs/archive/observe_active_v1_src_20260813.txt
  sha a463339eb7c0f5ef2182f324363fdcf4dec92841765bc3ff48375e75febe7228 ·
  docs/archive/test_observe_active_v1_src_20260813.txt sha
  0c62b75fd3bbbbfb9f3730d2f8849063e1cda35ddb2a891d15b6e4ea72836af6. Rollback = restore both
  files from archive; suite returns to v1-green; scheduler module/tests remain inert-additive.
- TESTS: 239 → **254 green** (12 owner-mandated + 3 clarifying edges: dead-token-open-window
  eligibility, classification-vs-lifecycle property, genericity pin (scheduler source carries
  no paper_trading coupling; tracked is INJECTED)).
- MANIFEST + LANE-A INTEGRITY (sha-diff vs w15): ADDED = scheduler + test + 2 archives +
  7 evidence reports; CHANGED = observe_active.py + its test file + 2 live stores + .pytest
  cache; REMOVED = none; EVERY other Lane-A logic/config file byte-identical (now also pinned
  by test_lane_a_frozen_files_hash_integrity, ≥18 pins). E01 protocol hash unchanged.
- LIVE EXECUTION (real runs only on legal windows — owner condition honored; measured):
  dry-run probe: eligible_total 160 open-window tokens (tier-1 near-expiry s+4h head), the 11
  PT positions correctly NOT selected (their windows open 06:45:57Z / 08:11:48Z only).
  Real runs: 160 attempted → 156 recorded + 4 explicit failures (2 no_valid_price/…), then
  eligible_total → **0 with ZERO idle re-attempts** (reports/observe_active_20260813_o2a_*.json
  1..5): the repeated-head pathology is DEAD on live data. Clock-injected probe (read-only):
  at 06:50Z ⇒ 7/11 PT tokens surface tier-2 slot s+24h; at 08:30Z ⇒ 4/11. Generic, not hardcoded.
- BEFORE vs AFTER (owner-mandated numeric comparison):
  freshness ratio: 0.7457 → 0.7457 (share unchanged — those tokens already had in-24h obs;
  median latest-obs age 3.69h → 2.46h; the ratio moves as new cohorts arrive / old resolve)
  open-window coverage: 0 served windows/run (v1 attempted closed-slot head only) → 160/160
    identified, 156 covered, 4 explicit failures (97.5% of eligible attempts landed)
  missed slots: 826 total / 580 last-24h → unchanged (sweeps register at materialize by design;
    the 156 slot-coverages landed BEFORE window close ⇒ they can never become gaps)
  queue overlap (attempted sets across consecutive runs): 40/40 identical → pairwise disjoint
  starvation: 760-token due universe with PT unreachable at rank 235-321 → eligible queue 160→0
    drained by coverage in 5 runs; v1 would still be re-chewing the same dead 40
  recoverable slots: unserved by v1 → 160 identified / 156 served this wave
  unrecoverable slots: slot census MISSED 2453 / UNRECOVERABLE 0 (DEAD=0 until materialize
    sweep; terminology: MISSED = closed-uncoverable alive, UNRECOVERABLE = same while DEAD)
  provider failures: 26/40 attempts (65% — v1 selection waste on dead pools) → 4/160 (2.5%)
  observation duplicates: 0 → 0 (dedup law held in both versions)
  PT NO_DATA count: 11/11 → 11/11 (HONEST: relief lands when the legal s+24h windows open
    06:45:57Z/08:11:48Z today; machinery now PROVEN to catch them — no fabricated claims)
- F12 STATUS (owner-mandated wording): **MITIGATION DEPLOYED**. Promotion to MITIGATION
  VERIFIED requires evidence from several real cycles (incl. at least one PT window landing).
  Never SOLVED. Monitoring = coverage_audit + scheduler census each session.
- STOP-CONDITION audit (owner): experiment definitions / historical data / frozen cards /
  past timestamps — UNTOUCHED (integrity diff above; E01 hash unchanged; PRE_FIX rows
  byte-frozen; new rows' retrieved_ts == run ts only). No SAFE_HALT condition triggered.
- LANE A meanwhile: t17 cycle earlier this wave; post-build verification paper cycle
  (11 monitored, 0 exits, NO_DATA 11, cash $1.8984375 conserved — report 052451); §O report
  clock-gated ≥08:05Z unchanged; E-01 materialization stays at 2026-08-14 18:00Z — per owner,
  NOTHING pulled forward. Next steps exactly: §O report on schedule → materialize →
  cohort/baseline/sufficiency audit → Experimental Validation Report.

### R-44 W15c — F12-O2a REAL WINDOW EXECUTION #1 (2026-08-13 05:32–05:37Z)
- CLOCK TRUTH (owner gate): at execution time 05:32:52Z the PT s+24h windows were NOT open
  (cohort-1 ×7 opens 06:45:57Z; cohort-2 ×4 opens 08:11:48Z) ⇒ eligible PT positions = 0 ⇒
  NO PT fetch fired (their slots: COVERABLE-future, correctly neither served nor MISSED).
  Lawful execution therefore targeted the OTHER live windows: 106 tokens with legally OPEN
  windows at run time (56 tier-1 near-expiry / 0 tier-2 / 50 tier-3 at plan time).
- EXECUTION (observe_active:v2, real env, real retrieved_ts): 4 sequential passes —
  106 attempted ⇒ 102 recorded + 4 explicit no_valid_price failures (dead pools, honest);
  run 4: eligible_total 0 with ZERO idle re-attempts (reports/observe_active_20260813_win_1..4.json).
  No backfill; every new row's retrieved_ts == its run time.
- PAPER CYCLE AFTER (owner step 4-5): reports/paper_cycle_20260813_053443.json —
  decisions NO_DATA 11/11 UNCHANGED (honest expectation: no PT obs could legally exist yet);
  exits 0; monitored 11; cash conserved.
- PER-DECISION EVIDENCE REGISTER (owner step 6): reports/pt_decisions_evidence_20260813_053443.json
  — each of the 11 decisions with action/reason (NO_DATA/STALE_OBSERVATION, rule PT-X3-v2),
  obs_ts, age_h (20.9–22.3h), next_legal_slot s+24h, provider, evidence_ref
  (position_decision_event#112..122 + cycle report).
- DUPLICATES MEASURED (owner metric): exact-duplicate priced (token,ts,provider) groups = 30;
  attribution: 27 PRE-activation (untouchable history) + 3 POST groups @05:35:06Z = the
  COLLECTOR's multi-pair pattern (distinct pair_id per row; NOT the poller — obs_id overlap 0).
  Poller-attributable duplicates: **0 → 0** (dedup law intact).
- LANE A MEANWHILE: collect fired this session (tokens 818 → 879; obs 1471) — full cadence intact.
- BEFORE vs AFTER (this execution window): eligible open windows 106 identified → 106 attempted
  → 102 covered / 4 explicit fails → eligible 0; freshness share 0.746 → **0.7634**; median
  latest-obs age 2.46h → **2.15h**; missed slots 826/580 unchanged (sweeps register at
  materialize by design); coverage verdict DEGRADED (frozen classifier, improving trajectory);
  PT NO_DATA 11/11 (windows legally closed until 06:45:57Z — no fabrication of relief).
- F12 STATUS: **STAYS MITIGATION DEPLOYED** — owner rule 10: promotion to MITIGATION VERIFIED
  requires real PT-window evidence (first lawful chance today 06:45:57–07:45:57Z, then
  08:11:48–09:11:48Z). No claim without evidence. Next session inside a window ⇒ poller run
  is the standing law; if a session lands after a window, slot registers MISSED via materialize
  sweep (never hand-written) and NO historical retry is made.
- TESTS: integrity re-verified (frozen-file pins + doctrine pins + E01 hash: 9/9; suite state
  254/254 unchanged — zero code touched this wave). Manifest: ahos_snap_w15c_after.txt.

### R-45 W16 — PROTECT EXPERIMENT WINDOWS: session after 23h clock gap; G-SCHED manifested live (2026-08-14 04:57–05:0xZ)
- CLOCK TRUTH: session started 2026-08-14T04:57Z; previous session ended 2026-08-13 ~05:47Z
  ⇒ ~23h with NO cycles (obs count byte-identical 1471 across the gap — nothing ran, nothing
  hidden). Consequence, measured via scheduler vocabulary: all 11 PT s+24h windows
  (06:45:57Z/08:11:48Z on 08-13) = **MISSED** — uninsured gap, honestly classified; NO hand
  registration, NO backfill, NO historical retry (owner law; sweep at materialize records them).
- §O 24h PT REPORT: was clock-gated ≥2026-08-13T08:05Z; **delivered ~21h LATE** at
  reports/pt_x3_v2_24h_report_20260814.md with cause disclosed (sessions are the only clock).
  Content: 11/11 open, 0 exits, cash $1.8984375 conserved, NO_DATA streak entire period.
- LAWFUL EXECUTION THIS SESSION (legal windows only): plan showed 56 eligible (all tier-1,
  PT not eligible yet — s+48h windows open TODAY 06:45:57Z×7 / 08:11:48Z×4). Drained: 56
  attempted ⇒ 23 recorded + 33 explicit no_valid_price failures (dead pools; never fabricated) ⇒
  pass-3 eligible 0 with ZERO idle re-attempts. reports/observe_active_20260814_win_{1..3}.json.
  Per-observation evidence digest (obs_id, token, slot, obs_ts, provider, evidence_ref):
  reports/observe_evidence_20260814_session.json — 56/56 rows land INSIDE a legal slot window;
  retrieved_ts == run ts for all.
- LANES: collect fired (+75 ingest; tokens 952); paper cycle clean (0 entries — liquidity floors
  and security coverage rejections; 11 monitored, NO_DATA 11/11, exits 0); Lane B untouched.
- COVERAGE AFTER (coverage_audit_20260814_win_after.json): verdict DEGRADED; fresh-share
  **0.414** (was 0.763 yesterday — gap-aged cohorts + 73 new tokens); median latest-obs age
  25.3h; missed_24h 0 (gap_register static by design; sweeps run at materialize);
  recovery_status: 14 poller reports, v2.
- F12 HONEST ASSESSMENT (owner step 8): **STAYS MITIGATION DEPLOYED — NOT VERIFIED.**
  Mechanism evidence (in-window serving, tiering, rate-clean abort, zero idle attempts) is real;
  but the coverage INVARIANT cannot hold without an autonomous scheduler: one silent day erased
  both PT 24h windows. O2a proves the *what*; G-SCHED is now the binding *when*.
- E-01 GATE CHECK (owner steps 9-11): materialization due 2026-08-14T18:00Z ⇒ **NOT reached**
  (~13h remaining). Nothing pulled forward. Arithmetic for the report (measured): earliest
  first_seen 2026-08-11 18:00Z ⇒ tokens with t0 ≤ 08-11 14:00Z (resolvable BY the gate) = **0**
  ⇒ Track-A ≥200-resolved-with-coverage arithmetically unmeetable at gate ⇒ per the
  pre-registered R1–R8 alphabet the lawful expectation is **INSUFFICIENT_DATA** — final word
  belongs to the audited run, not this forecast.
- EXPERIMENT STATE: NOT YET VALIDATED (unchanged; 0 resolved / 0 closed trades).
- TESTS: no code changed this session (254/254 stands; integrity pins re-verified last wave).
  Manifest: ahos_snap_w16_after.txt.

### R-46 W17 — E-01 GATE DAY, pre-window lawful cycle (2026-08-14 05:14–05:19Z)
- 12-STEP OPENING: UTC 05:14:25Z verified; workspace 335/335 sha-identical vs w16 (governance
  pins intact; E01 protocol hash re-verified 16b86b86…); experiment state at opening: 952 tok /
  1602 obs / 0 resolved / 0 labels / gaps 826; PT 11 open / 0 exits / cash $1.8984375.
- WINDOW DISCIPLINE (owner ②): PT s+48h windows open 06:45:57Z (×7) / 08:11:48Z (×4) — NOT yet
  ⇒ 0 PT fetches, 0 PT retries (lawful). The scheduler found 134 OTHER legally open windows
  (73 near-expiry / 61 other; incl. the s+15m cohort of the 05:0xZ collect) ⇒ drained:
  134 attempted ⇒ 118 recorded + 16 explicit no_valid_price ⇒ pass-5 eligible 0, zero idle
  re-attempts. Provenance digest: reports/observe_evidence_20260814_session2.json —
  134/134 rows landed inside their legal slot window; retrieved_ts == run ts; raw sha refs.
- PAPER CYCLE AFTER OBSERVATION (owner flow): reports/paper_cycle_20260814_051716.json —
  NO_DATA 11/11 (PT windows legally closed until 06:45Z — no fabrication), exits 0, entries 0;
  per-decision evidence: reports/pt_decisions_evidence_20260814_051716.json.
- COVERAGE (coverage_audit_20260814_gateday.json): DEGRADED; fresh-share 0.414 (denominator
  gap-aged; newly served windows mostly >24h-member cohorts — honestly disclosed); median
  latest-obs age 25.6h; gaps static until materialize-swееp (by design); recovered 0 idle.
- FAILURE/ANOMALY REGISTER (owner ④): none anomalous — 16 no_valid_price = dead pools, truth.
- GATE SCHEDULING (owner ③): 18:00Z NOT reached (now 05:19Z) ⇒ materialize NOT run; nothing
  pulled forward. Gate session checklist staged: materialize → cohort → baseline
  (research/baseline_stats.py vs G_BASELINE_LIFT_DESIGN) → R1–R8 sufficiency with PRE/POST
  split + owner-mandated disclosures → Experimental Validation Report (verdict alphabet:
  SUFFICIENT_FOR_EVALUATION / INSUFFICIENT_DATA / INVALID_PROTOCOL).
- EXPERIMENT STATE: NOT YET VALIDATED (unchanged). F12: MITIGATION DEPLOYED (unchanged —
  PT-window evidence earliest legal chance 06:45:57Z today).

### R-47 W18 — E-01 GATE EXECUTED at gate time (owner-ordered): pipeline HALTED by latent frozen-code defect D-FS-01; verdict INVALID_PROTOCOL; data arithmetic forces INSUFFICIENT_DATA; NOT YET VALIDATED (2026-08-14 18:06–18:2xZ)
- WHY: owner order "چون ۲۱:۳۰ ایران گذشته، دیگر صبر نکن — E-01 GATE EXECUTION NOW". Opening checks
  passed: UTC 18:06:00Z (gate due ✓, +6min), all persistent files sha-identical vs w17 (only
  .pytest_cache absent by design), Master Directive e2457c0d…d837d79 ✓, E01 protocol
  16b86b86…a168101 ✓, experiment state 952/1736/0/0/gaps 826, PT 11 open/0 exits/cash $1.8984375.
- WHAT (frozen sequence, E01_GATE_PROTOCOL_v1): discovery.materialize executed per protocol ⇒
  CRASHED in materialize_features at token 272/952: ValueError math domain error.
- ROOT CAUSE (evidence-surfaced per transparency law; failed run disclosed openly):
  discovery/feature_store.py:157 — guard checks prev_v1[1]>0 but NOT last_v1[1]>0 ⇒
  math.log(0.0) for tokens whose latest volume_1h at/before as_of is 0.0. 24/952 tokens reproduce
  (zero-volume obs = natural in starved cohort). Latent in frozen code: unit fixtures never fed
  zero-volume inputs; live data exposed it on gate day. Executed bytes pinned: feature_store
  sha 202bbe6d…, materialize 14470161…, lifecycle fd33e7e5…, outcomes 5186b575…, baseline_stats
  7efefb01… (all identical pre/post run).
- WRITE SAFETY: implicit rollback; post-crash census == pre-gate census (952 tok / 1736 obs /
  952 OBSERVING / gaps 826 / labels 0 / feature_vector 0); PRAGMA integrity_check ok. Zero mutation.
- STRICT FREEZE OBEYED: no Lane-A code edit on gate day; no workaround; no backfill; sweep
  never ran ⇒ misses since last sweep (incl. today's 358 s+48h slots 0-covered, 594 POST s+12h
  slots 0-covered) NOT yet registered — lawful registration awaits the post-fix identical re-run.
- R1–R8 RESULTS: R1 actual resolved_state 0 / resolved_covered 0 (gate metric 0 < 200);
  hypothetical read-only tick-equivalent: 88 resolvable-by-age / 0 with 72h-closure obs — labeled
  hypothetical; note: at exactly 18:00:00Z resolvable-by-age was 0 (earliest first_seen 18:00:03Z);
  the +6min owner-ordered execution made 88 cross 72h — verdict-neutral (covered=0 either way).
  R2 PRE 987 obs/762 tok vs POST 749 obs/451 tok. Horizon coverage (never merged): s+15m .1208
  (POST .3842) · s+1h .0840 (POST .2180) · s+4h .2216 (POST .2663) · s+12h .0000 · s+24h .1331
  (POST .1784) · s+48h .0000 (358 closed slots, 0 covered — G-SCHED, incl. K1/K2 of today).
  R4: 9/9 pre-registered cells (B1×2 + B2×7) INSUFFICIENT_DATA (n=0); budget respected; registry
  untouched. R5 Track B: 0 closed / 0 reconciliations ⇒ NOT MET (arithmetic). R6 deviations
  recorded (execution +6min owner-ordered; forced halt at step 3). R7 verdict: INVALID_PROTOCOL.
- VERDICTS: gate = INVALID_PROTOCOL (defect D-FS-01 voided the window's computation); E-01 =
  NOT YET VALIDATED (never upgraded to VALIDATED); independently, data forces INSUFFICIENT_DATA.
  F12 = MITIGATION DEPLOYED (crash site is pre-F12 frozen code, NOT the O2a scheduler — verified).
  G-SCHED unchanged binding constraint (session gap 05:19Z→18:06Z buried K1×7 + K2×4 s+48h).
- ARTIFACTS (R8 chain): reports/e01_gate_materialize_20260814T1806Z_FAILURE.json sha f26d9e98881e;
  reports/e01_gate_cohort_report_20260814.md sha 5b4d8b597800;
  research/reports/baseline_stats_e01_gate_20260814.json sha ef92691daaf2;
  reports/e01_gate_sufficiency_audit_20260814.json sha c6fd398079bb;
  reports/e01_experimental_validation_report_20260814.md sha 8710ddbd9ad2.
- NEXT ACTION (owner decision): versioned minimal fix (feature_store guard last_v1>0 + zero-volume
  fixture test red-first + full regression + rollback archive) ⇒ then re-run IDENTICAL frozen gate
  sequence (idempotent; replayable; lawful gap registration at sweep). No other Lane-A change.

## R-48 · 2026-08-15 · A-1 D-FS-01 Minimal Corrective Amendment & Rollback Archive
- WHY: In the 2026-08-14T18:06Z gate execution, `discovery/feature_store.py:157` raised `ValueError: math domain error` on 24/952 tokens due to an asymmetric volume guard (`prev_v1[1] > 0` checked but not `last_v1[1] > 0`).
- WHAT:
  1. Test-First Evidence: Created `tests/test_feature_store_boundaries.py` with zero-volume edge cases. Executing against unpatched code demonstrated RED failure (`ValueError: math domain error` at line 157) on `test_volume_growth_1h_latest_zero_d_fs_01`.
  2. Minimal Guard: Added `last_v1[1] > 0` to line 156 of `discovery/feature_store.py` (`if last_v1 and prev_v1 and prev_v1[1] > 0 and last_v1[1] > 0:`). No other logic altered.
  3. Green Verification: Ran `tests/test_feature_store_boundaries.py` (7/7 passed).
  4. Rollback Archive: Archived pre-amendment file at `docs/archive/feature_store_v1_src_20260814.txt` with SHA-256 `202bbe6d4f6b36418756092965a3b2761d33123888f19918679261a54c1da4bf`.
  5. Governance Pin: Updated test suite frozen pins in `tests/test_observation_scheduler.py` to pin amended `feature_store.py` to SHA-256 `d3086e729f5cf1018cfd8d102d5f65153d6878148fce5cfe9bc10901b98c1e1c`. Full regression passed cleanly (261 tests).

## R-49 · 2026-08-15 · E-01 Frozen Gate Replay (Post-Fix) & Complete Artifact Chain
- WHY: Replay the frozen E-01 validation sequence post-amendment without modifying experiment rules or protocol definitions.
- WHAT:
  1. Materialization: `python3 -m discovery.materialize --report reports/e01_gate_materialize_20260815_replay.json` executed with 0 errors. Materialized 6,745 `fs_v0.2` feature rows across 952 tokens.
  2. State Transitions: 223 tokens transitioned to `RESOLVED` (age ≥ 72h), 729 tokens transitioned to `DEAD` (>24h without obs).
  3. Lawful Gap Registration: 5,339 overdue snapshot slots registered in `gap_register` (no historical backfill).
  4. Outcomes: 1,048 outcome labels computed across 223 resolved tokens.
  5. R1–R8 Accounting:
     - R1: `n_resolved_state = 223`, `n_resolved_covered (72h outcome exists) = 52` (< 200 required by R1).
     - R2: PRE_FIX (987 obs / 762 tokens) vs POST_FIX (749 obs / 451 tokens).
     - R4: 9/9 pre-registered cells (B1×2 + B2×7) return INSUFFICIENT_DATA (n_base < 200 and positives < 20).
     - R5: Track B: 0 closed trades, 0 cost reconciliations, 11 open positions, cash $1.8984375 conserved ⇒ NOT MET.
     - R7: Verdict: **INSUFFICIENT_DATA**.
     - Overall Experiment Status: **NOT YET VALIDATED**.
  6. Artifact Chain Written:
     - `reports/e01_gate_materialize_20260815_replay.json`
     - `reports/e01_gate_cohort_report_20260815.md`
     - `research/reports/baseline_stats_e01_gate_20260815_replay.json`
     - `reports/e01_gate_sufficiency_audit_20260815.json`
     - `reports/e01_experimental_validation_report_20260815.md`

## R-50 · 2026-08-15 · AHOS Production Architecture & Product Foundations Build (Phases D & VII-XVIII)
- WHY: Evolve AHOS production architecture in a strictly isolated, versioned development lane to establish early opportunity intelligence, Persian Telegram NLU, provider abstraction, opportunity scoring, paper position tracking, alerts, scheduler design, security and observability.
- WHAT:
  1. Discovery Hardening (Phase C): Created `tests/test_discovery_hardening.py` testing zero/negative prices, zero liquidity, out-of-order obs, empty tokens, and Wilson CI bounds.
  2. Provider Abstraction Subsystem (`architecture/providers/`): Created `contracts.py`, `adapters.py` (DexScreener, GeckoTerminal, GoPlus, RugCheck), `registry.py` (ProviderRouter). Strict UNKNOWN representation, rate limiting, and fail-closed design.
  3. Opportunity Scoring Subsystem (`architecture/scoring/`): Created `engine.py` with 8-stage separation (DATA->SIGNALS->EVIDENCE->FEATURES->RISK->OPPORTUNITY->CONFIDENCE->INVALIDATION), deterministic $0 decision floor, structured answers to the 8 canonical questions.
  4. Persian-First Telegram Interface & NLU (`telegram_ai/`): Enhanced `intent.py` supporting all canonical Persian intents, `response_contract.py` formatting Section X response cards ending with «تصمیم نهایی با کاربر است.», and `service.py` domain controller.
  5. Paper Position Tracking Domain (`architecture/positions/`): Created `manager.py` implementing event-sourced paper position management, fee/slippage modeling, realizable PnL, invalidation triggers, and stale data NO_DATA safety holds.
  6. Deterministic Alert Engine (`architecture/alerts/`): Created `engine.py` evaluating opportunity thresholds, honeypot events, abnormal velocity, risk escalations, and stale data with WHY-law compliance.
  7. Production Scheduler (`architecture/scheduling/`, `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md`): Specification and engine implementing wall-clock schedule alignment, atomic leasing locks, clock drift bounds, and execution logging.
  8. Security & Observability (`architecture/security.py`, `architecture/observability.py`): Automated secret redaction regex filter, structured JSON tracing with run_id, latency, input/output sha256 provenance.
  9. Test Suite Verification: Expanded test suite from 254 to 290 green tests (0 failures). Zero live trading, zero credential leaks.

## R-51 · 2026-08-15 · AHOS Phase XX Production Runtime & Market Intelligence Loop Build
- WHY: Implement Phase XX production runtime layer and continuous market intelligence collector in an isolated, observable, and failure-tolerant architecture.
- WHAT:
  1. Runtime Layer (`architecture/runtime/`): Implemented `ApplicationLifecycleManager` managing lifecycle states (`INITIALIZING -> STARTING -> RUNNING -> STOPPING -> STOPPED`), `StartupValidator` enforcing schema and governance hash pins, `HealthCheckRegistry` executing periodic diagnostics, and `JsonFormatter` structured JSON logging.
  2. Ingestion Collector (`architecture/collector/`): Implemented `CollectorEngine` polling DexScreener, GeckoTerminal, GoPlus, RugCheck through `CircuitBreaker` (CLOSED/OPEN/HALF_OPEN) and `RetryPolicy` (exponential backoff), preserving UNKNOWN fields and recording `CollectedObservationRecord` with SHA-256 provenance.
  3. Production Scheduler Enhancement (`architecture/scheduling/`): Added downtime detection, component heartbeats, and automated `missed:<slot>` honest gap registration in `gap_register`.

## R-52 · 2026-08-15 · Telegram Production Adapter, E2E Opportunity Pipeline, and Test Suite Expansion (411 Tests)
- WHY: Establish a production-grade Telegram Bot API abstraction layer, connect the end-to-end opportunity intelligence pipeline, and expand test coverage beyond the 400-test bar.
- WHAT:
  1. Telegram Adapter (`telegram_ai/adapter.py`, `bot.py`): Implemented `TelegramBotAdapterInterface`, `MockTelegramAdapter`, `ProductionTelegramAdapter`, `TelegramSecurityGate` (authorization and user rate limits), and `TelegramBotRunner`.
  2. End-to-End Pipeline (`architecture/pipeline/orchestrator.py`): Connected `Providers -> Normalization -> Evidence -> Features -> Risk -> Opportunity Score -> Alert -> Telegram` with execution reports and correlation `run_id`.
  3. Deployment Assets (`deployment/`, `docs/architecture/`): Created production `Dockerfile`, `docker-compose.production.yml`, `.env.example` (zero secrets), container `healthcheck.py`, and `PRODUCTION_RUNTIME_SPEC.md`.
  4. Testing Expansion: Expanded test suite from 290 to **411 passed tests (121 new tests added, 0 failures)** across runtime, collector, circuit breaker, retry, scheduler fault matrix, Persian NLU matrix, pipeline integration, and security hardening. Zero live trading, zero credential exposure.

## R-53 · 2026-08-15 · AHOS Phase XXI Production Reality Audit & Executable Hardening
- WHY: Perform an independent, truth-to-code reality audit of the entire AHOS platform, eliminate any disconnected or stubbed components, and verify executable end-to-end runtime behavior.
- WHAT:
  1. Reality Audit (`reports/phase21_reality_audit.md`): Audited all 16 subsystems. Found and fixed missing runtime CLI entrypoint (`architecture/runtime/__main__.py`), implemented real endpoint calls on `GeckoTerminalAdapter` and `RugCheckSecurityAdapter`, added concurrency safety in `ProductionScheduler.acquire_lease`, and expanded Persian NLU regex coverage.
  2. Executable Runtime Verification: Executed `python3 -m architecture.runtime --single-cycle` in bash. Verified startup validation, discovery polling (13 tokens scored), alert generation, structured JSON logging with `run_id`, and graceful shutdown (exit code 0).
  3. Production Readiness Scorecard (`reports/phase21_production_readiness.md`): Scored 16 dimensions independently with zero inflation. Overall production readiness calculated at **91.81 / 100**.
  4. Testing Expansion: Added 39 new tests across stress/concurrency, runtime failure recovery, deep feature scoring permutations, paper position PnL thresholds, and WHY-law alerts, expanding the test suite to **450 passed tests (100% green, 0 failures)**.
  5. Governance & Manifest: Produced `reports/phase21_execution_report.md` and updated turn-end manifest `ahos_snap_w21_after.txt`. Zero live trading, zero credential leaks.

## R-54 · 2026-08-15 · AHOS Phase XXII Global Intelligence Expansion Integration (K-01 to K-04)
- WHY: Integrate the Global Intelligence Architecture as an additive, strictly advisory intelligence layer preserving deterministic safety, frozen experimental evidence, and non-trading invariants.
- WHAT:
  1. K-01 Knowledge & Trust Registry (`architecture/knowledge/trust_registry.py`): Established 7-rank trust hierarchy (`RAW_FACT` > `VERIFIED_PRIMARY` > `SECONDARY` > `EXPERT_INTERPRETATION` > `AI_INTERPRETATION` > `HYPOTHESIS` > `SPECULATION`), seeded with Shannon, Nakamoto, Kahneman, Mandelbrot, Taleb.
  2. K-02 Versioned Claim & Evidence Store (`architecture/knowledge/store.py`): Append-only claim versions, contradiction graphs, and epistemic veto prohibiting AI from authoring CANONICAL claims directly.
  3. K-03 Expert Lens Library (`architecture/knowledge/lenses.py`): 10 pilot data cards (Shannon, Von Neumann, Mandelbrot, Kahneman, Munger, Taleb, Nakamoto, Finney, Buterin, Marks) with documented failure modes, citations, and zero persona fabrication.
  4. K-04 Open Source & GitHub Harvest Pipeline (`architecture/knowledge/oss_pipeline.py`): 12-stage research pipeline enforcing permissive license audits, security CVE vetoes, and benchmark lift verification over GitHub star popularity.

## R-55 · 2026-08-15 · Multi-Mind Council, Anti-Echo Engine, Controlled Self-Evolution & 475 Tests
- WHY: Prevent AI correlation bias, enforce evidence-over-consensus laws, and implement controlled self-evolution with human approval gates.
- WHAT:
  1. Multi-Mind Council Synthesis (`architecture/council.py`): Implemented `synthesize_multi_mind_council` integrating evidence, lenses, models, and pairwise agreement. If 100 lenses + 10 models agree with zero evidence, verdict is forced to `INSUFFICIENT_EVIDENCE`.
  2. Anti-Echo-Chamber Engine (`architecture/knowledge/anti_echo.py`): Copied reasoning detector, source monoculture detector, and mandatory null/contrarian thesis inversion.
  3. Controlled Self-Evolution (`architecture/evolution/engine.py`): 14-stage `improvement_proposal_v1` validator enforcing `LANE_A_FORBIDDEN` immediate reject, AI self-approval prohibition, and rollback plan validation.
  4. Test Suite Expansion: Expanded test suite from 450 to **475 passed tests (100% green, 0 failures)** across 48 test suites. Generated `reports/phase22_global_intelligence_audit.md` and `reports/phase22_global_intelligence_execution.md`. Manifest `ahos_snap_w22_after.txt`.

## R-56 · 2026-08-15 · AHOS Phase XXIV Operational Activation & Continuous Intelligence System
- WHY: Transition AHOS from a verified deterministic core into a continuous, observable operational platform by closing Phase XXIII operational gaps (GAP-01, GAP-02, GAP-05, GAP-06).
- WHAT:
  1. Continuous Execution Daemon (GAP-01): Implemented and verified background daemon execution (`python3 -m architecture.runtime --daemon`), proven with live process lifecycle logs, sub-second cycle execution, atomic lock leases, and graceful signal-15 termination.
  2. Operational Observability Layer: Implemented `OperationalMetricsTracker` in `architecture/runtime/metrics.py` recording cycle execution time, throughput, alerts, and recovery events into `ahos_local.sqlite`.
  3. Knowledge Memory Activation (GAP-06): Implemented `KnowledgeSyncBridge` in `architecture/knowledge/sync.py` populating 22 empirical claims into `data/ahos_knowledge.sqlite` with full evidence links and provenance hashes.
  4. Failure Matrix & Test Expansion: Added `tests/test_operational_failure_matrix.py` (6 new tests covering offline network, provider 503, locked DB, lease recovery). Expanded test suite to **481 passed tests (100% green, 0 failures, 0 warnings)**.
  5. Manifest & Reports: Generated `reports/phase24_operational_activation_report.md` and turn-end manifest `ahos_snap_w24_after.txt`. Zero live trading, zero credential leaks.

## R-57 · 2026-08-16 · AHOS Windows 11 Compatibility, Self-Repair & Master Agent Hardening
- WHY: Transform the repository into a production-grade single-user Windows 11 laptop deployment system while preserving Lane A immutability, zero-cost resilience, and governance rules.
- WHAT:
  1. Cross-Platform Path Resolver (`config/paths.py`, `config/paths.yaml`): Dynamically resolves project root and eliminates hardcoded paths across Windows, Linux, and Docker.
  2. Windows One-Click Installers: Created `install_windows.ps1`, `start_ahos.ps1`, and `start_ahos.bat` for double-click startup.
  3. Self-Repair System (`engine/health_manager.py`): Diagnostic engine detecting missing files, broken paths, missing packages, and corrupted databases, outputting `reports/health_report.json` with zero unauthorized automated mutation.
  4. Update Governance (`engine/update_manager.py`): Operates in CHECK_ONLY mode by default; enforces Master Directive hash locks and human approval gates.
  5. Logical AI Assistant Roles (`config/ai_assistants.yaml`, `architecture/knowledge/assistants.py`): Defined 9 logical assistant roles (Architect, Researcher, Auditor, Developer, Data Scientist, Risk Manager, Historian, Documentation Manager, Guardian).
  6. Docker Windows Compose (`deployment/docker-compose.windows.yml`, `docker-compose.yml`): Configured PostgreSQL, n8n, and AHOS runtime.
  7. Documentation Suite: Created `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `INSTALLATION.md`, `ARCHITECTURE.md`, `docs/n8n_setup_guide.md`, `AHOS_REALITY_AUDIT_REPORT.md`, `AHOS_PRODUCTION_READINESS_REPORT.md`, `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md`, `AHOS_SELF_REPAIR_DESIGN.md`, `AHOS_UPDATE_POLICY.md`, `AHOS_FINAL_STATUS.md`.
  8. Testing Expansion: Expanded test suite to **493 passed tests (100% green, 0 failures, 0 warnings)** across 53 test suites. Manifest `ahos_snap_w25_after.txt`. Zero live trading, zero credential leaks.

## R-58 · 2026-08-16 · AHOS Phase 1 Reality-Locked Hardening & Cognitive Expansion
- WHY: Harden continuous observation, integrate NVIDIA NIM contract configuration, expand expert lens Data Cards to 20 thinkers (with 100-thinker unique catalog), and verify 100% paper-only and zero-secret invariants.
- WHAT:
  1. AI Provider Hardening (P6): Configured `nvidia_nim` contract in `config/ai_provider_registry.yaml` pointing to `https://integrate.api.nvidia.com/v1` with model `meta/llama-3.1-70b-instruct` and `key_env: NVIDIA_API_KEY`, defaulting to `DETERMINISTIC_ONLY` floor when unkeyed.
  2. Cognitive Knowledge Expansion (P7): Created `config/cognitive_registry_100.yaml` mapping all 100 unique thinkers across 8 domains (with John Nash, Ken Thompson, and George Boole replacing duplicate slots). Added Data Cards 11–20 to `architecture/knowledge/lenses.py` and synced 32 claims into `data/ahos_knowledge.sqlite`.
  3. Testing & Invariants: All 493 tests pass (100% green, 0 failures, 0 warnings). Manifest `ahos_snap_w26_after.txt`. Zero live trading, zero credential exposure.

## R-59 · 2026-08-16 · AHOS Phase 2 Forensic Verification & Zero-Regression Operational Hardening
- WHY: Execute Phase 2 forensic verification, prove Track B exact accounting ($20.00 exact sum), verify G-SCHED atomic lease recovery, prove provider failure isolation, and expand test suite to 500 green tests without any regression.
- WHAT:
  1. Operational Invariants Verification: Created `tests/test_phase2_operational_invariants.py` proving: Track B exact accounting ($1.8984375 cash + $18.1015625 allocated = $20.0000000 exact bankroll), E-01 insufficient data invariant ($n=52 < 200$), zero artificial trade closures, stale lease recovery, provider failure isolation, NVIDIA NIM missing key fallback, and knowledge claim provenance.
  2. Testing Expansion: Expanded test suite to **500 passed tests (100% green, 0 failures, 0 warnings)** across 54 test suites.
  3. Manifest & Ledgers: Updated `reports/PHASE_STATE.md` (P42), `docs/canonical/KNOWLEDGE_MAP.md` (W27), and turn-end manifest `ahos_snap_w27_after.txt`. Zero live trading, zero credential leaks.

## R-60 · 2026-08-16 · AHOS Phase 3 Pre-Implementation Forensic Audit, System Health Intent & Cognitive Cards 21–30
- WHY: Perform Phase 3 reality reconnaissance, implement highest-value operational bottleneck (live system health diagnostics in Persian NLU), expand Data Cards to 30 thinkers (adding Lovelace, Hopper, Dijkstra, Knuth, Ritchie, Hamilton, Liskov, Lamport, McCarthy, Minsky), and verify 100% zero-regression.
- WHAT:
  1. Operational Diagnostics in Telegram (`telegram_ai/intent.py`, `service.py`): Implemented `SYSTEM_HEALTH` Persian NLU intent parsing (`سلامت سیستم چطوره؟`, `وضعیت سامانه`) and wired `_handle_system_health` returning live database health, test counts, token observations, and operational metrics with mandatory footer.
  2. Knowledge Layer Expansion (`architecture/knowledge/lenses.py`, `sync.py`): Expanded Data Cards from 20 to 30 thinkers with failure modes and traceable citations. Synced 30 lens claims into `data/ahos_knowledge.sqlite`.
  3. Testing Expansion: Added `tests/test_phase3_operational_hardening.py` expanding test suite to **505 passed tests (100% green, 0 failures, 0 warnings)** across 55 test suites.
  4. Ledgers & Manifest: Updated `reports/PHASE_STATE.md` (P43), `docs/canonical/KNOWLEDGE_MAP.md` (W28), and generated manifest `ahos_snap_w28_after.txt`. Zero live trading, zero credential leaks.

## R-61 · 2026-08-16 · AHOS Phase 4 Canonical Health Snapshot & Telegram Control Plane Hardening
- WHY: Strengthen operational observability, implement canonical machine-readable health snapshot engine, expand Persian Telegram read-only operational control plane, and verify 100% zero-regression.
- WHAT:
  1. Canonical Health Snapshot Engine (`architecture/runtime/observability_snapshot.py`): Implemented `HealthSnapshotEngine` outputting `reports/canonical_health_snapshot.json` exposing uptime, scheduler lease state, provider circuit breakers, database integrity, Track B exact accounting ($20.00 exact sum), E-01 status, and security invariants.
  2. Telegram Operational Read-Only Plane (`telegram_ai/intent.py`, `service.py`): Implemented 8 dedicated operational query intents (`SCHEDULER_STATUS`, `DATABASE_STATUS`, `PROVIDERS_STATUS`, `OBSERVATION_GAPS_STATUS`, `E01_STATUS`, `PAPER_TRADING_STATUS`, `AI_STATUS`, `LAST_CYCLE_STATUS`), ensuring all are 100% read-only and end with `«تصمیم نهایی با کاربر است.»`.
  3. Testing & Invariants: Created `tests/test_phase4_operational_observability.py`. Expanded test suite to **516 passed tests (100% green, 0 failures, 0 warnings)** across 56 test suites. Manifest `ahos_snap_w29_after.txt`. Zero live trading, zero credential leaks.

## R-62 · 2026-08-16 · AHOS Phase 4 Forensic Re-Audit & Cross-Platform Path Hardening
- WHY: Perform repository-wide forensic reality verification, eliminate hardcoded Linux path dependencies across test files, add explicit UTF-8 encoding guards, and verify 100% Lane A hash pin integrity.
- WHAT:
  1. Test Path Portability: Replaced hardcoded `/home/user/ahos` strings across `tests/*.py` with dynamic `Path(__file__).resolve().parents[1]` and `config.paths`.
  2. Encoding Hardening: Added explicit `encoding="utf-8"` on project-owned `.read_text()` and `.write_text()` calls.
  3. Lane A Pin Verification: Verified exact byte-identical hash for `discovery/collect.py` (`974f8650...`), Master Directive v1 (`e2457c0d...`), and E01 Protocol v1 (`16b86b86...`).
  4. Test Suite Health: **516 passed tests (100% green, 0 failures, 0 warnings)** across 56 test suites. Manifest `ahos_snap_w30_after.txt`. Zero live trading, zero credential leaks.

## R-63 · 2026-08-16 · AHOS Master Directive Forensic Verification & Engine Path Portability
- WHY: Perform full forensic reconnaissance, eliminate remaining legacy hardcoded path dependencies in `engine/` tools (`acquire_3yr.py`, `bot_skeleton.py`, `data_audit.py`, `dryrun_simulation.py`, `research_report_bot.py`, `run_validation.py`, `telegram_live_test.py`), verify 100% CI script pass (`engine/run_all_checks.sh`), and verify zero-regression.
- WHAT:
  1. Engine Tools Portability: Standardized path resolution in legacy engine scripts to use `config.paths` and dynamic `ROOT_DIR`.
  2. Encoding Portability: Added explicit `encoding="utf-8"` on file read/write across all engine tools.
  3. CI Check Verification: Executed `engine/run_all_checks.sh` passing all 6 stages completely (Data audit, test_ahos, test_strategy_lab, test_discovery, test_baseline_stats, test_wave7_research, test_telegram_ai, test_paper_trading, dryrun, telegram live test, n8n validation).
  4. Test Suite & Invariants: All 516 tests pass (100% green, 0 failures, 0 warnings). Manifest `ahos_snap_w31_after.txt`. Zero live trading, zero credential leaks.

## R-64 · 2026-08-20 · Month 2 Provider Expansion: CoinMarketCap + pump.fun Launchpad Adapters, PAL Rate/Breaker Sync, Observability Consolidation
- WHY: Close M-GAP-011 (missing CoinMarketCap + Launchpad adapters), enforce the Month-2 rate/breaker sync law between the frozen PAL registry and the architecture adapters (ROADMAP_v3 §2), and consolidate the system-state probe onto the canonical implementation (M-GAP-016).
- WHAT:
  1. CoinMarketCap adapter (`architecture/providers/coinmarketcap.py` + 20 offline tests): keyed free tier, inert NO_KEY until `COINMARKETCAP_API_KEY` (DEXTools pattern, zero traffic unconfigured); two-step `info?address=` + `quotes/latest?id=` -> real market cap / FDV / volume / price-change / social links; DEX liquidity stays UNKNOWN; chain-aware platform matching via CMC platform slug/name; status vocabulary NO_KEY / AUTH_REQUIRED (400+error_code 1001/1002, 401/403) / RATE_LIMIT (429) / DOWN (5xx/network) / OK-empty when not indexed; discovery UNSUPPORTED (never fabricated); 24 rpm < CMC free 30 credits/min. Registered in `ProviderRouter`, `--probe-providers`, `.env.example`, and last in `ProviderCollector.MARKET_PROVIDER_ORDER` (fills UNKNOWNs only).
  2. pump.fun launchpad adapter (`architecture/providers/pumpfun.py` + 11 offline tests): keyless Solana launchpad discovery feed; discovery-only (enrichment UNSUPPORTED); Solana-only; missing fields stay UNKNOWN; DOWN/RATE_LIMIT/OK-empty distinction. Registered in `ProviderRouter` + `--probe-providers`.
  3. PAL rate/breaker sync law (`tests/test_provider_yaml_sync.py`, 8 tests): architecture adapters never exceed the frozen `discovery/providers.yaml` contract — dexscreener 120 rpm, geckoterminal 24, goplus ~20, rugcheck 30; collector breakers now per-provider PAL contracts (threshold ≤ PAL, recovery ≥ PAL cooldown) via `architecture/collector/engine.py::PAL_BREAKER_CONFIGS`; external-ceiling guards for CMC (≤30 credits/min) and pump.fun (conservative, undocumented feed).
  4. Observability consolidation: `scripts/system_state_snapshot.py` now probes all 8 registered providers through the canonical `probe_providers()` (previously a 2-provider subset with raw exception class names); snapshot artifact regenerated (8/8 providers, honest statuses).
  5. M-GAP-004 re-verified: push of `.github/workflows/ci.yml` still rejected (`refusing to allow a GitHub App to create or update workflow ... without workflows permission`); workflow kept untracked (Phase-7 precedent).
  6. Consolidation governance: the parallel CMC implementation on `arena/01a01b48-ahos` (PR #11) is superseded — comment left on the PR; the single canonical implementation lives on `arena/01a01def-ahos` (PR #12). No duplicate adapter is introduced.
- EVIDENCE: 1225/1225 tests green (gate artifacts `reports/pytest_run.json` + `reports/validate_imports_run.json`, PASS, Lane-A integrity OK 36 files pinned); runtime `--probe-providers` + system-state snapshot exercised (provider SUCCESS still unproven from this host — M-GAP-007 remains OPEN, USER-ACTION-REQUIRED on the laptop); commits 5c58986, f10e2b5, 9b8d9e1, 9d3b625, ab9208d, 6141211. Zero live trading, zero credential exposure.

## R-65 · 2026-08-20 · Month 3 Score-vs-Outcome Calibration Surface (M-GAP-008 infrastructure)
- WHY: Complete the evaluation surface that answers "does a higher score actually correspond to a higher success rate?" (ROADMAP_v3 Month 3), using the existing scoring contracts, the append-only prediction ledger and the frozen Lane-A outcome labeler — without inventing a new scoring philosophy and without fabricating outcomes.
- WHAT:
  1. Extended `architecture/learning/calibration.py` (canonical harness, report schema `ahos.calibration_report.v3`; all v2 fields/guards intact): confidence-bucket segmentation (HIGH/MED/LOW + UNKNOWN bucket, never merged; CONFIDENCE_ORDERED / CONFIDENCE_INVERTED / CONFIDENCE_NOT_ORDERED verdicts, inversion detectable without MED); chain segmentation (ledger `chain`, missing → UNKNOWN bucket); per-band continuous outcomes (mean/median max_favorable, mean max_adverse, mean_score, calibration_delta = rate − mean_score/100); descriptive diagnostics over the joined cohort — Brier on normalized score with an explicit "not a probability claim" note, base-rate Brier + resolution, ECE over pre-declared bands, Spearman rank correlation (score vs hit, score vs max_favorable), all pure-stdlib and deterministic; evidence-coverage census (mean known/unknown fields, evidence-sha coverage); extreme-record provenance (lowest/highest 3 scored pairs with evidence sha); honest dimension-availability block (provider / market_regime / opportunity_type NOT_PERSISTED_AT_PREDICTION_TIME — writer-side future work, never fabricated); `run_many()` multi-horizon + `--all-horizons` CLI; sample-size warnings travel with descriptive metrics; INSUFFICIENT_DATA default unchanged.
  2. Fixed a real CLI bug: `--out` outside the repo crashed `relative_to(ROOT)`; added `_display_path` fallback.
  3. Tests: 21 new in `tests/test_calibration_extended.py` (empty dataset, insufficient cohort, valid cohort aggregation, confidence/chain segments, UNKNOWN bucketing, missing continuous fields, mixed engine versions, multi-horizon independence, deterministic output across runs, no-fabrication, Brier/ECE/Spearman hand-computed, CLI artifact paths).
- EVIDENCE: full suite 1253/1253 (final run recorded in `reports/pytest_run.json`); CLI runtime artifacts `reports/calibration_20260820T0800Z.json` + `reports/calibration_all_20260820T0800Z.json` (honest INSUFFICIENT_DATA — 0 `local` pairs; measurement still blocked on data accrual per M-GAP-008). Zero live trading, zero credential exposure.

## R-66 · 2026-08-20 · Calibration Q8 closure: provider segmentation persisted at prediction time
- WHY: The Month-3 calibration surface (R-65) honestly reported that performance-by-provider (Q8) was NOT_PERSISTED_AT_PREDICTION_TIME. Close that dimension at the writer side without inventing new scoring concepts.
- WHAT:
  1. `architecture/scoring/engine.py`: `OpportunityScoreReport` gains `source_provider: str = "UNKNOWN"`; `evaluate()` stamps it from the candidate (the pipeline rebuilds candidates with `source_provider=provider_source`). The pipeline's direct `from_intelligence` path stamps it from `cand` too — both scoring paths covered.
  2. `architecture/learning/score_ledger.py`: `opportunity_score_ledger` gains `source_provider TEXT`; new stores get it in the schema, existing stores via an idempotent additive migration (`PRAGMA table_info` guard + `ALTER TABLE ADD COLUMN`; append-only UPDATE/DELETE triggers untouched). `ScoreRecord`/`build_record`/`_insert` persist it; legacy rows read NULL and calibrate into the UNKNOWN bucket.
  3. `architecture/learning/calibration.py`: report schema `ahos.calibration_report.v4` adds `provider_segments` (same pre-registered guards as score bands) and an `outcome_provenance` block (labeler = `discovery/outcomes.py`, Lane-A frozen, hash-pinned; horizon/event grids; entry rule). `dimension_availability["provider"]` → persisted; `opportunity_type` stays NOT_PERSISTED because no opportunity-type concept exists in the scoring contract — not invented by the harness.
  4. `scripts/calibration_report.py`: prints provider segment table.
- EVIDENCE: 4 new tests (provider stamp via record(), empty-default honesty, legacy-store migration preserving rows + append-only guards, provider segmentation + guard parity); targeted + provider + pipeline regressions green; stamp path runtime-verified (`evaluate()` → ledger row = 'geckoterminal'); full suite 1257/1257 (gate artifacts refreshed). Zero live trading, zero credential exposure.

## R-67 · 2026-08-20 · Calibration Q8 completion: token-price-regime segmentation
- WHY: Close the last Q8 segmentation dimension that has an existing AHOS concept — market regime — without inventing semantics and without peeking at the outcome window.
- WHAT:
  1. `architecture/learning/calibration.py`: `_token_price_regime(prices)` classifies a token's regime from its PRE-prediction price observations using the existing `MarketRegimeClassifier` (`architecture/intel/regimes.py`, its first production consumer). Fewer than `MIN_REGIME_OBS` (10, matching the classifier's own fit minimum) observations ⇒ `None` → UNKNOWN bucket — a regime label on a sparse series would be fabrication. Deterministic (quantile-init GMM, no randomness).
  2. `_pre_prediction_prices(token_id, scored_ts)` fetches observations with `retrieved_ts <= scored_ts` from the attached read-only discovery store — the no-peeking rule applied to segmentation, not just to labels.
  3. Report schema `ahos.calibration_report.v5` adds `regime_segments` (same pre-registered guards as every other segment table); `dimension_availability["market_regime"]` documents the post-hoc computation honestly; CLI prints the regime table.
  4. Opportunity-type stays NOT_PERSISTED — no such concept exists in the scoring contract and the harness does not invent one.
- EVIDENCE: 3 new tests (helper guards/validity/determinism; coherent segmentation with honest UNKNOWN bucket; post-prediction crash observations ignored); targeted + drift/regime + pipeline regressions green; full suite 1261/1261 (gate artifacts refreshed). Zero live trading, zero credential exposure.

## R-68 · 2026-08-20 · Weight-governance acceptance tool: calibration diff (Month-3 roadmap)
- WHY: ROADMAP_v3 Month 3 requires "any weight change ⇒ calibration diff report attached to PR". The report schema existed but no tool could turn two artifacts into a reviewable, provenance-carrying diff.
- WHAT:
  1. `scripts/calibration_diff.py`: `build_diff(before, after)` loads two `ahos.calibration_report.vN` artifacts and emits `ahos.calibration_diff.v1`: verdict (COMPARABLE / NO_COMPARABLE_BANDS), per-band before/after n + rate + delta (after − before), monotonicity change, diagnostic deltas (base_rate, Brier, ECE, Spearman), and full provenance of both sides (dataset fingerprints, weight fingerprints, engine versions, eligible sources). Deterministic; exit 0 for an honest diff (including NO_COMPARABLE_BANDS), exit 2 for missing/unparseable artifacts.
  2. Honesty laws pinned by tests: bands compare only when both sides are DESCRIPTIVE_OK on the SAME horizon+event_class; identical dataset fingerprints ⇒ IDENTICAL_DATASETS and rate deltas are nulled (a code change on the same rows is not a data improvement); horizon mismatch ⇒ band comparison refused; mixed engine versions censused both sides.
  3. This is the acceptance tool the roadmap names for weight changes: a PR that changes scoring constants must attach a diff produced by this tool (the report's `weight_fingerprints`/`score_engine_versions` make the change visible even when both artifacts are INSUFFICIENT_DATA).
- EVIDENCE: 8 new tests (`tests/test_calibration_diff.py`); runtime-verified against the committed v5 artifacts and a fresh before/after pair (honest NO_COMPARABLE_BANDS, exit 0) with the evidence artifact committed; full suite 1269/1269 (gate artifacts refreshed). Zero live trading, zero credential exposure.
