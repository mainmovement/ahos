# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** empty-gateway روی `main` است (#45). تیپ یک‌جا: PR **#58**.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## A) ترجیحی — دانلود .cmd و دوبارکلیک

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_RUN_TIP.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.cmd
AHOS_RUN_TIP.cmd
```

## B) PowerShell با TLS1.2

```bat
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; iex (iwr -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.ps1').Content"
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا Desktop `AHOS_PASTE_TO_CURSOR.txt`
- خلاصه: `reports\PRE_SOAK_STATUS.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
**#56 را merge نکنید.** لطفاً #58 را merge کنید.
