# University (دانشگاه) & Owner-Defined Agents — Discovery Report

**Phase:** 8b (Mission 8, 2026-10-02)
**Author:** Claude/Atria
**Scope:** READ-ONLY discovery. No code was changed by this phase.
**Question answered:** What do the owner's documents require for (a) the AHOS University and (b) the 19 owner-defined agents + the 9 new teams; what already exists in code versus in docs only; and what would have to be true before any of it is operational.

Reality ladder used throughout: `PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < OPERATIONAL`.
Nothing in this report is independently verified unless the line says so. This document is discovery, not evidence of working software, and it is not a claim that AGI/ACI is delivered.

---

## 1. What the documents require

### 1.1 The University — a Research & Learning Ecosystem, not a page

Primary source: `docs/owner_directives/owner_directive_part1.txt`

| Requirement | Source | Verbatim intent |
|---|---|---|
| A fully independent, architecturally central section named **AHOS UNIVERSITY** | part1 §21 (line 727) | «University نباید یک صفحه تزئینی باشد» — must be a real Research & Learning Ecosystem |
| Dozens of professor/student agents plus 15 named research roles (Research, Professor, Reviewer, Experiment, Benchmark, Scientific Method, Failure Analysis, Skill Research, AI Research, Trading Research, Security Research, Architecture Research, AGI/ACI Research) | part1 §21 (lines 741–758) | These are *roles within* the University, not a flat list of agents |
| Continuous activity: research, study, experiment, compare, benchmark, simulate, code/GitHub/skill/model/market/security/failure/architecture research | part1 §22 (line 763) | Permanent duty, not a mission-scoped task |
| A research→engineering delivery pipeline | part1 §23 (line 814) | `RESEARCH → HYPOTHESIS → EXPERIMENT → RESULT → VALIDATION → ENGINEERING PROPOSAL → TEST → INTEGRATION → VERIFICATION`, then handed to the Engineering group |
| Open problem-solving intake for every agent (questions, failures, ambiguity, architecture/security/technical questions, research gaps) | part1 §24 (line 836) | University must `Research → Cross-check → Experiment → Review → Resolve` and return the result to the agent **and Organizational Memory** |
| Dedicated **Failure / Mistake Learning** | part1 §25 (line 865) | `Failure → Root Cause → Architectural Cause → Process Cause → Test Gap → Governance Gap → Memory Gap → Prevention → New Test → Learning` |
| Controlled continuous learning and skill acquisition | part1 §26 (line 890) | Self-improvement must run `WEAKNESS → HYPOTHESIS → CANDIDATE → SANDBOX → HISTORICAL TEST → OUT-OF-SAMPLE → ADVERSARIAL TEST → REGRESSION → COMPARISON → INDEPENDENT VERIFICATION → GOVERNANCE → PROMOTE/REJECT`. «SELF-MODIFY → TRUST SELF → PROMOTE» is explicitly forbidden |
| **Permanent institution** — must not stop when a mission ends | part1 §92 (line 2716) | «PERMANENTLY ACTIVE RESEARCH SYSTEM»; its standing question set includes "what new tool/skill/model/architecture/GitHub project/failure has appeared", "what makes AHOS better/faster/more accurate/more secure", "what should be removed or changed" |
| **Global benchmarking** of AHOS against best-in-class OSS, AI agent systems, trading/research/cognitive/memory/dashboard/security systems | part1 §93 (line 2747) | Continuous external comparison, not self-assessment |
| Dashboard shows University as a real entity, with real research results and a University integration surface | part1 §95 (line 2804), §37 Wise Tree (line 1311), §35–36 Dashboard | The UI must surface real research, not decoration |
| Telegram: University research trigger and University results appear in the chat surface | part1 §33→§34 (lines 1200, 1234) | Chat must be able to trigger and display University output |

