# E-01 — EXPERIMENTAL VALIDATION REPORT · GATE 2026-08-14T18:00Z

Guardian hashes at execution: Master Directive v1 `e2457c0d…d837d79` ✓ · E01_GATE_PROTOCOL_v1
`16b86b86…a168101` ✓ · executed modules: feature_store `202bbe6d…`, materialize `14470161…`,
lifecycle `fd33e7e5…`, outcomes `5186b575…`, baseline_stats `7efefb01…` (all = pre-gate frozen
bytes; verified identical post-run).

---

## خلاصه‌ی فارسی (Persian summary)

**نتیجه‌ی نهایی رسمی گیت: INVALID_PROTOCOL (به‌علت نقص لوله‌ی اجرا) — همزمان داده به‌طور حسابی INSUFFICIENT_DATA را اجباری می‌کرد. وضعیت آزمایش: NOT YET VALIDATED.**

۱) گیت دقیقاً در پنجره‌ی قانونی خود و با دستور مالک اجرا شد (شروع 18:06Z = 21:36 ایران). ابتدا integrity حاکمیت و workspace تأیید شد (همه‌ی فایل‌های پایدار sha-identical با W17؛ هر دو هش پروتکل pin شدند).
۲) `discovery.materialize` طبق پروتکل اجرا شد اما در مرحله‌ی features با `ValueError: math domain error` در `discovery/feature_store.py:157` سقوط کرد. علت ریشه‌ای با evidence کامل کشف شد: guard نامتقارن — فقط `prev_v1>0` چک شده، `last_v1` نه؛ ۲۴ توکن از ۹۵۲ توکن با آخرین `volume_1h = 0.0` (پدیده‌ی طبیعی در cohort گرسنه) ⇒ `log(0)`. این نقص در کد فریزشده‌ی Lane A نهفته بود و باتری تست هرگز ورودی حجمی صفر را تمرین نداده بود؛ روی داده‌ی واقعی در روز گیت ظاهر شد.
۳) **هیچ نوشتاری در DB ماندگار نشد** — rollback خودکار؛ تمام شمارنده‌ها دقیقاً برابر وضعیت پیش از گیت (952 توکن / 1736 مشاهده / 952 OBSERVING / gap_register 826 / outcome_label 0) و `integrity_check = ok`.
۴) طبق STRICT FREEZE و دستور مالک، هیچ تعمیر/دورزدنی روی Lane A انجام نشد؛ نقص ثبت شد (artifact R8.1) و اجرای بقیه‌ی مراحل با همان پروتکل متوقف ماند، اما همه‌ی محاسبات read-only قانونی انجام و گزارش شد.
۵) اعداد کلیدی: R1 واقعی = resolved 0 / covered 0 (معیار گیت 0 < 200)؛ فرضیه‌ی read-only: حتی با sweep کامل 88 توکن ≥72h می‌شدند و **۰** تای آن‌ها در پنجره‌ی closure قانونی مشاهده داشت ⇒ INSUFFICIENT_DATA از نظر داده غیرقابل‌اجتناب بود. Track B: 0 بسته‌شده / 0 تطبیق هزینه ⇒ **NOT MET** (حسابی). Baseline: هر ۹ سلول پیش‌ثبت‌شده INSUFFICIENT_DATA (n=0).
۶) پوشش به تفکیک افق (ادغام ممنوع): s+15m 12.1% · s+1h 8.4% · s+4h 22.2% · **s+12h 0%** · s+24h 13.3% · **s+48h 0%** (POST_FIX: 38.4/21.8/26.6/0/17.8/0). G-SCHED باز هم قید اصلی است: شکاف ساعتی 05:19Z→18:06Z ⇒ پنجره‌های K1×7 و K2×4 امروز MISSED شدند؛ قانوناً بدون backfill ثبت خواهند شد.
۷) اقدام دقیق بعدی در انتهای این سند.

تصمیم نهایی با کاربر است.

---

## ENGLISH ARTIFACT

