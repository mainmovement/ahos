# AHOS — Soak Operator Start (Windows Laptop)

**One deterministic path from a fresh clone to a running 168-hour local soak.**

This is the command sheet. The reasoning behind each gate lives in
`AHOS_LOCAL_SOAK_PROTOCOL.md`; the hardware/power preconditions live in
`AHOS_LAPTOP_READINESS_CHECKLIST.md`. Run those first — this document assumes
the checklist is already green.

**Sandbox / Arena hours never count.** The official clock starts only on this
laptop, only after `official_168h_eligible=true`.

---

## 0. Preconditions (from the checklist)

- [ ] Windows 10/11, 64-bit, Python 3.11+
- [ ] AC power connected; sleep + hibernate disabled on AC; lid-close = Do nothing
- [ ] ≥ 2 GB free disk
- [ ] OS automatic time sync **ON** (drift detection assumes a sane host clock — M-GAP-006)

---

## 1. Update to the release commit

```powershell
cd C:\path\to\ahos
git pull
git rev-parse HEAD          # record this SHA in your soak log
```

## 2. Virtual environment + dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Initialize the local stores

```powershell
.\.venv\Scripts\python.exe scripts\init_databases.py --with-guards
```

Expect `RESULT: ALL STORES HEALTHY`. This also creates
`opportunity_score_ledger` (the prediction ledger) with its append-only guards.

## 4. Integrity gates — all three must pass

```powershell
.\.venv\Scripts\python.exe scripts\freeze_lane_a.py
.\.venv\Scripts\python.exe scripts\validate_imports.py
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

Expected: `Lane-A integrity OK (36 files pinned)`, `VALIDATION PASSED`, and a
fully green suite. **If any gate fails, stop.** A soak started on a red gate
produces evidence nobody can trust.

## 5. Provider probe — the M-GAP-007 moment

```powershell
.\.venv\Scripts\python.exe -m architecture.runtime --probe-providers
```

This writes `reports\provider_probe_<UTC>.json` and prints a classified table.
Statuses are disjoint and a failure is never rounded up:

| Status | Meaning |
|---|---|
| `SUCCESS` | provider answered **and** returned ≥ 1 token — the only success |
| `EMPTY` | answered cleanly with 0 tokens (reachable, but not proof of data) |
| `TLS_ERROR` | TLS/SSL handshake failed (the sandbox's signature failure) |
| `TIMEOUT` | no answer within the deadline |
| `RATE_LIMIT` | HTTP 429 / provider rate-limit envelope |
| `AUTH_REQUIRED` | credential missing or rejected |
| `UNSUPPORTED` | provider genuinely does not serve this chain / has no discovery endpoint |
| `ERROR` | reached but failed (5xx, bad payload) |
| `UNKNOWN` | unclassifiable — never means "probably fine" |

Exit code `0` = at least one `SUCCESS`; exit code `3` = ran fine, nothing live.

**Commit the artifact either way.** A laptop that reaches DexScreener closes
M-GAP-007; a laptop that does not has produced an honest failure record.

## 6. Record the official baseline

```powershell
.\.venv\Scripts\python.exe scripts\record_local_laptop_baseline.py
```

This refuses to certify unless: Windows, Python 3.11+, **clean git tree**,
Lane-A intact, all four SQLite stores `integrity_check = ok`, and no live-trading
env vars set. It exits `2` when ineligible.

Proceed only when the artifact says:

```json
"official_168h_eligible": true
```

## 7. Start the daemon — declare it as REAL evidence

```powershell
$env:AHOS_EVIDENCE_SOURCE = "local"
.\.venv\Scripts\python.exe -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

**`AHOS_EVIDENCE_SOURCE=local` is mandatory and deliberate.** Predictions are
stamped with an evidence namespace, and **only `local` is calibration-eligible**.
The default is `sandbox` precisely so that no unlabelled run can quietly become
the evidence your calibration is later computed from. The daemon logs which
namespace it is using on startup — check that line.

Equivalent without the env var:

```powershell
.\.venv\Scripts\python.exe -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
```

## 8. Confirm the watchdog sees a heartbeat

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -m architecture.scheduling.watchdog --status --json
```

Must report `OK` (not `NO_HEARTBEATS`) within a few minutes of daemon start.

## 9. Write the t0 snapshot — the clock starts here

```powershell
.\.venv\Scripts\python.exe scripts\system_state_snapshot.py --probe-providers
.\.venv\Scripts\python.exe scripts\soak_snapshot.py --window-hours 1
```

Record the UTC timestamp of the t0 snapshot. **That is hour 0 of 168.**

---

## During the window

| Cadence | Command |
|---|---|
| every 6h (first 48h), then daily | `scripts\soak_snapshot.py --window-hours <hours elapsed>` |
| nightly | `scripts\sqlite_backup_restore.py nightly` |
| any time | `python -m architecture.scheduling.watchdog --status` |

Nightly backups accumulate into `reports\nightly_backup_series.json`. That file
counts **distinct UTC dates**, not invocations — running it four times in one
evening still reads `1/7`. `series_complete` flips to true only after seven
real days, which is what M-GAP-010's residual actually requires.

Deliberate recovery events (kill -9, SIGTERM, a 20-minute pause) are scheduled
in `AHOS_LOCAL_SOAK_PROTOCOL.md` §6-7. Do them, and snapshot after each.

Commit snapshots under `reports\` and never overwrite one. A gap in the series
must be explained (sleep, travel, kill) — an unexplained gap invalidates the
window.

---

## After the window

```powershell
.\.venv\Scripts\python.exe scripts\calibration_report.py
```

Read `calibration_status` honestly:

- `INSUFFICIENT_DATA` — expected for a long time. The guards are
  n ≥ 200 per score band and ≥ 20 positives, inherited from
  `research/baseline_stats.py`. **Never lower them to get a greener word.**
- `DESCRIPTIVE_OK` — enough real pairs exist to describe score-vs-outcome.
  Read `monotonicity`: `NOT_MONOTONIC` means higher scores did **not** produce
  better outcomes, which is a finding about AHOS, not a bug in the report.

Every report carries `dataset_fingerprint`, `exclusion_reasons`,
`source_census` and `observation_window` so a reader can always answer
*"this number came from exactly which rows?"*.

---

## What this path deliberately does not do

- It does not deploy to a VPS. The target is this laptop.
- It does not enable trading. There is no order, wallet, or signing surface.
- It does not claim the soak, the provider success, the calibration, or the
  7-night backup series. Those become true only when the commands above are
  actually run here and their artifacts committed.
