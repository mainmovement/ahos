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

## M11.1 review notes (2026-10-03, Asia/Tehran)

Mission 11.1 — launcher finish. Every review stage is recorded here: agent
name, role, findings, verdict, and how the finding was resolved. Stage 1 ran
*before any code was written*; its findings were folded into the build plan.

### Stage 1 — prompt review (before code)

**آرش / Arash — architecture and plan.** Verdict: `CHANGES`.
Finding A1: the prompt's scope (d) said "a NON-SECRET launcher config/settings
key (e.g. `config/launcher.json`)" while the repo already resolves gateway
settings through `scripts/gateway_port.py` + `load_repo_env`; adding a second
settings channel risks two sources of truth. Resolved: one resolver is
extended, not duplicated — `gateway_port.py` gains `can_bind()` and
`select_port()`, candidates come from a non-secret `config/gateway_ports.json`
(env `AHOS_GATEWAY_CANDIDATE_PORTS` still outranks it), and the *launcher*
writes the chosen port back into `reports/launcher/` state, never into `.env`.
Finding A2: `resolve_gateway()` has ~40 references and existing tests pin the
3000 default; a rewrite would break them for no owner-visible gain. Resolved:
`resolve_gateway()` stays pure and unchanged; `select_port()` is the new
entry point for "which port will I actually use".

**رستم / Rostam — launcher and Windows process plumbing.** Verdict: `CHANGES`.
Finding R1: `spawn_detached` uses `DETACHED_PROCESS | CREATE_NO_WINDOW`, and
on Windows `CREATE_NO_WINDOW` is *ignored* in that combination; a console-less
`cmd /c npm` child then allocates its own **visible** console. Resolved: flags
become `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` and the docstring states
that survival on console-close now comes from the launcher's own hidden
console rather than detachment. Finding R2: the prompt's "prefer
`.venv\Scripts\pythonw.exe`" is the wrong call — `pythonw` has no console, so
the graceful CTRL_BREAK path is dead on arrival and unredirected stderr pops a
GUI dialog. Resolved: keep `python.exe`; "no visible window" is delivered by
`-WindowStyle Hidden` on the launching powershell, not by pythonw. Finding R3:
`_sweep_ours` identifies processes by substring markers, and the gateway
marker `<repo>\node_modules` matches *any* node/cmd process started from this
checkout — including `next dev`, vitest or tsc launched by an editor session.
Resolved: the sweep is rewritten on strict **parentage** (one CIM snapshot +
`descendant_of` against recorded pid-record roots and the launcher pid), so
markers can no longer be the reason a foreign process dies.

**پروانه / Parvaneh — owner UX and Persian text.** Verdict: `CHANGES`.
Finding P1: one desktop icon only — the prompt keeps `AHOS Status.lnk` /
`AHOS Stop.lnk` implied by the old code; the owner rule is a *single* `AHOS.lnk`
with Status/Stop/Restart living inside the dashboard. Resolved:
`shortcuts.py:ACTIONS` becomes `{"start": "AHOS"}` and the dashboard gains the
panel (scope c). Finding P2: `$lnk.WindowStyle = 7` is *minimized*, not
invisible; the owner rule "no visible console at any point" is only satisfied
by `-WindowStyle Hidden` in the shortcut arguments. Resolved: the arguments
carry `-WindowStyle Hidden` and `WindowStyle = 7` is kept as the fallback
presentation hint, documented as such. Finding P3: the panel needs owner-grade
Persian for statuses and ages, not English enum names. Resolved: `persian.py`
gains `STATUS_FA`, `HEALTH_FA`, `PANEL` and `age_fa`; the TS side mirrors the
same word list.

**گیتی / Giti — safety and governance.** Verdict: `CHANGES`.
Finding G1: the dashboard control endpoint must reject non-loopback callers
*before* it does any work; the prompt listed loopback and auth in the wrong
order. Resolved: the route does `isLoopbackRequest` → 403, *then*
`authorizeDashboardEndpoint`, *then* the audit write-ahead. Finding G2: "spawn
`python -m launcher stop`" detached from the gateway must not inherit the
gateway's own console group or a Ctrl-C event could kill the stop mid-flight.
Resolved: the route spawns `powershell -WindowStyle Hidden -File ahos.ps1`
`detached` + `windowsHide`, and `ahos.ps1` no longer blocks on `Read-Host` in
its default (hidden) path. Finding G3: no duplicate modules — the prompt's
wording allowed a second launcher surface. Resolved: extend `launcher/`, the
existing app routes and `CommandCenter.tsx` only; the only new files are the
one API route the panel calls and the non-secret ports config.

**Stage-1 conclusion:** no reviewer returned `APPROVE` without changes; all
eight findings above were folded into the build plan before the first edit.

