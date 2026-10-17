# VERIFY — دستورهای دقیق بازبینی

از داخل پوشه‌ی `13_missions_batch3/`:

    npm install
    npm run typecheck
    npm run lint
    npm run test
    npm run build
    npm run dev        # سپس سر زدن به مسیرهای /arena/*

وضعیت اجرا در این جلسه (۲۰۲۶-۱۰-۱۶):

| دستور | وضعیت | نتیجه |
|---|---|---|
| `npm install` | RUN | `added 229 packages` (exit 0) |
| `npm run typecheck` (`tsc --noEmit`) | RUN | exit 0 — بدون خطا |
| `npm run lint` (`eslint .`) | RUN | exit 0 — `0 problems` |
| `npm run test` (`vitest run`) | RUN | `Test Files 4 passed (4)` · `Tests 35 passed (35)` |
| `npm run build` (`next build`) | RUN | `Compiled successfully` · TypeScript pass · ۸ مسیر استاتیک |
| `npm run dev` + curl مسیرها | RUN | هر ۵ مسیر `/arena/*` و فایل قرارداد → HTTP 200 |
| اسکرین‌شات | NOT DELIVERED | به `SCREENSHOT_PLAN.md` نگاه کنید |
