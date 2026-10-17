# AHOS Arena — مأموریت‌های دسته ۳ (`13_missions_batch3/`)

اپ Next.js 16 + React 19 + TypeScript (strict) + Tailwind 4 برای پنج صفحه‌ی نمایشی/کاغذی AHOS.
همه‌ی مسیرها زیر `/arena/*` هستند. هیچ کنترل معاملاتی، نصبی یا اجرایی در هیچ صفحه‌ای وجود ندارد.

## اجرا

    npm install
    npm run dev        # http://localhost:3000 → redirect به /arena/science-radar
    npm run build      # بیلد تولیدی
    npm run typecheck  # tsc --noEmit
    npm run lint       # eslint .
    npm run test       # vitest run

بدون شبکه در زمان اجرا کار می‌کند؛ قرارداد به‌صورت فایل استاتیک از `public/` خوانده می‌شود.

## صفحه‌ها

| مسیر | عنوان | مأموریت |
|---|---|---|
| `/arena/science-radar` | رادار علم | M44 |
| `/arena/self-debug` | خطایابی خودکار | M46 |
| `/arena/weekly-exam` | آزمون هفتگی هوش | M50 |
| `/arena/skill-market` | بازار مهارت و افزونه | M52 |
| `/arena/news-center` | مرکز اخبار آرام | M18.N |

فلگ‌های پرس‌وجو (برای QA):

| فلگ | اثر |
|---|---|
| `?demo=1` | بنر/چیپ DEMO اجباری؛ تنها سوییچی که fallback ماک را (فقط هنگام خرابی قرارداد) باز می‌کند |
| `?violation=1` | نوار قرمز VIOLATION اجباری |
| `?tier=0` | فقط جدول/SVG دوبعدی |
| `?tier=1` | پنل‌های جامد (پیش‌فرض) |
| `?tier=2` | بلور و تزئین مجاز |
| `?state=loading` \| `empty` \| `error` \| `unavailable` | نمایش اجباری وضعیت مؤلفه |

## قواعد حقیقت (خلاصه)

- وضعیت‌ها: `LIVE, STALE, UNKNOWN, DEMO, CONFLICT, REJECTED` + حالت‌های مؤلفه `LOADING, EMPTY, ERROR, UNAVAILABLE, PARTIAL, SIMULATED, PLANNED, MISSING`.
- UNKNOWN خاکستری است و هرگز سبز نمی‌شود. مقدار نامشخص = `null` و نمایش «—»؛ هرگز صفر جعلی.
- ردیف‌ها/میان‌افزارهای `demo: true` با چیپ و ریبون DEMO نمایش داده می‌شوند و از همه‌ی شمارش‌ها حذف می‌شوند.
- بدون timestamp ⇒ UNKNOWN. STALE زمان آخرین به‌روزرسانی را نشان می‌دهد.
- رنگ سبز/قرمز سود/زیان ممنوع؛ رتبه‌بندی و رنگ‌بندی خوب/بد برای تصمیم‌ها ممنوع.
- قرص دائمی «فقط کاغذی · PAPER_ONLY» در همه‌ی صفحه‌ها. اگر `executionMode` غیر از `PAPER_ONLY` یا `realTrading=true` باشد، نوار قرمز VIOLATION نمایش داده می‌شود.

---

# قرارداد داده (contract)

یک فایل JSON برای همه‌ی صفحه‌ها:
`public/contract/ahos-arena-contract.example.json` (نمونه‌ی DEMO؛ هر رکورد `"demo": true`).

## کلیدهای بالاترین سطح

| کلید | نوع | الزامی | توضیح |
|---|---|---|---|
| `contractVersion` | string | بله | نسخه قرارداد (`"ahos-arena-1"`) |
| `executionMode` | enum | بله | `PAPER_ONLY` \| `SIMULATION` \| `LIVE` \| `UNKNOWN` — غیر از `PAPER_ONLY` یعنی VIOLATION |
| `realTrading` | boolean | بله | `true` یعنی VIOLATION |
| `source` | string \| null | بله | شناسه منبع (مثل `DEMO_FIXTURE`)؛ نامشخص ⇒ `null` |
| `generatedAt` | string \| null | بله | timestamp ایزو-۸۶۰۱؛ نامشخص ⇒ `null` ⇒ وضعیت UNKNOWN |
| `scienceRadar` | object | بله | اسنشات صفحه رادار علم |
| `selfDebug` | object | بله | اسنشات خطایابی |
| `weeklyExam` | object | بله | اسنشات آزمون هفتگی |
| `skillMarket` | object | بله | اسنشات بازار مهارت |
| `newsCenter` | object | بله | اسنشات مرکز اخبار |

