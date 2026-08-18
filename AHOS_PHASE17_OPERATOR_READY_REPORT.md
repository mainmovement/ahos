# AHOS Phase 17 — Operator Ready Report

**Type:** documentation audit · **Date:** 2026-08-18
**Branch:** `arena/01a015c9-ahos` · **Audit host:** Linux x86_64 (agent sandbox)
**Daemon started:** NO · **Soak evidence created:** NO · **`LOCAL_SOAK_RUNNING` claimed:** NO
**Source files changed:** NONE (documentation only)

---

## 1. The canonical start command

```powershell
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

### Why `--observation-cycle` is not optional

Verified in `architecture/runtime/__main__.py`: the flag gates whether the
`OBSERVATION_CYCLE` task is registered at all.

```python
if args.observation_cycle:
    cycle_tasks.append(ScheduleTask(
        task_id="OBSERVATION_CYCLE", ...
        action_fn=_execute_observation_cycle, ...))
```

Without it the daemon runs the scoring pipeline **only**. The E-01 observation
poller never polls and the frozen Lane-A outcome labeler never runs, so:

- predictions accumulate against **zero** outcome labels,
- the calibration join can never produce a pair,
- `calibration_status` stays `INSUFFICIENT_DATA` **forever**, regardless of uptime.

That is precisely M-GAP-014, closed in Phase 11. A soak run without this flag
would burn 168 real hours and produce no learnable evidence.

---

## 2. Audit results — every `--daemon` occurrence

`git grep` across all tracked files found **57 occurrences in 27 files**. Each
was classified as *instruction* (tells the operator to run something) or
*record* (describes something already executed).

### 2.1 Soak-path operator documents — already correct (7/7)

| Document | Status |
|---|---|
| `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` | ✅ correct |
| `AHOS_SOAK_OPERATOR_START.md` | ✅ correct (both variants) |
| `AHOS_LAPTOP_OPERATION_REPORT.md` | ✅ correct |
| `AHOS_LAPTOP_READINESS_CHECKLIST.md` | ✅ correct |
| `AHOS_WINDOWS_OPERATOR_RUNBOOK.md` | ✅ correct |
| `AHOS_LOCAL_SOAK_PROTOCOL.md` | ✅ correct |
| `AHOS_MONTH1_SOAK_PROTOCOL.md` | ✅ correct |

`AHOS_LOCAL_ACTIVATION_CHECKLIST.md` contains no daemon start command by design
(it is the pre-flight checklist) and correctly requires
`AHOS_EVIDENCE_SOURCE=local`.

### 2.2 General-install documents — **4 corrected this phase**

| Document | Problem | Fix |
|---|---|---|
| `INSTALLATION.md` | step 3 started the daemon without the flag | flag added + explanation of what is lost without it |
| `AHOS_FINAL_STATUS.md` | "How user starts AHOS" (Linux/Mac) lacked the flag | flag added |
| `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` | offered only the one-click launchers | warning box added + **Method C** = the supported soak command |
| `README.md` | pointed at `start_ahos.ps1` and older runbooks | launcher caveat added; soak path now points at the quickstart and t0 gate |

### 2.3 **Finding: the Windows one-click launchers are unsuitable for the soak**

This is the most consequential result of the audit.

```
start_ahos.ps1 : & $VenvPython -m architecture.runtime --daemon --interval-sec 60
start_ahos.bat : ".venv\Scripts\python.exe" -m architecture.runtime --daemon --interval-sec 60
```

Both are **double-click entry points** advertised by `README.md`,
`INSTALLATION.md` and `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md`, and both have two
defects for soak purposes:

1. **no `--observation-cycle`** → no observation polling, no outcome labels;
2. **no `AHOS_EVIDENCE_SOURCE=local`** → any predictions they record are stamped
   `sandbox` and are **not calibration-eligible**.

An operator who reasonably double-clicked `start_ahos.bat` would see a healthy
daemon logging cycles, and would discover only afterwards that the run produced
nothing usable.

**These are executable scripts, not documentation.** This phase forbids source
changes, so they were **not modified**. Instead every document that references
them now carries an explicit warning plus the correct command.

**Recommended follow-up (owner decision, deferred):** align `start_ahos.ps1` and
`start_ahos.bat` with the canonical command, or rename them to make their
demo-only status obvious.

### 2.4 Historical records — deliberately left unchanged

These state what *was executed* on a past date. Editing them would falsify the
record, and none of them instructs the operator:

`AHOS_FINAL_STATUS.md:12` (past-tense verification) ·
`AHOS_ISSUE_REGISTER.md:1098` · `AHOS_PRODUCTION_READINESS_REPORT.md:15`
(already labelled non-evidence by audit v2) · `AHOS_REALITY_AUDIT_v2.md:35`
(describes the entrypoint's existence) · `docs/canonical/KNOWLEDGE_MAP.md:254` ·
`reports/phase21_*.md`, `reports/phase24_*.md` (dated execution reports) ·
the two `01a0…md` session exports.

`deployment/ahos-runtime.service` already uses the full correct command, but is
a **systemd unit** — not part of the Windows laptop path.

### 2.5 Verification sweep

```
imperative instructions lacking --observation-cycle : 0
```

No document tells the operator to run, start, execute, or launch the daemon
without the flag.

---

## 3. Acceptance verification

| Requirement | Result | Evidence |
|---|---|---|
| No source files changed | **PASS** | `git diff --name-only` → 4 `.md` files, zero `.py/.ps1/.bat/.service` |
| Lane-A unchanged | **PASS** | `Lane-A integrity OK (36 files pinned)` |
| Tests pass | **PASS** | **1140 passed / 0 failed** |
| Import + architecture gate | **PASS** | 146 modules, `VALIDATION PASSED` |
| Daemon not started | **PASS** | no process launched |
| No soak evidence created | **PASS** | no artifact written under `reports/soak/` |
| `LOCAL_SOAK_RUNNING` not claimed | **PASS** | classification unchanged |

> **Note on a transient gate failure.** `validate_imports.py` first reported
> `FAIL: build artifact present: __pycache__/`. That was `__pycache__` left by
> my own audit commands, not a code defect — the gate correctly enforces a clean
> checkout. After cleaning, it passed. Recorded here rather than hidden, since a
> gate that failed and then passed should always be explained.

---

## 4. Current state (measured, unchanged by this phase)

```
host              : Linux            (required: Windows)
baseline eligible : false            (windows_host=false)
watchdog          : NO_HEARTBEATS
ledger rows       : 0     census: {}
namespace         : sandbox          (required: local)
t0_valid          : false            soak_status: NOT_STARTED
calibration       : INSUFFICIENT_DATA, 0 eligible pairs
```

**Classification remains `READY_FOR_REAL_LOCAL_DATA`.**

---

## 5. Operator start sequence (authoritative)

```powershell
# 1. verify
python scripts\freeze_lane_a.py
python scripts\validate_imports.py
python -m pytest tests\ -q

