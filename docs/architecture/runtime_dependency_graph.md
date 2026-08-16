# AHOS — RUNTIME DEPENDENCY GRAPH (machine-checked acyclic)
Source of truth: config/control_plane.yaml (infrastructure) + config/agent_registry.yaml
(ops.startup_policy.depends_on). The graph is rebuilt by architecture/control_plane.py and
cycle-checked on every boot and in CI (test_real_registry_is_acyclic).

## Topology (target)
```
                 AHOS MASTER START
                       │
               Runtime Controller (control_plane.py → Temporal slot later)
                       │
   ┌──────────┬────────┴───────────┬──────────────┬───────────────┐
PostgreSQL  Temporal            Redis*        NATS*/Kafka*      n8n (external edge only)
 (CRITICAL  (NON_CRITICAL,      (OPTIONAL,    (OPTIONAL,        (OPTIONAL today;
  target;    target; Python     NOT_JUSTIFIED) NOT_JUSTIFIED)   Telegram/webhooks/admin)
  BLOCKED    interim)
  NO_HOST)
                       │
                Agent Workers (25; boot_class ordered; W12: AG-25 registered)
                       │
        ┌──────────────┼─────────────────────┐
   Model Router    Red Team            Observability (run-ledger now;
   (ADVISORY)      (NON_CRITICAL,      OTel/Prometheus/Grafana target)
                    fail-closed for
                    promotions)
                       │
        Deterministic Lane-A core (CRITICAL floor: collector, gate, risk,
        decision, paper engine, evidence stores — NEVER depends on any AI)
```
*optional components never affect system status (test-pinned).

## Boot classes → failure semantics
CRITICAL (failed/unverified ⇒ SAFE_HALT): postgresql(target), ahos_engine, evidence_stores,
AG-01(∅ by design), AG-02, AG-07, AG-08, AG-09, AG-15, AG-16, AG-17, AG-21, AG-23(human gateway).
NON_CRITICAL (⇒ SYSTEM_DEGRADED): temporal(target), observability(target), AG-03..06, AG-14,
AG-18, AG-19, AG-22, AG-24.
ADVISORY (⇒ SYSTEM_DEGRADED, floor continues): AG-10, AG-11, AG-12, AG-13, AG-20, AG-25 (W12).
OPTIONAL (never affects status): redis, event_bus (both NOT_JUSTIFIED by evidence).

## Key edges (excerpt, from registry ops blocks)
AG-15 ← AG-07, AG-08, AG-09 · AG-16 ← AG-15 · AG-18 ← AG-16 · AG-08 ← AG-09 · AG-11 ← AG-12, AG-13 ·
AG-13 ← ∅ (post-F2 repair) · AG-14 ← AG-21 · AG-01 ← AG-22, AG-23 · AG-20 ← AG-14, AG-18 ·
AG-25 ← AG-14, AG-20 (W12) ·
AG-19 ← AG-02 · AG-22 ← AG-17 · AG-02..07/09/10/12/17/21/23/24 ← infra/pal (documented in ops.notes,
typed dependency kinds land with contract v2 — W10 F3 queue).

## Sandboxing law
Lane-A agents (AG-02, 03–09, 15–16, 18) run TODAY via the standing deterministic schedule;
the control plane REPORTS them (REGISTERED+liveness evidence) but does not yet start them
(orchestrated=0, pinned). When orchestration activates later, it MUST go through a new registry
version + replay parity evidence + owner approval (two-lane law).
