# AHOS Month 1 — 7-Day Soak Protocol

**Status:** ACTIVE (started 2026-08-18 — see §8 for live status)
**Window:** 7 consecutive days × 24h of continuous daemon operation (168h)
**Pre-registration rule:** the acceptance criteria in §7 were written BEFORE interpreting any
soak data. They may not be re-negotiated after evidence exists.

---

## 1. Objective

Determine whether AHOS survives real continuous operation without violating its safety,
scheduling, persistence, or provider contracts — and make every deviation visible.

## 2. System Under Soak

- Entrypoint: `python3 -m architecture.runtime --daemon --interval-sec 60 --observation-cycle`
  (lease-locked DAEMON_CYCLE + E-01 observation cycle, per-cycle fail-closed safety gate)
- No Telegram token (Mock adapter — no network Telegram), no external keys of any kind.
- Providers: live public endpoints (DexScreener / GeckoTerminal / GoPlus / RugCheck), best-effort,
  behind circuit breakers; failures are evidence, not blockers.

## 3. Installation Checklist (reproduced for any host)

```bash
git clone <repo> /opt/ahos && cd /opt/ahos
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/init_databases.py          # idempotent, zero fabrication
.venv/bin/python scripts/validate_imports.py         # must PASS
.venv/bin/python -m pytest tests/ -q                 # must be green
sudo cp deployment/ahos-runtime.service deployment/ahos-watchdog.service \
     deployment/ahos-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ahos-runtime ahos-watchdog.timer
```

(Sandbox pilot: same entrypoint and evidence pipeline via process supervisor; systemd N/A in-container.)

## 4. Required Recordings (auto-captured by existing instrumentation)

| Requirement | Where recorded |
|---|---|
| cycle start / completion / duration / drift / task errors | `scheduler_runs` (local DB) |
| scheduler delay | start-to-start gaps in `scheduler_runs` (snapshot tool computes) |
| heartbeat + downtime | `scheduler_heartbeats` |
| watchdog status | watchdog probe → snapshots + journald |
| lease acquisition/release | `scheduler_locks` + SKIPPED_LOCKED rows in `scheduler_runs` |
| provider availability / failures | fail-closed envelopes → `production_observations` gaps + circuit-breaker health; pipeline metrics |
| UNKNOWN fields / UNSUPPORTED responses | stored per-observation (`raw_evidence_hash`, unknown lists in candidates); cycle metrics |
| persistence events | all tables above + `runtime_operational_metrics` |
| restarts / crashes | systemd journal (VPS) / supervisor log (sandbox); visible as heartbeat downtime |
| clock-drift events | `scheduler_runs.clock_drift_sec` (ABORTED_DRIFT rows) |
| safety-gate events | BLOCKED observation reports → `runtime_operational_metrics` (status ERROR) |

## 5. Snapshot Cadence

`python scripts/soak_snapshot.py --window-hours <since start>` at minimum:
**every 6 hours** for the first 48h, then **every 12 hours**. Each snapshot is committed under
`reports/soak_snapshot_*.json` (never overwritten; gaps in snapshot series must be explained).

## 6. Deliberate Events (scheduled, to prove recovery paths for real)

| When | Event | Expected evidence |
|---|---|---|
| day 1, hour ≥ 2 | `kill -9` daemon, restart | SKIPPED_LOCKED-or-takeover path; heartbeat downtime recorded; watchdog STALE→OK transition |
| day 3 | `kill -TERM` (graceful) | clean shutdown log; immediate restart |
| day 5 | pause daemon 20 min | gap register entries + downtime_detected_sec ≈ 1200; no backfill |

## 7. Acceptance Criteria (pre-committed, objective)

A criterion is met only if the recorded evidence shows it — absence of evidence = not met.

**Scheduler**
- A1 zero overlapping executions (no concurrent SUCCESS pairs with interleaved start/finish; SKIPPED_LOCKED is the compliant outcome)
- A2 no silent scheduler death: watchdog status recorded in ≥ 95% of expected snapshots; any STALE must correspond to a real pause/restart event
- A3 no unexplained missed cycles: ≥ 90% of expected DAEMON_CYCLEs present (168h @ 60s ≈ 10,080 expected minus documented pauses); every gap > 5 min explained (restart/pause/ABORTED_DRIFT/SKIPPED_LOCKED)
- A4 heartbeat observable in every snapshot that follows a running period
- A5 watchdog remains fail-closed (NO_HEARTBEATS never reported as OK; STALE only for real silence)
- A6 clock-drift protection exercised: any drift > 5s ⇒ ABORTED_DRIFT row (no cycle runs under stepped clock)

**Persistence**
- B1 zero unexplained data loss: SQLite `integrity_check=ok` in every snapshot; observation counts never decrease without a documented cause
- B2 zero duplicate state transitions: no duplicate run_ids; no duplicate observation PKs
- B3 recovery proven for real: the three deliberate events of §6 produce the expected evidence

**Providers**
- C1 all failures explicit (error envelopes/breaker states — never silent zero-data SUCCESS)
- C2 unsupported capabilities remain UNSUPPORTED; C3 unavailable values remain UNKNOWN (spot-check sampled observations)
- C4 zero fabricated provider data (any value present ⇒ raw_evidence_hash present)
- C5 provenance traceable (spot-check: sampled fields resolve to provider + timestamp)

**Safety**
- D1–D4: zero real trading / wallet interaction / order execution / safety-bypass events (env veto + freeze gate stay armed; any BLOCKED report is evidence the gate works, not a failure)

**Observability**
- E1 every operational failure diagnosable from committed artifacts (journal/supervisor log + DBs + snapshots)
- E2 timestamps present on all recorded events (UTC)
- E3 logs sufficient to reconstruct failures (spot-check 3 incidents)

**Classification rule (Phase 5):** PASS = all criteria met with evidence · CONDITIONAL PASS =
system operated throughout with only non-critical gaps (A3/B1/C-series may carry ≤ 2 documented,
mitigated gaps; A1/A2/D-series must be clean) · FAIL = any critical (scheduler overlap, silent
death, data loss/fabrication, safety) requirement violated.

## 8. Live Status

- **Started:** 2026-08-18 (UTC) — sandbox pilot (host: Arena e2b container, NL region).
- **Environment caveat (honest):** the sandbox is a development container, not the target VPS.
  It proves real process behavior (scheduling, leases, persistence, fail-closed safety, live
  provider exposure) but the full 168h window requires an unmoved, always-on host. Migration to
  the VPS (same protocol, §3) is required for the gate's final classification; sandbox hours
  count as *pilot evidence*, not as the 168h window itself.
- Snapshots: `reports/soak_snapshot_*.json`; supervisor log captured continuously.
- Current status: see latest snapshot + `AHOS_MONTH1_OPERATIONAL_GATE.md`.
