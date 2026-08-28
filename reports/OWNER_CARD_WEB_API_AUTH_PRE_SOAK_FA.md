# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** PR #31–#36 روی `main` (`1dcc2c2`).  
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

- Ctrl+V محتوای `reports\OWNER_PASTE_WINDOWS_GATE.txt` در چت Cursor  
- یا کامنت `gh` روی PR #36  
- حتی اگر bat وسط راه fail شد، همان فایل paste را بفرستید

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام جداست.
