# E-01 GATE — COHORT REPORT (R8 artifact #2) · 2026-08-14 gate execution
Gate due: 2026-08-14T18:00:00Z · execution began: 2026-08-14T18:06:00Z (owner-ordered, after 21:30 IRST)

## Cohort definition (frozen)
- Cohort = all tokens in `observation_state` of `data/e01_discovery.sqlite` (first_seen in
  [2026-08-11T18:00:03Z .. 2026-08-14T04:59:36Z]).
- |cohort| = **952 tokens** · observations = **1736** · state census (actual, post-crash-rollback):
  **952 OBSERVING / 0 RESOLVED / 0 DEAD** (sweep never executed — see R8 artifact #1).

## R2 — coverage segmentation, PRE_FIX vs POST_FIX (never merged)
Poller activation boundary (F12-O2/O2a, owner-authorized): 2026-08-13T04:30:33Z (epoch 1786595433.489443).
| segment | observation rows | distinct tokens |
|---|---|---|
| PRE_FIX (retrieved_ts < activation) | 987 | 762 |
| POST_FIX (retrieved_ts ≥ activation) | 749 | 451 |

## Horizon-by-horizon coverage (closed legal windows only; per horizon; NEVER merged)
| horizon slot | windows closed | covered | coverage rate | POST-only closed | POST-only covered | POST rate |
|---|---|---|---|---|---|---|
| s+15m | 952 | 115 | 0.1208 | 190 | 73 | 0.3842 |
| s+1h | 952 | 80 | 0.0840 | 266 | 58 | 0.2180 |
| s+4h | 952 | 211 | 0.2216 | 522 | 139 | 0.2663 |
| s+12h | 952 | 0 | 0.0000 | 594 | 0 | 0.0000 |
| s+24h | 879 | 117 | 0.1331 | 656 | 117 | 0.1784 |
| s+48h | 358 | 0 | 0.0000 | 358 | 0 | 0.0000 |
| s+72h | 0 (earliest closures ~18:30Z, still open at audit) | — | — | — | — | — |
| 7d | not matured (matures 2026-08-18+) — NOT required for gate (protocol out-of-scope note) | — | — | — | — | — |

## Starvation / gap disclosure (measured, not hidden)
- gap_register = **826** rows (last lawful sweep 2026-08-13-era). Additional misses since then —
  including **358 s+48h closed slots with 0 coverage** (incl. today's K1/K2 PT-linked misses) and
  **594 POST s+12h slots with 0 coverage** — are **NOT yet registered**: the materialize sweep
  crashed before reaching `lifecycle.sweep` (R8 artifact #1). Next lawful registration = rerun of
  the identical frozen materialize after the owner-gated defect fix (idempotent upserts; no backfill —
  every missed slot is registered as `missed:<label>`, never re-fetched).
- Would-be DEAD (no observation for >24h, tick-equivalent, read-only): **805 / 952**.
- Would-be RESOLVED at gate time (≥72h age, tick-equivalent, read-only): **88**; of these,
  tokens with any observation inside the legal 72h closure window (±1800s): **0**.
- Freshness at gate time: 0.0% of tokens with obs ≤1h; median latest-obs age ≈33.9h. G-SCHED is the
  binding constraint (no autonomous scheduler; session clock gaps: 05:19Z→18:06Z with zero cycles —
  buried 06:45:57Z and 08:11:48Z windows; plus prior 23h gap 08-13→08-14).

## Cohort boundaries
First cohort token first_seen 2026-08-11T18:00:03Z; last 2026-08-14T04:59:36Z. 7d labels excluded by design.
Collector: observation engine v1 + observe_active:v2 poller (POST_FIX) · snapshot schedule frozen
(15m±300s, 1h±600s, 4h/12h/24h/48h/72h±1800s, 7d±7200s; DEAD_AFTER 24h; RESOLVE_AT 72h).
