# AHOS — Continuity Brief (decision set, not a recap)

Compiled 2026-10-08 (Asia/Tehran) by Grok Bot (executor). The laptop was read-only (`G:\robat\ahos` and the Grok Bot persistence folder). No secrets are quoted.
Purpose: let an assistant continue AHOS without making Mehrdad (the owner) re-explain decisions.
Conventions:
- Each decision line reads: ID · date (box-local/Tehran unless stated) · who decided · REQUIRES / FORBIDS · source.
- "Owner" means Mehrdad directly, or a document he authored or approved. "CoS" means the Chief of Staff agent acting "with full owner authority". "Grok" and "Claude" are the AI assistants. Agent names are Persian (roster in §C).
- Owner-directive parts 1/2 carry no dates; they are marked "undated (standing)".
- Reality ladder used throughout: VISION < DESIGN < PROPOSED < PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < ACCEPTED < OPERATIONAL < PRODUCTION-CAPABLE. **PLANNED ≠ DONE; CODE EXISTS ≠ OPERATIONAL.**
- Tonight's Sultan chat (2026-10-08) is not restated. Only a few facts from it appear in §5.

---

## 0. Authority / precedence (read first)

- **D-P01** · undated (standing) · Owner, Execution Mandate §3 · Decision priority:
  1. explicit, recent human order
  2. security / harm prevention
  3. provable repo + runtime reality
  4. Governance / TCB
  5. Lane A + Canonical Decision Authority
  6. evidence integrity
  7. independent verification
  8. current architecture
  9. MASTER CONTEXT
  10. AGI/ACI Charter
  11. Roadmap
  12. aesthetic / experimental ideas

  CURRENT REPOSITORY TRUTH > VISION CLAIM. CORRECTNESS > SPEED. SAFETY > FEATURE. (part2 Exec §3)
- **D-P02** · undated · Owner, part1 · Truth order: RUNTIME/REPO > VERIFIED EVIDENCE > TESTS > GOVERNANCE > DOCUMENTATION > VISION. (part1 header)
- **D-P03** · 2026-10-03 23:20 · گیتی (constitution agent) review, adopted into vision v1.6 · Trust order: human > repo > governance > evidence > Mission Control > Charter > Vision. Every vision section carries a [PROPOSED]/[PLANNED] header. Vision is NOT in DOC_TRUTH_MAP §A. (Arash chat; VISION header)
- **D-P04** · undated · Owner, part1 opening + §1 · REQUIRES continuing from the project's *real* stopping point. Everything already built is found, checked, validated, classified, compared, debugged, updated, matched, regression-tested and doc-synced. FORBIDS restarting from scratch, artificial reset, architecture reset, blind rewrite, or deleting evidence. ("از ابتدا شروع نکن… از دقیقاً همان جایی که پروژه در واقعیت متوقف شده است ادامه بده")
- **D-P05** · undated · Owner, part2 §159 · Grok handoff steps:
  - inspect the repo (`github.com/mainmovement/ahos`);
  - build a current-state map (implemented / tested / verified / partial / design-only / planned / missing / contradictory / unknown);
  - pick dependency-safe next missions.

  Do not make the human re-explain the vision. "This document does not grant the assistant authority."
- **D-P06** · 2026-08-13T04:55Z (= 09:25 Tehran) · Owner ratification · MASTER_DIRECTIVE_v1 is immutable. It changes only through v{n+1} + registry + AHOS_ISSUE_REGISTER (R-42, P29, tests/test_master_directive.py). Its 12-step wave protocol runs VERIFY WORKSPACE … CONTINUE. Its forbidden list: real money, LIVE, credential changes, breaking the Lane-A freeze, paid providers, irreversible deletion.
- **D-P07** · undated · Owner, part1 §114 / part2 §116 · The human is final governance authority. Proposal ≠ Policy; Capability ≠ Permission; Confidence ≠ Authority. Agents must never silently turn PROPOSAL into POLICY or AUTHORITY.
- **D-P08** · undated · Owner, part1 §8 · Non-mergeable distinctions:
  - Evidence ≠ Claim ≠ Hypothesis ≠ Prediction ≠ Observation ≠ Outcome ≠ Learning ≠ Promotion
  - Documentation ≠ Implementation ≠ Verification ≠ Acceptance
  - Simulation ≠ Execution; Paper ≠ Real
  - Unknown ≠ Safe; Stale ≠ Live; Rumor ≠ Fact
  - AI Opinion ≠ Evidence; Model Confidence ≠ Truth
  - Capability ≠ Permission
  - Agent Count ≠ Intelligence
  - Prompt ≠ Runtime
  - Test Pass ≠ Production Proof
  - AGI Label ≠ AGI
- **D-P09** · undated · Owner, part2 Mandate §28 · Full stop is allowed only when:
  1. everything is done and independently verified;
  2. a human governance decision is truly needed;
  3. a safety boundary forbids continuing;
  4. an external dependency is down with no fallback or parallel work;
  5. the human said STOP.

  Otherwise block only the blocked part and continue the rest (Mandate §3).
- **D-P10** · undated · Owner, part2 Exec §2 · Do not wait for the user to supply reports. Inspect the repo, branch, HEAD, commits and diffs yourself, then choose the bottleneck. Ask the user only for data or permission that cannot be obtained any other way.

---

## 1. Decision register

### A. Trading / safety

- **D-A01** · standing (MASTER_DIRECTIVE 2026-08-13; part1 §28/§91; part2 §19/§101; INV-01) · Owner · REQUIRES `PAPER_ONLY`, REAL TRADING = DISABLED, Real Money Movement = DISABLED. FORBIDS any AI, agent, model, Cursor process, Telegram bot or cognitive layer silently enabling real execution, real orders or fund movement. FORBIDS flipping Paper-Only to Live. (part2 Exec §11)
- **D-A02** · 2026-10-03 (vision v1.6) · Owner-approved vision · AUTONOMY_TIER_CURRENT = **T0 for all markets**. INV-01 keeps PAPER_ONLY until the T2→T3 gate.
- **D-A03** · 2026-10-03 23:21 (v1.6) · Owner-approved · T0–T4 replaces the older L0–L5 / G-L2 ladders.
  - T1: paper ≥6 months; signers owner + 16 + 19 + 03.
  - T2: shadow ≥3 months; owner + 16 + 19 + 03 + 11.
  - T3: ≤1% NAV or the owner's $ cap, per-trade human approval.
  - T4: 10% then 25%, quarterly re-sign.
  - Minimum ≥12 months to T4.
  - The AI may only **downgrade or halt**, never promote (INV-35: human-only promotion). (VISION §11.0)
- **D-A04** · undated · Owner, part1 §72 / part2 §81 · Execution permission ladder: Research → Paper → Backtest → OOS → Simulation → Limited Live → Controlled Autonomous. Execution path: Intelligence → Decision → Risk Governor → Permission → Execution. FORBIDS "Agent → Trade". (part1 §91)
- **D-A05** · undated · Owner, part1 §71 / part2 §83 · REQUIRES an independent Risk Governor enforcing exposure, leverage, loss, drawdown, liquidity, concentration, venue, volatility, emergency shutdown and kill switch. FORBIDS the trading engine disabling its own risk governor.
- **D-A06** · 2026-10-03 (vision; INV-05, INV-34) · Owner-approved · Golden rule: "LLM proposes, deterministic code decides". FORBIDS LLM output becoming an order, and any LLM in the order path. The Execution Gateway has no LLM (گیتی 23:20).
- **D-A07** · standing (part1 §44; vision §4) · Owner · One Canonical Decision Authority (single Python decision brain). UNKNOWN never counts as PASS. Telegram and any other surface must use it and must not create a second decision authority. (part1 §34)
- **D-A08** · 2026-09-15 · Chief Architect accepted the Agent-11 (رامین, risk) contract · Risk invariants: UNKNOWN ≠ LOW ≠ SAFE ≠ TRAPPED; no scalar risk score. Every risk result carries the headers `DECISION_MADE=NONE` and `AUTHORITY_USED=NONE`. Hazards: H1 fan-in without a shared evidence bar; H2 authority creep; H3 Plane D → live / Lane A; H-RI readiness inflation (S20-7). (Agent-11 chat)
- **D-A09** · 2026-10-03 · رامین (Agent-11) PROPOSED gate set, RI-RESULT-20261003-003, sent to the Chief Architect; status: proposal. Paper → next tier requires:
  - ≥6 months;
  - ≥3 of 4 regimes with ≥30 trades each;
  - ≥200 trades;
  - stress test at 2× slippage;
  - MaxDD ≤15% and ≤1.5× backtest;
  - Sharpe ≥1; DSR/PSR ≥0.95; PF ≥1.3;
  - no month >40% of profit;
  - walk-forward / OOS required;
  - the count resets on any breach.
- **D-A10** · 2026-10-03 · رامین PROPOSED · Leverage:
  - 1x/2x, hard cap 3x, isolated margin only;
  - liquidation distance ≥25% or 3×ATR;
  - risk ≤0.5% per position; gross ≤100%; cluster ≤25%;
  - shorts ≤50% of gross, with hard stops;
  - no shorts on illiquid or Agent-10-UNKNOWN assets.

  Owner standing rule: leverage is a variable, never a target, and extreme leverage is never hard-coded. (part2 §82)
- **D-A11** · 2026-10-03 · رامین PROPOSED · Kill switch:
  - −2% daily: no new entries;
  - −8% from peak: flatten + halt, restart by owner only;
  - halt on stale data, ledger mismatch, or USDT depeg >0.5%;
  - one-tap kill; flat in ≤60 s;
  - monthly fault injection.
- **D-A12** · 2026-10-03 · رامین PROPOSED · Capital tiers: paper → shadow → 1% → 10% → 25%, each ≥3 months. Auto-downgrade only, never auto-upgrade.
- **D-A13** · 2026-10-03 (vision §5) · Owner-approved vision · Risk:
  - Kelly fraction 0.10–0.25;
  - vol target 10%;
  - DD ladder −3/−5/−10/−15%;
  - kill switches.

  Where §5 and §11.0 differ, **the stricter value wins** (see C-06).
- **D-A14** · 2026-10-03 (INV-15) · Owner · $100 → $1M North Star is **aspirational, panel only** (NS-SANDBOX). The risk engine must never read it. The vision admits it would need Sharpe ≈15.
- **D-A15** · 2026-10-03 22:07 / v1.5–v1.6 · Owner confirmation · Mother Safety Fund (M32):
  - 20% weekly;
  - INV-18 / INV-25 exception: T4 only, owner-set whitelist, isolated key.
- **D-A16** · 2026-10-03 23:21 (v1.6, INV-36) · Owner · Withdrawals: **request-only**. The system builds a request and the owner executes it manually. Compounding by default; withdraw on request (OA-08, v1.2). FORBIDS autonomous withdrawal (replaces the earlier "Babak executes" text; see C-05).
- **D-A17** · 2026-10-03 23:20 · سپهر (security) review, adopted into v1.6:
  - no withdrawal keys on the machine;
  - apiRestrictions self-check;
  - broker-side withdrawal whitelist;
  - two-layer cap;
  - wincred prefix `AHOS/broker/`;
  - hash-chained ledger; nightly reconcile.

  Telegram approval must NOT repeat the old ahos_03 `/approve` bypass.
- **D-A18** · 2026-10-03 · رامین PROPOSED treasury:
  - each broker ≤40%;
  - trade-only API keys;
  - withdrawals to a whitelist only, from realized profit only, with a timelock and owner signature.
- **D-A19** · 2026-10-03 (INV-08) · Owner-approved vision · FORBIDS sanctions evasion (Iran). Legitimate routes include TSE/IME domestic markets. A venue_eligibility registry is required. Only PaperAdapter is active; BrokerAdapter stays an interface; extend `paper_trading/`.
- **D-A20** · 2026-10-03 (INV-26..30, OA-17 Token Hunter M33) · Owner · FORBIDS block-0 sniping, MNPI, hacking and market manipulation.
- **D-A21** · undated · Owner, part2 §5 / part1 §42 · **Token identity is a critical safety boundary.**
  - Never guess a contract address; symbol or name alone is insufficient.
  - Same symbol on several assets → IDENTITY = AMBIGUOUS.
  - Unresolved → DECISION = MONITOR_ONLY / UNRESOLVED, failing closed.
  - Execution Mandate §11 FORBIDS fabricating a contract or guessing an identity.
- **D-A22** · undated · Owner, part2 §50 · Initial phase: AHOS does not trade. The user may report his own positions (token, capital, entry). AHOS monitors them and suggests HOLD / MOVE STOP / SELL 25/50/100% / EMERGENCY EXIT, based on evidence and rules.
- **D-A23** · undated · Owner, part2 §79 · HFT is not the first objective. Ladder: fast data → order book → detection → paper → backtest → latency → limited real (after proof) → HFT / market making only if justified.
- **D-A24** · undated · Owner, part1 §49 / part2 §24–28 · Paper lifecycle: PROPOSED → APPROVED FOR PAPER → OPEN → MONITORING → EXIT TRIGGERED → CLOSED → OUTCOME → POST-MORTEM → LEARNING. Learn from wins, losses and skips. **A single success must never auto-promote.**
- **D-A25** · undated · Owner, part1 §46 · Security overrides Opportunity. FORBIDS: FOMO as an entry licence; social virality as evidence; UNKNOWN → SAFE; stale → live. (Exec §11)
- **D-A26** · undated · Owner, part1 addendum §16 · Gated operations always go AI proposal → policy gate → human approval → execute → verify → record:
  - delete DB
  - factory reset
  - destructive delete
  - unsafe security change
  - credential rotation
  - REAL TRADING
  - destructive infra change
  - irreversible data loss

### B. Data / infrastructure

- **D-B01** · 2026-10-02 18:49 · Owner · Remove n8n / Docker **safely**, with M10 before the launcher. (OWNER_DIRECTIVE_MISSION_PLAN)
- **D-B02** · 2026-10-03 13:09 · CoS "with full owner authority" · M10 = Docker / n8n removal. Owner goal "one icon, no Docker". v2's "Docker/DB up" becomes "native DB up". (Arash chat)
- **D-B03** · 2026-10-03 13:09 · CoS · DB: **native portable PostgreSQL**:
  - official zip, pg_ctl;
  - data dir outside git;
  - no Windows service, no admin;
  - bind 127.0.0.1.

  **SQLite rejected.** (Superseded in practice by D-B04; see C-01.)
- **D-B04** · after 2026-10-03 (D3, commit d80b5b7, parity 7ace415) · Grok decision recorded in the mission plan and continuation guide · M10 store = **embedded PGlite**, with native PG as fallback. Runtime path planned: `pglite:G:/robat/ahos_runtime/pglite/ahos`.
- **D-B05** · 2026-10-03 13:09 · CoS · Migration: pg_dump → restore → parity tests (row counts + checksums + tests). FORBIDS touching Docker volumes until owner approval. FORBIDS touching `reports/pgdump_*.sql`.
- **D-B06** · 2026-10-03 · آرش acceptance points for M10/M11:
  - inventory first with rg;
  - FORBIDS `docker volume rm` and `system prune`;
  - secrets move to wincred (GM-12, `wincred_reader.py`);
  - final grep finds no docker/n8n except under `archive/`;
  - delivery needs agents 16 + 19 + 05.
- **D-B07** · 2026-10-03 13:09 · CoS · n8n workflows are replaced by native Python with parity tests. A secret-stripped export goes to `archive/`.
- **D-B08** · 2026-10-07 · Owner (DECISIONS_LOG, QUEUE_DECISION_M10_blocked_owner) · M10 Stage 4 is **prepare-only, no flip**. Re-confirmed 2026-10-08.
  - The flip is an owner act: set `DATABASE_URL` to the PGlite path in `.env` and restart.
  - FORBIDS any assistant changing `.env` on the owner's behalf.
  - Status: BLOCKED_OWNER.
- **D-B09** · 2026-10-07 · DECISIONS_LOG · Also logged: fixed a `db/index.ts` ReferenceError; corrected the `/api/chat` smoke receipt; deliberately skipped `config/.env.template`; used a venv shim for `run_all_checks.sh`.
- **D-B10** · undated · Owner, part1 addendum §18 · Target is local-first: Windows host + AHOS runtime + local stores + Next.js dashboard + optional local AI + provider adapter + engineering core. Docker / PG / n8n may stay only as dev infrastructure, never a runtime dependency. Any migration requires backup + evidence + verification first.
- **D-B11** · undated · Owner, part1 §54 / part2 §35, §37 · Free-first → local → open source → free API → fallback. No single paid provider for a critical capability. No VPS, no cloud, no paid service assumed. Single user (part2 §95).
- **D-B12** · 2026-10-03 (vision §3) · Owner-approved · Data must be point-in-time and survivorship-free. External text is untrusted. Evidence grades A–D. A new factor needs t-stat ≥3.
- **D-B13** · 2026-10-03 13:09 · CoS environment notes:
  - 8 GB RAM; ports 3000/3500; proxy 10809;
  - production build, not `next dev`;
  - stop only launcher PID-file processes;
  - never kill unrelated claude/node.

  GROK_HANDOFF: port 3000 is unbindable (Hyper-V reserved range).
- **D-B14** · 2026-10-03 · M9 findings (mission plan) · Postgres was never live; SQLite was the de facto canonical store at M9 time. The paper loop is the highest-leverage node. CC-1 ControlPlane. Agents are buildable but not activatable.
- **D-B15** · standing (REMAINING_REALITY_REGISTER §17) · n8n is recorded as resolved by M10.
- **D-B16** · 2026-10-08 · Sultan chat (fact only) · Claude was told to finish the token identity resolver, using DexScreener + GeckoTerminal as independent sources (24,357 tokens seen by both).

### C. Agents / organization

- **D-C01** · undated · Owner, part1 §12 · Find and activate or integrate the 19 existing roles. Do not rebuild them blindly. If duplicates exist, no merge without a governance decision. If another taxonomy exists, **keep both, record provenance, build an explicit mapping. Silent merge forbidden.** The 19:
  1. Chief Orchestrator
  2. Reality Forensics
  3. Evidence Transport
  4. Security
  5. Identity
  6. Canonical Decision Audit
  7. Scoring Science
  8. Paper Trading
  9. Learning/Memory
  10. Calibration
  11. Cognitive AGI/ACI
  12. Windows Runtime
  13. Provider/Data
  14. Integration
  15. Frontend/UX
  16. Independent Verification
  17. Red Team
  18. Change Architecture
  19. Release Governance
- **D-C02** · undated · Owner, part1 §13 / part2 Mandate §7, §100 · Agent-01 = orchestrator, status FUTURE_NON_AUTHORITY_ROOT. It is NOT root of trust. FORBIDS Agent-01:
  - self-granting authority;
  - changing policy or governance;
  - declaring independent verification or self-approving;
  - enabling live trading;
  - bypassing the TCB or security;
  - turning capability into permission.
- **D-C03** · undated · Owner, part1 §14–15 · Lifecycle: REGISTERED → IDLE → DORMANT → WAITING_FOR_COMMAND → ACTIVE → MISSION_EXECUTION → WAITING_FOR_VERIFICATION → COMPLETED. No self-activation without valid authority. New agents only where architecturally needed; "Agent Count is not the goal". Each agent must define mission, boundary, capability, authority, tools, memory scope, evidence, verification, failure handling and metrics.
- **D-C04** · undated · Owner, part1 §16–20, §27, §29, §30, §32 · Required teams:
  - GitHub Intelligence;
  - Skill Intelligence;
  - AGI/ACI Architecture;
  - Frontier Technology;
  - Guardian / Supervision;
  - Gold Division with ≥18 named roles, incl. ≥2 guardians + ≥2 integrators;
  - an independent Accounting / Ledger agent;
  - a Credential / Identity agent (secure storage only, **no financial authority**);
  - News Intelligence.
