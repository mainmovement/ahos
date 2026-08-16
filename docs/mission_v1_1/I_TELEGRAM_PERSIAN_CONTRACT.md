# I. TELEGRAM PERSIAN INTERFACE CONTRACT v0.1 — Mission v1.1 §16/§18 — 2026-08-11
# Builds on docs/TELEGRAM_PERSIAN_UX_DESIGN.md (v0.1). Contract-level, implementation-ready.
# Footer law: every decisional message ends with «تصمیم نهایی با کاربر است.» — no certainty language, ever.

## 1. Inbound intents (NLP intake → structured commands; deterministic ledger authoritative)
| Persian surface form (examples) | Intent | Required slots | Action |
|---|---|---|---|
| «من ۵ میلیون تومان ABC خریدم» · «۵ میلیون تومن از این خریدم» (in token context) | position.open | amount, currency(toman/usdt/dollar), token | parse → **confirmation card** (✔ثبت/✎اصلاح/✖لغو) → PAPER position row |
| «از این ۲ اتریوم خریدم» | position.open(qty) | quantity, token(ETH→major alias map), ±price | same confirm-first flow |
| «این توکن رو زیر نظر بگیر» · «پایشش کن» | watchlist.add | token (context or explicit) | watch row + ack |
| «نصفش رو بفروشم؟» · «نیمشو بدم بیرون؟» | position.partial_exit_query | token; fraction=0.5 | advisory readout (paper P/L, thesis state) + «تصمیم نهایی با کاربر است.» — system executes nothing |
| «وضعیتش چطوره؟» · «وضعیت ABC» | position.status | token (context) | status card §2.4 |
| «موقعیت‌هام» | portfolio.list | — | list + aggregate paper P/L |
| «فرصت‌ها» / «چیزی پیدا کردی؟» | opportunities.list | — | ranked list (rank-first; bullets fa) |
Parsed-confidence < 0.7 or ambiguous token ⇒ clarifying question (never guess financial records).
Numbers: Persian/Arabic-Indic digits + Latin accepted (۵≡5); typo map for تومان/تومن/تتر/دلار.

## 2. Outbound message classes (exact contracts)
1. 🚨 OPPORTUNITY (rank-surface this wave; numbers only post-calibration):
   header «فرصت جدید پیدا شد» · token/chain · رتبه/امتیاز* · چرا (≤۵ بولت شواهد فارسی) · ریسک (≤۳) ·
   توصیه: {پایش/صبر/پرریسک†/اجتناب} · ابطال‌گرها (لیست شرطی) · footer. *score hidden until research gate; †needs user risk-mode + gates.
2. 🟢 IMPROVING / 🟡 MONITOR / 🟠 RISK-UP / 🔴 INVALIDATED / 🚨 SECURITY-EVENT:
   «چه چیزی عوض شد» · «چرا مهم است» · شواهد · اعتماد(و غیرقطعیت) · ریسک · اقدام پیشنهادی کاربر · footer.
3. 📊 POSITION status: entry vs now · paper سود/زیان٪ · حالت سناریو · «شرایط خروج کامل فعال نشده» (اگر چنین است).
4. ⚠️ PARTIAL-PROFIT advisory: دلایل لیستی + درصد پیشنهادی از قوانین ریسک (نسخه‌بندی‌شده)، نه احساس.
5. 🔴 FULL-EXIT advisory: دلایل + «اقدام پیشنهادی: خروج/بررسی خروج».
6. ℹ️ SYSTEM: boot «AHOS SYSTEM ONLINE» (fa variant فاز ۶) · خطای دیتا (شفاف، بدون سکوت) · «هیچ فرصتی نیست» (خروجی معتبر و موفق — به‌صورت خلاصهٔ دوره‌ای، نه اسپم).

## 3. Delivery & auth
- All outbound via PAL telegram adapter; env-only token; rate-safe batching; alert dedupe (alert_id unique per token/level/transition).
- Inbound admin-gate = TELEGRAM_ADMIN_CHAT_ID (env); unauthenticated ⇒ reject + AUTH_FAIL audit (wave-3 harness law, unchanged).
- RTL safety: bullet lists; Latin tickers embedded safely; digits fa for مجوعات کاربر، لاگ‌ها latin.

## 4. Test contract (Phase-6 CI)
tests/fixtures/telegram_fa/*.golden — parser fixture set (≥12 utterances incl. all table rows) 100% pass;
renderer snapshot tests per message class; footer-presence assertion on every decisional class;
no-English-leak lint for user-facing fields.
