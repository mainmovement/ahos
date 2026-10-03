# AHOS one-click launcher (Mission 11)

The owner double-clicks one desktop icon and the whole observation stack comes
up — **without Docker**. This document is the operator-facing description plus
the engineering contract for the launcher package.

**Status (reality ladder):** the package and its orchestrator logic are
`TESTED` (124 automated tests across `tests/test_launcher_orchestrator.py`,
`tests/test_phase18_launchers.py`, `tests/test_run_bot_launcher.py`).
Real-process evidence has been recorded for the idempotent start→status→stop→
start cycle and the port-busy failure injection (`VERIFIED` only when a human
reads the receipts under `reports/launcher/smoke_*.json`). Nothing here is
`OPERATIONAL` until the owner runs it on their own machine and says so.

## What starts, in what order

```
stores      init_databases.py --with-guards   (SQLite, Lane-B)      CRITICAL
db_backend  Postgres or embedded pglite                            OPTIONAL
gateway     Next.js gateway + dashboard                            OPTIONAL
telegram    Telegram bot (owner interaction edge)                  OPTIONAL
engine      architecture.runtime --daemon ...                      CRITICAL
```

`launcher/components.py:START_ORDER` is the single list. The engine is launched
with the canonical command `--daemon --interval-sec 60 --observation-cycle
--evidence-source local`, and every child inherits `AHOS_PAPER_ONLY=1` and
`AHOS_EVIDENCE_SOURCE=local` hard-set (`ENGINE_ENV_HARD`) — so the daemon's rows
stay calibration-eligible and nothing can trade. The launcher refuses to start
the engine in any non-paper mode.

Optional components that fail do not halt the stack: the run is reported
`DEGRADED`. A critical failure rolls back exactly the processes this run
spawned (reverse boot order) and never a service that was already running
before us — the `fresh` flag on `ComponentResult`.

## Entry points (no-duplicates rule)

| Surface | Role |
| --- | --- |
| `launcher/ahos.ps1` / `launcher/ahos.bat` | the console wrapper the shortcuts open |
| `python -m launcher start\|stop\|status\|restart\|preflight` | the orchestrator (source of truth) |
| `start_ahos.ps1` / `start_ahos.bat` | thin delegates, kept for muscle memory only |

Do not add launch logic to `start_ahos.*`; the package owns it.

## Desktop shortcuts

`launcher/shortcuts.py` creates, for user `Sniper`:

- `AHOS.lnk` — start (opens the dashboard in the default browser when healthy)
- `AHOS Stop.lnk` — stop, only our own processes
- `AHOS Status.lnk` — status as a desktop notification/console read-out

Shortcuts target the console wrapper via `WScript.Shell`; the icon is the
in-repo `launcher/ahos.ico`.

## Health evidence, not pings

The engine is judged by real work in `ahos_local.sqlite`, not by a ping. Two
rows are read together:

- `scheduler_heartbeats.last_heartbeat_ts` (`DAEMON_CYCLE`), and
- the latest `scheduler_runs` row (`status`, `started_ts`) for `DAEMON_CYCLE`.

`record_heartbeat` fires **once per cycle, at the top of**
`execute_scheduled_cycle`, *before* its tasks run — so an observation cycle that
lasts many minutes legitimately ages the heartbeat far past any fixed window.
On a cold host the runtime init alone is ~110–160s and the first observation
cycle has been measured at ~21 minutes. Judging the engine by heartbeat
freshness alone therefore reports a working engine as dead, and the launcher
used to force-kill a healthy daemon on that basis. Verdicts now:

| situation | verdict |
|---|---|
| pid alive, heartbeat within `max_age` (200s) | `HEALTHY` |
| pid alive, heartbeat stale, but a `RUNNING` cycle begun by *this* pid within `MAX_CYCLE_SEC` (3600s) | `HEALTHY "in scheduler cycle"` |
| that cycle older than the budget | `UNHEALTHY "wedged"` |
| heartbeat stale, cycle not `RUNNING` or started before this pid (an orphaned row from a previously killed daemon) | `UNHEALTHY "stale"` |
| pid alive but no heartbeat yet | `UNHEALTHY "still booting"` |

The pid linkage matters: the pid record stores `started_ts`, so a `RUNNING` row
left behind by a force-killed previous daemon cannot pass a freshly-spawned
engine as healthy. The health wait for the engine is 420s, and after 45s of
still-unhealthy probing the console emits a one-time Persian "the engine is
running its first cycle; this takes a few minutes" line.

A process that is alive but never turned healthy within the wait is reported
`UNHEALTHY` with its last probe, not a generic "timed out".

Status is written to `reports/launcher/status.json` (latest) and a timestamped
archive; logs go to `logs/launcher/`.

## Owner-facing messages

All progress and error text is short Persian: what failed and what to do. The
port-busy line, for example:

> درگاه و داشبورد: ⚠ یک سرویس اجرا نشد. پورت ۳۴۵۰ توسط برنامهٔ دیگری اشغال
> شده. آن برنامه را ببندید یا با اجازهٔ صاحب پروژه AHOS_GATEWAY_PORT را عوض
> کنید.

Numbers are rendered in Persian digits. Every `ACTIONS` template is rendered
through `persian.error`, which substitutes `{port}`/`{sec}` — a placeholder
left literal is a bug, and there is a test for it.

