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

## Desktop shortcut — one icon

`launcher/shortcuts.py` creates exactly **one** icon for user `Sniper`:

- `AHOS.lnk` — start; opens the dashboard in the default browser when healthy

Target: `powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden
-File "<repo>\launcher\ahos.ps1" -Action start`, with `WindowStyle = 7`
(minimised) and `IconLocation = <repo>\launcher\ahos.ico,0`. The icon count is
an owner rule: **Status, Stop and Restart live inside the dashboard panel**, not
on the desktop. The two legacy links (`AHOS Stop.lnk`, `AHOS Status.lnk`) are
retired into `launcher/_retired_shortcuts/` rather than deleted.

"Minimised" is not "invisible": `-WindowStyle Hidden` in the arguments is what
actually keeps a console off the owner's screen, while the `.lnk`'s own
`WindowStyle = 7` is only the fallback hint a host would use if it ignored the
arguments.

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

Telegram is judged by the same principle — alive is not ready. `run_bot.py`
runs its own preflight (token presence, proxy, discovery stores, a live
`get_me()`) and exits 1 on any failure, so a bot that is *dying* is still
alive for the first second of its life. `probe_telegram` therefore requires
three things before it will say `HEALTHY`:

| situation | verdict |
|---|---|
| pid not ours / not alive | `UNAVAILABLE`, plus the last 3 redacted log lines |
| pid alive for less than `telegram_stable` (8s) | `UNHEALTHY "still in its own preflight"` |
| alive past the bar, but the readiness line has not appeared yet | `UNHEALTHY "readiness line ... (poll loop not started)"` |
| alive past the bar **and** the readiness line is in the log | `HEALTHY "alive for Ns and polling"` |

The readiness line is the one `run_bot.py` already prints once its long-poll
loop starts (`🤖 AHOS در حال گوش دادن است (offset=…)`) — a process that has
not reached the polls cannot print it, so it is a real readiness signal rather
than a second heartbeat. Because the launcher log is append-only, the search
starts at the byte offset recorded in the pid record at spawn time; a line
left by a *previous* bot cannot satisfy a fresh boot. The boot path demands
the line; the `status` poll and the "already running" path only use it when
it is there (`require_ready=False`), because a bot that has been up for hours
may have rotated its log.

If the bot exits inside the window, the report is `UNAVAILABLE` with the last
3 lines of `logs/launcher/telegram.log`, passed through both existing redaction
layers (`architecture.security.hygiene` and `architecture.mission.ledger`).
The token is never read or printed — only the *name* `TELEGRAM_BOT_TOKEN`
appears in the Persian action string.

This is a health-reporting change only. The idempotency decision is untouched:
a young-but-alive recorded pid is still `ours_running`, so a second concurrent
`start` never spawns a second bot polling the same token.

Status is written to `reports/launcher/status.json` (latest) plus a bounded set
of timestamped archives (`status_<utc>.json`, pruned to
`MAX_STATUS_ARCHIVES` — only state-changing actions archive anything); logs go
to `logs/launcher/`. The dashboard panel polls `GET /api/launcher`, which reads
that same file, so a poll never opens a socket against a component it is asking
about (fix e5: status polling now touches `status.json` only).

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

`HEALTH_WAIT["gateway"]` is 240s, not the 120s an earlier version allowed. The
probe already targets `/api/launcher` — the cheapest route in the app — but on
a slow filesystem Turbopack's *first* compile of even that one route has been
measured past 120s, so a gateway that was about to answer read `UNAVAILABLE`,
an OPTIONAL component failed, and a healthy boot was reported `DEGRADED` for no
real reason. The probe retries every second, so raising only the deadline was
the correct fix: it does not delay a fast boot, it just stops a cold one from
being misreported.

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

### The gateway marker, and why the npm wrapper is gone (M11.3)

The gateway was the last component whose marker could not match. It was spawned
as `cmd /c "npm run start --silent"`, a command line containing no path at all,
while its marker was `<root>\node_modules` — a directory, not a substring of any
command line. Every identity question about the gateway therefore went through a
special case: the pid record was trusted outright and the recorded command line
compared against the live one (Finding R7), while `stop` had to ask the TCP table
which process had inherited the port — the pid we recorded was the `cmd` wrapper,
which exits and reparents its `next start` child, so killing the recorded pid
never touched the listener.

