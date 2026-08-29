# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). آخرین پیست `220318` قبل از #45 بود (G2 BLOCKED).  
**اول merge کن:** PR **#59** (MAIN_CLEAR). PR **#56** را باز نگه دار (paste sink).  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## فقط این (لپ‌تاپ)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/4adfacb3154943a119396f5d7d82c06943a61a53/AHOS_MAIN_CLEAR_G2.cmd
AHOS_MAIN_CLEAR_G2.cmd
```

بعد از merge شدن #59 می‌توانی از `main` بگیری:

```bat
curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/main/AHOS_MAIN_CLEAR_G2.cmd
AHOS_MAIN_CLEAR_G2.cmd
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا فایل دسکتاپ `AHOS_PASTE_TO_CURSOR.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام فقط برای OPERATOR_READY.
