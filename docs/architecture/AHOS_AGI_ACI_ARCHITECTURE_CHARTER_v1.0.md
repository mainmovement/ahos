# AHOS AGI/ACI Architecture Charter v1.0

**Status:** GOVERNED ARCHITECTURE (Lane B). **AGI/ACI is NOT IMPLEMENTED.**  
**Authority class:** Strategic architecture for evolution research. Does **not** override operational soak, Lane-A freeze, PAPER_ONLY, or `docs/NEXT_DEVELOPMENT_BACKLOG.md` deferral of *autonomous* evolution.  
**Conflict record:** `docs/architecture/ADR_ACI_001_CHARTER_VS_DEFERRED_EVOLUTION.md`  
**Evidence pack:** `reports/agi_aci_evolution/`  
**Code contracts:** `architecture/cognitive/`  
**Baseline SHA (main):** `f273feb5875c24b9fbccdc552445d82175a6597c`

This charter maps the approved AGI/ACI direction onto the *existing* repository. A file named Cognitive / AGI / Evolution is not a capability. Status vocabulary:

`IMPLEMENTED_AND_VERIFIED` · `IMPLEMENTED_BUT_UNVERIFIED` · `PARTIAL` · `DOCUMENTATION_ONLY` · `PLACEHOLDER` · `MISSING` · `CONFLICTING` · `DEPRECATED` · `NOT_IMPLEMENTED`

Do not upgrade a lower class through documentation.

## 1. Placement law

| Question | Placement |
|----------|-----------|
| Can this exist independently of finance? | Cognitive Core (`architecture/cognitive/`, plus existing domain-general Lane B: knowledge, evolution engine, council protocol) |
| Is it market- or instrument-specific? | Domain Adapter (`architecture/intel/`, `architecture/intelligence/`, frozen Lane A discovery/paper_trading) |

Finance is the first proving domain. The Cognitive Core must not import `discovery`, `paper_trading`, `telegram_ai`, or `engine`.

## 2. Current AHOS (verified, compressed)

AHOS is an evidence-first **paper-only opportunity intelligence** system with:

- Frozen Lane A: `discovery/**`, `paper_trading/**` (36-file freeze).
- One Python decision brain: `architecture/decision/authority.py` wrapping `DecisionAdvisor`.
- Observation daemon: `python -m architecture.runtime`.
- Advisory AI council: `architecture/council.py` (no majority vote, `advisory_only`).
- Deterministic cognitive panel lenses: `architecture/knowledge/panel.py`.
- Agent *registry* (not a multi-agent runtime): `config/agent_registry.yaml`.
- Controlled evolution *proposals*: `architecture/evolution/engine.py` (AI may propose, never self-approve).
- Experiment ledger: `architecture/evolution/experiment.py` (`proposals/experiments.jsonl`).
- Versioned claims: `architecture/knowledge/store.py`.
- Calibration / score ledger: `architecture/learning/` (join pairs gated; soak in progress).
- Trading-domain hindsight: `architecture/evolution/hindsight.py` (does not overwrite soak outcomes).

Cursor `.cursor/skills/` are **developer instructions**, not AHOS runtime agents.

## 3. Subsystem map (charter target vs current class)

