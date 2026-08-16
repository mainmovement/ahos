# AHOS Production Scheduler Architectural Specification (Section XV)

## 1. Problem Statement & Historical Context
The E-01 validation window and Track B paper trading suffered from session-clock gaps (`G-SCHED` finding), where observations between interactive Agent sessions were missed. The historical protocol strictly forbids retroactively backfilling missed observations (§7/§23).
To transition from experimental gate mode to 24/7 continuous opportunity intelligence, a production-grade durable scheduler is required.

## 2. Core Architectural Laws
1. **No Silent Backfilling:** Missed observation windows must be logged as `missed:<slot>` in `gap_register`. Future coverage improves through continuous execution, not revisionism.
2. **Deterministic Time Injection:** All domain functions receive explicit `now: float` timestamps. Clock reads occur strictly at the outer edge/scheduling harness.
3. **Idempotency & Deduplication:** Concurrent or repeated execution of a snapshot task within its tolerance window ($\pm \text{tol}$) must be safe and idempotent (`INSERT OR IGNORE` / `ON CONFLICT DO UPDATE`).
4. **Lease & Distributed Locking:** Any multi-worker or cloud deployment must enforce atomic lease acquisitions (`scheduler_locks`) with expiration timeouts to prevent split-brain observation recording.
5. **Fail-Closed & Drift Bounds:** If system clock drift exceeds 5.0 seconds vs monotonic reference, scheduled tasks must abort to protect scientific causal ordering.

## 3. Observation Cadence & Window Tolerances
| Schedule Slot | Offset from Discovery ($T_0$) | Tolerance Window ($\pm$) | Target Operation |
|---|---|---|---|
| `s+15m` | 900s (15 min) | $\pm 300\text{s}$ | Rapid post-launch liquidity & volume check |
| `s+1h` | 3,600s (1 hour) | $\pm 600\text{s}$ | Baseline feature extraction point (`JOIN_OFFSET`) |
| `s+4h` | 14,400s (4 hours) | $\pm 1,800\text{s}$ | Early accumulation & holder check |
| `s+12h` | 43,200s (12 hours) | $\pm 1,800\text{s}$ | Mid-day traction & stability evaluation |
| `s+24h` | 86,400s (24 hours) | $\pm 1,800\text{s}$ | Primary outcome & survival evaluation |
| `s+48h` | 172,800s (48 hours) | $\pm 1,800\text{s}$ | Secondary continuation / rug detection |
| `s+72h` | 259,200s (72 hours) | $\pm 1,800\text{s}$ | Lifecycle closure / `RESOLVED` state transition |
| `s+7d` | 604,800s (7 days) | $\pm 7,200\text{s}$ | Macro trend / sustained liquidity audit |

## 4. Recommended Infrastructure Target
- **Phase 1 (Current):** Python SQLite-backed atomic leasing scheduler (`architecture/scheduling/engine.py`).
- **Phase 2 (VPS / Distributed):** Temporal.io or Celery Beat with Redis/PostgreSQL durable queues, running in isolated Docker containers with health probes and Prometheus metric exporters.
