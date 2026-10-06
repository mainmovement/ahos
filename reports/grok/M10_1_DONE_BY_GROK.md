# M10.1 DONE BY GROK

Written: 2026-10-07 Asia/Tehran
HEAD before: `ca4ac8331c3a4c83947e8280dccbf4821c947dd8` (ahos, includes grok box-security merge)
Commit message: `grok: M10.1 pglite init from launcher (+ --check)`
PAPER_ONLY. Never pushed. HOLD.flag left in place (Claude autopilot stays on HOLD).
Did not kill PID 4708 or interactive Claude 9580. Did not touch `.env` secrets.

## What changed

| File | Change |
|------|--------|
| `scripts/pglite_restore.ts` | Add read-only `--check` (PG_VERSION + `ahos_system_state`); no mkdir/migrate on check |
| `scripts/pglite_restore_lib.ts` | Add `checkReady()` |
| `launcher/components.py` | `database_target` uses `pglite_data_dir`; `decide_pglite_init_action` / `pglite_needs_schema_init` / argv helpers / `run_pglite_tool`; probe = PG_VERSION + `--check` (injectable `check_runner`) |
| `launcher/orchestrator.py` | `_start_db_backend` runs schema-only restore once when PG_VERSION missing (before gateway); records evidence in status; never migrates Postgres |
| `launcher/processkit.py` | Restore `port_in_use` dropped by box-security merge (needed by probe/preflight) |
| `tests/test_launcher_orchestrator.py` | `TestPgliteInitM101` — decision logic + fake restore/check runners |

## Evidence

### Unit tests (fake runner)
```
pytest tests/test_launcher_orchestrator.py::TestPgliteInitM101 \
       tests/test_launcher_orchestrator.py::TestComponents \
       tests/test_launcher_orchestrator.py::TestProcessKit::test_port_in_use
→ 43 passed
```

### Fresh-dir smoke (Windows, no long soak)
```
empty dir + --check → exit 1 (PG_VERSION missing)
schema-only restore (no --dump) → migration applied 33 statements; ready: ahos_system_state present; exit 0
--check after restore → check OK: PG_VERSION + ahos_system_state present; exit 0
```

## Claude: do not redo
Treat M10.1 PGlite launcher init + `--check` as **DONE by Grok**. Prefer extending tests over rewriting.
HOLD remains until owner clears model/quota blocker (see `M10_1_MODEL_BLOCKER.md`); this mission implementation does not require releasing HOLD.
