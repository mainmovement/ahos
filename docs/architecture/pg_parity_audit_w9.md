# AHOS W9/P2 — SQLite ⇄ PostgreSQL PARITY AUDIT (audit only; NO migration performed)
2026-08-13 · computed from live stores + `database/postgresql_schema.sql` (read-only).

## Measured parity matrix
| Store | Live SQLite tables | Covered by PG DDL | Verdict |
|---|---|---|---|
| e01_discovery.sqlite | 15 (tokens, pairs, discovery_observations, raw_payloads, observation_state, lifecycle_events, feature_*, outcome_label, security_verdicts, gap_register, gate_summary, opportunity_rank, holder_snapshot, wallet_observation) | **0/15** | FULL DRIFT |
| paper_trading.sqlite | 17 (incl. v2/v3: portfolio_ledger, position_state_event, realizable_snapshot, position_decision_event, paper_exit_v3, post_trade_lesson, learning_stats_snapshot, scam_assessment, decision_snapshot_v2 …) | **0/17** | FULL DRIFT |
| ahos_local.sqlite | 1 (control_flags) | 0/1 | DRIFT |
| PG DDL only (no live counterpart) | — | 8 (agent_audit_trail, agent_registry, evolution_memory, market_data, model_parameter_history, position_monitoring, telegram_audit, trade_decisions) | wave-1 era; needs reconciliation |

**Total drift: 33/33 live tables absent from the PG DDL; 8 LDA-era PG tables need mapping/merge decisions.**
Name collision flagged: PG DDL `agent_registry` vs this wave's W9 agent-registry concept
(Lane-B store `data/architecture_registry.sqlite`) — semantics differ (n8n runtime agents vs
cognitive agents); reconciliation required in P2, no silent merge.

## P2 plan (designed, not executed)
1. Generate PG DDL for all 33 live tables from the SQLite DDL (dialect translation: REAL→NUMERIC,
   INTEGER PK AUTOINCREMENT→BIGSERIAL, triggers→rules/functions; append-only law preserved via
   triggers in PG).
2. Parity tests: same insert battery into both stores ⇒ row-count + checksum equality per table;
   replay a fixed cycle window through both stores.
3. Dual-write OFF experiment path initially: PG mirror populated from SQLite snapshots
   (additive, reversible; SQLite remains the experiment's source of truth until gates pass).
4. Provenance preservation: created_utc/obs_ref/sha columns migrate byte-identical; no row
   rewriting; migration itself recorded as a register entry with row-counts before/after.
5. Destruction rule: SQLite evidence is NEVER deleted by migration.

## Blockers for P2 execution
Nothing technical blocks the AUDIT; execution requires a host running PG (VPS blocker) OR a
local container runtime — absent in this sandbox. P2 execution therefore waits for Docker/VPS
(P4 dependency) unless a local postgres mock is approved ($0 constraint noted).
