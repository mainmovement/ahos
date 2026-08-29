# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). تیپ یک‌جا: PR **#58**.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.
**مهم:** فایل `.bat` را از raw گیت‌هاب `curl` نکنید (LF است و cmd می‌شکند). از PowerShell زیر کنید.

## A) ترجیحی — CRLF-safe

```bat
cd /d G:\robat\ahos
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex (iwr -useb https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.ps1).Content"
```

## B) اگر A شکست — FIX_G2

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File .\AHOS_RUN_TIP.ps1 -Mode fix_g2
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا Desktop `AHOS_PASTE_TO_CURSOR.txt`
- خلاصه: `reports\PRE_SOAK_STATUS.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
**#56 را merge نکنید.** لطفاً #58 را merge کنید.
