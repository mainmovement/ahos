# AHOS — Pre-Soak Protocol (controlled short soak)

**Status:** PROTOCOL — not an executed soak  
**Not:** 72h evidence accrual · not 168h soak  
**Purpose:** Prove scheduler/DB/restart stability before asking the operator for ≥72h uptime.

---

## Duration

**Minimum:** 2 hours continuous daemon  
**Recommended:** 4–6 hours on the Windows operator laptop  

Record as `PRE_SOAK`, never as full soak.

---

## Start (PowerShell)

```powershell
cd C:\path\to\ahos
.\.venv\Scripts\Activate.ps1
$env:AHOS_EVIDENCE_SOURCE = "local"
$env:AHOS_NARRATIVE_FETCH = "1"

# Optional once:
python scripts\backfill_lane_a_from_production.py
python scripts\prediction_lifecycle_status.py --json-out reports\pre_soak_t0_lifecycle.json

python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local --snapshot-interval-hours 1
```

Keep laptop awake (OS power settings).

---

## Checks during PRE_SOAK

Every ~30–60 minutes:

```powershell
python scripts\prediction_lifecycle_status.py
python -m architecture.scheduling.watchdog --status
```

Monitor:

| Signal | Healthy |
|--------|---------|
| Cycles | increasing |
| discovery_observations | non-decreasing |
| observation_state | stable/growing |
| outcome_labels | still 0 if <72h since first_seen (expected) |
| provider failures | logged, not silent |
| DB integrity | no crash loops |
| Restart | stop/start once mid-window; continues |

Mid-window restart drill:

```powershell
# Ctrl+C daemon, then:
python scripts\sqlite_backup_restore.py drill
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
```

---

## End artifact

```powershell
python scripts\prediction_lifecycle_status.py --json-out reports\pre_soak_end_lifecycle.json
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill --json-out reports\operator_validation_report.json
```

Write a short note in `reports/pre_soak_notes_<UTC>.md`:

* start/end UTC
* interruptions
* FAIL symptoms
* PASS/FAIL decision for proceeding to 72h

---

## PASS criteria (PRE_SOAK)

* Daemon ran ≥2h without process crash
* At least one successful discovery/score cycle with persisted evidence
* Restart drill completed; DBs readable
* Lane-A freeze still OK
* No fabricated outcomes

## FAIL → do not start 72h

* Repeated TLS/total provider failure with zero observations
* DB corruption / integrity_check fail
* Lane-A freeze drift
* Scheduler stuck with zero heartbeats and no recovery

---

## After PRE_SOAK PASS

Proceed to **72h evidence accrual** (OWNER):

```powershell
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local --snapshot-interval-hours 6
```

After ≥72h from earliest `first_seen_ts` of tracked tokens:

```powershell
python scripts\calibration_report.py
```

Expect `joined_pairs > 0` only when RESOLVED labels exist. Keep `INSUFFICIENT_DATA` until guards met.
