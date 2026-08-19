# AHOS Operator Quickstart — Windows

**One page, PowerShell only, in order.** Copy each block as-is.

Every command here was verified to exist with these exact flags at commit
`164766b`. Nothing in this file is bash, and nothing requires a VPS.

- Full reasoning per gate → `AHOS_SOAK_OPERATOR_START.md`
- Pre-flight boxes (power, disk, sleep) → `AHOS_LOCAL_ACTIVATION_CHECKLIST.md`
- The 168-hour contract and recovery drills → `AHOS_LOCAL_SOAK_PROTOCOL.md`

> **Arena/sandbox hours never count.** Only this laptop can produce real evidence.

---

## 0. Open PowerShell in the repo

```powershell
cd C:\path\to\ahos
```

If scripts are blocked when activating the venv, allow them for this session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## 1. Clone or pull

First time:

```powershell
git clone https://github.com/mainmovement/ahos.git
cd ahos
```

Already cloned:

```powershell
git pull
git rev-parse HEAD
```

Record that SHA — every artifact you produce is tied to it.

## 2. Create and activate the venv

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation your prompt shows `(.venv)`. Confirm the interpreter and that
it is 64-bit:

```powershell
python -c "import sys; print(sys.version); print(sys.executable); print(sys.maxsize > 2**32)"
```

Requires **3.11+** and `True`.

> Every command below assumes the venv is active. If you prefer not to activate,
> replace `python` with `.\.venv\Scripts\python.exe` throughout — both work.

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Initialize the databases

```powershell
python scripts\init_databases.py --with-guards
```

Expect `RESULT: ALL STORES HEALTHY` (four stores + append-only guards).

## 5. Verify the repository

```powershell
python scripts\freeze_lane_a.py
python scripts\validate_imports.py
python -m pytest tests\ -q
```

Expect `Lane-A integrity OK (36 files pinned)`, `VALIDATION PASSED`, and a fully
green suite. **If any of the three is red, stop here.**

## 6. Provider probe

```powershell
python -m architecture.runtime --probe-providers
```

Writes `reports\provider_probe_<UTC>.json`.

| Exit | Meaning |
|---|---|
| `0` | at least one provider `SUCCESS` — this laptop reaches market data |
| `3` | ran fine, nothing live — still commit the artifact |

Only `SUCCESS` (answered **and** ≥ 1 token) counts. Other statuses:
`EMPTY`, `TLS_ERROR`, `TIMEOUT`, `RATE_LIMIT`, `AUTH_REQUIRED`, `UNSUPPORTED`,
`ERROR`, `UNKNOWN`. Do **not** disable TLS verification to force a green result.

## 7. Baseline — the eligibility gate

```powershell
python scripts\record_local_laptop_baseline.py
```

Writes `reports\local_laptop_baseline.json`. Requires
`"official_168h_eligible": true`. Exits `2` and refuses otherwise, listing the
failed checks. **Do not continue past a refusal.**

Optional wider readiness view:

```powershell
python scripts\local_activation_report.py
```

## 8. Start the daemon — declare it as REAL evidence

```powershell
$env:AHOS_EVIDENCE_SOURCE = "local"
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

The startup log must read:

```
Prediction evidence namespace: local
```

If it says `sandbox  (NOT calibration-eligible)`, the variable did not reach the
process — stop, set it, and restart. **Only `local` rows can ever be used for
calibration**; the default is `sandbox` so nothing becomes real evidence by
accident.

Leave this window open. Run everything below in a **second** PowerShell window
(`cd` to the repo and activate the venv there too).

## 9. Confirm the watchdog sees a heartbeat

```powershell
python -m architecture.scheduling.watchdog --status --json
```

Must report `OK` within a few minutes of daemon start (not `NO_HEARTBEATS`).

## 10. Write the t0 snapshot — the clock starts here

```powershell
python scripts\soak_t0_snapshot.py
```

Writes `reports\soak\system_state_t0.json`. Requires `"t0_valid": true`
(exit `0`). If it exits `3`, the file lists exactly what is missing — the four
conditions are: Windows host, eligible baseline, watchdog `OK`, and
`AHOS_EVIDENCE_SOURCE=local`.

**The `timestamp_utc` in that file is hour 0 of 168.** Record it.

## 11. Verify the first real prediction

After a few cycles:

```powershell
python -c "from architecture.learning.score_ledger import ScoreLedger; l=ScoreLedger(); print(l.source_census(), l.count(source='local'))"
```

Expect `{'local': N}` with `N > 0`. If it stays `{}`, the providers are not
returning data (see step 6) — the daemon is healthy but has nothing to score.

---

## During the 168 hours

### Snapshots

```powershell
python scripts\soak_snapshot.py --window-hours 6
python scripts\system_state_snapshot.py --probe-providers
```

Every 6h for the first 48h, then daily. Increase `--window-hours` to the hours
elapsed since t0. Never overwrite a previous snapshot; commit them under
`reports\`.

### Nightly backup

```powershell
python scripts\sqlite_backup_restore.py nightly
```

Appends to `reports\nightly_backup_series.json`. It counts **distinct UTC dates**,
so running it four times in one evening still reads `1/7`. `series_complete`
needs seven real days.

Verify a backup independently at any time:

```powershell
python scripts\sqlite_backup_restore.py drill
```

### Recovery drills (scheduled in the soak protocol §6)

Find the daemon and stop it hard (the Windows equivalent of `kill -9`):

```powershell
Get-Process python | Select-Object Id,StartTime,Path
Stop-Process -Id <PID> -Force
```

Graceful stop instead: press **Ctrl+C** in the daemon window.

After either, restart with step 8 and snapshot. Expect the scheduler to log
`SKIPPED_LOCKED` then take over, and the watchdog to go `STALE` → `OK`.

### Health check any time

```powershell
python -m architecture.scheduling.watchdog --status
```

---

## After the window

```powershell
python scripts\calibration_report.py
python scripts\calibration_report.py --horizon 24h --event-class "+50%"
```

Read `calibration_status` honestly:

- `INSUFFICIENT_DATA` — expected for a long time. Guards are n ≥ 200 per score
  band and ≥ 20 positives. **Never lower them to get a greener word.**
- `DESCRIPTIVE_OK` — enough real pairs exist. Then read `monotonicity`:
  `NOT_MONOTONIC` means higher scores did **not** produce better outcomes, which
  is a finding about AHOS, not a bug in the report.

---

## If something goes wrong

| Symptom | Check |
|---|---|
| `Activate.ps1 cannot be loaded` | run the `Set-ExecutionPolicy` line in step 0 |
| `python` not found | install Python 3.11+ and tick *Add to PATH* |
| Namespace logs `sandbox` | `$env:AHOS_EVIDENCE_SOURCE = "local"` in the **daemon's** window |
| Watchdog `NO_HEARTBEATS` | the daemon is not running — step 8 |
| Baseline exits `2` | open the JSON and read `failed_checks` |
| t0 exits `3` | open the JSON and read `t0_invalid_reasons` |
| Ledger census `{}` | providers returned nothing — step 6 |
| Laptop slept | log the UTC gap in `reports\local_soak_interruptions.jsonl`; those hours do not count |

## Scope

Observation-only. This procedure starts no trading, holds no wallet, signs no
transaction, and deploys nothing to a server. Completing it does **not** mean the
soak passed, the scoring is calibrated, or the system is production-ready — it
means AHOS is running locally and honestly recording what it sees.
