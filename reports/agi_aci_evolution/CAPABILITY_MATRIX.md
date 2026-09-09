# AGI/ACI Capability Matrix

Source of progress measurement. Do not mark IMPLEMENTED_AND_VERIFIED without tests + artifacts. Promotion status is **not main**.

| Capability | Current Status | Evidence | Architecture Target | Gap | Priority | Implementation Status | Test Status | Promotion Status |
|------------|----------------|----------|---------------------|-----|----------|----------------------|-------------|------------------|
| Cognitive Core interfaces | PARTIAL | `architecture/cognitive/` | Domain-general loop | Loop not executed | P1 | contracts | `tests/test_cognitive_core.py` | isolated PR |
| Memory (Lane-B substrate) | PARTIAL | `architecture/cognitive/memory/`; `tests/test_cognitive_memory.py` | typed stores + provenance + production ingest | ACI-GAP-001 | P2 | SQLite substrate | 16 targeted tests | this PR |
| Versioned claims | PARTIAL | `architecture/knowledge/store.py` | semantic memory | claims ≠ full memory | P2 | existing | existing knowledge tests | already on main |
| Hypothesis lifecycle | PARTIAL | `hypothesis.py` HYP- ids | persistent lifecycle | not linked to soak DB | P3 | JSONL store | test_hypothesis_lifecycle | isolated PR |
| Experiment provenance | PARTIAL | `experiment_bridge.py` → ExperimentLedger | first-class experiments | no general lab runner | P3 | bridge | test_record_cognitive_experiment | isolated PR |
| DuckDB research hypotheses | PARTIAL | `knowledge/duck_store.py` | financial research metrics | different ID/status model | P3 | existing | existing | already on main |
| Self-research reports | PARTIAL | `self_research.py` | live self-model | snapshot-only; not soak reader | P4 | builder | test_self_research | isolated PR |
| Metacognition (full) | MISSING | — | answers from real traces | no agent reliability memory | P4 | NOT_IMPLEMENTED | n/a | not proposed |
| World model (KG/causal) | NOT_IMPLEMENTED | `world_model.py` | KG+temporal+causal+CF | ACI-GAP-002 | P5 | inventory only | test_world_model | isolated PR |
| Financial hindsight CF | PARTIAL | `evolution/hindsight.py` | oos review | not general CF | P5 | existing | existing hindsight tests if any | already on main |
| Novelty classification | PARTIAL | `novelty.py` | investigate ≠ promote | no production detector | P7 | classifier | test_novelty | isolated PR |
| Creative intelligence | NOT_IMPLEMENTED | `CreativeClass` enum | classified ideas | no generator | P7 | enum only | n/a | not proposed |
| Cognitive society / council | PARTIAL | council.py + panel + registry | memory-bearing agents | ACI-GAP-003 | P6 | passports | test_agent_passports | isolated PR |
| Meta-cognitive arbitration | PARTIAL | council disagreement matrix; no majority vote | reliability-weighted arbitration | no agent calibration history | P6 | existing council | existing council tests | already on main |
| Agent creation | NOT_IMPLEMENTED | — | sandbox→benchmark→human | auto-deploy forbidden | P6 | NOT_IMPLEMENTED | n/a | not proposed |
| Controlled evolution | PARTIAL | `evolution/engine.py` + `evolution_gate.py` | full test gauntlet + human | ACI-GAP-004 autonomy OFF | P8 | B_ONLY gate | test_lane_b_evolution | isolated PR |
| Frontier research | PARTIAL | OSS pipeline / AG-25 PLANNED | discover→benchmark→adopt/reject | no auto-adopt | P9 | existing partial | existing | already on main |
| Tool intelligence | PARTIAL | `architecture/tools/sandbox.py` | auditable selector | no selector | P9 | existing sandbox | existing | already on main |
| Provider independence | PARTIAL | `contracts/ai_provider_contract_v1.json` | fallback/local | paid default false | P9 | existing | existing | already on main |
| Multi-market adapters | PARTIAL | token/crypto intel | add markets w/o core rewrite | gold/FX/eq MISSING | P10 | NOT this pass | n/a | not proposed |
| Financial decision intelligence | PARTIAL | scoring + decision authority | risk-adjusted outcomes | not portfolio/hedge | P11 | existing | existing | already on main |
| Trading intelligence / leverage | PARTIAL | paper_trading frozen | leverage as variable not default | live OFF | P11–P12 | not activated | n/a | forbidden now |
| Risk governor | PARTIAL | `architecture/risk/` + security overlay | independent reject | not full limits set | P12 | existing | existing | already on main |
| Permission / kill switch | PARTIAL | PAPER_ONLY; n8n/telegram kill sketches | independent kill | not Cognitive-Core-independent hardware | P12 | not changed | n/a | not proposed |
| Evaluation / benchmarks | PARTIAL | `evaluation.py` + BENCHMARK_PLAN.md | vs 6 baselines | no executed AGI suite | P1 | refuse fabricated scores | test_refuse_fabricated | isolated PR |
| Goal discovery / planning | NOT_IMPLEMENTED | — | bounded goal FSM | unrestricted authority forbidden | P1 | NOT_IMPLEMENTED | n/a | not proposed |
| Progressive autonomy L0–L7 | PARTIAL | `AutonomyLevel` + ceiling L1 | explicit levels | L3+ not authorized | P12 | enum | test_autonomy_ceiling | isolated PR |
| M-GAP-003 ≥7-day soak | OPEN | `AHOS_GAP_REGISTER.md` | reliability evidence | 72h ≠ 7d | P0 | not closed | soak in progress | human later |
| Data integrity labels | PARTIAL | score ledger source stamps | REAL/SYNTHETIC/TEST | cognitive reports typed | P0 | data_label on self-research | tests | isolated PR |
