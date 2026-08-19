# AHOS Phase 19 — PR #8 Final Release Gate

**Date:** 2026-08-19 · **Audit host:** Linux x86_64 (agent sandbox)
**PR:** [#8](https://github.com/mainmovement/ahos/pull/8) · **HEAD SHA:** `72f4e6f24589f55f78f929533d6915865748a15d`

**Daemon started:** NO · **168h soak started:** NO · **Soak evidence created:** NO · **`LOCAL_SOAK_RUNNING` claimed:** NO

---

## VERDICT

# `READY_FOR_WINDOWS_LAPTOP_ACTIVATION`

All nine release gates pass. PR #8 is safe to merge. **It has not been merged** —
merge is the owner's action.

One thing this verdict does **not** assert: that the launchers have been *run*.
See §10.

---

## 1. PR #8 GitHub state

| Field | Value |
|---|---|
| Number / state | **#8 · OPEN** (not draft) |
| Base ← head | `main` ← `arena/01a015c9-ahos` |
| HEAD SHA | `72f4e6f24589f55f78f929533d6915865748a15d` |
| Local HEAD | `72f4e6f…` — **identical**, nothing unpushed |
| Mergeable | **`MERGEABLE`** · mergeStateStatus **`CLEAN`** |
| Changed files | **44** (+6726 / −32) |
| Commits | **13** |
| Contains `72f4e6f` | **YES** — it is the tip commit (index 12) |

### CI / check status

```
gh pr checks 8  ->  "no checks reported on the 'arena/01a015c9-ahos' branch"
statusCheckRollup -> empty
```

**This is not a failing CI — it is the absence of CI.** Verified as a repository
fact, not a transient glitch: `.github/workflows/` does not exist on this branch
**or on `origin/main`**. There is no automated gate on this repo, which is
precisely why the gates in §4–§5 were run locally and their output recorded here.

*Advisory (not a blocker):* the repo has no CI. Every quality gate is currently
manual. Worth adding, but out of Phase 19 scope.

---

## 2. Diff contents — intended changes only

### Phase 18 alone (`ec0d3bf..72f4e6f`) — 7 files

```
 .gitattributes                           |  17 ++
 AHOS_PHASE18_OPERATOR_LAUNCHER_REPORT.md | 160 ++
 AHOS_WINDOWS_DEPLOYMENT_GUIDE.md         |  20 +-
 README.md                                |  12 +-
 start_ahos.bat                           |  52 +-
 start_ahos.ps1                           |  50 +-
 tests/test_phase18_launchers.py          | 135 ++
```

| File of interest | Status |
|---|---|
| `start_ahos.ps1` | modified — canonical command, `local` namespace, DB init, guards |
| `start_ahos.bat` | modified — same semantics in cmd form |
| `install_windows.ps1` | **UNCHANGED** (0 diff lines, whole PR) |
| `.gitattributes` | **new** — pins `*.bat`/`*.ps1` to `eol=crlf` |
| tests | **new** `tests/test_phase18_launchers.py`, 19 regressions |
| documentation | `README.md`, `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` stale warnings removed |

### Whole PR (`8dc77f8..72f4e6f`) — 44 files

13 commits spanning Phases 11–18: the prediction ledger + calibration harness,
the provider probe, operator documentation, evidence artifacts, and the Phase 18
launcher hardening. No unrelated or stray file. The two large `01a0….md` files
at repo root are **pre-existing on `main`** (last touched by merge `8dc77f8`) and
are **not** part of this diff.

---

## 3. Untouched-path confirmation

| Path | Phase 18 | Whole PR #8 |
|---|---|---|
| `discovery/` (Lane-A) | UNTOUCHED | **UNTOUCHED** |
| `paper_trading/` (Lane-A) | UNTOUCHED | **UNTOUCHED** |
| `database/` | UNTOUCHED | **UNTOUCHED** |
| `architecture/` | UNTOUCHED | **7 files changed — see below** |
| Lane-A frozen set | UNTOUCHED | **UNTOUCHED** |

### Honest note on `architecture/`

The "do not touch `architecture/`" rule was the **Phase 18** scope grant, and
Phase 18 honoured it exactly. The wider PR necessarily contains the Phase 11
learning-loop feature, which was authorised at the time:

```
A  architecture/learning/__init__.py        (new)
A  architecture/learning/calibration.py     (new)
A  architecture/learning/score_ledger.py    (new)
A  architecture/providers/probe.py          (new)
M  architecture/pipeline/orchestrator.py    (+27/-…, additive)
M  architecture/runtime/__main__.py         (+61,  additive CLI flags)
M  architecture/runtime/observation_loop.py (+29,  additive)
```

Four are **new files**. The three modifications are additive: the orchestrator
gains an **explicitly injected, never-defaulted** `score_ledger` (so a stray test
construction cannot write into the operator's real prediction store), the runtime
gains CLI flags, and the observation loop gains hooks. **The scoring engine is
not among them** — no weight or threshold was altered.

### Lane-A frozen-file cross-check

Every one of the PR's 44 changed paths was intersected against the 36 entries in
`config/lane_a_freeze.sha256`:

```
CHANGED ∩ FROZEN = EMPTY   -> no frozen file modified
```

---

## 4. Mandated gates

| # | Command | Result |
|---|---|---|
| 1 | `python scripts/freeze_lane_a.py` | **PASS** — Lane-A integrity OK, **36 files pinned**, exit 0 |
| 2 | `python scripts/validate_imports.py` | **PASS** — wiring clean, 2144 source files scanned |
| 3 | `python -m pytest tests/ -q` | **1159 passed / 0 failed** in 150s |

No test was skipped, weakened, or deleted to reach green.

---

## 5. Execution-surface audit

Repo-wide scan of `architecture/ discovery/ paper_trading/ telegram_ai/ scripts/ database/`:

| Pattern | Hits |
|---|---|
| `import ccxt` / `from ccxt` | 0 / 0 |
| `import web3` / `from web3` | 0 / 0 |
| `.place_order(` / `.create_order(` / `.submit_order(` | 0 / 0 / 0 |
| `sign_transaction` / `send_raw_transaction` / `eth_sendTransaction` | 0 / 0 / 0 |
| `PRIVATE_KEY` | 0 |
| `private_key` | **1 — inspected, benign** |

The single `private_key` hit is `architecture/security/hygiene.py:45`, inside the
log sanitizer's redaction deny-list:

```python
sensitive_keys = {"token", "key", "api_key", "secret", "private_key", ...}
```

That is a control that **scrubs** such values from logs — the opposite of a
capability. `requirements.txt` declares no exchange, wallet, or chain-signing
library.

### Result: **`NO_EXECUTION_SURFACE`**

---

## 6. Official Windows soak command

Required:

```
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

| Location | Line | Content |
|---|---|---|
| `start_ahos.ps1` | 66 | `& $VenvPython -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local` |
| `start_ahos.bat` | 53 | `"%VENV_PY%" -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local` |

The mandated command appears **verbatim** as a prefix in both. `--evidence-source local`
is an addition, not a deviation: it is the highest-precedence input to
`resolve_source`, so the namespace holds even if the environment variable is lost.

### `AHOS_EVIDENCE_SOURCE=local` established

| Location | Line | Content |
|---|---|---|
| `start_ahos.ps1` | 50 | `$env:AHOS_EVIDENCE_SOURCE = "local"` |
| `start_ahos.bat` | 42 | `set "AHOS_EVIDENCE_SOURCE=local"` |

Verified live against the code:

```
resolve_source("local")        -> local
resolve_source(None) + env     -> local
CALIBRATION_ELIGIBLE_SOURCES   -> frozenset({'local'})
```

Both paths reach the only calibration-eligible namespace. Every flag the
launchers pass was confirmed present in the runtime's own `--help`.

### Supporting launcher properties

- **DB init:** both call `scripts/init_databases.py --with-guards` before start
  (ps1:42, bat:34). Confirmed necessary — `install_windows.ps1` contains **no**
  `init_databases` step.
- **Line endings:** `start_ahos.bat` CRLF=54 / bare_LF=0; `start_ahos.ps1`
  CRLF=67 / bare_LF=0. `git check-attr` reports `eol: crlf` for both, so a
  checkout on **any** platform materialises CRLF.

---

## 7. No stale daemon instruction

Every **live operator document** was checked for a `--daemon` command missing
`--observation-cycle`:

```
AHOS_OPERATOR_QUICKSTART_WINDOWS.md, AHOS_SOAK_OPERATOR_START.md,
AHOS_LOCAL_ACTIVATION_CHECKLIST.md, AHOS_WINDOWS_OPERATOR_RUNBOOK.md,
AHOS_MONTH1_SOAK_PROTOCOL.md, AHOS_LAPTOP_READINESS_CHECKLIST.md,
README.md, INSTALLATION.md, AHOS_WINDOWS_DEPLOYMENT_GUIDE.md
-> no stale instruction found
```

One near-miss, examined and cleared: `AHOS_LOCAL_SOAK_PROTOCOL.md:91` reads
*"Entrypoint: `architecture/runtime/__main__.py` `--daemon` (default interval
60s), SIGINT/SIGTERM graceful stop"*. That is descriptive prose about the module,
not a command to run; the document's two actual commands (`:55`, `:84`) both
carry `--observation-cycle`.

Remaining bare-`--daemon` matches elsewhere are **dated historical reports**
(`reports/phase21_*`, `phase24_*`, `AHOS_FINAL_STATUS.md`, `AHOS_ISSUE_REGISTER.md`),
the `__main__.py` docstring, and test deny-lists. Rewriting dated records would
falsify history, so they stand.

---

## 8. No false readiness claims

Scanned all 13 documents changed by PR #8:

| Claim | Found as an assertion |
|---|---|
| `LOCAL_SOAK_RUNNING` | **NO** — 8 hits, every one a negation or a precondition list ("**claimed:** NO", "NOT PERFORMED", "conditions unmet") |
| 168h completed / soak complete | **NO** — zero hits |
| calibrated | **NO** — 3 hits, all in "**It does not mean** … the scoring is calibrated" |
| `PRODUCTION_READY` / `LOCAL_PRODUCTION_READY` | **NO** — zero hits |
| production ready | **NO** — 1 hit, in the gap register **banning** the phrase |

Corroborated by the artifacts themselves:

- `AHOS_PHASE_PROGRESS_SNAPSHOT.md:4` — classification `READY_FOR_REAL_LOCAL_DATA` (unchanged)
- `reports/calibration_*.json` — `total_predictions = 0`
- `reports/soak/system_state_t0.json` — `t0_valid = false`

The documentation and the evidence agree, and both say the same thing: nothing
has run yet.

---

## 9. Gate summary

| # | Gate | Result |
|---|---|---|
| 1 | PR #8 state queried, contains `72f4e6f` | **PASS** |
| 2 | Diff = intended launcher/operator changes only | **PASS** |
| 3 | `discovery/`, `paper_trading/`, `database/`, Lane-A untouched | **PASS** |
| 4 | `freeze_lane_a.py` — 36 pinned | **PASS** |
| 5 | `validate_imports.py` | **PASS** |
| 6 | `pytest tests/ -q` — 1159 passed / 0 failed | **PASS** |
| 7 | Execution-surface audit | **`NO_EXECUTION_SURFACE`** |
| 8 | Canonical command + `AHOS_EVIDENCE_SOURCE=local` | **PASS** |
| 9 | No stale command, no false readiness claim | **PASS** |

**Merge status: NOT MERGED.** All gates pass, so the merge is unblocked, but
performing it is the owner's decision.

---

## 10. What this gate does *not* prove

- **The launchers have never been executed.** This is a Linux sandbox with no
  PowerShell or `cmd.exe`. Proven: correct command text, every flag accepted by
  the live CLI, namespace resolving to `local`, correct CRLF on checkout.
  Unproven until the operator runs them: actual Windows runtime behaviour.
- **No provider egress exists here**, so the probe cannot return `SUCCESS`
  (M-GAP-007).
- **Merging changes no operational fact.** After merge the classification is
  still `READY_FOR_REAL_LOCAL_DATA`; the 168-hour window begins only on the
  Windows laptop, through the gated procedure in
  `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`.

### Blockers to activation (unchanged, all USER-ACTION-REQUIRED)

| # | Blocker | Gap |
|---|---|---|
| 1 | Windows laptop required — baseline exits `2` on non-Windows | — |
| 2 | No provider egress (2 × `TLS_ERROR`, 0 × `SUCCESS`) | M-GAP-007 |
| 3 | Daemon not running (`NO_HEARTBEATS`) | M-GAP-003 |
| 4 | 7 nightly backups + fresh-host restore | M-GAP-010 |
| 5 | Telegram token rotation | M-GAP-009 |

These block the **soak**, not the **merge**. Each requires the physical laptop.

---

**Classification: `READY_FOR_WINDOWS_LAPTOP_ACTIVATION`.**
PR #8 is safe to merge. Daemon not started. No soak evidence. Nothing calibrated.
