# AHOS Phase 16 — Pre-Start Audit

**Type:** audit only · **Date:** 2026-08-18
**Audit host:** Linux x86_64 (agent sandbox) · **Branch:** `arena/01a015c9-ahos` @ `7f006ec`
**Daemon started:** NO · **Soak evidence created:** NO · **`LOCAL_SOAK_RUNNING` claimed:** NO
**Source code modified:** NO

---

## 1. PR #6 synchronization readiness

**Verdict: `SYNCHRONIZED_BY_CONTENT — MERGE OPTIONAL, NO CONFLICT RISK`**

| Field | Value |
|---|---|
| Title | Phase 8: reliability evidence and NOT_READY production gate |
| State | **OPEN** |
| Head → Base | `arena/01a01560-ahos` → `main` |
| Head commit | `bb5b270d5699bd51c818412014ee4e5e9f5d89a0` |
| Size | 15 files, +1325 / −14 |
| CI checks | none reported (no `.github/workflows/` — M-GAP-004) |

### Ancestry

`bb5b270` is **not** an ancestor of `main`, and **not** an ancestor of this
branch. So by graph topology PR #6 is genuinely unmerged.

### Content comparison (the question that actually matters)

Every code and test file in PR #6 is **byte-identical** to the copy already in
this branch (verified with `git hash-object` vs `git rev-parse <sha>:<path>`):

| File | Result |
|---|---|
| `scripts/evidence_common.py` | **IDENTICAL** |
| `scripts/record_test_run.py` | **IDENTICAL** |
| `scripts/reliability_challenge.py` | **IDENTICAL** |
| `scripts/system_state_snapshot.py` | **IDENTICAL** |
| `tests/test_reliability_challenge.py` | **IDENTICAL** |
| `tests/test_system_state_snapshot.py` | **IDENTICAL** |
| `AHOS_GAP_REGISTER.md` | DIFFERS — this branch is a superset (16 M-GAP rows vs 12) |

These arrived through the merged PR #7 reconstruction, which is why the working
tree already contains them despite the graph showing PR #6 as unmerged.

### Files unique to PR #6 (absent here)

| File | Assessment |
|---|---|
| `AHOS_BASELINE_STATE_REPORT.md` | historical Phase-8 snapshot; superseded by `AHOS_PHASE_PROGRESS_SNAPSHOT.md` |
| `AHOS_PRODUCTION_GATE_REPORT_V2.md` | verdict **NOT_READY** — consistent with current stance; superseded by the local-laptop gate |
| `AHOS_VPS_MIGRATION_READINESS.md` | **contradicts the no-VPS mandate.** Its own text says *"prepare only — no deploy"* and *"Nothing here was executed on a VPS"*, so it is not a false claim — but the operational target is now explicitly the Windows laptop, and this document describes Debian/systemd hosting. |

### Merge-conflict analysis

```
conflicts vs main            : 0
conflicts vs this branch     : 0
```

### Recommendation (no action taken — audit only)

PR #6 is **not a blocker for the laptop soak**: its executable content is
already present and test-covered here. Three options, for the owner to decide:

1. **Merge as-is** — safe (0 conflicts), adds three historical documents. The
   VPS-readiness file would then sit in a no-VPS repository, which invites the
   exact confusion the program has been eliminating.
2. **Close as superseded** — the code landed via PR #7; the gate verdict
   (`NOT_READY`) is preserved and strengthened by the current local gate.
   **This is the cleanest option given the no-VPS mandate.**
3. Merge after dropping `AHOS_VPS_MIGRATION_READINESS.md`.

**Nothing here blocks Phase 15 execution on the laptop.**

---

## 2. Windows operator path

**Verdict: `VERIFIED — READY FOR OPERATOR EXECUTION`**

