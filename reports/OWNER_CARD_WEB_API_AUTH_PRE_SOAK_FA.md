# کارت اقدام مالک — مسیر PAPER_ONLY تا PRE_SOAK (بدون READY جعلی)

**تاریخ:** 2026-08-28  
**مسدودکننده فعلی:** PR #31 هنوز روی `main` merge نشده  
**DB:** STATE B — **migrate ممنوع**

## یک مسیر (بعد از Merge #31)

روی لپ‌تاپ:

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

Reconcile حالا در صورت وجود `web_api_auth.ts` توکن وب را هم می‌سازد.

سپس:

```powershell
# ترمینال A
npm run dev

# ترمینال B
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

JSON گیت + REPORT را در Cursor بچسبانید.

## حقیقت

| ادعا | وضعیت |
|------|--------|
| Merge #31 | OWNER |
| توکن وب روی لپ‌تاپ | بعد از reconcile / ensure script |
| STATE B / no migrate | الزام |
| `pre_soak_entry_ok` | فقط اگر G1–G10 روی Windows همه PASS |
| `OPERATOR_READY` | فقط با G11 (Telegram E2E artifact) هم |

Cloud Agent به `G:\robat\ahos` دسترسی ندارد — بدون گزارش ویندوز READY اعلام نمی‌شود.
