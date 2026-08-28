# کارت مالک — فقط لپ‌تاپ Windows (به‌سوی PRE_SOAK)

**کد روی main:** PR #31 (auth) + PR #32 (گیت‌رانر).  
**توصیه قوی:** PR #33 (بات + ری‌استارت Next + پیست خودکار).  
**DB:** STATE B — `db:migrate` / `db:push` ممنوع. READY جعلی نمی‌شود.

## راه ۱ — دابل‌کلیک (PR #33)

روی `G:\robat\ahos` فایل `AHOS_WINDOWS_OPS.bat` را دابل‌کلیک کنید.  
خودش: pull → reconcile (بدون حذف هلپرها) → preflight → **ری‌استارت Next** → گرم‌کردن `/api/chat` → گیت → کپی در کلیپ‌بورد.

سپس در Cursor: **Ctrl+V** (یا فایل `reports\OWNER_PASTE_WINDOWS_GATE.txt`).

## راه ۲ — main بدون #33

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

**مهم:** اگر `:3000` قبل از توکن روشن بود، Next را ببندید و دوباره `npm run dev`.  
بعد:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
```

## چی را در Cursor بچسبانید

`reports\OWNER_PASTE_WINDOWS_GATE.txt` یا BEGIN REPORT + JSON گیت.

**توجه:** G4/G5/G8/G9 از SQLite محلی می‌آیند نه از شمارش Postgres STATE B.  
اگر FAIL شدند یک single-cycle محلی بزنید و گیت را تکرار کنید.

**هدف این موج:** `pre_soak_entry_ok=true` (G1–G10). G11 تلگرام برای OPERATOR_READY کامل است — جعل نمی‌شود.