Cross-reference (same document set, restated): `docs/owner_directives/owner_directive_part2.txt` (MASTER CONTEXT v2.0) repeats the 19-agent specialization at §8 (line 5426) and the Cognitive Society / AGI-ACI definition at part2 §§17–19, and at line 2308 states the canonical Slice-1 19-role taxonomy and the planned/architectural 19-role taxonomies **remain distinct until an explicit governance decision resolves them**. It also carries the standing rule (part2 §0) that vision/design/proposed/implemented/tested states must never be silently conflated.

### 1.2 The 19 owner-defined agents

Source: `docs/owner_directives/owner_directive_part1.txt` §12 (lines 438–461), duplicated in `owner_directive_part2.txt` §8 (line 5426).

1. Chief Orchestrator — 2. Reality Forensics — 3. Evidence Transport — 4. Security — 5. Identity — 6. Canonical Decision Audit — 7. Scoring Science — 8. Paper Trading — 9. Learning / Memory — 10. Calibration — 11. Cognitive AGI/ACI — 12. Windows Runtime — 13. Provider / Data — 14. Integration — 15. Frontend / UX — 16. Independent Verification — 17. Red Team — 18. Change Architecture — 19. Release Governance

Binding instruction in the same section: «این 19 نقش را کورکورانه دوباره نساز» — do **not** blindly rebuild these 19 roles. Inspect the repository first; develop the real agents that already exist; complete what is incomplete; do not merge duplicates without a governance decision.

**Agent-01 ceiling** (part1 §13, line 480): Agent-01 is Orchestrator / Mission Decomposer / Coordinator / Context Manager / Prioritizer / Delegator / Aggregator / Challenger / Learner — but it is explicitly **not the Root of Trust**. It cannot grant authority, change policy or governance, declare independent verification, self-approve, enable live trading, bypass the security boundary or TCB, turn a capability into a permission, or become an absolute commander.

**Agent lifecycle** (part1 §14, line 513): `REGISTERED → IDLE → DORMANT → WAITING_FOR_COMMAND → ACTIVE → MISSION_EXECUTION → WAITING_FOR_VERIFICATION → COMPLETED`. An agent may not activate itself without valid authority.

### 1.3 The new teams

Sources: `docs/owner_directives/owner_directive_part1.txt` §§15–20, 27, 29, 30, 33 and `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md:55–57` (owner update 2026-10-02 18:47 Tehran, binding on ordering).

| Team | part1 section | Mission-plan label (M11) |
|---|---|---|
| GitHub Intelligence | §16 (line 555) | GitHub Intelligence |
| Skill Intelligence | §17 (line 611) | Skill Intelligence |
| AGI / ACI Architecture | §18 (line 638) | AGI/ACI Architecture |
| Global Technology / Frontier Intelligence | §19 (line 670) | Frontier |
| Agent Supervision / Guardian | §20 (line 701) | Guardian |
| News Intelligence | §33 (line 1149) | News |
| Gold Trading Division (research; live gold trading remains forbidden) | §27–28 (lines 930, 1024) | Gold-research |
| Accounting Agent | §29 (line 1066) | Accounting-paper |
| Credential / Identity Agent | §30 (line 1098) | (part of M11 org) |
| **University** | §21–26, §92–95 | University |

Part1 §15 (line 530) is binding on *how* these are built: agent count is not the goal. Every agent must have a defined mission, boundary, capability, authority, tool access, memory scope, evidence requirements, verification requirements, failure handling, and performance metrics.

The mission plan fixes the order: M9 truth baseline → M10 one-click launcher → **M11 agent organization as real, registered, lifecycle-managed, tested components** → M12 paper-trading lifecycle + learning → M13 autonomous engineering core → M14 contradiction + council → **M15 University + GitHub R&D** → M16 dashboard command center → M17 news + daily report → M18 gold research / accounting (paper). The University is M15; the agent organization is M11. M10 (one-click launcher) is ahead of both and is not yet done.

---

## 2. What exists in code versus docs only

### 2.1 The University: docs only. Zero University code.

