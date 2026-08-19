# AHOS Phase 18 — Operator Launcher Hardening Report

**Date:** 2026-08-18 · **Branch:** `arena/01a015c9-ahos`
**Audit host:** Linux x86_64 (agent sandbox)
**Daemon started:** NO · **Soak evidence created:** NO · **`LOCAL_SOAK_RUNNING` claimed:** NO

---

## 1. What was wrong

`start_ahos.ps1` and `start_ahos.bat` are the **double-click entry points**
advertised by `README.md`, `INSTALLATION.md` and the Windows deployment guide.
Both started the daemon like this:

```
-m architecture.runtime --daemon --interval-sec 60
```

Two defects, both silent:

1. **No `--observation-cycle`.** The flag gates registration of the
   `OBSERVATION_CYCLE` task in `architecture/runtime/__main__.py`. Without it
   the daemon runs the scoring pipeline only — the frozen Lane-A E-01 poller and
   the outcome labeler never run, predictions accumulate against **zero** outcome
   labels, and `calibration_status` stays `INSUFFICIENT_DATA` **forever**,
   regardless of uptime. (M-GAP-014)

2. **No `AHOS_EVIDENCE_SOURCE=local`.** The runtime defaults to `sandbox`, and
   **only `local` rows are calibration-eligible**. Predictions recorded by the
   launchers were therefore excluded from calibration by design. (M-GAP-015)

The failure mode was the dangerous kind: the operator sees a healthy daemon
logging cycles on schedule, and discovers only later that the run produced
nothing usable.

---

## 2. What changed

### `start_ahos.ps1` and `start_ahos.bat`

| Change | Reason |
|---|---|
| Canonical command `--daemon --interval-sec 60 --observation-cycle` | mandated form; enables observation + outcome labeling |
| `AHOS_EVIDENCE_SOURCE=local` exported | predictions become calibration-eligible |
| `--evidence-source local` also passed explicitly | explicit argument outranks the env var, so the namespace is unambiguous even if the variable is lost |
| `scripts/init_databases.py --with-guards` before start | a fresh clone has no stores; the daemon must not be first to touch them. Idempotent |
| Exit-code checks after install and DB init | previously the `.bat` would blindly run a missing interpreter |
| `$ErrorActionPreference = "Stop"` (PS1) | fail fast instead of continuing past an error |
| Startup banner states mode, evidence source, interval | the operator can confirm at a glance |
| Banner points at `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` | starting the daemon is one step, not the whole gated window |
| **CRLF line endings** | `cmd.exe` mis-parses LF-only `.bat` files — a multi-line `if` block or trailing `pause` can break. Both were LF-only |

### `.gitattributes` (new)

Pins `*.bat` and `*.ps1` to `eol=crlf` so a Linux checkout cannot silently
rewrite them to LF, and everything else to `eol=lf`.

### Documentation corrected

| Document | Change |
|---|---|
| `README.md` | removed the now-stale "unusable as soak evidence" caveat; states what the launchers actually do; still routes the 168-hour window through the gated procedure |
| `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` | removed the "do NOT use the one-click launchers" warning; all three methods now documented as equivalent, with the gated-procedure reminder retained |

`AHOS_PHASE17_OPERATOR_READY_REPORT.md` was **left unchanged**: it is a dated
record of what was true at the time, and rewriting it would falsify history.

---

## 3. What was deliberately NOT changed

Per the directive's forbidden list — verified by `git diff --name-only`:

```
architecture/     UNTOUCHED
discovery/        UNTOUCHED   (Lane-A)
paper_trading/    UNTOUCHED   (Lane-A)
database/         UNTOUCHED
```

No scoring change, no schema change, no frozen evidence rewritten.

---

## 4. Verification

| Gate | Command | Result |
|---|---|---|
| 1 | `python scripts/validate_imports.py` | **PASS** — 146 modules, wiring clean |
| 2 | `python scripts/freeze_lane_a.py` | **PASS** — Lane-A integrity OK, **36 files pinned** |
| 3 | `python -m pytest tests/ -q` | **1159 passed / 0 failed** (1140 + 19 new) |
| 4 | execution-surface scan | **NO_EXECUTION_SURFACE** |

### Execution surface detail

Scanning the changed files for `ccxt`, `web3`, `place_order`, `create_order`,
`private_key`, `market_buy`, `market_sell`, `sign_transaction`,
`send_transaction`:

- **launchers: 0 matches**
- three matches in `tests/test_phase18_launchers.py` are the **deny-list inside
  the guard test itself** — a defense, not a capability
- repo-wide real capability: **0**

### Launcher content verification

```
start_ahos.ps1   OK canonical command · OK env var · OK explicit flag · OK db init
start_ahos.bat   OK canonical command · OK env var · OK explicit flag · OK db init
line endings     start_ahos.bat CRLF=54 bare_LF=0 · start_ahos.ps1 CRLF=67 bare_LF=0
```

Every flag the launchers pass was verified against the runtime's own `--help`:
`--daemon`, `--interval-sec`, `--observation-cycle`,
`--evidence-source {local,sandbox,test,synthetic}`. `resolve_source("local")`
returns `local`, and `local` is in `CALIBRATION_ELIGIBLE_SOURCES`.

### New regressions (19 tests)

`tests/test_phase18_launchers.py` pins: canonical command present; **no
`--daemon` invocation line lacking `--observation-cycle`**; `local` namespace
declared both ways; DB init present; CRLF endings; `.gitattributes` pinning; no
execution surface; flags accepted by the live CLI; and that documentation no
longer carries the stale warning **while still requiring the gated procedure**.

---

## 5. Honest scope

The launchers were **not executed** — this is a Linux sandbox with no
PowerShell or `cmd.exe`. What is proven here is that they contain the correct
command, that every flag they pass is accepted by the runtime, that the
namespace resolves to `local`, and that their line endings are correct for
Windows. Their runtime behaviour on Windows remains unverified until the
operator runs them.

Nothing in this phase produces soak evidence. Double-clicking a launcher starts
a correctly-configured daemon; it does **not** start the official 168-hour
window, which still requires baseline eligibility, a provider probe, and a valid
t0 snapshot.

**Classification unchanged: `READY_FOR_REAL_LOCAL_DATA`.**

---

## 6. Remaining blockers (unchanged, all USER-ACTION-REQUIRED)

| # | Blocker | Gap |
|---|---|---|
| 1 | Windows laptop required — baseline exits `2` on non-Windows | — |
| 2 | No provider egress in sandbox (2 × `TLS_ERROR`, 0 × `SUCCESS`) | M-GAP-007 |
| 3 | Daemon not running (`NO_HEARTBEATS`) | M-GAP-003 |
| 4 | 7 nightly backups + fresh-host restore | M-GAP-010 |
| 5 | Telegram token rotation | M-GAP-009 |

---

**Launcher hardening complete. Daemon not started. No soak evidence created.
No calibration claimed.**