هر بخش (section) خودش یک «اسنشات کامل» است: `kind` + متادیتای مشترک (`executionMode`, `realTrading`, `source`, `generatedAt`, `demo?`) + ردیف‌هایش. اگر متادیتای بخش مقدار نداشت، اعتبارسنج از مقادیر بالاترین سطح ارث‌بری می‌کند؛ اما اگر `executionMode`/`realTrading` در هیچ‌کدام نبود، کل سند نامعتبر است (⇒ UNAVAILABLE).

## قانون unknown

> هر مقدار نامشخص = `null` (در UI «—»). هرگز مقدار جعلی ساخته نمی‌شود؛ رشته‌ی خالی هم «—» نمایش داده می‌شود.
> هر رکورد یک `demo: boolean` الزامی دارد.

## `scienceRadar` (M44)

`items[]`:

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `id` | string | بله | شناسه یکتای یافته |
| `title` | string | بله | عنوان |
| `sourceType` | enum | بله | `paper` \| `repo` \| `blog` \| `university` \| `agent` |
| `topic` | string | بله | برچسب موضوع |
| `foundAt` | string \| null | بله | تاریخ یافت‌شدن (ایزو) |
| `relevanceNote` | string \| null | بله | یادداقت خنثی؛ هرگز ادعا |
| `status` | enum | بله | `NEW` \| `REVIEWED` \| `DISMISSED` \| `UNKNOWN` (فقط نمایش) |
| `sourceText` | string \| null | بله | ارجاع منبع به‌صورت متن ساده (لینک زنده نیست) |
| `demo` | boolean | بله | ردیف DEMO از شمارش‌ها حذف می‌شود |

## `selfDebug` (M46)

`incidents[]`:

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `id` | string | بله | شناسه رخداد |
| `time` | string \| null | بله | زمان رخداد |
| `component` | string | بله | مؤلفه |
| `errorSignature` | string (≤120) | بله | امضای خطا؛ redacted؛ بدون رمز/نام کاربری |
| `diagnosisNote` | string \| null | بله | یادداشت تشخیص |
| `status` | enum | بله | `OPEN` \| `DIAGNOSED` \| `CLOSED` \| `UNKNOWN` |
| `evidencePath` | string \| null | بله | مسیر شواهد به‌صورت متن؛ بدون شواهد ⇒ «بدون شواهد» |
| `timeline[]` | array | بله | `{time: string\|null, event: string, source: string\|null}` |
| `logExcerpt[]` | string[] (هر سطر ≤200) | بله | گزیده گزارش redacted |
| `demo` | boolean | بله | |

ادعای «رفع‌شدن» بدون مسیر شواهد هرگز نمایش داده نمی‌شود (در UI اصلاً چنین ادعایی وجود ندارد).

## `weeklyExam` (M50)

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `minSampleSize` | number ≥1 | بله | زیر این تعداد ⇒ «نمونه ناکافی» |
| `runs[]` | array | بله | اجراهای آزمون |

هر run:

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `id` | string | بله | |
| `week` | string \| null | بله | برچسب هفته به تاریخ تهران (مثل `1405-W29`) |
| `itemsCount` | number \| null | بله | تعداد موارد |
| `answeredCount` | number \| null | بله | تعداد پاسخ‌داده |
| `withEvidenceCount` | number \| null | بله | تعداد با شواهد |
| `resultSummary` | string \| null | بله | فقط اعداد خنثی؛ هرگز قبول/مردود |
| `state` | enum | بله | `SCHEDULED` \| `RAN` \| `PARTIAL` \| `NOT_RUN` \| `UNKNOWN` — `NOT_RUN` خاکستری و هرگز «قبول» |
| `items[]` | array | بله | `{id, topic, answered: yes\|no\|UNKNOWN, evidence: yes\|no\|UNKNOWN, reviewState: string\|null, demo}` |
| `demo` | boolean | بله | |

## `skillMarket` (M52)

