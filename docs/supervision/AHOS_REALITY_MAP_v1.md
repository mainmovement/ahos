# AHOS REALITY MAP v1 (AID_STATIC draft — ruthless labels)

> **AID_NOT_VERIFY / AID_NOT_PASS** — Chief of Staff static/remote aid only.  
> **≠ Agent-16 VERIFY packet. ≠ Agent-19 CHALLENGE absorb.**  
> Do not cite this file as post-land VERIFY, D1_ON_MAIN CLOSED, or readiness.  
> Stamp applied 2026-09-24 by Agent-01 after Agent-19 CHALLENGE on CoS pack.


**Date:** 2026-09-24 (Asia/Tehran, UTC+3:30)  
**Repo sampled:** `mainmovement/ahos` @ main HEAD `d721d92d08450b69a09d6ff1e626470ad8949edf`  
**Method:** Remote `gh api` / raw reads only. No clone. No runtime soak. No Windows operator evidence in this session.  
**Binding inputs:** `/workspace/AHOS_MASTER_CONTEXT_v2.0.md`, `/workspace/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`, `/workspace/AHOS_MASTER_AUTONOMOUS_COMPLETION_MANDATE.md`, plus repo `AGENTS.md`, `docs/DOC_TRUTH_MAP.md`, `docs/CURRENT_TRUTH_SNAPSHOT.md`, `config/agent_registry.yaml`, architecture inventory.

**Census conflict (binding):** Folk “19-agent org” ≠ registry truth. `config/agent_registry.yaml` lists **25** agents (AG-01…AG-25). Label: `CONFLICTING`. Dual-19 = review law, not agent census.

**Law:** REALITY > DOCUMENTATION. Overclaim = fail. VISION ≠ IMPLEMENTATION. AGI/ACI = North Star, **not delivered**.

Epistemic labels used: `IMPLEMENTED_AND_VERIFIED` · `IMPLEMENTED_BUT_UNVERIFIED` · `PARTIAL` · `DOCUMENTATION_ONLY` · `PLACEHOLDER` · `MISSING` · `CONFLICTING` · `NOT_IMPLEMENTED` · `STATIC_ONLY` (this session).

---

## Summary table

| Claim area | Doc claim | Repo evidence | Epistemic label | Gap | Next safe step |
|------------|-----------|---------------|-----------------|-----|----------------|
| **Identity / knowledge** | Lane-B owns canonical identity (`architecture/identity/` wraps frozen `discovery/identity.py`); dossier/evidence graph compose views without inventing identity | `architecture/identity/{types,resolution,fusion,gates,validate}.py` exist; `architecture/knowledge/{dossier,evidence_graph,store}.py` exist; PR #108 on main hardens exact-type + always-recompose | `PARTIAL` / `IMPLEMENTED_BUT_UNVERIFIED` (units exist; this session static-only; D1 not closed per PR) | Real-typed VERIFIED forgery still OUT_OF_SCOPE; no local pytest here; consumers of identity outside knowledge graph not fully audited remotely | Cloud agent: pytest identity+dossier packs; W1.4 mint-marker PR (see M3) |
| **Evidence graph** | Read-only projection; canonical TOKEN only from VERIFIED dossier+canonical_id; never mints OBSERVED/FACT | `evidence_graph.py` always recomposes; module docs match; tests T5–T11 assert discard/`dossier=` forge fail | `PARTIAL` → harden **STATIC_ONLY**; executable verify pending | `dossier=` dead API param; graph is a view not a store; not wired as soak world model | Deprecate `dossier=`; run `pytest tests/test_evidence_graph.py -q` |
| **“19-agent org”** | Mandate/context speak of agent org / Dual-19; humans often say “19 agents” | `config/agent_registry.yaml`: **25** agents AG-01…AG-25; statuses: 9 EXISTS / 12 PARTIAL / 3 PLANNED / 1 MISSING (AG-01 orchestrator absent by design). Registry header: “25-agent matrix”. Charter: registry ≠ multi-agent runtime | `CONFLICTING` (folk “19” vs registry 25) + `PARTIAL` (registry+libs, not a live society) | Calling it a running 19-agent AGI org is an **overclaim**. AG-01 MISSING; many PARTIAL/PLANNED; `memory_bearing` not a live multi-agent runtime | Cite registry counts only; never upgrade PARTIAL→EXISTS without ops evidence; keep Dual-19 as *review law*, not agent census |
| **PAPER_ONLY** | Master context / AGENTS.md / README: paper-only; real trading DISABLED | README + AGENTS.md + charter explicit; `config/lane_a_freeze.sha256` pins **36** discovery/paper_trading paths; live execution charter class NOT_IMPLEMENTED; PROJECT_STATE: LIVE trading CLOSED | `IMPLEMENTED` (policy + freeze) / `OPERATOR_READY = NOT_VERIFIED` (Windows gates) | Policy is strong in docs/code contracts; this session did **not** prove a live Windows soak is PAPER_ONLY in production | Keep freeze verify; never enable live connectors; no Lane A edits |
| **Risk / kill switch** | Risk governor PARTIAL; kill switch PARTIAL (Telegram/n8n sketches; not independent of those edges) | `architecture/risk/engine.py` = evidence-consuming RiskFinding merger (market-structure + security merge); `architecture/security/gate.py` overlay exists; kill_switch hits: `docs/RUNBOOK_OPERATIONS.md`, `engine/bot_skeleton.py`, n8n telegram/signal workflows — **edge-coupled** | `PARTIAL` | No evidence of an independent, Cognitive-Core-orthogonal hard kill that works without Telegram/n8n | Design brief for independent kill (Lane B control plane) — governance gated; do not wire live execution |
| **Cognitive memory / world model** | Charter: memory PARTIAL (P2 substrate); world model **NOT_IMPLEMENTED**; ACI-GAP-001 PARTIAL | `architecture/cognitive/memory/` (store, consolidation, types, …) — docstring: “not AGI memory”; `world_model.py` returns `CapabilityStatus.NOT_IMPLEMENTED` for KG/temporal/causal/CF; probabilistic PARTIAL note only | Memory: `PARTIAL` · World model: `NOT_IMPLEMENTED` (honest inventory) | Production soak ingestion not wired; observations ≠ world model; do not treat Dex snapshots as KG | Keep inventory honest; no claim of world model; optional isolated memory ingest **read-only** vs soak |
| **AI council** | Advisory only; no majority vote; `advisory_only`; README also says “100 roles · 10 teams” | `architecture/council.py`: ADVISORY ONLY, disagreement first-class, OFFLINE→INSUFFICIENT_EVIDENCE; red_team lint for numeric-without-refs. `config/ai_council_providers.yaml` + `cognitive_registry_100.yaml` exist (config/registry). AG-11 Multi-Mind Council = **PLANNED** in agent_registry | `PARTIAL` (protocol + deterministic council module) · **overclaim risk** on “100 roles live” | Registry config ≠ 100 live disagreeing memory-bearing agents; AG-11 PLANNED; Cursor skills ≠ runtime agents | Prefer council.py contract language; treat 100-role registry as **config/docs**, not operational AGI society |
| **Verification / red-team** | Mandate: adversarial test, independent verify, Dual-19 no silent merge; AG-14 Red Team | `council.py::red_team` deterministic lints; AG-14 status **PARTIAL**, `live: false`, evidence = council stage + tests refs; large `tests/` tree including cognitive/identity/security; PR #108 adds adversarial spoof tests | `PARTIAL` | Red team is **lint/stage**, not continuous adversarial runtime; Independent VERIFY of #108 not evidenced this session; Dual-19 is process law, not an automated gate proven here | Cloud: post-land VERIFY packet on d721d92; keep CHALLENGE before “D1 closed” |