A repository-wide search for `university`, `research_registry`, `skill_registry`, `failure_memory` across `*.py` and `*.ts` (excluding `node_modules`, `.venv`, `.git`) finds **no University implementation, no research registry, no skill registry, no failure-memory store**. The only matches are (a) the Persian intent strings added in Phase 8a (`chat_intent.ts`, `dev_missions.ts`, `scripts/chat_intent_selftest.ts` — the dev-mission intake that routes «دانشگاه رو بساز» to a queued engineering mission) and (b) an unrelated `failure_memory_id` field on a cognitive-loop contract.

**Ladder state: PLANNED.** Not PARTIAL — there is no partial University, only substrates that a future University could stand on:

| Required capability | Closest existing substrate | Ladder state |
|---|---|---|
| Research → hypothesis → experiment → validation pipeline | `architecture/cognitive/` (`hypothesis.py`, `experiment_bridge.py`, `sandbox.py`, `evaluation.py`, `counterfactual.py`, `novelty.py`, `self_research.py`, `benchmark/`, `loop/`); `architecture/evolution/` (`engine.py`, `experiment.py`, `findings.py`, `validate.py`, `hindsight.py`, `selection.py`) | IMPLEMENTED as **libraries with no University caller** — no registry, no orchestrator, no permanent loop |
| Failure learning (part1 §25) | `paper_trading/lessons.py`; `architecture/evolution/hindsight.py`; `architecture/knowledge/feedback.py` | PARTIAL — lesson extraction exists inside the paper-trading lane; there is no cross-system failure registry feeding a University |
| Skill registry / skill research | `architecture/knowledge/` (`store.py`, `dossier.py`, `trust_registry.py`, `lenses.py`, `assistants.py`, `oss_pipeline.py`); `architecture/learning/` (`calibration.py`, `drift.py`, `score_ledger.py`, `prediction_lifecycle.py`) | PARTIAL substrate — a knowledge store and calibration ledger exist; no skill registry, no skill-research agent |
| GitHub research (part1 §16, M15) | `architecture/knowledge/oss_pipeline.py`; `engine/oss_audit.py`; `docs/OSS_HARVEST_LOG.md` | PARTIAL — an OSS audit pipeline exists and is harvested, but it is not connected to a research institution and records no adopt/reject decisions with evidence |
| Permanent benchmark loop (§93) | `architecture/cognitive/benchmark/` | IMPLEMENTED as a library; no standing benchmark loop runs |
| Hand-off to Engineering (§23) | **`dev_missions.ts` (Phase 8a)** | IMPLEMENTED (this phase) — but only the *intake*: a hash-chained QUEUED queue with **no consumer** |
| Memory the results return to (§24: "Agent and Organizational Memory") | `architecture/knowledge/`, `architecture/cognitive/memory/` | PARTIAL substrate |

### 2.2 The 19 agents: a policy model, not a runtime

`docs/governance/AGENT_TAXONOMY_MAP.md` (machine-readable authority `docs/governance/agent_taxonomy_map.json`, enforced by `tests/test_agent_taxonomy_map.py`) is the honest picture. It records **five** naming namespaces, not one organization:

| Namespace | Source | Count | Honest class |
|---|---|---|---|
| `agent.*` | `architecture/registry.py` (`CANONICAL_AGENT_IDS`) | 19 | **[IMPLEMENTED]** policy model — no runtime, no external I/O |
| `AG-*` | `config/agent_registry.yaml` | 25 | machine-readable ops registry; `orchestrated: 0` for every agent |
| `AGENT-*` | `docs/AGENT_MAPPING.md` (Phase-1 frozen lock) | 10 (+15 expert roles) | frozen two-layer map; documentary |
| `agent.org.*` | `docs/agents/PLANNED_19_AGENT_MAP.md` | 19 | **[PLANNED]** documentary blueprint; not seeded in code |
| `A`–`H` | M0 reality matrix | 8 | evaluation roles, not repository ids |

The map explicitly refuses to collapse these (status `RECONCILED_NOT_MERGED`; silent merge is forbidden by part1 §12) and flags the "agent 01" collision — `agent.chief-orchestrator`, `AG-01` (Master Orchestrator, status MISSING, absent by design), `AGENT-01` (DataFetch, a data ingest role, **not** an orchestrator) and `agent.org.01-chief-architect` mean four unrelated things. Three of the eight M0 evaluation roles have no Slice-1 anchor at all.

