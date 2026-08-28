# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** PR #31–#40 روی `main` (`24151d6`) — شامل رفع PS 5.1 (ASCII + UTF-8 BOM + parse preflight).  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.  
**توجه:** ردیف‌های Postgres برای G4/G5/G8/G9 کافی نیستند — SQLite محلی لازم است.

## فقط این

```powershell
cd G:\robat\ahos
git checkout main
git pull origin main
```

سپس دابل‌کلیک: `AHOS_WINDOWS_OPS.bat`

## خروجی برای Cursor (الزامی)

- Ctrl+V از کلیپ‌بورد یا فایل دسکتاپ `AHOS_PASTE_TO_CURSOR.txt`
- یا محتوای `reports\OWNER_PASTE_WINDOWS_GATE.txt`
- حتی اگر bat وسط راه fail شد، همان paste را بفرستید

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام جداست.
