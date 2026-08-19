# AHOS Laptop Operation Report

**Phase 13 — Local Laptop Real Operation Gate**
**Report status:** `AWAITING_LAPTOP_EXECUTION`
**Last agent-side verification:** 2026-08-18 · commit `50d047d` · branch `arena/01a015c9-ahos`

---

## 0. Why this report is not filled in yet

Phase 13 requires execution **on the Windows laptop**. Every field below is a
*measurement*, and the measurements were attempted in the agent sandbox and
**refused by the tooling itself**:

```
$ python scripts/record_local_laptop_baseline.py
  official_168h_eligible : false
  failed_checks          : ["windows_host"]
  EXIT 2
  STOP: baseline is not eligible; do not start the official 168h clock.
```

Task 4 of the directive says the daemon starts **ONLY after baseline PASS**.
The baseline did not pass, so the daemon was **not** started, no t0 was
certified, and no prediction was fabricated. Filling this report with sandbox
values would produce exactly the "deployment theater" the program forbids.

The tables below are the template the operator completes on the laptop; each
one names the command that produces the value, so nothing is typed from memory.

---

## 1. Hardware environment

| Field | Value | Source command |
|---|---|---|
| Machine model | *(to record)* | `wmic computersystem get model,manufacturer` |
| CPU | *(to record)* | `wmic cpu get name,numberofcores` |
| RAM (GB) | *(to record)* | `wmic computersystem get totalphysicalmemory` |
| Free disk (GB) | *(to record; ≥ 2 GB required)* | `Get-PSDrive C \| Select-Object Used,Free` |
| Power source | *(must be **AC**)* | `powercfg /batteryreport` |
| Sleep on AC | *(must be **disabled**)* | `powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE` |

## 2. Operating system

| Field | Value | Source |
|---|---|---|
| OS name / edition | *(to record)* | `systeminfo \| findstr /B /C:"OS Name"` |
| OS version / build | *(to record)* | `systeminfo \| findstr /B /C:"OS Version"` |
| Architecture | *(must be 64-bit)* | `wmic os get osarchitecture` |
| Automatic time sync | *(must be **ON** — M-GAP-006)* | `w32tm /query /status` |

Recorded automatically into `reports/local_laptop_baseline.json` under `os`.

## 3. Python version

| Field | Value | Source |
|---|---|---|
| Python version | *(must be ≥ 3.11)* | `python --version` |
| Interpreter path | *(must be the venv)* | `.\.venv\Scripts\python.exe` |
| 64-bit interpreter | *(must be true)* | `python -c "import sys; print(sys.maxsize > 2**32)"` |

## 4. Dependency hash

| Field | Value | Source |
|---|---|---|
| `requirements.txt` sha256 | *(to record)* | `reports/local_laptop_baseline.json#dependency_hash` |
| `lane_a_freeze.sha256` sha256 | *(to record)* | same artifact |
| Import gate | *(must be PASS)* | `python scripts/validate_imports.py` |

**Agent-side reference values at commit `50d047d`** (these must match on the
laptop unless `requirements.txt` changed):

```
requirements_txt_sha256 : af3e7716e08f32da2d9a27f99a66cba6651792a22ec635fa1473a4d23e6fb7e5
lane_a_freeze_sha256    : 2f5d67dd9176bd7d45a11a5f17b63a9d91cf80f43b7ac8fd7cf505484446312d
```

> The operator should treat the laptop's own artifact as authoritative; a
> mismatch means the dependency set or the frozen surface differs and must be
> investigated **before** the soak, not during it.

## 5. Database integrity

| Store | Required | Source |
|---|---|---|
| `e01_discovery.sqlite` | `integrity_check = ok` | `scripts/init_databases.py --with-guards` |
| `paper_trading.sqlite` | `integrity_check = ok` | same |
| `ahos_local.sqlite` | `integrity_check = ok` | same |
| `ahos_knowledge.sqlite` | `integrity_check = ok` | same |
| `opportunity_score_ledger` guards | both `ahos_guard_*` triggers present | `reports/local_activation_report.json#prediction_ledger` |

**Agent-side verification (Linux sandbox, commit `50d047d`): all four `ok`,
both append-only guards present.** The laptop must re-verify on its own stores.

## 6. Lane-A freeze status

| Field | Agent-side value | Laptop value |
|---|---|---|
| Files pinned | **36** | *(to record)* |
| Drift | **none** | *(must be none)* |
| Missing | **none** | *(must be none)* |
| Verdict | **`Lane-A integrity OK (36 files pinned)`** | *(to record)* |

Command: `python scripts/freeze_lane_a.py`

## 7. Evidence source

| Field | Agent sandbox | Required on laptop |
|---|---|---|
| `AHOS_EVIDENCE_SOURCE` | *(unset)* | **`local`** |
| Resolved namespace | **`sandbox`** | **`local`** |
| Calibration-eligible | **no** | **yes** |
| Ledger rows | **0** | *(to record, > 0 after first cycles)* |

```powershell
$env:AHOS_EVIDENCE_SOURCE = "local"
```

The daemon prints its namespace at startup. If the line reads
`sandbox  (NOT calibration-eligible)`, the variable did not reach the process
and **the resulting predictions will never enter calibration**.

---

## 8. Provider probe (Task 3)

Command: `python -m architecture.runtime --probe-providers`

### Agent sandbox result — 2026-08-18T19:31:07Z (recorded, not bypassed)

