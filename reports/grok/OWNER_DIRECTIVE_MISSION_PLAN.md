# OWNER DIRECTIVE MISSION PLAN (derived by Grok, 2026-10-02 ~18:50 Tehran)

Sources: docs/owner_directives/owner_directive_part1.txt (Master Autonomous Execution & Completion Directive + Autonomous Engineering addendum),
docs/owner_directives/owner_directive_part2.txt (AHOS MASTER CONTEXT v2.0 + Completion Mandate + Autonomous Master Execution Mandate).
These documents are VISION/REQUIREMENTS, not authority and not evidence (part1 add. §28, part2 §159). Reality ladder:
PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < OPERATIONAL. Never PLANNED=DONE, never CODE EXISTS=OPERATIONAL.

Ordering rule: part1 §85 priorities + part2 §127 (Truth > Identity > Security > Governance > Verification > Reliability >
Data Quality > Paper Trading > Learning > Cognitive Expansion > UX > Low-Latency > Multi-Market > Controlled Live Execution)
and the 32-item technical goal list (Mandate §12). Dependency reality in the repo overrides this order.

## Done before this plan (per GROK_HANDOFF, self-tested, not independently verified)
GM-02..GM-09, Phases 4-7b (chat gate, presentation, Gemini phraser, intent router, conversational AI with confirm-gated paper commands),
Phase 8 (in progress at plan time): dev-mission intake tool + UNIVERSITY_AND_AGENTS_DISCOVERY.md.

## Ordered missions (each = one Claude mission; tests + docs sync + local commit each)
M9  Truth & Remaining Reality Register: full test baseline (pytest/tsc/eslint/selftests), import-time side-effect audit+fixes,
    Remaining Capability Graph (nodes/deps/proof/governance edges, critical path) -> reports/grok/REMAINING_REALITY_REGISTER.md;
    sync stale truth maps/gap registers; Failure Memory entries for fixed bugs. (Mandate §12 items 1-4; part1 §76-80, §2)
M10 Identity/provenance + epistemic separation: token identity safety (chain+contract canonical id), provenance on records,
    Evidence/Claim/Hypothesis/Prediction/Observation/Outcome typed separation in the data model; TCB/session hardening tests.
    (items 5-7, 17; part2 §4-5)
M11 Agent Organization v1 (control plane, read-mostly): agent registry for the 19 agents + new teams with lifecycle states
    (PROPOSED..ACTIVE..RETIRED), Agent-01 authority ceiling (orchestrator, not absolute), Mission Controller consuming the
    Phase-8 dev-mission queue as QUEUED->TRIAGED only (no autonomous code execution), process-isolated worker stub, audit.
    (items 8-10, 15-16; part1 §11-15, part2 §60-66)
M12 Paper trading lifecycle + learning: open/manage/exit simulation, outcome tracking, success/failure/skip learning records,
    positive & failure pattern memory, calibration + model performance memory vs baselines. PAPER_ONLY. (items 19-22; part2 §24-29, §86-92)
M13 Autonomous engineering core (bounded): provider abstraction + fallback, quota/credential-exhaustion = graceful stop + owner
    request (never extract creds), mission continuity checkpoints, self-diagnosis report, self-repair limited to allowed ops list.
    (addendum §6-17, item 23)
M14 Contradiction intelligence + AI council v1: source/model disagreement records, council review with dissent preserved,
    security overrides opportunity. (items 18; part1 §44-48, part2 §15-16, §23)
M15 University v1 (institution as code): research registry, error-learning -> failure memory, skill registry with
    research->skill->agent adoption gate (no blind adoption), GitHub/skill intelligence read-only research jobs. (part1 §21-26, §92-100)
M16 Dashboard command center + One-Click AHOS: real-data status, missions, agents, university, Wise Tree from real learning data,
    honest stale/unknown display. Telegram stays secondary. (items 25-28; part1 §35-38, add. §19-21)
M17 News intelligence (read-only) + daily intelligence report (Telegram/dashboard), provenance+freshness. (part1 §32-33, part2 §51)
M18 Gold intelligence research + accounting agent on paper ledger only. (part1 §27, §29; roadmap phase 6 — research/paper only)
Later (after foundation stable): low-latency research path, dynamic environment/audio/3D polish, multi-market.

## Human-gated: SKIP and list (never done by agents)
- Any live trading (crypto/gold/forex), leverage, exchange keys, Execution Permission Ladder promotion (part1 §28, §72, §91; part2 §81-82)
- Financial transfer architecture beyond design; credential/identity agent touching real credentials (part1 §30-31)
- Constitution/governance/authority changes, Lane A changes, Canonical Decision Authority changes
- Secret creation/rotation (Gemini key stays in Windows Credential Manager AHOS/ai/gemini)
- GitHub push/merge (local commits only for now)
- Claiming AGI/ACI delivered (forbidden at any time)

