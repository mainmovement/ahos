# AHOS — TELEGRAM PERSIAN UX DESIGN v0.1 (DESIGN — Maturity A)
# Language: simple natural Persian. Footer on every decisional message: «تصمیم نهایی با کاربر است.»

## Message templates (texts are versioned; rendered by engine/ux_fa.py at implementation)
1) 🚨 فرصت جدید — «فرصت جدید پیدا شد: {token} ({chain}) · امتیاز: {score}/۱۰۰ · اعتماد: {conf}٪»
   دلیل اصلی (حداکثر ۵ گلوله شواهد) · ریسک‌ها (حداکثر ۳) · توصیه: {WATCH/WAIT/AVOID…} · ابطال‌گرها:
   «اگر نقدینگی از {x} کمتر شود / نهنگ‌ها توزیع کنند / … امتیاز خودکار کاهش می‌یابد.»

2) 📊 وضعیت {token} — قیمت خرید: {entry} · فعلی: {price} · سود/زیان: {pnl٪} ·
   وضعیت سناریو: {strengthening/weakening/invalidated} · «شرایط خروج کامل فعال نشده.»

3) ⚠️ سیو سود پیشنهادی — دلایل ضعیف‌شدن سناریو (لیست) + درصد پیشنهادی (از قوانین ریسک، نه احساس)

4) 🔴 خروج/ابطال — دلایل (لیست) + اقدام پیشنهادی + «تصمیم نهایی با کاربر است.»

5) سطوح هشدار پایش — 🟢 تقویت · 🟡 تغییر · 🟠 ریسک رو به رشد · 🔴 ابطال · 🚨 رویداد امنیتی · 🚀 شتاب غیرعادی

## Natural-language position intake (Persian-first)
Parse: «من ۵ میلیون تومان {token} خریدم» / «۵ میلیون ABC خریدم» / «۲۰ دلار سول گرفتم»
→ extract {amount, currency(تومان/دلار/USDT), token, approx price at time} →
CONFIRMATION card (inline buttons: «✔ ثبت» / «✎ اصلاح» / «✖ لغو») → positions row.
Never silently register financial claims — confirmation is mandatory (Human Gate at UX level).

## Command surface (extends workflow 03 — read/health/agents/kill/reset stay English-literal commands)
/ موقعیت‌هام · / فرصت‌ها · / وضعیت {token} · / توقف (/kill) · / ریست (/reset) · / کمک
Slash-Latin aliases preserved; Persian free text routed through intent parser with confidence ≥0.7;
below → clarifying question. All UX Persian, all logs code.

## Tone rules
No imperative purchase verbs. Use «پیشنهاد سیستم». Numbers in Persian digits for user-facing %; raw
values in detail view. NEVER a probability without «برآورد» prefix and uncertainty note.
