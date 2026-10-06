# M54 — StartupValidator / tests honour AHOS_DATA_DIR

Status: DONE by Grok (2026-10-07 Asia/Tehran). See `reports/grok/M54_DONE_BY_GROK.md`.

## Goal
Single data-dir resolver: StartupValidator and `tests/test_f1_s1.py` honour `AHOS_DATA_DIR` via `config.paths` (`create_dir=False`), while explicit `workspace_root` still pins temp-tree tests to `<root>/data`.

## Acceptance
- With `AHOS_DATA_DIR=<temp>`: targeted pytest passes.
- With unset: still passes.
- Do not skip/weaken tests. PAPER_ONLY. Never push. Leave HOLD.flag unchanged.
