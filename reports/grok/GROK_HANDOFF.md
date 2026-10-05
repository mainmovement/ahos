# GROK HANDOFF (living document) — for Claude Code

> **Claude: start with [`reports/grok/CLAUDE_CONTINUATION_GUIDE.md`](CLAUDE_CONTINUATION_GUIDE.md)**. It covers Phases 1–9 (Phase 7 = conversational AI with confirm-gated paper commands, owner authority decision 2026-10-02, pending سپهر/قاسم/رضا review; Phase 8 = dev-mission intake + University/agents discovery; Phase 9 = Mission 9 truth baseline + Remaining Reality Register; Phase 9.5 + 9.6 = corrective mission closing every finding in two independent reviews): what was built, where the code lives, exact Windows commands, invariants, process setup, local-only commits (pushes paused), and blocker A.

<!-- M11_1:START -->
## Mission 11.1 (2026-10-04, Claude/Atria): launcher finish — the dashboard buttons, the log, and the health budgets

Mission 11.1 — the finish pass on the Mission 11 one-click launcher. Scope
(a)–(f): one desktop icon, zero visible consoles, a Status/Stop/Restart panel
inside the dashboard, a gateway port resolved by a *real bind test*, Grok's
eight review findings closed, and targeted tests plus real-process receipts.

**The short version:** M11 left two latent defects that only fire on the real
CLI path, and both were invisible to the unit suite. The dashboard's Stop /
Restart buttons did nothing, and the owner-readable launcher log was never
written. Both are fixed, proven on the real path, and both root causes are
measured rather than inferred.

### What changed

- **`app/api/launcher/route.ts` — the dashboard buttons now actually execute.**
  The handler spawned the orchestrator child with Node's `detached: true`, which
  on Windows is `DETACHED_PROCESS`. Windows PowerShell 5.1 started that way has
  *no console host*, so it exits 0 without executing the script at all — proven
  by a four-variant matrix on the same command: `detached: false` → exit 7 with
  the expected output; `detached: true` → instant exit 0, empty stdout/stderr,
  regardless of `windowsHide` and regardless of a full path vs. bare
  `powershell.exe`. Even `powershell -Command "Write-Output X; exit 7"` produced
  nothing under `detached: true`. The `202` the panel received was the starter
  shell's silent no-op, not the orchestrator's. And `detached` would not have
  helped even if it ran: the orchestrator stops the gateway with
  `taskkill /PID <pid> /T`, a process-tree kill by parentage, and `detached`
  does not break that parentage — proven with a heartbeat child that perished at
  its own `taskkill /T /F` against its parent. What does reparent is
  `Start-Process` (ShellExecute): the worker's ppid becomes a shell host, and
  the same heartbeat child then survived. The route now starts `ahos.ps1`
  through a hidden `Start-Process -PassThru` and returns the **reparented** pid
  in the 202 body, so the panel reports the worker that actually runs. A failed
  or non-numeric pid now returns `500` `LAUNCHER_SPAWN_ERROR` *and* writes the
  `FAILED` audit line — the old handler returned 202 for a spawn that never ran.
  The lock no longer clears on the starter shell's exit (that would clear
  instantly); it holds to its TTL and the orchestrator's per-component
  idempotency answers a late second click with `ALREADY_RUNNING`.
