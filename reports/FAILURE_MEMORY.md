# AHOS Failure Memory

Owner directive §67 chain, one entry per defect: **Incident → Root Cause →
Impact → Failed Assumption → Control → Remediation → Regression → Lesson →
Memory.**

This file is append-only. An entry is written when a defect is fixed, not when
it is discovered, and it is never deleted — a recurring failed assumption is the
most valuable signal here.

---

## FM-001 — Scheduler cycle never returned against the production discovery DB

- **Incident.** During the M9 baseline, the batch-00 pytest run was killed at
  the 1500s harness timeout. `execute_scheduled_cycle` did not return.
- **Root cause.** `architecture/scheduling/engine.py::audit_and_register_missed_windows`
  ran one dedup SELECT per `(token, snapshot slot)` against `gap_register`,
  which carries no index on `(token_id, kind)`. Each probe was a full table
  scan: ~30,000 full scans of a 56k-row table per cycle, ≈1.6 billion row
  comparisons. Complexity was O(tokens × slots × rows), not O(rows).
- **Impact.** Any scheduler cycle against a real discovery DB hung
  indefinitely. The observation pipeline kept working (2,642 `scheduler_runs`
  rows are SUCCESS) only because the slow path is not on the daemon's hot loop —
  which is also why it went undetected for weeks.
- **Failed assumption.** "A per-row SELECT in a loop is fine on a small table."
  The table was not small, and the probe count was multiplicative, not additive.
- **Control.** `tests/test_alert_engine.py::test_audit_and_register_missed_windows_is_not_on2`
  pins the complexity bound: 200 tokens × 8 slots, all overdue, asserts the
  audit completes in under 10 s **and** registers exactly 200 × 8 gaps, **and**
  asserts a second pass registers 0 (idempotency).
- **Remediation.** `gap_register` is Lane A-owned and frozen, so no index was
  added. The `(token_id, kind)` keys are read once into a set and membership is
  tested in memory — O(rows) total. Verified against the production discovery
  DB that exposed the bug: **0.59 s** where it previously hung indefinitely.
- **Regression.** Same test as the control, plus the full 2647-test suite still
  green.
- **Lesson.** In a frozen-schema lane, the fix for an indexing problem is
  algorithmic, not DDL. Read the keys once, do the membership test in memory.
- **Memory.** Before adding any per-row query inside a loop, count probes as
  `outer × inner`, not `outer + inner`, and check the target table's row count
  on the production DB, not on the test fixture.

## FM-002 — A unit test was silently reading production state

- **Incident.** `tests/test_alert_engine.py::test_production_scheduler_cycle`
  stalled for the same reason as FM-001 — but it was a unit test.
- **Root cause.** The test constructed `ProductionScheduler(db_path)` without
  injecting `discovery_db_path`. The constructor falls back to
  `get_discovery_db_path()`, so `audit_and_register_missed_windows` audited the
  **real** production discovery DB (3,720 OBSERVING tokens × 8 slots).
- **Impact.** A test passed or failed depending on machine state — on what
  happened to be in the owner's discovery DB. That is not a test. It also meant
  every CI run had a data-dependent timeout.
- **Failed assumption.** "Optional constructor parameters default to something
  inert." The default was a live production database.
- **Control.** The test now builds its own discovery DB in `tmp_path`, seeds
  the three tables it needs, and injects it explicitly. A second test pins the
  bound (see FM-001). Any future fallback to the production path shows up as a
  stall in a hermetic test, not a silent production read.
- **Remediation.** Committed in `3710288`.
- **Regression.** 6 passed in `tests/test_alert_engine.py`; the scheduler tests
  now run against a temp DB and finish in well under a second.
- **Lesson.** A resource-path parameter with a production default is a
  production coupling hiding in a signature. Every default like that is a
  hermeticity bug waiting for a test to trigger it.
- **Memory.** When auditing a module for test hermeticity, grep the
  constructors for `or get_<production>_path()` — that is the shape of this
  defect, and it is not specific to the scheduler.

## FM-003 — `import engine.bot_skeleton` killed the interpreter

- **Incident.** The M9 part B audit harness recorded `engine.bot_skeleton` in
  `import_failures` verbatim: `TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_CHAT_ID
  missing — refusing to start (Agent-04 rule)` and exited.
- **Root cause.** `logging.basicConfig()` ran at module scope, and the
  env-missing guard called `sys.exit(2)` at module scope — reachable from a
  plain `import`, not just from `main()`.
- **Impact.** No test or module could import the bot skeleton without setting
  both env vars. Importing it in a test harness terminated the process.