The marker is now derived the same way as the engine's and telegram's — from the
argv the launcher spawns, which is

```
node <root>\node_modules\next\dist\bin\next start --hostname 127.0.0.1
```

the same script and flags `npm run start` resolves to (`dev` for the dev mode),
so `package.json`'s scripts stay the human entry point and no second entry point
exists. The recorded pid *is* the server, its own command line carries the
marker, and `pid_is_ours` answers on any OS — the special case is gone and `stop`
terminates the real listener. The marker is also *tighter* than what it replaced:
`<root>\node_modules` matched any node process started from this checkout, while
`...\node_modules\next\dist\bin\next` matches only a process running this
checkout's own next binary.

What the marker does *not* identify, unchanged: route health. A stale build that
404s every dashboard route has a perfectly good marker, so past its boot budget
the gateway is still route-probed like any other component. Port reclamation
stays too — a hard kill of the launcher (console close instead of `AHOS Stop`)
still orphans the listener — but that orphan is now the process we spawned, not a
reparented grandchild we can never reach by parentage.

If `node` or `node_modules/next` is missing, the gateway reports `UNAVAILABLE`
with a named reason rather than silently falling back to the npm wrapper, which
would reintroduce the identification defect.

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
  `idempotent`, `port-busy`, and `dashboard-api`. Never leaves a component
  behind. The receipt that closes the control chain is
  `reports/launcher/smoke_dashboard-api_20261005T021119Z.json`
  (`verdict.passed: true`, all eight control predicates true, zero visible
  consoles); the six earlier `dashboard-api` receipts stay as history.

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
markers can no longer be the reason a foreign process dies. M11.3 tightens the
gateway marker itself to this checkout's own `next` binary path, so the substring
no longer matches an editor's `next dev`/vitest/tsc either.

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

### Stage 2 — build review (2026-10-04, Asia/Tehran)

**رستم / Rostam — launcher and Windows process plumbing.** Verdict: `CHANGES`,
resolved and re-reviewed to `APPROVE`. Four defects, each proven by an isolating
experiment on this host rather than inferred:

*Finding R4 — the dashboard buttons did nothing.* `POST /api/launcher` returned
`202` with a pid and the stack never moved. Three-part root cause, each part
measured:
1. Node's `spawn(..., { detached: true })` starts the child with
   `DETACHED_PROCESS`. Windows PowerShell 5.1 with no console host **exits 0
   without executing the script at all**. Proven by a four-variant matrix on the
   same command: `detached: false` → exit `7` with the expected output;
   `detached: true` → instant exit `0`, empty stdout/stderr — regardless of
   `windowsHide` and regardless of a full path vs. bare `powershell.exe`. Even
   `powershell -Command "Write-Output X; exit 7"` produced nothing under
   `detached: true`. The 202 we saw was the starter shell's silent no-op, not
   the orchestrator's.
2. `detached: true` would not have helped even if it ran. The orchestrator stops
   the gateway with `taskkill /PID <gateway> /T`, which is a **process-tree** kill
   by parentage; `detached` does not break that parentage. Proven with a
   heartbeat child that perished at its own `taskkill /T /F` against its parent.
3. What does reparent is `Start-Process` (ShellExecute): the worker's ppid
   becomes a shell host rather than the gateway pid, and the same heartbeat child
   then survived `taskkill /T /F` on its grandparent and ran to completion.
   *Resolved:* the route now starts `ahos.ps1` through a hidden
   `Start-Process -PassThru` and returns the **reparented** pid in the 202 body,
   so the dashboard reports the worker that actually runs. The lock no longer
   clears on the starter shell's exit (that would clear instantly); it holds to
   its TTL and the orchestrator's per-component idempotency answers a late second
   click with `ALREADY_RUNNING`.

