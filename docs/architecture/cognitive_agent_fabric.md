# AHOS — COGNITIVE AGENT FABRIC (how agents become real)
W10/W11/W12 · sources of truth: config/agent_registry.yaml (25 agents, ops blocks) ·
contracts/agent_contract_v1.json (+ ops-fields) · architecture/control_plane.py

## 1. Agent existence is earned, never declared
"No agent may exist merely because a YAML file claims it exists" (W11 §6). The registry
encodes four INDEPENDENT machine-readable booleans per agent (ops.operability), validated by
tests (test_operability_totals_truthful):
- implemented — an executable artifact exists (file evidence linted for EXISTS agents)
- contracted — an enforceable contract covers its I/O (envelope/council/provider/proposal)
- orchestrated — the control plane can actually boot it (TODAY: 0/25 — honest)
- live — it has run in the current runtime (Lane-A agents run via standing cycles = live)
Invariant: live ⇒ implemented (validator-enforced; fake liveness fails validation).
Status letters (measured 2026-08-13 post-W12): 9 EXISTS / 12 PARTIAL / 3 PLANNED / 1 MISSING
(25 total) — never promoted without executable workspace evidence. W12 deltas: AG-17 promoted
PARTIAL→EXISTS after F1-S1 made its append-only claim measured-true on all governed stores
(probe refs in its registry block; R-34); AG-25 (OSS Capability Intelligence) registered PLANNED.

## 2. Lifecycle (contract enum)
REGISTERED → HEALTH_CHECK → READY → RUNNING → DEGRADED → CIRCUIT_OPEN → RECOVERING → RUNNING.
UNKNOWN health never becomes READY (no-evidence law applies to liveness).

## 3. Operability truth today (registry totals, test-pinned)
implemented 21 · contracted 6 · orchestrated 0 · live 15.
The 6 contracted: AG-11 (council contract), AG-12 (provider contract), AG-13 (council contract),
AG-14 (council contract/red-team stage), AG-20 (improvement_proposal_v1), AG-22 (control-plane
contract). The 8 Lane-A EXISTS agents are implemented+live but NOT yet contract-enveloped —
their I/O predates the contract and is FROZEN; wrapping is a future opt-in migration, never a
silent rewrite. The 9th EXISTS, AG-17 (Memory/Evidence Custodian, SHARED lane), is likewise
implemented+live, not yet contract-enveloped — promoted 2026-08-13 only after F1-S1 made its
trigger-guard claim measured-true (evidence: f1_s1 apply report, data_identical=true).

## 4. Criticality for boot (boot_class, independent of risk criticality)
CRITICAL (10): AG-01, 02, 07, 08, 09, 15, 16, 17, 21, 23 — failure/halt semantics per
control-plane law (SAFE_HALT). NON_CRITICAL (9): failure ⇒ DEGRADED. ADVISORY (6): AG-10, 11,
12, 13, 20, 25 — failure ⇒ DEGRADED, deterministic floor continues. OPTIONAL (0 today).
(ADVISORY is now 6 post-W12: AG-25 added; totals recomputed from registry by test.)
boot_class totals are computed from the registry by test, not asserted.

## 5. Dependencies (machine-checked)
The dependency graph is ACYCLIC (test_real_registry_is_acyclic — F2 permanently pinned;
AG-13's edge to AG-11 removed 2026-08-13: it consumes envelopes post-hoc, no service dep).
Dependency graph drives boot order (topo) and shutdown order (reverse topo).

## 6. Cognitive principles attached per agent
Each agent's ops.cognitive_principles links to matrix ids (config/cognitive_principles.yaml);
test_matrix_links_to_registry pins reference existence. The fabric's honesty chain:
principle → agent_capability → probe → contract → test → evidence (see
cognitive_agent_runtime_matrix.md for the full corpus table).
