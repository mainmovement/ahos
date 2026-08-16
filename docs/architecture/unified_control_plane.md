# AHOS — UNIFIED CONTROL PLANE (specification + implemented engine)
W10 §4–§6 / W11 §2 · contract: contracts/control_plane_contract_v1.json · engine:
architecture/control_plane.py (IMPLEMENTED, test-pinned) · config: config/control_plane.yaml

## 1. Operator abstraction law
The operator sees ONE system and five verbs: START · STOP · STATUS · SAFE_HALT · RESUME.
The operator NEVER manually starts Python agents, stores, routers, red team, n8n, or probes
during normal operation. A repeated START is idempotent; a restart inspects the durable ledger,
determines the last valid state, and resumes — never a blind restart.

## 2. Boot chain (16 ledgered phases)
env_validation → infra_discovery → postgres_health → temporal_health → engine_health →
n8n_health → optional_redis_health → optional_bus_health → config_verify → state_verify →
registry_load → dependency_graph (cycle = SAFE_HALT) → locks (single-active-run; stale-lock
takeover is recorded) → agent_startup (only operability.implemented==orchestrated==true agents
ENTER the runtime; every other agent is REPORTED as REGISTERED/NOT_IMPLEMENTED, never pretended)
→ workflow_startup → health_verify → terminal status.

## 3. Terminal status law (exactly three operator states + transitions)
- SYSTEM_ONLINE — all CRITICAL and NON_CRITICAL/ADVISORY components verified HEALTHY.
- SYSTEM_DEGRADED — any NON_CRITICAL or ADVISORY component failed/unavailable (e.g. Council
  OFFLINE, Gemini UNAVAILABLE, Telegram UNAVAILABLE). Deterministic AHOS continues — this is
  the deterministic-floor law expressed operationally.
- SAFE_HALT — any CRITICAL component failed or UNVERIFIED (PostgreSQL, evidence integrity,
  security gate, risk engine, decision engine, memory journal…). NO VALID EVIDENCE ⇒ NO
  CONFIDENT BOOT: UNKNOWN health on a CRITICAL component halts (test-pinned).
Transition states: BOOTING / RECOVERING / HALTED (contract enum).

## 4. Idempotency
idempotency_key = sha256(config_sha + registry_sha + intent). An identical completed START
returns the SAME run (idempotent_replay=true; zero duplicate activation rows — assert-tested).
A SAFE_HALTed run is NEVER replayed as success: a later START after recovery executes anew
(test: new run_id after prober recovery).

## 5. Resume / recovery
RESUME = START: in-flight run detection via idempotency key; completed phases replay as
PHASE_SKIPPED_RESUME events; health is ALWAYS re-measured (never cached truth); activations are
INSERT-OR-IGNORE (idempotent); crash mid-phase ⇒ phase re-runs, evidence accumulates append-only.

## 6. Locks
Single active run via a global ledger lock with heartbeat TTL (120s default). Fresh foreign lock
⇒ REFUSED + SAFE_HALT record. Stale lock (crash evidence) ⇒ STALE_LOCK_STOLEN audit event +
takeover (test-pinned).

## 7. Graceful shutdown
STOP walks the dependency graph in reverse topological order, ledgers every STOP, ends HALTED.

## 8. Observability surface (W10 §19 answers, live from the ledger)
status() returns: running · failed · why · evidence · last_valid_state · resumable.
Full metrics model: docs/mission_v1_1/W11_UNIFIED_RUNTIME_ARCHITECTURE.md §Observability.

## 9. Today's REAL boot (honest)
With the actual configs and no injected probers the engine returns SAFE_HALT: postgresql is
BLOCKED_NO_HOST and every unprobed health is UNKNOWN (test_real_config_boot_never_fabricates_online).
The plane never fabricates ONLINE. In this repo reality the deterministic Lane-A core continues
via its standing schedule — safe BY DESIGN, not by pretending the plane is up.
