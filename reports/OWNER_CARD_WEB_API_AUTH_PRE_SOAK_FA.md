# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** PR #31–#34 روی `main`. PR #35 باز است (postgres ensure + ضد جعل READY).  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## فقط این (الان، قبل از merge #35)

```powershell
cd G:\robat\ahos
git fetch origin
git checkout cursor/windows-main-unlock-4bde
git pull origin cursor/windows-main-unlock-4bde
```

سپس دابل‌کلیک: `AHOS_WINDOWS_OPS.bat`

بعد از merge #35 کافی است: `git pull origin main` سپس همان bat.

## خروجی برای Cursor

- اگر `gh` لاگین است: کامنت خودکار روی PR  
- وگرنه: Ctrl+V فایل `reports\OWNER_PASTE_WINDOWS_GATE.txt`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows واقعی). G11 تلگرام جداست.