| Subsystem | Architecture target | Current class | Where it lives / why |
|-----------|---------------------|---------------|----------------------|
| Cognitive Core | Domain-general perception→reasoning→learning loop | **PARTIAL** | New contracts in `architecture/cognitive/`; no full loop |
| Memory System | Working/episodic/semantic/procedural + provenance | **PARTIAL** | Claims store + JSONL ledgers; no unified MemoryStore |
| World Model | KG + temporal + causal + probabilistic + CF | **NOT_IMPLEMENTED** | Observations ≠ world model (`world_model.py` inventory) |
| Reasoning | Orchestrator over named modes | **PARTIAL** | FSMs, scoring, council; no orchestrator (`reasoning.py`) |
| Metacognition | Answer “what do I know / why / what fails” from real data | **PARTIAL** | `self_research.py` builds reports from **caller snapshots only** |
| Creativity | Classified IDEA/HYPOTHESIS/… never as truth | **NOT_IMPLEMENTED** | `CreativeClass` enum only |
| Goal Discovery | Bounded GOAL→DECOMPOSE→…→REVISE | **NOT_IMPLEMENTED** | Governance-bounded; not coded |
| Planning | Domain-general planner | **NOT_IMPLEMENTED** | Pipelines exist; not a planner |
| Hypothesis Engine | Persistent HYP- ids + lifecycle | **PARTIAL** | New `HypothesisStore`; duck_store is financial metrics, not this lifecycle |
| Experiment Engine | First-class reproducible experiments | **PARTIAL** | Reuses `ExperimentLedger`; no general lab runner |
| Counterfactual Reasoning | Observed vs alternative; never overwrite facts | **PARTIAL** | Financial hindsight PARTIAL; general engine NOT_IMPLEMENTED |
| Cognitive Society | Memory-bearing tool-using agents that disagree | **PARTIAL** | Registry + lenses + advisory council |
| Agent Memory | Per-agent episodic/error history | **NOT_IMPLEMENTED** | Passports set `memory_bearing=false` |
| Agent Creation | Gap→spec→sandbox→benchmark→human promote | **NOT_IMPLEMENTED** | Unrestricted auto-deploy forbidden |
| Self-Research | Machine-readable WHAT I KNOW / DON’T / FAIL | **PARTIAL** | Snapshot builder; not a live soak reader |
| Learning Engine | Calibration + lessons without fabricating joins | **PARTIAL** | `architecture/learning/`; soak joins may be 0 |
| Controlled Evolution | Weakness→sandbox→tests→governance→promote/reject | **PARTIAL** | Engine + human gate; Evolution layer doctrine **OFF** for autonomy |
| Frontier Research | DISCOVER→BENCHMARK→ADOPT/REJECT | **PARTIAL** | OSS pipeline / AG-25 PLANNED; no auto-adopt |
| Tool Intelligence | Auditable tool selection | **PARTIAL** | `architecture/tools/` sandbox + providers; no selector |
| Domain Adapters | Markets added without rewriting core | **PARTIAL** | Token/crypto intel; other markets MISSING |
| Financial Intelligence | Opportunity + risk from evidence | **PARTIAL** | Scoring + intel; not portfolio construction |
| Trading Intelligence | Size/route/hedge under risk | **PARTIAL** | Paper trading frozen Lane A; cognitive ceiling L1_ANALYZE |
| Risk Governor | Independent reject of attractive ideas | **PARTIAL** | `architecture/risk/` + security overlay; not a full governor |
| Permission Layer | Human/policy/emergency | **PARTIAL** | PAPER_ONLY; n8n human gate sketches; live OFF |
| Execution Layer | After permission only | **NOT_IMPLEMENTED** (live) | Paper path exists in Lane A; live must stay disabled |
| Governance | Human approve/reject/rollback | **PARTIAL** | Contracts + freeze + gap register |
| Evaluation | Named benchmarks vs baselines | **PARTIAL** | Plan + refusal of fabricated scores |
| Rollback | Per-proposal rollback plan | **PARTIAL** | Required on improvement proposals |
| Kill Switch | Stop execution without Cognitive Core | **PARTIAL** | Telegram/n8n kill sketches; not independent of those edges |
| Provider Independence | Registry→health→fallback→local | **PARTIAL** | `architecture/ai/` + provider contracts; paid default false |
| Progressive Autonomy L0–L7 | Explicit levels | **PARTIAL** | Enum in contracts; **ceiling L1_ANALYZE**; PAPER_ONLY |
| Novelty Discovery | KNOWN…NOVEL; novelty ≠ truth | **PARTIAL** | `novelty.py` classifier; no production detector |

## 4. Cognitive Core loop (target)

```text
perception → context → reasoning → planning → memory retrieval
 → hypothesis → criticism → experiment → learning → metacognition
 → tool selection → capability-gap detection
```

Implemented now: **contracts and fail-closed stores**, not the loop.

Autonomy ceiling for this package: `L1_ANALYZE`. Paper trading remains a frozen Lane-A subsystem; this charter does not activate L4–L7.

## 5. Memory evolution path

| Store | Current | Target |
|-------|---------|--------|
| Working | process state / evidence bundles | typed WM with TTL |
| Episodic | observation rows, cycle reports | provenance-bearing episodes |
| Semantic | `VersionedClaimStore` | queryable beliefs + contradiction |
| Procedural | scripts + frozen Lane A | versioned procedures with rollback |
| Market / Experience / Failure | score ledger, experiment JSONL, hindsight | linked to hypotheses |
| Hypothesis / Strategy / Agent / Causal / Self-model | HypothesisStore JSONL; others MISSING | separate stores, not one dump |

Every memory record should eventually carry: provenance, timestamp, source, confidence, validity, contradiction, revision, decay, domain, context, outcome linkage.

## 6. Safety invariants (binding)

```text
Evidence ≠ Score ≠ Decision ≠ Outcome
UNKNOWN ≠ PASS ≠ SAFE
STALE ≠ LIVE ≠ BUY ≠ ENTER
Prediction ≠ Fact
Simulation ≠ Reality
Novelty ≠ Truth
Creativity ≠ Validated knowledge
AI Opinion ≠ Evidence
Documentation ≠ Operational Proof
SELF-IMPROVEMENT ≠ UNCONTROLLED SELF-MODIFICATION
```

No Cognitive Core, Agent, or Council may bypass Risk Governor or Permission Layer. PAPER_ONLY. No live trading from this charter.

Soak protection: do not stop/start the Windows daemon, reset T0, rewrite observations, retune calibration, or change Lane-A scoring semantics to “make cognition look live”.

## 7. Execution / intelligence separation (target)

```text
INTELLIGENCE → DECISION → RISK GOVERNOR → PERMISSION → EXECUTION
```

Current: intelligence and paper decision exist; live execution is closed. Future connectors default disabled.

## 8. What this charter authorizes now

Lane-B isolated work:

1. Cognitive contracts and tests.
2. Hypothesis/experiment provenance bridged to existing ExperimentLedger.
3. Self-research reports from **explicit snapshots** (never treating Cloud sqlite as soak authority).
4. Capability-gap JSONL (does not rewrite `AHOS_GAP_REGISTER.md`).
5. Evolution proposals via existing `SelfEvolutionEngine` with B_ONLY gate.
6. Honest world-model / reasoning / novelty / evaluation inventories.

It does **not** authorize: Lane A edits, soak interruption, live trading, autonomous promotion, fabricated 99.9% intelligence, or claiming AGI/ACI achieved.
