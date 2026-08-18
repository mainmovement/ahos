# AHOS Laptop Readiness Checklist (Windows)

Official 168h clock starts **only** on this machine after every box is checked and `reports/local_laptop_baseline.json` exists.

Sandbox / Arena hours **do not count**.

---

## 1. Operating system

- [ ] Windows 10 or 11 (target)
- [ ] 64-bit
- [ ] Record edition + build: `winver` or `systeminfo | findstr /B /C:"OS Name" /C:"OS Version"`

## 2. Power (mandatory)

On **AC power**:

```
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 15
```

- [ ] AC connected
- [ ] Sleep disabled on AC
- [ ] Hibernate disabled on AC
- [ ] Lid close = Do nothing (Control Panel → Power Options → Choose what closing the lid does)
- [ ] Automatic shutdown / “battery saver sleep” off while on AC

If the laptop sleeps anyway: log UTC in `reports/local_soak_interruptions.jsonl` and **do not** count those hours.

## 3. Storage

- [ ] ≥ 2 GB free on the drive that holds the clone
- [ ] Database dir: `%CD%\data` (or `AHOS_DATA_DIR` if you set one)
- [ ] Backup dir: `%CD%\data\backups` (create it; gitignored)

```
mkdir data\backups
dir data
```

## 4. Runtime

From the clone (PowerShell):

```
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_databases.py
.\.venv\Scripts\python.exe scripts\freeze_lane_a.py
.\.venv\Scripts\python.exe scripts\validate_imports.py
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

- [ ] Python 3.11+
- [ ] venv created
- [ ] `requirements.txt` installed
- [ ] `freeze_lane_a.py` → `Lane-A integrity OK`
- [ ] `validate_imports.py` PASS (record with `scripts\record_test_run.py` if desired)
- [ ] pytest green

## 5. Environment variables

- [ ] `TELEGRAM_BOT_TOKEN` unset (mock adapter is correct for soak)
- [ ] `AHOS_EXECUTE_LIVE_TRADES` unset / not `1`
- [ ] `AHOS_ALLOW_REAL_FUNDS` unset / not `1`
- [ ] `AHOS_CHAIN` optional (`solana` default)
- [ ] `ALL_PROXY` / `HTTPS_PROXY` only if you already use them for egress

No exchange keys. No wallet keys.

## 6. Clean laptop baseline (before start)

Working tree must be **clean** on the merged `main` release SHA. Record the exact SHA; do not rely on unavailable historical SHAs.

```
git status
git rev-parse HEAD
.\.venv\Scripts\python.exe scripts\record_local_laptop_baseline.py
```

Must create `reports\local_laptop_baseline.json` with: timestamp UTC, git SHA, OS, Python, dependency hash, DB integrity, Lane-A status, daemon command.

- [ ] `reports\local_laptop_baseline.json` written on **this** laptop
- [ ] `git.working_tree_clean` is true inside that file
- [ ] `checks.all_databases_integrity_ok` is true
- [ ] `checks.execution_flags_disabled` is true
- [ ] `official_168h_eligible` is **true**

## 7. Official soak start (only after §1–6)

```
.\.venv\Scripts\python.exe -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

Leave this window open. Then in a **second** PowerShell:

```
.\.venv\Scripts\python.exe -m architecture.scheduling.watchdog --status --max-age-sec 300 --json
.\.venv\Scripts\python.exe scripts\system_state_snapshot.py --probe-providers --out reports\soak\system_state_t0.json
```

The 168h clock starts only when **all** of these are true on this laptop:

- [ ] daemon running
- [ ] watchdog `status=OK`
- [ ] first snapshot written
- [ ] `reports\local_soak_start.json` updated with laptop UTC + SHA (do not reuse the sandbox start file as-is)

## 8. During soak (no code changes)

Every 6h (first 48h), then every 12h:

```
.\.venv\Scripts\python.exe scripts\system_state_snapshot.py --probe-providers --out reports\soak\system_state_<UTC>.json
.\.venv\Scripts\python.exe scripts\soak_snapshot.py --window-hours <hours since start>
```

Every 24h: update `AHOS_LOCAL_SOAK_STATUS.md`.  
Nightly: backup each `data\*.sqlite` into `data\backups\` via `scripts\sqlite_backup_restore.py backup`.

## 9. Failure injection (do not improvise)

| When | Action |
|---|---|
| Day 1, hour ≥ 2 | Task Manager / `taskkill /F /PID <pid>` then restart §7 |
| Day 3 | Ctrl+C (graceful), wait, restart |
| Day 5 | stop 20 minutes, restart; confirm integrity |

## 10. Classification (do not skip)

| State | When |
|---|---|
| `LOCAL_SOAK_READY` | checklist done, baseline file exists, daemon not yet official |
| `LOCAL_SOAK_RUNNING` | laptop daemon + watchdog OK + t0 snapshot |
| `LOCAL_SOAK_FAILED` | silent death, data loss, fabricated data, or safety breach |
| `LOCAL_PRODUCTION_READY` | **only** after 168h laptop evidence + recoveries + backups |

Sandbox `LOCAL_SOAK_RUNNING` on Arena is **not** this clock.
