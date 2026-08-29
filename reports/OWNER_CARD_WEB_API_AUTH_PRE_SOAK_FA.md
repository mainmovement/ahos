# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). تیپ یک‌جا: PR **#58**.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.
**آخرین paste:** `20260828_220318` — G2 خالی، G3–G10 پاس (قبل از #45).

## A) سریع‌ترین — MAIN_FIRST از تیپ #58

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_MAIN_FIRST.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_MAIN_FIRST.bat
AHOS_MAIN_FIRST.bat
```

## B) اگر A شکست — FIX_G2 از همان تیپ

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_FIX_G2_AND_GATE.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_FIX_G2_AND_GATE.bat
AHOS_FIX_G2_AND_GATE.bat
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat` / Desktop `AHOS_PASTE_TO_CURSOR.txt`
- خلاصه: `reports\PRE_SOAK_STATUS.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
**#56 را merge نکنید.** لطفاً #58 را merge کنید.
