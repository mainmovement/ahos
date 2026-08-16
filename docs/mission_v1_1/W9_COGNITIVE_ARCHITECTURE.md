# AHOS W9 — COGNITIVE ARCHITECTURE (Lane B, isolated from the frozen experiment)
Status: AUTHORITATIVE under W9/EXECUTION-01 · governance immutable · LIVE TRADING CLOSED · 2026-08-13

## 0. Two-lane isolation (binding)
- **LANE A (frozen experiment):** E-01 track A + PT-BANKROLL-v2/PT-X3-v2 track B. Only
  collection/observation/lifecycle/paper decisions/outcomes/materialization. No tuning, no
  retro-edits, no architecture substitution, no AI-authored rules. Evidence immutable.
- **LANE B (this wave):** contracts, registry, cognitive matrix, router/red-team/orchestrator
  DESIGN+isolated code. Lane B must not alter the E-01 execution path; promotion only via
  replay/parity evidence + human approval for governance-touching changes.

## 1. Cognitive pipeline (binding order)
principle → lens → probe → agent capability → evidence → verdict.
Named persons are intellectual provenance only (`source_inspiration`), never authority.
No personality imitation; no claim of participation; DATA > MODEL OPINION;
pattern ≠ proof; AI confidence ≠ evidence; DETERMINISTIC_ONLY is the permanent floor.

## 2. Authority model (binding)
OBSERVE · ANALYZE · ADVISE · CHALLENGE · VETO · DECIDE · PROMOTE
- AI agents: ANALYZE + ADVISE + CHALLENGE only.
- Red Team: CHALLENGE + VETO(claims/promotions) — never data/rule edits.
- Deterministic engine: DECIDE within frozen governance only.
- Human: PROMOTE governance-touching changes.
Forbidden for all AI: frozen-rule changes, authoritative numbers, evidence bypass,
self-promotion, red-team override, silent threshold shifts.

## 3. This execution pass (what exists NOW, evidence in workspace)
- P0 COMPLETE: `docs/architecture/cognitive_principle_matrix.md` (matrix + current-arch audit
  against it), `config/cognitive_principles.yaml` (machine-readable; 35 principles, 6 domains;
  every entry carries evidence_requirement + candidate_probe + authority_level).
- P1 COMPLETE: `contracts/agent_contract_v1.json` (10-field interface contract),
  `config/agent_registry.yaml` (24 agents; status evidence-based — PARTIAL/PLANNED not upgraded
  without executable proof), `architecture/` package (`contracts.py` validator, `registry.py`
  builder → isolated store `data/architecture_registry.sqlite`), tests.
- P2 DOWN PAYMENT: `docs/architecture/pg_parity_audit_w9.md` — schema audit + parity matrix
  (audit only; NO migration this pass; SQLite evidence untouched, additive+reversible rule holds).
- P3/P4: NOT STARTED (per §14 stop rule; readiness report precedes them).

## 4. Probe inventory state
EXISTING (live in Lane A): PROVENANCE (sha raw payloads, linked 585/585), STALE_DATA law
(PT-X3-v2, fired LIVE t9/t10), SURVIVORSHIP retention law, UNKNOWN≠PASS security gate,
conservation invariants, replay/no-look-ahead pins.
DEFINED-NOT-IMPLEMENTED (Lane B queue): router probes, red-team runtime lints
(LIQUIDITY_ILLUSION runtime, OVERFIT, AI_CORRELATION, SOURCE_DISAGREEMENT, etc.) — statuses
honest in the yaml (`probe_status: DEFINED|EXISTING`).

## 5. Validation gates (unchanged, not lowered)
Track A: ≥200 resolved ∧ ≥20 positive ∧ two distinct 72h windows (current: 0 resolved).
Track B: ≥30 closed trades ∧ ≥1 realized cost reconciliation (current: 0 closed).
Baselines owed at maturity: random / naive-liquidity / naive-volume / momentum / ranker.
R-C3: CLOSED (PT-X3-v2) under regression watch. Experiment remains NOT YET VALIDATED.