## Gateway mode

`AHOS_GATEWAY_MODE` selects `prod` (a built `.next`) or `dev`. `auto` builds
once if the existing build is stale (`components.build_stale` compares `.next`
against source mtimes) and degrades to `dev` if the build fails or times out.
The smoke harness pins `dev` so a build never dominates a smoke run; the
production build is an explicit, separately recorded step.

## Windows port reservations

Windows reserves wide TCP ranges for Hyper-V/WSL
(`netsh int ipv4 show excludedportrange protocol=tcp`). A `connect` probe
reports such a port as free while `bind` still fails with `WinError 10013`. On
the development host the default gateway port 3000 lies inside one such range
and **cannot be bound by a non-admin process**. The smoke harness detects this
and retargets the injection to a bindable port via `AHOS_GATEWAY_URL`
(which outranks `AHOS_GATEWAY_PORT`). An operator hitting this on their own
machine gets the Persian port-busy message above and the same honest degrade.

## Process identification on this host

The project's `.venv\Scripts\python.exe` is a **shim**: it re-launches the real
interpreter (`C:\Users\Sniper\AppData\Local\Programs\Python\Python311\python.exe`)
with the same argv, so every AHOS Python process appears **twice** in
`tasklist`/`Get-CimInstance` — the shim and the worker it spawned. A pid record
therefore names the shim, and a process listing that looks like two identical
daemons is usually one daemon plus its shim, not a double start.

The stop path is written for this: `send_ctrl_break` signals the whole process
group (shim and worker share it) and `taskkill /T` walks the tree, so the worker
is stopped with the shim. What *does* orphan the worker is killing the launcher
itself (e.g. closing its console, or a harness timeout) instead of running
`AHOS Stop`: the detached children survive without a parent to issue the tree
kill. The cleanup for that case is `taskkill /T` on each root, not killing pids
individually.

### Marker must match the spawned argv (postmortem)

Identification is a *substring* match of a marker against the live command line,
so the marker is derived from the command we actually spawn, never hand-written.
An earlier version wrote the engine marker as

```
G:\robat\ahos\.venv\Scripts\python.exe architecture.runtime
```

but the engine is launched with `python -m architecture.runtime` — the `-m` is
between the interpreter and the module, so the marker was never a substring of
any real command line. Three failures followed, all observed in the receipts:

1. `probe_engine` → `probe_process` → `pid_is_ours` returned False, so every
   probe reported the running engine as *"recorded pid N is not a live AHOS
   process"*, the 420s health wait expired, and the CRITICAL engine failed the
   boot with rc=1 — while `engine.log` showed cycles completing.
2. `component_state("engine")` always returned `down`, so `start` spawned a
   **new** engine each time instead of an idempotent replay, orphaning the
   previous one.
3. `_sweep_ours` is blinded by the same marker, so `stop` never reclaimed the
   orphans it existed to catch.

Telegram was `HEALTHY` in every receipt throughout — its argv has no `-m`
(`python run_bot.py`), so its marker matched. That controlled contrast is what
isolated the cause, and it is now pinned by `TestProcessMarkers`, which asserts
each marker is a substring of the command the launcher actually builds.

The base-interpreter child of the shim carries no repo path at all, so the sweep
also carries the canonical daemon argv (`-m architecture.runtime --daemon`) as a
fallback marker for an engine whose shim has already died.

### Honest verdicts, and how `stop` reports what it halted (postmortem)

Three defects only fire on the real CLI path and each one alone kept the smoke's
`verdict.passed` false in every early receipt:

1. `stop` passed plain dicts into the report builder, which read `res.status` and
   raised — so a stop that *did* halt the engine and telegram exited 1 after
   printing "all AHOS services stopped". Stop now reports a `STOPPED`
   `ComponentResult` per component, naming how it was halted.
2. `status` ranked `UNAVAILABLE` below `UNHEALTHY` and mapped it to `DOWN`, so a
   stack missing only the optional gateway read `DOWN` and exited 1 while the
   engine ran cycles. `status` now uses `start`'s ladder: a CRITICAL component
   down is `DOWN`, an OPTIONAL one down is `DEGRADED`, everything healthy is
   `ONLINE`.
3. The smoke parsed the CLI's JSON report from the last line of stdout, but
   `--json` prints the Persian progress lines first and the report indented
   afterwards — so it read `}` and always failed, scoring a genuinely idempotent
   replay as a failure.

## Tests and evidence

- `tests/test_launcher_orchestrator.py` — Persian rendering, process kit,
  component builders, orchestrator idempotency/rollback/degrade, control-plane
  bridge, icon and shortcut specs, CLI exit codes, and `TestProcessMarkers`
  pinning every identity marker against the spawned argv.
- `tests/test_phase18_launchers.py` — pins the daemon contract at the launcher
  package, CRLF endings on every `.bat`/`.ps1` surface, and paper-only.
- `launcher/smoke.py` — real-process receipts under `reports/launcher/`:
  `idempotent` and `port-busy`. Never leaves a component behind.

## What this does not do

No trading, no wallet, no order execution. The launcher hard-sets paper-only
for every child. It does not change credentials, does not edit `.env`, and does
not decide the gateway port — that is an owner action.
