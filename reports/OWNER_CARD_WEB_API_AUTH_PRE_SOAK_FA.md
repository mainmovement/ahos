# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). تیپ PR #57 برای مسیر جراحی.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## سریع‌ترین (فقط main)

```bat
cd /d G:\robat\ahos
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows_ensure_web_api_token.ps1
AHOS_PRE_SOAK_NOW.bat
```

## اگر A شکست — تیپ جراحی

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_FIX_G2_AND_GATE.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/AHOS_FIX_G2_AND_GATE.bat
AHOS_FIX_G2_AND_GATE.bat
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat`
- خلاصه: `reports\PRE_SOAK_STATUS.txt` (روی تیپ)

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
