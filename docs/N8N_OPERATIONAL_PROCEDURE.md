# n8n Operational Procedure

**Status:** JSON VALID ≠ OPERATIONAL  
**Structural validation:** `python tests/validate_n8n.py` (6/6)  
**Live execution:** OWNER_ACTION_REQUIRED / EXTERNAL_BLOCKED without credentials  
**QUARANTINED (do not import):** `ahos_03_telegram_control.json` — see `reports/grok/GM06_N8N_QUARANTINE.md`. The quarantine is **name-enforced**, not path-enforced, so it followed the file into the M10 archive below.

## Structural (agent/CI can do)

```powershell
python tests\validate_n8n.py
```

Workflows are archived at
`docs/archive/quarantine_2026-10/docker_n8n/n8n/` (M10 Stage 5; the validator
resolves them there via `config.paths.get_n8n_workflows_dir()`).

## Operational (owner)

1. Install n8n (native or Docker — prefer documented Windows path in deployment docs)
2. Import each JSON in `docs/archive/quarantine_2026-10/docker_n8n/n8n/` **except quarantined ones** (`ahos_03_telegram_control.json` — the validator prints `[QUARANTINED(do-not-import)]`)
3. Configure credentials referenced by nodes (Telegram, HTTP, etc.) — never commit secrets
4. Set environment variables to match local AHOS ports/paths
5. Activate workflows one at a time
6. Trigger a test execution; confirm:
   - webhook receives payload
   - error path does not invent market data
   - retries behave as configured
7. Archive execution screenshots/IDs under `reports/n8n_ops_<UTC>/`

Until step 6–7 succeed: **n8n = JSON VALID only**.

## Post-retirement ownership map (M10, 2026-10-07)

n8n is retired by M10. The six shipped workflow cadences have recorded Python
homes — **the authoritative ownership map is
`architecture/scheduling/n8n_migration.py`**, not this document. Check it
first when asking "where did this job go?". It records, per workflow: the
verbatim n8n trigger rule, the owner (module callable or exact CLI argv), the
migration status, and file:line evidence. Its self-check is
`python -m architecture.scheduling.n8n_migration`.

The import procedure above is **superseded for the five non-quarantined
workflows** and retained as the record of how they were once run:

| Workflow | Status | Where it went |
|---|---|---|
| `ahos_01_data_ingest_integrity.json` | superseded, write leg not reimplemented | daemon 60s `OPPORTUNITY_CYCLE` / `--observation-cycle` tasks |
| `ahos_02_signal_pipeline.json` | already running | canonical decision authority, every daemon cycle |
| `ahos_03_telegram_control.json` | **QUARANTINED — never re-imported or re-implemented** | safe read-only surfaces in `run_bot.py`; kill switch is M39 |
| `ahos_10_research_lab.json` | deferred to M44 | argv recorded; M44 wires the run |
| `ahos_11_data_update.json` | deferred to M44 | argv recorded; M44 wires the run |
| `ahos_12_research_report.json` | deferred to M44 | argv recorded; M44 wires the run |

The workflow JSONs are archived (never deleted) at
`docs/archive/quarantine_2026-10/docker_n8n/n8n/`; every `n8n/workflows/` path
in this document now resolves there. The archive `README.md` records what each
file was and how to restore it.