## Owner update 2026-10-02 18:47 Tehran (binding on ordering)
Claude has a large budget (Atria): missions are BIG and broad. FINAL GOAL: AHOS fully usable and launched from ONE desktop icon
(Desktop of user Sniper): double-click -> ~~Docker/DB up~~ [SUPERSEDED 2026-10-03: no Docker; native portable PostgreSQL started by the launcher via pg_ctl, see 'Decisions 2026-10-03' below], gateway/dashboard, Telegram bot, engine in PAPER mode, health checks,
opens dashboard; robust startup/health/error messages in short Persian; idempotent (already-running services detected), clean stop option.
Revised order: M9 truth baseline -> M10 ONE-CLICK LAUNCHER (+stop/status, health, Persian errors, desktop .lnk) ->
M11 Agent Organization designed creatively per docs with Claude (19 agents + teams: GitHub Intelligence, Skill Intelligence,
AGI/ACI Architecture, Frontier, Guardian, University, News, Gold-research, Accounting-paper) as real registered, lifecycle-managed,
tested components -> M12 paper trading lifecycle + learning -> M13 autonomous engineering core -> M14 contradiction+council ->
M15 University + GitHub R&D (study real open-source projects, record adopt/reject decisions with evidence) -> M16 dashboard command center
-> M17 news + daily report -> M18 gold research/accounting (paper) -> continuous debug/update/regression missions.

## Owner update 2026-10-02 18:49 Tehran: REMOVE n8n/Docker safely (binding)
New M10 (before launcher): staged migration off Docker/n8n. (1) inventory every dependency (Docker Postgres, compose, n8n workflows,
scripts, tests, docs); (2) back up DB first (pg_dump to local uncommitted backup, never commit); (3) replace with native Windows
equivalents (native/embedded Postgres or SQLite where justified; Python/Node schedulers instead of n8n workflows); (4) migrate data,
verify feature parity by tests; (5) switch only after tests pass; keep a documented rollback path; (6) archive (not delete) old
Docker/n8n files. Launcher (now M11) must NOT need Docker. Order: M9 truth -> M10 de-Docker/de-n8n -> M11 one-click launcher -> M12 agents -> ...

## M9 outcome (2026-10-03, Claude/Atria) — evidence-based ordering notes

M9 is complete. The ordering above is **not** revised — the owner updates above
are binding on ordering. This section records what the truth baseline changed
about the plan's assumptions, plus two inconsistencies the plan should absorb.

**M9 deliverables (all local commits, no push):**
- A) Test baseline: `reports/m9/BASELINE.md` — pytest/tsc/eslint/self-test
  counts with skip reasons (`629e757`).
- B) Import-time side-effect audit (Mandate §12 item 2): 266 modules audited,
  0 confirmed side effects (`3b0da90`).
- C) Remaining Capability Graph, 33 capability areas + 5 cross-cutting
  findings: `reports/grok/REMAINING_REALITY_REGISTER.md` (`f056256`, `a9a2820`).
- D) 12 stale truth/capability maps bannered or corrected (`d2aa09b`);
  Failure Memory FM-001..FM-007 (`1b88fcb`, `0b878be`).

**Evidence that affects later missions (from the register, not from prose):**

1. **The paper-trading closed loop is the single highest-leverage node in the
   whole graph.** It is mission M12 in the current order, and it blocks five
   capabilities: calibration (§6), outcome tracking (§8), the live decision
   authority (§12), trade-derived learning (§21), and accounting (§30). All 19
   `paper_trading.sqlite` tables hold 0 rows and `paper_exits = 0` across all
   15 cycle reports. **It requires no governance gate, no Lane A write, and no
   new capability** — `paper_trading/cycle.py:run_full_cycle` already exists and
   only needs wiring into the daemon. Every mission after it that touches
   learning, accounting, or calibration is building on an empty table until it
   is done. *Recommendation, not a reorder:* consider splitting a small
   "wire-and-run paper loop" mission out of M12 and running it in parallel with
   M10/M11, since it shares no code surface with either.
2. **The launcher (M11) has a hidden prerequisite.** `ControlPlane` documents
   itself as the ONE operator surface (START/STOP/STATUS/SAFE_HALT/RESUME,
   idempotent, ledger-resumable, stale-lock recovery) but is instantiated only
   in tests; the daemon runs `observation_loop.py` directly. A one-click
   launcher cannot offer clean start/stop/health semantics until the daemon is
   routed through the control plane (register CC-1). Fold CC-1 into M11.
3. **De-Docker (M10) is lower-risk than it looks.** Postgres was never live on
   this host — "live Postgres boot pending blocker ②" has stood since 2026-08
   and `reports/PRE_SOAK_STATUS.txt` says `STATE B: do not db:migrate / db:push`.
   The canonical live path is already SQLite. The migration is largely
   *recognizing* the existing topology, and it closes blocker ② by elimination.
