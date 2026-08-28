# کارت مالک — PRE_SOAK (Windows PAPER_ONLY)

**کد:** unlock روی `main` (#53) + تیپ PR #57 (اگر هنوز merge نشده).  
**DB:** STATE B — migrate ممنوع. READY جعلی نمی‌شود.

## مسیر سریع (اگر #57 هنوز merge نشده)

```bat
cd /d G:\robat\ahos
git fetch origin cursor/windows-evidence-notify-retarget-4bde
git checkout origin/cursor/windows-evidence-notify-retarget-4bde -- AHOS_APPLY_TIP.bat
AHOS_APPLY_TIP.bat
```

## بعد از merge شدن #57

```bat
cd /d G:\robat\ahos
git pull origin main
AHOS_PRE_SOAK_NOW.bat
```

## خروجی برای Cursor (الزامی)

- `reports\OWNER_PASTE_WINDOWS_GATE.txt` را در PR **#56** (باز بماند) یا **#38** کامنت کنید
- یا `AHOS_PUSH_EVIDENCE_NOW.bat`

هدف: `pre_soak_entry_ok=true` (G1–G10 روی Windows). G11 تلگرام فقط برای OPERATOR_READY.
