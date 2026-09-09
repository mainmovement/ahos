# AGI/ACI Evolution Gap Register

Operational gaps remain in `AHOS_GAP_REGISTER.md`. This file is the AGI/ACI evolution register. **Never close a gap without evidence.**

| GAP ID | Description | Impact | Dependency | Priority | Evidence | Proposed solution | Implementation status | Validation status |
|--------|-------------|--------|------------|----------|----------|-------------------|----------------------|-------------------|
| ACI-GAP-001 | Lane-B memory substrate exists; soak/runtime ingestion not wired; not unified with VersionedClaimStore | Cannot yet use memory as a live self-model over soak evidence | P2 | P2 | `architecture/cognitive/memory/`; `tests/test_cognitive_memory.py` | Keep isolated SQLite; optional read-only ID links later | PARTIAL | SUBSTRATE_TESTED |
| ACI-GAP-002 | No general causal world model; financial hindsight ≠ causal engine | Cannot represent multi-domain alternatives without mutating facts | P5 | P5 | `world_model.py`; `hindsight.py` PARTIAL | Isolated CF records; never mutate observation tables | OPEN | UNVALIDATED |
| ACI-GAP-003 | Council/registry/lenses are not memory-bearing independent agents | No agent reliability, error history, or tool use | P6 | P6 | `agent_registry.yaml`; `council.py`; passports `memory_bearing=false` | Passports now; later sandboxed agents + human promotion | PARTIAL | PASSPORTS_ONLY |
| ACI-GAP-004 | Autonomous evolution doctrine-OFF; human gate required | Self-improvement ≠ self-modification of production/Lane A | P8 | P8 | PROJECT_STATE Evolution A (OFF); `evolution/engine.py` | Keep proposal ledger; B_ONLY gate; never auto-promote | PARTIAL | HUMAN_GATE_REQUIRED |
| ACI-GAP-005 | M-GAP-003 ≥7-day soak not closed by 72h soak | Reliability questions remain after T+72h | Operational soak | P0 | `AHOS_GAP_REGISTER.md` M-GAP-003; owner T0 2026-09-10 | Post-soak proposal only; do not auto-calibrate | OPEN | SOAK_IN_PROGRESS |
| ACI-GAP-006 | No domain-general reasoning orchestrator | Modes exist in isolation (FSM, scoring, council) | P1/P5 | P5 | `reasoning.py` orchestrator=NOT_IMPLEMENTED | Provenance-preserving orchestrator later | OPEN | UNVALIDATED |
| ACI-GAP-007 | Creative intelligence not implemented | No classified novel hypotheses/strategies from a measured generator | P7 | P7 | `CreativeClass` enum only | Generator later; never present IDEA as truth | OPEN | UNVALIDATED |
| ACI-GAP-008 | Goal discovery / planner not implemented | No bounded GOAL→REVISE loop | P1 | P1 | no goal module | Governed goal store later; no host takeover | OPEN | UNVALIDATED |
| ACI-GAP-009 | Agent creation pipeline not implemented | Cannot specify/sandbox/benchmark new agents | P6 | P6 | none | Spec→sandbox→benchmark→human; no auto-deploy | OPEN | UNVALIDATED |
| ACI-GAP-010 | No executed AGI/ACI benchmark suite | Cannot claim intelligence improvement | P1 | P1 | BENCHMARK_PLAN.md only | Run plan against labeled TEST data after soak | OPEN | PLAN_ONLY |
| ACI-GAP-011 | Multi-market adapters beyond tokens/crypto | Core would be rewritten if finance stays hardcoded | P10 | P10 | intel is token-centric | Domain adapters; keep core domain-general | OPEN | UNVALIDATED |
| ACI-GAP-012 | Live execution / L6–L7 | Out of scope; PAPER_ONLY | P12 | P12 | PAPER_ONLY doctrine | Remain disabled; connectors default off | OPEN (intentionally) | FORBIDDEN_NOW |

Machine-readable seed of ACI-GAP-001…005: `architecture/cognitive/capability.py` `BASELINE_GAPS`. Closing requires non-empty `closed_evidence` (`CapabilityRegister.close`).