4. **Agent Organization (M12 per the 18:49 order) is build-able but not
   activatable.** All 19 agents sit at maturity `REGISTERED` (0) below the
   policy floor of 2, and advancing maturity is a governance-authority change —
   human-gated. The mission can deliver the registry, lifecycle states, the
   mission controller, and the isolated worker stub, and it can *say* none of
   them may execute. Splitting "build" from "activate" keeps the mission honest
   and makes the human gate visible instead of implicit.
5. **University (M15), Wise Tree (M16), Gold (M18) are correctly late.** All
   three are docs-only with empty or absent runtime stores
   (`ahos_knowledge.sqlite` = 0 claims, `ahos_cognitive_memory.sqlite` = 0
   bytes, no charting dependency, no gold ingestion path).
6. **News (M17) is gated on a paid credential** — a live news API requires
   explicit owner approval, which is why the implemented surface has never
   produced an artifact.

**Inconsistencies in this plan that a future mission should reconcile:**

- **Numbering drift between the 18:47 update and the original list.** Line 57
  (18:47) makes M11 = launcher, M12 = agents, M13 = paper trading; the original
  list at lines 23-28 has M11 = agents, M12 = paper trading. The 18:49 order at
  line 66 ("M11 one-click launcher -> M12 agents") follows the 18:47
  renumbering, but the original list was never renumbered. **Use the 18:49
  order; treat lines 16-40 as the mission *definitions* and lines 50-66 as the
  authoritative order.** Two different missions are both called "M12" above.
- **The 18:47 update's M12 (agents) and the original list's M12 (paper trading
  + learning) are the two halves of the register's critical path** — agents are
  the buildable-but-gated half, paper trading is the ungated-but-unstarted half.
  They are not in sequence by accident; they are the two missions whose
  ordering most affects total time-to-usability, and the register's evidence
  says the paper loop is the longer pole.

**Unchanged:** the human-gated list above stands exactly as written. M9 touched
none of it — no live trading, no constitution or governance change, no Lane A
edit, no secret rotation, no push.

## Decisions 2026-10-03 (owner, binding) + Owner Directive Traceability (Grok)

### HARD RULE — search first, extend, never duplicate (applies to every mission)
Before building anything, Claude must search the repo (`rg -i <concept>` across architecture/, agent_org/, ahos_org/,
paper_trading/, discovery/, telegram_ai/, research_worker/, strategy_lab/, engine/, app/, root *.ts, scripts/, tests/, docs/,
reports/) and the matrix's Evidence column, then **extend the existing module**. No parallel/duplicate modules, no "v2" copies,
no second registry/council/engine/launcher/gate for a concept that already has a home. If a new file is unavoidable, the mission
report must list the paths searched and say why the existing module could not be extended. If a mission finds an existing
duplicate, it records the duplicate and does not add a third copy. Consolidation happens only in the missions listed below.

### M10 decision — safe Docker/n8n removal on native portable PostgreSQL (supersedes the "Docker/DB up" launcher wording above)
- Native **portable PostgreSQL on Windows** (zip binaries, managed by `pg_ctl`). Data dir lives **outside git**
  (e.g. `C:\Users\Sniper\ahos_pg\data`). Bind to **127.0.0.1 only**.
- Migrate with `pg_dump` from the Docker DB, then restore into native PG. Prove it with **parity tests** (row counts, schema,
  key queries) before switching. SQLite stays canonical where it already is (M9 finding).
- **Docker volumes are left untouched** for rollback. Compose and n8n files are archived, not deleted. n8n workflows move to
  existing Python/Node schedulers (`architecture/scheduling/engine.py`, `observation_loop.py`); don't write a new scheduler.
  The n8n governance validator (`8e48cf3`) is reused for the inventory.
- Reuse: `docker-compose.yml`, `n8n/workflows/`, `database/postgresql_schema.sql`, `reports/grok/DOCKER_N8N_DEPENDENCY_MAP.md`.
  `reports/pgdump_*.sql` must never be committed.

### M11 decision — one-click launcher
One desktop .lnk that starts native PG (pg_ctl), the runtime routed through `ControlPlane` (CC-1), gateway/dashboard, the
Telegram bot and the engine in PAPER mode. It runs health checks, gives short Persian errors, is idempotent, and has
stop/status. **No Docker.** Consolidate the existing launchers (`start_ahos.bat`, `start_ahos.ps1`, `AHOS_WINDOWS_OPS.bat`,
`AHOS_PRE_SOAK_NOW.bat`, `AHOS_MAIN_FIRST.bat`, `install_windows.ps1`) into one entry point instead of adding a sixth.

