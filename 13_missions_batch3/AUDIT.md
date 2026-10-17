# AUDIT — دسته ۳ مأموریت‌های AHOS Arena (2026-10-16)

هیچ ادعایی بدون اجرا ثبت نشده است. موارد اجرا‌نشده صراحتاً NOT RUN/NOT DELIVERED
هستند.

## جدول وضعیت صفحه‌ها

| صفحه | مسیر | مأموریت | وضعیت | داده | تست‌ها (نوشته/اجرا/نتیجه) | اسکرین‌شات | شکاف‌های شناخته‌شده |
|---|---|---|---|---|---|---|---|
| رادار علم | `/arena/science-radar` | M44 (Science Radar) | DONE | فقط DEMO (نمونه‌ی قرارداد + ماک؛ endpoint واقعی bind نشده) | 35/35/35 سبز (کل مجموعه) | NOT DELIVERED | endpoint واقعی AHOS bind نشده (بلوک `BIND AHOS ENDPOINT HERE` آماده است) |
| خطایابی خودکار | `/arena/self-debug` | M46 (Self-Debug) | DONE | فقط DEMO | در همان ۳۵ | NOT DELIVERED | timeline/لاگ فقط از قرارداد می‌آید؛ هیچ اقدامی (restart/patch/apply) پیاده نشده — عمداً |
| آزمون هفتگی هوش | `/arena/weekly-exam` | M50 (Weekly Intelligence Exam) | DONE | فقط DEMO | در همان ۳۵ | NOT DELIVERED | برچسب هفته (Jalali) از داده می‌آید؛ محاسبه‌ی تقویمی هفته پیاده نشده |
| بازار مهارت و افزونه | `/arena/skill-market` | M52 (Skill/Plugin Marketplace) — «doc only» در فایل وضعیت | DONE (نمایش کاتالوگ) | فقط DEMO | در همان ۳۵ | NOT DELIVERED | نصب/فعال‌سازی/به‌روزرسانی/حذف عمداً وجود ندارد؛ فقط «کپی شناسه» |
| مرکز اخبار آرام | `/arena/news-center` | M18.N (Didehban calm news center) | DONE | فقط DEMO | در همان ۳۵ | NOT DELIVERED | تازگی از timestamp قرارداد محاسبه می‌شود؛ منبع خبری زنده bind نشده |

مأموریت‌های عمداً ردشده (طبق prompt): M45 (BLOCKED_OWNER)، M35.x/M47/M49/M58/M59/M62
(دسته‌های ۱–۲)، M-D8..M-D12 (PAUSED با دستور مالک ۲۰۲۶-۱۰-۱۶)، M51 (فقط مستندات)،
M31 (هم‌پوشانی با کارت شبانه‌ی message-hub).

## تست‌ها

نوشته‌شده در `tests/` (vitest + jsdom + Testing Library):

| فایل | پوشش |
|---|---|
| `tests/contract.test.ts` | اعتبارسنج نمونه را می‌پذیرد؛ ورودی خراب ⇒ `null` (UNAVAILABLE)؛ adapter روی خطای شبکه/payload خراب UNAVAILABLE برمی‌گرداند |
| `tests/truth.test.tsx` | UNKNOWN خاکستری و هرگز سبز؛ فقط LIVE سبز؛ DEMO راه‌راه؛ VIOLATION فقط برای PAPER_ONLY+false مخفی؛ حذف DEMO از جمع‌ها؛ بدون timestamp ⇒ UNKNOWN؛ REVIEWED/REJECTED بدون دلیل ⇒ UNREVIEWED |
| `tests/pages.test.tsx` | اسکن کنترل‌های ممنوع در هر ۵ صفحه؛ رادار: بدون proven/score و حذف DEMO از شمارش‌ها؛ خطایابی: «بدون شواهد» و بدون ادعای fixed؛ آزمون: NOT_RUN خاکستری، «نمونه ناکافی»، بدون قبول/مردود/leaderboard؛ بازار: «دلیل ثبت نشده»؛ اخبار: بدون زمان ⇒ UNKNOWN، موضوع‌های PLANNED، بدون سنتیمنت؛ نوار VIOLATION یکپارچه؛ حالت اجباری `?state=empty` |
| `tests/guards.test.ts` | grep: کامپوننت‌ها/فیچرها/اپ `@/mock` یا JSON قرارداد را import نمی‌کنند؛ adapterها مستقیم fetch ندارند؛ هیچ font-size زیر 12px؛ صادرات نام‌های مشترک Shell؛ متن فارسی واقعی UTF-8 |