The nine new teams have **no code namespace of their own**. `docs/agents/AGENT_ORGANIZATION_README.md`, `docs/agents/AGENT_MISSION_CHARTER_TEMPLATE.md` and `docs/agents/PLANNED_19_AGENT_MAP.md` are documentary blueprints only.

### 2.3 The Mission Controller does not exist

`architecture/mission/` contains the ledger plumbing (hash-chained append-only records — the same pattern Phase 8a reused for the dev-mission queue) but no controller that reads a mission queue and dispatches work. `architecture/control_plane.py` has **no non-test importer** (`tests/test_control_plane_soak.py`, `tests/test_runtime_w11.py`, `scripts/doc_drift.py` only). No mission is dispatched by software today.

### 2.4 The blocking mechanical fact for M11

From `AGENT_TAXONOMY_MAP.md`, verified against live code:

> All 19 Slice-1 canonical agents are seeded at `MaturityLevel.REGISTERED` (0).
> `MINIMUM_MATURITY_FOR_ALLOW = 2` (`IMPLEMENTED`).
> **Therefore no Slice-1 agent can currently be granted execution authority.**

This is not a documentation gap or a missing wiring task. The maturity floor is a deliberate gate and every canonical agent sits below it. As of 2026-09-27 the legal ramp exists — `AgentRegistry.advance_maturity`, fail-closed, evidence-mandatory, audit-logged, and never called by any seed or production path — so the *missing-mechanism* half of the blocker is resolved and the *missing-evidence* half remains. Raising maturity requires documented evidence per agent, not an edit to the floor.

Supporting invariants from the same map (all live-code-verified): only `AG-15` Decision Engine and `AG-16` Paper-Trading hold `DECIDE` authority and neither is a Slice-1 anchor; `AG-09`'s veto is deterministic, never an AI veto; `AG-23` holds PROMOTE+VETO as a documented **human gateway only**; research contexts cannot receive identity/approval/promote/delegate/execution/policy/verification/task capabilities; an AI council can only downgrade or abstain; and `hygiene.py` vetoes `AHOS_ALLOW_REAL_FUNDS` / `AHOS_EXECUTE_LIVE_TRADES` with `trading.live` a global deny.

---

## 3. What operationalizing the agents needs (control-plane status)

In dependency order — each row blocks the rows below it:

