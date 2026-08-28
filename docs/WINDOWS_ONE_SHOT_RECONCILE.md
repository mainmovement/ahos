# AHOS — یک دستور برای یکدست‌سازی لپ‌تاپ بعد از merge

این فایل راهنمای owner است. Cloud Agent به `G:\robat\ahos` دسترسی ندارد.

## کار شما (فقط همین)

1. در ویندوز PowerShell را باز کنید.
2. بروید به ریپو:

```powershell
cd G:\robat\ahos
git fetch origin
git pull origin main
```

اگر `pull` به‌خاطر فایل‌های کثیف owner گیر کرد، نگران نباشید — اسکریپت پایین خودش با حفظ owner sync می‌کند. کافی است اسکریپت روی `main` باشد:

```powershell
git fetch origin
git show origin/main:scripts/windows_post_merge_reconcile.ps1 | Out-File -Encoding utf8 scripts\windows_post_merge_reconcile.ps1
```

یا بعد از merge شدن PR مربوطه:

```powershell
git fetch origin
git merge --ff-only origin/main
```

3. فقط این را اجرا کنید:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

4. بعد از merge شدن PR توکن وب (Lane-B auth)، یک‌بار توکن را بسازید/هم‌تراز کنید:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_ensure_web_api_token.ps1
```

سپس Next و ربات را ری‌استارت کنید. **migrate نزنید.**

5. بلوک `BEGIN REPORT` … `END REPORT` را کامل کپی کنید و در Cursor بچسبانید.

## اسکریپت چه می‌کند

- ریپو را به `origin/main` می‌رساند
- سه فایل owner را حفظ می‌کند: `.gitignore`, `deployment/docker-compose.windows.yml`, `reports/backup_restore_drill.json`
- فقط خواندن از Postgres (`SELECT` / `\dt`)
- **هرگز** migrate / reset / stash / force-push نمی‌کند

## اسکریپت چه نمی‌کند

- پروژه را «تمام‌شده» اعلام نمی‌کند
- OPERATOR_READY جعلی نمی‌سازد
- روی DB چیزی نمی‌نویسد