- **`launcher/ahos.ps1` — the owner-readable log exists.** The hidden path's tee
  branch threw every run, because of two independent PowerShell 5.1 traps, both
  silent: (a) `Tee-Object` has **no `-Encoding` parameter** on 5.1 (it is a
  PowerShell 7 parameter), so the pipeline failed with "a parameter cannot be
  found" *before python started*, and the `catch` re-ran python with no log;
  (b) under `$ErrorActionPreference = 'Stop'` a native command's stderr line is
  a *terminating* error, so the first python warning would have aborted the pipe
  mid-stream even if (a) were fixed. Replaced with `Out-File -Encoding utf8
  -Append` inside a local `'Continue'` preference restored in a `finally`.
  Verified on this host: Persian survives as real UTF-8, python's stderr lands
  in the log instead of killing it, and `$LASTEXITCODE` still propagates (a
  deliberate `sys.exit(7)` reached the shell's exit code).
- **`launcher/orchestrator.py` — the gateway health budget covers a cold
  compile.** `HEALTH_WAIT["gateway"]` was 120s; Turbopack's *first* compile of
  `/api/launcher` on this slow G: drive has been measured past that, so a
  gateway that was about to answer read `UNAVAILABLE`, an OPTIONAL component
  failed, and a healthy boot reported `DEGRADED` for no real reason. Now 240s.
  The probe already targets the cheapest route in the app and retries every
  second, so a fast boot is not slowed at all — only a cold one stops being
  misreported.
- One-icon rule (`launcher/shortcuts.py`): `ACTIONS = {"start": "AHOS"}`.
  Status/Stop/Restart live inside the dashboard panel, not on the desktop; the
  two legacy links are retired into `launcher/_retired_shortcuts/`.
- Gateway port resolution (`scripts/gateway_port.py` + non-secret
  `config/gateway_ports.json`): `can_bind()` / `select_port()` do a real bind
  test, so the launcher never spawns a gateway onto a port it cannot hold. The
  launcher writes the chosen port into `reports/launcher/` state, never `.env`;
  `resolve_gateway()` stays pure and unchanged.
- `launcher/smoke.py`: the restart/stop poll deadlines are derived from
  `TIMEOUTS` + `_CHILD_SLACK` (180s) rather than hand-typed 900/300, which once
  expired *inside* a restart that was still succeeding and recorded
  `passed: false` for a stack that came back correctly. A new `dashboard-api`
  case proves the whole control chain against the real gateway: loopback guard,
  auth guard, write-ahead audit pair, a child that actually moves the stack, and
  a poll that reads `status.json` without opening a socket against the component
  it is asking about.

**Follow-up findings during delivery verification (R6–R11).** Exercising the
real hidden path end to end surfaced six more defects; all resolved, all
recorded with the isolating measurement that proved each one. R6: the R5
`Out-File` tee itself wedged the shell (a PowerShell pipe ends when the *write*
end closes, and the detached children inherit that handle — eight zombie
`powershell.exe` accumulated, each holding the module lock); superseded by
`AHOS_LAUNCHER_LOG` + a Python-side `_Tee` that writes the file *first*. R7: a
second `start` called our own gateway `foreign_busy` because `cmd /c npm run
start` carries no repo substring — the pid record is now authoritative, with the
recorded command line compared against the live one so a reissued pid is still
rejected (2 regression tests). R8 (DEFECT A): a dashboard Restart silently
widened the stack because a skipped component left no pid record and
`priorSkips()` returned `[]` — skips now persist to `data/launcher/skips.json`.
R9 (DEFECT B): `status()` probed the configured 3000 while the gateway had
walked to 8300 — an `_adopted_gateway` pass keyed off the port the live listener
actually bound. R10: the "new wedge" that followed R6 was **not a code defect** —
my outer smoke wrapper ran `timeout 1500` against an internal `_RESTART_DEADLINE`
of 1680s, so I strangled my own smoke mid-restart. The leading hypothesis
(`GenerateConsoleCtrlEvent` kills the shared-console caller) is *disproven* by a
faithful hidden-console repro: the caller printed `SURVIVED`, `ps1 rc=0`. Same
experiment established that `GenerateConsoleCtrlEvent` returns spuriously `True`
against a console-less detached tree and that `taskkill /T` without `/F` fails
rc=128 — which is exactly why `pk.terminate` lands on `taskkill /F /T` and real
stops report force. The failed path then ran directly: 8s, ONLINE, skips
preserved. Outer wrapper budget for any re-run: ≥3500s. R11: the
`dashboard-api` smoke at `20261004T162806Z` returned 404 for every control
call after a 1680s restart wait — a Next server *was* up on 8300 (our own
rendered 404 page), but it did not hold `/api/launcher`. The source tree is
innocent: the prod build carries the route and a fresh `next dev` from this
repo answers 401 on it in 40s. Two masking layers kept that stale listener in
place — `probe_gateway` counted any `<500` answer as listening (a 404 read
HEALTHY and the status even quoted the 404), and `component_state` returned
`ours_running` from the pid record alone, so every later `start` replayed the
dead server as "already running" and the real gateway was never restarted.
Fixed in `863819f`: a 404 probe is `UNAVAILABLE` with the cause named, and a
recorded gateway past its 240s boot budget must also pass the route probe
(inside the budget the pid record still wins, since the route is compiled on
first request and a booting gateway can legitimately miss the probe). 4
regression tests, one of which makes the host-flaky adoption test deterministic.

### Review workflow (all three stages recorded)

Stage 1 (prompt review, *before any code*) — آرش/Arash, رستم/Rostam,
پروانه/Parvaneh, گیتی/Giti: no reviewer returned APPROVE without changes; all
eight findings were folded into the build plan. Stage 2 (build review) —
رستم/Rostam (R4, R5), گیتی/Giti, سامان/Saman (S1, S2), فرناز/Farnaz (F1, F2,
F3): every finding resolved with a measured fix. Stage 3 (delivery sign-off) —
قاسم/Ghasem, رضا/Reza, عرفان/Erfan, each checking the scope list item by item,
all APPROVE. **All of it is in `docs/ONE_CLICK.md` under "M11.1 review notes" —
that is the authoritative record for this mission.**

### R12 — restart stranded the gateway port (found at delivery sign-off)

The dashboard-api smoke kept failing on `restart_brought_stack_back`, and the
stack stayed DEGRADED with no gateway afterwards. Two coupled defects, both
proven live:

1. **Port-release race.** `restart` was `stop()` + `time.sleep(1.0)` + `start()`.
   Measured on this host, the killed gateway's listening socket becomes bindable
   ~1.1 s after `taskkill /F` returns, so the flat 1 s sleep sat exactly on the
   boundary: the restarted gateway found its own just-killed port still held,
   reported `port_not_bindable`, and the stack came back DEGRADED with no gateway.
2. **Unreclaimable orphan.** The gateway is `cmd /c npm run start`; its `next
   start` child is reparented the moment the `launcher start` that spawned it
   exits, and once the pid record is cleared the parentage sweep can never reach
   it (`roots` = recorded pids ∪ our own pid). One failed restart therefore left a
   live listener on 8300 with no record naming it, and every later `start` read
   `foreign_busy` forever — proven: orphan `cmd → npm node → next cmd → node`
   alive in LISTEN while `data/launcher/` held only `skips.json`.

Fixes: `restart` is now a real `AhosOrchestrator.restart()` that polls the port
with a real `bind` (bounded, so a port that never frees still returns a report
instead of hanging); `stop()` now verifies the gateway port afterwards and, if a
listener survives, asks the TCP table for its owner and terminates that tree —
but only when the owner's command line proves it is ours, so a foreign program
on the same port is reported, never killed. Two audit-predicate bugs in
`launcher/smoke.py` were fixed at the same time: the append count read only the
last 40 ledger lines (it saturated at zero) and the pair check matched a
previous run's EXECUTING/CONFIRMED pair.

### R12b — the stopper signalled itself (root cause of the remaining failures)

The R12 fixes were necessary but not sufficient: the dashboard-api smoke still
left a live gateway listener after `POST stop`, and `launcher.log` died right
after the "stopping" header. Root cause, proven: `GenerateConsoleCtrlEvent` targets
a **process group**, not one process, and the dashboard route launches its
orchestrator as a descendant of the very gateway `stop()` must terminate. Every
descendant inherits the gateway's group, so `send_ctrl_break(gateway_pid)` delivered
a SIGBREAK to the orchestrator itself, which had no handler and died mid-stop —
after emitting the header, before terminating anything. The pid record was left
untouched and the listener stayed bound.

Two fixes:

1. `processkit.arm_console_break_immunity()` installs a `SetConsoleCtrlHandler`
   that returns `TRUE` for CTRL_C and CTRL_BREAK, so the default handler never
   runs; `stop()` arms it as its first action, before any signal goes out.
2. `_gateway_listen_addr()` no longer falls back to the *configured* port (3000 —
   unbindable on this host) when the pid record is gone. A new
   `_live_our_gateway_port()` scans the non-secret candidate list against the TCP
   table and adopts a listener only when its owner's command line proves it is
   ours, so a stranded listener is reached instead of reported as foreign.

Evidence: `reports/launcher/smoke_dashboard-api_20261005T021119Z.json` —
`verdict.passed: true` with `restart_brought_stack_back`, `route_served_after_restart`,
`restart_preserved_skip`, `audit_pair_for_restart`, `audit_pair_for_stop`,
`stack_stopped`, and `components_owning_windows: []` (zero visible consoles) all
true; `logs/launcher/launcher.log` now runs the whole stop to `overall: STOPPED`
instead of stopping at the header. Six earlier receipts (`012011Z`, `014054Z`,
`162806Z`, `182940Z`, `190910Z`, `223502Z`) remain in place as history, unedited.

One residue the smoke surfaced but I could **not** reproduce minimally, so its
mechanism is `UNKNOWN` rather than fixed: after the route's stop/restart the hidden
`ahos.ps1` shell that hosted the orchestrator stayed alive ~30 min past its python
child's exit, idle with only a `conhost.exe` child, holding no port and no window.
`-WindowStyle Hidden` means it is invisible, so it does not break the no-console
rule, and later control actions are unaffected (verified: a status shell exits in
0.5 s, a fast-path stop shell in 8.5 s, and both a minimal `spawn_detached` host and
a group-targeted CTRL_BREAK host exited cleanly). Removed with
`Stop-Process -Force` (`taskkill /T /F` silently failed on them). Left recorded,
not invented.

### Tests and evidence

- `pytest tests/test_launcher_orchestrator.py` → **89 passed** (~340 s). 7 new
  tests cover the two fixes above: the immunity handler only swallows
  CTRL_C/CTRL_BREAK (not event 5) and reports unavailable without kernel32;
  `stop()` arms immunity before it signals; `_gateway_listen_addr()` prefers the
  recorded port, finds our live listener without the record, ignores a foreign
  listener on a candidate, and skips the TCP scan for a non-loopback gateway.
- `pytest tests/test_launcher_smoke.py` → **25 passed**; the same file's 3 new
  audit-baseline tests are counted in it.
- `pytest tests/test_phase18_launchers.py tests/test_gateway_port.py` →
  **81 passed** (~12 s).
- `pytest tests/test_run_bot_launcher.py tests/test_control_plane_soak.py` →
  **33 passed** (~320 s; the soak's real waits dominate).
- `npx tsc --noEmit -p .` → **0 errors**.
- Real-process receipts under `reports/launcher/`: `idempotent`, `port-busy`,
  `dashboard-api`. The proof both real-path fixes work is `logs/launcher/
  launcher.log` — written by the reparented child the route spawned, in correct
  UTF-8 Persian; it had never existed before this mission.

### Standing items (owner action, not mine)

- The stack's real `OPERATIONAL` claim needs the owner to run `AHOS.lnk` on
  their own machine and say so. Self-tests cap at `TESTED`.
- Port 3000 is inside a Hyper-V/WSL excluded range on this host and cannot be
  bound by a non-admin process; the launcher degrades to a bindable candidate.
  An operator hitting this gets the Persian port-busy message and the same
  honest degrade.
<!-- M11_1:END -->

<!-- PHASE9_6:START -->
## Phase 9.5 + 9.6 (2026-10-03, Claude/Atria, 12:14 Tehran): corrective mission from two independent reviews

Mission 9.6 (corrective mission, parts 1 and 2). Two independent reviews of the
local commits — `reports/grok/reviews/REDTEAM_19_LOCAL_COMMITS_20261002-2313.md`
and `reports/grok/reviews/LOCAL_COMMITS_5_HARDMODE_REVIEW.md` — raised 1 blast
finding, 4 major, 7 minor (REDTEAM-19) and 3 blast, 13 major, 12 minor
(HARDMODE). **Every finding is closed; no row is NOT FIXED, PARTIAL, or
HUMAN-GATED.** The per-finding map with commits and re-runnable tests is
`reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md` — that is the authoritative
record for this phase; the tables below are the summary.

Commits: `0638643` (9.5, part 1) and `8e54953`, `832f0ce`, `6b2e0f6`,
`5974da0`, `e22a154`, `da651af`, `c127f68`, `dbc9125` (9.6, part 2). All local;
nothing pushed.

### What changed

- **Identity is now server-proven, never claimed** (B1/BL-3, M1/MJ-6): `isOwner`
  requires `id.proven` and membership of `TELEGRAM_ADMIN_USER_IDS`; the reader
  allowlist grants read only. The client assertion is carried through the
  gateway for the audit record and is never a grant.
- **Confirm-flow integrity** (M3/MJ-1/MJ-7, m1/MN-7, m2, m5, m6): the proposal
  binds the full summary text plus a 64-hex `summaryHash`; `confirmCode` is
  threaded from the proposal into the queue and stored only as a hash; two
  dashboard sessions get distinct identity keys; 5 wrong guesses lock the
  identity out; paper quantity clamps to `MAX_PAPER_QUANTITY`.
- **Audit before action** (MJ-1/MJ-2/MJ-13): an EXECUTING record is written
  before anything runs, a broken audit sink aborts the action and burns the
  code, and `scripts/verify_control_audit.ts` anchors the chain prefix.
- **Secrets never leave the boundary** (M2/BL-1/BL-2, m3/m4, MJ-5, MN-5):
  redaction is global and runs on the summary, the title, the DB insert and the
  memory copy; the current message is redacted before Gemini.
- **Tests that actually drive the code** (MJ-4, MJ-11, MJ-12): the static gate
  pins were re-anchored after the snapshot seam moved, the reply validator
  rejects flipped direction / out-of-order numbers / added buy advice, and a
  DB-free `handleChat` harness exercises every channel and confirm path.
- **MN-1 (last code finding, `dbc9125`)**: `hashId` and `messageHash` are now
  HMAC-SHA256 keyed by a local pepper (env → 0600 data-dir file → per-process
  random), so Telegram ids are not brute-forceable and short commands are not
  dictionary-reversible. The append-only static pin was re-scoped to
  `FileAuditSink`, not weakened.
- **Config and docs** (MN-4, MN-9, MN-12, MJ-9, MJ-10, MN-10, MN-11): Gemini
  egress is an explicit file-backed owner approval, default-on, with
  `AHOS_GEMINI_EGRESS` as the kill switch; the registry attribution and the
  dev-mission topic match were corrected; the `dev_missions.ts` docstring now
  states plainly that raw user text stays in `chat_messages` (redacted); the
  owner directives, mission plan, orchestration log, reviews and PoC are
  tracked; the 9.5 receipts are committed; the two key-storage helpers are
  tracked after a masked secret scan found 0 hits.

### Tests run this phase (all exit 0)

- `npx tsc --noEmit -p .` → 0 errors.
- `npm run lint` → 0 problems.
- 15/15 self-test suites, 466 tests, 0 failures: web-api-auth 9,
  canonical-read-model 13, canonical-security 19, alert-banner 8,
  dashboard-truth 34, chat-reply-format 48, chat-intent 76, chat-control-gate
  131, chat-agent 30, dev-missions 14, gemini-phraser 12, chat-auth 23,
  chat-actions 18, chat-handlechat 18, gemini-egress 13.
- `pytest tests/test_chat_control_gate_static.py` → 12 passed.

### Failures and root causes

1. `test_audit_record_has_no_raw_text_or_raw_id_fields` failed once at
   `assert "writeFileSync" not in src`: the MN-1 pepper persistence added a
   `writeFileSync` to `chat_control_gate.ts` and tripped the append-only pin.
   Fixed by scoping the ban to the `FileAuditSink` class body — the invariant's
   real subject — and strengthening it with a `mode: 0o600` assertion. The
   pepper file is a separate, once-created secret, not the audit file.
2. A stray `data/.id_pepper` was written into the repo during the first test
   run. Root cause: `recordControlAudit` with the default env resolves the
   pepper through `process.cwd()/data`. Fixed by pinning `AHOS_ID_PEPPER` in
   the self-tests that touch the audit path; `data/` is gitignored, so
   nothing was committed. Re-checked after the fix by running every suite
   with the file deleted between runs: it is no longer created. One more
   writer surfaced in the re-check — `dev_missions_selftest.ts` goes through
   `DevMissionStore.append`, which hashes the confirm code internally, so it
   needed the same pin (`ba40fb7` follow-up).
3. The test total first recorded for this phase was 414; the per-suite list
   already summed to 466. Re-measured suite by suite and corrected to 466 in
   the matrix, this handoff and the guide.

### Remaining unknowns / next action

None from the reviews. The mission's own open list is unchanged by this phase:
GM-01 (doc-drift clean-checkout regression), GM-02 (Telegram offline harness),
GM-03 (dashboard stale-READY), the gateway port decision, and the wall-clock
items. **Self-tests are not independent verification** — the two reviews were
the independent pass; a third-party re-run of the matrix's test column is the
next step up the reality ladder.

<!-- PHASE9_6:END -->
<!-- PHASE11:START -->
## Phase 11 (2026-10-03, Claude/Atria, ~19:30 Tehran): Mission 11 — one-click launcher, no Docker

The owner's final goal: double-click one desktop icon and the whole observation
stack comes up without Docker. Built the in-repo `launcher/` package
(`ahos.ps1`/`ahos.bat` console wrapper, `orchestrator.py`, `components.py`,
`processkit.py`, `persian.py`, `shortcuts.py`, `make_icon.py`, `smoke.py`) plus
`docs/ONE_CLICK.md`. Reality ladder: **TESTED** (124 unit tests) + real-process
smoke receipts under `reports/launcher/`; nothing is OPERATIONAL until the owner
runs it and says so.

Commits: `2270146` (package + tests), `9e74645` (real-process evidence), and the
marker-fix commit this phase. All local; nothing pushed.

### What changed

- **Boot order + criticality** — `START_ORDER = stores, db_backend, gateway,
  telegram, engine`; only `stores` and `engine` are CRITICAL. An optional
  component failing reports `DEGRADED`, a critical one rolls back exactly the
  processes that run spawned (reverse boot order) and never a service that was
  already healthy (`ComponentResult.fresh`).
- **Paper-only is structural** — `ENGINE_ENV_HARD` hard-sets `AHOS_PAPER_ONLY=1`
  and `AHOS_EVIDENCE_SOURCE=local` on every child; the launcher refuses to start
  the engine in any non-paper mode.
- **Health by real work, not pings** — the engine is judged by
  `scheduler_heartbeats.last_heartbeat_ts` plus the latest `scheduler_runs` row
  (status, started_ts) for `DAEMON_CYCLE`. Because `record_heartbeat` fires once
  per cycle *before* its tasks, a long observation cycle legitimately ages the
  heartbeat; a `RUNNING` row begun by *this* pid within `MAX_CYCLE_SEC` (3600s)
  is `HEALTHY "in scheduler cycle"`, while the same row started before this pid
  (an orphan from a killed daemon) is `UNHEALTHY "stale"`. On a cold host the
  first cycle is ~21 minutes, so a heartbeat-only check reported a working
  engine as dead.
- **Persian operator messages** — every progress/error line is short Persian,
  Persian digits, and each `ACTIONS` template is rendered through
  `persian.error` with `{port}`/`{sec}` substituted; a literal placeholder is a
  tested bug.
- **Shortcuts** — `AHOS.lnk`, `AHOS Stop.lnk`, `AHOS Status.lnk` for user
  `Sniper` via `WScript.Shell`, targeting the console wrapper with the in-repo
  `launcher/ahos.ico`.

### Root cause this phase — identity marker missed the `-m` (postmortem)

The launcher decides "is this process ours" by a substring match of a marker
against the live command line. The engine marker was hand-written as

```
G:\robat\ahos\.venv\Scripts\python.exe architecture.runtime
```

but the engine is spawned as `python -m architecture.runtime --daemon …` — the
`-m` sits between interpreter and module, so the marker was **never** a
substring of any real command line. Three failures followed, all visible in the
`reports/launcher/status_*.json` receipts:

1. `pid_is_ours` → False, so every probe reported *"recorded pid N is not a live
   AHOS process"* while `logs/launcher/engine.log` showed cycles completing; the
   420s health wait expired and the CRITICAL engine failed the boot (rc=1).
2. `component_state("engine")` always returned `down`, so `start` spawned a
   **new** engine on each invocation instead of an idempotent replay — the
   receipts show pids 6296 → 17584 → 17532 across three starts.
3. `_sweep_ours` is blinded by the same marker, so `stop` never reclaimed the
   orphans it exists to catch; pid 6296 was still alive 43 minutes after the
   smoke's final stop.

Telegram probed `HEALTHY` in every single receipt throughout — its argv has no
`-m` (`python run_bot.py`), so its marker matched. That controlled contrast
isolated the cause. **Fix:** markers are now derived from the commands the
launcher actually builds, and `TestProcessMarkers` asserts exactly that
relationship (4 new tests). The sweep also carries the canonical daemon argv as
a fallback, because the venv shim's base-interpreter child carries no repo path
at all. The orphan was killed with `taskkill /T /F` on the shim pid.

### Three more latent bugs the smoke surfaced once the marker was fixed

With the engine finally detectable, the smoke got far enough to expose three
defects that had each independently kept `verdict.passed` false in every receipt
so far. None was visible in unit tests; each only fires on the real CLI path.

1. **`stop` crashed after doing its job.** `_report` reads `res.status`, but
   `stop` passed it plain dicts (`{"pid", "how", "secs"}`), so a stop that
   successfully halted the engine and telegram then raised `AttributeError` and
   exited 1. The Persian output said "all AHOS services stopped" while rc was 1.
   Fixed: stop now builds real `ComponentResult` objects with status `STOPPED`
   and the termination method as detail, so the receipt names what was halted.
2. **`status` reported a working stack as `DOWN`.** Its verdict ranked
   `UNAVAILABLE` below `UNHEALTHY` and mapped it to `DOWN`, so with the optional
   gateway absent (unbindable port 3000 — see below) the whole stack read `DOWN`
   and exited 1 while the engine ran cycles. `start` already called this
   `DEGRADED`; `status` now uses the same ladder — critical component down →
   `DOWN`, optional down → `DEGRADED`, all healthy → `ONLINE`.
3. **The smoke could not read its own result.** `_run` parsed the CLI's JSON
   report from the *last line* of stdout, but `--json` still prints the Persian
   progress lines first and the report pretty-printed with `indent=2` — so the
   last line is `}` and the parse always failed, leaving `report: null` on every
   step. A genuinely idempotent second start was therefore scored
   `second_start_was_idempotent_replay: false`. Fixed with `_parse_report`, which
   tries each `{` in stdout and takes the first that decodes to end-of-output.

The processes that kept reappearing after each stop were not a launcher bug: two
orphaned `ahos.ps1 -Action start` consoles (from earlier double-click attempts)
were still alive with their own `python -m launcher start` children, which
re-spawned the engine and telegram as soon as the smoke stopped them. Killed with
`taskkill /T /F` on each console tree before the final smoke run.

### Real-process evidence (first green receipts)

`reports/launcher/smoke_idempotent_20261003T171539Z.json` — 8 steps, **all rc=0,
`passed: true`**. start (engine pid 6664, heartbeat 2s) → status (DEGRADED, same
pid) → start again (**"already running (idempotent)", same pid 6664**, control
plane `idempotent_replay: true`) → stop (STOPPED) → start (fresh pid 13064) →
status → stop → stop again (NOT_RUNNING clean no-op). This is the first receipt
where the second start did not re-spawn the engine and where `stop` exited 0.

`reports/launcher/smoke_port-busy_20261003T173201Z.json` — failure injection:
port 3450 held by a foreign listener, gateway correctly `UNHEALTHY
foreign_busy`, overall `DEGRADED` (never ONLINE), the Persian port-busy line
emitted with the port number substituted, `passed: true`. The host was left with
no AHOS processes after both runs.

### Standing items (owner action, not mine)

- **Gateway port 3000 is unbindable on this host** — it lies inside a Hyper-V/WSL
  excluded port range (`WinError 10013` on `bind`, while a `connect` probe says
  free). The gateway is therefore `UNAVAILABLE` in every receipt and its log is
  empty. Choosing another port (e.g. 3450 via `AHOS_GATEWAY_PORT` /
  `AHOS_GATEWAY_URL`) or excluding 3000 from the reservation is **OWNER_ACTION**;
  I do not edit `.env`.
- The `DATABASE_URL` pglite flip is M10 Stage 4 and owner-gated.
- Blocker A (GM-01 doc-drift clean-checkout regression) remains open.

### Next action

Owner runs `AHOS.lnk`, reads the Persian console, and either sees the dashboard
open or the named failing component; the receipt under `reports/launcher/` is
what turns TESTED into VERIFIED.

<!-- PHASE11:END -->
<!-- PHASE9:START -->
## Phase 9 (2026-10-03, Claude/Atria): Mission 9 — truth baseline + Remaining Reality Register

Owner-directive mission M9, five parts, all complete. **Grok's source, config,
and runtime state were untouched**; every commit is docs, one Lane-B bug fix,
or a previously untracked evidence file. Pushes still paused — local commits
only. Lane A untouched and verified.

### 9a: Test baseline + import side-effect audit (A, B)

- `reports/m9/BASELINE.md` — exact pytest / tsc / eslint / self-test counts
  with the reason for every skip and xfail. Genuine failures were small and
  root-caused with regression tests; nothing was silently quarantined
  (`629e757`).
- `reports/m9/IMPORT_SIDE_EFFECTS.md` — Mandate §12 item 2: 266 modules in
  `architecture/`, `scripts/`, `src/` audited for network / IO / DB / env /
  thread mutation at import time. **0 confirmed** side effects (`3b0da90`).

### 9b: The one real bug found and fixed (FM-007, `0b878be`)

`architecture/learning/prediction_lifecycle.py` hard-coded
`eligible_join_pairs_estimate = 0`, so the census claimed "no
calibration-eligible join" while the live ledger held thousands of eligible
pairs. Root cause: the two stores are separate sqlite connections, so the
obvious cross-DB JOIN is unavailable and the original code silently returned
the sentinel instead of approximating. Fixed by intersecting the two token-id
sets in memory; verified against the live DBs (19 labeled tokens ∩ 20,744
predicted tokens = **10**) and pinned by a new regression test in
`tests/test_prediction_lifecycle_bridge.py` (6/6). Failure Memory entry
FM-007 appended to `reports/FAILURE_MEMORY.md`.

> **This resolves the handoff's unresolved item 7** ("prediction_lifecycle
> census fix — pending owner approval"). The fix is in `0b878be`; re-derive
> live counts with `scripts/calibration_report.py` rather than quoting the
> old `0`. Note the units differ: the census's **10** is distinct tokens; the
> calibration report's **6,037** is (prediction, label) pairs per
> (horizon, event-class). Both are correct.

### 9c: Remaining Reality Register (C) — the new standing authority

`reports/grok/REMAINING_REALITY_REGISTER.md` — the Remaining Capability Graph
per owner directive part1 §76–§80: **33 capability areas** (§1–§33) plus **5
cross-cutting findings** (CC-1..CC-5), each with ladder state, evidence path,
dependencies, proof requirement, and governance gate. Every live count was
re-queried for the register, not quoted from prose.

Read this file before quoting any readiness claim. Where it disagrees with an
older map, **the register wins**. Headline states: discovery pipeline
`OPERATIONAL`; provider fallback, scoring, Lane-A freeze, calibration and
backup/restore `VERIFIED`; paper trading `PARTIAL` (the loop never closed);
scheduler / runtime / identity / decision authority `TESTED`; n8n
`CONTRADICTED`; live trading `ABSENT BY CONSTRUCTION`.

### 9d: Stale-map banners (D)

Twelve historical readiness maps now carry dated STALE / SUPERSEDED banners
pointing at the register, including `AHOS_PROJECT_STATE_MAP.md` (its A–E
taxonomy and its "Verified = re-checked by automated tooling" definition are
exactly what §76 forbids), `reports/PHASE_STATE.md` (its "first live cycle
executed" is contradicted by `paper_exits = 0` and a 100%-empty
`paper_trading.sqlite`), and `reports/G2_MISSION_REPORT_20261002.md` (its
`pre_soak_entry_ok = TRUE` is transitory; the standing
`reports/PRE_SOAK_STATUS.txt` holds `False` with G2/G3/G10 `NOT_VERIFIED`).
`docs/CANONICAL_IMPLEMENTATION_MATRIX.md` was corrected, not only bannered:
two narrative-intel paths fixed to their `architecture/` roots and its summary
recounted by hand (COMPLETE 17 / PARTIAL 10 / BLOCKED_EXTERNAL 3 /
DEFERRED_BY_DESIGN 2 / NOT_IMPLEMENTED 1 = 33 rows; a prior 29 had drifted).
`reports/FAILURE_MEMORY.md` gained FM-001..FM-007; `reports/nightly_backup_series.json`
was committed as tracked (`1834779`) because four canonical docs cite it and a
clean checkout was failing the doc-drift check.

### 9e: Mission-plan notes (E)

`reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md` gained an "M9 outcome" section.
The owner's binding order is **unchanged**; the section records evidence that
affects later missions. Two things in that plan are inconsistent and a future
mission should reconcile them: the original mission list and the 18:47 owner
update disagree on what "M12" means (agents vs paper trading + learning), and
the 18:49 order follows the 18:47 renumbering while the original list was
never renumbered. **Use the 18:49 order; treat the original list as mission
definitions only.**

### Findings the next mission should act on (all dependency-safe, none gated)

1. **Wire `paper_trading/cycle.py:run_full_cycle` into the daemon.** The
   register's single highest-leverage node: it unblocks calibration, outcome
   tracking, the live decision authority, trade-derived learning, and
   accounting — five capabilities, all currently sitting on a 0-row database.
   No new capability needed, no governance gate, no Lane A write.
2. **CC-3** — `architecture/ai/debate_council.py::_risk_manager_evaluation`
   annotates a bare `Tuple` it never imports. One-line fix plus a test; latent
   `NameError`, never triggered because the council has never run on a real
   token.
3. **CC-4** — `cycle_duration_ms` max is 58,621,870 ms (~16.3 h) on a 60 s
   cadence daemon: clock-drift / suspend contamination, not a real cycle. Any
   latency SLO derived from that column must sanitize it first (250/2,644
   samples exceed 60 s).
4. **CC-5** — `chain_id = 'robinhood'` labels 3,635 observations (3.3%);
   robinhood is not a blockchain. Per-chain stats and identity joins must
   treat it as invalid. Correction touches Lane A semantics → reviewed
   migration, not a drive-by fix.
5. **CC-1** — route the daemon through `ControlPlane` so START/STOP/SAFE_HALT
   are actually reachable by an operator. `assert_safe_environment` *is* wired
   into the live loop, so this is operator-control parity, not a safety hole —
   but the one-click launcher mission cannot deliver clean stop/health without
   it.

### Tests run this phase (Windows, all exit 0)

Targeted only, per the per-directory chunking rule: `tests/test_prediction_lifecycle_bridge.py`
6/6 (incl. the new FM-007 regression test), plus the m9 baseline suites
recorded in `reports/m9/BASELINE.md`. The full suite count is in that file,
not re-run wholesale here.

### Security / governance

PAPER_ONLY held. Lane A untouched and re-verified. No execution surface
created or enabled (`NO_EXECUTION_SURFACE` stands). No secrets printed or
written — the Gemini key stayed in Windows Credential Manager `AHOS/ai/gemini`
and was never read. `.cursor/hooks.json`, `*.local-backup`,
`ahos-hooks-local-diff.txt`, and `reports/pgdump_*.sql` were not touched.
No push; no force, reset, rebase, or history rewrite.
<!-- PHASE9:END -->

<!-- PHASE8:START -->
## Phase 8 (2026-10-02, Claude/Atria): dev-mission intake in the chat assistant + University/agents discovery

Mission 8. The previous Phase 8 run died with an API 400 and produced nothing; this run started clean (nothing was reused). Pushes still paused: **local commits only**. Status: IMPLEMENTED / TESTED (self-tests; no live gateway check this run). Not independently verified.

### 8a: dev-mission intake (`d10383e`)

The chat assistant cannot write code. When the owner asks for engineering work (new features, the university, operationalizing agents), it now proposes recording it as a **development mission**, using **exactly the same confirm flow and words as the paper commands**: model or whole-message request → PROPOSAL (Persian summary + one-time 6-char code, 5 min, bound to the proposer's identity) → «تایید <code>» → one line appended to a hash-chained queue with status QUEUED → reply that it is recorded for the engineering team and that **no work is done**. `list_dev_missions` is a read tool showing queued-mission status. Non-owners are refused and audited.

**Files:**
- `dev_missions.ts` (new): `DevMissionStore`, an append-only JSONL queue (schema `ahos.dev_missions.v1`, default `<AHOS data dir>/dev_missions/dev_missions.jsonl`, or `AHOS_DEV_MISSIONS_PATH`). One record per mission: `seq, ts, id (DM-000001), confirmCode, titleFa, summaryFa, status: "QUEUED", channelClaimed, userIdHash, prev_hash, entry_hash`. It reuses `FileAuditSink` (torn-tail isolation, never rewrites), `verifyAuditLines` (edit/deletion/reorder detection) and `hashId` (sender id hashed, never raw) from `chat_control_gate.ts`. Secret-like substrings in the summary are redacted **before** hashing/writing (`redactMissionSecrets`; the marker carries the rule name only — an earlier draft leaked the first 12 chars of the secret into the marker and the self-test caught it). The raw chat message is never stored: `cleanSummaryFa` keeps the owner's own words but strips greetings, zero-width/bidi marks and newlines, and truncates to 280 chars. No status but QUEUED is writable from the chat path, and the module executes nothing.
- `chat_actions.ts`: `ActionKind` gains `dev_mission`; `ActionParams` gains `missionSummaryFa`; `Capability` gains `MISSION_WRITE` (with a deny-by-default refusal text); `propose()` rejects an empty summary (DENIED `EMPTY_SUMMARY`, audited); `ActionDeps` gains `recordDevMission`, bound in `defaultActionDeps()` to `getDevMissionStore().append()`; `handleConfirmation` appends the QUEUED line and audits `PROPOSED → CONFIRMED` (reason `MISSION_QUEUED`). `proposalTextFa` now emits a warm locked intro for dev missions («حتماً! من خودم کد نمی‌نویسم…») and the header «آماده ثبت است (هنوز ثبت نشده)».
- `chat_agent.ts`: new PROPOSE tool `submit_dev_mission{summaryFa}` and READ tool `list_dev_missions`; `runReadTool` takes an optional `ReadToolCtx { missions?, owner? }` — the read tool is owner-only (non-owners get an empty view with a Persian note); the jargon guard now also blocks `submit_*`/`list_*` tool names in answers; the Persian system prompt tells the model it writes no code, may never claim work is done/started, and must answer warmly before proposing.
- `chat_intent.ts`: new conservative `dev_mission` intent (requires BOTH a development topic and an explicit build verb, so complaints and questions do not match). It is the **deterministic fallback** for when the agent is off/circuit-open; when the agent is up it is never reached (the agent answers first).
- `chat.ts`: passes the store into `ChatAgent.run`; deterministic `dev_mission` branch mirrors the `watch_add` pattern (propose or refuse).
- `chat_control_gate.ts`: `canonicalJson` is now exported (reused by `dev_missions.ts` for the hash chain).

**Tests (Windows, all exit 0):**
- tsc 0; eslint 0 on all touched files.
- `npm run test:dev-missions` (new): 14/14 — hash chain and stable ids, empty-summary refusal, greeting/truncation cleaning, secret redaction, hashed sender id, newest-first Persian age labels, tamper detection (edit / delete-first / reorder), the documented keyless-chain limitation (deleting only the last line is invisible; `head_hash` must be anchored outside the file), fail-closed append.
- `npm run test:chat-agent`: 30/30 (was 23; +7 dev-mission cases: warm locked proposal, non-owner denial, empty summary, owner-only queue read, confirm appends exactly once and audits PROPOSED→CONFIRMED, cancel/wrong-identity never queue, system-prompt pins).
- `npm run test:chat-intent`: 72/72 (was 52; +20 Persian dev-mission cases incl. negatives).
- chat-control-gate 126/126, chat-reply-format 40/40, gemini-phraser 12/12, canonical-read-model 13/13; `npm run audit:control-verify` OK.
- pytest static set (`test_chat_control_gate_static`, `test_gemini_chat`, `test_telegram_reply_presentation`, `test_gemini_phraser`, `test_agent_taxonomy_map`): 60 passed, 1 skipped.

**Not done / open:**
- No live gateway POST this run (the gateway was not restarted; hot-reload picks up the TS on the next request). A live end-to-end «دانشگاه رو بساز» → code → «تایید CODE» → queued line is **unverified**.
- The queue has **no consumer**: nothing reads it yet. The future mission-controller layer (M13, "autonomous engineering core", in the mission plan) is the intended reader; the store's own docstring says so.
- `AHOS_DEV_MISSIONS_PATH` is not in any config-validation scan (same as `AHOS_CONTROL_AUDIT_PATH` — pre-existing gap).
- A gateway reload does not lose queued missions (they are on disk), only pending proposals.
- Recorded missions are never shown as done; there is deliberately no DONE/COMPLETED status.

### 8b: University + agents discovery
See `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` (new this phase). Read-only; no code changed.
<!-- PHASE8:END -->


<!-- PHASE7:START -->
## Phase 7 (2026-10-02, Grok): conversational AI for Telegram and dashboard (Gemini + tools + confirm-gated paper commands)

**Pushes are still paused by the owner: local commits only.** Status: IMPLEMENTED / TESTED (self-tests and a live gateway check). Not independently verified. **The owner's authority decision of 2026-10-02 changes the GM-04 invariant for owners. It is flagged for سپهر/قاسم/رضا review** (see `GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md` §8).

### 7a: intent router fix (`231e7ac`)
- New pure `chat_intent.ts`: price intent (BTC/ETH/SOL spelling variants, freshness and stale flag, no invented numbers), trade_signal intent (locked PAPER_ONLY policy reply that outranks stop_loss), thanks, greeting-prefix routing, watchlist view checked before watch_add.
- `scripts/chat_intent_selftest.ts`: 52 Persian regression cases (`npm run test:chat-intent`).
- The GM-04 whole-message control detection still runs first.
- 7a is now the **deterministic fallback** under 7b.

### 7b: owner scope change at 17:35. The chat is a real conversational AI.
The owner asked for free-form, multi-turn Persian chat like ChatGPT/Grok, not keyword intents. The same backend (`chat.ts::handleChat`) serves Telegram (`telegram_ai/service.py` → `/api/chat`, channel `telegram` plus the real user_id) and the dashboard chat panel.

**Flow per message (`chat.ts::handleChat`):**
1. A whole-message `تایید CODE` / `لغو [CODE]` goes to `chat_actions.handleConfirmation` (before any intent detection).
2. `detectIntent` runs, then the GM-04 gate (whole message, so «stop loss» is never a stop).
   - **Non-owner** control intent: REFUSED, audited (unchanged).
   - **Owner** control intent: a confirm-gated proposal. Nothing executes.
3. The snapshot is taken. **`ChatAgent.run` comes first** (Gemini function calling over a whitelisted tool registry, max 4 model steps).
   - On success: the reply is the agent's grounded Persian answer, or the locked proposal/denial text.
   - On failure (provider down, quota, breaker open, validation rejected twice): the deterministic 7a path runs, with an honest note at the top. The note says either «دستیار هوشمند الان در دسترس نیست…» or «پاسخ دستیار هوشمند با داده‌های سیستم تطبیق نداشت…».
4. Memory is updated and the chat rows are written (same `chat_messages` table as before).

**Files:**
- `chat_agent.ts` (new)
  - Tool registry:
    - READ: `get_market`, `list_opportunities`, `explain_token{symbol}`, `get_news{query}`, `get_engine_status`, `get_paper_positions`, `get_watchlist`, `get_system_health`
    - PROPOSE: `propose_engine_start`, `propose_engine_stop`, `propose_paper_buy{symbol,quantity}`, `propose_watch_add{symbol}`
  - `runReadTool` is pure over the existing `commandSnapshot()` read model. It returns Persian labels plus freshness (`updatedAgoFa`, `stale`) and never raw English status codes (`faLabel`). For BTC/ETH/SOL, `explain_token` returns market data and the note "no TP/SL".
  - **Validator** `validateAgentAnswer`. It rejects:
    - EMPTY or TOO_LONG answers
    - JARGON (GM-xx, canonical, UNKNOWN, INSUFFICIENT_EVIDENCE, tool names)
    - CLAIMS_EXECUTION (first-person "I turned it off")
    - **TRADE_PICK** (leverage figures, `20x`, حد ضرر/حد سود/stop loss/take profit followed by a number)
    - **NEW_NUMBER**: every number must appear in tool output, the user message or earlier assistant turns. Persian and Arabic digits and separators are normalized; rounded and هزار/میلیون/میلیارد/تریلیون scaled forms are accepted; 0–10 is always allowed.
  - One corrective round: a rejected draft goes back to the model with an internal Persian reason (`correctionFa`). A second rejection means fallback.
  - Breaker: 3 failures → open 60 s; auth, quota or credential failure → open 10 min.
  - `systemPrompt` (Persian): PAPER_ONLY, tools-first, admit stale data, trading-advice policy (analysis/paper only, not a personal signal, no invented leverage/TP/SL or tokens outside tool output), commands only via `propose_*`, «stop loss» ≠ stop engine, no secrets/authority changes.
- `architecture/ai/gemini_chat.py` (new)
  - One `generateContent` step with `tools.functionDeclarations` and `toolConfig AUTO`. Key read here only (Credential Manager `AHOS/ai/gemini`, read-only), same rules as the phraser.
  - Model parts are relayed verbatim, so Gemini 3 thought signatures survive; `thought` parts are dropped.
  - Two models, 4 s each, 9 s total budget. No retry on AUTH, QUOTA or BLOCKED.
  - `gemini_phraser.py` gained `call_model_payload`. `gemini_phraser.ts` gained `spawnPythonJson`, with a module whitelist `HELPER_MODULES`.
- `chat_actions.ts` (new)
  - Owner check `isOwner`:
    - Telegram user_id must be in `TELEGRAM_ADMIN_USER_IDS` ∪ `TELEGRAM_ALLOWED_CHAT_IDS`. If both are empty, nobody qualifies.
    - Channel `web`/`dashboard` counts as the owner (same bearer token as the dashboard buttons).
    - `api` or any other channel is not the owner.
  - `PendingActionStore`: 6-character code from an unambiguous alphabet, 5-minute TTL, single use, bound to the proposer's identity, in memory.
  - `parseConfirmation`: whole message only. `تایید|تأیید|تائید|confirm|yes CODE` confirms; `لغو|کنسل|cancel|انصراف [CODE]` cancels. A bare «تایید», «بله» or «stop loss» is never a confirmation.
  - `handleConfirmation` checks identity, owner, expiry and single use, then executes through the **same functions as the dashboard routes**:
    - `engine.startEngine` / `stopEngine` (= `/api/engine`)
    - `engine.addWatch`
    - paper buy = `paperAllowedFromCanonical` + `addPaper` (= `/api/paper`; the Canonical Decision Authority still decides)
  - Every step is appended to the hash-chained control audit with surface `chat_confirm`. Decisions: PROPOSED / CONFIRMED / CANCELLED / EXPIRED / DENIED / FAILED.
- `chat_memory.ts` (new): per-conversation memory keyed by `sha256(channel|userId)`. Last 10 exchanges, 6 h TTL, 200 conversations max, secrets redacted (API keys, Telegram tokens, JWTs, private keys, Bearer, PEM, `*_TOKEN=`). In memory only.
- `chat_control_gate.ts`: `Capability` adds `WATCH_WRITE`; the audit gains the `chat_confirm` surface and the new decision values. The gate function and the non-owner refusal are unchanged.
- Plumbing:
  - `ChatResponse.pendingAction` → `conversation_gateway` → `/api/chat` `pending_action {code, kind, summaryFa, expiresAt}`.
  - `CommandCenter.tsx`: multi-turn chat display (unchanged) plus **تایید / لغو buttons** under a proposal. They send `تایید CODE` / `لغو CODE`.
- Tests:
  - `scripts/chat_agent_selftest.ts` (`npm run test:chat-agent`): 23 cases with a fake runner, no network, temp audit path.
  - `tests/test_gemini_chat.py`: 5 cases.
  - `tests/test_gemini_phraser.py` and `tests/test_telegram_reply_presentation.py`: static pins updated.

**Env (none set in `.env`):**
- `AHOS_CHAT_AGENT=off` disables the agent (back to 7a deterministic replies).
- `AHOS_GEMINI_MODELS` is shared with the phraser.
- `AHOS_CHAT_AGENT_TIMEOUT_MS`: per-attempt timeout, default 4000.

**Tests (Windows, 18:00–18:20 Tehran):**
- tsc exit 0; eslint 0 on all touched files.
- npm: chat-agent 23/23; chat-intent 52/52; chat-reply-format 40/40; gemini-phraser 12/12; chat-control-gate 126/126.
- pytest gemini/telegram/canonical/provider set: 230 passed, 2 skipped.

**Live check** via gateway `127.0.0.1:3500/api/chat`, model `gemini-flash-lite-latest`, 2.5–7 s per reply. Verbatim replies are in the final Phase 7 report. Summary:
1. «قیمت بیت کویین الان چقدر هست؟» → `get_market` → BTC ۷۹٬۷۳۲ دلار, +۰٫۱۵٪, «داده‌ها قدیمی هستند… ۳۵ روز پیش».
2. The futures/leverage/TP/SL request → `list_opportunities` → "paper/analysis only, no signal/leverage/TP/SL; no token has an approved verdict", plus a risk warning.
3. A 3-turn free conversation (market mood → lowest-risk opportunity → «چرا؟») was answered from tools with context carried over.
4. «موتور تحلیل رو خاموش کن» → `propose_engine_stop` → proposal with code → «لغو CODE» → «لغو شد… هیچ تغییری اعمال نشد.»
   - Audit lines: PROPOSED, then CANCELLED.
   - The engine was already off; nothing executed.
5. A non-owner Telegram id got «⛔ این دستور فقط برای مالک سیستم مجاز است» (audit DENIED NOT_OWNER).
6. «stop loss بیت کوین رو کجا بذارم؟» was answered as analysis only, with no stop and no number.

**Open items (Phase 7):**
- Telegram has no inline confirm buttons; it confirms by text «تایید CODE». The dashboard has buttons.
- The pending store and memory are in memory, so a gateway reload drops them. This is the safe default; dropped proposals simply expire.
- Anyone holding `AHOS_WEB_API_TOKEN` can claim channel `web` and therefore owner. This is the same exposure as `/api/engine` and `/api/paper`.
- `TELEGRAM_ADMIN_USER_IDS` is empty in `.env`, so Telegram owner identity currently comes from `TELEGRAM_ALLOWED_CHAT_IDS` (the owner's private chat id equals his user id).
- Latency is about 5 s for tool answers (2 model calls plus 2 Python spawns). A long-lived helper would cut about 1 s per call.
- The agent reads the snapshot taken at message time; market data is 35 days old because the engine is off (the model says so).
- GM-04 owner-authority change and GM-12 Credential Manager read path still need **سپهر/قاسم/رضا review**.
<!-- PHASE7:END -->

<!-- PHASE6:START -->
## Phase 6 (2026-10-02, Grok): Gemini reply phraser behind the ReplyPhraser seam

**Pushes are still paused by the owner: local commits only.** Full continuation notes for Claude: `reports/grok/CLAUDE_CONTINUATION_GUIDE.md`.

### What was built
- **Read-only Windows Credential Manager backend** (owner-approved; GM-12 independent review still pending):
  - `architecture/ai/wincred_reader.py`: CredReadW, `AHOS/ai/*` targets only, buffer zeroed before CredFree.
  - `architecture/ai/credential_store.py`: `WindowsCredentialManagerStore` now reads instead of raising NotImplementedError; adds `CredentialUnavailable`.
  - Details in the GM09 doc, section "Phase 6 update".
- **`architecture/ai/gemini_phraser.py`:** a Python helper run as `python -m architecture.ai.gemini_phraser`.
  - It reads the key in-process from `AHOS/ai/gemini` and calls `generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` with the `x-goog-api-key` header.
  - It tries at most 2 models, with 4 s per attempt and a 9 s total budget.
  - A follow-up attempt is skipped on AUTH, QUOTA or BLOCKED.
  - Errors are classified through `provider_status.classify_provider_error`.
  - The output JSON on stdout carries no key, and a key literal is scrubbed from any error detail.
- **`gemini_phraser.ts`:** `GeminiPhraser implements ReplyPhraser`.
  - It spawns the helper with no shell and fixed argv. The env is minimal (no `DATABASE_URL` or tokens), with `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`. Stdin and stdout are UTF-8.
  - The circuit breaker opens for 60 s after 3 failures, and for 10 min after one AUTH, QUOTA, NO_CREDENTIAL or NOT_WINDOWS failure.
  - Drafts that contain links (news) are skipped.
  - It strips a model-written footer and markdown, then appends the footer itself.
  - `getDefaultPhraser()` is the singleton.
- **`response_composer.ts`:** `phrasedHtml()`.
  - Accepted phrased text is escaped line by line; the only markup is `<b>` on a short title and `<i>` on the footer.
  - Any HTML supplied by the phraser is ignored.
  - `validatePhrased` is unchanged: no new numbers, no jargon, footer exactly once, length limit.
- **`chat.ts`:**
  - The normal-reply `finalizeReply(..., getDefaultPhraser())` call now gets the phraser.
  - **The GM-04 refusal call is still `locked: true` with no phraser.**
  - Evidence gains `phraser {used, rejected, reason, model, latencyMs}`.
- **Config (env):**
  - `AHOS_PHRASER=off` disables the phraser. The default is on, and it falls back to deterministic text if the key or network is missing.
  - `AHOS_GEMINI_MODELS` (default `gemini-flash-lite-latest,gemini-3.5-flash-lite`; at most 2 are used)
  - `AHOS_PHRASER_TIMEOUT_MS` (default 4000)
  - `AHOS_PHRASER_PYTHON`
  - None of these are in `.env`, and `.env` was not edited.

### Tests (self-tests, not independent verification)

**Windows**
- `tests/test_gemini_phraser.py` + `tests/test_ai_provider_status.py`: 78 passed, 2 skipped (two non-Windows-only tests).
- The earlier set with telegram_reply_presentation, chat_control_gate_static and canonical_read_model: 112 passed, 2 skipped.
- npm selftests:

  | Suite | Result |
  |---|---|
  | `test:gemini-phraser` (new) | 12/12 |
  | chat-reply-format | 40/40 |
  | chat-control-gate | 126/126 |
  | web-api-auth | 9/9 |
  | canonical-read-model | 13/13 |
  | canonical-security | 19/19 |
  | alert-banner | 8/8 |
  | dashboard-truth | 34/34 |

- `tsc --noEmit`: 0 errors. eslint: clean.

**Box**
- Full pytest suite: 2636 passed, 3 failed. All 3 failures are pre-existing or environmental:
  - `test_doc_drift` and `test_evidence_package` doc-drift (blocker A)
  - `test_sqlite_backup_restore::...relative_executable` (a Windows path on Linux)
- Phase 6 tests after the timeout tweak: 80 passed.
- `validate_imports`: PASSED.

### Live evidence (laptop, 2026-10-02, Tehran time)
- **Direct helper:** 3 consecutive calls OK, about 1.1 s model latency each.
  - Example: input draft «📊 وضعیت بازار / • بیت‌کوین: ۶۴٬۲۰۰ دلار (۲۴ساعت: +۱٫۲٪) / • اتریوم: ۳٬۱۰۰ دلار / • حال کلی بازار: نامشخص»
  - Output: «وضعیت بازار ارزهای دیجیتال / • بیت‌کوین: ۶۴٬۲۰۰ دلار (۲۴ساعت: +۱٫۲٪) / • اتریوم: ۳٬۱۰۰ دلار / • حال کلی بازار: نامشخص»
  - All numbers were kept. Persian UTF-8 round-tripped intact.
- **Node-spawned helper** (the same runner the gateway uses): 3/3 OK, about 2.0 s end to end (about 0.9 s is Python spawn).
- **The one live gateway smoke** (17:21 Tehran, POST «بازار چه خبر؟» to 127.0.0.1:3500/api/chat):
  - HTTP 200 in 9.3 s, `intent=market`.
  - Evidence: `phraser {used:false, rejected:NO_OUTPUT, reason:NETWORK, latencyMs:7676}`.
  - The deterministic reply was returned correctly (the fallback worked). It wrote the normal 2 chat rows.
  - Cause: the first connection through the owner's local proxy (`127.0.0.1:10809`, registry proxy) stalled for more than 5 s after an idle period. The first direct run showed the same stall; every later run was about 1.1 s.
  - Mitigation committed: 4 s per attempt and a 9 s total budget, so a stalled first attempt leaves a full second attempt. Attempts now record `error_kind` (exception class only).
  - **A phrased reply through the live gateway has NOT been observed yet** (one-smoke limit). Next chat messages will show `evidence.phraser.used`.
- **Processes:** the gateway was not restarted; Next hot-reloaded `chat.ts` and `gemini_phraser.ts`. The bot was not restarted (no Python Telegram change). The owner's own `scripts/store_ai_key.py` process (PID 15216, untracked owner script) was left alone.
<!-- PHASE6:END -->

<!-- PHASE5:START -->
## Phase 5 (2026-10-02, Grok): Telegram/chat reply presentation cleanup (presentation only)

**Pushes are still paused by the owner: local commits only.**

### Trigger

The owner ran the live G11 test (`reports/telegram_e2e/telegram_e2e_20261002T1221Z.md`). Refusals worked and the audit returned CHAIN_OK, but the replies were cluttered:
- internal "GM-04" text
- a news dump instead of a market summary for «بازار چه خبر؟»
- filler text, «0 حکم BUY کانونیکال»
- the engine-off notice on every reply

### What changed (wording and format only)

**No change to:**
- decision, authority or canonical logic
- the GM-04 gate behaviour (it still always refuses; the selftest is unchanged at 126/126)
- data sources
- PAPER_ONLY

**New modules**
- `reply_format.ts` (pure): block model with `renderPlain`, `renderTelegramHtml` and `escapeHtml`.
  - Only http(s) links are kept.
  - Replies are cut at whole blocks within a 3600-character budget, so they stay under 4096 and the HTML stays balanced.
- `chat_replies.ts` (pure): reply builders.
  - Persian labels replace raw enum codes.
  - Missing values show «نامشخص» or a single «داده کافی نیست» note.
  - No internal ids in user text.

**Routing and notices in `chat.ts`**
- `chat.ts` keeps routing; the pinned function names are kept as thin wrappers.
- «بازار چه خبر؟» now routes to **market**: BTC/ETH/SOL price and 24h change first, then the market mood, fear and greed, and data age with a staleness flag. At most 3 Persian headlines follow.
- News: at most 5 items, one line each, original source plus link.
  - Half-translated titles fall back to the original title, with one note.
  - No English summary, importance or classification dump.
- New `stop_loss` intent (presentation routing only): asks which token, shows only the recorded invalidation condition, never invents a number.
- The general fallback is a short "didn't understand" line plus suggestions; the filler text is gone.
- The engine-off notice now appears only for help/greeting, opportunities, health, or questions that mention the engine.
- The footer «تصمیم نهایی با کاربر است.» appears once per reply.

**Refusal text**
- `chat_control_gate.ts`: refusal text shortened to «⛔ … غیرفعال است. … هیچ تغییری اعمال نشد.» with no "GM-04".

**Telegram HTML path**
- `conversation_gateway.ts`, `types.ts` and `app/api/chat/route.ts` add an optional `answer_html` field.
- The dashboard keeps using plain `reply`/`answer`.

**Telegram bot**
- `telegram_ai/service.py` and `bot.py` send `answer_html` with `parse_mode=HTML`.
- They fall back to plain text when the HTML is missing, longer than 4096, or rejected by Telegram (an HTTP 400 parse error).
- Plain text is clamped to 4096 with the footer kept.
- The gateway-unavailable path is unchanged (plain).

### Shared response composer and the future LLM seam

The owner wants to back replies with a free AI model later, using the same style on Telegram and the Windows dashboard. This phase prepares for that without implementing it.

**One composer for every chat surface: `response_composer.ts`**
- Dashboard chat reads `reply` from `/api/chat`; Telegram reads `answer_html`. Both come from the same `finalizeReply()` call in `chat.ts`.

**Pipeline**
1. Verified snapshot / read-model data.
2. `chat_replies.ts` builders turn it into `ReplyBlock[]` (grounded facts only).
3. These become a `GroundedDraft {intent, blocks, footer, locked?}`.
4. `finalizeReply(draft, phraser?)` produces a `ComposedReply {plain, html, composer}`.

**House style**
- `RESPONSE_STYLE_FA` holds the shared rules. It is meant to become the future LLM prompt's style section, so the deterministic output and any LLM output follow the same rules.

**The seam**
- `interface ReplyPhraser { name; phrase(draft, deterministic, style) }`. **None is configured today**, so the deterministic text is final, and `evidence.composer = "deterministic"`.
- A future phraser may only *rewrite the grounded draft*. Its output is accepted only if `validatePhrased()` passes:
  - not empty and within the length limit
  - footer exactly once
  - no jargon (GM-xx / canonical / UNKNOWN)
  - **no number that is not in the deterministic draft**
- Otherwise the deterministic text is used, and the rejection reason is recorded in `phraserRejected`.
- Phraser output is treated as untrusted: its HTML is rebuilt by escaping.
- `locked: true` drafts (the GM-04 refusals) are never rephrased.
- The phraser never decides anything and never sees credentials.

**To add an LLM later (not done)**
1. Implement `ReplyPhraser` using the GM-09 provider status / credential-store interfaces (free model, with a timeout).
2. Pass it into the two `finalizeReply` calls in `chat.ts`, behind an off-by-default flag.
3. Keep the deterministic composer as the fallback.
4. Add evals.
5. Independent review is required before enabling.

### Tests (self-tests, not independent verification)

**npm selftests**

| Suite | Result |
|---|---|
| `test:chat-reply-format` (new) | 40/40: snapshot, escaping, 4096 limit, jargon scan, no fabricated digits when data is missing, stale flag, intent helpers, composer and phraser-seam guard |
| chat-control-gate | 126/126 |
| web-api-auth | 9/9 |
| canonical-read-model | 13/13 |
| canonical-security | 19/19 |
| alert-banner | 8/8 |
| dashboard-truth | 34/34 |

**Other checks**
- `tsc --noEmit`: 0 errors. eslint on the changed files: clean.
- pytest: the new `tests/test_telegram_reply_presentation.py` (11) plus the static, canonical, config, one-brain, all Telegram, engine-import-safety, web-api-auth and dashboard-truth sets: **281 passed, 1 xfailed**.
- `validate_imports --imports-only`:
  - **Box mirror (identical tree): PASSED**, 242 modules, no evidence mutated.
  - **Windows run: FAILED** its evidence-mutation check. That run started at 12:36:10Z. During it, the bot restart created `reports/telegram_e2e/bot_*_20261002T123754Z.log`, the empty logs from the intermediate start were deleted, and two docs were deployed. The check blamed `telegram_ai.envelope`, which writes no files. This is a timing artefact, not an import side effect.
  - The Windows run was not repeated: it takes about 47 minutes under load.

### Runtime

- The gateway (`next dev`, 127.0.0.1:3500) hot-reloaded. Verified with a local POST «توقف»: the new short refusal came back with `answer_html` and the decision was REFUSED. That POST was refused before any DB access; it appended one audit line.
- **Telegram bot restarted (only the bot):**
  - Old PIDs 13096/8500 were stopped with `taskkill` (non-forced; the parent accepted the signal and the child exited with it).
  - The bot was started hidden via `Start-Process`, with `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1` (added so the logs are visible) and `AHOS_GATEWAY_URL=http://127.0.0.1:3500/api/chat`.
  - Logs: `reports/telegram_e2e/bot_{stdout,stderr}_20261002T123754Z.log`.
  - An intermediate start at 12:36:39Z (buffered, empty logs) was stopped and its empty logs removed.
- `.env` unchanged.
<!-- PHASE5:END -->

<!-- PHASE4:START -->
## Phase 4 (2026-10-02, Grok): GM-04 conservative capability gate and G11 live-E2E runbook

**Pushes are still paused by the owner: local commits only.** Claude/reviewers: `git log origin/ahos..ahos`.

### What changed

GM-04 was implemented in its capability-reducing form. It **only removes capability**. Status: IMPLEMENTED/TESTED (self-tests only), **PENDING INDEPENDENT REVIEW by سپهر/قاسم/رضا**.

**Start/stop matching**
- `chat.ts` start/stop detection is now **whole-message explicit commands** (`chat_control_gate.ts` `detectControlCommand`).
- "stop loss", "stoploss", "start-up", "restart", "توقف ضرر" never match.
- `paper_buy` needs an explicit phrase; a bare "paper" no longer counts.

**Refusal on `/api/chat`**
- `/api/chat` refuses `start`, `stop` and `paper_buy` for **every** channel, with a Persian reply.
- The client `channel` field is never a grant: it is recorded as `channel_claimed` only.
- `startEngine`/`stopEngine` were removed from `chat.ts`.
- Reason: the chat path cannot prove the local dashboard (shared bearer, client-asserted channel). See the GM04 doc §7.

**Documented dashboard change**
- Dashboard *chat* typing «شروع/توقف/خریدم» is now refused and points to the buttons. It was equally exposed.
- The dashboard **buttons** (`/api/engine`, `/api/paper`) are unchanged. `/api/engine` start/stop now writes an ALLOWED audit line.

**Audit**
- Append-only, hash-chained JSONL with hashed ids and no raw text.
- Location: `data/control_audit/chat_control_audit.jsonl` (override `AHOS_CONTROL_AUDIT_PATH` / `AHOS_DATA_DIR`).
- Verify with `npm run audit:control-verify`.

**Other**
- `conversation_gateway.ts` forwards `channel`/`user_id` into ChatContext, for the audit only.

### Tests (self-tests, not independent verification)

**On Windows (node 24):**
- npm `test:chat-control-gate`: 126/126. Covers:
  - the negative/positive matrix
  - case, fullwidth (NFKC), zero-width, bidi and Arabic-letter variants
  - Persian phrases
  - spoofed channels (web/local/dashboard/null/injection)
  - replay
  - tamper and deletion detection
  - torn tail
  - sink failure staying fail-closed
- Other npm selftests:

  | Suite | Result |
  |---|---|
  | web-api-auth | 9/9 |
  | canonical-read-model | 13/13 |
  | canonical-security | 19/19 |
  | alert-banner | 8/8 |
  | dashboard-truth | 34/34 |

- `tsc --noEmit`: 0 errors. eslint on the changed files: clean.
- pytest: `test_chat_control_gate_static` plus the canonical, config, one-brain, Telegram (offline harness / adapter / service / launcher / ai / conversational / html / NLU matrix), engine-import-safety, web-api-auth and dashboard-truth sets: **271 passed, 1 xfailed**.
- `scripts/validate_imports.py --imports-only`: **VALIDATION PASSED** (242 modules, no evidence mutated).

**On the box (python 3, bun):** the same pytest sets gave 250 passed, 1 xfailed (subset without canonical/config). The selftest also ran under bun: 126/126.

### Files

| Status | Files |
|---|---|
| New | `chat_control_gate.ts`, `scripts/chat_control_gate_selftest.ts`, `scripts/verify_control_audit.ts`, `tests/test_chat_control_gate_static.py`, `reports/grok/G11_LIVE_E2E_RUNBOOK.md` |
| Modified | `chat.ts`, `conversation_gateway.ts`, `app/api/engine/route.ts`, `package.json`, GM04 doc, MISSION_DISCOVERY |

### Runtime

- No `run_bot.py` is running.
- The gateway (`next dev`, 127.0.0.1:3500) hot-reloads `chat.ts`.
- Live E2E: **OWNER_ACTION_REQUIRED**. Follow `reports/grok/G11_LIVE_E2E_RUNBOOK.md`. Its port override is the bot-session `$env:AHOS_GATEWAY_URL="http://127.0.0.1:3500/api/chat"`; `service.py` ignores `AHOS_GATEWAY_PORT`. `.env` is unchanged.

### Residuals for review

1. Any holder of `AHOS_WEB_API_TOKEN` can still call `/api/engine` (GM-04 phase 2: loopback check / second secret).
2. The chat `watch` intent (watchlist write) is ungated (out of scope).
3. `AHOS_CONTROL_AUDIT_PATH` is not in the config-validation scan list.
4. Blocker A (`test_doc_drift`, Claude) is unchanged.
<!-- PHASE4:END -->

<!-- PHASE3:START -->
## Phase 3 status (Grok, 2026-10-02, foundation missions): read this first

**PUSHES ARE PAUSED BY OWNER INSTRUCTION (2026-10-02 14:52 Tehran).** Everything after `a6638bf` exists **only as local commits** on branch `ahos` in `G:\robat\ahos`; none of it is on GitHub. Claude: review these with `git log origin/ahos..ahos`. Do not assume `origin/ahos` is current, and do not push them yourself unless the owner says so.

Same constraints as Phase 2. Every commit was preceded by a fetch with fast-forward only and staged by explicit path. P3-M1 (`a6638bf`) was pushed and checked for HEAD == @{u}. Later commits are local only.
- PAPER_ONLY.
- Lane A frozen.
- Canonical Decision Authority untouched.
- Hooks overlay and `ahos-guard.py` untouched.
- None of Claude's files touched.
- No `.env` edits.
- No Postgres writes.
- No service started or stopped.

Self-tests are **not** independent verification. The reality ladder for each item is in `reports/grok/PHASE3_ARCHITECTURE_NOTE.md`.

Blocker A (for Claude) is still open. See the Phase 2 note below.

| Mission | Status | Ladder | Commit |
|---|---|---|---|
| P3-M1 tsconfig exclude `docs/archive` | IMPLEMENTED_VERIFIED (self-tests) | TESTED | `a6638bf` (pushed) |
| GM-08 mission/engineering ledger | IMPLEMENTED_VERIFIED (self-tests) | IMPLEMENTED + TESTED (not INTEGRATED) | `d1571c4` (local, not pushed) |
| GM-09 AI provider status model | IMPLEMENTED_VERIFIED (offline self-tests); credential store interface only; Windows Credential Manager backend DESIGN_ONLY | IMPLEMENTED + TESTED (not INTEGRATED) | local commit adding `architecture/ai/provider_status.py` (not pushed) |

### P3-M1: tsconfig
- `tsconfig.json`: `"docs/archive"` was added to `exclude`. That is the only change.
- `tests/test_tsconfig_archive_exclusion.py` checks two things: the exclusion and the existing excludes are still present, and no live TS file imports from `docs/archive`. The negative check was confirmed: a planted import makes the test fail.
- Evidence (Windows, node 24):
  - Before and after, `tsc --listFilesOnly` differs by exactly 7 files, all under `docs/archive/consolidation_2026-09-26/ahos022_divergent/`. No other file changed.
  - `tsc --noEmit`: exit 0, **0 errors** (it was 9).
  - npm selftests: web-api-auth 9/9, canonical-read-model 13/13, canonical-security 19/19, alert-banner 8/8, dashboard-truth 34/34.
  - pytest: tsconfig + canonical_decision_authority, 31 passed.

### GM-08: mission/engineering ledger (`architecture/mission/ledger.py`, CLI `scripts/mission_ledger.py`)
- **Inspected first; no duplicates created:**
  - `scripts/execution_state.py` (M5) is a read-only session-start state recorder. It is not a mission ledger.
  - `ahos_org/audit.py` + `ahos_org/tasks.py` are the hash-chained audit and task lifecycle of the org *policy model*. The ledger reuses their hash convention (sha256 over canonical JSON, a genesis hash of 64 zeros), but does not import from or extend governance.
  - No other ledger, checkpoint or resume code exists.
  - The four agent taxonomies are **referenced, not merged**. `CURRENT_AGENT` must be namespaced as `engineering:*`, `agent:*`, `AG:*`, `AGENT:*`, `agent.org:*` or `M0:*`, and a bare "01" is rejected. Every entry carries `agent_taxonomy_ref = docs/governance/agent_taxonomy_map.json`.
- **Storage:**
  - A local append-only JSONL at `<AHOS data dir>/mission_ledger/mission_ledger.jsonl`, written with O_APPEND + fsync. Database paths are refused.
  - No existing DB is read or written.
  - Resolving the default path creates nothing. The ledger has **not** been seeded on the laptop, so no file exists yet.
- **Fields:** the 13 required fields. Each line is a full state snapshot; unknown fields are rejected.
- **States:** PENDING, RUNNING, PAUSED, WAIT_FOR_AI, BLOCKED, RESUMED, COMPLETED_UNVERIFIED, FAILED, CANCELLED, with a legal-transition table.
  - There is **no DONE or COMPLETED state**. Verification goes in LAST_VERIFICATION.
  - Terminal states cannot be reopened.
- **Checkpoint and resume:**
  - `checkpoint()` stores up to 64 KB of JSON.
  - `pause()` moves to PAUSED, WAIT_FOR_AI or BLOCKED.
  - `resume()` returns the stored checkpoint unchanged and cannot reset it.
  - `start()` refuses an existing id, so a mission is never restarted from zero.
  - After a crash: `resume(crash_recovery=True)`.
  - A torn final line (crash mid-write, including a record cut just before its newline) blocks appends until `recover_torn_tail()` appends a hashed acknowledgement of the torn line's sha256. Nothing is rewritten, and the unconfirmed write is not trusted.
- **Tamper evidence:**
  - `seq` + `prev_hash` + `entry_hash` detect a modified, re-hashed, deleted, swapped, duplicated, blank or garbage line. The ledger never appends onto a broken chain.
  - Limit: a keyless chain cannot detect a *whole-file* rewrite. Record `head_hash` externally and check it with `verify(anchor_hash=...)` or the CLI `--anchor`; this is tested.
- **Secrets:**
  - Secret-looking content in keys and values is redacted **before hashing**. Covered patterns: OpenAI/Anthropic/xAI/Groq/GitHub/Google/AWS/Slack keys, Telegram tokens, JWTs, EVM keys, URL credentials, Bearer tokens, `*_KEY=`/`password:` assignments, and PEM private keys. Redaction is idempotent.
  - `strict=True` rejects the write instead, and writes nothing.
  - A secret-looking MISSION_ID is refused.
  - Over-redaction of benign `token=...` text is possible by design.
- **Not an authority:**
  - `authority: "NONE"` on every entry.
  - Static tests confirm the ledger imports no decision, trading or telegram code, and that nothing in decision/risk/positions/scoring/paper_trading/discovery/engine imports it.
- **Tests:** `tests/test_mission_ledger.py`, 72 cases.
  - Box: 72 passed.
  - Box regression set (architecture graph, zero-money, config validation, boundaries, architecture_p1, engine import safety, agent taxonomy, phase12): 183 passed, 1 xfailed.
  - Box `validate_imports`: PASSED.
  - Windows: `test_mission_ledger` + `test_agent_taxonomy_map`: 92 passed (72 + 20).
- **Next:** wire GM-09 provider status into the ledger (pause with a checkpoint). Optionally, Claude and Grok record missions here.

### GM-09: AI provider status + credential-store abstraction (details: `reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md`)
- **Inspected first:**
  - `architecture/ai/clients.py` (`AIResponse`: OK, DOWN, NO_KEY, SKIPPED_PAID) and `architecture/ai/router.py`.
  - The market-data provider statuses (`types.ts` `PROVIDER_STATUSES`, `architecture/providers`) are a separate vocabulary and were **not changed**.
  - GM-09 is additive.
- **`architecture/ai/provider_status.py`:**
  - The seven-state `AIProviderStatus` and `classify_provider_error`: 401/403 → AUTH_FAILED (geo 403 → BLOCKED); 402/429/quota text → QUOTA_EXHAUSTED (an explicitly transient 429 → DEGRADED); 404/model text → MODEL_UNAVAILABLE; 5xx/timeout/network → UNAVAILABLE.
  - `classify_ai_response` for the existing envelopes.
  - `safe_provider_call`: an outage never crashes the runtime.
  - Error detail is redacted.
- **`architecture/ai/credential_store.py`:**
  - The interface has no raw getter. `SecretValue` never prints its value and cannot be pickled.
  - Null and Fake stores.
  - `WindowsCredentialManagerStore` = DESIGN_ONLY: it refuses every access and imports nothing OS-level.
  - The Persian new-key message tells the owner to use Credential Manager target `AHOS/ai/<provider>`, and never to paste the key in chat, Telegram or .env.
- **`architecture/ai/mission_guard.py`:**
  - QUOTA_EXHAUSTED / AUTH_FAILED → the ledger mission is PAUSED with its checkpoint kept and an owner message is returned.
  - Outage → WAIT_FOR_AI.
  - READY → RUNNING.
- **Tests:** `tests/test_ai_provider_status.py`, 64 cases.
  - Fake providers and fake transports only, with a socket guard.
  - Box: 64 passed. AI/provider regression set: 327 passed, 1 xfailed. `validate_imports`: PASSED.
  - Windows: GM-09 + ledger + ai_council_live + ai_router_and_debate + provider_abstraction: 168 passed. `validate_imports --imports-only`: PASSED.
  - Mutation checks: disabling the credential-pause branch makes 4 tests fail; removing redaction makes 1 fail.

### Remaining blockers (Phase 3)
1. **Blocker A** (Claude): two untracked artifacts are cited by canonical docs, so `test_doc_drift` fails on a clean checkout. Unchanged.
2. **Pushes paused** (owner instruction). Commits `d1571c4` and the GM-09 commit exist only locally.
3. GM-04 still waits for security review. That includes the `stop` regex false positive.
4. The gateway port choice is OWNER_ACTION (.env says 3000, the listener is on 3500). G11 live Telegram E2E is OWNER_ACTION.
5. The Windows Credential Manager backend needs owner + security review (GM-12) before any OS credential access. GM-09 runtime wiring (calling `guard_provider_call` from the council or router) is not done.
6. Wall-clock items are unchanged.

### Next recommended missions
- Wire `guard_provider_call` / `classify_ai_response` into `LiveCouncil` as advisory status reporting.
- Seed the ledger with real Claude and Grok missions; record `head_hash` in the handoff.
- GM-12 review.
- GM-04 implementation after review.
- GM-01 (Claude).
<!-- PHASE3:END -->

<!-- PHASE2:START -->
## Phase 2 status (Grok, 2026-10-02, implementation): read this first

**Note for Claude about blocker A (still open, not touched by Grok):** your commit `25b33cc` makes the canonical docs cite `reports/nightly_backup_series.json`. That file is **untracked** in the working tree on this laptop. `scripts/doc_drift.py::_exists` checks the working tree, so the test passes here.

**Confirmed in Phase 2:** on a clean clone of `origin/ahos` (Grok's box), `tests/test_doc_drift.py::test_canonical_docs_have_zero_real_stale_refs` **FAILS** with 2 stale references in `AHOS_GAP_REGISTER.md`:
1. `reports/nightly_backup_series.json` (25b33cc)
2. `reports/validate_imports_run_20260928T045640Z.json`, cited since `7ebea7a` (M-GAP-037). It is also untracked (`??`) on the laptop.

You need to choose one fix (GM-01):
- (a) commit both artifacts, or
- (b) give doc_drift "exists-but-untracked" semantics or an exemption.

Grok has not touched `scripts/doc_drift.py`, the artifacts, `AHOS_GAP_REGISTER.md`, or any of your dirty or untracked files.

Constraints held in every Phase 2 commit:
- PAPER_ONLY.
- Lane A frozen.
- Canonical Decision Authority untouched.
- `.cursor/hooks.json` overlay and `ahos-guard.py` untouched.
- `.env` and the pgdump file not committed.
- No secrets.
- No DB writes.
- No service started or stopped.
- Files staged by explicit path only.

Self-tests are **not** independent verification.

| Mission | Status | Commit |
|---|---|---|
| GM-02 Telegram offline edge harness | IMPLEMENTED_VERIFIED (offline/self-test only); live E2E = LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED | `552eda7` |
| GM-03 dashboard truthfulness | IMPLEMENTED_VERIFIED (self-tests; presentation only; browser view not visually checked) | `789dfa2` |
| GM-05 gateway port single source + diagnosis | IMPLEMENTED_VERIFIED (self-tests + one real read-only diagnosis run); port choice = OWNER_ACTION_REQUIRED | `06e44e6` |
| GM-06 n8n validator + ahos_03 quarantine | IMPLEMENTED_VERIFIED (static self-tests); ahos_03 QUARANTINED (file kept) | `8e48cf3` |
| GM-04 Telegram control capability gate | DESIGN_ONLY: `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`, awaiting security review (سپهر/قاسم/رضا) | the docs commit that adds that file |

### GM-02: what changed
- `telegram_ai/envelope.py` (new, pure, no network or authority imports):
  - versioned update envelope `ahos.telegram.update_envelope.v1`
  - `hash_identifier` (sha256 prefix)
  - `redact_envelope` (removes raw chat_id/user_id)
  - `ReplayGuard` (bounded LRU of update_ids: ACCEPT / DUPLICATE / INVALID)
  - `TelegramAuditLog` (in-memory, plus an optional append-only JSONL; hashed ids, length and sha of the text, **never raw text**)
- `telegram_ai/bot.py`:
  - new optional `replay_guard` and `audit_log` constructor arguments. Defaults keep the old behaviour, plus a default in-memory guard and log.
  - Duplicate and invalid update_ids are rejected before auth, rate-limit or gateway are touched.
  - Every exit path is audited: PROCESSED, UNAUTHORIZED, RATE_LIMITED, DUPLICATE_REJECTED, INVALID_UPDATE_REJECTED.
  - The context passed to the service now carries `user_id`. This fixes the empty `user_id` that `service.py:84` forwarded to the gateway; `service.py` itself is unchanged. The caller's dict is not mutated.
- `telegram_ai/adapter.py`: `MockTelegramAdapter` update_ids are now monotonic. Before this, ids restarted at 1 after a poll, which the new replay guard would have rejected.
- `tests/test_telegram_offline_harness.py` (new): 20 test functions, 28 cases.
  - Covers the end-to-end path MockTelegramAdapter → TelegramBotRunner → TelegramDomainService → stub HTTP gateway on 127.0.0.1 (no proxy, no credentials).
  - Checks: envelope contract, sender identity in the gateway body, fail-closed empty allowlist, unauthorized rejection with no gateway call, rate-limit, duplicate and invalid update_id rejection, audit with no raw text and no raw ids, JSONL append-only, offline fallback when the gateway is down, non-PAPER mode not echoed.

### GM-02: tests (Windows `.venv` Python 3.11.9, plus box)
- Telegram suites + `test_run_bot_launcher` + `test_engine_import_safety`: **203 passed, 1 xfailed** (Windows, 255 s; same on box).
- `validate_imports.py --imports-only`: PASSED on Windows. Full `validate_imports.py` PASSED on box (pre-existing orphan warnings only).
- Mutation checks:
  - removing identity propagation → 2 harness tests fail
  - disabling the replay check → 9 fail

### Current reality / blockers / next
- Live Telegram E2E (G11) stays **LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED**. The running bot only picks this up after the owner restarts it; Grok restarted nothing.
- The Telegram → `chat.ts` start/stop free-text control leak is **still open**. See GM-04 (design only).
- Next: GM-03.

### GM-03: what changed (presentation only, no authority)
- `dashboard_truth.ts` (new, pure, no imports):
  - `freshnessStatus`: OK only for a real timestamp within the limit. Missing, NaN or a >1 min future timestamp → UNKNOWN; too old → STALE.
  - `evidenceFreshnessLimitMs`: the larger of 10 min and 3× the engine interval.
  - `executionModeStatus`: PAPER_ONLY → OK, any other value → VIOLATION, empty → UNKNOWN.
  - `paperPortfolioStatus` and `lastCycleStatusHealth`.
  - `deriveViewTruth`: stale on refresh error, a snapshot older than 90 s, or no snapshot.
  - `presentStatus`: a green status becomes STALE when the view is stale.
  - `presentRunning`: UNKNOWN when stale.
- `snapshot.ts`:
  - The hard-coded `"OK"` for پورتفوی کاغذی and صفرپولی (formerly `:161,163`) is gone. Both now derive from the persisted `state.executionMode`.
  - امنیت داده and تازگی شواهد now use the freshness limits.
  - The other dimensions are unchanged.
- `CommandCenter.tsx`:
  - A 15 s clock re-evaluates freshness without a fetch.
  - `bootError` is cleared only after a successful fetch.
  - A red STALE banner shows when a refresh failed or the snapshot is old.
  - The run pill says "وضعیت نامعلوم — STALE" instead of "running".
  - Health pills go through `presentStatus`; VIOLATION renders red.
- `scripts/dashboard_truth_selftest.ts` (new) and npm script `test:dashboard-truth`; `tests/test_dashboard_truth_static.py` (new, wiring pins).

### GM-03: tests (Windows, node 24 / Python 3.11.9)
- `npm run test:dashboard-truth`: 34/34 pass.
- Exit 0: `test:web-api-auth`, `test:canonical-read-model`, `test:canonical-security`, `test:alert-banner`.
- `npx eslint` on the changed files: exit 0.
- `tsc --noEmit`: exit 2, but **all 9 errors are pre-existing ones under `docs/archive/consolidation_2026-09-26/ahos022_divergent/`**. There are 0 errors outside docs/archive. Known debt, not caused by GM-03.
- pytest `test_dashboard_truth_static` + one_brain + alerts_web_banner + canonical_decision_authority + canonical_read_model + web_api_auth_gate: **87 passed**.
- Adversarial: the selftest covers future timestamps, NaN or empty timestamps, the refresh-error-with-fresh-snapshot case, green→STALE, VIOLATION not masked, and non-green statuses passing through unchanged.
- Not verified: how the page actually renders in a browser (no service restart, no screenshot). The Next dev server hot-reloads on its own.
- Next: GM-05.

### GM-05: what changed (non-breaking option; `.env` NOT edited; 3000 NOT mass-replaced)
- `scripts/gateway_port.py` (new, stdlib only, read-only):
  - `resolve_gateway`: precedence is `AHOS_GATEWAY_URL` > `AHOS_GATEWAY_PORT` > `http://127.0.0.1:3000/api/chat`.
  - It warns on an invalid port, on a port that disagrees with the URL, and on an unparseable URL.
  - `diagnose` probes loopback ports only (the configured port plus `AHOS_GATEWAY_CANDIDATE_PORTS`, default 3000,3500). Verdicts: `CONFIGURED_PORT_LISTENING`, `CONFIGURED_PORT_NO_LISTENER` (with an OWNER_ACTION hint), `NO_GATEWAY_LISTENING`, `NON_LOCAL_URL_NOT_PROBED`.
  - CLI: `--json`, `--url-only`, `--env-file`. It never writes anything.
- `scripts/operator_validation_gate.py`:
  - G2's default URL comes from the resolver.
  - `AHOS_GATEWAY_PORT` is loaded from .env.
  - When G2 is not PASS, a `gateway_port_diagnosis` is attached. The **status is unchanged**.
  - The historical .env persistence of the 3000 default happens only when source = DEFAULT, never for a port override.
- `scripts/windows_run_operator_gate.ps1` (BOM and CRLF preserved; parser: 0 errors):
  - It now uses `gateway_port.py --url-only` (same resolution), falling back to 3000.
  - It persists via the ensure script only when no port override is set.
  - It prints the read-only diagnosis.
- `tests/test_gateway_port.py` (new): 26 cases.

### GM-05: tests and real diagnosis
- Windows: `test_gateway_port` + `test_operator_validation_gate` + `test_web_api_auth_gate` + `test_phase18_launchers`: **110 passed**. `validate_imports --imports-only`: PASSED.
- Real run on the laptop, read-only (.env hash unchanged before and after):
  `verdict=CONFIGURED_PORT_NO_LISTENER`, `listening_candidates=3500`. So .env says 3000, and the gateway is actually listening on 3500.
- Mutation checks (each made one test fail):
  - hard-coding 3000 back in G2
  - removing the loopback-only guard
- **OWNER_ACTION_REQUIRED:** choose one:
  - (a) restart the gateway on 3000, or
  - (b) set `AHOS_GATEWAY_PORT=3500` (or `AHOS_GATEWAY_URL`) yourself.

  Grok edited no `.env` and restarted nothing.
- Next: GM-06.

### GM-06: n8n governance rules and ahos_03 quarantine (details: `reports/grok/GM06_N8N_QUARANTINE.md`)
- `tests/validate_n8n.py` gains `governance_findings`. These rules are **errors**:
  - AUDIT_TAMPER (DELETE, TRUNCATE or UPDATE on `agent_audit_trail`)
  - AUTHORITY_BYPASS (`UPDATE trade_decisions … execution_status`)
  - SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER (`{{ }}` in SQL in a telegram, webhook, form or chat triggered workflow)

  These are **warnings**:
  - SQL_INTERPOLATION (internal schedule workflows)
  - DECISION_WRITE_OUTSIDE_CANONICAL_AUTHORITY (`INSERT INTO trade_decisions`)
- `QUARANTINED_WORKFLOWS` = {`ahos_03_telegram_control.json`}, matched by exact filename only. For that file the errors become `QUARANTINED <rule>` warnings, and the CLI prints `[QUARANTINED(do-not-import)]`. G12 stays `STRUCTURAL_VALID` (exit code unchanged). **The file is not deleted or edited.**
- `docs/N8N_OPERATIONAL_PROCEDURE.md`: quarantine banner, and import step 2 now excludes quarantined workflows.
- Tests: `tests/test_n8n_governance_rules.py` has 24 cases, covering positives, benign negatives, disabled nodes, the look-alike filename, ahos_03 failing once un-quarantined, and the CLI.
  - Box: 24 + `test_validate_n8n_utf8` + `test_operator_validation_gate` + `test_ahos -k n8n` all pass.
  - Windows results are in the next commit message / final report.
- Finding: `ahos_02_signal_pipeline.json` has a node **`Record PENDING (LIVE)`** that INSERTs into `trade_decisions`, plus SQL interpolation on an internal schedule. It produces warnings only, and the workflow is dormant (0 imported). Review it before any import.
- Next: GM-04 design doc (`reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`) for review by سپهر/قاسم/رضا.

### GM-04: design only (no code)
- Proposal: `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`.
  - an intent → capability map
  - default deny of start/stop/paper_buy from remote channels
  - the body-asserted `channel` is not trusted (two options for reviewers)
  - an optional admin principal plus a single-use confirmation nonce
  - word-boundary intent hardening
  - append-only audit with hashed ids
  - the canonical authority is untouched
- New adversarial finding recorded there: the `chat.ts` `stop` regex `/(توقف|استاپ|stop|خاموش)/` has **no word boundary**, so a message containing "stop loss" or "stoploss" stops the engine (T2). The fix is waiting for the GM-04 review; nothing has been changed.

### Remaining blockers (end of Phase 2)
1. **Blocker A** (Claude): 2 untracked artifacts are cited by canonical docs, and `test_doc_drift` fails on a clean checkout. See the note at the top of this file.
2. Telegram start/stop control leak and the `stop`-substring false positive. Status: DESIGN_ONLY (GM-04), awaiting review.
3. Gateway port: .env says 3000, the listener is on 3500. OWNER_ACTION_REQUIRED (restart on 3000, or set AHOS_GATEWAY_PORT/URL).
4. G11 live Telegram E2E: LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED.
5. `tsc --noEmit` has 9 pre-existing errors under `docs/archive/.../ahos022_divergent/`. Suggestion: exclude `docs/archive` in tsconfig (small and separate; not done).
6. ahos_02 `Record PENDING (LIVE)` node needs review before any n8n import.
7. Wall-clock items unchanged: T+72h labels not before 2026-10-05T02:54Z (06:24 Tehran); soak and nightly backup nights 2–7.

### Next recommended missions
- GM-01 (Claude's call: blocker A).
- GM-04 implementation after review.
- tsconfig exclusion of `docs/archive` (tiny).
- GM-08 (mission ledger schema).
- GM-09 (provider QUOTA_EXHAUSTED state).
- GM-07 after owner approval.

### May Claude safely continue?
**YES.**
- Grok's Phase 2 commits touch only these paths: `telegram_ai/{envelope,bot,adapter}.py`, `dashboard_truth.ts`, `snapshot.ts`, `CommandCenter.tsx`, `package.json` (+1 script), `scripts/{gateway_port.py,dashboard_truth_selftest.ts,operator_validation_gate.py,windows_run_operator_gate.ps1}`, `tests/{validate_n8n.py,test_telegram_offline_harness.py,test_dashboard_truth_static.py,test_gateway_port.py,test_n8n_governance_rules.py}`, `docs/N8N_OPERATIONAL_PROCEDURE.md`, `reports/grok/*`.
- None of your dirty or untracked files were touched.
- Fast-forward `origin/ahos` before your next commit.
<!-- PHASE2:END -->

> Below: Phase 1 handoff (2026-10-02 10:36Z), kept for history.


| Field | Value |
|---|---|
| Timestamp (UTC) | 2026-10-02T10:36Z (14:06 Tehran) |
| Agent | Grok (parallel Autonomous Engineering / Research agent), Phase 1 = reality inspection + mission discovery |
| Mission IDs | GROK-P1-20261002 (inspection); discovered GM-01 … GM-12 (see MISSION_DISCOVERY_2026-10-02.md) |
| Branch | `ahos` |
| Upstream | `origin/ahos` (not origin/main) |
| Starting HEAD | `25b33cceb280b5b3d67bf37586500ba297bdb65f` (== origin/ahos, 0 ahead / 0 behind after `git fetch origin`) |
| Ending HEAD | the single Grok docs commit that adds this file (parent `25b33cc`); message `docs(grok): session 2026-10-02 reality inspection, mission discovery, handoff [PAPER_ONLY]`. If absent from `git log`, the commit/push did not happen — see final Grok report |
| origin/main | `8ae411a` (ahos is 30 ahead / 2 behind main; not merged, not touched) |

## Files changed by Grok
Added only (new files):
- `reports/grok/GROK_SESSION_2026-10-02_REALITY_INSPECTION.md`
- `reports/grok/TELEGRAM_REALITY_MAP.md`
- `reports/grok/DOCKER_N8N_DEPENDENCY_MAP.md`
- `reports/grok/DASHBOARD_ONECLICK_REALITY.md`
- `reports/grok/MISSION_DISCOVERY_2026-10-02.md`
- `reports/grok/GROK_HANDOFF.md`

NOT changed / NOT staged: all source, `.env`, `.cursor/hooks.json` (+ `.local-backup`, `ahos-hooks-local-diff.txt`), Claude's modified `reports/backup_restore_drill.json`, `reports/month1_failure_matrix.json`, `reports/reliability_matrix.json`, Claude's ~40 untracked `reports/*` evidence files, `next-env.d.ts`. No service/container/gateway started, stopped, or restarted. No DB writes (one read-only psql session with `default_transaction_read_only=on`).

## Tests run (all exit 0)
- pytest cognitive set + test_doc_drift: 117 passed (448.7 s)
- pytest Telegram set + test_engine_import_safety: 150 passed, 1 xfailed (387.4 s)
- npm: canonical-read-model 13/13, canonical-security 19/19, web-api-auth 9/9, alert-banner 8/8
- `validate_imports.py --imports-only`: PASSED (236 modules)
- `freeze_lane_a.py` verify: OK (36 files)
Interpreter: `.venv\Scripts\python.exe` (Python 3.11.9).

## Runtime evidence (~10:10–10:34Z)
- Gateway: node PID 13120 LISTEN 127.0.0.1:3500 (manual `npm run dev -- -p 3500`), GET / 200. Port 3000 free.
- Docker Desktop + WSL2 running; `ahos_postgres_win` healthy (pg_isready OK); `ahos_runtime_win` unhealthy (5 s healthcheck timeout, stale container config); `ahos_n8n_win` up, **0 workflows imported**.
- VHDX backups re-hashed by Grok: ext4 + docker_data both match recorded SHA256.
- Nightly backup night 1/7 verified (spot hash); **no scheduled task exists**.
- Native `start_ahos.bat` daemon not running; container `python3 -m architecture.runtime` is the only observer writing `data/` via bind mount.

## Unresolved issues / known regressions
1. **KNOWN REGRESSION (STRONGLY INDICATED): 25b33cc + untracked `reports/nightly_backup_series.json`** — `scripts/doc_drift.py::_exists` checks the working tree; the artifact is untracked (not ignored); canonical docs cite it (`AHOS_GAP_REGISTER.md:24`, `AHOS_LOCAL_ACTIVATION_CHECKLIST.md:131`, `AHOS_OPERATOR_QUICKSTART_WINDOWS.md:206`, `AHOS_SOAK_OPERATOR_START.md:151`). Clean checkout/CI → `test_canonical_docs_have_zero_real_stale_refs` fails. Claude: decide commit-the-artifact vs exemption (GM-01). Grok did not touch it.
2. Telegram → gateway can trigger `startEngine/stopEngine` by free-text regex (`chat.ts:233-234`, `:43-48`) with no capability check/audit; sender `user_id` is sent empty (`telegram_ai/service.py:84`).
3. n8n `ahos_03_telegram_control.json`: SQL interpolation, audit-row DELETE on `/reset`, `/approve` writes `trade_decisions.execution_status` bypassing canonical authority. Dormant (not imported) but target tables exist. Do not import.
4. Dashboard stale-READY: after a successful load, a failed poll keeps old green health (`CommandCenter.tsx:304-306`).
5. Port: `.env:99` = 3000, running gateway = 3500, no tracked reference to 3500; ~40 repo refs to 3000. Not a one-line script drift.
6. `ahos_runtime_win` config drift (created 2026-08-28; healthcheck enabled; port 18000 vs compose 8000).
7. `prediction_lifecycle.py:326` hard-coded `eligible_join_pairs_estimate=0` (Claude finding, Lane B) — pending owner approval.
8. M0 audit report file not found in repo or `G:\AHOS_FORENSIC_REPORT`; Gate 4 cache report not present.
9. `reports/pgdump_ahos_chat_messages_20261002T002200Z.sql` contains operator chat rows — privacy review before anyone commits it.

## OWNER_ACTION items
- G11 Telegram live E2E (archive `reports/telegram_e2e_<UTC>.md`).
- Canonical gateway port decision (restart on 3000, or edit `.env:99` to 3500).
- Scheduled task for nightly backups (nights 2–7) or manual nightly runs.
- Recreate `ahos_runtime_win` from committed compose (service restart).
- Approve `prediction_lifecycle` census fix; decide single runtime owner (container vs native daemon).
- Cleanup of exited legacy containers (`AHOS-N8N`, `ahos-postgres`, `ahos-redis`) — deletion.

## Wall-clock dependencies
- T+72h outcome labels: not before 2026-10-05T02:54:19Z (T0 2026-10-02T02:54:19Z).
- Soak / nightly backup nights 2–7: one per calendar night (2026-10-03 … 2026-10-08 at the earliest).
- Calibration sufficiency: NOT proven; never report CLOSED.

## Security / governance
- Lane A untouched and verified; Canonical Decision Authority untouched; PAPER_ONLY held; no secrets printed or written (Telegram token = CREDENTIAL_PRESENT_BUT_REDACTED; leak scan: 0 real hits, 1 synthetic fixture `tests/test_engine_import_safety.py:101`; git history not scanned).
- `.cursor/hooks.json` failClosed guard (`ahos-guard.py`) preserved, not modified.
- No Credential Manager abstraction exists (DESIGN_ONLY).

## Next recommended mission
GM-01 (doc-drift clean-checkout regression — Claude's call, small) → GM-02 (Telegram offline harness, tests only) → GM-03 (dashboard stale-READY).

## May Claude safely continue?
**YES.** Grok changed no source, no config, no Claude file, and no runtime state; the only repo change is the new `reports/grok/` directory. Claude should pull/fast-forward `origin/ahos` before its next commit if Grok's docs commit was pushed (it only adds `reports/grok/*`, so no conflict is possible with Claude's dirty files). Coordinate before either agent edits `scripts/doc_drift.py`, `telegram_ai/`, `chat.ts`, or `CommandCenter.tsx`.

## MISSION 11.1 — LAUNCHER FINISH (Claude, 2026-10-03, Asia/Tehran)

Follow-up to M11 (commits 2270146, 9e74645, 4feecd0). Stage-1 prompt review by
four agents ran BEFORE any code was written; all four returned CHANGES and all
eight findings were folded into the plan. Full notes: `docs/ONE_CLICK.md`
"M11.1 review notes". Summary: (A1/A2) one gateway-port resolver, not two;
`resolve_gateway()` untouched, new `select_port()`; (R1) spawn flags lose
`DETACHED_PROCESS`; (R2) `python.exe` not `pythonw.exe`; (R3) sweep rewritten
on parentage, not substring markers; (P1) one desktop icon, controls inside the
dashboard; (P2) `-WindowStyle Hidden` is what makes nothing visible,
`WindowStyle 7` is only a hint; (P3) Persian status/age strings added;
(G1) loopback 403 before auth; (G2) stop/restart spawned detached so a gateway
restart cannot kill the stop itself; (G3) no duplicate modules.

### Phase log
| UTC | Part | Files | Result |
|---|---|---|---|
| start | Stage-1 review | docs/ONE_CLICK.md, this file | 4 agents, 8 findings, all folded into plan |
