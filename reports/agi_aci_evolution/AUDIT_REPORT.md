# AGI/ACI Evolution — Audit Report

**Record:** EVOLUTION_RECORD_0001  
**Date (UTC):** 2026-09-09  
**Auditor:** Cursor Cloud Agent (Lane B)  
**Base SHA:** `f273feb5875c24b9fbccdc552445d82175a6597c`  
**Branch:** `cursor/agi-aci-evolution-v1-9500`  
**Method:** Source, tests, contracts, docs, skills. Documentation was not trusted without code.  
**Soak:** Not queried. Cloud `data/*.sqlite` is not Windows soak authority.

Owner-supplied T0 (copied, not recomputed):

```text
run_id = run_1788987515_7ad11528
T0 = 2026-09-10 00:27:41 +03:30
OBSERVING = 800
RESOLVED = 1482
outcome_labels = 392
discovery_observations = 4471
production_observations = 6966
local_predictions = 1156
eligible_join_pairs_estimate = 0
```

## Skills inspected (used where relevant)

| Available skill | Purpose | Relevant AHOS area | How used | Evidence of use |
|-----------------|---------|--------------------|----------|-----------------|
| `ahos-governance-context` | One Brain, Lane A freeze, PAPER_ONLY | All of this pass | Binding laws; no Lane A; no second brain | This report + cognitive package import bans |
| `ahos-change-verification` | freeze / validate_imports / pytest | Verification | Commands recorded in TEST_EVIDENCE.md | `reports/agi_aci_evolution/TEST_EVIDENCE.md` |
| `ahos-ai-council` | Advisory council, no vote | Cognitive society | Reused `architecture/council.py` + passports | `architecture/cognitive/agents.py` |
| `ahos-research-intelligence` | Evidence not headlines | Self-research / novelty | Snapshot-typed reports; no fabricated numbers | `self_research.py` |
| `ahos-security-analysis` | Defensive security, no live | Sandbox / PAPER_ONLY | No security-control weakening | `sandbox.py` |
| `ahos-domain-backend` | Python brain vs TS edges | Placement law | Cognitive Core in Python Lane B only | charter §1 |
| `ahos-opportunity-hunter` | Opportunity vs risk | Financial adapter (not core) | Not extended this pass | deferred P11 |
| `ahos-token-identity` | Identity overlay | Domain adapter | Not modified (could affect scoring) | deferred |
| `ahos-market-intelligence` | Intel analyzers | Domain adapter | Not modified | deferred |
| `ahos-product-intelligence` | Product/web | Out of scope | Not used | — |
| `ahos-web-experience` | UI | Out of scope | Not used | — |

No new fake skill integration was added. Gap: there is no Cursor skill for “hypothesis/experiment lifecycle” or “world model”; those are new Lane-B modules, not skills.

## Systems inspected (minimum set)

| Area | Paths | Classification vs AGI/ACI claim |
|------|-------|----------------------------------|
| architecture/ | 129 Python modules incl. decision, runtime, learning, intel, evolution, knowledge, ai, risk, security, tools | Real Lane-B brain; **not** AGI |
| intelligence/ | `architecture/intelligence/**` | EvidenceBundle consumers; domain adapters |
| evolution/ | `architecture/evolution/{engine,experiment,hindsight,validate,selection,findings}.py` | Proposal engine PARTIAL; autonomy OFF |
| council/ | `architecture/council.py`, `architecture/ai/council_live.py`, `architecture/ai/debate_council.py`, `architecture/knowledge/panel.py` | Advisory + deterministic lenses; not independent agents |
| AI / agents | `config/agent_registry.yaml`, `contracts/agent_contract_v1.json`, `.cursor/skills/` | Registry + developer skills ≠ multi-agent cognition |
| memory | `architecture/knowledge/store.py`, `duck_store.py` | Claims + research metrics; no unified memory |
| prediction | `architecture/learning/score_ledger.py`, `prediction_lifecycle.py` | Ledger; calibration INSUFFICIENT until joins |
| scoring | `architecture/scoring/**` | Score ≠ decision |
| market intel | `architecture/intel/**` | Token-centric adapters |
| discovery / observation | frozen `discovery/**`, `architecture/runtime/observation_loop.py` | Lane A + daemon; soak producer |
| paper trading | frozen `paper_trading/**` | PAPER_ONLY |
| Telegram | `telegram_ai/**` | Edge; not a second brain |
| web/API | `app/**` | Display; canonical Python is authority |
| n8n | `n8n/workflows/**` | Includes kill-switch/human-gate sketches; not Cognitive Core |
| DB models | sqlite stores under `data/` (gitignored); schema docs | Not migrated this pass |
| tests | `tests/test_self_evolution_engine.py`, `test_cognitive_panel.py`, `test_architecture_p1.py`, … | Existing proofs reused |
| scripts | `scripts/freeze_lane_a.py`, `validate_imports.py` | Gates |
| reports / docs / canonical / governance | `docs/DOC_TRUTH_MAP.md`, `AHOS_GAP_REGISTER.md`, `docs/canonical/PROJECT_STATE.md`, `docs/NEXT_DEVELOPMENT_BACKLOG.md`, `docs/PRE_SOAK_PROTOCOL.md`, `docs/WINDOWS_OPERATOR_HANDOFF.md`, `docs/CALIBRATION_LIFECYCLE.md`, `docs/architecture/SELF_EVOLUTION_LOOP.md`, `AHOS_FINAL_STATUS.md` (superseded) | Dual authority recorded in ADR-ACI-001 |
| config | `config/agent_registry.yaml`, `config/cognitive_principles.yaml` | Principles ≠ runtime cognition |
| CI | GitHub App workflows permission still a gap (M-GAP-004); template exists | Unchanged |
| security | `architecture/security/**`, PAPER_ONLY | Unchanged |

## Search terms (do not modify merely because they match)

AGI, ACI, cognitive, cognition, memory, world model, reasoning, metacognition, hypothesis, experiment, self-improvement, evolution, agent, council, research, backtest, counterfactual, causal, learning, strategy, simulation, tool selection, goal, planner, autonomy.

Findings of note:

- `docs/architecture/cognitive_*.md` are W9–W11 **principle/agent mapping** artifacts, not a Cognitive Core runtime.
- `architecture/evolution/hindsight.py` is honest financial out-of-sample review, not a general world model.
- `paper_trading/lessons.py` still says `NO_COUNTERFACTUAL_PROTOCOL_YET` for some fields.
- No `WorldModel` / `MemoryStore` / `Metacognition` class existed before this pass (except new inventories).

## Document conflicts

| Document | Claim | Resolution |
|----------|-------|------------|
| NEXT_DEVELOPMENT_BACKLOG | autonomous evolution deferred | Still operationally true |
| PROJECT_STATE | Evolution A (OFF) | Still true for autonomy |
| New Charter | AGI/ACI strategic direction | Lane-B contracts only; ADR-ACI-001 |
| AHOS_FINAL_STATUS.md | historical READY language | SUPERSEDED; not used |

## Soak / Lane A

No daemon start/stop. No T0 reset. No observation rewrite. No calibration retune. No Lane A file edits. `scripts/validate_imports.py` only added `architecture/cognitive` to `EVIDENCE_SURFACES`.
