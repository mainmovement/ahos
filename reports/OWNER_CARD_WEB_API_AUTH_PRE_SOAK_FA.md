# کارت مالک — فقط لپ‌تاپ Windows (به‌سوی PRE_SOAK)

**کد روی main:** PR #31 (auth) + PR #32 (گیت‌رانر).  
**اختیاری:** PR #33 = دابل‌کلیک کامل‌تر (با شروع خودکار Next).  
**DB:** STATE B — `db:migrate` / `db:push` ممنوع. READY جعلی نمی‌شود.

## راه ۱ — دابل‌کلیک (بعد از merge شدن #33)

روی `G:\robat\ahos` بعد از `git pull` فایل `AHOS_WINDOWS_OPS.bat` را دابل‌کلیک کنید.  
خودش: pull → reconcile → preflight → `npm run dev` → انتظار `:3000` → گیت.

## راه ۲ — همین الان روی main (بدون #33)

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

ترمینال دیگر: `npm run dev`  
بعد:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
```

## چی را در Cursor بچسبانید

ترجیحاً کل محتویات:

`reports\OWNER_PASTE_WINDOWS_GATE.txt`

اگر نبود: BEGIN REPORT + `reports\operator_validation_report_windows_*.json`  
(+ در صورت وجود `reports\LATEST_WINDOWS_GATE.txt`)

**هدف این موج:** `pre_soak_entry_ok=true` از JSON ویندوز (G1–G10).  
G11 (تلگرام) برای OPERATOR_READY کامل لازم است — جعل نمی‌شود.
