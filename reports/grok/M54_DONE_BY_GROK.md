# M54 DONE BY GROK

Written: 2026-10-07 Asia/Tehran
HEAD before: `0611df8d3cbac8ff4979b0d0c679259c4a31c095` (ahos, after M10.1)
Commit message: `grok: M54 StartupValidator and tests honour AHOS_DATA_DIR`
PAPER_ONLY. Never pushed. HOLD.flag left in place (Claude autopilot stays on HOLD).
Did not kill PID 4708 or interactive Claude 9580. Did not touch `.env` secrets.

## What changed

| File | Change |
|------|--------|
| `architecture/runtime/lifecycle.py` | StartupValidator resolves DBs via `get_discovery_db_path` / `get_paper_trading_db_path` / `get_local_db_path` (`create_dir=False`) when no `workspace_root` override; override still uses `<root>/data` for temp-tree tests. ApplicationLifecycleManager passes `workspace_root` through (None → config.paths) and uses the same resolver for the local health probe / lifecycle events. |
| `tests/test_f1_s1.py` | `PAPER` uses `get_paper_trading_db_path(create_dir=False)` (E01/LOCAL stay on live `ROOT/data` for live-census assertions). |
| `tests/test_runtime_lifecycle.py` | New tests: StartupValidator follows `AHOS_DATA_DIR`; explicit `workspace_root` ignores `AHOS_DATA_DIR`. |

## Evidence

```
# unset AHOS_DATA_DIR
pytest tests/test_f1_s1.py tests/test_runtime_lifecycle.py -q
→ 17 passed

# AHOS_DATA_DIR=<temp>
pytest tests/test_f1_s1.py tests/test_runtime_lifecycle.py -q
→ 17 passed
```

## Claude: do not redo
Treat M54 StartupValidator / AHOS_DATA_DIR path honouring as **DONE by Grok**. Prefer extending tests over rewriting.
HOLD remains until owner clears model/quota blocker (see `M10_1_MODEL_BLOCKER.md`); this mission implementation does not require releasing HOLD.
