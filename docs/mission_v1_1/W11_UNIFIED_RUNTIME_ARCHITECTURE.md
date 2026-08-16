# AHOS W11 — UNIFIED RUNTIME ARCHITECTURE (master document)
2026-08-13 · Mode: architecture/contracts/tests — NO premature infrastructure · Lane A continued
uninterrupted (t11 landed this session). Contract set: agent_contract_v1 (+ops), control_plane_v1,
ai_provider_v1, ai_council_v1, improvement_proposal_v1. Experiment verdict unchanged:
**NOT YET VALIDATED** (0/200 resolved, 0/30 closed, 0 reconciliations; gates un-lowered).

## 1. Architecture answer in one paragraph
One operator surface (START/STOP/STATUS/SAFE_HALT/RESUME) drives a 16-phase, ledgered,
idempotent boot over a cycle-checked dependency graph; infra is declared with MEASURED
availability (targets stay targets — nothing pretends to run); agents enter only with
implemented+orchestrated truth; the AI council is advisory-only behind a probe-gated free-first
router with circuit breakers; Red Team vetoes claims deterministically; when nobody AI answers,
the DETERMINISTIC FLOOR keeps AHOS alive. Today this is a Python engine with an append-only
run-ledger — the exact slot Temporal occupies later without redesign.

## 2. Component contract table (target stack; W10 §3 / W11 §3 evaluated)
| Component | Purpose | Owner | Health check | Failure mode | Fallback | Adoption verdict |
|---|---|---|---|---|---|---|
| PostgreSQL | canonical evidence/state (F1 target) | AG-17 | tcp probe (defined) | SAFE_HALT critical | sqlite stores (current truth) | TARGET, host-blocked |
| Temporal | durable workflows/retries/resume | runtime controller | probe (defined) | DEGRADED | Python control plane (NOW) | RECOMMEND-TARGET, DEFER-INSTALL |
| Redis | cache/queue | AG-24 watch | n/a | none (OPTIONAL) | sqlite | NOT JUSTIFIED — no measured need |
| NATS/Kafka | event bus | AG-22 watch | n/a | none (OPTIONAL) | ledger+cycle files | NOT JUSTIFIED — scale unproven |
| n8n | external automation edge ONLY | operator | probe (defined) | OPTIONAL degraded | CLI entrypoints | KEEP at edge (currently host-blocked) |
| OTel/Prom/Grafana | observability | AG-22 | n/a | DEGRADED | run-ledger + periodic reports | DESIGN target |
| Contracts/Governance | truth surface | AG-23 (human) | CI suite | SAFE_HALT on law conflict | — | LIVE (this repo) |
| Model Router | advisory AI routing | AG-12 | provider probes | DEGRADED→floor | DETERMINISTIC_ONLY | IMPLEMENTED (test-pinned) |
| Red Team | claims veto | AG-14 | lint suite | fail-closed promotions | — | PARTIAL (lints live) |

## 3. Runtime topology
See docs/architecture/runtime_dependency_graph.md (boot classes, edges, anti-SPOF fallbacks).
Key property: the deterministic Lane-A core has NO dependency on any AI/infra target; every
weekly-increasing layer is additive around it.

## 4. Docker target (design artifact only)
deployment/docker-compose.target.yml — declares every service with healthcheck, restart policy,
dependency conditions, resource boundaries, log config, version pins, config boundaries; secrets
exclusively via env. NOT built here (no Docker in sandbox); activation gate = host exists +
owner trigger. Current delivered compose (PG16+n8n) remains the only execution-era artifact.

## 5. Observability model (W10 §19 / W11 §20)
Levels: SYSTEM AGENT WORKFLOW PROVIDER MODEL RUN EVIDENCE FAILURE LATENCY COST HEALTH.
Today: run-ledger answers (running/failed/why/evidence/last_valid_state/resumable) + cycle
reports carry per-run timing + counters. Target: OTel spans per phase, Prometheus metrics per
agent (health, latency, errors, circuit, invocations, evidence counts, provider state, resource),
single AHOS SYSTEM STATUS surface. Status enum: ONLINE / DEGRADED / SAFE_HALT / RECOVERING.

## 6. Self-improvement loop (contracted)
DETECT → DIAGNOSE → council → ImprovementProposal → sandbox → replay → CI → red team → council
review → governance check → HUMAN (mandatory when governance-touching) → version → deploy →
monitor → rollback. improvement_proposal_v1 stage machine enforces: no skips (INVALID),
no self-approval (INVALID), Lane-A targets auto-REJECT. Rollback via versioned cards (proven
pattern: PT-X3-v1→v2).

## 7. Acceptance criteria — answered with evidence (W11 §25)
1. One master Start initializes the complete runtime? **PARTIAL** — engine does the full chain
   honestly TODAY (test-pinned); real containerized boot BLOCKED_NO_HOST (no fabrication: real
   config boot ⇒ SAFE_HALT verdict, recorded).
2. Detect dependency failure? **YES** — critical⇒SAFE_HALT / non-critical⇒DEGRADED (tests).
3. Recover without duplicate execution? **YES** — resume-from-ledger + idempotent keys (tests).
4. Every agent registered & contract-validated? **YES** — 24/24 validate zero errors (test).
5. AI providers enter/leave without rewriting AHOS? **YES** — registry-driven, breaker-managed,
   floor-tested (council offline test).
6. Operate with zero AI providers? **YES** — DETERMINISTIC_ONLY live-verified (PRB-AI-001) +
   floor tests.
7. Multiple AIs critique one artifact without authority? **YES** — advisory_only=true envelopes;
   disagreement protocol; no averaging (tests).
8. Red Team veto unsupported claims? **YES** — REJECT/INVALID with probe_id, test-pinned.
9. Distinguish EXISTS vs PLANNED honestly? **YES** — operability 4-axis machine-readable,
   orchestrated=0 pinned, live⇒implemented enforced.
10. Architecture evolve without touching frozen rules? **YES** — proven this wave (Lane-A
    hashes identical; lane-isolation pins extended to 3 new modules).
11. One system-status surface eventually? **YES (design) / PARTIAL (today: ledger STATUS)** —
    OTel/Prometheus target documented; interim surface implemented.
12. Lane A uncontaminated? **YES** — snapshot diff proof (doc section M of final report).

## 8. Contradictions resolved this wave (open record)
- W10 said "decide Temporal by comparison"; W11 said "Temporal is the core". Resolution (evidence):
  RECOMMEND-AS-TARGET + DEFER-INSTALL + Python interim that slot-conforms (orchestration_comparison.md).
- F1 (trigger overclaim): corrected by text-truth + plan; stores untouched pending owner (F1 plan).
- F2 (AG-11↔AG-13 cycle): repaired in registry (acyclic, CI-pinned forever).
- F5 (PROMOTE holder): AG-23 documented as human gateway; NEVER-to-be-software law recorded in ops.
- F6/F14 (stale counters/count drift): refreshed to measured values (569/716, 716/716, 63 principles).
- F9 (router mechanics): circuit breaker + health gating + numeric-provenance validator implemented+tested.

## 9. What remains design-only (honest)
Temporal slots, PG canonical store, OTel stack, n8n-edge activation, per-agent envelope wrapping
for the 8 Lane-A EXISTS agents (frozen — wrap only via owner-authorized migration + replay parity),
provider-strength probes on real models (needs keys = owner decision), AG-01 runtime (awaits P4-host).