- **D-C05** · 2026-10-03 20:43 · Owner approval · 18 new agents (#20–37) + the vision doc design. Roster:
  - Existing 1–19: آرش, سامان, سپهر, گیتی, عرفان, روشا, دانا, کامیار, نیما, تینا, رامین, کیمیا, آریا, رستم, پروانه, قاسم, پریسا, فرناز, رضا.
  - New 20–37: کوروش CIO, بهرام macro, زرین gold/oil, سارا US, لیلا EU, مهسا Asia, فرهاد futures, نگار news, بیژن chart, شیدا GitHub, سیاوش AGI/ACI, بابک treasury, داریوش execution, مریم compliance, هومن failure analysis, فرزانه dean, ژاله accounting, آیدا guardian.
- **D-C06** · 2026-10-03 22:07 (v1.5) · Owner · Agent #38 سروش (judge).
- **D-C07** · 2026-10-03 23:04 · **OWNER-APPROVED** · Agent #39 **کیان (Kian) = the Leader**.
  - Runs on Gemini, OWNER-CONFIRMED 23:07, via `gemini_chat.py`; the key lives in Windows Credential Manager under `AHOS/ai/gemini` (value never read or quoted).
  - Design: tools allowlist, K-1..K-10 tests, Kian audit store (v1.7).
  - **INV-32: the owner talks only to the Leader.**
- **D-C08** · 2026-10-03 23:47 (v1.7, OA-22) · Owner approved 23:44 · M44–M51 plus leadership constraints. M36.4 merged into M51.
- **D-C09** · 2026-10-03 (vision §2) · Owner-approved · Three lines of defense. Veto holders: رامین (risk), مریم (compliance), سپهر (security). A no-duplicates register.
  - Empty seats recorded: GH-2, SKILL-1..4, ACI-2..4, FRONT-1..2, GUARD-2, GOLD-SCI, GOLD-STRAT, CRED-ID, OSINT, SOCIAL.
  - **The two-taxonomy mapping is still UNRESOLVED.**
- **D-C10** · 2026-10-03 23:20 · گیتی review · New components:
  - Treasury Custodian
  - Kill-Switch Monitor
  - Execution Gateway (no LLM)
  - Market Adapters
  - Compliance Reviewer

  Governance uses T0–T4 with named signers. Decision records go in `docs/governance/decisions/`.
- **D-C11** · 2026-09-15 · Chief Architect order · Agent-11 must not open Agent-03/05/14 work orders itself; it escalates through the Chief Architect. Dual-19 deny-inheritance applies.
- **D-C12** · standing (Arash chat) · Post-merge dual review is Agent 16 VERIFY → Agent 19 CHALLENGE. Typical verdict: CLEARED_WITH_GAPS. Example: PRs #115 (tip 4b37be3) and #116 (tip 8ae411a).
- **D-C13** · 2026-10-03 (vision INV-41, OA-23, M52 Skill Marketplace) · Owner approved 23:57 · Skills carry **no authority**. INV-37..40 are the self-improvement guardrails.
- **D-C14** · undated · Owner, part2 §99 · The full chain Human → Agent-01 → Mission Controller → Specialist → Worker → TCB → Independent Verification → Acceptance → Memory is a **target** until runtime evidence proves it.

### D. UI / desktop

- **D-D01** · 2026-10-02 18:47 · Owner · **One desktop icon** is the final goal. Big missions, not micro-tasks. (mission plan)
- **D-D02** · undated · Owner, part1 addendum §19 · Double-click runs: env check → infra check → runtime → dashboard → health → AI-provider check → engineering check → READY. The user must never hand-manage Docker or n8n, open several terminals, or coordinate services manually.
- **D-D03** · 2026-10-03 13:09 · CoS · M11 = launcher, which consolidates the 6 existing launchers into the `launcher/` package.
- **D-D04** · 2026-10-03 · آرش acceptance for the launcher:
  - idempotent; has stop and status;
  - **refuses to run if a LIVE flag is set**;
  - reads the Telegram token only from wincred;
  - short Persian error messages;
  - desktop `.lnk` created by a separate, reversible script.
- **D-D05** · 2026-10-06 · Owner approval (OWNER_APPROVAL_20261006, continuation guide) · M11.1 / M11.2 approved. Queue later marks M11.1–M11.4 DONE.
- **D-D06** · standing (mission plan CH-01..09) · Owner style requirements:
  - no visible console windows;
  - a world-class dashboard;
  - short Persian replies;
  - visible mission stages;
  - no duplicates;
  - no push.
- **D-D07** · undated · Owner, part1 §35 / addendum §20–21 · The dashboard is a real command center. It shows system, DB, runtime, dashboard, agent-society and AI-provider health, plus current mission, task, progress, last evidence, last test, blocker and next action. **Never fake live state** ("Thinking", "Connected", debate). On quota exhaustion it must say in Persian that the provider credit ran out, the mission is paused, the checkpoint is kept, and it asks for a new key.
- **D-D08** · undated · Owner, part1 §36 / part2 §41–47 · Aesthetic direction: Wise Tree / roots / cognitive network / agent rooms / holographic / market maps. Saifullah Dev, Van Lent, Edolus, Igloo, Active Theory and Dreamwave are **references, not templates**. Visual excellence must rest on real intelligence (part2 §127).
- **D-D09** · 2026-10-03 (v1.2, OA-09) · Owner · Wealth panel. v1.3 adds the nightly report (M31).
- **D-D10** · 2026-10-08 · Sultan chat (fact only) · The owner wants a **desktop app window, not a browser tab**. A Chrome app-mode launcher change was proposed but not confirmed as built.
- **D-D11** · undated · Owner, part1 §34 / part2 §48–49 · Telegram is a secondary interface (chat, query, reports, alerts with evidence and context). It uses the same canonical authority. Bot: @Sun_sniperbot.
- **D-D12** · AD-0128 (date per handoff) · Telegram **sending is BLOCKED until the bot token is rotated**. Rotation is a gated owner act (D-A26).
- **D-D13** · 2026-10-02 17:35 (GROK_HANDOFF Phase 7b) · Owner scope change · Real conversational AI in the dashboard. Owner commands are confirm-gated with a 6-character code and a 5-minute TTL. Phase 8 = dev-mission intake.

### E. AI / council / provider

- **D-E01** · undated · Owner, part1 §47 / part2 §15–16 · The AI Council has 10 specialties:
  1. math
  2. crypto
  3. on-chain
  4. cyber
  5. OSINT
  6. news
  7. social
  8. software
  9. AI research
  10. strategy / red team

  Process: discovery → evidence → security → specialists → cross-exam → contrarian → debate → reconciliation → scoring → confidence → decision. **Majority vote is not truth.** Disagreement is information.
- **D-E02** · undated · Owner, part1 §48 · Contradiction intelligence: THESIS → ANTI-THESIS → EVIDENCE FOR / AGAINST → UNRESOLVED → FINAL CONFIDENCE. Never delete a contradiction. (Exec §11)
- **D-E03** · undated · Owner, part1 addendum §8–9, §17 · Provider states: READY, DEGRADED, UNAVAILABLE, QUOTA_EXHAUSTED, AUTH_FAILED, MODEL_UNAVAILABLE, BLOCKED.
  - On quota exhaustion: PAUSE, record the reason, request user action; never crash, never restart the mission.
  - The Credential Manager validates and health-checks a new key, then resumes.
  - FORBIDS guessing, extracting or self-creating keys.
  - External AI must not be a single point of failure; tasks that need it go WAIT_FOR_AI.
- **D-E04** · 2026-10-03 (v1.6, M37) · Owner-approved · Frontier model slots. GPT-6 Astra listed at $10/$50; Gemini 4 Argon noted as not public. Planned, not built.
- **D-E05** · 2026-10-04 00:01 · Owner order (CLAUDE_AUTOPILOT_QUEUE) · If Grok is disconnected, **Claude continues the queue one mission at a time** (claude_autopilot.ps1, run_mission.ps1, watchdog).
- **D-E06** · 2026-10-07 08:22 · Grok hold (HOLD.flag) · Autopilot held because the owner's interactive Claude was doing M10, to avoid a double run. The heartbeat showed INTERACTIVE_CLAUDE.
- **D-E07** · 2026-10-08 · DECISIONS_LOG · The runner was repaired to classify quota and model failures as INFRA, not mission failure. M12 was reset to PENDING / NEEDS_REVIEW, **not DONE**.
- **D-E08** · 2026-10-03 (v1.3, OA-11..16) · Owner · Approved:
  - Arena (M28)
  - Crisis Simulator (M29)
  - multi-layer mind (M15.6–11)
  - memory (M30)
  - nightly report (M31)
  - Mother Safety Fund (M32)
- **D-E09** · 2026-10-03 (v1.5, OA-18) · Owner · Coherence audit (M34) + Leader + autonomous world (M36). Competitive analysis M33.16–24.
- **D-E10** · undated · Owner, part1 §9 / part2 §18–20 · Architect for AGI/ACI-like domain-general cognition, using the measurable cognitive loop PERCEIVE → … → PROMOTE/REJECT. **Never claim real AGI** because of agent count, prompts, UI or names (Exec §11).
- **D-E11** · undated · Owner, addendum §14 / part2 §56 · Controlled autonomous evolution, never unrestricted self-modification. Self-improvement may not rewrite Lane A (part2 §57).

### F. University

- **D-F01** · undated · Owner, part1 §21–26, §92–95 · The AHOS University is a **permanent institution**. It covers research, problem solving, error learning and continuous learning; it integrates with engineering and holds a global benchmark; the dashboard shows it. (Sections read by heading only; body not read in full.)
- **D-F02** · 2026-10-03 20:20 (v1.1) · Owner · University continuous-learning engine. 18 agent charters rewritten.
- **D-F03** · 2026-10-03 (vision §8) · Owner-approved · Faculties, plus a certification ladder L0–L4. Dean = فرزانه (#35). §8.3 details not read.
- **D-F04** · undated · Owner, part1 §98–99 · Research → Skill → Agent pipeline. Skills carry no authority (INV-41).

### G. Markets beyond crypto

- **D-G01** · undated · Owner, part1 §69 / part2 §2, §80, §93 · Expansion order: Crypto → Gold → Forex → EU equities → Asian equities → US equities → Oil → Macro.
  - Roadmap phases: 1 token discovery; 2 advanced paper; 3 automated token trading (after evidence); 4 automated crypto; 5 chart intelligence; 6 gold; 7 forex.
  - **Foundation first**: multi-market must never destabilize Phase 1 (part2 §94).
- **D-G02** · undated · Owner, part1 §27–28 · Gold Division (D-C04). The architecture must be ready for live gold trading, but stays PAPER_ONLY until the full gate list passes:
  - governance, Risk Governor, permission
  - security, credential security
  - broker/API verification
  - backtest, OOS, simulation, paper
  - independent verification
  - kill switch, exposure / loss / DD limits, emergency shutdown
  - audit
- **D-G03** · 2026-10-03 · D4 (mission plan) · Gold-paper work lives **inside M13** (gold-first paper). No separate mission.
- **D-G04** · 2026-10-03 (vision §2, §6) · Owner-approved · Agents for macro (بهرام), gold/oil (زرین), US (سارا), EU (لیلا), Asia (مهسا), futures (فرهاد). TSE/IME domestic routes are legitimate (INV-08).
- **D-G05** · 2026-10-03 (v1.2 OA-10, M42/M43 etc.) · Owner · Playbooks + regime rotation. Market Adapters component (گیتی). Not built.

### H. Process / git / missions

- **D-H01** · 2026-10-03 · Owner HARD LAW (via CoS 13:09; mission plan "Decisions 2026-10-03") · **Search existing repo code first and extend it. Duplicate or parallel modules are forbidden.**
- **D-H02** · 2026-10-03 13:09 · CoS mandatory routine for every Claude mission (repo `G:\robat\ahos`, local commit only, no push, PAPER_ONLY):
  1. Before: آرش + the domain specialist review the prompt, پروانه refines it, گیتی checks the constitution.
  2. During: each part goes to its domain agent (سپهر security, سامان system, رامین risk, دانا data, کیمیا quant, فرناز/پریسا dashboard, رستم runtime).
  3. Delivery: قاسم QA + رضا red team + عرفان evidence. No completion without all three.
- **D-H03** · 2026-10-03 (vision §14.0) · Owner-approved · SP mission protocol: SP-1 prompt review → SP-2 search-first → SP-3 build → SP-4 tests → SP-5 evidence → SP-6 sign-off.
- **D-H04** · standing · INV-04 + Arash chat + CHs · **No push.** Pushes paused since 2026-10-02 14:52 (GROK_HANDOFF). **No bot-merge**: mainmovement merges.
- **D-H05** · standing · continuation guide · Commit rules:
  - stage explicit paths only;
  - never touch `.cursor/hooks.json` or `ahos-guard.py` (also part1 §105: preserve the fail-closed preToolUse guard);
  - `scripts/store_ai_key.py` is an untracked owner script: **never commit, edit, or run it**.
- **D-H06** · standing (INV-03; scripts/freeze_lane_a.py) · **Lane A frozen** (`discovery/**`, `paper_trading/**` per freeze script); Lane B is where changes happen. Note: the vision also says "extend paper_trading/" (see C-10).
- **D-H07** · undated · Owner, part1 §58–60 / part2 Mandate §20–21, Exec §10 · Loop: INSPECT → MODIFY → TEST → DIFF REVIEW → REGRESSION → VERIFY → COMMIT (→ push / merge only if authorized).
  - Commit body: area / Why / Tests / Verification / Risk.
  - FORBIDS force-push, destructive reset/rebase, deleting tests, weakening asserts, fake fixtures, rewriting evidence, hiding failures.
  - Push blocked → record `PUSH_BLOCKED_EXTERNAL`, keep commits, continue. MERGE ≠ PROOF.
- **D-H08** · standing (Arash chat) · Banned claims: readiness, PROMOTE, "D1/07 closed", AGI, rewriting a past SHA as green.
- **D-H09** · 2026-09-30 · CoS · Next mission at that time: remove the deprecated `compose_evidence_graph(dossier=)` shim. Cloud Agent was blocked on Cursor quota, so the sunsniper98-ctrl fork + gh path was used. Leave PR #105 alone.
- **D-H10** · 2026-10-03 13:09 · CoS · Order: finish **M9.6 security → M10 (Docker/n8n removal) → M11 (launcher)**.
- **D-H11** · undated · Owner, part1 §56–57 · Repo copies exist:
  - ahos-push-staging
  - ahos022
  - ahos-agent-org
  - `G:\n8n\AHOS`
  - `G:\home\user\ahos`
  - ahos-transfer
  - AHOS_BACKUP_2026-08-19
  - ahos-grok

  None is canonical by name; git identity decides. Forensic reports are evidence, not authority. Preserve the 3D / upload / web / presentation trees.
- **D-H12** · undated · Owner, part2 §102 · Windows claims need Windows evidence. Do not start or declare an official soak just because a daemon runs.
- **D-H13** · 2026-10-03 (INV-02) / part1 addendum §9 / part2 §108–109 · No secrets in code, git, docs, logs, evidence, chat or prompts. Use wincred.
- **D-H14** · 2026-10-08 · GROK_HANDOFF · Blocker A / GM-01 RESOLVED. The `isLoopbackRequest` guard was restored (b9eba89). The `source-map-js` bump is still open (the npm install was classifier-denied).

---

## 2. Open contradictions (each stated once, with both sides)

- **C-01 DB store.** Side 1: CoS "with full owner authority", 2026-10-03 13:09 (Arash chat) — native portable PostgreSQL; SQLite rejected. Side 2: Grok D3 (mission plan; continuation guide; queue M10) — embedded PGlite, PG as fallback. The owner has twice declined to flip to PGlite (10-07 and 10-08, QUEUE_DECISION_M10). Side 3: part1 addendum §18's target diagram shows "SQLite / Local Stores". The owner has not chosen explicitly.
- **C-02 Is live trading ever allowed?** Side 1: REMAINING_REALITY_REGISTER §33 says live trading is "ABSENT BY CONSTRUCTION, permanently prohibited", with 4 enforcement layers. Side 2: Owner-approved vision (OA-01, OA-04, T0–T4) and part1 §28/§91 / part2 §81 plan an owner-gated path to limited live trading.
- **C-03 Mission numbering drift.** OWNER_DIRECTIVE_MISSION_PLAN's original M9–M18 definitions give M10, M11 and M12 different meanings from the 2026-10-03 re-numbering (M10 = Docker/n8n, M11 = launcher) and from vision §13 (M12–M52).
- **C-04 Agent count.** The queue's M12 row says "37+ agents"; vision v1.6 says 39; the code registry has 25 (DECISIONS_LOG 10-08).
- **C-05 Withdrawals.** Pre-v1.6 vision text: the system withdraws / بابک executes. v1.6 INV-36: request-only with manual owner execution, plus the mother-fund exception (T4, whitelist, isolated key). Treat v1.6 as current; the old text has not been removed everywhere.
- **C-06 Risk caps.** Vision §5: −15% DD kill, 25% per venue. §11.0 / رامین: −8% from peak flattens, 40% per broker. The vision says the stricter wins, but the numbers are still not reconciled in the text.
- **C-07 OWN-6 / OWN-7.** Recorded HUMAN-GATE contradictions in the mission plan traceability: OWN-6 (autonomy level) and OWN-7 ("live for all" markets) conflict with PAPER_ONLY / T0. They need an owner ruling.
- **C-08 GM-04 owner-authority change.** Pending review by سپهر / قاسم / رضا; unresolved.
- **C-09 Two taxonomies.** part1 §12's 19 functional roles vs the persona roster (آرش… رضا). The mapping is UNRESOLVED (vision §2), and Dual-19 is BLOCKED on it. Silent merge is forbidden.
- **C-10 Lane A vs "extend paper_trading/".** Lane A freeze covers `paper_trading/**` (freeze_lane_a.py), but vision §6 says to extend `paper_trading/` with adapters, and M13 needs `run_full_cycle` wired. The governance path for touching it is not stated.
- **C-11 Push / merge autonomy.** part2 Execution Mandate §2 tells the assistant to commit, push and merge itself. Current rules (INV-04, CoS routine, Arash chat, CH) say local commit only: no push, no bot-merge, mainmovement merges. Pushes have been paused since 2026-10-02 14:52.
- **C-12 "Never a trading bot" identity vs Token Hunter / automated trading phases.** part1 §6 / part2 §1 say AHOS must not be merely a trading bot. Roadmap Phases 3–4 (automated token / crypto trading) and OA-17 Token Hunter M33 are trading-centric. This is reconcilable (identity vs capability) but is frequently cited on both sides.

---

## 3. Built vs paper (only where a source gives evidence)

- **Built / verified**
  - M11.1–M11.4 launcher steps: DONE (queue). The owner approved M11.1–11.2 on 10-06.
  - M10.1, M48.1, M54, BL: DONE (queue).
  - PGlite store code + parity: commits d80b5b7, 7ace415 (mission plan D3). **Not switched on**; the flip is the owner's act.
  - pytest at the M10 decision: 2932 passed, 1 failed, 4 skipped (QUEUE_DECISION_M10).
  - `isLoopbackRequest` guard restored (b9eba89). Blocker A / GM-01 resolved 10-08.
  - PR #115 / #116 merged with dual review CLEARED_WITH_GAPS. Ungated census ZERO (forge IDLE). Reality Map 0.1.16/0.1.17.
  - Kian runtime path: `gemini_chat.py` with a wincred key (vision v1.6). Existence is cited by the vision; I did not run it.
  - Autopilot runner (claude_autopilot.ps1, run_mission.ps1, watchdog, HOLD.flag, heartbeat, state.json): exists and in use.
- **Partial**
  - Paper trading: §7 PARTIAL. All tables have 0 rows and `run_full_cycle` is not wired; 0/30 closed exits (REMAINING_REALITY_REGISTER).
  - Labels: 508 of 22,285.
  - Traceability (mission plan): 594 requirements — 73 implemented+tested, 417 exists-partial, 13 planned, 68 missing, 18 human-gate, 5 unknown.
  - Telegram bot exists; sending is blocked pending token rotation (AD-0128).
  - Identity resolver: in progress tonight (DexScreener + GeckoTerminal overlap, 24,357 tokens).
- **Paper only (design, no code)**
  - Vision §0 baseline: 0 paper rows, no gold code, no treasury; 19 agents without runtime.
  - Agents #20–39 are design only, apart from the Kian chat path.
  - T1–T4, Treasury Custodian, Kill-Switch Monitor, Execution Gateway, Market Adapters, Mother Fund, Token Hunter, Arena, Crisis Simulator, Skill Marketplace, frontier slots, university engine: all [PROPOSED]/[PLANNED].
  - Live trading: absent (D-A01).
  - The full Human → … → Memory chain is a target (part2 §99).

---

## 4. Next unfinished engineering work (project's own order)

Sources: CLAUDE_AUTOPILOT_QUEUE, vision §14.7 / §14.10.4, REMAINING_REALITY_REGISTER critical path.

0. **Currently on: finish the token identity resolver** (Claude, 2026-10-08). Register follow-up: persist identity resolution.
1. **M12**: re-run. Reset to PENDING/NEEDS_REVIEW 10-08; the agent count is disputed (C-04).
2. **M34** coherence audit.
3. **M13** gold-first paper. Includes wiring `run_full_cycle` until ≥30 closed paper exits (register critical path: pre-soak → paper loop → labels → calibration → live decisions → soak). Gold-paper lives here (D4).
4. **M42, M43.**
5. **M35.1, M35.2, M35.4, M35.5** (Kian stages + K tests). M35.3 is BLOCKED_OWNER.
6. **M47 → M44 + M49 → M46 / (M45 BLOCKED_OWNER) / M48 → M52 → M50 → M51.**
7. **M37 → M41 → M39 → M38 → M40.** The mission plan's v1.6 order lists M42, M43 → M41 → M39 → M38 → M40.
8. **M14–M33, M55, M56, M57, M58.1–6, M59.1–5, M36, M53.**

Dependency-safe side items from the register: CC-3/CC-4/CC-5 fixes, CC-1 ControlPlane, the `source-map-js` bump (needs an approved npm install).

**Owner-blocked (do NOT do on his behalf):**
- M10 flip (`DATABASE_URL` in `.env`);
- M35.3, M45;
- Telegram token rotation;
- Docker volume removal;
- any push;
- choosing among C-01 / C-02 / C-07.

---

## 5. Notes from tonight (fact-only, from the Sultan chat; not restated)

- The owner judged the previous summary to be ~1% of the decisions. This file is the replacement.
- The owner wants a desktop app window (D-D10). The identity-resolver work is in progress (D-B16).

---

## 6. Source index

Laptop machine `85216a69-bff0-4528-a382-56b0cdfb7a26` (DESKTOP-DH7QOCK). All reads were read-only.

**Grok Bot persistence** — `C:\Users\Sniper\AppData\Roaming\Grok Bot\sand-client-persistence\` (blob names are base32 slice keys):

| Blob | Size | Chat? | Contents / read status |
|---|---|---|---|
| `…transcript.replicas.09241e18-139f-4fbb-8136-953b6c3691aa` | 24,715 B | Chat | رامین / Agent-11 Risk Intelligence, 2026-09-15 → 10-03. Read fully. |
| `…transcript.replicas.2ede3ba5-5bfa-49c3-8296-35142ae32402` | 96,002 B | Chat | آرش / Chief Architect, last 100 entries (seq ~1050–1150), 2026-09-24 → 10-03. Parsed fully. |
| `…user_01M4967ZT4JQ8K6JG8MH7J8JP5…transcript.replicas.7a6892b9-d93f-46e5-af00-ba93cc557006` | 31,644 B | Chat | Tonight's Sultan chat. Skimmed; not restated. |
| ui-layout | 145 B | No | |
| account-slot | 75 B | No | |
| export-policy ×2 | 50 B | No | |
| composer-draft 68bc03cf | 353 B | No | Draft "چه خبر از کار؟" |
| client capabilities ×2 | 154 B | No | |
| sidebar rows | 39 B / 1,200 B | No | |
| active-agent ×2 | 78 B | No | |
| records ×2 | 42 B | No | |
| sections ×2 | 43 B | No | |
| pinned | 168 B | No | |
| onboarded | 46 B | No | |
| .migrated-from-local-storage | 24 B | No | |

**Owner directives** — `G:\robat\ahos\docs\owner_directives\`:
- `owner_directive_part1.txt` (97,155 B, 4,644 lines). Master Autonomous Execution & Completion Directive §1–119 + addendum §1–29.
  - Read: §1, §6–9, §12–15, §27–31, §34–36, §47–49, §54–60, §69–72, §91, §105, §114; addendum §8–9, §15–21, §28–29.
  - All other sections: headings only.
- `owner_directive_part2.txt` (146,676 B, 7,198 lines). MASTER CONTEXT v2.0 §0–160 + Completion Mandate §1–36 + Autonomous Master Execution Mandate §1–16.
  - Read: §1–2, §5, §37, §48–50, §57, §79–83, §93–95, §98–102, §116, §127, §159; Mandate §3, §7, §19–21, §28; Exec §2–3, §10–11.
  - All other sections: headings only.

**Repo docs** — `G:\robat\ahos\` (exact subfolders as found):
- `AHOS_AUTONOMOUS_VISION.md` (384,527 B, 2,810 lines, v1.8).
  - Read: header, version history, §0–§1, §2 roster/defense, §3–§7, §8 outline, §10–§13, §14.0, §14.7, §14.9, §14.10.4, §16.
  - NOT read: §2.3.3 charters (lines 184–405), §4.5–4.6, §8.3, §9, §14.1–14.6, §14.8, §14.10.1–3, §14.11 details, §15.
- `DECISIONS_LOG.md`: read fully.
- `CLAUDE_AUTOPILOT_QUEUE.md`: read fully.
- `OWNER_DIRECTIVE_MISSION_PLAN.md` (690 lines): read lines 1–500 and 610–690; lines 501–609 not read.
- `GROK_HANDOFF.md` (1,470 lines): partial — lines 1–100, 300–314, 526–545, 626–802, 1085–1109, 1199–1234, 1417–1452.
- `CLAUDE_CONTINUATION_GUIDE.md` (1,328 lines): partial — lines 1–224, 805–885, 1288–1328.
- `REMAINING_REALITY_REGISTER.md` (701 lines): partial (critical path, §7, §17, §33, next missions, CC-1..5).
- `MASTER_DIRECTIVE_v1.md` (3,674 B): read fully.
- `OWNER_VISION_REGISTRY.md` (2026-09-12): North Star, 8-stage roadmap, P0–P4, constraints, model pool.
- `OWNER_ACTION_REQUIRED.md` (2026-08-27): OA-MERGE, OA-PG, G1–G11.
- `OWNER_APPROVAL_20261006.md`.
- Autopilot `HOLD.flag`, heartbeat, `state.json`, `QUEUE_DECISION_M10_blocked_owner.md`.

**Found but NOT read:**
- docs/supervision/AHOS_VISION_ALIGNMENT_AUDIT.md
- AHOS_AGENT_SUPERVISION_COUNCIL.md
- SUPERVISION_ARCHITECTURE.md
- protocols/AGENT_SUPERVISION_PROTOCOL.md
- OWNER_DIRECTIVE_TRACEABILITY.md (177 KB)
- ALL_DOCS_TRACEABILITY.md (526 KB)
- ALL_DOCS_ADD_v13–v18
- UNIVERSITY_AND_AGENTS_DISCOVERY.md
- M10_STAGE4_FLIP_RUNBOOK.md

**Incidental side effect:** two oversized command outputs were spilled by the remote tool into laptop temp/tool files (`agent-tools\a1b98534…txt`, `terminals\787107.txt`). These are tool artefacts, not intentional writes; nothing was written under `G:\robat\ahos`.

---

## Pass 2 — new decisions, corrections, contradictions (appended 2026-10-09)

Only items NOT already captured in Pass 1. IDs continue per theme with a "2" prefix (e.g. D-A2xx). Sources: `P1` = `G:\robat\ahos\docs\owner_directives\owner_directive_part1.txt`, `P2` = `...\owner_directive_part2.txt` (both undated, standing owner voice); `RG\` = `G:\robat\ahos\reports\grok\`.

### P2.1 Owner directive part 1 — previously heading-only sections

**Documentation / memory / process**
- **D-H201** · undated · Owner (P1 §2) · REQUIRES CODE ↔ TEST ↔ RUNTIME ↔ DOCS ↔ EVIDENCE ↔ MEMORY ↔ ARCHITECTURE to stay in sync. Old debug/audit/gap/issue registers, truth maps and test reports must be updated, not abandoned. A new agent must reach the registry; a capability change must reach the Truth Map; a fixed bug must reach Failure Memory / Debug History. FORBIDS new code with stale docs (and vice versa), and new tests with old reports.
- **D-H202** · undated · Owner (P1 §3) · REQUIRES every mission, research, experiment, debug, architecture/agent/skill/provider change, test or failure to be documented with: date, time, timezone, mission ID, goal, reason, prior state, evidence, files inspected/changed, commands, tests, results, failures, root cause, fix, verification, unknowns, risks, dependencies, governance status, commit/push/merge status, runtime status and next action. Docs are categorized Organizational Memory, written so any successor (Claude, GPT, Gemini, Grok, Atria, a human) can continue without restarting.
- **D-E201** · undated · Owner (P1 §4) · Use the strongest available model/mode, chosen by *measured* capability (context, reasoning, tools, coding, cost), never by name. "Capability must be measured, not assumed." Run a capability preflight before assigning Atria or other models a role. Model name grants no authority.
- **D-E202** · undated · Owner (P1 §5) · Atria's 100M-token budget is research capital: use it for deep research, codebase analysis, cross-checks, council review and contradiction detection, never aimlessly. Token Budget ≠ Authority; Model Opinion ≠ Evidence.
- **D-E203** · undated · Owner (P1 §10) · A world model covers markets, assets, chains, exchanges, whales, liquidity, narratives, macro, regulation, events, causality, uncertainty and provenance. Every datum is labelled Observation / Inference / Hypothesis / Prediction / Causal Relation / Unknown / Contradiction.
- **D-C201** · undated · Owner (P1 §11) · Agents must not be just prompts. Important agents gradually gain specialization, memory, methodology, prediction and error history, calibration, evidence preferences, failure memory and performance metrics. They must be able to disagree, hypothesize, test and self-evaluate.

**Teams (specifics beyond D-C04)**
- **D-C202** · undated · Owner (P1 §16) · GitHub Intelligence team of ≥2 dedicated agents. Each repo is assessed on architecture, license, activity, maintenance, tests, security, dependencies, performance, docs, community, relevance, integration cost and risk. Method DISCOVER → LICENSE → INSPECT → COMPARE → TEST → ADAPT → VERIFY; FORBIDS COPY.
- **D-C203** · undated · Owner (P1 §17) · Skill Intelligence team of **four**: discover → evaluate → security review → sandbox → benchmark → adapt → integrate → verify. Existing skills are reviewed too. FORBIDS a skill entering production blindly.
- **D-C204** · undated · Owner (P1 §18) · AGI/ACI Architecture team of **four**. Guiding question: "how does AHOS get smarter, not just bigger?"
- **D-C205** · undated · Owner (P1 §19) · Frontier Intelligence team: continuously study what others built that is ahead of AHOS ("AHOS must not fall behind"). Adoption only after evidence and test.
- **D-C206** · undated · Owner (P1 §20) · An independent Guardian / Supervision team checks every agent: mission done, boundary, evidence, hallucination, self-verification, authority escalation, tool misuse, docs updated, failures logged, skill use, Charter fit, governance bypass. FORBIDS it being just a status dashboard; it must really verify and monitor.

**University (new detail beyond D-F01..F04)**
- **D-F201** · undated · Owner (P1 §21–22) · The University is a real research and learning ecosystem, not a decorative page. It hosts dozens of professor and student agents plus research, reviewer, experiment, benchmark, scientific-method, failure-analysis, skill/AI/trading/security/architecture/AGI research agents. Topics: crypto, gold, oil, futures, US/EU/Asia stocks, forex, macro, AI/AGI/ACI, security, low latency, data engineering, agent architecture, cognitive science, world models, memory, reasoning.
- **D-F202** · undated · Owner (P1 §23) · University → engineering pipeline: RESEARCH → HYPOTHESIS → EXPERIMENT → RESULT → VALIDATION → ENGINEERING PROPOSAL → TEST → INTEGRATION → VERIFICATION, handed to the engineering group. FORBIDS any research entering the system without verification.
- **D-F203** · undated · Owner (P1 §24) · Any agent with a question, problem, failure, ambiguity or research gap can consult the University. The answer returns to that agent and to Organizational Memory.
- **D-F204** · undated · Owner (P1 §25) · Failure-learning chain: Failure → Root Cause → Architectural / Process cause → Test / Governance / Memory gap → Prevention → New Test → Learning.
- **D-E204** · undated · Owner (P1 §26) · Self-improvement must run WEAKNESS → HYPOTHESIS → CANDIDATE → SANDBOX → HISTORICAL TEST → OOS → ADVERSARIAL → REGRESSION → COMPARISON → INDEPENDENT VERIFICATION → GOVERNANCE → PROMOTE/REJECT. FORBIDS SELF-MODIFY → TRUST SELF → PROMOTE.

**News / crypto / security / decision rules**
- **D-G201** · undated · Owner (P1 §32–33) · The News division covers crypto, gold, oil, futures, US/EU/Asia, forex, macro, AI, security, GitHub and research. Every item carries source, timestamp, originality, reliability, contradiction, relevance, impact and freshness. News may trigger detection, risk, research, re-evaluation, exits or monitoring. FORBIDS news auto-becoming fact. News ≠ evidence of profitability; News ≠ automatic buy signal.
- **D-A201** · undated · Owner (P1 §41) · Crypto scope: Solana, BNB, Base, Ethereum and other chains; new / prelaunch / under-discovered tokens. Allowed sources: DexScreener, DEXTools, GeckoTerminal, pump.fun, free APIs, Telegram, X, TikTok, Instagram, web, GitHub. Source reliability must be recorded.
- **D-A202** · undated · Owner (P1 §43) · Security checklist: honeypot, sellability, black/whitelist, mint, freeze, upgradeability/proxy, tax/fees, max tx/wallet, trading controls, LP ownership/lock/removal, holder/insider/deployer concentration, bundled/related wallets, developer and contract history. States: PASS / UNKNOWN / INCOMPLETE / FAIL.
- **D-A203** · undated · Owner (P1 §44) · Preserve **AHOS-CANONICAL-DECISION-v1** rules:
  - one market source → UNRESOLVED;
  - unresolved pool → MONITOR_ONLY;
  - AI challenge may downgrade but **never upgrade ENTER**;
  - security overlay-v2 PASS required;
  - UNKNOWN → INCOMPLETE;
  - missing `pair_created_ts` → fail closed;
  - GoPlus missing honeypot → None;
  - no OPERATOR / PRODUCTION / LAUNCH readiness without required Windows evidence.
- **D-A204** · undated · Owner (P1 §45–46) · The funnel (1000→500→100→20→5→1) is illustrative, not fixed architecture. **NO TRADE / SKIP with zero opportunities is a valid result.** HIGH OPPORTUNITY + CRITICAL SECURITY RISK never trades. VIRAL ≠ VALID; INFLUENCER ≠ EVIDENCE; ENGAGEMENT ≠ VALUE.
- **D-E205** · undated · Owner (P1 §50–51) · Master learning loop: DISCOVER → ANALYZE → DECIDE → PAPER → MONITOR → RESULT → POST-MORTEM → LEARN → UPDATE → RETEST → IMPROVE. Metrics to define precisely: paper PnL, win/loss, average return/loss, drawdown, accuracy, FP/FN, calibration, per-agent/model/security/novelty/prediction performance, latency, cost, reliability. FORBIDS "99.9%"-style numbers without measurement.
- **D-E206** · undated · Owner (P1 §52–53) · AIProvider + ModelRegistry + Capability Registry + Performance History + Routing / Fallback Policy. **FORBIDS a hard-coded model list**; models earn trust from measured performance. Independent providers: market data, blockchain, news, social, AI, security, weather, exchange. Provider failure ≠ system failure (fallback → local → graceful degradation → offline test).

**UI**
- **D-D201** · undated · Owner (P1 §37–40) · Wise Tree mapping (if kept):
  - Roots = data sources; Soil = internet/GitHub/chain/markets;
  - Rocks = errors / blocked APIs / bad models;
  - Water = knowledge; Groundwater = deep knowledge; Ocean = collective intelligence;
  - Trunk = core architecture; Branches = teams; Leaves = collectors;
  - Fruit = opportunities; Golden Fruit = exceptional ones.

  Growth and all visuals must follow real system events and state (no fake animation). The environment engine uses real location, weather, timezone and day/night; FORBIDS trusting device time unverified. Performance + accessibility + correctness + security + clarity outrank beauty.

**Testing / review / verification (P1 §61–68)**
- **D-H203** · undated · Owner (P1 §61) · Test standard, where relevant: unit, integration, regression, import safety, filesystem mutation, security, malformed input, boundary, persistence, recovery, worker, subprocess, CLI, frontend typecheck, lint, build, selftest, adversarial, Windows-specific, runtime smoke, E2E, negative controls, reproducibility. **Skip ≠ Pass.**
- **D-H204** · undated · Owner (P1 §62) · Red-team every important capability with: positive, negative, boundary, malformed, corrupted state, replay, duplicate messages, race, restart, crash, timeout, disconnect, stale/forged evidence, identity mismatch, authority escalation, capability confusion, self-verification, unauthorized mutation, import/filesystem/network side effects, secret leakage, partial commit, recovery failure.
- **D-H205** · undated · Owner (P1 §63) · Five review passes on every important change: 1 Engineering, 2 Security, 3 Epistemic, 4 Architecture, 5 Critique the critiques (was a review wrong or over-conservative? is there a simpler, safer path? style vs real blocker?). Repeated as "multi-stage critique" in P2 Exec §7.
- **D-H206** · undated · Owner (P1 §64–65) · Trusted Command Boundary chain: Envelope → Session → Principal → Capability → Policy → State Validation → Transaction → Audit → Projection. **Caller-supplied maturity or capability claims are never authoritative.** Independent verification needs independent identity, authority, execution path, evidence and checks; self-check ≠ IV.
- **D-E207** · undated · Owner (P1 §66–68) · Organizational Memory holds accepted knowledge, failed missions, methods, agent performance, contradictions, decisions, verification, architecture history, hypotheses, experiments, postmortems; memory must not bypass evidence or governance. Failure chain: Incident → Root Cause → Impact → Failed Assumption → Control → Remediation → Regression → Lesson → Memory. Self-diagnostics cover collector, API, data quality, scoring, model, DB, Telegram, web, scheduler, memory, provider disagreement, identity mismatch, stale data, missing evidence: DETECT → RECORD → ANALYZE → PROPOSE FIX → TEST → VALIDATE → DEPLOY → MONITOR.

**Research / reality / planning (P1 §73–90)**
- **D-H207** · undated · Owner (P1 §73–75) · Every research item records Problem → Evidence → Failure modes → Cost → Baseline → Test → Rollback → Threats. OSS: DISCOVER → LICENSE → ARCHITECTURE → COMPARE → LESSONS → ADAPT RESPONSIBLY → TEST → PROVENANCE. **No blind adoption**: every DB, framework, model, API, agent, queue, cloud, language, tool or skill needs a stated reason.
- **D-H208** · undated · Owner (P1 §76) · **Correction to the Pass-1 ladder:** the reality classification also includes **BLOCKED, UNKNOWN, CONTRADICTED**. Never declare DESIGN → IMPLEMENTED or IMPLEMENTED → OPERATIONAL without evidence. (M0 addendum ladder: VISION → DESIGN → IMPLEMENTED → TESTED → INTEGRATED → RUNTIME VERIFIED → INDEPENDENTLY VERIFIED → OPERATIONAL.)
- **D-H209** · undated · Owner (P1 §77–80) · The Reality Gate is a real workflow, not a report: what exists / works / is tested / runtime-verified / independently verified / unknown / failed / rejected / next. Before the first change, inspect: branch, HEAD, remote, worktree, commits, structure, tests, CI, Truth Map, protected files, Lane A, entrypoints, agents, workers, TCB, governance, persistence, frontend, Telegram, providers, reports, debug history, Windows state, research, skills, agent registry. Then build a **CURRENT STATE MAP**. The stop point is set by Repository + Runtime + Evidence, never by docs or the last prompt. Then build a Remaining Capability Graph: nodes = capabilities, edges = dependencies, verification edges = proof, governance edges = approval, critical path = blockers.
- **D-P211** · undated · Owner (P1 §82) · **Correction / extension to D-P09:** P1 lists **8** stop conditions; P2 lists 5. The extra three in P1:
  - an irreversible, financial or credential-sensitive action needs a human decision;
  - a serious, unmitigable security risk;
  - data missing for a correct decision.
- **D-H210** · undated · Owner (P1 §83–84) · Blocker classes: A coding, B testing, C architecture, D research, E fallback, F external dependency, G human governance, H safety. Solve A–E; handle F with fallback or parallel work; G/H pause only the dependent part. Parallel work is allowed only with no dependency, authority or data-corruption conflict and a clear integration boundary.
- **D-H211** · undated · Owner (P1 §88–89) · Definition of Done:
  - code exists, behaviour tested, relevant tests pass, negative cases;
  - security and architecture reviewed;
  - evidence recorded, docs updated, protected boundaries intact;
  - commit; push/merge verified when possible;
  - runtime verified where required; independent verification;
  - failure-aware, observable, recoverable, reproducible.

  Otherwise status is **PARTIAL / IMPLEMENTED_NOT_VERIFIED**. No completion theater (green tests, nice UI, docs, agent names, prompts, fake data, synthetic benchmarks, mocks).
- **D-H212** · undated · Owner (P1 §108) · **User Reality Test** for every completion claim: "If the owner sat at the Windows laptop right now, would this actually work?" NO → keep going; PARTIAL → state exactly what works; YES → record evidence.
- **D-A205** · undated · Owner (P1 §109) · **Never guess**: token address, contract, pool, user credential, API key, market data, news, holders, whales, liquidity, launch date, security result, AI opinion, historical outcome.

**University, skills, federation (P1 §92–100)**
- **D-F205** · undated · Owner (P1 §92–95) · The University is a PERMANENTLY ACTIVE research system. It keeps asking what new tools, skills, models, architectures, research or GitHub projects exist, and what to remove or change. It benchmarks AHOS against the best OSS, agent, trading, research, cognitive, memory, dashboard and security systems (LEARN → ADAPT → TEST → IMPROVE, not copy). Its research frontier includes causal AI, Bayesian methods, RL, knowledge graphs, retrieval, agent evaluation, calibration, anomaly detection, market microstructure and quant finance. The dashboard shows it as a real entity: active research, professors, students, experiments, discoveries, failed experiments, new skills/tools/models, and proposed / verified / rejected improvements.
- **D-C207** · undated · Owner (P1 §96–97) · Agent messages follow a Mission/Message/Evidence protocol: sender, receiver, mission, timestamp, evidence, claim, confidence, capability, required action, verification status. The federation must prevent authority collapse, identity confusion, capability escalation, forged agents/maturity, fake verification, replay, unauthorized missions and secret leakage.
- **D-C208** · undated · Owner (P1 §98–100) · All agents use the project's defined skills (registry, versioned, performance measured, failures logged, improvements sent to the University). Pipeline: RESEARCH → TOOL/SKILL → SECURITY REVIEW → BENCHMARK → SANDBOX → ADAPT → INTEGRATE → VERIFY → AGENT ADOPTION → MEASUREMENT → UNIVERSITY MEMORY. An architecture change from research needs WHY / EVIDENCE / RISK / DEPENDENCY / SECURITY / GOVERNANCE / TEST / ROLLBACK / BENCHMARK, then PROPOSE → TEST → VALIDATE → DECIDE → IMPLEMENT → VERIFY.

**Historical evidence / docs / presentation (P1 §101–107)**
- **D-H213** · undated · Owner (P1 §101–104) · Find all existing docs (Master Context, Truth Map / DOC_TRUTH_MAP, Project State, Knowledge Map, Gap / Issue registers, Canonical Implementation Matrix, AGI/ACI Charter, Agent Registry, …). **Do not delete old evidence** (72-hour soak, 168-hour references, identity census, runtime reports, independent clone audit); record contradictions explicitly. Historical evidence keeps its timestamp and a LIVE / RECENT / STALE / UNKNOWN freshness label; historical test ≠ current runtime. Re-verify prior audits (freeze checks, Windows evidence, identity join, hook protection) rather than assuming them.
- **D-D202** · undated · Owner (P1 §106–107) · Do not delete presentation / 3D / web trees for being old. 3D/UI must never become a second Decision Authority. A feature that only makes the project look nicer, but harms reliability, security, performance, truth or auditability, has no priority.

**Identity / final orders (P1 §115–119, finals)**
- **D-P212** · undated · Owner (P1 §115–117) · AHOS must never become:
  - a black-box score generator, FOMO machine, unverified AI-consensus machine or hallucination engine;
  - a fake autonomous organization or docs-only project;
  - an uncontrolled self-modifier or contract guesser;
  - stale-as-live, confidence-as-truth, live-without-governance, hidden-failure, or an alert-count optimizer.

  Intelligence means better questions, evidence, verification, reasoning, experiments, memory, prediction, error detection, learning and adaptation — not more tokens, agents, models, code, scores or alerts. Goal: ACTUAL WORKING SYSTEM, not COMPLETION APPEARANCE.
- **D-P213** · undated · Owner (P1 §119 FINAL COMMAND) · Numbered build list:
  - preserve and review the 19 roles; create the needed new agents;
  - activate GitHub Intelligence, Skill Intelligence, the AGI/ACI team and the Guardian team;
  - make the University real;
  - build the Gold Division, News Intelligence, Accounting, Telegram and the Local Dashboard;
  - secure the credential architecture;
  - make research, learning and failure-learning permanent; keep self-improvement controlled;
  - prepare multi-market and live-trading architecture, without enabling real trading.

  Banners: NO FABRICATION, NO GUESSING, NO COMPLETION THEATER, NO SILENT ARCHITECTURAL CHANGES, NO SILENT TAXONOMY MERGES, NO DELETION OF VALID EVIDENCE, NO FAKE LIVE STATE, NO SELF-GRANTED AUTHORITY, NO SELF-VERIFICATION AS IV. Operating identity: "Controlled Autonomous Engineering Orchestrator". Principle: "MOVE FAST, BUT NEVER FASTER THAN TRUTH."

**M0 Continuation Addendum (P1 ~lines 3560–3660) — high-impact, new**
- **D-P214** · undated (after the M0 audit) · Owner (P1 M0 addendum) · The Master Directive stays authoritative and must not be replaced by a shortened version. M0 READ-ONLY audit is done; do not repeat it. Starting state per M0:
  - repo `G:\robat\ahos`, branch `ahos`, HEAD at M0 `c02fb8b`;
  - **four agent taxonomies coexist and must NOT be silently merged**;
  - Agent A / true control-plane orchestration not yet implemented;
  - Lane A frozen and verified;
  - Canonical Decision Authority exists and remains authoritative;
  - live trading disabled;
  - research-host/runtime isolation incomplete;
  - **Atria is an evaluation resource, NOT an authority**.
- **D-C209** · undated · Owner (P1 M0 addendum items 6–8) · Start with the highest-value dependency-safe blocker, not large speculative architecture. **"Do not build dozens of new agents merely because the Master Vision describes them. First establish the control-plane, lifecycle, authority, verification and execution foundations."** Where a subsystem is DESIGN_ONLY or PLANNED, build its prerequisite first. (See C-202.)
- **D-H214** · undated · Owner (P1 M0 addendum items 10–20) · When technical work is permitted, execute it rather than describe it. Every mission syncs code, tests, docs, debugging records, evidence, architectural state, organizational memory and TODO/gap registers. Not implemented merely because a file, registry entry, prompt, doc, synthetic test, UI or design exists. Inspect the repo before every major change to avoid duplicates; preserve provenance when taxonomies conflict; never silently delete inconvenient evidence.

**Autonomous-engineering addendum (P1 addendum §1–7, §10–14, §22–27)**
- **D-E208** · undated · Owner (P1 add. §1–4) · Target: a controlled autonomous engineering and cognitive system that self-checks infra, separates cause from symptom, fixes and tests code and agents within policy, syncs docs, checkpoints and resumes, then moves to the next prioritized task.
  - Loop: PERCEIVE → UNDERSTAND → DIAGNOSE → PLAN → EXECUTE → TEST → VERIFY → DOCUMENT → LEARN → NEXT TASK.
  - Change path: Evidence → Proposal → Policy/Gate → Change → Test → Verification → Evidence → Promotion.
  - An "Autonomous Engineering Core" runs 13 duties (state, gap, priority, agent pick, plan, execute, test, regression, verify, evidence, docs, checkpoint, next task).
  - An Orchestrator layer coordinates but never has absolute authority.
- **D-C210** · undated · Owner (P1 add. §5) · Minimum engineering roles: 5.1 Coding, 5.2 Infrastructure (Windows, processes, ports, Python, Node, DB, network, Docker/WSL, CPU/RAM/disk), 5.3 Forensics/Debugging, 5.4 Architecture (drift, duplicates), 5.5 Documentation/Specification, 5.6 Agent-Society Governance (registry, health, missing/duplicate agents), 5.7 Test/Verification, 5.8 Git/Change-Control. Must map onto the 19 roles: no deletion, silent merge or duplication.
- **D-E209** · undated · Owner (P1 add. §6–7) · AI Provider Abstraction Layer (Atria, Claude/Claude Code, Local AI, future), selected by capability, availability, cost/quota and policy. **AHOS ≠ Atria; AHOS ≠ Claude.** Claude Code + Atria is a current-phase engine only; no permanent dependency.
- **D-E210** · undated · Owner (P1 add. §10–13) · Mission State / Engineering Ledger fields: MISSION_ID, CURRENT_PHASE, CURRENT_TASK, TASK_STATUS, CURRENT_AGENT, LAST_EVIDENCE, LAST_TEST, LAST_VERIFICATION, LAST_COMMIT, CURRENT_BLOCKER, NEXT_ACTION, AI_PROVIDER, CHECKPOINT.
  - Quota exhausted → PAUSED → checkpoint → new key → validation → RESUMED from checkpoint (never restart from zero).
  - Self-diagnosis walks Dashboard → API → DB → Runtime → OS toward root cause (CODE_FAILURE, DB connection, PostgreSQL / Docker / WSL unavailable, host resources); unknown causes stay UNKNOWN.
  - Self-repair: Failure → Evidence → Diagnosis → Repair Plan → Policy Gate → Change → Test → Verify → Promote/Reject.
  - Self-development generates tasks from gaps under governance; never change things just "to stay active".
- **D-H215** · undated · Owner (P1 add. §22–24) · Score ≠ Decision; Decision ≠ Outcome; Documentation ≠ Runtime Proof. The addendum must never bypass Lane A, CanonicalDecisionAuthority, the **Python Lane B Decision Authority**, PAPER_ONLY, token identity, security gates, UNRESOLVED / MONITOR_ONLY, or fail-closed behaviour. The Engineering Core serves the official architecture and never replaces it.
- **D-H216** · undated · Owner (P1 add. §25–27) · Autonomous-AHOS Definition of Done is a 26-item checklist:
  - one-click launch; runtime self-check; infra diagnosis; root-cause workflow;
  - Coding / Infra / Forensics / Architecture / Docs / Agent-Governance / Test agents working;
  - mission checkpoint; provider abstraction; credential request; quota handling; resume;
  - controlled self-repair and self-development; evidence generation; doc sync; git traceability;
  - security gates; destructive ops gated; PAPER_ONLY enforced; external-AI outage preserves state;
  - a full E2E autonomous-engineering scenario passes.

  **Done = Code + Test + Runtime Evidence + Verification.** Governing rule: "No intelligence owns AHOS". AI proposes/executes within policy; evidence proves; tests verify; governance controls; architecture defines; the human keeps ultimate control over sensitive and irreversible actions.

### P2.2 Owner directive part 2 — MASTER CONTEXT v2.0, previously heading-only sections

- **D-P215** · undated · Owner (P2 header, §0) · MASTER CONTEXT header: Primary repo `github.com/mainmovement/ahos`; mode PAPER-ONLY; real trading DISABLED; deployment Single User / Windows laptop / Local-First / Free-First. "This document is not proof that a feature exists." The repo, executable behaviour, tests, runtime evidence and governance records decide current reality; the document decides intent and *how* work is performed.
- **D-P216** · undated · Owner (P2 §4) · Absolute epistemic rule: AHOS must be able to answer UNKNOWN / INSUFFICIENT EVIDENCE / CONFLICTED EVIDENCE / UNVERIFIED rather than invent. Never manufacture token data, contracts, launch dates, liquidity, holders, whale activity, security results, market stats, news, social activity, AI opinions or historical outcomes.
- **D-A206** · undated · Owner (P2 §6–7) · Three opportunity classes: A PRE-LAUNCH, B NEWLY LAUNCHED, C EXISTING HIDDEN. **Danger discovery (fraud, manipulation, illiquidity, unverifiability) is equal in importance to opportunity discovery.** Core questions: what do we know / not know / how to find it / how to verify / what would prove us wrong / how will we learn if wrong.
- **D-A207** · undated · Owner (P2 §8–10) · Additional source families beyond D-A201:
  - CoinGecko, CoinMarketCap, DEX/exchange APIs, WebSocket feeds, order books;
  - explorers, RPC, wallet histories, deployer wallets, smart money, transaction graphs;
  - Reddit, Discord;
  - official announcements, project blogs;
  - GitHub commits, contributors and releases.

  "Social activity is evidence about attention, not value." FOMO is a measurable phenomenon: FOMO DETECTED → INVESTIGATE → VERIFY → assess manipulation / liquidity / security / sustainability. Never auto-entry.
- **D-A208** · undated · Owner (P2 §12–13) · Every meaningful token gets a full **intelligence dossier**, not a score:
  - identity fields; liquidity, market cap, volume;
  - opportunity / security / liquidity / evidence scores; confidence;
  - whale, social, narrative, on-chain, dev, tokenomics; council decision;
  - WHY, EVIDENCE, COUNTER-EVIDENCE, RISKS, REJECT CONDITIONS;
  - bull / base / bear / extreme scenarios;
  - what would change the decision; what is still unknown; next observation.

  "A score without an evidence-backed explanation is insufficient." **Confidence stays independent of opportunity** (Opportunity HIGH + Confidence LOW is valid). A correct skip is a successful decision (§14).
- **D-E211** · undated · Owner (P2 §15–17) · Council specialists in detail: math (Bayesian, time series, anomaly), crypto market, on-chain, cyber/hacker, investigative/OSINT, news/journalism (misinformation detection), social/narrative (X, Telegram, Reddit, Discord), software engineering, AI research, strategic red team. The key question is "Why do they disagree?" A **meta-cognitive layer** evaluates the agents; "the Council is also an object of learning." Not "100 meaningless agents".
- **D-E212** · undated · Owner (P2 §18–23) · AHOS does **not** claim general AGI. Novel situations get NOVELTY DETECTED → collect → hypothesize → search prior knowledge → compare → design experiment → test → observe → update, never "NOT IN RULES". ACI memory types: long-term, episodic, semantic, procedural, failure, hypothesis, causal, self-model, organizational. Novelty classes: KNOWN, KNOWN_BUT_UNCERTAIN, UNKNOWN, CONTRADICTORY, NOVEL, POTENTIALLY_IMPORTANT_NOVELTY. Novelty triggers investigation, not belief. The world model answers what / why / cause / next / what changes it / what if wrong.
- **D-A209** · undated · Owner (P2 §24–28) · Paper trades are made even when the user buys nothing. Fields: virtual capital, position size, stop, targets 1–3, **maximum holding time**, exit conditions, reason, evidence snapshot, decision snapshot. Duration ranges from 1 hour to a week or more.
  - Success → POSITIVE PATTERN, never auto-promoted into a rule.
  - Failure → mandatory post-mortem (failed assumption, wrong data, misleading signal, which agent was wrong, confirmation bias, stale data, deceptive whales, artificial social activity, incomplete security, timing, exit, liquidity/slippage underestimated, regime misclassified, thesis wrong) → FAILURE PATTERN.
  - SKIP → track the later outcome and update the decision-quality model. "Not losing money is the successful outcome."
- **D-E213** · undated · Owner (P2 §30–33) · Knowledge sources: paper results, web, academic, GitHub, docs, model comparisons, user feedback, outcomes, security incidents, historical data, OSS, new tools. Provenance is always kept. Multi-model plan (ChatGPT, Claude, Grok, Gemini, local) with role routing (research / coding / security / criticism / reasoning), chosen by measured accuracy, calibration, domain performance, failure patterns, cost, latency, consistency, reasoning and security performance.
- **D-B201** · undated · Owner (P2 §35–36) · **$0 initial budget.** The architecture must tolerate provider blocking, regional restrictions, **filtering**, rate limits, auth problems and outages, via abstraction, fallback, caching, local capability and graceful degradation.
- **D-D203** · undated · Owner (P2 §38–39) · **The website is the primary human interface** (Telegram is secondary). Pages: dashboard, token discovery, opportunity ranking, token intelligence, security, council results, paper trades, performance, learning, news, reports, health, logs, architecture, roadmap, cognitive state, memory, experiments, research, system evolution. (See C-205 on the desktop-window wish.)
- **D-D204** · undated · Owner (P2 §40–47, §128–130) · The user should "see the intelligence working": agents as visible characters / avatars ("eyes"), evidence flows, debate, confidence and risk states, knowledge growth.
  - Visual Truth Rule: every visual element maps to a real state.
  - Tree learning story: SEED → ROOT → TREE → FOREST → ECOSYSTEM.
  - Environment engine (location, weather, timezone, season, day part) drives background, lighting, sky, theme, audio and characters; season × day-part hierarchy with sun/cloud/rain/storm/snow/fog overlays.
  - Audio scenes: FARM, FOREST, OFFICE, GALAXY; they react to time, weather, state, alerts, risk and discoveries; controllable and accessible.
  - Website trust: show what happened, why, evidence, sources, which agents disagreed, unknowns, expectations, what would change it, what happened after, what was learned.
  - Aesthetic North Star: cinematic, sophisticated 3D, realistic agents, immersive audio (Dreamwave / The Game Awards style references, not templates); mobile usability counts.
- **D-B202** · undated · Owner (P2 §43) · Modular Intelligence ("four-output") principle: extract more intelligence per valid source (e.g. blockchain → wallet / whale / holder / transaction intelligence), rather than adding more sources.
- **D-D205** · undated · Owner (P2 §51–53) · Daily intelligence report:
  - new, strong and rejected opportunities;
  - open and closed paper trades; P&L;
  - success and failure causes;
  - major news; system changes; learning status;
  - security events; provider health; model performance.

  **Full Decision Record** for every important decision: timestamp, asset, identity, evidence, sources, models, agent opinions, scores, confidence, decision, reason, counter-evidence, outcome, post-mortem, learning result. Metrics must be defined precisely before being treated as proof.
- **D-A210** · undated · Owner (P2 §58–59) · Path: Evidence → Canonical Decision Authority → Risk/Security → Paper Decision. **Unresolved identity must never become ENTER.** Security is compositional (PASS / UNKNOWN / INCOMPLETE / FAIL); missing critical info may force INCOMPLETE / MONITOR_ONLY / REJECT.
- **D-C211** · undated · Owner (P2 §60–64) · Target chain HUMAN → AGENT-01 → MISSION CONTROLLER → SPECIALIST → WORKER → TCB/GOVERNED WRITE → EVIDENCE → IV → ACCEPTANCE → ORG MEMORY → AGENT-01/HUMAN. Agent-01 is the primary interface with the human, and may not create identity or appoint its own commander. **Only the authorized commander/mission system activates agents.** The canonical **Slice-1 19-role taxonomy** and other planned 19-role taxonomies stay distinct until governance decides; never rename, merge or reinterpret them.
- **D-C212** · undated · Owner (P2 §65) · **COGNITION ≠ GOVERNANCE ≠ EXECUTION.** Cognition produces hypotheses, analysis, proposals, research, predictions. Governance decides permissions, promotion, protected changes, authority, policy. Execution performs external actions, trading, deployment, mutations. They must stay separable.
- **D-H217** · undated · Owner (P2 §69–75) · Mission model fields: ID, objective, scope, owner, commander, constraints, dependencies, inputs, expected outputs, acceptance criteria, verification criteria, risk, evidence, status, outcome, lessons. Dev protocol has 14 steps (understand → inspect repo → architecture → governance → dependencies → real state → plan → **minimum safe change** → test → verify → regressions → document → evidence → next action). Never code blindly. DOCUMENTED ≠ IMPLEMENTED ≠ TESTED ≠ VERIFIED ≠ ACCEPTED ≠ PRODUCTION. "Knowledge must survive the developer."
- **D-D206** · undated · Owner (P2 §73) · No false automation: never display AI DEBATE COMPLETE, LIVE DATA, VERIFIED or AGI unless real.
- **D-C213** · undated · Owner (P2 §76–77) · **Cursor is an Engineering Agent, not a root of trust**; it must not bypass governance. Multi-agent development risks correlated errors, duplicated assumptions, context poisoning, authority confusion and verification theater; optimize for independent useful cognition, not agent count.
- **D-E214** · undated · Owner (P2 §84–92) · Frontier pipeline: DISCOVER → EVALUATE → EXPERIMENT → BENCHMARK → CHALLENGE → VALIDATE → ADOPT/REJECT. Error as data: FAILURE → CLASSIFY → ROOT CAUSE → CONTEXT → COUNTERFACTUAL → LESSON → MEMORY → FUTURE TEST. Positive pattern: SUCCESS → cause → signal attribution → context → replication test → candidate → OOS → memory. Counterfactuals must be labelled as such. Calibration compares predicted confidence with observed outcome. Per-model/agent performance memory drives routing. "99.9%" is an aspiration, not a metric. Compare against previous version, simple baseline, alternative model/strategy.
- **D-H218** · undated · Owner (P2 §96–97, §103–106) · Observability: system, provider, agent, mission, evidence, verification, paper, memory and model status; errors; audit logs; architecture status — make uncertainty visible. Reality states also include NOT_IMPLEMENTED / DESIGN_ONLY / PRODUCTION_READY; never DESIGN → PRODUCTION. Tests add browser, performance and failure-mode tests. **Importing a module must never mutate tracked evidence**; separate functions from execution. Missing source data → EVIDENCE = NON-REPRODUCIBLE, never VERIFIED. Provider Registry needs data contracts, provenance, freshness, lineage, quality, conflict detection, reconciliation and fitness gates.
- **D-H219** · undated · Owner (P2 §107–110) · Least privilege for AI agents: no arbitrary credentials, network, filesystem, subprocess or mutation authority; process isolation ≠ a full sandbox. **An accidentally exposed credential is compromised and must be rotated or revoked** (basis for the Telegram-token block, D-D12). AI must never reproduce secrets from context. Code quality: no fixture patches, hidden bypasses, fake tests, swallowed errors, or **silent fallbacks that alter truth**.
- **D-H220** · undated · Owner (P2 §111–115) · Bug → ask which invariant failed and prefer general fixes.
  - Contradiction record format: CONTRADICTION / SOURCE A / SOURCE B / CLAIMS / EVIDENCE QUALITY / EXPLANATIONS / UNRESOLVED / NEXT VERIFICATION STEP.
  - Something missing → check required? already elsewhere? planned? governance-blocked? Lane A conflict? new authority path? new dependency? safe now?
  - Ambiguity → inspect / research / clarify over guess.
  - **Stop and ask the human** for: governance choice, irreversible action, unavailable dependency, credential authorization, **paid infrastructure**, live trading, destructive operation, **unresolved architectural conflict**.
- **D-P217** · undated · Owner (P2 §117) · Architectural priority hierarchy (10 levels): human command > safety/security > verified repo reality > canonical governance > evidence/tests > existing architecture > master vision > roadmap > experiments > aesthetics. "A future AGI capability cannot override Lane A."
- **D-P218** · undated · Owner (P2 §121, §124, §131, §136–137) · Progress means more accurate, calibrated, explainable and robust; better at uncertainty, scam detection, hidden opportunities, novelty and failure learning; and **preserving previous capabilities while improving**.
  - Golden Fruit: 1 exceptional or 0 opportunities beats 1000 alerts.
  - Most important requirement: identity resolved before intelligence; traceable evidence; explicit uncertainty; tests for every change; evidence-justified promotion; **explicit permission for every execution**.
  - Finance goal is evidence-based risk-adjusted intelligence (expected return, risk, probability, liquidity, volatility, correlation, drawdown, costs, slippage, funding, latency, counterparty risk, regime), not maximum raw return.
  - Decision quality, not always being right.
- **D-H221** · undated · Owner (P2 §140–154) · Master AI operating contract.
  - ALWAYS: inspect, verify, research, test, document, preserve evidence/audit/security/governance/back-compat, expose uncertainty, record contradictions, seek counter-evidence, prefer general fixes, measure, protect Lane A, keep real trading disabled.
  - NEVER: invent data, addresses, implementation status, verification or sources; hide uncertainty; bypass governance/security; casually modify protected truth paths; treat docs/confidence/popularity/FOMO/engagement as proof; enable live trading autonomously; self-grant authority; self-verify as IV; silently merge taxonomies; silently rewrite architecture.
  - Workflows: 18-step repository workflow; research workflow (… replication → knowledge candidate → verification → memory); decision workflow (IDENTITY → DATA QUALITY → EVIDENCE → SECURITY → MARKET → ON-CHAIN → SOCIAL → NEWS → NARRATIVE → TOKENOMICS → DEV → MATH → COUNCIL → COUNTER-EVIDENCE → RISK → CONFIDENCE → DECISION); paper-trade workflow (OPPORTUNITY → IDENTITY VERIFIED → SECURITY → EVIDENCE SNAPSHOT → ENTRY HYPOTHESIS → RISK → SIZE → ENTRY → MONITOR → EXIT → OUTCOME → POST-MORTEM → LEARNING).
  - Reality vs Master Context → record both and classify.
  - Better idea → evaluate, then PROPOSE → TEST → VALIDATE → DECIDE.
  - Large task → decompose (mission → sub-missions → tasks → tests → verification → acceptance).
  - Provider fails → never substitute fake data; continue only if evidence quality stays acceptable.
  - Stale → label it. Sources disagree → never average blindly; classify RECONCILED / CONFLICTED.
  - Models disagree → ask about evidence, assumptions, historical strength, calibration.
  - System wrong → incident record.
- **D-P219** · undated · Owner (P2 §155–158) · Final definition: an Evidence-First Cognitive Intelligence Platform starting with crypto; eventually, **under explicit governance and independent risk control, support autonomous [execution]**. "Do not confuse automation with autonomy; intelligence with authority." Central question: "What do we not know?"
- **D-E215** · undated · Owner (P2 after §160) · A separate **AHOS AGI/ACI ARCHITECTURE CHARTER v1.0** was delivered as a complement to the Master Context (memory, world model, reasoning, planning, metacognition, causal / counterfactual / creative intelligence, controlled self-improvement, frontier research, multi-market, Risk Governor / Permission / Kill Switch, path to domain-general / "domain-superhuman" intelligence). Rules:
  - VISION ≠ IMPLEMENTATION; CHARTER ≠ CAPABILITY; AMBITION ≠ ACHIEVEMENT.
  - On receipt: "change no code, build nothing, declare nothing implemented"; add it to the mental model only.
  - Where the Charter conflicts with repo reality or newer protocols, the newer reality wins.
  - Its trust order: human > repo > governance/safety/security > evidence > MASTER CONTEXT > Charter > roadmap > ideas.
  - The Charter body itself was not located in part2 (only this wrapper was seen).

### P2.3 Owner directive part 2 — Completion Mandate & Execution Mandate, previously heading-only sections

- **D-P220** · undated · Owner (P2 Completion Mandate preamble) · The mandate is addressed to "Agent-01 / Project Orchestrator", to be applied after reading MASTER CONTEXT + AGI/ACI Charter + repo knowledge. It **creates no new authority and cancels no governance rule.** Cycle: DISCOVER → UNDERSTAND → TRACE → DESIGN → IMPLEMENT → TEST → DEBUG → ADVERSARIAL → CRITIQUE → SELF-CRITIQUE → COUNCIL → IMPROVE → TEST AGAIN → IV → ACCEPT/REJECT → INTEGRATE → MEMORY → REASSESS → CONTINUE. "MISSION COMPLETE → STATE REASSESSMENT → NEXT MISSION", never "→ REPORT → STOP" (§1–2).
- **D-H222** · undated · Owner (P2 Mandate §4–5) · Before any important change, reconcile authoritative knowledge: vision, directives, DOC_TRUTH_MAP, Project State, Knowledge Map, Gap/Issue registers, Canonical Implementation Matrix, Charter, agent registry/specs, protocols, `.cursor/skills`, tests, reports, git/PR history, forensics, failure memory, benchmarks, runtime/Windows/soak/provider/frontend/Telegram/n8n evidence. "DOCUMENTATION IS KNOWLEDGE · CODE IS IMPLEMENTATION · TESTS ARE EVIDENCE · RUNTIME IS REALITY." Mandate ladder: DOCUMENTED → DESIGNED → PARTIALLY IMPLEMENTED → IMPLEMENTED → TESTED → INTEGRATED → RUNTIME VERIFIED → INDEPENDENTLY VERIFIED → OPERATIONAL → PRODUCTION-CAPABLE.
- **D-C214** · undated · Owner (P2 Mandate §6, §8) · The goal is a real, provable chain, not "19 files or metadata records". Find each broken link (cause, dependency) and engineer it when safe. Taxonomy rule: preserve provenance, make differences explicit, build the mapping, **record collisions**, leave governance decisions in place.
- **D-E216** · undated · Owner (P2 Mandate §9–12) · The Council must be able to say "design wrong / implementation incomplete / tests insufficient / evidence weak / architecture dangerous / abstraction unnecessary / runtime fails / regression likely / scientific assumption unproven". Decision chain: THESIS → ANTI-THESIS → FOR → AGAINST → UNKNOWN → CONTRADICTION → RESOLUTION → DECISION.
  - Self-critique asks: did a fixture fake success? hidden coupling? broken back-compat? is the evidence current?
  - Red-team findings become engineering missions.
  - Root-cause layers: immediate, root, architectural, process, test gap, governance gap, memory gap, prevention.
- **D-E217** · undated · Owner (P2 Mandate §14–15) · The world model needs semantics, not just a large DB. Make episodic, semantic, procedural, failure, hypothesis, causal, self-model, organizational and agent-performance memory operational. **Failure Memory should eventually influence decisions in a governed way.**
- **D-H223** · undated · Owner (P2 Mandate §17–18, §22–24) · End-to-end audit of DATA → NORMALIZATION → IDENTITY → EVIDENCE → SECURITY → MARKET → ON-CHAIN → SCORING → RISK → CANONICAL DECISION → PAPER → OUTCOME → CALIBRATION → MEMORY → LEARNING → ALERT → DASHBOARD → TELEGRAM. For each stage say whether it is real, mock, test-only, partially integrated or runtime-verified, and list its failure modes.
  - **Mocks are allowed only if explicitly labelled as mocks.**
  - Runtime chain: CODE → IMPORTS → TESTS → INTEGRATION → RUNTIME → FAILURE HANDLING → RECOVERY → IV; if runtime is unprovable, say exactly that.
  - Order is CODE → TEST → VERIFY → DOCUMENT (never DOCUMENT → CLAIM → HOPE).
  - Sync truth map, project state, gap/issue registers, implementation matrix, verification records and org memory, without beautifying reality.
- **D-H224** · undated · Owner (P2 Mandate §29–31) · Incomplete capabilities stay in the **REMAINING REALITY REGISTER** with true status. "Best architecture with minimum unnecessary complexity." Unnecessary → remove; bad abstraction → redesign; wrong architecture → fix; feature contradicting the mission → reject; built only to impress → remove. (See C-207.) Global standard: "If a top-tier world team built this subsystem, what would still be missing?" A professional look is never proof.
- **D-E218** · undated · Owner (P2 Mandate §32) · Epistemic law addition: never **UNKNOWN → POSITIVE** (on top of UNKNOWN → SAFE etc.).
- **D-H225** · undated · Owner (P2 Mandate §36) · Immediate execution protocol: Phase A reality map → B remaining capability graph → C critical path → D parallel safe missions → E implementation → F test + debug → G council critique → H red team → I IV → J integration (only valid results) → K memory/truth/docs → L next mission. Repeat D→L.
- **D-H226** · undated · Owner (P2 Exec §4–5) · Continuous loop: repo forensics → state map → blocker prioritization → mission design → implement → local tests → adversarial review → independent-style review → critique of critique → remediation → regression → docs → commit → push → merge if valid → post-merge verification → next. **Next-mission priority bands:**
  - P0: security, truth, broken runtime, data corruption, Lane-A breakage
  - P1: wiring core components / architectural blockers
  - P2: tests, verification, persistence, observability, auditability
  - P3: core product capabilities
  - P4: learning, memory, AGI/ACI, cognitive society
  - P5: UI, 3D, audio, polish
  - P6: frontier ideas

  The pre-selection checklist includes: "is Cursor still outside the trusted boundary?", "is the Agent Organization still documentary?", "is the Mission Controller missing?".
- **D-H227** · undated · Owner (P2 Exec §6.3, §7 Pass 2) · Minimal safe change: small, reviewable, reasoned, lowest risk, back-compat checked, **rollback stated**, tested, docs updated, Lane A untouched. Security review adds duplicate JSON keys, forged maturity/capability, unsafe subprocess/filesystem writes, fake live status, and accidental live trading.
- **D-H228** · undated · Owner (P2 Exec §8–9) · Never just "Tests passed": state which tests, on which environment, what they prove, what they do not prove, and what is still UNKNOWN. Skipped ≠ passed. Defect loop: record → severity → root cause → compare fixes → lowest-risk general fix → re-run tests and critiques → commit. **"Previous Output Is Not Sacred."**
- **D-H229** · undated · Owner (P2 Exec §12) · Ordered technical goals (soft order; repo dependencies decide):
  1. repo truth
  2. import side effects
  3. Lane A
  4. Paper-Only
  5. identity / provenance
  6. TCB
  7. identity / session
  8. Mission Controller
  9. Agent-Org ↔ AHOS federation
  10. process-isolated worker
  11. persistence
  12. audit / org memory
  13. real IV
  14. safe Cursor federation
  15. Agent-01 non-absolute
  16. specialists + lifecycle
  17. claim separation
  18. contradiction intelligence
  19. paper lifecycle
  20. outcome tracking
  21. positive / failure patterns
  22. calibration
  23. provider abstraction
  24. low-latency research
  25. website surface
  26. Telegram secondary
  27. cognitive visualization
  28. tree growth
  29. environment engine
  30. audio / 3D polish
  31. AGI/ACI + controlled evolution
  32. multi-market only after the foundation is stable
- **D-H230** · undated · Owner (P2 Exec §14–15) · Report per cycle (short): MISSION, OBJECTIVE, ACTUAL CHANGES, FILES, TESTS, VERIFICATION, CRITIQUE FINDINGS, REMEDIATIONS, COMMIT, PUSH, MERGE, CURRENT REALITY, BLOCKERS, NEXT MISSION. "The report is the result of work, not a substitute for it." Allowed stops (Exec list): human/governance decision; missing credential or external access; serious security risk; irreversible or financial action; **unresolved conflict between two valid orders**; missing data; genuine completion. Otherwise do not ask permission for each step.

### P2.4 Owner's raw voice notes appended at the end of part 2 (lines ~7187–7197, Persian, undated) — highest-fidelity owner orders

These are the owner's own words, not an AI rewrite. Several are the original source of later decisions.
- **D-P221** · Owner (P2 L7187) · "**Not one word is to be removed**" from the directive. Continue from wherever the project stopped. Update and match the old debug files at the same time. Claude must use its highest, fastest, most professional, most technical version. Document everything with **date, time and subject, categorized**, so any other super-intelligence can understand — "a law for all super-intelligences".
- **D-E219** · Owner (P2 L7187, L7191) · AGI/ACI must be considered in every part of the build and the bot: all of Claude, every build step, every agent in Claude, the bot overall, every bot agent and tool, and runtime operation must "use AGI and ACI".
- **D-E220** · Owner (P2 L7187) · "In acquiring knowledge and skills it needs **no permission from me**; in debugging itself, developing itself, updating itself and making itself smarter it needs **no permission from me**." (See C-203.)
- **D-A211** · Owner (P2 L7187) · "**Live trade must definitely be enabled for all parts and options**", and "it must be able to live-trade in the future, once it has developed and trained itself to world level." **This is the literal source of HUMAN-GATE contradiction OWN-7** (correction to C-07: source located). It conflicts with PAPER_ONLY (D-A01) unless read as "eventually, via the gated path".
- **D-G202** · Owner (P2 L7187) · **Gold first:** "I intend to first launch automated gold trading, as a test and as real trades but **with hypothetical money**; **when we reach real profit, run the other lines** of the project." Gold agents the owner asked for:
  - one learns gold science (buy/sell, futures, long/short);
  - one applies AGI/ACI to gold trading;
  - one learns chart reading;
  - one brings top-level projects;
  - one learns online trading;
  - **two** supervise the gold agents;
  - **two** match all gold parts together.

  "Add any gold agent, skill or proposal you want." This is the owner-voice source for D4 / M13 gold-first paper and for gating the other lines on gold paper profit.
- **D-C215** · Owner (P2 L7187) · Activate all 19 defined agents for building the project; **two agents only search GitHub** and bring in the best projects; agents use the project's defined skills; a **4-person skills team** injects the best skills; a **4-person AGI/ACI team**; a **4-person web/frontier study team** ("so agents work like AGI/ACI"); a guardian group watches all agents. "19 agents before, a few now; add as many as you want, any specialty."
- **D-F206** · Owner (P2 L7187–7189) · The University is "super-super-super exceptional": dozens of professor and student bots researching speed, intelligence, alertness, tools, new GitHub projects in **US/EU/Asia stocks, gold, oil, crypto, tokens**. It hands results to the "**Ministry of Labour group**" (گروه وزارت کار) for implementation in the bot. It works continuously. Agents with problems, ambiguity or doubt consult it. **The University can decide to add a new agent with specific knowledge, or add duties to another agent.** It has a part that learns from the bot's mistakes, in every field.
- **D-D207** · Owner (P2 L7189, L7197) · An agent group builds the **local dashboard**, very professional and beautiful (model on the most beautiful), every part creative, clean, technical, scientifically precise. Tree/roots site design only if suitable; otherwise replace with the most beautiful patterns. Consider AGI/ACI in the dashboard design.
- **D-P222** · Owner (P2 L7190) · "Proceed per the project documents — **but some decisions have been updated; do those parts per the updated decisions.**" (Basis for later docs overriding older directive text.)
- **D-E221** · Owner (P2 L7192) · Document everything so that **if tokens run out and I enter a new API key, it does not restart from scratch or skip anything.**
- **D-C216** · Owner (P2 L7193) · Accounting agent across **all** sections. A credential agent receives passwords, usernames and wallet addresses "with any name and spec" for **account opening, account-to-account transfers, cash-out, conversion (crypto → oil unit, gold → stock unit), or deposit to my personal account**, using AGI/ACI, trained by the University. All agents keep training and updating themselves. (Directive §29–31 later constrained this: credentials have no financial authority; Capability ≠ Permission.)
- **D-E222** · Owner (P2 L7194) · "Many people use up-to-date super-intelligences like **astra ai**" and projects or skills far above ours. Claude's agents and the bot's University agents must find and use these "so we do not fall behind". (Source of the Frontier team and M37 frontier slots.)
- **D-G203** · Owner (P2 L7195) · The news agent group covers every field and style, finds all news sites relevant to each line, and feeds them to every line (gold, stock exchanges, oil, tokens, crypto, futures). Purpose: **earlier, timely buys and timely sells** for more profit; also feeds the University on new tools and studies.
- **D-D208** · Owner (P2 L7196) · An agent group builds a Telegram bot "so I can chat with it easily and raise any request". **The same super-intelligence must also be in the dashboard on the local laptop.** AGI/ACI active. "**Take a lot of inspiration from Grok Bot's AI.**"

### P2.4b Repo reports — GROK_HANDOFF, CLAUDE_CONTINUATION_GUIDE, REMAINING_REALITY_REGISTER (previously unread chunks)

Paths: `RG\GROK_HANDOFF.md` (1,470 lines), `RG\CLAUDE_CONTINUATION_GUIDE.md` (1,328 lines), `RG\REMAINING_REALITY_REGISTER.md` (701 lines). Times are Tehran unless marked.

**Telegram / chat / control path**
- **D-D209** · 2026-10-02 (Phase 4) · Grok, GM-04 · The Telegram/chat **control gate only removes capability** ("conservative capability gate"). The `stop` regex had no word boundary, so "stop loss"/"stoploss"/"توقف ضرر" could stop the engine; it now never matches. The client `channel` field is never a grant (`channel_claimed` only). Status: IMPLEMENTED/TESTED by self-test, **pending سپهر/قاسم/رضا review**. Residual: any holder of `AHOS_WEB_API_TOKEN` can call `/api/engine` and claim channel `web` = owner (phase 2: loopback check / second secret; `isLoopbackRequest` later restored, D-H14). (RG\GROK_HANDOFF L1004–1079; guide L458)
- **D-D210** · 2026-10-02 (Phase 5) · Grok, after the owner's live G11 test (refusals OK, CHAIN_OK) · Reply presentation rules:
  - no internal "GM-04" text;
  - refusal reads «⛔ … غیرفعال است. … هیچ تغییری اعمال نشد.»;
  - footer «تصمیم نهایی با کاربر است.» once per reply;
  - a `stop_loss` intent shows only the recorded invalidation condition and **never invents a number**.

  The owner wants replies backed later by a **free AI model**, same style on Telegram and the Windows dashboard. (GROK_HANDOFF L882–960)
- **D-E223** · 2026-10-02 (Phase 6) · Grok, owner-approved · Gemini "ReplyPhraser" seam: the phraser **never decides and never sees credentials**. `locked: true` refusals are never rephrased; news and replies with links are never phrased. Read-only Windows Credential Manager backend is owner-approved but **GM-12 independent review still pending**. Models: `AHOS_GEMINI_MODELS` default `gemini-flash-lite-latest,gemini-3.5-flash-lite`, max 2 (others gave 503/404 in owner tests). Proxy `127.0.0.1:10809` stalls >5 s after idle. (GROK_HANDOFF L802–878; guide L317–366)
- **D-D211** · 2026-10-02 17:35 (Phase 7b) · **Owner scope change** · Free-form, multi-turn Persian chat "like ChatGPT/Grok", not keyword intents. Same backend `chat.ts::handleChat` for Telegram and dashboard.
  - Non-owner control intent → REFUSED + audited («⛔ این دستور فقط برای مالک سیستم مجاز است»).
  - Owner control intent → confirm-gated proposal; nothing executes until «تایید CODE».
  - Confirmation is whole-message only; a bare «تایید»/«بله»/«stop loss» is never a confirm.
  - Execution reuses the **same functions as the dashboard routes**; paper buy still goes through `paperAllowedFromCanonical` (Canonical Authority decides).
  - **NEW_NUMBER rule:** every number in a reply must appear in tool output, the user message or earlier turns.
  - Futures/leverage/TP/SL requests get "paper/analysis only, no signal/leverage/TP/SL" + a risk warning.
  - Budget: 2 models × 4 s, 9 s total; no retry on AUTH/QUOTA/BLOCKED.
  - New commands must be added to ActionKind + PROPOSE_TOOLS + CAPABILITY + defaultActionDeps, reusing the dashboard route function, with selftests.

  (guide L370–474)
- **D-H231** · 2026-10-03 12:14 (Phase 9.5/9.6) · Claude/Atria, from two independent reviews (REDTEAM-19 and HARDMODE; 4 blast, 17 major, 19 minor — **all closed**, authoritative record `RG\reviews\FIX_MATRIX_PHASE9_5_9_6.md`) · Rules now in force:
  - **identity is server-proven or nothing** (`isOwner` needs `id.proven` + `TELEGRAM_ADMIN_USER_IDS`; reader allowlist grants read only);
  - confirm proposals bind a 64-hex `summaryHash`; confirm code stored only as a hash;
  - **5 wrong guesses lock the identity**; paper quantity clamped to `MAX_PAPER_QUANTITY`;
  - **audit before action** (EXECUTING record first; a broken audit sink aborts and burns the code);
  - global redaction before Gemini/DB/memory;
  - `hashId`/`messageHash` are HMAC-SHA256 with a local pepper;
  - **Gemini egress is an explicit file-backed owner approval, default-on, kill switch `AHOS_GEMINI_EGRESS`**.

  "Self-tests are not independent verification." (GROK_HANDOFF L314–403)
- **D-H232** · 2026-10-02 · Owner (guide L291; GROK_HANDOFF L1074, L1259) · The G11 live Telegram E2E is an **owner action** (runbook `RG\G11_LIVE_E2E_RUNBOOK.md`); the bot only picks up changes after an owner restart; Grok restarts nothing. Gateway port mismatch (`.env` 3000 vs listener 3500) is OWNER_ACTION: restart on 3000, or set `AHOS_GATEWAY_PORT/URL`. `.env` NOT edited; 3000 NOT mass-replaced (GM-05).
- **D-E224** · 2026-10-02 (Phase 8a) · Claude/Atria · Dev-mission intake: the chat assistant **does not write code**. When the owner asks for engineering work it proposes a confirm-gated **development mission** record (`dev_missions.jsonl`, schema `ahos.dev_missions.v1`; warm intro «حتماً! من خودم کد نمی‌نویسم…»). The queue has a writer and **no reader**; its intended consumer is "the M13 mission controller" (see C-208). (guide L478–499)

**Mission ledger / provider status**
- **D-E225** · 2026-10-02 (Phase 3) · Grok, GM-08 / GM-09 · Mission ledger (`architecture/mission/ledger.py`, CLI `scripts/mission_ledger.py`):
  - states PENDING / RUNNING / PAUSED / WAIT_FOR_AI / BLOCKED / RESUMED / COMPLETED_UNVERIFIED / FAILED / CANCELLED, with a legal-transition table;
  - `start()` refuses an existing id (**never restart from zero**);
  - hash chain `seq` + `prev_hash` + `entry_hash`; never append onto a broken chain;
  - `CURRENT_AGENT` must be namespaced (`engineering:*`, `agent:*`, `AG:*`, `AGENT:*`, `agent.org:*`, `M0:*`); a bare "01" is rejected; **the four taxonomies are referenced, not merged**.

  GM-09: seven-state `AIProviderStatus`; 401/403 → AUTH_FAILED (geo-403 → BLOCKED); 402/429/quota → QUOTA_EXHAUSTED (transient 429 → DEGRADED); `safe_provider_call` never crashes the runtime; `SecretValue` never prints and cannot be pickled; quota/auth → ledger PAUSED + checkpoint + owner message. **The new-key message tells the owner to use Credential Manager target `AHOS/ai/<provider>` and never paste the key in chat, Telegram or `.env`.** (GROK_HANDOFF L1118–1179)
- **D-B203** · 2026-10-02 (Phase 2) · Grok, GM-06 · n8n governance rules + **ahos_03 quarantine** (`RG\GM06_N8N_QUARANTINE.md`, `tests/test_n8n_governance_rules.py`). **GM-07 waits for owner approval.** (GROK_HANDOFF L1325, L1368)
- **D-H233** · 2026-10-02 · GROK_HANDOFF Phase 2 note · Phase 1–2 commits were **pushed**; from Phase 3 on, pushes are paused by the owner (local commits only). Consistent with D-H04's pause from 2026-10-02 14:52.

**Launcher (M11) specifics**
- **D-D212** · 2026-10-03 ~19:30 (Phase 11) · Claude/Atria · `launcher/` package (`ahos.ps1`/`ahos.bat`, `orchestrator.py`, `components.py`, `processkit.py`, `persian.py`, `shortcuts.py`, `make_icon.py`, `smoke.py`) + `docs/ONE_CLICK.md`, 124 unit tests.
  - `START_ORDER = stores, db_backend, gateway, telegram, engine`; only `stores` and `engine` are CRITICAL; optional failure → DEGRADED; a critical failure rolls back only processes it spawned.
  - **Paper-only is structural**: `ENGINE_ENV_HARD` forces `AHOS_PAPER_ONLY=1` and `AHOS_EVIDENCE_SOURCE=local`; the launcher refuses any non-paper engine.
  - Health by real work, not pings. The chosen port is written to `reports/launcher/` state, **never `.env`**.
  - A foreign program on a gateway port is reported, never killed (adopted only if its command line proves it is ours).
  - Owner-readable log: `logs/launcher/launcher.log` (UTF-8 Persian).
  - **OPERATIONAL requires the owner to run `AHOS.lnk` and say so; self-tests cap at TESTED; VERIFIED needs an owner to read receipts.**

  (GROK_HANDOFF L300–311, L407–430; guide L641–718)
- **D-H234** · 2026-10-06 · Claude (owner-authorized) · Autopilot rules:
  - **one-shot rule**: a mission turn must never end while background work is pending; foreground suite chunks;
  - `MAX_ATTEMPTS=3`, then NEEDS_REVIEW holds the queue at an owner gate;
  - a completed (consumed) mission is never executed again;
  - the **owner's recovery rule forbids redoing artifacts that are already valid**.

  Known residual: `_reclaim_gateway_port` can still kill an owner-started dev server bound to a candidate port. (guide L938–1249)

**Reality Register specifics**
- **D-H235** · 2026-10-03 (M9) · Claude/Atria, per owner P1 §76–80 · `RG\REMAINING_REALITY_REGISTER.md` is **the standing readiness authority: where it disagrees with an older map, the register wins.** Twelve older maps carry STALE/SUPERSEDED banners (e.g. `AHOS_PROJECT_STATE_MAP.md`; `reports/PHASE_STATE.md` "first live cycle executed" is contradicted by `paper_exits = 0`). `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` recount: COMPLETE 17 / PARTIAL 10 / BLOCKED_EXTERNAL 3 / DEFERRED_BY_DESIGN 2 / NOT_IMPLEMENTED 1 = 33. `reports/FAILURE_MEMORY.md` has FM-001..FM-007. (GROK_HANDOFF L582–613)
- **D-H236** · 2026-10-03 · M9 outcome (GROK_HANDOFF L615–624; guide L566–569) · **Mission numbering: "Use the 18:49 order; treat the original list as mission definitions only."** "M12" means *agents* in the 18:47/18:49 owner order but *paper trading + learning* in the original list. (Partial resolution of C-03.)
- **D-H237** · standing (register L367–375) · Governance-gated list (do not do, only list):
  - Lane A freeze regeneration (`scripts/freeze_lane_a.py --write`, human-only);
  - `security_verdicts` schema write inside the frozen lane;
  - soak start (`docs/PRE_SOAK_PROTOCOL.md`);
  - G11 live E2E;
  - n8n / deployment topology;
  - constitution / governance-authority changes (two open contradictions);
  - live trading.

  Also gated: operator-facing one-click activation; **live Gemini council calls (paid quota → explicit owner approval)**; **live news APIs (paid → explicit owner approval)** — which is why news intelligence is "IMPLEMENTED, never harvested".
- **D-A212** · standing (register §33) · Four live-trading enforcement layers:
  1. `architecture/hygiene.py::assert_safe_environment`
  2. `scripts/month1_failure_matrix.py::_EXECUTION_SURFACE_RE`
  3. `ahos_org/policy.py::GLOBAL_DENY_CAPABILITIES` (`trading.live` denied to all 19 agents, no override path)
  4. the canonical authority emits paper/abstain only

  `PRE_SOAK_STATUS.txt`: `execution_surface = NO_EXECUTION_SURFACE`; "STATE B: do not db:migrate / db:push". Enabling live trading needs a **constitution change (MASTER_DIRECTIVE_v1, Class A doctrine) + an owner decision**.
- **Built-vs-paper additions (register, 2026-10-03, re-queried counts):**
  - Discovery: OPERATIONAL — 22,285 tokens (DEAD 12,629 / RESOLVED 5,936 / …).
  - VERIFIED: provider fallback, scoring, Lane-A freeze, security overlay (one unpersisted path), calibration (thin: 19 labelled tokens; needs ≥1,000 labels + ≥30 closed trades), backup/restore, mission ledger.
  - TESTED: scheduler, runtime (soak entry BLOCKED: G2/G3/G10 NOT_VERIFIED), identity/provenance, canonical decision (0 runtime decisions), governance, AI council (never ran on a real token; latent `Tuple` NameError), quota-stop.
  - PARTIAL: paper (0/30), outcome tracking, dashboard/one-click, TCB/session (docs-heavy), contradiction intelligence (0 claims, 0 edges).
  - IMPLEMENTED: news (never harvested), low-latency (measurement VERIFIED).
  - Accounting ledger: TESTED with 0 rows.
  - PLANNED / docs-only: **agent organization (19 logical agents; nothing dispatches)**, **University**, **wise-tree visualization**, **gold intelligence**.
  - Multi-market: ingestion OPERATIONAL, execution ABSENT.
- **D-C217** · 2026-10-03 (register CC-2) · Namespace collision: `agent.*` (19 `CANONICAL_AGENT_IDS` in `ahos_org/registry.py`), `AG-*` (control-plane tests), `AGENT-*` (frozen 10-agent model in bannered `docs/AGENT_MAPPING.md`). `docs/governance/AGENT_TAXONOMY_MAP.md` maps them, but **no rule says which id a new component must use**; this becomes a real contradiction once any agent reaches the maturity floor. (See C-201 on the count.)

### P2.5 Vision `RG\AHOS_AUTONOMOUS_VISION.md` (v1.8, 2026-10-03) — previously skipped sections (charters, §2.4–2.7, §4.5–4.6, §8.3, §9, §14.1–14.6, §14.8, §14.10.1–3, §14.11, §15)

Read by keyword filter over the full ranges (authority / cannot / forbidden / never / caps / owner / INV), not line by line. Status of everything here: [PROPOSED]/[PLANNED] unless marked owner-approved.

**Charters (§2.3.1–2.3.3)**
- **D-C218** · 2026-10-03 ~20:43 (owner-approved design) · Owner Agent Template, inherited by every charter:
  - the 10 fields; the cognitive profile; an explicit Agent-01-style "cannot" list; P1§14 lifecycle; COGNITION/GOVERNANCE/EXECUTION plane; P1§96 message protocol.
  - **A University certificate L0–L4 only permits the WAITING_FOR_COMMAND → ACTIVE transition within the certified domain** (replaces the v1.0 lifecycle).
  - History, calibration and failure fields are filled at runtime from the decision journal (آیدا) and University scores, never fabricated.
  - **Ask-the-University is mandatory** on question, problem, failure or ambiguity.
- **D-C219** · 2026-10-03 · Vision §2.3.2 · Reporting lines:
  - کوروش → Chief of Staff; بهرام, زرین, سارا, لیلا, مهسا, فرهاد → کوروش (فرهاد dotted to رامین);
  - نگار → دانا; بیژن → کیمیا; شیدا, هومن → فرزانه;
  - سیاوش, فرزانه → آرش + عرفان; بابک → Chief of Staff; داریوش → کوروش (permission from سپهر);
  - مریم, آیدا → گیتی; ژاله → بابک with independent reporting to گیتی; سروش → عرفان;
  - **کیان → the owner directly.**
- **D-C220** · 2026-10-03 · Vision §2.3.3 key "cannot" clauses:
  - کوروش cannot change risk caps, build `ApprovedOrder`, move money, self-approve or enable live.
  - فرهاد cannot raise leverage above the tier cap or make leverage an optimization target.
  - نگار cannot declare news a fact or execute news text as an instruction (prompt-injection defence).
  - بیژن: **order numbers are never read from an image**; a chart signal alone is never an entry basis.
  - شیدا cannot import external code without a gate or add a dependency without a hash pin.
  - سیاوش cannot promote itself or any agent (INV-07).
  - بابک cannot place trades, change the allowlist, hold credentials, or move above-threshold amounts without the owner; an incomplete transfer or unknown address freezes all transfers.
  - داریوش cannot send an order without both رامین's and مریم's stamps, nor bypass the Risk Governor or turn on a live adapter.
  - **مریم: PASS/VETO on every order and venue; the CIO cannot override her veto.**
  - هومن cannot turn `LUCK` into a firm lesson.
  - فرزانه: a certificate is not a trading permit; she cannot let one party both author and grade an exam without an independent reviewer; she may propose new agents (D7).
  - ژاله: declaring a ledger break blocks new entries (INV-12).
  - آیدا can move an agent/strategy to PROBATION but cannot delete agents or change rules; **a journal outage blocks new entries ("decision without record = no decision")**.
- **D-C221** · 2026-10-03 · Vision §2.5–2.7 · No-duplicates register:
  - ژاله **is** the owner's P1§29 Accounting agent.
  - The Credential/Identity agent stays a separate owner-defined seat (`CRED-ID`), never silently merged into بابک or سپهر.
  - The Gold Division's ~22 roles are mostly **profiles** (`@gold`) on existing agents (بهرام, بیژن, فرهاد, نگار, رامین, کیمیا, روشا…).
  - The Risk Governor **is** رامین; Token Identity = تینا; Crypto = کامیار + نیما.
  - کوروش does not replace Agent-01.
  - The Council lacks OSINT and Social seats.
- **D-C222** · 2026-10-03 · Vision §2.6 · Candidate mapping of the 19 owner roles to Persian names (all UNRESOLVED until گیتی + owner decide):
  - 1 → کیان (OWNER-APPROVED);
  - 4 سپهر, 7 کیمیا, 12 رستم, 13 دانا, 14 سامان, 16 قاسم, 17 رضا, 18 آرش, 19 گیتی = CANDIDATE;
  - 5 Identity (تینا vs CRED-ID) and 11 AGI/ACI (آریا vs سیاوش) = COLLISION;
  - **8 Paper Trading = GAP (nobody)**; 15 = فرناز + پریسا (2→1);
  - 2, 3, 6, 9, 10 = UNRESOLVED.

  Unmapped names: عرفان, روشا, کامیار, نیما, رامین, پروانه, پریسا. "No name changes without a governance decision."

**Rotation & playbooks (§4.5–4.6, OA-10)**
- **D-A213** · 2026-10-03 (v1.2 OA-10, owner-approved concept; numbers PROPOSED) · Cross-asset rotation A→B needs:
  - `ER_B − ER_A` ≥ 2 × (exit + entry + switching costs) and ≥ 1 SD of estimation error;
  - caps respected, diversification not reduced (or corr(B, book) ≤ 0.7);
  - minimum hold 5 trading days; staged ≤ 25% of a sleeve per day; cost budget ≤ 30% of expected alpha;
  - council dissent recorded; **a veto from رامین or مریم cancels it**.
- **D-A214** · 2026-10-03 (PROPOSED) · Per-market playbook caps (L3 defaults; pilot halves them with leverage 1×; portfolio caps always win):
  - **Gold:** notional ≤ 20% NAV, leverage ≤ 3×, risk ≤ 0.5%/trade; **roll ≥ 5 business days before First Notice Day, never physical delivery**; liquidation distance ≥ 3×ATR.
  - **Oil:** ≤ 15% NAV, ≤ 2×, ≤ 0.4%; roll ≥ 5 days before last trade, never hold to expiry; no new entries from 5 min before to 15 min after EIA.
  - **BTC/ETH:** ≤ 25% NAV, ≤ 2× (pilot 1×). **Top-50 coins:** ≤ 10% total, ≤ 2% each, ≤ 1.5×. Isolated margin only; annualized funding > 30% bans long perps; venue ≤ 25% of treasury.
  - **Small tokens:** ≤ 1% NAV each, ≤ 5% total, position ≤ 1% of pool depth.
  - **US:** stock ≤ 5%, sector ≤ 15%, region ≤ 30%; single-name short ≤ 2%, total short ≤ 15%; index futures for hedge only, net ≤ 1×.
  - **EU:** stock ≤ 4%, region ≤ 30%.
  - **Asia:** stock ≤ 3%, region ≤ 30%, lot sizes.

  (See C-206 on the L2/L3 references.)

**University engine (§8.3) & research pipeline (§9)**
- **D-F207** · 2026-10-03 20:20 (v1.1, owner-approved concept) · Certification thresholds:
  - L1 (paper analysis): total ≥ 70, safety 100%, Brier ≤ 0.22.
  - L2 (council vote): ≥ 75, each mandatory competency ≥ 65, ECE ≤ 0.10.
  - **L3 (paper order proposal):** ≥ 80, each ≥ 70, ECE ≤ 0.08, blind replay net Sharpe ≥ baseline + 0.3 and MaxDD ≤ baseline, safety 100%.
  - L4 (real-pilot eligibility): ≥ 85 + 3 months shadow with no violations + قاسم/رضا/عرفان sign-off, only after the T-gate.

  Failing drops a level with no vote until re-passed (INV-17). **Certificate ≠ Permission.** Claims in the Knowledge Store carry evidence grade, validity window, contradicts/supersedes and provenance. AskU triggers include **agent confidence < 0.6** and any contradiction with an active claim. A blocking AskU returning UNKNOWN defaults to **"don't trade / shrink"** (INV-16). Research tickets run OPEN → TRIAGED (P0–P3) → … → ENGINEERING_PROPOSAL → ledger → gate (قاسم+رضا+عرفان; locked areas: owner). Quarterly: curriculum review, re-certification, new-agent proposals (D7).
- **D-H238** · 2026-10-03 · Vision §9 · GitHub/paper research pipeline (شیدا → فرزانه):
  - gate = قاسم + رضا + عرفان;
  - **locked areas (Lane A, risk, treasury, constitution) also need owner signature**;
  - integrate = local commit only (**never push**) → shadow → champion/challenger → promote.

**Approved capabilities (§14.1–14.6, OA-11..16, owner-approved 2026-10-03 21:52)**
- **D-E226** · Arena (§14.1, INV-20) · Strategy lifecycle INCUBATION (shadow, no capital) → PROBATION (≤ 2%) → ACTIVE → DEMOTED → RETIRED. Promotion only via gate; **never automatically to real money**.
- **D-E227** · Multi-layer mind (§14.3, INV-22) · Structured bull/bear debate; with consensus, a **mandatory bear** is assigned. Independent judge سروش issues GO / NO-GO / RESIZE / DEFER with calibrated probability. He **cannot override** the risk engine, مریم or the stress gate, cannot join a side, and cannot delete dissent. Layer L5 = the owner, for money tiers only.
- **D-E228** · Long-term memory (§14.4, INV-23) · **Safety-relevant error memories never decay.**
- **D-D213** · Nightly owner report (§14.5, INV-24; M31, lead پریسا) · Short Persian nightly message: what happened, why, what was learned.
  - **All numbers come only from the ledger snapshot**; a number-consistency checker strikes any LLM digit not in the snapshot (shows "—"/UNKNOWN).
  - No secrets, wallet addresses or keys; sent only to the owner's chat_id.
  - **Until the Telegram token is rotated (AD-0128), it is archived in the dashboard only, with send status BLOCKED.**
- **D-A215** · Mother's Safety Fund (§14.6, INV-25) · Owner may set X in 0–50%; **changing X needs the owner's signature** (confirmed value per Pass 1).
  - Separate custody (multisig or cold hardware wallet), outside trading NAV; **only the owner signs; AHOS holds no key**.
  - Never traded (no staking, lending, yield, collateral or margin); **never used to cover trading losses**.
  - USDC/USDT split and any gold/fiat option are owner decisions.
  - Release only to an allowlisted owner wallet via the 7.4 request flow.
  - Activation (M32.7) is HUMAN-GATE with the M26 pilot.

**Token Hunter (§14.8, OA-17, design approved 2026-10-03 22:40; v1.5 extension 22:53)**
- **D-A216** · Data and cost rules:
  - **$0/month cost cap**; paid APIs are never a hard dependency (AD-0358); DEXTools and CMC paid APIs dropped (AD-0359); paid Chainalysis/TRM never (AD-0360).
  - X API has no free tier from 2026 (~$0.005/post) → optional, only with owner budget.
  - Raw responses sha256-stored (AD-0361); keys only in the owner's secret store.
  - Gate never silently PASSes UNKNOWN (AD-0348); RPC holder count = UNKNOWN, never fake (AD-0345); social and narrative feature families never merged upstream (AD-0370); تینا's finding is never rewritten (AD-0665).
  - **Lane A treats "PASS WITH UNKNOWN" as QUALIFIED, frozen (AD-0995); the Lane-B hunter gate is stricter.**
- **D-A217** · Pipeline and trading rules:
  - Identity needs ≥ 2 independent sources and `pair_created_ts`.
  - Safety gate keeps the 4-word vocabulary; **a fifth word is forbidden**.
  - **PRE-LAUNCH is always MONITOR_ONLY; presale/whitelist buys forbidden.**
  - Gate thresholds are Grok's proposals, not owner decisions, tunable only via gate and **never to "enter more"**.
  - Kelly c ≤ 0.10 on calibrated p; **sleeve brake: −30% from sleeve peak halts new entries for 7 days**; time stop: exit if not +20% within 24 h, max hold 72 h (HIDDEN class excepted with review).
  - Never unlimited slippage. **AHOS never sandwiches, front-runs or MEVs other users.**
  - Paid DexScreener boost = advertising cost, zero positive weight. "+100% illiquid ≠ opportunity" (AD-0353). Baseline comparison mandatory (AD-0355).
  - Discovery → full dossier ≤ 45 s target, 90 s hard cap.
- **D-A218** · Legal OSINT (§14.8.3-a, owner addition 22:48; lead نگار, legal veto مریم):
  - public content only; never private groups, paid "signal"/"premium pump" subscriptions or fake accounts;
  - **joining pump groups to trade is forbidden**; read-only, never post;
  - every claim is UNVERIFIED until proven; only CORROBORATED/VERIFIED carry positive weight; rumours are HYPOTHESIS with zero weight;
  - announced pump times are **never used to enter before the announcement** (INV-29).

  White-hat layer (§14.8.3-b, تینا): defensive analysis of public code only (Slither, Mythril with stated limits), **never exploit, never attack mainnet**; an exploit/rug alert blocks entry and closes the position; vulnerabilities are reported only via bug bounty / responsible disclosure **with owner + مریم approval**. Compliance veto (مریم): any "yes" or "unknown" on the checklist = veto.
- **D-A219** · Legal and wallet rules (§14.8.6):
  - no pump-group participation, shilling, rumour spreading, wash trading or MEV;
  - MNPI: no leaked listings or insider-bought info; mempool watching only to detect launches;
  - official APIs only, no ToS-violating scraping;
  - **separate hot sleeve wallet with balance cap; never unlimited `approve` to unknown contracts; revoke approvals after each exit; trading keys have no withdrawal permission**.
- **D-A220** · Acceptance (§14.8.8) and competitive rules (§14.8.10):
  - Live paper ≥ 3 months and ≥ 50 entries; realized slippage within limit in ≥ 95%; 0 cap breaches; FIXTURE results never reported as real detection rates.
  - Red-team must reject "listing leak" messages, pump-group invites and exploit requests.
  - Block-0 launch sniping / Jito bundles **forbidden (INV-26) unless the owner HUMAN-GATE M33.24 opens it, and even then INV-28..30 hold**.
  - Blind copy-trading (GMGN/Axiom/Trojan) forbidden; wallet reputation is just one as-of feature with decoy detection; insider/dev clusters are risk signals, never an MNPI source.
  - AHOS's edge is "understanding sooner, not buying sooner".
  - **No model promotes itself**: challenger runs in shadow; promotion only through `evolution_gate` with قاسم + رضا + عرفان. No new "Token Hunter agent" (reuse کامیار etc.).

**Self-completing layer (§14.10.1–3, OA-22, owner-approved 23:44)**
- **D-E229** · 2026-10-03 · Vision §14.10.1–2 · One-way loop:
  - M47/M46 only discover and write lessons to M49; M51 only reads M49 and patches on a separate branch; M51 never writes to M49 or runs on its own output.
  - **M50 scores are never promotion evidence** (`[OBSERVED]` only).
  - Outputs of M46/M48/M51 are local commits on separate branches through 16/19/05 — **no auto-merge, no push, manual merge by the owner**.
  - Changing lists, gates, caps or governance docs needs an **owner L2 record in `AHOS_ISSUE_REGISTER.md`**.
  - **کیان, Gemini and the mission itself never VERIFY**: VERIFY = 16 (قاسم) only, CHALLENGE = 19 (رضا) only.
  - Low-privilege user + firewall rule for M45 is a one-time owner human gate; otherwise M45 fails closed.
  - One scheduler, not 8 daemons; at most one heavy job at a time; **M45 and M50 never in parallel (8 GB RAM)**.
  - Self-improvement never raises its own authority or touches gates, `policy.py`, risk caps or the registry.
- **D-E230** · 2026-10-03 · Vision §14.10.3 · Per mission:
  - Research scout uses official APIs (arXiv with rate spacing, GitHub REST Search, not scraping trending); results never auto-flow to paper or live.
  - **M46 auto-RCA patches only on a separate branch/working copy; never push, never apply.**
  - **M47 health: READ / DOWNGRADE / HALT only**; auto-restart only for listed safe components with backoff, never risk/treasury/execution; it cannot delete logs; **unHALT only with the owner's signature**; TLS never disabled.
  - Lessons never change gates or caps (L2 record needed).
  - **M50 weekly intelligence test: Saturday 08:00 Tehran (owner's choice)**; question set and answer key outside runtime reach (hash only); results with bootstrap uncertainty and n, labelled `[OBSERVED]`, reported by کیان.
  - M51: best verdict `PASS_WITH_GAPS`; forbidden to touch gates, policy, caps, its own authority, the registry, or the protected list.

**Skill marketplace (§14.11, OA-23, owner request 23:57)**
- **D-C223** · 2026-10-03 · Vision §14.11 · Status `[PLANNED]`/VISION **until separate owner approval**. M52 is a daemon job, not an agent.
  - "Acquire" means propose → evaluate → gated adoption: branch (M46/M51 path) + test-integrity receipt + VERIFY 16 + CHALLENGE 19 + **manual owner merge** → registry (version, hash, expiry).
  - Strong copyleft (GPL/AGPL) only with مریم + owner decision. GitHub stars are a weak signal only.
  - **Suggested expiry 90 days**, then disabled until re-evaluated.
  - Always forbidden to skills: money, withdrawal, order path, wincred, protected paths, registry/policy, agent activation. A skill can never grant authority (`AUTHORITY_CLASS` unchanged).
  - MCP servers/executable plugins run only in an isolated child, never in the daemon or کیان's process.
  - Paid skills: `LOCKED_PENDING_KEY_AND_OWNER_BUDGET` with a monthly cap and cost meter. Acceptance S-7: zero auto-install, zero auto-merge.
- **§15 references:** the R-numbered bibliography (e.g. R1 TradingAgents, R2 FinMem, R3 FinCon, R4 FinAgent (with a K-line leakage caveat), R5–R6 FinRL, R7 FinGPT, R8 Qlib, R9 RD-Agent, R10 Chronos …). No decisions; the file says "all real and checkable".

### P2.6 Traceability addenda `RG\ALL_DOCS_ADD_v13.md`..`v18.md` (OWN-AV-64..202; vision v1.2–v1.8, all 2026-10-03, Tehran times)
These six files are append-instructions for ALL_DOCS_TRACEABILITY §5b. Most rows restate vision items already captured above (D-A15/16, D-A20, D-C05/06, D-C13, D-D09, P2.5). Only the rows not already in this brief are listed here.

- **D-A260** · 2026-10-03 20:44 (v1.2, OWN-AV-69, INV-19) · Panel numbers come **only from the ledger**. **PAPER and LIVE are never summed.** An unknown value shows as "—", **never 0**. Status: HUMAN-GATE (locked). (`RG\ALL_DOCS_ADD_v13.md`)
- **D-A261** · 2026-10-03 21:52 (v1.3, OWN-AV-76, INV-21) · Every **Major Decision** needs a stress-test PASS, and a FAIL blocks it. A Major Decision is: ≥5% NAV, any leverage increase, rotation ≥10%, a new market / venue / ACTIVE strategy, or any ladder step. OWN-AV-86 adds that every ladder step also needs a judge verdict, and **neither replaces the owner**. (`v13`)
- **D-A262** · 2026-10-03 21:52 (OWN-AV-72/73) · There is **one statistics library** (DSR, PBO/CSCV, MinTRL, BH-FDR, White RC, Hansen SPA, Romano–Wolf). M25 reuses it; **no second copy**. Status: MISSING.
  - Paper allocator: Bayesian Sharpe shrinkage, Thompson sampling, HRP, **≤20% per strategy, 10% exploration**, EMA-smoothed weights. (`v13`)
- **D-A263** · 2026-10-03 21:52 (OWN-AV-74) · The crisis simulator uses **10 named historical episodes** (1987, 2008, 2010 flash crash, 2013 gold, 2015 CNY, 2020 COVID, 2020 oil, 2022 LUNA, 2022 FTX, 2023 USDC), each labelled FULL / PARTIAL / PROXY. (`v13`)
- **D-D260** · 2026-10-03 21:52 (OWN-AV-82, INV-24) · The nightly owner report is **short Persian, ≤12 lines, at 23:45 Tehran**: done / why (decision_ids) / learned (claim_ids). It is idempotent and archived on the dashboard.
  - A number-consistency checker removes mismatches. PAPER/LIVE status goes on the first line.
  - OWN-AV-137 (v1.6): **Kian writes and sends it** (extends M31, not a second reporter). It appears on the dashboard now and on Telegram after AD-0128. (`v13`, `v16`)
- **D-A264** · 2026-10-03 22:40 (v1.4, OWN-AV-105) · Token Hunter acceptance requires a **paper marathon of ≥3 months and ≥50 entries**. Live private routing is a HUMAN-GATE tied to the M26 pilot. (`v14`)
- **D-A265** · 2026-10-03 22:53 (v1.5, OWN-AV-119/120) · **Pump.fun graduation alone never means ENTER.** A migration state machine (bonding curve → graduation → PumpSwap/Raydium) has a post-migration observation window.
  - M33 execution order: M33.1–11 → M33.16–23 → M33.12–14 → M33.15 / M33.24 (both HUMAN-GATE). (`v15`)
- **D-A266** · 2026-10-03 22:53 (OWN-AV-115) · Speed is for **discovery and exits, not block-0 entry**. A private RPC or dedicated node is only an optional Tier-4 budget item.
  - Proposed p95 budgets: exit trigger → paper order ≤2 s; discovery → dossier hard cap 90 s.
  - These are design proposals, not measurements. (`v15`)
- **D-E260** · 2026-10-03 22:53 (OWN-AV-126, INV-33) · Opening the dashboard calls **`world.ensure_running()`** (idempotent). This starts the always-on supervised runtime that runs every loop. Self-improvement happens only via the sandbox. (`v15`)
- **D-E261** · 2026-10-03 23:04–23:21 (v1.6, OWN-AV-135) · Human-gate approvals use a **one-time code issued and verified by the gate service, not by Kian**.
  - The code is single-use, bound to the payload hash and **valid 10 minutes**.
  - Replay, expiry or any content change makes it invalid. (`v16`)
- **D-E262** · 2026-10-03 (v1.6, OWN-AV-136) · Kian safety measures:
  - taint labels and spotlighting;
  - no write tools from tainted content;
  - a رضا attack corpus in CI;
  - a hash-chained audit of every Kian action;
  - proposed rate limits of **30 messages/min and 60 tool calls/min**. Status: MISSING. (`v16`)
- **D-E263** · 2026-10-03 23:14–23:17 (OWN-AV-142) · Paid-model budget: a **monthly cap set by the owner, default 0**. A per-call cost meter in router.py is recorded in the ledger. **Warning at 80%, automatic lock at 100%.** (`v16`)
- **D-B260** · 2026-10-03 23:44 (v1.7, OWN-AV-173) · A **one-time owner human gate** creates the low-privilege Windows user and the firewall rule, using a setup doc. **If either is missing, M45 Auto-Lab fails closed.**
  - Isolation is a short-lived child process under Windows Job Object caps (RAM, CPU, process count, time). (`v17`)
- **D-B261** · 2026-10-03 23:44 (OWN-AV-177/178) · Process boundary and boot order: **Next → daemon + Kian endpoint → Telegram last**. A crash stops only the components that start after it.
  - Decision records: **DR-KIAN-AUDIT-01** (Lane B SQLite audit store under data/, سپهر's 4 conditions) and **DR-KIAN-TS-GEMINI-02**. The Gemini logic in the TS path is **archived, not deleted**, and TS only displays. (`v17`)
- **D-H260** · 2026-10-03 (all six files) · **Process fact.** As of these files, the ADD rows are append-instructions ("Append to ALL_DOCS_TRACEABILITY.md §5b…"). Whether they were merged into ALL_DOCS_TRACEABILITY is checked in P2.8 below.
  - Every ADD file states that its latency budgets, thresholds and model targets are **design proposals, not measurements**.
- **Correction / evidence for C-210:** OWN-AV-145 (v1.6 header) records the vision's trust order as **human > repo > governance > evidence > Master Context > Charter > Vision**. Here repo sits above governance and safety, the same as the Charter wrapper. Exec §3 and P2 §117 put safety above repo reality (see C-210 below).

### P2.7 `RG\UNIVERSITY_AND_AGENTS_DISCOVERY.md` (Phase 8b, 2026-10-02, Claude/Atria, read-only discovery) and `docs\supervision\*` (2026-09-12 council docs)

**University and agents discovery (read in full):**
- **D-C260** · 2026-10-02 (§2.4, from AGENT_TAXONOMY_MAP, verified against live code) · **Blocking fact for agent activation:**
  - All 19 Slice-1 canonical agents are seeded at `MaturityLevel.REGISTERED` (0).
  - `MINIMUM_MATURITY_FOR_ALLOW = 2` (IMPLEMENTED), so **no Slice-1 agent can be granted execution authority**.
  - Since 2026-09-27 the legal ramp `AgentRegistry.advance_maturity` exists (fail-closed, evidence-mandatory, audit-logged, never called by any seed or production path).
  - **Raising maturity requires per-agent evidence, not an edit to the floor.**
- **D-C261** · 2026-10-02 (§2.2) · Only **AG-15 Decision Engine and AG-16 Paper-Trading hold DECIDE authority**, and neither is a Slice-1 anchor. AG-09's veto is deterministic, never an AI veto. Never grant DECIDE to a Slice-1 anchor.
- **D-H261** · 2026-10-02 (§4) · **Phased org plan U0–U6** (each phase starts only when the previous one is TESTED with receipts; all PAPER_ONLY):
  - U0: canonical agent inventory + a regression guard against namespace collapse;
  - U1: launcher;
  - U2: per-anchor evidence packages + human-gated `advance_maturity`, one anchor at a time;
  - U3: control plane becomes a service (first non-test importer of `architecture/control_plane.py`);
  - U4: Mission Controller = first consumer of `data/dev_missions/dev_missions.jsonl`;
  - U5: University registries (research / skill / failure) + permanent benchmark loop + hand-off into the dev-mission queue, **dashboard/Telegram surface only after real records exist**;
  - U6: the teams registered as agents.
- **D-H262** · 2026-10-02 (§4–5) · **Three decisions are human-gated and must not be made unilaterally:**
  - which agent namespace is authoritative for M11;
  - each maturity advance;
  - **whether the Mission Controller may auto-dispatch or only propose dispatch**.
- **D-F260** · 2026-10-02 (§2.1, §4 U5) · University = **zero code** (ladder PLANNED, not PARTIAL; a repo-wide search found no university / research_registry / skill_registry / failure_memory).
  - The Phase 8a dev-mission queue is to be **"the system's single legal intake"** for University engineering hand-offs.
  - It has a writer (chat) and no reader. Until U4 exists, the chat reply «ثبت شد… کاری هنوز انجام نشده است» ("Recorded… no work has been done yet") remains literally true.
- **Correction to C-201 (taxonomy count):** this report counts **five** namespaces: `agent.*` (19, ahos_org/registry.py), `AG-*` (25, config/agent_registry.yaml, `orchestrated: 0`), `AGENT-*` (10 + 15, frozen), `agent.org.*` (19, PLANNED doc), and `A`–`H` (8 M0 evaluation roles). Status: `RECONCILED_NOT_MERGED`. There is also an "agent 01" collision across four of them.

**Supervision docs (council charter, architecture v2, protocol, latest directive, two cycle records, vision alignment audit read in full; owner journey audit read keyword-filtered). Dated 2026-09-12/13; file mtimes 2026-09-24. These are the pre-October oversight regime; nothing found marks them superseded, but the October mission plan has overtaken their sequencing.**
- **D-H263** · 2026-09-12 (SUPERVISION_ARCHITECTURE v2; council charter) · An **Independent AHOS Oversight Council** (not a code builder) supervises the build agent (Cursor config `bc-2773f4bf…`). Principle: **event-driven > schedule-driven**.
  - Four layers: L1 immediate on PR / commit / security / Lane-A / readiness-claim events; L2 operational every 30 min (delta-only); L3 strategic every 4 h; L4 milestone gates G0–G6, where **"tests green alone ≠ pass"**.
  - Hourly supervision was retired 2026-09-12.
  - Directive vocabulary: ALLOW / MONITOR / DO / DO_NOT / FIX_BEFORE_CONTINUE / FIX_BEFORE_MERGE / BLOCK / STOP / ESCALATE_TO_HUMAN.
  - 20-specialist council.
  - **PRE-FLIGHT / POST-FLIGHT report on every material change** (a missing POST-FLIGHT means FIX_BEFORE_CONTINUE).
  - Stall flag after ≥2 operational cycles without progress.
- **D-H264** · 2026-09-12 (LATEST_DIRECTIVE_FOR_AHOS_AGENT, updated 2026-09-12) · **Owner safety locks §20 (S20-1..9):**
  - Lane A do not touch;
  - hold W4 Slice 7;
  - **do NOT merge PR #103**;
  - **do NOT start Slice 8**;
  - no new identity authority;
  - no historical mapping;
  - no readiness upgrade claims;
  - no fixture patch to fake green;
  - no aesthetic-only architecture.
  - Escalate to human: Telegram token rotation (S-01) and Windows soak start. *(Whether #103 / Slice 8 were later resolved was not checked in Pass 2.)*
- **D-H265** · 2026-09-12 (AHOS_VISION_ALIGNMENT_AUDIT §11) · **FINAL BEST PATH (Sept):**
  - Phase 0 human ops (rotate token, Windows G1–G10, soak window);
  - Phase 1: W1.3 spoof hardening, merge W2 (#95) only, DOSSIER + DOC_TRUTH_MAP, stop W4;
  - Phase 2: P1 product (FA chat E2E, Telegram, loud alerts web + TG, contract display);
  - Phase 3: selective W4, human per slice;
  - Phase 4: soak + calibration;
  - Phase 5+: Environment Engine, AGI research, multi-market.
  - Self-critique recorded: "foundation first became research first"; the council over-weighted W4 PR depth and under-weighted owner P1.
- **D-H266** · 2026-09-12 (AHOS_OWNER_JOURNEY_LAUNCH_ACCEPTANCE_AUDIT) · **Verdict NO.** The owner could not complete Mission A (discovery → identity → security → evidence → score → decision → chat → alert → paper) end to end.
  - J0–J12 max at "Tested (E2)"; launch contract 0/15 operational proofs.
  - Calibration: 352 predictions, **0 eligible pairs**.
  - Telegram test log was SIMULATED.
  - FALSE-GREEN list FG-1..FG-10 (e.g. "2128 tests pass" on the agent host ≠ Windows; agent-host gates ≠ Windows evidence).
  - Gate chain: G-HUMAN-0 → G-OPS-1 → G-BUILD-1 → G-BUILD-2 → G-BUILD-3 → G-VALID-1 → G-VALID-2 → G-LAUNCH-1. **LAUNCH_READY only at E4+ on the owner's Windows.**
  - One-Brain risks: OBR-1 Python vs TS scoring (HIGH); OBR-2 three paper ledgers; OBR-3 W2 off main; OBR-7 dual provider-health writers.
- **D-C262** · 2026-09-15 (`docs\protocols\AGENT_SUPERVISION_PROTOCOL.md` v0.1.0, DESIGN_ONLY, RUNTIME_VERIFIED=NO) · **Every charter must name who assigns, reviews, challenges, verifies, rejects, changes the mission, and changes the authority.**
  - Defaults: the human assigns and changes the mission; authority changes need human governance plus a code change, **never the agent**.
  - Agent One may request and collect, never verify itself.
  - Slice-1 `agent.red-team` ≠ planned agent 19.
  - A 19-agent org supervisor is **absent** (DEFERRED_IMPLEMENTATION).
  - "POLICY ≠ SECURITY BOUNDARY": in-process Python is not a security boundary.
- **Correction (reality-ladder variants, extends the P2.1 note):** more ladders are in use:
  - Supervision 5-state: DESIGNED / IMPLEMENTED / TESTED / VALIDATED / OPERATIONAL.
  - Supervision 8-state: … INTEGRATED → OPERATIONAL → PRODUCTION_READY → LAUNCH_READY, where insufficient evidence = UNKNOWN.
  - Discovery: PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < OPERATIONAL.
  - Owner-journey evidence grades E2 / E4.
  - NS-10 scorecard: VISION / DESIGN / IMPLEMENTED / TESTED / OPERATING.
  - There is still no single ladder.

### P2.8 `RG\OWNER_DIRECTIVE_TRACEABILITY.md` (generated 2026-10-03, mtime 2026-10-05) and `RG\ALL_DOCS_TRACEABILITY.md` (mtime 2026-10-03 20:44)
OWNER_DIRECTIVE_TRACEABILITY: summary, missing items, governance contradictions, duplicates list and OWN-1..37 rows read in full; HUMAN-GATE / UNKNOWN rows filtered from the 594-row matrix. ALL_DOCS_TRACEABILITY: rules, summary, supersession register, DECIDED contradictions, North Star / NS rows, CH rows and §6 read in full; the 1,211 AD rows were only filtered for SUPERSEDED / DECIDED / CONFLICT.

- **D-H267** · 2026-10-03 (ALL_DOCS rules 1–7) · Traceability rules:
  - **Supersession: the newest owner statement wins** (doc or commit date). Older items are marked SUPERSEDED and are never active.
  - **Locked regardless of date (never superseded; owner may lift explicitly, agents never):** PAPER_ONLY / no real money; no secrets in git / logs / prompts; **no push** (push URL `NO_PUSH_owner_rule_local_only`); constitution / governance / authority changes; Lane A / CDA changes.
  - Remaining contradictions are **resolved by a recorded technical decision (DECIDED)**: "No contradiction is left for the owner to answer."
  - Dedupe means MERGED → existing row id.
  - Every mission ticks its OD / AD / CH / NS rows at close, with evidence.
- **D-H268** · 2026-10-03 (ALL_DOCS §3, **DECIDED contradictions D1–D13**). Several were open in this brief:
  - **D1:** PAPER_ONLY stays. Gold first on real-market data with fake money; live only via the ladder + an explicit owner gate.
  - **D2:** full autonomy only for safe reversible engineering (debug, refactor, tests, docs, local commits); the locked set stays gated.
  - **D3:** keep **PGlite** as the M10 store; portable PG via pg_ctl = documented fallback; Docker volumes kept for rollback.
  - **D4:** gold-paper track runs **inside M13**; mission order M9→M19 unchanged.
  - **D5:** one AI core serves Telegram and dashboard; **dashboard stays canonical for state**.
  - **D6:** SQLite stores canonical; former Postgres tables in PGlite; `postgresql_schema.sql` historical.
  - **D7:** add agents freely when a mission needs them (charter / boundary / evidence / lifecycle each); **count is never a KPI**.
  - **D8:** keep the 3D/web trees as **read-only design references**; build only in CommandCenter.tsx/app (M17).
  - **D9/D10:** launcher has no Docker; use the 18:49 mission order.
  - **D11:** the vision's treasury / custody design **supersedes** the P1 §30–31 credential-agent transfer idea; testnet only.
  - **D12:** vision lifecycle (PROPOSED→…→RETIRED) = maturity axis; old REGISTERED→… states = runtime activity states inside ACTIVE.
  - **D13:** $100→$1M is an aspirational benchmark only; it never changes caps (INV-15).
- **D-H269** · 2026-10-03 (ALL_DOCS §2 supersession register) · Superseded items not already in this brief:
  - **12 older readiness/truth maps** bannered STALE by M9 (d2aa09b), replaced by REMAINING_REALITY_REGISTER;
  - `docs/archive/**` (170+ docs, consolidation 2026-09-26) historical;
  - **MASTER_DIRECTIVE_v1 superseded where W43 restates it, but Class A rules are never demoted**;
  - the Phase-18 "do not touch architecture/" grant expired with its phase;
  - single_start_runtime "docker compose + Temporal" superseded by 18:49 + PGlite.
  - **OD-416 (P2 §93 crypto-first roadmap) SUPERSEDED on priority by OD-575 (OWN-18 gold first).**
- **D-B262** · 2026-10-03 (OWNER_DIRECTIVE_TRACEABILITY "Existing duplicate / parallel implementations") · Recorded parallel copies that must be extended or consolidated, never multiplied:
  - 4–5 website/3D trees;
  - `slills/` (typo, 16) vs `.cursor/skills/` (11);
  - `agent_org/` vs `ahos_org/`;
  - `tests/` vs `tests2b/`;
  - paper engines v1/v2/v3 + three schemas;
  - three council implementations;
  - two whale modules;
  - two identity modules;
  - two security gates (+ TS);
  - two positions modules;
  - two news modules;
  - **six launchers** (M11 consolidates);
  - three DB schemas;
  - **five provider registries**;
  - overlapping requirement registers.
- **D-H270** · 2026-10-03 (OWNER_DIRECTIVE_TRACEABILITY "Most important MISSING") · Missing items mapped to missions, with an explicit "extend, don't create" target for each:
  - UNI → M16 (reuse self_research / strategy_lab / research_worker);
  - GOLD → M13 → M18 (**no parallel gold engine**);
  - MISSIONCTL → M14 (build on mission/ledger.py + dev_missions.ts, **not a new controller package**);
  - LIFE → M12 (extend registry REGISTERED→IMPLEMENTED path c7ed457);
  - AGCOMM → M12;
  - LOWLAT / MULTIMKT → M19;
  - FINXFER → M18 design-only;
  - SEC:whitelist → M13 (extend contract_analysis / holder_analysis);
  - SRC:Development → M13 / M18.
- **D-E264** · 2026-10-03 (ALL_DOCS §5 CH-02, CH-05, CH-07; owner chat) · Owner chat orders recorded as rows:
  - **CH-02: no visible console windows at launch** (hidden processes, status via dashboard/tray), MISSING;
  - **CH-05: every mission prompt reviewed before work by آرش + the domain specialist + پروانه + گیتی**, MISSING;
  - **CH-07: delivery sign-off by قاسم, رضا and عرفان** before acceptance;
  - CH-09: local commits only, never push (locked).
  - **Note:** the review line-up here (آرش + specialist + پروانه + گیتی) is the 2026-10-03 version; check it against any later change before applying.
- **D-E265** · 2026-10-03 (ALL_DOCS §4 NS-01..NS-11) · North Star capability rows. Two are not elsewhere in this brief:
  - **NS-10: an honest capability scorecard in the dashboard** labelling each capability VISION / DESIGN / IMPLEMENTED / TESTED / OPERATING (MISSING, M17);
  - **NS-11: one domain-agnostic cognitive loop serves crypto, gold and later markets, with no per-market forks**.
- **D-H271** · 2026-10-03 (both matrices, summary rows) · **Matrix size.** OWNER_DIRECTIVE_TRACEABILITY: 594 atomic owner requirements. ALL_DOCS: 1,888 rows (OD 594 + AD 1,211 + CH 9 + NS 11 + OWN-AV 63), with statuses IT 227, PARTIAL 1,384, PLANNED 16, MISSING 129, HUMAN-GATE 124, UNKNOWN 5, SUPERSEDED 3.
  - "IMPLEMENTED+TESTED" ≠ operating (paper loop 0 rows; agents REGISTERED; stores empty).
  - **ALL_DOCS stops at OWN-AV-63 (vision v1.0/v1.1).** The ADD_v13–v18 rows OWN-AV-64..202 were **not merged**: a search for OWN-AV-64 / 88 / 131 / 166 / 190 / 202 found nothing.
- **Corrections to Pass 1 contradictions (now resolved by the project's own DECIDED records):**
  - **C-01** (DB store) → D3 / D6: PGlite + SQLite canonical, pg_ctl fallback.
  - **C-07** (OWN-6 / OWN-7) → D1 / D2. Pass 1 said these "need an owner decision"; the matrix records them as DECIDED and kept HUMAN-GATE for the locked set.
  - **C-03** → D10: use the 18:49 order. C-04 is partly addressed by D7 (count not a KPI); the actual count mismatch remains.

### P2.9 Pass 2 contradictions (new; each stated once with both sources)
- **C-201 Agent taxonomy count.** Four taxonomies (P1 M0 addendum; GM-08 namespaces: engineering / agent / AG / AGENT / agent.org / M0) vs three (REMAINING_REALITY_REGISTER CC-2: `agent.*`, `AG-*`, `AGENT-*`) vs two (vision §2.6, functional 19 vs persona roster) vs **five** (UNIVERSITY_AND_AGENTS_DISCOVERY §2.2, `RECONCILED_NOT_MERGED`). All sources agree on "no silent merge"; they disagree on what is being kept apart. The authoritative namespace for M11 is a human-gated decision (D-H262).
- **C-202 Agent build-out pace.** P1 M0 addendum: "do not build dozens of new agents… control plane first", and the discovery doc: no agent gets authority before evidence packages and maturity ramp (U0–U3). Against these: the vision's 39-agent roster and owner raw OWN-17 "add as many agents as needed". ALL_DOCS D7 resolves **count** (add when a mission needs it), but not **sequencing** against the control-plane-first order. Partially resolved.
- **C-203 Self-development permission.** Owner raw P2 L7187 ("no permission from me" to learn / debug / develop / update) vs P1 §26, addendum §14 / §16, Mandate §16, INV-35 / INV-37 (governance + IV required; no self-escalation). **Resolved by ALL_DOCS D2** (autonomy for safe reversible engineering only; locked set gated). Listed because the owner's own words remain broader than the resolution.
- **C-204 Gold-first vs roadmap.** Owner raw OWN-18 gold first (paper money, then other lines) vs P2 §93 (Phase 1 token discovery; gold Phase 6) and Exec §12 (multi-market only after the foundation is stable). **Resolved by ALL_DOCS D4 / OD-416 SUPERSEDED:** gold paper inside M13. Still in tension with the vision / roadmap token-first M33 Token Hunter emphasis (C-12) and with the Sept supervision North Star (token-opportunity intelligence first, multi-market "FUTURE"; D-H265).
- **C-205 Primary interface.** P2 §38: the website is the primary interface (P2 §48: Telegram secondary) vs the owner's wish for a desktop app window (Sultan chat, D-D10) + CH-01 one desktop icon + OWN-36 the same AI in Telegram and dashboard. ALL_DOCS D5 resolves Telegram vs dashboard (one AI core, dashboard canonical for state). **Browser site vs desktop window is still open** (the Chrome app-mode launcher was proposed, not confirmed built).
- **C-206 Playbook tiers and venue caps.** Vision §4.6 playbook caps still reference the superseded L2/L3 tiers (L0–L5 SUPERSEDED by T0–T4, OWN-AV-146), and venue ≤25% of treasury (§5) vs broker ≤40% (§11.0). The "stricter wins" rule exists, but the text is not reconciled (related to C-06).
- **C-207 Deletion / cleanup.** Mandate §30 "remove unnecessary / impressive-only things" vs P1 §57 / §106 (preserve presentation trees; evidence-backed deletion only), addendum §16 (destructive delete gated) and DR-KIAN-TS-GEMINI-02 "archive, not delete". ALL_DOCS D8 resolves the 3D trees (keep as read-only references). The general Mandate §30 cleanup authority is unreconciled.
- **C-208 Meaning of M13 (and M14–M16).** CLAUDE_CONTINUATION_GUIDE Phase 8a / UNIVERSITY_AND_AGENTS_DISCOVERY: "M13 autonomous engineering core / mission controller", M15 = University. Mission plan / ALL_DOCS §4 / OWNER_DIRECTIVE_TRACEABILITY: M13 = paper + learning (+ gold paper), **M14 = autonomous engineering core / mission controller, M15 = contradictions + council, M16 = University**. Same root as C-03; use the 18:49 / ALL_DOCS numbering.
- **C-209 Credential / transfer agent.** Owner raw OWN-31 (credentials for account opening, transfers, cash-out, conversions, deposits to a personal account) vs P1 §30 (no financial authority), INV-36 (withdrawal request-only), the vision's بابک READ + PROPOSE limits, and the Sept supervision "FORBIDDEN — never" (discovery §3 row 10). **Resolved by ALL_DOCS D11** (vision treasury design supersedes; testnet only; OWN-32 transfers HUMAN-GATE). The owner's literal ask remains broader.
- **C-210 Trust order.** ALL_DOCS rule 1 and the vision v1.6 header (OWN-AV-145): human > **repo reality > governance/safety** > evidence > Master Context > Charter > Vision; the Charter wrapper is similar. Exec §3 and P2 §117 put **safety above repo reality**. These give opposite results when the repo state is itself unsafe. Unresolved.
- **C-211 Contradiction-handling policy.** `docs/governance/M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION.md` (2026-09-28, AD-0126): "When two statements in PART B conflict, **record the contradiction; do not resolve it**". AD-0520 / 0521 / 0858 / 1051 add that the known org contradiction (Dual-19) **must remain visible**. ALL_DOCS rule 4 (2026-10-03) says the opposite: contradictions are **resolved by a recorded technical decision (DECIDED)**; "No contradiction is left for the owner to answer". (Source: ALL_DOCS_TRACEABILITY L5–15, L1204, L1993–1994.)
- **C-212 Mission controller dispatch authority.** UNIVERSITY_AND_AGENTS_DISCOVERY §4 U4 / §5: whether the controller may auto-dispatch is **human-gated**. NS-05 (ALL_DOCS) describes it as "consumes the dev-mission queue → plan → build → test → review/sign-off → local commit" (autonomous), and the owner's raw orders (OWN-15 "built and used immediately"; OWN-6) favour autonomy. No recorded decision found.
- **C-213 Traceability coverage.** ALL_DOCS_TRACEABILITY says every mission must tick its rows, but the file stops at OWN-AV-63 (v1.1). The six ADD files (OWN-AV-64..202, vision v1.2–v1.8 including T0–T4, the treasury design, Kian, M44–M52) say "append to §5b" and were not appended (D-H271). D11 / D12 cite vision sections whose traceability rows are absent from the matrix.

**Owner-order count in Pass 2:**
- 15 raw-voice owner orders in P2.4 (OWN-1..37 compressed into D-P221, D-E219..222, D-A211, D-G202 / 203, D-C215 / 216, D-F206, D-D207 / 208, D-P222).
- Numbered owner orders extracted in P2.1–P2.3 from P1 §0–119, the M0 addendum (items 1–20), the Autonomous-engineering addendum §1–29 and the P2 Completion / Execution Mandates (see those sections).
- Plus 4 owner chat orders newly recorded from the CH rows (CH-02, CH-05, CH-07, CH-09).

### P2.10 Pass 2 source index (what was and was not finished)
**Finished (read in full or in full for all decision-bearing parts):**
- owner_directive_part1.txt (all heading-only sections, M0 addendum, Autonomous-engineering addendum §1–29)
- owner_directive_part2.txt (MASTER CONTEXT, Completion / Execution Mandates, raw owner notes L7187–7197)
- ALL_DOCS_ADD_v13..v18 (all rows)
- UNIVERSITY_AND_AGENTS_DISCOVERY.md
- AHOS_AGENT_SUPERVISION_COUNCIL.md, SUPERVISION_ARCHITECTURE.md, AGENT_SUPERVISION_PROTOCOL.md, LATEST_DIRECTIVE_FOR_AHOS_AGENT.md
- CYCLE_OWNER_JOURNEY_AUDIT / CYCLE_VISION_AUDIT (2026-09-12)
- AHOS_VISION_ALIGNMENT_AUDIT.md
- the persistence folder re-list (no new chat blobs; only the current Sultan chat grew, not restated)

**Partial (keyword-filtered or section-filtered; stated honestly):**
- GROK_HANDOFF.md: unread chunks keyword-filtered plus L300–362, 396–430, 582–626 in full.
- CLAUDE_CONTINUATION_GUIDE.md: L224–804 and 886–1287 keyword-filtered.
- REMAINING_REALITY_REGISTER.md: states and gates filtered plus five ranges in full.
- AHOS_AUTONOMOUS_VISION.md: charters and §9 / §14 / §15 filtered; §2.4–2.7, §4.5–4.6 in full.
- AHOS_OWNER_JOURNEY_LAUNCH_ACCEPTANCE_AUDIT.md: headings, verdicts, gates, FG / OBR rows.
- OWNER_DIRECTIVE_TRACEABILITY.md: summary sections + OWN rows in full; 594-row matrix filtered for HUMAN-GATE / UNKNOWN.
- ALL_DOCS_TRACEABILITY.md (526 KB): rules, summary, §2–§6 in full; 1,211 AD rows filtered for SUPERSEDED / DECIDED / CONFLICT only.

**Not read in Pass 2:**
- The AGI/ACI Charter v1.0 body: not present inside part2, only its wrapper. The separate file `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` was not opened.
- Supervision extras not on the task list: AHOS_PROJECT_TRUTH_MODEL.md, AHOS_REALITY_MAP_v1.md, CONNECTION_PROTOCOL.md, AHOS_AGENT_WAKE_MESSAGE.md, AID_M1_POSTMERGE_STATIC_PR108.md, M3_W14_RESOLVER_MINT_BRIEF.md, the other cycle files and gates/G0.
- OWNER_DIRECTIVE_MISSION_PLAN.md L501–609 (still unread since Pass 1).
- The archive vision files (AHOS Ultimate Vision v1.0, System Vision v1.0).
