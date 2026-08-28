# Goal status — Windows PAPER_ONLY operational (honest)

**Generated (UTC):** 2026-08-28T20:48Z  
**main tip:** `d9a50f3` (includes PR #31 + #32)  
**Claim:** tooling READY for owner Windows run — **OPERATOR_READY = NOT_VERIFIED**

## Requirement audit

| Requirement | Evidence | Status |
|-------------|----------|--------|
| Merge web-api auth | PR #31 merged → `web_api_auth.ts` on main | **DONE** |
| Set tokens on laptop | No Windows REPORT / `.env` attestation pasted | **MISSING** (owner) |
| STATE B / no migrate | Reconcile + docs forbid migrate; STATE B classification | **ENFORCED in code/docs** (Windows runtime not re-verified this turn) |
| Operator validation G1–G10 | No `reports/operator_validation_report_windows_*.json` | **MISSING** (owner) |
| Toward PRE_SOAK | Needs `summary.pre_soak_entry_ok=true` from Windows JSON | **BLOCKED** |
| G11 for full OPERATOR_READY | Telegram E2E artifact | **MISSING** (owner) |
| No invented READY | Agent-host never claims Windows READY | **HONORED** |

## On main now (owner can run)

- `scripts/windows_post_merge_reconcile.ps1` (sync + token ensure)
- `scripts/windows_ensure_web_api_token.ps1`
- `scripts/windows_run_operator_gate.ps1`
- `scripts/operator_validation_gate.py` (Bearer + OWNER_NEXT remediations)

## Optional (PR #33)

- `AHOS_WINDOWS_OPS.bat` double-click wrapper

## Exact owner commands

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
# other window: npm run dev
powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
```

Paste REPORT + gate JSON into Cursor. Do **not** `db:migrate` / `db:push`.