| Provider | Status | Tokens | Detail |
|---|---|---|---|
| dexscreener | **TLS_ERROR** | 0 | `URLError: TLS/SSL connection has been closed (EOF)` |
| geckoterminal | **TLS_ERROR** | 0 | `URLError: TLS/SSL connection has been closed (EOF)` |
| coingecko | UNSUPPORTED | 0 | no discovery capability (market data only) |
| chain_explorer | UNSUPPORTED | 0 | no discovery capability (onchain only) |
| goplus | UNSUPPORTED | 0 | no discovery capability (security only) |
| rugcheck | UNSUPPORTED | 0 | no discovery capability (security only) |

```
counts: {'UNSUPPORTED': 4, 'TLS_ERROR': 2}
SUCCESS: 0    ERROR: 0    UNKNOWN: 0
any_success = false  →  M-GAP-007 remains OPEN
```

Artifact: `reports/provider_probe_20260818T193107Z.json`

The TLS failure was verified as genuine sandbox egress blocking with a raw
`urllib` call independent of AHOS. **It was not worked around**; a repository
test asserts no `verify=False` / `CERT_NONE` / unverified-context bypass exists.

### Laptop result — *(to record)*

| Status | Count | Meaning |
|---|---|---|
| `SUCCESS` | *(≥ 1 required to close M-GAP-007)* | answered **and** returned ≥ 1 token |
| `ERROR` | *(to record)* | reached but failed (5xx, bad payload, DOWN) |
| `UNKNOWN` | *(to record)* | unclassifiable — never means "probably fine" |
| others | *(to record)* | `EMPTY` / `TLS_ERROR` / `TIMEOUT` / `RATE_LIMIT` / `AUTH_REQUIRED` / `UNSUPPORTED` |

Commit the artifact **whatever the outcome**. Exit `0` = a live success exists;
exit `3` = ran fine, nothing live.

---

## 9. Baseline execution (Task 2)

Command: `python scripts/record_local_laptop_baseline.py`

| Check | Agent sandbox | Required |
|---|---|---|
| `windows_host` | **false** ← blocker | true |
| `python_3_11_or_newer` | true | true |
| `working_tree_clean_before_artifact` | true | true |
| `lane_a_intact` | true | true |
| `all_databases_integrity_ok` | true | true |
| `execution_flags_disabled` | true | true |
| **`official_168h_eligible`** | **false** | **true** |

Artifact: `reports/local_laptop_baseline.json` · exit code `2` in the sandbox.

## 10. Daemon start (Task 4) — **NOT PERFORMED**

Gated on baseline PASS, which did not occur. On the laptop:

```powershell
$env:AHOS_EVIDENCE_SOURCE = "local"
.\.venv\Scripts\python.exe -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

## 11. t0 snapshot (Task 5)

Command: `python scripts/soak_t0_snapshot.py` → `reports/soak/system_state_t0.json`

Contains timestamp, git SHA, environment fingerprint, watchdog status,
heartbeat status and provider status — plus `t0_valid` and, when false, the
explicit reasons.

### Agent sandbox attempt — `t0_valid: false`

```
host is Linux, not Windows — sandbox hours never count
laptop baseline is not eligible (failed: ['windows_host'])
watchdog status is NO_HEARTBEATS — daemon must be running before t0 is meaningful
evidence namespace is 'sandbox' — set AHOS_EVIDENCE_SOURCE=local
```

`t0_valid` becomes true only when all four hold; verified by test.

## 12. First local prediction (Task 6) — **NOT ACHIEVABLE HERE**

Requires `source=local` **and** a live provider. On this host: ledger rows `0`,
census `{}`, providers `0 SUCCESS`. No prediction was invented.

On the laptop, after the daemon has run a few cycles:

```powershell
.\.venv\Scripts\python.exe -c "from architecture.learning.score_ledger import ScoreLedger; l=ScoreLedger(); print(l.source_census(), l.count(source='local'))"
```

Required: `{'local': N}` with `N > 0`.

---

## 13. Gate summary

| Task | Status | Blocker |
|---|---|---|
| 1 Operation report | **TEMPLATE READY** | needs laptop measurements |
| 2 Baseline `official_168h_eligible=true` | **BLOCKED** | `windows_host=false` |
| 3 Provider probe | **EXECUTED (honest failure)** | 0 SUCCESS — egress blocked |
| 4 Daemon start | **NOT PERFORMED** | correctly gated on Task 2 |
| 5 t0 snapshot | **TOOLING READY** (`t0_valid=false` here) | Tasks 2+4 |
| 6 First local prediction | **NOT ACHIEVABLE** | needs `local` + live provider |
| 7 Snapshot → `LOCAL_SOAK_RUNNING` | **NOT PERFORMED** | all four conditions unmet |

**Current classification remains `READY_FOR_REAL_LOCAL_DATA`.** It does not
advance to `LOCAL_SOAK_RUNNING`, because none of the four required conditions
(Windows laptop, `source=local`, watchdog OK, valid t0) can be satisfied in
this environment — and asserting otherwise would be a fabricated milestone.

## 14. Standing gates at commit `50d047d`

| Gate | State |
|---|---|
| Test suite | **1096 passed / 0 failed** |
| Lane-A freeze | **36 files pinned, unchanged** |
| Import + architecture gate | **PASS** (146 modules) |
| Execution surface | **NO_EXECUTION_SURFACE** |
| TLS verification | never bypassed (scan-enforced) |
| Calibration | `INSUFFICIENT_DATA`, 0 eligible pairs — no fake calibration |
