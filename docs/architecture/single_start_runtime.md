# AHOS — SINGLE-START RUNTIME (Master Runtime Controller)
W11 §2/§4 · implementation state: CONTROL SURFACE IMPLEMENTED+TESTED (Python, this repo);
target runtime slots (Temporal/PG) contracted, deferred (no host — see orchestration_comparison.md).

## 1. The one control surface
`AHOS_START` / `AHOS_STOP` / `AHOS_STATUS` / `AHOS_SAFE_HALT` / `AHOS_RESUME`
Operator experience today (this repo): `python3 -c "from architecture.control_plane import
ControlPlane; print(ControlPlane().start())"` — one command, full boot chain, honest verdict.
Tomorrow (host exists): the same surface wraps docker compose + Temporal; the operator NEVER
sees the difference.

## 2. What ONE START does (all ledgered, all evidenced)
1. env validation (secrets presence = env-only; none read into files)
2. infra discovery (measured, never assumed)
3. PostgreSQL health → 4. Temporal health → 5. AHOS engine health → 6. n8n health →
7/8. optional Redis/bus health (never affects status) → 9. config verification →
10. state verification → 11. agent registry validation → 12. dependency graph (cycle ⇒ HALT)
→ 13. locks (single active run) → 14. agent startup (orchestrated only) → 15. workflow startup
→ 16. health verification → SYSTEM_ONLINE / SYSTEM_DEGRADED / SAFE_HALT

## 3. Idempotency proof obligations (test-pinned)
- repeated START with same config+registry ⇒ SAME run, 0 duplicate activations
- crash mid-run ⇒ RESUME skips completed phases, re-measures health, completes
- SAFE_HALT run NEVER replays as a later success (new attempt executes)
- ledger rows are append-only (trigger-enforced; tamper test included)

## 4. Component contract (every component declares)
purpose · owner(agent/boot class) · health check · failure mode · fallback — see
config/control_plane.yaml `infrastructure` block (8 components declared with MEASURED
availability; targets stay targets until a host exists).

## 5. Current honest capability of the surface
| Verb | Works today? | Evidence |
|---|---|---|
| START (full chain, honest verdict) | YES (Python engine) | test_one_start_system_online + test_real_config_boot_never_fabricates_online |
| STOP (graceful, reverse order) | YES | test_graceful_stop_reverse_order |
| STATUS (6 questions) | YES | test_status_surface_answers_six_questions |
| SAFE_HALT (operator-forced) | YES | API + lock steal audit test |
| RESUME (from ledger) | YES | test_restart_resumes_from_ledger |
| Boot actual containers/Temporal workers | NO — NO HOST | BLOCKED_NO_HOST, never claimed |
| Start real agent services | NO — orchestrated=0 by design this wave | totals test pins orchestrated=0 |
