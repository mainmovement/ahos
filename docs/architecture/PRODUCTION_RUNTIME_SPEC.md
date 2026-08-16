# AHOS Production Runtime Architecture Specification (Phase XX)

## 1. System Overview
The AHOS Production Runtime is an evidence-first, resilient cryptocurrency opportunity intelligence platform designed for 24/7 autonomous monitoring without real financial trading risk ($0 cost ceiling, Iran-resilient, non-trading by contract).

```
                      +-----------------------------+
                      | ApplicationLifecycleManager |
                      |    (architecture/runtime)   |
                      +--------------+--------------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
+--------v--------+         +--------v--------+         +--------v--------+
| CollectorEngine |         |  ProdScheduler  |         | TelegramRunner  |
| (collector/)    |         |  (scheduling/)  |         | (telegram_ai/)  |
+--------+--------+         +--------+--------+         +--------+--------+
         |                           |                           |
         +---------------------------+---------------------------+
                                     |
                    +----------------v----------------+
                    | OpportunityPipelineOrchestrator |
                    |      (architecture/pipeline)    |
                    +----------------+----------------+
                                     |
                    +----------------v----------------+
                    | Storage Backplanes & SQLite DBs |
                    +---------------------------------+
```

## 2. Core Subsystems

### 2.1 Runtime Layer (`architecture/runtime/`)
- **Lifecycle Manager:** Transitions cleanly through `INITIALIZING -> STARTING -> RUNNING -> STOPPING -> STOPPED`.
- **Startup Validator:** Validates schema integrity, governance hash locks (Master Directive v1 SHA-256), and paper-only invariant before accepting traffic.
- **Structured Logger:** Redacts secrets automatically and outputs JSON logs with correlation `run_id`.
- **Health Checks:** Probes database files, memory usage, and circuit breaker status.

### 2.2 Collector Engine (`architecture/collector/`)
- **Multi-Source Polling:** Queries DexScreener, GeckoTerminal, GoPlus, and RugCheck.
- **Circuit Breaker:** Triple-state (CLOSED, OPEN, HALF-OPEN) preventing cascade failures during RPC rate limits or network outages.
- **Retry Policy:** Exponential backoff with configurable jitter and max retries.
- **Provenance:** Records exact timestamp, provider, token, and payload SHA-256 digest for every observation.

### 2.3 Production Scheduler (`architecture/scheduling/`)
- **Wall-Clock Schedule:** Aligns observation cycles to standard intervals ($s+15\text{m}, s+1\text{h}, s+4\text{h}, s+12\text{h}, s+24\text{h}, s+48\text{h}, s+72\text{h}, s+7\text{d}$).
- **Atomic Lease Locking:** Uses `scheduler_locks` to prevent overlapping worker runs.
- **Missed Window Detection:** Identifies overdue snapshot slots and registers `missed:<slot>` in `gap_register` without backfilling.
- **Clock Drift Safety:** Aborts if system clock drift exceeds 5.0 seconds.

### 2.4 Telegram Intelligence Surface (`telegram_ai/`)
- **Bot API Abstraction:** Unified interface for Mock and HTTP Production adapters.
- **Persian NLU:** Deterministic intent parser supporting all 9 canonical queries.
- **Security Gate:** Enforces authorized chat IDs and user rate limits.
- **Section X Response Contract:** Delivers structured Persian intelligence ending with: «تصمیم نهایی با کاربر است.».

### 2.5 Opportunity Pipeline (`architecture/pipeline/`)
- Orchestrates end-to-end flow:
  $\text{Providers} \rightarrow \text{Normalization} \rightarrow \text{Evidence} \rightarrow \text{Features} \rightarrow \text{Risk} \rightarrow \text{Opportunity Score} \rightarrow \text{Alerts} \rightarrow \text{Telegram}$

## 3. Failure Modes and Recovery Strategies

| Failure Mode | Detection Mechanism | Immediate Action | Recovery Strategy |
|---|---|---|---|
| **Provider Rate Limit (429 / HTTP Error)** | HTTP Status / Exception caught in Collector | Circuit Breaker trips to `OPEN`; requests fail fast | Auto-retry after 30s cooldown; fallback to secondary providers |
| **Database Corruption / Missing DB** | Startup Validator `PRAGMA integrity_check` | Startup halts (`FAILED` state); log emitted | Restore from point-in-time snapshot; reject corrupted writes |
| **System Clock Drift (> 5s)** | Scheduler monotonic drift detector | Cycle aborts with `ABORTED_DRIFT` | Resynchronize NTP; resume once clock aligns |
| **Session Clock Gap / Scheduler Downtime** | Heartbeat delta detector | Downtime logged; overdue slots registered as `missed:<slot>` | Process legal open windows only; no retroactive backfilling |
| **Honeypot / Security Risk Escalation** | GoPlus / RugCheck signal processor | Score drops to 0; Critical alert emitted | Position auto-invalidates (`CLOSED_INVALIDATED`) |
| **Secret / Key Leak Attempt** | Security regex filter | Token / key pattern replaced with `[REDACTED_SECRET]` | Sanitized text emitted; zero credentials persisted |