| # | Need | Status | Blocks |
|---|---|---|---|
| 1 | **One-click launcher** (M10): Docker/DB up, gateway + dashboard + Telegram bot + engine in PAPER mode, health checks, Persian startup/error messages, idempotent, clean stop, desktop `.lnk` | NOT_STARTED (mission-plan order puts it ahead of M11) | Everything below, because there is no stable runtime to register agents into |
| 2 | **Per-agent evidence packages** — for each of the 19 anchors, documented implementation + test + verification evidence sufficient for `advance_maturity` from REGISTERED to IMPLEMENTED | NOT_STARTED; the mechanism exists, the evidence does not | #3 |
| 3 | **Maturity ramp decisions** — `AgentRegistry.advance_maturity` per anchor, human-gated, audit-logged | MECHANISM IMPLEMENTED, never invoked in production | #4, #5 |
| 4 | **A real control plane with a non-test importer** — `architecture/control_plane.py` is currently imported only by tests and `doc_drift.py` | IMPLEMENTED-as-library, NOT_OPERATIONAL | #5, #6 |
| 5 | **Agent lifecycle runtime** — REGISTERED→IDLE→…→COMPLETED with valid-authority activation (part1 §14) | PLANNED; the states exist as an enum-level policy model, no runtime transitions | #6 |
| 6 | **Mission Controller** that reads a mission queue and dispatches to agents with authority checks | NOT_STARTED (ledger plumbing exists, no controller) | M13 autonomous engineering core |
| 7 | **Dev-mission queue consumer** — the Phase 8a queue has a writer (chat) and no reader | IMPLEMENTED (writer only) | The queue is dead storage until #6 exists |
| 8 | **Taxonomy reconciliation governance decision** — five namespaces, four of which mean different things by "agent 01"; part2 line 2308 keeps them distinct until governance resolves it | HUMAN-GATED — do not merge | Clean agent identity for M11 |
| 9 | **University institution** — research/skill/error-learning registries, permanent benchmark loop, engineering-proposal hand-off | PLANNED (substrates exist, no institution) | M15 |
| 10 | **Live gold trading / credential / financial-transfer authority** | FORBIDDEN — global deny, `hygiene.py` veto. Gold and accounting remain research/paper only | Never (human-gated, outside this system's authority) |

**Net:** the control plane is a library, not a service. No agent holds execution authority, nothing imports the control plane outside tests, and no controller consumes a mission queue. M11 cannot be "wired" — it has to be built bottom-up from evidence.

---

## 4. A phased safe plan, foundations first

Each phase is strictly gated: nothing below starts before the row above reports TESTED with receipts, and no phase claims more than its own ladder state. All work stays PAPER_ONLY; no phase touches live trading, credentials, or Lane A.

### Phase U0 — Truth baseline for the org (before any agent code)
- Freeze a single **canonical agent inventory** sheet: for each of the 19 Slice-1 anchors, its current code anchor, its maturity, its capability set, and *what evidence would be needed* for `advance_maturity`. Source from `architecture/registry.py`, `agent_taxonomy_map.json` and `docs/agents/PLANNED_19_AGENT_MAP.md`; do not merge namespaces, just tabulate them side by side.
- Add a **regression guard** that fails if a new namespace silently collapses an existing one (extends `tests/test_agent_taxonomy_map.py`).
- Deliverable: a reviewed document, no behaviour change. Ladder target: VERIFIED (it is a document about code, and it is checkable).
- Human-gated input needed: which namespace is authoritative for M11. Do not decide this unilaterally.

### Phase U1 — Launcher and runtime substrate (M10, per mission-plan order)
- One-click launcher: Docker/DB, gateway, dashboard, Telegram bot, engine in PAPER mode, health checks, Persian messages, idempotent start, clean stop, desktop shortcut.
- Why first: agents register into a running system. There is nothing to register into until this exists, and the owner's binding order puts M10 before M11.
- Ladder target: TESTED locally, then VERIFIED by an operator run.

### Phase U2 — Evidence packages and the maturity ramp (M11 core)
- For each anchor, one evidence file: implementation pointer, test suite + counts, verification receipt.
- Then human-gated `advance_maturity` calls, one anchor at a time, audit-logged.
- Ladder target per anchor: IMPLEMENTED → TESTED. Only the anchors that clear this get any execution authority, and only the capabilities the taxonomy allows — never DECIDE for a Slice-1 anchor, never a global-deny capability.
- Explicitly not attempted: raising the floor, granting DECIDE, or anything on the INV list.

### Phase U3 — Control plane becomes a service (M11 runtime)
- Give `architecture/control_plane.py` its first non-test importer: a small supervised service that boots the registry, evaluates maturity, and refuses to grant anything below the floor.
- Implement the part1 §14 lifecycle transitions with valid-authority activation; an agent that cannot prove authority stays REGISTERED/IDLE.
- Ladder target: TESTED with soak receipts; fail-closed by default (deny when any check is missing).

### Phase U4 — Mission Controller and the queue consumer (M13)
- The controller reads the Phase 8a dev-mission queue (`data/dev_missions/dev_missions.jsonl`), verifies the hash chain, and turns each QUEUED mission into dispatched work *with authority checks*, recording the outcome back to the mission ledger.
- This is the first consumer of the queue and the first thing that can ever move a mission out of QUEUED. Until it exists, the chat assistant's reply («ثبت شد… کاری هنوز انجام نشده است») remains literally true.
- Ladder target: TESTED. Human-gated: whether the controller may auto-dispatch at all, or only propose dispatch for approval.

### Phase U5 — University institution (M15, per mission-plan order)
Stand up the smallest honest version of part1 §21–26 first, then grow it:
1. **Research registry** over `architecture/knowledge/` — proposals, hypotheses, experiments, results, with provenance on every record (reuses the existing hash-chain ledger pattern).
2. **Skill registry** — skills with evidence, benchmark results, and a promote/reject decision attached, so part1 §26's `GOVERNANCE → PROMOTE / REJECT` is recorded rather than asserted.
3. **Failure / error-learning registry** — implements part1 §25's chain (Failure → Root Cause → Architectural/Process/Test/Governance/Memory Gap → Prevention → New Test → Learning), fed initially from `paper_trading/lessons.py` and `architecture/evolution/hindsight.py`.
4. **Permanent benchmark loop** (part1 §93) over `architecture/cognitive/benchmark/`, benchmarking AHOS against external OSS reference points via the existing `oss_pipeline.py`, recording adopt/reject decisions with evidence (the M15 GitHub R&D requirement).
5. **Engineering hand-off** — the `RESEARCH → … → ENGINEERING PROPOSAL → TEST → INTEGRATION → VERIFICATION` pipeline of part1 §23 terminates by writing to the **Phase 8a dev-mission queue**, which is now the system's single legal intake for engineering work. This closes the loop: University research becomes a queued mission, the M13 controller dispatches it, the result returns to Organizational Memory.
6. Only then: the dashboard surface (part1 §95, the Wise Tree §37) and the Telegram research trigger/results (§33→§34) — and only showing real records, never decoration.
- Ladder target: each sub-item TESTED individually; the institution as a whole reaches OPERATIONAL only after an operator-run soak. **No phase may claim the University is a Research & Learning Ecosystem until the registries hold real records with provenance.**

### Phase U6 — Teams as registered agents (M11 remainder, M17, M18)
- The nine teams are registered as agents under the same maturity ramp, same evidence requirement, same authority constraints. Gold and accounting are research/paper-only by global deny; live gold trading and financial transfer are never built.
- Ladder target: per-team TESTED; OPERATIONAL only with operator evidence.

### Cross-phase rules
- Every phase records receipts without overwriting history; every phase leaves Lane A, the maturity floor, the global-deny list, and the PAPER_ONLY boundary untouched.
- Self-improvement of any kind follows part1 §26's controlled chain end to end; the forbidden shortcut (`SELF-MODIFY → TRUST SELF → PROMOTE`) is a hard rule, enforced by the existing evolution gate.
- Human-gated items this plan does **not** do, only lists: the authoritative-namespace decision (U0), each maturity advance (U2), the auto-dispatch decision (U4), any live-trading or credential authority (never).

---

## 5. Honest summary

- The University is **entirely docs** today. Strong, detailed, internally consistent docs — with usable substrates already in `architecture/cognitive/`, `architecture/evolution/`, `architecture/knowledge/` and `architecture/learning/`, but no institution, no registries, no permanent loop, and no consumer for the research→engineering pipeline.
- The 19 agents are a **policy model**, not a runtime: seeded, reconciled (not merged), and all pinned at `REGISTERED` below the execution floor. Nothing is broken; the gate is deliberate and the evidence to open it does not exist yet.
- The nine teams are **names in two documents** with no code namespace.
- The single most useful thing built this phase for this roadmap is small: the Phase 8a dev-mission queue is the **intake layer** the University's engineering hand-off and the M13 controller both terminate in. It has a writer and no reader, by design.
- Ordering is settled by the owner's 2026-10-02 18:47 Tehran update: M10 launcher → M11 agents → … → M15 University. Building the University before the launcher and the maturity ramp would produce decoration, which part1 §21 expressly forbids.

**Remaining unknowns:** which namespace governance declares authoritative for M11; what evidence per-anchor standard will satisfy `advance_maturity`; whether the M13 controller may auto-dispatch or only propose. All three are human-gated and are listed, not resolved, here.