وضعیت اجرا در همین جلسه: **نوشته ۳۵ · اجرا ۳۵ · موفق ۳۵** (`Test Files 4 passed (4)`).

## دستورهای واقعاً اجراشده با خروجی واقعی

- `npm install --no-audit --no-fund` → `added 229 packages in 35s` (exit 0)
- `npx tsc --noEmit` → `tsc: OK (exit 0)`
- `npx eslint .` → `eslint: OK (exit 0, 0 problems)`
- `npx vitest run` → `Test Files 4 passed (4)` / `Tests 35 passed (35)` (شروع 00:29:44)
- `npx next build` → `✓ Compiled successfully in 7.2s` · `Finished TypeScript in 3.3s` ·
  مسیرهای استاتیک: `/`, `/arena/news-center`, `/arena/science-radar`, `/arena/self-debug`,
  `/arena/skill-market`, `/arena/weekly-exam`
- `npm run dev` + curl → هر ۵ مسیر `/arena/*` و
  `/contract/ahos-arena-contract.example.json` → HTTP 200؛ متن‌های فارسی کلیدی در HTML
  تأیید شدند («فقط کاغذی · PAPER_ONLY»، «رادار فقط یافته‌ها را نشان می‌دهد؛ ادعا نیست»،
  «اخبار اطلاعاتی است، نه سیگنال معاملاتی»).

## اسکرین‌شات‌ها

`NOT DELIVERED` — تحویل متنی است و هیچ باینری/تصویری مجاز نیست. برنامه‌ی دقیق
۱۶۰۰×۹۰۰ در `SCREENSHOT_PLAN.md` است.

## موارد تأییدنشده

- ظاهر نهایی در مرورگرهای واقعی (فقط رندر SSR/CSR در jsdom و curl بررسی شده).
- رفتار cross-browser و دسترس‌پذیری با screen-reader واقعی (فقط نشانه‌گذاری معنایی/aria).
- رفتار Intl فونت fa-IR در مرورگرهای بدون ICU کامل (در Node 22 و مرورگرهای مدرن استاندارد است).

## انحراف‌ها از prompt (آگاهانه و مستند)

1. پیشوند خط `// FILE:` با `13_missions_batch3/<path>` نوشته شده نه `11_missions_batch/<path>`
   (الگوی کپی‌شده از prompt 11)؛ دلیل در `README_MERGE.md` آمده است.
2. `TelemetryStrip` علاوه بر قرارداد بدون-props (از طریق context داخلی Shell)، props اختیاری
   هم می‌پذیرد تا در ادغام با دسته‌های دیگر قابل استفاده باشد.
3. ماک‌ها فقط به‌عنوان fallback حالت `?demo=1` (و آن هم فقط وقتی قرارداد در دسترس نباشد)
   استفاده می‌شوند؛ خطا بدون `?demo=1` همیشه UNAVAILABLE است.
4. «title not in status file» صدق نمی‌کند — هر پنج عنوان در فایل وضعیت/ prompt آمده‌اند؛
   برای M52 یادداشت «doc only» در جدول آمده است.
5. قانون `paperAllowed=false` ⇒ «غیرمجاز» در این پنج صفحه موضوعیت ندارد (چنین ردیفی در
   قرارداد این صفحه‌ها نیست)؛ برای صفحه‌های موقعیت دسته‌های قبلی باید رعایت شود.
6. تحویل چتی در ۵ بخش `PART n/5` انجام شد اما هر بخش بالای ~۲۵ هزار کاراکتر است
   (مجموع ۶۰ فایل ≈ ۱۷۵ هزار کاراکتر)؛ طبق اولویت «complete بودن تحویل» و درخواست
   مالک برای تحویل حداکثری، هیچ فایل یا صفحه‌ای قربانی سقف بخش‌ها نشده است. فهرست
   فایل↔بخش و CHECKSUM در انتهای بخش ۵ آمده است.

## شکاف‌های عمومی

- تست E2E مرورگر (Playwright) نوشته نشده — فقط vitest/jsdom.
- endpoint های واقعی AHOS bind نشده‌اند (جداکننده‌ها مستند شده‌اند).
- آیتم‌های بدون تاریخ در نمای آرام جای خود را حفظ می‌کنند (سهمیه‌ی رزرو) تا هرگز بی‌صدا
  حذف نشوند؛ اگر بیش از ۷ مورد بدون تاریخ وجود داشته باشد، بقیه فقط در «جزئیات» دیده
  می‌شوند.
