# D949CB_DROP_RESTORE — launcher symbols the box-security merge orphaned

Written: 2026-10-07 Asia/Tehran by Claude.
Scope: local `ahos` branch, PAPER_ONLY, no push.

## Root cause

`d9492cb` ("grok: merge box security/debug series") is a **single-parent
squash** (parent `e912fb6`) that re-applied the box branch's working tree.
The box branch had forked *before* M11.1/M11.2, so re-applying it silently
deleted later work from the `ahos` line while keeping the callers and tests
that referenced it. Each defect had the same shape: **caller retained,
implementation removed**.

`git log -S "def spawn_detached" -- launcher/processkit.py` → `d9492cb`
(removed) and `2270146` (introduced).

## Defects found and restored

| # | Symbol | File | Effect when missing |
|---|--------|------|---------------------|
| 1 | `spawn_detached` | `launcher/processkit.py` | **All** component spawning failed with `AttributeError`. Gateway, telegram, engine could not start. `posix_group_ok`'s own docstring still asserted "spawn_detached starts each child as a session leader". |
| 2 | `_skip_set` | `launcher/__main__.py` | `--skip` degraded to whitespace-only tokens; the dashboard's comma-joined `-Skip` value silently excluded nothing. |
| 3 | `_Tee` + `_install_log_tee` | `launcher/__main__.py` | The `AHOS_LAUNCHER_LOG` contract broke: `ahos.ps1` still exported the var but nothing read it, reverting to the R5 pipe-wedge that M11.1's R6 fixed. |
| 4 | `_CONSOLE_HANDLER = None` | `launcher/processkit.py` | Module global referenced by `global _CONSOLE_HANDLER` in `arm_console_break_immunity`; `monkeypatch.setattr` raised `AttributeError`. |
| 5 | `_write_gateway_record` / `_recorded_gateway` / `_clear_gateway_record` + `__init__`/`start()`/`stop()` wiring | `launcher/orchestrator.py` | The port chosen at start was in-memory only. A *new process* (`ahos.ps1 status`, the dashboard's Status button) re-resolved the configured 3000, probed a dead port, and advertised a `dashboard_url` pointing at nothing. Origin: box commit `e7aa551` (M11.1 d). |
| 6 | `LauncherPanel`, `LAUNCHER_LABELS_FA`, `LAUNCHER_STATUS_FA`, `statusFa`, `LauncherSnapshot`/`LauncherComponent` types, launcher state + fetch wiring, `StatusPill` `label` prop, `MutableRefObject` import | `CommandCenter.tsx` | The dashboard's service-status panel and its stop/restart controls were deleted (226 lines). The `/api/launcher` route remained fully functional server-side — only the UI consumer was gone. |

Defect 6 also removed the M11.1 lexicon pin, which is what made it visible:
`test_dashboard_panel_lexicon_mirrors_the_persian_module` compares
`LAUNCHER_LABELS_FA`/`LAUNCHER_STATUS_FA` against `launcher/persian.py`.

## Restorations, adapted not copy-pasted

- **`spawn_detached`**: restored with a new POSIX branch
  (`start_new_session=True`) the original lacked, because the box series made
  the process layer POSIX-aware (`TestPosixProcessKit`) and `posix_group_ok`
  requires the child to be a session leader. Windows branch keeps
  `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`; `creationflags=0` on the POSIX
  branch keeps the phase18 AST scan honest without raising `ValueError`.
- **`_skip_set`**, **`_Tee`/`_install_log_tee`**, **`_CONSOLE_HANDLER`**:
  restored verbatim from `e912fb6`; semantics unchanged.
- **Gateway record**: restored, but composed with HEAD's newer
  `_adopted_gateway` — a recorded port wins only while our gateway is live
  (`RECORDED_RUNNING`), otherwise adoption and a fresh record. The pre-merge
  version predated `_adopted_gateway`.
- **`CommandCenter.tsx`**: restored into the *rewritten* HEAD file, not the
  old one. HEAD's `StatusPill` had lost its `label` prop and the launcher
  tones (`HEALTHY`/`ONLINE`/`UNHEALTHY`/`FAILED`/`DEGRADED`/`SKIPPED`);
  re-added additively so existing callers (which pass no `label`) are
  unaffected. The panel keeps its own confirm step; it calls
  `POST /api/launcher`, which is a *different* surface from the F2
  propose→confirm gate on `/api/engine`, so the two do not conflict.

## Verification

- `tests/test_launcher_orchestrator.py` + `tests/test_phase18_launchers.py`:
  **11 failed → 0 failed** (179 passed, 1 skipped) at the final run.
- `npx tsc --noEmit`: `CommandCenter.tsx` clean. One pre-existing error
  remains elsewhere (`app/api/launcher/route.ts` imports `isLoopbackRequest`
  from `@/chat_auth`, which exports it from `next/server`); verified
  pre-existing by stashing the change and re-running.
- `npx eslint CommandCenter.tsx`: clean.

## Not regressions (recorded so they are not re-investigated)

The merge's net effect on `test_launcher_orchestrator.py` was **fixed 10,
regressed 10, persisting 2**. All 10 regressions and both persisting failures
were the six defects above; every one is now cleared. The pre-merge baseline
was established in an isolated worktree at `82d5b0a`.

`probe_db_backend`'s signature also changed in this range
(`(target, now)` → `(target, now, *, root, check_runner)`), but that was the
intended M10.1 evolution by `0611df8`, not a drop: the new signature and its
callers are consistent at HEAD.

## Carried forward

- The pre-existing `isLoopbackRequest` import error in
  `app/api/launcher/route.ts` is unrelated to this restore and predates it;
  it belongs to the BL mission's dependency-hygiene scope, not here.
