# M53: quarantine dead / duplicate trees and scripts (M34 coherence input)

## Evidence (box, tracked files at 238b090)
Not referenced by the Next app (app/, tsconfig paths) or Python packages, each a separate scaffold with its own
schema/db/seed:
- `01/` (37 files; own drizzle config with postgres:postgres@.../app_db), `advanced-3d-audiovisual-website/` (33),
  `advanced-3d-audiovisual-website (1)/` (60), `درخت کاملتر immersive-3d-audiovisual-website/` (7),
  `سایت درختadvanced-3d-audiovisual-platform/` (66; own /api/paper, /api/chat, /api/telegram routes writing paper rows).
- `run_ahos.sh`: starts `uvicorn ahos.interfaces.api.main:app --host 0.0.0.0`, `celery -A ahos.worker...`;
  the `ahos` package does not exist; it would also bind 0.0.0.0.
- `tests2b/` (24 files) outside pytest testpaths; `slills/` (typo dir, 16 files).
- `docker-compose.yml` + `n8n/` while M10 retires Docker/n8n.
## Required change
Do NOT delete. Move each into `docs/archive/quarantine_2026-10/<name>/` with a README line (what, why dead, last
commit), update tsconfig/eslint excludes if needed, and list them in the M34 duplicate map. run_ahos.sh: replace
with a 5-line script that calls `python -m launcher "$@"` (launcher now runs on POSIX, box commits 85d2617/1e22a96)
or move to quarantine.
## Acceptance
`git grep` shows no live import of moved paths; tsc/eslint/build/all test suites unchanged in counts; doc_drift 0.
