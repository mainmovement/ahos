# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** PR #31–#35 روی `main`. Harden بعدی: `cursor/windows-g1-g10-harden-4bde`.  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.  
**توجه:** ردیف‌های Postgres برای G4/G5/G8/G9 کافی نیستند — SQLite محلی لازم است.

## فقط این (الان)

```powershell
cd G:\robat\ahos
git fetch origin
git checkout cursor/windows-g1-g10-harden-4bde
git pull origin cursor/windows-g1-g10-harden-4bde
```

سپس دابل‌کلیک: `AHOS_WINDOWS_OPS.bat`

بعد از merge harden: `git checkout main && git pull origin main` سپس همان bat.

## خروجی برای Cursor

- اگر `gh` لاگین است: کامنت خودکار روی PR  
- وگرنه: Ctrl+V فایل `reports\OWNER_PASTE_WINDOWS_GATE.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام جداست.
