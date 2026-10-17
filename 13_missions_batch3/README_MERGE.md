# README_MERGE — ادغام دسته ۳ با دسته‌های ۱ و ۲

## ساختار مشترک (فرض‌های اجرای مشترک)

- نام‌ها و props کامپوننت‌های مشترک دقیقاً مطابق prompt 12 است تا هر سه دسته یک
  پیاده‌سازی واحد داشته باشند:
  - `src/components/shell/Shell.tsx` — `Shell({title, truth, source, lastRead, rowCount, snapshot?, children})`
  - `src/components/truth/TruthChip.tsx` — `TruthChip({status})`
  - `src/components/truth/TierChip.tsx` — `TierChip({tier})`
  - `src/components/shell/TehranClock.tsx` — بدون props
  - `src/components/shell/ViolationBar.tsx` — `ViolationBar({executionMode, realTrading})`
  - `src/components/shell/TelemetryStrip.tsx` — `TelemetryStrip({source?, lastRead?, rowCount?})`
    با fallback به context داخلی Shell (بنابراین فراخوانی بدون props هم کار می‌کند).
- فایل‌های اضافی کوچک (برای استفاده‌ی مشترک بین دسته‌ها، بی‌ضرر اگر lift شوند):
  `StateBlock.tsx`, `DetailsDrawer.tsx`, `DataTable.tsx` در `src/components/truth/`.
- توکن‌های بصری در `src/app/globals.css` با پیشوند `--ah-*`؛ متغیرهای بین اپ‌ها برخورد
  نمی‌کنند. Tailwind 4 فقط به‌صورت `theme.css` + `utilities.css` (بدون preflight) import
  شده تا هیچ reset سراسری با اپ میزبان برخورد نکند.
- در ادغام: `Shell` و پوسته را فقط یک بار نگه دارید؛ صفحه‌های دسته‌های قبلی را به همین
  Shell وصل کنید و `src/lib/flags.ts` (فلگ‌های `?demo/?violation/?tier/?state`) را مشترک
  کنید.

## یادداشت خط اول فایل‌ها (strip)

طبق «DELIVERY FORMAT» نهایی:

- بلوک‌های کدی (`ts`, `tsx`, `js`, …) با خط اول `// FILE: 13_missions_batch3/<path>`
  شروع می‌شوند. **مالک باید این خط اول را از هر فایل کدی حذف کند** تا فایل اجرایی تمیز
  بماند.
- بلوک‌های `json`, `md`, `mjs`, `css` و فایل‌های dotfile (مثل `.gitignore`) تمیز تحویل
  داده شده‌اند و مسیرشان به‌صورت `FILE: <path>` روی خط **قبل از** fence آمده است؛ نیازی
  به حذف چیزی از داخل این فایل‌ها نیست.
- فایل‌های markdown که خودشان شامل سه backtick هستند داخل fence از نوع `~~~~` قرار
  گرفته‌اند تا fence شکسته نشود.

### انحراف آگاهانه در پیشوند مسیر

قالب «DELIVERY FORMAT» در prompt (که از prompt 11 کپی شده) پیشوند
`11_missions_batch/<path>` را نوشته است؛ چون پوشه‌ی تحویلی این دسته
`13_missions_batch3/` است، خطوط `// FILE:` با `13_missions_batch3/<path>` نوشته شده‌اند
تا استخراج به پوشه‌ی درست بریزد. اگر اسکریپت برداشت شما پیشوند `11_missions_batch/`
را انتظار دارد، بعد از استخراج یک find/replace روی خطوط `// FILE:` انجام دهید.

## ادغام کلیدهای قرارداد در یک فایل

سه دسته روی یک سند JSON واحد می‌نشینند:

    {
      "contractVersion": "ahos-arena-1",
      "executionMode": "PAPER_ONLY",
      "realTrading": false,
      "source": "...",
      "generatedAt": "...",
      "healthMonitor": { ... },        // دسته ۱
      "lessons": { ... },              // دسته ۱
      "workroom": { ... },             // دسته ۱
      "portable": { ... },             // دسته ۱
      "oilGold": { ... },              // دسته ۱
      "messageHub": { ... },           // دسته ۲
      "selfEvaluation": { ... },       // دسته ۲
      "ideaShelf": { ... },            // دسته ۲
      "researchInstitute": { ... },    // دسته ۲
      "missionMap": { ... },           // دسته ۲
      "scienceRadar": { ... },         // دسته ۳ (این بسته)
      "selfDebug": { ... },            // دسته ۳
      "weeklyExam": { ... },           // دسته ۳
      "skillMarket": { ... },          // دسته ۳
      "newsCenter": { ... }            // دسته ۳
    }

- هر بخش یک اسنشات کامل (`kind` + متادیتای مشترک + ردیف‌ها) است؛ متادیتای بخش می‌تواند
  از مقادیر بالاترین سطح ارث‌بری کند.
- کلیدهای دسته ۳ با دسته‌های ۱ و ۲ هم‌پوشانی ندارند؛ فقط کلیدهای مشترک بالاترین سطح
  (`executionMode`, `realTrading`, `source`, `generatedAt`) یکسان‌اند.
- loader دسته ۳ (`src/adapters/_contract.ts`) هر بخش را مستقل اعتبارسنجی می‌کند؛ خرابی
  یک بخش بقیه را خراب نمی‌کند (اما اعتبارسنج کل سند در `validateContract` سخت‌گیر است).

## مجوزها

ببینید `LICENSES.md`. وابستگی‌ها npm/pypi standard هستند؛ فونت باینری وجود ندارد.