Path: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` §0 → §11, then the during-window
section. Gate sequence and enforcement:

| Step | Gate | Enforced by | Behaviour on failure |
|---|---|---|---|
| 5 | `validate_imports` + `freeze_lane_a` + `pytest` | scripts | non-zero exit |
| 6 | provider probe | `architecture/providers/probe.py` | exit `3`, no live success |
| 7 | baseline eligibility | `record_local_laptop_baseline.py` | **exit `2`**, `STOP:` message |
| 8 | evidence namespace | `score_ledger.resolve_source()` | defaults `sandbox`, logged at startup |
| 9 | watchdog | `architecture.scheduling.watchdog` | `NO_HEARTBEATS` |
| 10 | t0 validity | `soak_t0_snapshot.py` | exit `3`, `t0_valid=false` + reasons |

The four `LOCAL_SOAK_RUNNING` conditions (Windows host, eligible baseline,
watchdog `OK`, `AHOS_EVIDENCE_SOURCE=local`) are each independently enforced and
regression-tested (`tests/test_phase13_laptop_operation.py`, one test per
condition).

### Windows-specific mechanics

| Item | Status | Evidence |
|---|---|---|
| `python -m venv` creates `Scripts\` on Windows | **CONFIRMED** | CPython 3.11 docs: *"creates a `bin` (or `Scripts` on Windows) subdirectory"* |
| `Activate.ps1` requires an execution policy | **CONFIRMED** | CPython 3.11 docs recommend `Set-ExecutionPolicy` — present as quickstart §0 |
| Daemon signals valid on Windows | **CONFIRMED** | `__main__.py` registers only `SIGINT`/`SIGTERM`, inside `try/except` |
| Hard-kill recipe is PowerShell | **CONFIRMED** | `Get-Process` / `Stop-Process -Id <PID> -Force` |
| `SIGKILL` in operator path | **NONE** | only in `month1_failure_matrix.py` (test harness, not an operator command) |
| POSIX paths / bash builtins / VPS steps / production claims | **NONE** | scan across all four operator docs |

---

## 3. Quickstart command verification

**Verdict: `ALL COMMANDS RESOLVE`** — 33 commands extracted from the PowerShell
blocks; every executable one verified.

### Scripts referenced (10/10 exist)

`init_databases` · `freeze_lane_a` · `validate_imports` ·
`record_local_laptop_baseline` · `local_activation_report` · `soak_t0_snapshot` ·
`soak_snapshot` · `system_state_snapshot` · `sqlite_backup_restore` ·
`calibration_report`

### Flags verified against live `--help` (14/14)

| Command | Flag | Result |
|---|---|---|
| `init_databases.py` | `--with-guards` | OK |
| `soak_snapshot.py` | `--window-hours` | OK |
| `system_state_snapshot.py` | `--probe-providers` | OK |
| `calibration_report.py` | `--horizon`, `--event-class` | OK |
| `soak_t0_snapshot.py` | `--no-probe`, `--out` | OK |
| `local_activation_report.py` | `--no-probe`, `--out` | OK |
| `record_local_laptop_baseline.py` | `--help` (Phase-14 fix) | OK — prints usage, does **not** overwrite the artifact |
| `architecture.runtime` | `--probe-providers`, `--daemon`, `--interval-sec`, `--observation-cycle`, `--evidence-source` | OK |
| `architecture.scheduling.watchdog` | `--status`, `--json` | OK |
| `sqlite_backup_restore.py` | `nightly`, `drill`, `backup`, `restore` | OK |

### Inline one-liners executed

- version/64-bit check → `3.11.2`, `True`
- ledger census → `{} 0` (empty, correct on this host)

### Not executable in this environment (Windows-only, by design)

`cd C:\path\to\ahos` · `Set-ExecutionPolicy` · `.\.venv\Scripts\Activate.ps1` ·
`Get-Process` / `Stop-Process` — all confirmed correct by CPython documentation
and PowerShell semantics rather than by execution.

### Divergence noted (not an error)

Phase 15 §7 gives `--daemon --interval-sec 60`; the quickstart gives
`--daemon --interval-sec 60 --observation-cycle`. **The quickstart form is the
correct one** — without `--observation-cycle` the E-01 poller and the outcome
labeler never run, so outcome labels are never produced and the calibration join
stays permanently empty (this was M-GAP-014).

---

## 4. Current gate state (measured, read-only)

```
host              : Linux                    (required: Windows)
baseline eligible : false  (windows_host=false)
watchdog          : NO_HEARTBEATS
ledger rows       : 0        census: {}
namespace         : sandbox                  (required: local)
t0_valid          : false    soak_status: NOT_STARTED
```

| `LOCAL_SOAK_RUNNING` condition | Met |
|---|---|
| Windows laptop | **NO** |
| `evidence_source=local` | **NO** |
| watchdog `OK` | **NO** |
| valid t0 snapshot | **NO** |

**Classification remains `READY_FOR_REAL_LOCAL_DATA`.**

---

## 5. Standing gates

| Gate | State |
|---|---|
| Test suite | **1140 passed / 0 failed** |
| Lane-A freeze | **36 files pinned, unchanged** |
| Import + architecture gate | **PASS** (146 modules) |
| Execution surface | **NO_EXECUTION_SURFACE** |
| TLS verification | never bypassed (scan-enforced by test) |
| Calibration | `INSUFFICIENT_DATA`, 0 eligible pairs |
| Working tree | clean; **no source files modified by this audit** |

---

## 6. Findings and blockers

### Findings

1. **PR #6 is content-synchronized.** Its code/tests are byte-identical here;
   only three historical documents are unique to it. Zero merge conflicts.
2. **`AHOS_VPS_MIGRATION_READINESS.md` (PR #6 only) contradicts the no-VPS
   mandate** in target, though not in claim — it explicitly states nothing was
   deployed. Recommend closing PR #6 as superseded, or dropping that file.
3. **Phase 15's daemon command omits `--observation-cycle`.** Following it
   literally would run the scoring pipeline while the observation/labeling half
   stayed idle — predictions with no outcomes, and calibration permanently at
   zero pairs. Use the quickstart form.
4. **No CI exists** (`.github/workflows/` absent) — M-GAP-004, known and
   classified optional for local laptop operation.

### Blockers to Phase 15 (all USER-ACTION-REQUIRED)

| # | Blocker | Gap |
|---|---|---|
| 1 | Not a Windows host — baseline exits `2` | — |
| 2 | No provider egress here (2 × `TLS_ERROR`, 0 × `SUCCESS`) | M-GAP-007 |
| 3 | Daemon not running (`NO_HEARTBEATS`) | M-GAP-003 |
| 4 | Namespace `sandbox`, not `local` | M-GAP-015 control |

### Next action

Execute `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` on the Windows laptop, using
`--observation-cycle` on the daemon. When `soak_t0_snapshot.py` reports
`t0_valid=true`, send that artifact plus `reports/local_laptop_baseline.json`
and the classification can advance to `LOCAL_SOAK_RUNNING` **on evidence**.

---

**Audit complete. Daemon not started. No soak evidence created. No calibration
claimed. Stopping here as instructed.**
