# n8n Operational Procedure

**Status:** JSON VALID ≠ OPERATIONAL  
**Structural validation:** `python tests/validate_n8n.py` (6/6)  
**Live execution:** OWNER_ACTION_REQUIRED / EXTERNAL_BLOCKED without credentials  
**QUARANTINED (do not import):** `n8n/workflows/ahos_03_telegram_control.json` — see `reports/grok/GM06_N8N_QUARANTINE.md`

## Structural (agent/CI can do)

```powershell
python tests\validate_n8n.py
```

Workflows live under `n8n/workflows/`.

## Operational (owner)

1. Install n8n (native or Docker — prefer documented Windows path in deployment docs)
2. Import each JSON in `n8n/workflows/` **except quarantined ones** (`ahos_03_telegram_control.json` — the validator prints `[QUARANTINED(do-not-import)]`)
3. Configure credentials referenced by nodes (Telegram, HTTP, etc.) — never commit secrets
4. Set environment variables to match local AHOS ports/paths
5. Activate workflows one at a time
6. Trigger a test execution; confirm:
   - webhook receives payload
   - error path does not invent market data
   - retries behave as configured
7. Archive execution screenshots/IDs under `reports/n8n_ops_<UTC>/`

Until step 6–7 succeed: **n8n = JSON VALID only**.
