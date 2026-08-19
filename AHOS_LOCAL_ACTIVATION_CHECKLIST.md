# AHOS Local Activation Checklist (Windows Laptop)

**Purpose:** bring AHOS from verified infrastructure into **real local operation**.
Every box must be ticked on the laptop itself before the official 168-hour clock starts.

**Scope:** observation-only. No VPS, no trading, no wallet, no execution surface.

**Related documents**
- `AHOS_SOAK_OPERATOR_START.md` — the command-by-command activation path
- `AHOS_LAPTOP_READINESS_CHECKLIST.md` — hardware/power detail
- `AHOS_LOCAL_SOAK_PROTOCOL.md` — the 168-hour contract and recovery drills

> **Arena/sandbox hours never count.** The agent environment has no market-data
> egress (verified: `TLS_ERROR` on both discovery providers). Only this laptop
> can produce real operational evidence.

---

## 1. Python environment

- [ ] Python **3.11+** on PATH — `python --version`
- [ ] 64-bit interpreter — `python -c "import sys; print(sys.maxsize > 2**32)"` → `True`
- [ ] Virtual environment created in the clone — `python -m venv .venv`
- [ ] venv interpreter used for **every** command below (`.\.venv\Scripts\python.exe`)

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## 2. Dependency validation

- [ ] `requirements.txt` installed into the venv
- [ ] Imports verified (this is the real gate, not `pip list`)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\validate_imports.py
```

Expect `VALIDATION PASSED`. It also re-checks the Lane-A freeze and scans for secrets.

- [ ] Lane-A freeze intact — `python scripts\freeze_lane_a.py` → `Lane-A integrity OK (36 files pinned)`
- [ ] Full suite green — `python -m pytest tests\ -q`

**If any gate is red, stop.** Evidence gathered on a red gate is not evidence.

## 3. Database initialization

- [ ] All four SQLite stores created and healthy

```powershell
.\.venv\Scripts\python.exe scripts\init_databases.py --with-guards
```

Expect `RESULT: ALL STORES HEALTHY`. This creates:

| Store | Holds |
|---|---|
| `e01_discovery.sqlite` | observations, feature vectors, **outcome labels** |
| `ahos_local.sqlite` | scheduler, metrics, **prediction ledger** |
| `paper_trading.sqlite` | paper ledger (no real funds, ever) |
| `ahos_knowledge.sqlite` | knowledge claims |

- [ ] `opportunity_score_ledger` exists with its two append-only guards

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3;from config.paths import get_local_db_path;c=sqlite3.connect(get_local_db_path());print([r[0] for r in c.execute(\"select name from sqlite_master where type='trigger' and name like '%score_ledger%'\")])"
```

Expect both `ahos_guard_no_update_...` and `ahos_guard_no_delete_...`.

## 4. Sleep prevention (mandatory)

