# AHOS Local Soak Protocol (laptop — 168h)

**Target host:** a single personal laptop (Linux, macOS, or Windows).  
**Not required:** VPS, cloud VM, systemd-on-server, off-box uptime monitors.  
**Window:** 168 consecutive hours of the local daemon.  
**Pre-registration:** these criteria are fixed before interpreting soak data.

`AHOS_MONTH1_SOAK_PROTOCOL.md` remains historical (sandbox pilot + VPS wording).  
**This file is the production soak contract for the local architecture.**

---

## 1. Laptop requirements

| Item | Minimum | Evidence of check |
|---|---|---|
| CPU / RAM | 2 cores, 4 GB free | host `uname` / Task Manager note in first snapshot |
| Disk | 2 GB free under `AHOS_DATA_DIR` (default `./data`) | `df` / Explorer |
| Python | 3.11+ venv from `requirements.txt` | `python --version` |
| Clock | OS time sync **on** (Windows: “Set time automatically”; macOS: Date & Time; Linux: `timedatectl`) | M-GAP-006 residual if off |
| Network | whatever the laptop already has; provider **success** is recorded honestly (failure is evidence) | `reports/system_state_snapshot.json#provider_probe` |
| Power | AC power preferred for 168h | §2 |

No extra servers. No Docker required. Telegram token **not** required (mock adapter).

---

## 2. Sleep prevention (mandatory)

A sleeping laptop is a **paused soak**, not a failed product — but it **breaks the 168h clock**. Document every sleep.

**Windows**

```
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 15
```

Keep lid-close action = Do nothing while on AC (Control Panel → Power Options).

**macOS**

```
sudo pmset -c sleep 0 disksleep 0
caffeinate -s -w <daemon_pid>
```

**Linux**

```
# GNOME example — disable automatic suspend on AC
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
# or: systemd-inhibit --what=sleep:idle --who=ahos --why='local soak' --mode=block \
#      .venv/bin/python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

If the laptop sleeps anyway: log UTC start/end in `reports/local_soak_interruptions.jsonl` and do **not** count those hours toward 168h.

---

## 3. Power settings

- Run on AC. Battery-only is allowed only if sleep is still disabled and capacity lasts the planned window (unusual for 168h).
- Do not enable “battery saver” CPU parking that stops the Python process.
- Disk: leave enough free space for SQLite growth + nightly backups under `data/backups/` (gitignored).

---

## 4. Daemon start procedure (local)

From the clone, no root, no systemd required:

```bash
cd /path/to/ahos
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/init_databases.py
.venv/bin/python scripts/validate_imports.py
.venv/bin/python -m pytest tests/ -q
# record those two commands via scripts/record_test_run.py before starting soak

# start (foreground terminal you will leave open, or a user-level process)
.venv/bin/python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

Windows (PowerShell): same with `.venv\Scripts\python.exe`.

Optional user-level restart (not a VPS): Task Scheduler / `launchd` / user systemd — **optional**. The contract is “the process stays up,” not “a server unit exists.”

Entrypoint: `architecture/runtime/__main__.py` `--daemon` (default interval 60s), SIGINT/SIGTERM graceful stop (`:96-104`).

---

## 5. Heartbeat interval

| Signal | Interval | Probe |
|---|---|---|
| Daemon cycle | 60s (`--interval-sec 60`) | `scheduler_runs` |
| Heartbeat write | each successful/attempted cycle | `scheduler_heartbeats` |
| Watchdog probe | every 5 minutes while soak is active | `python -m architecture.scheduling.watchdog --status --max-age-sec 300 --json` |

Watchdog is **local and read-only** (`architecture/scheduling/watchdog.py`). Exit 0=OK, 2=STALE, 3=NO_HEARTBEATS. Off-box alerting is **optional** (M-GAP-012).

---

## 6. Snapshot interval

From the same laptop, while the daemon runs:

| When | Command |
|---|---|
| t=0 (start) | `python scripts/system_state_snapshot.py --probe-providers` |
| every 6h, first 48h | `python scripts/soak_snapshot.py --window-hours <hours since start>` **and** `system_state_snapshot.py` |
| every 12h after that | same |
| nightly | `python scripts/sqlite_backup_restore.py backup` per store into `data/backups/` |

**Automatic mode (recommended):** the daemon writes both snapshot types itself —
start it with
`python -m architecture.runtime --daemon --observation-cycle --snapshot-interval-hours 6 [--snapshot-probe-providers]`
and the first snapshot lands at t=0, then every 6h, under `reports/`
(`soak_snapshot_<utc>.json` + `system_state_snapshot_<utc>.json`, never
overwritten). A snapshot-cycle failure is logged and never stops the daemon;
a gap in the series must still be explained (sleep, travel, kill).

Commit snapshots under `reports/` (never overwrite). A gap in the snapshot series must be explained (sleep, travel, kill).

---

## 7. Failure injection plan (on the laptop)

Do these **during** the 168h window. Record UTC + snapshot after each.

| When | Action | Expected local evidence |
|---|---|---|
| Day 1, hour ≥ 2 | Kill daemon (`taskkill /F` / `kill -9`), restart §4 | `SKIPPED_LOCKED` then takeover; heartbeat downtime; watchdog STALE→OK |
| Day 3 | Graceful stop (Ctrl+C / SIGTERM), restart | clean shutdown; next cycle SUCCESS |
| Day 5 | Pause 20 min (stop process, wait, start) | `downtime_detected_sec ≈ 1200`; no fabricated backfill |
| Any day | `python scripts/reliability_challenge.py` | 7/7 still PASS (injected, not a substitute for §7 events) |

---

## 8. Recovery verification

After each injection:

1. `python -m architecture.scheduling.watchdog --status --json` → not `NO_HEARTBEATS` once the daemon is back.
2. `python scripts/system_state_snapshot.py` — `integrity_check=ok` on existing stores.
3. `scheduler_runs` accumulate (counts do not reset to a lie).
4. Write one line to `reports/local_soak_recovery_<utc>.json` with command, SHA, watchdog status.

---

## 9. Database integrity checks

- Every snapshot: `PRAGMA integrity_check` via `scripts/system_state_snapshot.py` / `soak_snapshot.py`.
- After restore practice: `python scripts/sqlite_backup_restore.py drill`.
- Fail-closed: missing store = `NO_DATA`, never invented `ok`.

---

## 10. Acceptance (local 168h)

Same numeric bars as the Month-1 protocol §7 (A1–A6, B1–B3, C1–C5, D, E), evaluated **only** from committed laptop snapshots + local SQLite + the interrupt log.

- Sleep hours **do not count**.
- Provider **failure** on a filtered network is compliant C1 (explicit). Provider **success** is a separate gap (M-GAP-007) and does not block soak mechanics.
- Off-box watchdog is **not** an acceptance item.

**LOCAL_PRODUCTION_READY** is allowed only after this window closes with the criteria met. Until then the honest class is at most **LOCAL_SOAK_READY**.