# 2. probe providers (commit the artifact either way)
python -m architecture.runtime --probe-providers

# 3. baseline — must report official_168h_eligible=true (else exits 2)
python scripts\record_local_laptop_baseline.py

# 4. start the daemon — BOTH parts matter
$env:AHOS_EVIDENCE_SOURCE = "local"
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle

# 5. second window: watchdog must be OK, then t0 must be valid
python -m architecture.scheduling.watchdog --status --json
python scripts\soak_t0_snapshot.py
```

`t0_valid=true` is hour 0 of 168. Full detail: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`.

---

## 6. Remaining blockers (all USER-ACTION-REQUIRED)

| # | Blocker | Gap |
|---|---|---|
| 1 | Windows laptop required — baseline exits `2` here | — |
| 2 | No provider egress in sandbox (2 × `TLS_ERROR`, 0 × `SUCCESS`) | M-GAP-007 |
| 3 | Daemon not running (`NO_HEARTBEATS`) | M-GAP-003 |
| 4 | Namespace `sandbox`, not `local` | M-GAP-015 control |

### Deferred (needs owner decision, source change required)

Align `start_ahos.ps1` / `start_ahos.bat` with the canonical command, or rename
them to signal demo-only status.

---

**Audit complete. Daemon not started. No soak evidence created. No calibration
claimed. Stopping here as instructed.**
