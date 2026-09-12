# Latest Directive for Ahos cursor configuration Agent

**Updated:** 2026-09-12 (Cycle 002)  
**Status:** `STOP` — read before any action  
**Supervision run:** `bc-da96e388-c281-4c98-be23-903f12552701`  
**Charter:** `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` (binding north-star)

---

## STOP (الان متوقف شو تا این‌ها انجام شود)

1. **W4 (#97–#103) merge نکن** — زنجیره identity fusion جلوتر از W2 ساخته شده
2. **PR جدید باز نکن** تا W1.3 + W2 (#95) آماده merge باشد
3. **Charter §39:** تا اجازه صریح owner، runtime semantics / calibration / scoring consumer تغییر نده

## DO (بعد از STOP، به این ترتیب)

1. **W1.3 hardening:** بستن dynamic class identity spoof
2. **تست:** `test_w1_2_dynamic_class_spoof_is_not_canonical`
3. **W2 (#95):** merge-ready با hardening
4. **مستندات:** `architecture/knowledge/DOSSIER.md` + `docs/DOC_TRUTH_MAP.md`
5. **rename:** `test_w12_*` → `test_w1_2_*`
6. **fail-closed:** security overlay/decision disagreement → conflict

## DO NOT (همیشه)

1. Lane A (`discovery/**`, `paper_trading/**`) — Charter §38
2. ادعای AGI/ACI/world model تحویل‌شده — Charter §42
3. live trading / L6+ execution — Charter §25 (فعلاً L0–L1 فقط)
4. dossier/graph → runtime wiring
5. PR بدون `git push`

## Charter checks (هر commit)

| § | سوال |
|---|------|
| §29 | evidence ≠ score ≠ decision؟ |
| §38 | Lane A دست نخورده؟ |
| §39 | soak مختل نشده؟ |
| §42 | نام فایل = capability نیست؟ |
| §48 | فایل جدید ≠ موفقیت — تست و evidence؟ |

## STOP conditions

- `freeze_lane_a.py` fail
- pytest < 2120 passed
- هر تغییر Lane A
- Charter §39 violation (runtime/scoring during soak)

## Rationale

`docs/supervision/cycles/CYCLE_002_2026-09-12.md`