### Gate execution record
| item | value |
|---|---|
| gate due | 2026-08-14T18:00:00Z |
| execution start (verified UTC) | 2026-08-14T18:06:00Z (+6 min; owner-ordered "execute now") |
| pre-gate integrity | all persistent files sha-identical to manifest w17; both governance hashes pinned ✓ |
| materialize | **CRASHED** in `materialize_features` (token #272 of 952) — `ValueError: math domain error`, `discovery/feature_store.py:157` |
| writes persisted | **none** (implicit rollback; post-crash census == pre-gate census; pragma ok) |
| stages reached | features only (partial, rolled back) — sweep/labels NOT reached |

### Defect record (new finding — registered as gate-day protocol halt)
- Root cause: asymmetric guard — `prev_v1[1] > 0` checked, `last_v1[1] > 0` not checked ⇒
  `math.log(0.0)` for tokens whose latest `volume_1h` at/before as_of is 0.0.
- Population: **24/952 tokens** reproduce (list in artifact R8.1); 928 compute cleanly.
- History: latent in frozen code since feature_store v0.2; test battery never fed zero-volume
  observations; surfaced first on live starved cohort at gate execution.
- Freeze law obeyed: **no code edit on gate day**; no workaround; defect fixed only via
  owner-gated versioned amendment (see Next Action).

### R1 — resolved accounting (both ways, per protocol)
| measure | value | note |
|---|---|---|
| n_resolved_state (actual) | **0** | sweep never ran (crash); state census 952 OBSERVING |
| n_resolved_covered (actual, THE gate metric) | **0** | outcome_label = 0 |
| gate requirement | ≥200 | **0 < 200** |
| hypothetical (read-only, tick-equivalent) | state 88 / covered **0** | labeled READ-ONLY HYPOTHETICAL; none of the 88 has any obs in the legal 72h closure window |

### R2 — PRE/POST segmentation (activation 2026-08-13T04:30:33Z)
PRE_FIX: 987 obs / 762 tokens · POST_FIX: 749 obs / 451 tokens. Horizon-by-horizon coverage in artifact #2 (merged metrics forbidden; reported separately, e.g., POST s+15m 38.4% vs s+12h 0.0%).

### R4 — baseline comparison (pre-registered budget only)
9 cells (B1×2 + B2×7, H14/H15/H18/H20) via `research/baseline_stats.py`, guards n≥200 / pos≥20:
**9/9 → INSUFFICIENT_DATA** (n_baseline = 0, pos = 0 in every cell). No new hypotheses minted.
Artifact: `research/reports/baseline_stats_e01_gate_20260814.json`.

### R5 — Track B (arithmetic, not narrative)
0 closed trades · 0 cost reconciliations · 11 open v2 positions · cash $1.8984375 conserved ⇒
**NOT MET**. NO_DATA(STALE_OBSERVATION) streak = safety-law behavior, not exits.

### R6 — deviations on gate day (recorded before reporting)
1. Execution at +6 min (18:06Z) — owner-ordered immediacy; cutoff-based, no impact on legality.
2. Forced halt at protocol step 3 — pipeline defect (not a chosen deviation). Evidence: artifact R8.1.
No other deviations; registry untouched (cells used as registered; no re-registration).

### R7 — verdict (exactly one from the alphabet)
## **INVALID_PROTOCOL**
Rationale: a pipeline defect voided this window's gate computation — the frozen pipeline could not
produce features/sweep/labels, so the gate artifact chain cannot certify Track A. **Independently**,
R1/R2 arithmetic shows that even a perfect run today would terminal at **INSUFFICIENT_DATA**
(0 covered, <200). Both statements are required by honesty law; neither is weakened.

### Experiment statement
**E-01 = NOT YET VALIDATED.** (Reason: gate unconcluded by defect + coverage insufficiency.)
This is a measurement of today's evidence, not a verdict on the experiment's future.

### Failures / gaps
- Defect D-FS-01 (above). · G-SCHED: two buried window clusters today (K1×7 s+48h 06:45:57Z;
  K2×4 08:11:48Z) — cause = session-clock gap 05:19Z→18:06Z; recorded, not fixed (owner order).
- gap_register = 826 frozen since last sweep; all later misses pending lawful registration at the
  post-fix materialize re-run (no backfill; `missed:<slot>` registration only).
- F12 = **MITIGATION DEPLOYED** (unchanged; O2a scheduler is NOT the crash site — verified: crash
  is in pre-F12 frozen feature_store; poller itself performed as designed on 2026-08-13/14 runs).

### R8 — artifact chain (paths)
1. `reports/e01_gate_materialize_20260814T1806Z_FAILURE.json` (run report, failure form, 24-token list, traceback, hashes)
2. `reports/e01_gate_cohort_report_20260814.md` (cohort + R2 segmentation + horizon table)
3. `research/reports/baseline_stats_e01_gate_20260814.json` (9 cells, verdicts)
4. `reports/e01_gate_sufficiency_audit_20260814.json` (R1–R7 numbers + verdict)
5. this report (fa summary + en artifact)

### Exact next action
**A-1 (owner decision required — Lane A amendment):** minimal versioned fix in
`discovery/feature_store.py`: guard `last_v1[1] > 0` (mirroring the existing prev-guard) for
`volume_growth_1h`; tests-first: new zero-volume fixture test (red-first), then fix, full
regression, rollback archive. No other change.
**A-2:** re-run the **identical** frozen gate sequence (`discovery.materialize → cohort →
baseline → R1–R8`). Replayable by construction: all inputs are stored observations guarded by
immutability triggers; sweep then registers all pending `missed:*` slots lawfully; verdict is
arithmetic-expected INSUFFICIENT_DATA unless new data arrives.
**A-3:** Lane A cadence continues (collect/observe/paper cycle per standing law); §O PT cadence
per PT-X3; user blockers stand (Telegram keys, VPS/host, AI keys).