A sleeping laptop silently ends the soak window. On **AC power**:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 15
```

- [ ] Sleep disabled on AC
- [ ] Hibernate disabled on AC
- [ ] **Lid close = Do nothing** (Control Panel → Power Options → *Choose what closing the lid does*)
- [ ] Verify: `powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE` shows AC index `0x00000000`
- [ ] Windows Update auto-restart deferred for the window (an unplanned reboot is a soak gap)

If the machine sleeps anyway, log the UTC gap in `reports\local_soak_interruptions.jsonl`
and **do not count those hours**. An unexplained gap invalidates the window.

## 5. AC power requirement

- [ ] Charger physically connected and charging
- [ ] Battery ≥ 50% at t0 (headroom for a brief power cut)
- [ ] Confirm AC: `powercfg /batteryreport /output battery.html` → *AC* at the latest entry
- [ ] OS **automatic time sync ON** — drift detection assumes a sane host clock (M-GAP-006)

## 6. Disk space check

- [ ] ≥ **2 GB** free on the drive holding the clone

```powershell
Get-PSDrive C | Select-Object Used,Free
```

Rough budget for 168h: SQLite stores + snapshots + 7 nightly backups. Backups are
full copies of all four stores each night — size them at `7 × (current data\ size)`.

```powershell
"{0:N1} MB" -f ((Get-ChildItem data -Recurse -File | Measure-Object Length -Sum).Sum/1MB)
```

## 7. Backup directory

- [ ] `data\backups\` exists (gitignored)

```powershell
mkdir data\backups -Force
```

- [ ] One nightly backup rehearsed **before** t0, so the command is known-good:

```powershell
.\.venv\Scripts\python.exe scripts\sqlite_backup_restore.py nightly
```

Expect `night verdict : PASS` and `distinct days : 1/7`.

> The series ledger (`reports\nightly_backup_series.json`) counts **distinct UTC
> dates**, not invocations — running it repeatedly in one evening still reads `1/7`.
> `series_complete` requires seven real days. This is M-GAP-010's residual and it
> cannot be shortcut.

## 8. Evidence source = local  ← the step that makes data real

- [ ] `AHOS_EVIDENCE_SOURCE=local` set in the daemon's shell

```powershell
$env:AHOS_EVIDENCE_SOURCE = "local"
```

**Why this is mandatory.** Every prediction is stamped with an evidence namespace,
and **only `local` is calibration-eligible**. The default is `sandbox`, deliberately:
producing real evidence is opt-in, so no stray script, test run, or agent session can
quietly become the data your calibration is later computed from.

- [ ] Daemon startup line confirms it:
  `Prediction evidence namespace: local`
  (if it says `sandbox  (NOT calibration-eligible)`, the variable did not reach the process)

- [ ] Verify after the first cycles:

```powershell
.\.venv\Scripts\python.exe -c "from architecture.learning.score_ledger import ScoreLedger; print(ScoreLedger().source_census())"
```

Expect `{'local': N}` with N > 0. Any `test`/`sandbox`/`synthetic` rows are excluded
from calibration and named in the report's `exclusion_reasons`.

## 9. Provider connectivity (the M-GAP-007 moment)

- [ ] Probe run and artifact committed — **whatever the result**

```powershell
.\.venv\Scripts\python.exe -m architecture.runtime --probe-providers
```

| Exit | Meaning |
|---|---|
| `0` | ≥ 1 provider `SUCCESS` — this laptop reaches market data, **M-GAP-007 closes** |
| `3` | ran fine, nothing live — an honest failure record, still commit it |

Statuses are disjoint; a failure is never rounded up to success:
`SUCCESS` · `EMPTY` · `TLS_ERROR` · `TIMEOUT` · `RATE_LIMIT` · `AUTH_REQUIRED` ·
`UNSUPPORTED` · `ERROR` · `UNKNOWN`

Only `SUCCESS` (answered **and** returned ≥ 1 token) counts. Do **not** disable TLS
verification to force a green result — a bypassed error is a fabricated success.

If everything fails here, AHOS still runs correctly: it will record
`provider_failure_events` and honest UNKNOWNs. But **no real predictions accumulate**,
so calibration stays at zero pairs. Fix networking before starting the 168h window.

## 10. Activation evidence package

- [ ] Generate the machine-readable activation record

```powershell
.\.venv\Scripts\python.exe scripts\local_activation_report.py
```

Writes `reports\local_activation_report.json` with git SHA, environment fingerprint,
database status, provider status, runtime status and the evidence source.

- [ ] `official_168h_eligible` confirmed by the baseline recorder

```powershell
.\.venv\Scripts\python.exe scripts\record_local_laptop_baseline.py
```

Exits `2` when ineligible. Proceed only on `"official_168h_eligible": true`.

---

## Final go/no-go

| Gate | Required |
|---|---|
| Python 3.11+, venv, dependencies | ✅ |
| `validate_imports` + `freeze_lane_a` + `pytest` | all green |
| Four stores healthy, ledger guards present | ✅ |
| Sleep/hibernate off, lid = do nothing, AC connected | ✅ |
| ≥ 2 GB free, `data\backups\` created, one nightly rehearsed | ✅ |
| `AHOS_EVIDENCE_SOURCE=local` confirmed in the daemon log | ✅ |
| Provider probe artifact committed | ✅ (either outcome) |
| `official_168h_eligible = true` | ✅ |

All ticked → start at `AHOS_SOAK_OPERATOR_START.md` §7 and write the t0 snapshot.

## What this checklist does not claim

Completing it does **not** mean the soak passed, the providers work, the scoring is
calibrated, or the system is production-ready. It means AHOS is correctly installed
and honestly instrumented to **begin** collecting real evidence.