### Traceability matrix
`reports/grok/OWNER_DIRECTIVE_TRACEABILITY.md` splits both owner directive docs into 594 atomic requirements:
73 IMPLEMENTED+TESTED, 417 EXISTS-PARTIAL (reuse/extend), 13 PLANNED, 68 MISSING (now assigned below), 18 HUMAN-GATE, 5 UNKNOWN.
**Each mission must tick off its rows.** At mission close, update the Status/Evidence cells of the rows whose Mission column names
it, and cite the commit and test. A row with no evidence stays open.

### MISSING items now assigned to missions (from the matrix)
- **M12 agents:** a real agent lifecycle (REGISTERED→IDLE→…→MISSION_EXECUTION→WAITING_FOR_VERIFICATION), built by extending the
  `ahos_org/registry.py` REGISTERED→IMPLEMENTED path (`c7ed457`). An agent message protocol (sender/receiver/mission/evidence/
  claim/confidence/capability), built by extending `contracts/agent_contract_v1.json` + `agent_org/research_host/contracts.py`.
  Also decide the `agent_org/` vs `ahos_org/` split; don't add a third plane.
- **M13 paper+learning (+ gold-paper track, per OWN-18 "gold first"):** missing security checks (whitelist, fees, max-tx,
  max-wallet, trading controls, liquidity removal, insider concentration, developer history, previous tokens, contract history)
  go into `architecture/security/contract_analysis.py` / `holder_analysis.py`. Pick ONE paper engine
  (`paper_trading/engine*.py` v1/v2/v3) and wire `cycle.py:run_full_cycle`. Gold paper trading on real-market data with fake money
  reuses `paper_trading/` + `architecture/providers/` (new gold price adapter only). Live gold stays HUMAN-GATE.
- **M14 autonomous engineering core:** a Mission Controller built on `architecture/mission/ledger.py` (`d1571c4`) +
  `dev_missions.ts` (`d10383e`), not a new package. An Architecture Agent registered via `ahos_org/registry.py`.
- **M16 University/GitHub:** the University (professors/students, help-desk, failure-learning department, dashboard view,
  University→engineering pipeline, proposals to add agents or duties). Build it on `architecture/cognitive/self_research.py`,
  `strategy_lab/`, `research_worker/`, `architecture/knowledge/oss_pipeline.py`. Design input:
  `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` (`3eea757`).
- **M17 dashboard:** Memory and System Evolution views. First consolidate the 5 parallel website/3D trees
  (`advanced-3d-audiovisual-website*`, `درخت کاملتر…`, `سایت درخت…`, `01/src`) into the live `CommandCenter.tsx` + `app/`.
  Preserve them (P1 §106); don't add another tree.
- **M18 news/gold/accounting:** the Gold Division agents (22 rows) are registered in the existing registry, not a new org. A
  development-activity data source goes into `architecture/providers/`. The financial-transfer/account-opening study is a
  **design doc only**; any transfer is HUMAN-GATE. Accounting extends `paper_trading/ledger.py` + `cost_model.py`.
- **NEW M19 multi-market + low-latency + environment/audio polish (after a stable foundation):** forex/equities/oil/macro
  adapters in `architecture/providers/`, a low-latency order-book/websocket research path (research/paper only), and
  environment/audio engines extending `01/src/components/atmosphere.tsx` and
  `advanced-3d-audiovisual-website/src/utils/audio.ts`.

### Contradictions recorded as HUMAN-GATE (not resolved by agents)
- OWN-6 "no permission for self-development": autonomy only for safe reversible ops (P1A §15). Gated ops (P1A §16) and the list
  above still need the owner.
- OWN-7 "live trade for all parts": PAPER_ONLY stands. Per OWN-18, gold paper comes first, then other lines after real paper
  profit. Any live step is an explicit owner decision.

### Existing duplicates (do not extend the duplication; consolidate only in the named mission)
4+1 website/3D trees (M17); `slills/` vs `.cursor/skills/` (M16); `agent_org/` vs `ahos_org/` (M12); `tests/` vs `tests2b/` (M14);
paper engines v1/v2/v3 + 3 schemas (M13); council in `council_live.py` / `debate_council.py` / `council.ts` (M15); whales in
`architecture/intel/whales.py` vs `architecture/intelligence/whales/` (M18); identity in `discovery/identity.py` vs
`architecture/identity/` (M13); security gate in `discovery/security_gate.py` vs `architecture/security/gate.py` (M13);
positions in `telegram_ai/positions.py` vs `architecture/positions/` (M13); 6 launchers (M11); 3 DB schemas (M10); 5 provider
registries (M13/M14); overlapping registers (`docs/supervision/OWNER_VISION_REGISTRY.md`, `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`,
`docs/COMPONENT_REUSE_MAP.md`, `REMAINING_REALITY_REGISTER.md`); the traceability matrix cross-references them.