*Finding R5 — `logs/launcher/launcher.log` was never written.* The hidden path's
tee branch threw every run. Two independent PowerShell 5.1 traps, both silent:
(a) `Tee-Object` has **no `-Encoding` parameter** on 5.1 (it is a PowerShell 7
parameter) — the pipeline failed with "a parameter cannot be found" before
python started, and the `catch` re-ran python with no log; (b) under
`$ErrorActionPreference = 'Stop'` a native command's stderr line is a
*terminating* error, so the first python warning would have aborted the pipe
mid-stream even if (a) were fixed. *Resolved:* the tee is replaced by
`Out-File -Encoding utf8 -Append` wrapped in a local
`$ErrorActionPreference = 'Continue'` that is restored in a `finally`.
Verified on this host: Persian output survives as real UTF-8 (BOM + correct
glyphs), python's stderr lines land in the log instead of killing it, and
`$LASTEXITCODE` still propagates to `exit $rc` (a deliberate `sys.exit(7)`
reached the shell's exit code).

**گیتی / Giti — safety and governance, on R4.** Verdict: `APPROVE` on the
direction, one constraint recorded. The write-ahead audit chain is unchanged:
`EXECUTING` is still recorded before anything is spawned, `FAILED` if no
reparented pid comes back, `CONFIRMED` only after one does. The one consequence
worth naming: the launcher's exit code can no longer be observed by the route,
because the worker is deliberately outside our tree — so the panel's source of
truth for "did it work" is the `status.json` it polls, never the spawn call
itself. That is the honest dependency: the route can only promise *it handed the
work to a live, reparented process*.

**Stage-2 conclusion:** both build findings are resolved with measured fixes;
the dashboard stop/restart path now actually executes, and the owner-readable
launcher log exists.

**سامان / Saman — TypeScript surfaces and the dashboard contract.** Verdict:
`CHANGES`, resolved. Two findings, both about what the panel may *infer* from
the route's answers:

*Finding S1 — the 202 lied on the one path that matters.* The old handler
returned `202` for a spawn whose child never ran, so the panel rendered
"در حال اجرا" for a stop that did not happen and the owner had no way to tell a
real in-flight action from a silent no-op. Resolved: the route now distinguishes
the three outcomes honestly — a starter-shell failure or a non-numeric pid
returns `500` `LAUNCHER_SPAWN_ERROR` *and* writes the `FAILED` audit line, so
the ledger never claims an action that was never handed off; only a reparented
pid returns `202`. The panel's own guidance is that a `202` means "handed to a
live worker", never "done" — the work is done when `status.json` says so.

*Finding S2 — `priorSkips` could carry a stale marker.* The restart forwards the
previous run's `SKIPPED` components so Restart restores the stack that was
running instead of widening it. But `SKIPPED` was read without checking *which*
run wrote it: a status file left over from an earlier, unrelated boot would have
forwarded that boot's exclusions into this one. Resolved: `priorSkips` reads the
same status file the GET returns, and the marker is only meaningful because the
orchestrator writes a fresh report on every run; the smoke's
`restart_preserved_skip` asserts the forwarded set equals the set the smoke
asked for, which is the end-to-end check that the round trip is not stale.
Constraint recorded, deliberately not "fixed": the file has no run-id of its own,
so the freshness guarantee rests on the orchestrator always rewriting it — a
property the idempotency tests pin, not something the route can verify alone.

**فرناز / Farnaz — evidence, receipts and the reality ladder.** Verdict:
`CHANGES`, resolved.

*Finding F1 — the smoke's own deadlines were shorter than the work it
measures.* The hand-typed 900s restart / 300s stop waits once expired *inside* a
restart that was still succeeding, so the receipt recorded `passed: false` for a
stack that came back correctly ~44 minutes in. Resolved: both deadlines are now
derived from `TIMEOUTS` plus a `_CHILD_SLACK` of 180s, so the poll budget can
never drift below the timeout the table already budgets for that action. The
comment naming the incident stays in `smoke.py` so the number is not quietly
re-tightened later.

*Finding F2 — a run killed mid-case leaves no receipt, and that used to read as
an ambiguous result.* `main()` writes the JSON only after the case returns
normally, so a harness kill mid-run lands nothing at all — an empty output file
that says neither pass nor fail. Two things were genuinely missing and one
deliberately was not. Resolved: each case's own `finally` runs two real `stop`
invocations, so no started component survives an interrupted case even when the
receipt never lands; and a receipt that *does* land with `passed: false` names
the specific wait that expired (`restart_seconds`, `stop_seconds`) instead of a
bare boolean, so a false verdict is diagnosable. What is deliberately not fixed
and is recorded as a limitation: the receipt itself cannot be written from a
`finally` at the process level, because a hard kill cannot run Python. The
honest reading of a missing receipt is therefore "interrupted, no evidence",
never "failed".

*Finding F3 — the gateway health budget misreported a cold compile.* A cold
Turbopack compile of `/api/launcher` on this slow drive outlasted the 120s
`HEALTH_WAIT["gateway"]`, so an OPTIONAL component failed on a boot whose only
defect was the compile, and the run reported `DEGRADED`. The probe target was
already the cheapest route in the app, so the deadline was the wrong number.
Resolved: the budget is 240s (see "Gateway mode" above). A fast boot is not
slowed at all — the probe turns healthy the moment the route answers.

**Stage-2 conclusion (final):** all build findings are resolved with measured
fixes; the dashboard stop/restart path executes through a reparented worker, the
owner-readable `launcher.log` is written in UTF-8 Persian, and the health
budgets cover the cold-boot costs this host actually exhibits.

### Stage 2 — follow-up findings during delivery verification

Four more defects surfaced while exercising the real hidden path end to end.
Each is recorded here because a reviewer reading only the sections above would
otherwise believe the resolutions above were the last word. Two of them
supersede a resolution above; that is stated rather than rewritten.

*Finding R6 — the `Out-File` tee that resolved R5 wedged the shell.* The R5
resolution (a PowerShell `| Out-File -Append` pipe) was itself the defect: a
PowerShell pipe ends when its **write** end closes, not when python exits, and
`spawn_detached`'s children inherit that handle. A `restart` stops the very
gateway that spawned the shell, python then exits, and the shell stays pinned on
the pipe reader forever — a hidden `powershell.exe` holding the module lock the
next stop/restart reports as `ALREADY_RUNNING`. Proven on this host: the wedged
shell's only live child was `conhost.exe`; python was long gone. Eight such
shells had accumulated before this was found. *Resolved (supersedes R5's
resolution):* the pipe is gone. `ahos.ps1` runs a plain `& $Python @PyArgs` and
exports `AHOS_LAUNCHER_LOG`; `launcher/__main__.py` installs a `_Tee` on
`sys.stdout`/`sys.stderr` that appends to that file, **file first** so a console
whose codepage cannot render Persian still gets every line into the UTF-8 log. A
file has no reader to block on, so the shell waits on nothing but python and
`$LASTEXITCODE` still reaches `exit $rc`. Verified through the route's exact
`Start-Process -WindowStyle Hidden` spawn: the `status` shell exits in 0.8s, the
`restart --skip telegram,engine` shell exits in 21s with the stack back ONLINE
and both skips carried forward. The eight zombie shells were cleared.

*Finding R7 — a second `start` called our own gateway a foreign port.*
`component_state` identified a live pid by a repo substring in its command line,
but the gateway runs as `cmd /c "npm run start --silent"`, whose command line
carries no repo substring. A second `start` therefore read our own live gateway
as `foreign_busy`, reported `DEGRADED`, and emitted the Persian line for "another
program holds the port" — a fabricated claim about a service we spawned
ourselves. *Resolved:* the pid record is authoritative for the gateway (only we
write it), with the recorded command compared against the live one so a pid
Windows re-issued to an unrelated program is still rejected. Verified live: a
second `start` while ONLINE now reports the gateway idempotent at its recorded
pid and stays ONLINE. Two regression tests pin both the adopted and the
reissued-pid cases. **Superseded by M11.3** (like R6 superseded R5): the root
cause was that the gateway was spawned through an npm wrapper whose command line
carried no marker, so the comparison above was a stop-gap over a marker that
could never match. The gateway is now spawned as `node <next cli> start` and the
marker is derived from that argv, so this special case is deleted — see "The
gateway marker, and why the npm wrapper is gone" above.

*Finding R8 — a dashboard Restart silently widened the stack (DEFECT A).* A
skipped component leaves no pid record, so a read-only poll read it as
`UNAVAILABLE`, the route's `priorSkips()` returned `[]`, and Restart brought up
components the owner had excluded. *Resolved:* the skip set is persisted to
`data/launcher/skips.json` before the results loop, and `status`/`stop` relabel
those components `SKIPPED` ("skipped by request (carried forward)"). The smoke's
`restart_preserved_skip` is the end-to-end assertion.

*Finding R9 — `status` probed the configured port while the gateway served
another (DEFECT B).* `status()` probed port 3000 while the gateway had walked to
8300 because 3000 is Windows-reserved here, so the panel reported the dashboard
down while the owner's browser had it open. *Resolved:* an `_adopted_gateway`
pass runs in both `start()` and `status()`, keyed off the port the live listener
actually bound (`chosen_via: ADOPTED_OUR_LIVE_LISTENER`), guarded by the same
recorded-pid check as R7 so a stale record left by a crashed gateway is not
adopted.

*Finding R10 — the "new wedge" was not a code defect at all.* After R6 the
hidden `restart` path appeared to wedge again: a smoke run died mid-restart and
left an orphaned route-spawned shell. My first hypothesis was that
`pk.send_ctrl_break` — `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, pid)` — was
killing the *caller*, since a hidden `-WindowStyle Hidden` shell shares one
console with its children. **That hypothesis is disproven, not merely abandoned.**
A faithful repro under a real hidden PowerShell console (a ps1 spawning a python
that spawns a detached `cmd`, then calling `send_ctrl_break` on that pid)
recorded `send_ctrl_break -> True`, `caller still alive after ctrl_break`,
`SURVIVED`, `ps1 rc=0`. The caller survives. Two related measurements came out of
the same experiment and are worth keeping: against a console-less detached tree
`GenerateConsoleCtrlEvent` returns `True` with `lasterror=0` but does **nothing**
(spurious success), and `taskkill /PID <pid> /T` **without** `/F` fails with
rc=128 ("this process can only be terminated forcefully") — which is exactly why
`pk.terminate`'s real stops land on the final `taskkill /F /T` branch and report
`(۰.۹s, force)`. That is correct behaviour, not a bug to fix.

The actual cause was in my own harness, not the launcher: the outer wrapper used
`timeout 1500`, which is **180s shorter than the smoke's own internal
`_RESTART_DEADLINE` of 1680s** (`TIMEOUTS["restart"] 1500 + _CHILD_SLACK 180`),
so I strangled my own smoke mid-restart and the orphaned shell was the corpse.
The smoke's deadlines were already correct (F1); the outer budget was not.
*Resolved:* the outer wrapper budget is 3500s — above every internal deadline
combined — and the exact path that failed (`restart --skip telegram,engine`,
hidden, through the route's own spawn shape) was then run directly and completed
in **8 seconds**, ONLINE, gateway pid 10688 on 8300,
`gateway_chosen_via: CANDIDATE_BINDABLE`, `cp_status: SYSTEM_ONLINE`,
`idempotent_replay: true`, both skips carried forward. The standing rule for any
re-run: the outer budget must never fall below 3500s.

**Follow-up conclusion:** R6–R10 are all resolved; R6 and R7 supersede the R5 and
foreign-port resolutions above respectively, and R10 exonerates code that a
weaker diagnosis would have "fixed" wrongly.

*Finding R11 — a Next server answering 404 for the control route is not our
gateway, and the launcher used to say it was.* The `dashboard-api` smoke run at
`20261004T162806Z` failed with **every** HTTP step at `status=404, sec=0.0` and
`audit_lines_appended: 0`, after `restart_seconds: 1680.7` (the full budget) and
`stop_seconds: 270.1`. The 404 bodies were our own rendered 404 page
(`lang="fa" dir="rtl"`, vazirmatn/orbitron), so a Next server was definitely up
on 8300 — it simply did not have `/api/launcher` registered in the server that
held the port.

Two independent checks pinned the source tree as innocent: the production build
does carry the route (`.next/server/app/api/launcher/route.js`, and both
`app-path-routes-manifest.json` and `routes-manifest.json` list it), and a
**fresh** `next dev` started from this repo answered `HTTP 401`
`WEB_API_UNAUTHORIZED` on the same route in 40s. The route is correct; the server
on 8300 was not built from it — a stale listener from an earlier run that no
later `start` replaced.

Why no later `start` replaced it is the actual defect, and it had two layers:

1. `probe_gateway` treated *any* answer under HTTP 500 as "listening", so a 404
   read `HEALTHY` — the status report literally said *"gateway answers HTTP 404
   on http://127.0.0.1:8300/api/launcher"* and declared the gateway HEALTHY and
   the stack ONLINE. A 404 is not a boot delay and not a slow compile: it means
   the route is not registered in the server that answered, so it is now
   `UNAVAILABLE` with the reason named in the detail.
2. `component_state` returned `ours_running` for the gateway from the pid record
   alone. The record proves we *spawned* a process that is still alive, not that
   the process is still serving this app — so the stale server was replayed as
   "already running (idempotent)" on every subsequent start and the real gateway
   was never restarted. Past the gateway's boot budget the pid record is no
   longer sufficient: the route probe must agree. Inside the budget a young
   gateway is still trusted on its pid record, because the launcher route is not
   compiled until first request and a booting gateway can legitimately miss the
   probe for the first seconds — without that grace every `start` would spawn a
   second gateway while the first was still booting.

This is also why the failure cost 28 minutes instead of seconds: the smoke polls
`status.json` on disk while it waits for the restart report, and the audit ledger
never gained the line the dead route could not write. With the probe honest, the
same condition now fails fast with a diagnosable message instead of waiting out
its budget.

*Resolved:* commit `863819f` (probe + idempotency), with four regression tests —
the 404 probe, a stale gateway past budget reading `down`, a booting gateway
inside budget still reading `ours_running`, and the previously host-flaky
`test_start_adopts_our_live_gateway_port` made deterministic (pid 4242 is a
dummy; `pid_alive`/`process_cmdline` were not stubbed, so it passed only when
Windows happened to have that pid open).

**Follow-up conclusion (final):** R6–R11 are all resolved. R6, R7 and R11
supersede R5, the foreign-port resolution and the R3 health-probe target
respectively — each replaced a mechanism that was correct under one condition
and silently wrong under another (a tee that wedged the shell, a pid record that
outlived the app it named, a probe that counted a 404 as listening). R10
exonerates code that a weaker diagnosis would have "fixed" wrongly.

### Stage 3 — delivery sign-off (2026-10-04, Asia/Tehran)

Each reviewer walked the scope list (a)–(f) item by item against the delivered
tree, not the plan. A `CHANGES` verdict would have to be fixed and re-signed
before the final commit; all three returned `APPROVE` with the deviations below
recorded in place of silence.

**قاسم / Ghasem — owner contract, scope (a), (b), (e).** Verdict: `APPROVE`.

- (a) One shortcut is created by `launcher/shortcuts.py` (`ACTIONS = {"start":
  "AHOS"}`), pointing at `launcher/ahos.ps1 -Action start` with
  `-WindowStyle Hidden` and `launcher/ahos.ico,0`. No second icon is created
  anywhere in the delivery; the retired shortcut templates live in
  `launcher/_retired_shortcuts/` outside the install path. Recorded deviation:
  the icon file was replaced during the mission and the previous copy is kept as
  `launcher/ahos.ico.old-20261003-200745`, a local artifact that is not
  installed and not committed.
- (b) No visible console at any point: `ahos.ps1` runs hidden, children inherit
  `CREATE_NO_WINDOW`, and the smoke case proves it with a window census rather
  than an assertion — it enumerates the visible-window processes on the host and
  requires none of them to be ours. Recorded deviation from the original plan:
  the ps1 pipeline had to stop using a PowerShell tee (R6) because the tee's
  write end closing wedged the detached children; the log is now written by a
  Python-side `_Tee` that writes the file first, so "no visible console" and
  "the launcher log exists" are both true at once.
- (e) All eight Stage-1 findings are closed with code, and the five delivery
  findings that followed (R6–R10) plus the 404 (R11) are closed too. Ghasem's one
  caveat is about coverage, not correctness: R11 was found by evidence, not by a
  test that would have caught it — a stale-listener condition is not reproducible
  in a unit test without a live port, so the regression tests pin the *decision
  rules* (404 → UNAVAILABLE; pid record alone is not enough past the boot budget)
  rather than the scenario.

**رضا / Reza — evidence and the reality ladder, scope (f).** Verdict: `APPROVE`.

- Launcher pytest, measured per file: `test_launcher_orchestrator.py` 89 passed,
  `test_launcher_smoke.py` 25 passed, `test_phase18_launchers.py` +
  `test_gateway_port.py` 81 passed, `test_run_bot_launcher.py` +
  `test_control_plane_soak.py` 33 passed — plus 4 `test:launcher-route` and 26
  `test:chat-auth` TypeScript selftests, and `npx tsc --noEmit -p .` clean. One
  test (`test_gateway_port_we_can_bind_still_spawns`) spawns a real gateway and
  is slow; it passes, but it is why targeted runs name node ids instead of
  running the whole file blindly. The orchestrator file's 7 newest tests cover
  the R12b fixes (console-break immunity, marker-proven live-port lookup).
- Real-process receipts land under `reports/launcher/`: `smoke_idempotent_*` for
  the idempotency contract and `smoke_dashboard-api_*` for the full control
  chain. The dashboard-api receipt that closes this mission is
  `reports/launcher/smoke_dashboard-api_20261005T021119Z.json`, which reads
  `verdict.passed: true` with every control-chain predicate true —
  `restart_accepted`, `restart_preserved_skip`, `restart_brought_stack_back`,
  `route_served_after_restart`, `audit_pair_for_restart`, `stop_accepted`,
  `stack_stopped`, `audit_pair_for_stop` — and `components_owning_windows: []`,
  zero visible consoles. Six earlier dashboard-api receipts stay in place as
  history and are not overwritten: `…20261004T012011Z.json` and
  `…20261004T014054Z.json` (the first control-chain attempts),
  `…20261004T162806Z.json` (404 on a stale listener, R11),
  `…20261004T182940Z.json` (a leftover dev server from my own probe script blocked
  out of `.next/dev`, so the gateway never bound and every control timed out — an
  artifact of the investigation, not a launcher defect; the probe scripts were
  deleted), `…20261004T190910Z.json` and `…20261004T223502Z` (the two that exposed
  R12b: `stop()` signalled its own process group and died mid-stop, leaving the
  gateway listener bound — fixed by `arm_console_break_immunity` plus a
  marker-proven live-port lookup; see `GROK_HANDOFF.md` R12b).
- One residue is recorded as `UNKNOWN` rather than fixed: the hidden
  `ahos.ps1` shell that hosted a route-spawned orchestrator once stayed idle
  ~30 min past its python child's exit, invisible and holding no port. Four
  minimal reproductions all exited cleanly, so no mechanism is claimed. It does
  not affect the no-console rule or later control actions.
- Reality ladder: self-tests cap at `TESTED`. `VERIFIED` needs an owner-read
  receipt, and `OPERATOR_READY` / `PRODUCTION_READY` need real operator
  evidence. Nothing in this delivery claims past `TESTED`; OD-249 and OD-257 are
  ticked `IMPLEMENTED+TESTED` with the counts above, and the "pending owner read
  for VERIFIED" clause is kept rather than dropped.
- Deviation recorded: the stack is left stopped at the end of the delivery, as
  the scope requires, and the receipts are the only thing still warm.

**عرفان / Erfan — safety and authority boundaries, scope (c), (d).** Verdict:
`APPROVE`.

- (c) The panel's Status/Stop/Restart live inside `CommandCenter.tsx` and go
  through `POST /api/launcher`, which demands loopback *and* the web API token
  and writes the audit line before anything is spawned (`EXECUTING` →
  `CONFIRMED`/`FAILED`, ledger `data/control_audit/chat_control_audit.jsonl`).
  Read-only status polling reads `reports/launcher/status.json` only and never
  opens a socket against the component it is asking about — the smoke case
  asserts exactly that separation. No second recommendation authority was
  created: the route moves processes, it does not score or decide, and
  PAPER_ONLY is untouched.
- (d) The gateway port comes from non-secret `config/gateway_ports.json` with a
  real `bind` test (`can_bind`, not a connect probe — a Windows exclusion range
  fails bind with nothing listening, and the delivery proved this on 3000). The
  chosen port is pushed to children as `AHOS_GATEWAY_URL`/`PORT` and recorded in
  `status.json`; `.env` is never written and no secret lands in the config or the
  log. `AHOS_WEB_API_TOKEN` is never logged by any path in this delivery; the
  smoke reads it only to prove the auth guard demands it, and prints status, not
  the value.
- Deviation recorded, and it is a real one: the health probe had to change target
  from `/api/chat` to `/api/launcher` (R3 → R11). `/api/launcher` is the cheapest
  route in the app and the one the panel itself polls, so the probe costs a
  fraction of the compile — but it is also an *authenticated* route, so the probe
  sees `401` on a healthy gateway. That is why `http_ok`'s "any answer under 500
  counts" was correct for liveness and wrong for identity, and why the 404 case
  is now named explicitly instead of folded into "listening".

**Stage-3 conclusion:** all three sign off. The delivery is `TESTED`, not
`VERIFIED` — the difference is the owner-read receipt, and it is the owner's to
give. The stack is stopped.

