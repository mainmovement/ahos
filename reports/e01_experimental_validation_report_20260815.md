# E-01 — EXPERIMENTAL VALIDATION REPORT · REPLAY POST D-FS-01 FIX (2026-08-15)

Guardian hashes at execution:
- Master Directive v1: `e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79` ✓
- E01_GATE_PROTOCOL_v1: `16b86b86e89392c3f84d82a1c2c6d87534fea988c4dff5a1454fcc137a168101` ✓
- Executed modules: feature_store `d3086e729f5cf1018cfd8d102d5f65153d6878148fce5cfe9bc10901b98c1e1c` (amended per A-1), materialize `144701613f13…`, lifecycle `fd33e7e5bb9d…`, outcomes `5186b5750831…`, baseline_stats `7efefb015cc3…`.

---

## خلاصه‌ی فارسی (Persian summary)

**نتیجه‌ی نهایی گیت در اجرای مجدد قانونی (Replay): INSUFFICIENT_DATA (به‌دلیل عدم کفایت آماری مشاهدات در افق ۷۲ ساعته و سلول‌های پایه). وضعیت آزمایش: NOT YET VALIDATED.**

۱) اصلاحیه قانونی A-1 روی نقص D-FS-01 (عدم تقارن گارد حجم در `discovery/feature_store.py:157`) به روش Test-First اجرا شد: ابتدا تست با خروجی قرمز (Red) خطای `math domain error` را اثبات کرد، سپس گارد حداقلی `last_v1[1] > 0` اعمال شد، تست سبز (Green) گردید، رگرسیون کامل با ۲۶۱ تست پاس شد و نسخه قبلی در آرشیو ثبت شد.
۲) بازپخش قانونی پروتکل E-01 با دستور `discovery.materialize` با موفقیت کامل و بدون خطا اجرا شد:
   - ویژگی‌های تمام ۹۵۲ توکن استخراج و ۶,۷۴۵ سطر بردار ویژگی (`fs_v0.2`) ذخیره شد.
   - وضعیت تمام ۹۵۲ توکن به‌روزرسانی شد: ۲۲۳ توکن RESOLVED و ۷۲۹ توکن DEAD.
   - شکاف‌های مشاهده قانونی در `gap_register` ثبت شد (مجموع ۵,۳۳۹ سطر شامل تمام اسلات‌های overdue بدون جعل داده یا backfill).
   - برای توکن‌های واجد شرایط، ۱,۰۴۸ سطر outcome_label تولید شد.
۳) معیارهای R1 تا R8:
   - **R1 (وضعیت و پوشش RESOLVED):** تعداد `n_resolved_state = 223`، اما تعداد `n_resolved_covered` در افق ۷۲ ساعته برابر **۵۲** است که از حد نصاب ۲۰۰ کمتر است (52 < 200).
   - **R2 (تفکیک دوره‌ها):** دوره PRE_FIX شامل ۹۸۷ مشاهده روی ۷۶۲ توکن؛ دوره POST_FIX شامل ۷۴۹ مشاهده روی ۴۵۱ توکن.
   - **R4 (تحلیل پایه‌ها):** تمام ۹ سلول پیش‌ثبت‌شده (B1 و B2) وضعیت **INSUFFICIENT_DATA** دریافت کردند (حجم نمونه n_base < 200 و رویدادهای مثبت < 20).
   - **R5 (ترک B - معاملات کاغذی):** تعداد ۰ معامله بسته شده / ۰ تطبیق هزینه / ۱۱ پوزیشن باز / موجودی نقد ۱.۸۹۸۴۳۷۵ دلار ⇒ وضعیت: **NOT MET**.
   - **R6 (انحرافات):** اجرای بازپخش پس از اصلاحیه حداقلی مصوب A-1 بدون هیچ انحراف یا تغییر در فرضیات.
   - **R7 (حکم نهایی پروتکل):** **INSUFFICIENT_DATA**.
۴) وضعیت آزمایش: **NOT YET VALIDATED** (نیاز به جمع‌آوری داده‌های تازه در کوهورت‌های آتی و ادامه کارکرد poller بدون دستکاری گذشته).

تصمیم نهایی با کاربر است.

---

## ENGLISH ARTIFACT

### Replay Execution Record
| Item | Value |
|---|---|
| Replay timestamp | 2026-08-15T07:10:00Z |
| Prerequisite | A-1 D-FS-01 minimal fix verified & hash-pinned |
| Governance status | Master Directive v1 & E01_GATE_PROTOCOL_v1 pinned ✓ |
| Materialize execution | **SUCCESS (0 errors)** — 952 tokens processed, 6,745 feature rows written |
| Observation state census | 223 RESOLVED, 729 DEAD, 0 OBSERVING, 0 DISCOVERED (Total: 952) |
| Outcome labels written | 1,048 rows across 223 RESOLVED tokens |
| Gap register rows | 5,339 overdue snapshot gaps lawfully registered (no backfill) |

### R1 — Resolved Accounting
| Measure | Value | Protocol Requirement | Status |
|---|---|---|---|
| `n_resolved_state` | 223 | — | Counted |
| `n_resolved_covered` (72h outcome exists) | **52** | ≥ 200 | **NOT MET (52 < 200)** |

### R2 — Segmentation (Activation 2026-08-13T04:30:33Z)
- PRE_FIX (retrieved_ts < activation): 987 obs / 762 tokens
- POST_FIX (retrieved_ts ≥ activation): 749 obs / 451 tokens

### R4 — Baseline Comparison (9 Pre-registered Cells)
All 9 pre-registered cells evaluated via `research/baseline_stats.py`:
- 9/9 return **INSUFFICIENT_DATA** (n_base < 200 and positives < 20).
- Zero exploratory cells minted; zero p-hacking.

### R5 — Track B Accounting (Arithmetic)
- Open paper trades: 11
- Closed paper trades: 0 (Threshold: ≥ 30)
- Realized cost reconciliations: 0 (Threshold: ≥ 1)
- Cash balance: $1.8984375
- Status: **NOT MET**.

### R7 — Protocol Verdict
## **INSUFFICIENT_DATA**

### Overall Experiment Status
**E-01 = NOT YET VALIDATED.**
Validation criteria remain unsatisfied due to statistical data starvation. Immutability laws hold: no historical observations were backfilled or altered.
