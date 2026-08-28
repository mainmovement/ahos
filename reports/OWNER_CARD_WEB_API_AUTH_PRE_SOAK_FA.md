# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** unlock روی `main` (#53) + تیپ PR #57.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## یک‌خطی (در `G:\robat\ahos`)

```bat
cd /d G:\robat\ahos
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/scripts/windows_bootstrap_presoak.ps1 -OutFile scripts\windows_bootstrap_presoak.ps1; powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows_bootstrap_presoak.ps1"
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