`entries[]`:

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `id` | string | بله | |
| `name` | string | بله | |
| `kind` | enum | بله | `skill` \| `plugin` |
| `version` | string \| null | بله | |
| `source` | string \| null | بله | |
| `installState` | enum | بله | `AVAILABLE` \| `INSTALLED` \| `BLOCKED` \| `UNKNOWN` — فقط نمایشی |
| `permissions` | string[] | بله | فهرست متنی مجوزهای درخواستی؛ خنثی؛ هرگز «ایمن» |
| `reviewState` | enum | بله | `UNREVIEWED` \| `REVIEWED` \| `REJECTED` |
| `reason` | string \| null | بله | برای `REVIEWED`/`REJECTED` اجباری؛ نبودنش ⇒ نمایش `UNREVIEWED` + «دلیل ثبت نشده» |
| `demo` | boolean | بله | |

## `newsCenter` (M18.N)

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `staleAfterMinutes` | number ≥1 | بله | آستانه تازگی |
| `items[]` | array | بله | |

هر item:

| فیلد | نوع | الزامی | توضیح |
|---|---|---|---|
| `id` | string | بله | |
| `time` | string \| null | بله | بدون زمان ⇒ تازگی UNKNOWN |
| `sourceName` | string \| null | بله | |
| `topic` | enum | بله | `Oil` \| `Gold` \| `Macro` \| `Other` — فقط Oil/Gold «متصل»؛ بقیه PLANNED «متصل نیست» |
| `summary` | string (≤120) | بله | جمله خنثی؛ بدون سنتیمنت؛ بدون سیگنال معاملاتی |
| `reliability` | string \| null | بله | `null` ⇒ «نامشخص» |
| `demo` | boolean | بله | |

تازگی (LIVE/STALE/UNKNOWN) محاسبه‌شده از timestamp است: نبودِ زمان یا `generatedAt` ⇒ UNKNOWN؛ سن آیتم نسبت به `generatedAt` کمتر/مساوی `staleAfterMinutes` ⇒ LIVE؛ بیشتر ⇒ STALE؛ آیتم جدیدتر از snapshot ⇒ UNKNOWN.

---

## نگاشت «endpoint های AHOS ← کلید قرارداد»

مسیرها placeholder هستند و باید با endpoint های واقعی AHOS جایگزین شوند:

| Endpoint AHOS (فرضی) | کلید قرارداد | محل binding |
|---|---|---|
| `GET /api/arena/contract` | سند کامل | `src/adapters/_contract.ts` |
| `GET /api/arena/science-radar` | `scienceRadar` | `src/adapters/science-radar.ts` |
| `GET /api/arena/self-debug` | `selfDebug` | `src/adapters/self-debug.ts` |
| `GET /api/arena/weekly-exam` | `weeklyExam` | `src/adapters/weekly-exam.ts` |
| `GET /api/arena/skill-market` | `skillMarket` | `src/adapters/skill-market.ts` |
| `GET /api/arena/news-center` | `newsCenter` | `src/adapters/news-center.ts` |

## خطا ⇒ UNAVAILABLE

- هر خطای شبکه/parse/اعتبارسنجی در loader به `null` تبدیل می‌شود؛ adapter اسنشات UNAVAILABLE برمی‌گرداند (بدون ردیف ساختگی) و صفحه بلوک `UNAVAILABLE` را نشان می‌دهد. هیچ استثنایی به UI نمی‌رسد.
- اعتبارسنج (`src/contract/validate.ts`) هیچ وابستگی بیرونی ندارد و ورودی خراب را رد می‌کند (`null`).
- فقط `src/adapters/_contract.ts` اجازه‌ی fetch فایل JSON را دارد؛ کامپوننت‌ها هرگز JSON یا `@/mock/*` را import نمی‌کنند (تست grep دارد).

## جایگزینی نمونه با endpoint واقعی

1. یا `CONTRACT_URL` در `src/adapters/_contract.ts` را به آینه‌ی سند قرارداد روی AHOS تغییر دهید؛
2. یا در هر adapter داخل بلوک `// BIND AHOS ENDPOINT HERE` فراخوانی fetch اختصاصی همان endpoint را جایگزین `load…()` کنید و پاسخ را از همان `validate…()` عبور دهید.
3. در هر دو حالت، قواعد خطا ⇒ UNAVAILABLE و unknown ⇒ `null` باید حفظ شوند.

## فونت‌ها

Vazirmatn و Inter فقط از `local()` (فونت‌های نصب‌شده روی سیستم) با fallback به `system-ui` خوانده می‌شوند؛ هیچ فایل فونت باینری بسته‌بندی نشده است (ببینید `AUDIT.md` و `LICENSES.md`).
