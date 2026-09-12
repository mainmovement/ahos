# Latest Directive for Ahos cursor configuration Agent

**Updated:** 2026-09-12 (Cycle 001)  
**Status:** `PROCEED_WITH_CONSTRAINTS`  
**Supervision run:** `bc-da96e388-c281-4c98-be23-903f12552701`

---

## DO (الان انجام بده)

1. **W2 (#95):** قبل از ادامه W4، W2 را با hardening W1.3 آماده merge کن
2. **تست spoof:** `test_w12_dynamic_class_spoof_is_not_canonical` اضافه کن
3. **مستندات:** `architecture/knowledge/DOSSIER.md` + ثبت در `docs/DOC_TRUTH_MAP.md`
4. **نام تست:** `test_w12_*` → `test_w1_2_*` (جلوگیری از اشتباه audit)
5. **fail-closed:** اختلاف security overlay/decision → conflict، نه scalar PASS

## DO NOT (انجام نده)

1. **Lane A** (`discovery/**`, `paper_trading/**`) را ویرایش نکن
2. **زنجیره W4 (#97–#103)** را به `main` merge نکن تا W2 + W1.3 روی main باشد
3. ادعای `PRODUCTION_READY` / `OPERATOR_READY` / AGI/ACI تحویل‌شده نکن
4. dossier/graph را به runtime daemon یا pipeline وصل نکن (read-model isolated)
5. PR جدید بدون `git push` باز نکن (۳ بار fail دیده شد)

## STOP conditions (اگر دیدی، کار را متوقف کن و گزارش بده)

- `freeze_lane_a.py` fail
- `validate_imports.py` fail
- pytest زیر 2120 passed
- هر تغییر در `discovery/` یا `paper_trading/`
- هر wiring مستقیم TS authority بدون `canonicalBackend`

## Authority reminders

- `UNKNOWN > fabricated`
- Python Lane B = canonical decision; TS = read model only
- Classification: `INTEGRATION_READY` — not operator-ready

## Full rationale

See `docs/supervision/cycles/CYCLE_001_2026-09-12.md`
