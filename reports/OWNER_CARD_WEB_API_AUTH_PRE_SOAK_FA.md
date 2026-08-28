# کارت مالک — فقط لپ‌تاپ (main کافی است)

**کد:** PR #31 روی `main` است. PR #32 اختیاری (گیت‌رانر راحت‌تر).  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## راه ۱ — دابل‌کلیک

بعد از `git pull` روی `G:\robat\ahos` فایل `AHOS_WINDOWS_OPS.bat` را دابل‌کلیک کنید  
(اگر نبود: اول PR #32 را merge کنید، یا از مسیر زیر استفاده کنید).

## راه ۲ — سه دستور (فقط main)

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

ترمینال دیگر: `npm run dev`  
بعد:

```powershell
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

REPORT + JSON را در Cursor بچسبانید.
