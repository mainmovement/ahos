# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). آخرین پیست `220318` قبل از #45 بود (G2 BLOCKED).  
**اول merge کن:** PR **#59**. PR **#56** و **#60** را باز نگه دار.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## فقط این (لپ‌تاپ)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_G2_CLEAR_MAIN.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-ops-evidence-push-main-4bde/AHOS_G2_CLEAR_MAIN.cmd
AHOS_G2_CLEAR_MAIN.cmd
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** یا **#38** کامنت کنید
- یا فایل دسکتاپ `AHOS_PASTE_TO_CURSOR.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام فقط برای OPERATOR_READY.
