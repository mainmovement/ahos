# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** unlock روی `main` (#53) + تیپ PR #57.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## یک‌خطی (در `G:\robat\ahos`)

```bat
cd /d G:\robat\ahos
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/AHOS_APPLY_TIP.bat' -OutFile 'AHOS_APPLY_TIP.bat'"
AHOS_APPLY_TIP.bat
```

## بعد از merge شدن #57

```bat
cd /d G:\robat\ahos
git pull origin main
AHOS_PRE_SOAK_NOW.bat
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