---

## Area notes (ruthless)

### Identity / knowledge
- **True:** Lane B identity package and knowledge composers exist; #108 materially raises the bar against *dynamic type spoof* and *caller TokenDossier trust*.
- **False/unsafe if claimed:** “Identity spoofing solved” / “D1 closed” / “canonical identity unforgeable.”
- **Truth class:** harden landed; threat model incomplete.

### Evidence graph
- **True:** Always-recompose on main; tests assert forge paths fail.
- **False if claimed:** Evidence graph is a knowledge graph / world model / claim store writer.
- Module itself says it does not decide, verify identity, or mint facts.

### Agent organization
- **Census:** 25 registered IDs, not 19. Folk “19” must not overwrite `agent_registry.yaml`.
- **Runtime:** AG-01 Master Orchestrator `MISSING` (“ABSENT BY DESIGN”). Registry is ops truth for *design status*, not proof of a cognitive society.
- Cursor `.cursor/skills/` = developer instructions (AGENTS.md / charter).

### PAPER_ONLY / Lane A
- Freeze file lists 36 hashed Lane-A paths — matches charter “36-file freeze.”
- Lane A discovery/** and paper_trading/** remain frozen scientific surface; do not edit.

### Risk / kill
- Risk engine is scoring/intel consumer, not a full independent Risk Governor with permission-layer veto proven end-to-end in this sample.
- Kill switch appears coupled to Telegram/n8n/engine dry-run paths — charter already labels this PARTIAL.

### Cognitive / AGI
- Charter and `world_model.py` correctly refuse AGI/world-model claims.
- P2/P3/P4 artifacts exist as **isolated Lane-B** work; soak-wired AGI = **NOT_IMPLEMENTED**.
- Any UI or README flourish that sounds like delivered AGI fails honesty gate.

### Council
- Strong: advisory_only laws in `council.py`.
- Weak: marketing “100 roles · 10 teams” without operability=true across agents — treat as aspiration/config.

### Verification
- Good unit/adversarial tests for #108 surfaces (static).
- Missing here: executable green run, Agent-16/19 post-land packets, soak-level independent verify.

---

## Explicit non-claims (this map)

- Does **not** claim OPERATOR_READY, PRODUCTION_READY, soak passed, calibration validated, Telegram E2E, n8n operational.
- Does **not** claim AGI/ACI achieved.
- Does **not** authorize Lane A edits, live trading, or autonomous promotion.
- `docs/CURRENT_TRUTH_SNAPSHOT.md` dated 2026-08-27 is **stale relative to main HEAD** (still useful for honesty vocabulary; do not treat its HEAD SHA as current).

---

## Sampling receipt

| Sample | Result |
|--------|--------|
| Root listing | Large hybrid Python+TS monorepo; discovery/, paper_trading/, architecture/, tests/, n8n/, app/ |
| `AGENTS.md` | PAPER_ONLY; Lane A freeze; Python Lane B authority; TS non-authoritative |
| `docs/DOC_TRUTH_MAP.md` | Points to charter, cognitive memory/loop, gap register; bans READY without artifacts |
| `architecture/*` | identity, knowledge, cognitive, risk, security, decision, evolution, council.py, … |
| `config/agent_registry.yaml` | 25 agents; status tally above |
| `config/lane_a_freeze.sha256` | 36 discovery/paper_trading hashed entries |
| PR #108 files | See `AID_M1_POSTMERGE_STATIC_PR108.md` (AID static only — ≠ VERIFY packet) |

**Map status:** DRAFT v1 — STATIC_ONLY remote sample. Promote rows only when executable or operator evidence appears.
