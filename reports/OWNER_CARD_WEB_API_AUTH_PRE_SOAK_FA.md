# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** unlock تیپ PR #57.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## اگر آخرین پیست فقط G2 خالی بود (G3–G10 پاس)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_FIX_G2_AND_GATE.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/AHOS_FIX_G2_AND_GATE.bat
AHOS_FIX_G2_AND_GATE.bat
```

## مسیر کامل (اولین بار)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_BOOTSTRAP_PRESOAK.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/AHOS_BOOTSTRAP_PRESOAK.bat
AHOS_BOOTSTRAP_PRESOAK.bat
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat`
- خلاصه: `reports\PRE_SOAK_STATUS.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
