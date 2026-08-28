# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** web-api auth + G2 fixes روی `main` / unlock tip PR #53.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.  
**توجه:** ردیف‌های Postgres برای G4/G5/G8/G9 کافی نیستند — SQLite محلی لازم است.

## فقط این

```bat
cd /d G:\robat\ahos
git pull origin main
AHOS_PRE_SOAK_NOW.bat
```

اگر `/api/chat` هنوز 500 بود: `AHOS_VALIDATE_G2_NOW.bat`  
(با ریکاوری forensics + DATABASE_URL + restart)

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در Cursor بچسبانید
- یا کامنت روی PR #54 / #53 / #38
- حتی اگر bat وسط راه fail شد، همان paste را بفرستید

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام فقط برای OPERATOR_READY.
