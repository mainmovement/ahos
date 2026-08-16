# E-01 GATE REPLAY — COHORT REPORT (R8 artifact #2) · 2026-08-15 Replay
Replay timestamp: 2026-08-15T07:10:00Z · Pre-requisite: A-1 D-FS-01 minimal amendment applied & proven

## Cohort definition (frozen)
- Cohort = all tokens in `observation_state` of `data/e01_discovery.sqlite` (first_seen in [2026-08-11T18:00:03Z .. 2026-08-14T04:59:36Z]).
- |cohort| = **952 tokens** · observations = **1736**
- Observation State Census (post-materialize sweep):
  - **RESOLVED**: 223 tokens (reached ≥72h age)
  - **DEAD**: 729 tokens (no observation for >24h)
  - **OBSERVING**: 0 tokens
  - **DISCOVERED**: 0 tokens

## R2 — Coverage segmentation, PRE_FIX vs POST_FIX (never merged)
Poller activation boundary (F12-O2/O2a, owner-authorized): 2026-08-13T04:30:33Z (epoch 1786595433.489443).
| Segment | Observation Rows | Distinct Tokens |
|---|---|---|
| PRE_FIX (retrieved_ts < activation) | 987 | 762 |
| POST_FIX (retrieved_ts ≥ activation) | 749 | 451 |

## Horizon-by-horizon coverage (closed legal windows only; per horizon; NEVER merged)
| Horizon Slot | Total Closed | Covered | Coverage Rate | Missed Gaps Registered |
|---|---|---|---|---|
| s+15m | 952 | 115 | 0.1208 | 837 |
| s+1h | 952 | 80 | 0.0840 | 872 |
| s+4h | 952 | 211 | 0.2216 | 741 |
| s+12h | 952 | 0 | 0.0000 | 952 |
| s+24h | 952 | 117 | 0.1229 | 835 |
| s+48h | 952 | 73 | 0.0767 | 879 |
| s+72h | 952 | 729 (52 outcomes generated) | 0.0546 (covered outcomes) | 223 |
| 7d | not matured (matures 2026-08-18+) | — | — | — |

## Gap Register Audit (Honest law-abiding registration)
- `gap_register` total rows: **5,339**
- Breakdown by kind:
  - `missed:s+12h`: 952
  - `missed:s+15m`: 837
  - `missed:s+1h`: 872
  - `missed:s+24h`: 835
  - `missed:s+48h`: 879
  - `missed:s+4h`: 741
  - `missed:s+72h`: 223
- All overdue snapshot slots have been registered with full provenance in accordance with §7 and §23 immutability laws. No backfill, no fabrication.

## Cohort boundaries & Execution Context
- First token discovery: 2026-08-11T18:00:03Z; last discovery: 2026-08-14T04:59:36Z.
- Feature vectors materialized: **6,745** rows across 952 tokens under `fs_v0.2`.
- Outcome labels generated: **1,048** rows across 223 RESOLVED tokens.
- 7d labels remain out-of-scope until maturation (2026-08-18+).
