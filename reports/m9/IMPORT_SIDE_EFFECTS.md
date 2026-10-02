# M9 Part B — Import-time side-effect audit (Mandate §12 item 2)

Method: `scripts/audit_import_side_effects.py` — two independent passes.
**Static (AST)** flags module-scope statements that can reach the outside world
(call, `os.environ` write, `open(...)`, top-level `await`) outside
`if __name__ == "__main__"` / `import.meta.main` guards. **Runtime** then
imports every module in a fresh interpreter with tripwires armed
(socket connect, file write, sqlite connect, subprocess spawn, thread start,
env mutation) and records which ones actually fired. **The runtime pass is the
authority**: an AST hit may be a false positive, an AST miss a false negative —
the two are cross-checked here. Imports were executed with `AHOS_ROOT`
redirected to a temp dir, so a module that writes cannot touch tracked evidence.

Both JSONs below were re-run **after** the `3710288` fixes, so the numbers
describe the current tree, not the pre-fix one.

## Python — 266 modules audited, 0 confirmed side effects, 0 import failures

| pass | result |
|---|---|
| roots | `architecture`, `scripts`, `engine`, `telegram_ai`, `discovery`, `ahos_org`, `ahos_compose` |
| module_count | 266 (`import_side_effects.json`) + 54 (`import_side_effects_extra.json`, same roots re-scanned post-fix) |
| `runtime_confirmed_side_effects` | `{}` — no tripwire fired at import time |
| `import_failures` | `{}` — every module imports cleanly with the tripwires armed |
| `runtime_detail` events | 5, all `dependency_subprocess` from `dependency:pandas/compat/_constants.py` spawning `('ver',)` |

The 5 subprocess events are honest noise, not defects: pandas probes the Windows
`ver` command from its own compat module while being imported. They originate
inside a third-party dependency, not in any audited module, and they do not
touch AHOS state.

### Static candidates: 39 modules, all benign

| candidate | count | verdict |
|---|---|---|
| module-scope `sys.path.insert(0, <repo root>)` | 40 across 39 modules | benign and load-bearing — it is how a script/import reaches the repo before `config.paths` resolves. Idempotent (inserting an already-present path is a no-op), pure-Python, no I/O. |
| `telegram_ai.intent::_DIGIT_MAP.update(...)` | 1 | benign — populates a module-level digit map from a constant. Pure, no I/O. |

No module-scope `open()`, network call, database connect, thread start, or
environment mutation survived the runtime pass.

## Four real defects found and fixed (commit `3710288`)

The pre-fix run of this audit is what exposed them — it could not even complete,
which is exactly the signal it was built to produce. Each had a working test that
imported the module, so the suite masked them by never importing the real module
at all (or by running the whole thing under `__main__`).

| module | defect at import | fix | regression test |
|---|---|---|---|
| `engine/bot_skeleton.py` | `logging.basicConfig()` ran at module scope, and a top-level guard called `sys.exit(2)` when env was missing → any `import engine.bot_skeleton` without `TELEGRAM_BOT_TOKEN` killed the interpreter. `import_failures` recorded the abort verbatim. | logging/basicConfig moved into `main()`; the env check is `main()`-only. Importing is now inert. | `tests/test_engine_import_safety.py` |
| `engine/run_validation.py` | ran its **entire backtest at module scope** and wrote a report file as a side effect of `import`. | backtest moved behind a function + main guard; import does no work and writes nothing. | `tests/test_engine_import_safety.py` (the strict xfail this test used to carry is gone — it now asserts the invariant directly) |
| `scripts/verify_control_audit.ts` | `main()` ran at module scope, reading files and calling `process.exit()` on plain `import` — the TS analogue of running a Python script's body on import. | work is behind `if (import.meta.main)`; the module is now import-safe for tests and other scripts. | `npm run audit:control-verify` still exits 0 / `CHAIN_OK`; the TS import-safety selftests |
| `scripts/windows_g2_probe.py` | `os.chdir()` at module scope mutated the process working directory as a side effect of import. | chdir moved into `main()`; import no longer moves the cwd. | covered by `tests/test_m9_import_side_effects.py` import-innocuity pass |

Every fix moved the effect into a function or a main guard. None changed any
module's behaviour when run as a script — only when imported. `npm run
audit:control-verify` before and after the change returns the same
`CHAIN_OK` over the same 9 lines, which is the check for the one module that
has a real exit code contract.

## TypeScript — 47 modules, 0 top-level executable statements

The Python audit has a runtime tripwire harness; TypeScript has no equivalent
here, so the server-side `.ts` (everything in `src/`, `scripts/*.ts`, and the
root server modules, excluding `*.test.*` and `*.d.ts`) was scanned statically
for top-level executable statements — anything at brace depth 0 outside a
declaration, outside an `import.meta.main` guard. **0 found across 47 files.**
The `import.meta.main` guard (Node 22+) is the TS equivalent of Python's
`if __name__ == "__main__":`, and every script that has an exit-code or
file-reading contract now sits behind one.

This is a static heuristic, not a runtime tripwire, so it is corroborated by the
two gates that actually run: `npx tsc --noEmit` exit 0 and `npx eslint .` exit 0
over the same tree.

## What this audit is NOT

It proves imports are free of side effects **on this tree, under these
tripwires**. It does not prove a module cannot develop one — the guard is the
`tests/test_m9_import_side_effects.py` suite, which re-runs the innocuity check
and must stay green. A new module that reaches the network or a database at
import time will fail that suite rather than silently slow down every importer.