- **Failed assumption.** "Code in a `main()`-style script module is only reached
  when the module is run." It was at module scope.
- **Control.** `tests/test_engine_import_safety.py` imports the module with a
  scrubbed environment and asserts the interpreter survives.
- **Remediation.** `basicConfig` and the env check moved into `main()`
  (`3710288`). Importing is now inert; running as a script behaves identically.
- **Regression.** Part of 21 passed across the two import-safety modules.
- **Lesson.** `sys.exit` at module scope is a process bomb with an `import`
  trigger. An entrypoint module's failure modes belong behind its own guard.
- **Memory.** Treat any module-scope `sys.exit`, `os.chdir`, `basicConfig`, or
  `process.exit` as a defect until proven otherwise — see FM-004, FM-005,
  FM-006 for the same shape in three other modules, two languages.

## FM-004 — `engine/run_validation.py` ran a full backtest on import

- **Incident.** The same audit recorded `engine.run_validation` failing with
  `FileNotFoundError` on a temp path during import.
- **Root cause.** The module executed its entire backtest at module scope and
  wrote a report file as a side effect of being imported.
- **Impact.** Importing the module cost a full backtest run and wrote files.
  `tests/test_engine_import_safety.py` could only document the defect with a
  *strict xfail* — it could not assert the invariant, because the invariant was
  false.
- **Failed assumption.** "Expensive work in a validation script happens when
  someone runs it." It happened when someone imported it.
- **Control.** The strict xfail is deleted; the test now asserts import is
  side-effect free directly. The current tree has 0 xfail.
- **Remediation.** Backtest moved behind a function and a `__main__` guard
  (`3710288`).
- **Regression.** `tests/test_engine_import_safety.py`, now asserting rather
  than documenting.
- **Lesson.** A strict xfail is an honest confession, not a fix — and it is
  worth more deleted than kept, because a kept one teaches the suite that
  broken invariants are normal.
- **Memory.** While auditing a module, the presence of a strict xfail naming
  that module is a lead, not a closed item.

## FM-005 — `scripts/verify_control_audit.ts` read files and exited on import

- **Incident.** The TypeScript analogue of FM-003/004: importing the audit
  script read the audit file from disk and called `process.exit()` on the
  importing process.
- **Root cause.** `main()` ran at module scope with no entrypoint guard.
- **Impact.** Any module importing it for `verifyAuditLines` risked terminating
  the process and touching the audit file as an import side effect — and it
  discouraged the reuse of exactly the verification function the control gate
  needs.
- **Failed assumption.** "JavaScript modules don't have the `__main__` problem."
  Without a guard they have exactly the same problem.
- **Control.** `if (import.meta.main)` (Node 22+) is the guard; the static
  top-level scan in part B covers all 47 server-side TS modules.
- **Remediation.** `3710288`. Before/after the change,
  `npm run audit:control-verify` returns the same `CHAIN_OK` over the same
  9 lines — the exit-code contract it is run for is unchanged.
- **Regression.** `npm run audit:control-verify` exit 0; `tsc`/`eslint` clean.
- **Lesson.** Entrypoint discipline is language-independent. In TS, an
  `import.meta.main` guard is the equivalent of Python's `if __name__ == ...`.
- **Memory.** Any `.ts` file whose `main()` is not behind `import.meta.main` is
  a latent `process.exit` for whoever imports it.

## FM-006 — `scripts/windows_g2_probe.py` moved the process working directory on import

- **Incident.** Found by the part B static AST pass, not by a crash — the most
  insidious of the six, because it was silent.
- **Root cause.** `os.chdir()` at module scope.
- **Impact.** Any module that imported the probe inherited a changed working
  directory, which silently redirects every later relative path in the process.
  Failures would appear as "file not found" in unrelated code, far from the
  cause.
- **Failed assumption.** "A probe script can set up its own cwd." Only when run
  as a script; import makes it everyone's cwd.
- **Control.** `tests/test_m9_import_side_effects.py` re-runs the innocuity
  pass over the audited roots.
- **Remediation.** `os.chdir` moved into `main()` (`3710288`).
- **Regression.** Part of the 21 import-safety tests.
- **Lesson.** Process-global mutation (`chdir`, `basicConfig`, `environ`) is
  never safe at module scope, because import makes the module a guest in
  someone else's process.
- **Memory.** The four module-scope statements to grep for in every new module:
  `os.chdir`, `logging.basicConfig`, `sys.exit`, `os.environ[...] =`.
