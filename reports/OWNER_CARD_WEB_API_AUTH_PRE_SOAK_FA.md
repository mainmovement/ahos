# کارت اقدام مالک — PAPER_ONLY تا PRE_SOAK (بدون READY جعلی)

**وضعیت کد:** PR #31 روی `main` merge شده (`967f5dc`)  
**مسدودکننده فعلی:** شواهد ویندوز (توکن + گیت اپراتور) هنوز ارسال نشده  
**DB:** STATE B — **migrate ممنوع**

## فقط این سه دستور

```powershell
cd G:\robat\ahos
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
```

Reconcile توکن وب را می‌سازد. سپس:

```powershell
# Terminal A
npm run dev

# Terminal B
powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
```

REPORT + `reports\operator_validation_report_windows_*.json` را در Cursor بچسبانید.

## حقیقت

| ادعا | وضعیت |
|------|--------|
| Merge #31 | DONE |
| توکن روی لپ‌تاپ | OWNER (reconcile) |
| G1–G10 Windows | OWNER (gate script) |
| OPERATOR_READY | فقط با G11 Telegram E2E |
| migrate | ممنوع (STATE B) |
