# AHOS Master Agent Mode Operational Directive

## دستورالعمل دائمی توسعه، ممیزی و تکامل پروژه AHOS

| فیلد | مقدار |
|---|---|
| Repository | `mainmovement/ahos` |
| Path | `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` |
| Version | Master Living Document |
| Status | ACTIVE (عملیاتی) |
| Last updated | 2026-08-18 |
| Branch | `arena/01a0118a-ahos` |
| Pull Request | https://github.com/mainmovement/ahos/pull/2 |

> **رابطه با دکترین تغییرناپذیر:** این سند **جایگزین** `docs/canonical/MASTER_DIRECTIVE_v1.md` نیست و آن را تضعیف نمی‌کند. دکترین v1 همچنان ACTIVE و hash-pinned است (`e2457c0d…`). این فایل مرجع **عملیاتی زنده** برای Agent Mode است: هر جلسه با خواندن آن شروع می‌شود و بعد از هر مرحله مهم به‌روز می‌شود.

---

# 1. هدف سند

این سند مرجع دائمی همکاری بین:

* Agent Mode
* AI Architect
* Developer Environment
* Repository Maintainers

است.

این سند باید:

* در ابتدای هر روز / هر جلسه کاری خوانده شود.
* قبل از هر تغییر کد بررسی شود.
* بعد از هر مرحله مهم توسعه به‌روزرسانی شود.
* وضعیت جدید پروژه در آن ثبت شود.

هیچ توسعه‌ای نباید بدون بررسی این سند انجام شود.

---

# 2. چرخه دائمی کار AHOS

چرخه کاری اجباری:

```
Read Directive
        ↓
Repository Audit
        ↓
Architecture Review
        ↓
Identify Gaps
        ↓
Implement
        ↓
Run Tests
        ↓
Senior Architect Review
        ↓
Update Directive
        ↓
Commit
        ↓
Repeat
```

---

# 3. نقش Agent Mode

Agent Mode قبل از هر Commit باید همزمان نقش‌های زیر را اجرا کند:

* Senior Software Architect
* Senior Python Engineer
* Security Reviewer
* Data Architecture Reviewer
* System Integration Reviewer

هدف فقط اضافه کردن کد نیست.

هدف:

ساخت یک سیستم یکپارچه، قابل اجرا، قابل تست و قابل توسعه است.

---

# 4. قوانین غیرقابل تغییر AHOS

## AHOS چیست؟

AHOS:

Artificial Hybrid Opportunity Scoring System

یک سیستم:

* Market Intelligence
* Opportunity Discovery
* Risk Analysis
* Evidence-Based Decision Support

است.

AHOS یک Trading Bot ساده نیست.

---

## ممنوعات

تا زمانی که Safety Architecture اجازه نداده:

ممنوع:

* معامله خودکار واقعی
* ارسال سفارش
* امضای تراکنش
* کنترل Wallet
* برداشت سرمایه
* اتصال مستقیم برای خرید و فروش

---

# 5. ماموریت نهایی پروژه

ساخت یک سیستم هوشمند که بتواند:

## Discovery

بررسی کند:

* DexScreener
* DEXTools
* GeckoTerminal
* CoinGecko
* CoinMarketCap
* Blockchain Explorerها
* Launchpadها

---

## Market Intelligence

تحلیل کند:

* قیمت
* حجم
* نقدینگی
* FDV
* Market Cap
* رشد کاربران
* رفتار بازار

---

## Security Intelligence

بررسی کند:

* Contract Risk
* Ownership Risk
* Mint Authority
* Freeze Authority
* Proxy Contract
* Liquidity Risk
* Honeypot Risk
* Sellability
* Holder Concentration
* Suspicious Patterns

---

## Whale Intelligence

بررسی کند:

* Large Wallet Movement
* Smart Money
* Accumulation
* Distribution
* Wallet Classification

---

## Social Intelligence

بررسی کند:

* Telegram
* X/Twitter
* Reddit
* TikTok
* Instagram
* News Sources

برای پیدا کردن:

* Viral Momentum
* Community Growth
* Sentiment Change

---

# 6. معماری اصلی داده

قانون طلایی:

هیچ ماژول Intelligence اجازه مصرف مستقیم Raw Data ندارد.

معماری:

```
Provider
    |
    ↓
Evidence
    |
    ↓
EvidenceBundle
    |
    ↓
Feature Extraction
    |
    ↓
Risk Assessment
    |
    ↓
Opportunity Score
    |
    ↓
Explanation
    |
    ↓
Telegram Interface
```

پیاده‌سازی فعلی این لوله:

```
materialize_evidence(candidate)
        ↓
SecurityIntelligence + WhaleIntelligence   (Phase 5)
        ↓
FeatureExtractor
        ↓
RiskEngine.assess(..., extra_findings=…)   # merge بدون جریمه دوبل
        ↓
OpportunityCalculator
        ↓
ExplanationEngine
        ↓
OpportunityPipelineOrchestrator → Alert → Telegram
```

---

# 7. قانون توسعه ماژول‌ها

هیچ ماژول جدا و بدون اتصال پذیرفته نیست.

قبل از ساخت هر فایل:

بررسی شود:

* آیا مشابه آن وجود دارد؟
* آیا می‌توان توسعه داد؟
* آیا بخشی از معماری فعلی است؟
* آیا تست دارد؟

---

# 8. AI Council Architecture

AHOS باید دارای سیستم ارزیابی چنددیدگاهی باشد.

هدف:

استفاده از مدل‌ها و دیدگاه‌های مختلف:

* ChatGPT
* Claude
* Gemini
* Grok
* Local AI Models

در صورت امکان.

---

AI Council نباید تصمیم کور ایجاد کند.

باید خروجی دهد:

```
Analysis
+
Agreement
+
Disagreement
+
Risk Warning
+
Confidence
```

وضعیت فعلی: `architecture/council.py` و `architecture/ai/council_live.py` پیاده شده‌اند. شورا advisory است و DECIDE ندارد.

---

# 9. مفهوم شورای تخصصی

شخصیت‌های تحلیلی:

* اقتصاددان
* تحلیلگر بازار
* متخصص Tokenomics
* متخصص امنیت قرارداد
* برنامه‌نویس Blockchain
* متخصص داده
* ریاضیدان احتمال
* متخصص رفتار بازار
* متخصص هک اخلاقی
* متخصص هوش مصنوعی

هدف:

ساخت Consensus با ذکر دلیل.

وضعیت فعلی: لنزهای خبره در `architecture/knowledge/lenses.py` و پنل در `architecture/knowledge/panel.py`. جعل شخصیت ممنوع است.

---

# 10. Self Learning و Hindsight

AHOS باید اشتباهات گذشته را تحلیل کند.

مثال:

```
Token Selected:
Date:
Reason:

What happened later?

Prediction accuracy:

Lesson:
```

هدف:

ارتقای تدریجی سیستم.

وضعیت فعلی: `architecture/evolution/hindsight.py` و `architecture/evolution/engine.py` وجود دارند. هر یادگیری باید Evidence-backed و بدون بازنویسی تاریخچه باشد.

---

# 11. Telegram AI Interface

رابط اصلی کاربر:

Telegram

باید مکالمه طبیعی فارسی داشته باشد.

نمونه:

کاربر:

"امروز بازار چطوره؟"

سیستم:

* خلاصه بازار
* فرصت‌ها
* ریسک‌ها
* دلیل تحلیل

---

کاربر:

"من این توکن را خریدم"

سیستم:

ثبت کند:

* زمان خرید
* قیمت
* مقدار
* دلیل خرید

و سپس:

* Monitoring
* Risk Alert
* Exit Conditions

ارائه دهد.

قانون UX: هر پاسخ عملیاتی با «تصمیم نهایی با کاربر است.» تمام می‌شود.

---

# 12. اجرای سیستم

هدف فعلی:

Single User

Environment:

Laptop Personal

بدون نیاز اجباری به VPS.

اولویت:

* Windows Compatible
* Low Cost
* Local AI Friendly
* Resistant to Filtering Limitations

ورود فعلی: `python -m architecture.runtime` یا `start_ahos.ps1` / `start_ahos.bat`.

---

# 13. ابزارهای مجاز

استفاده شود:

* Python
* n8n
* Docker در صورت نیاز
* SQLite
* PostgreSQL در مرحله مناسب
* Ollama / Local AI در صورت نیاز

سقف هزینه جاری: `$0/month` مگر با تصویب صریح انسان.

---

# 14. Repository Hygiene

قبل از Commit:

حذف:

* `__pycache__`
* `.pytest_cache`
* Runtime Database
* Temporary Files
* Random Uploads
* Unused Artifacts

`.gitignore` باید همیشه به‌روز باشد.

---

# 15. پروتکل هر Task

## مرحله 1

Audit

## مرحله 2

Implementation

## مرحله 3

Integration

بررسی:

* Architecture
* Imports
* Database
* Tests

## مرحله 4

Testing

حداقل:

3 بار اجرای Test Suite کامل

## مرحله 5

Senior Review

بررسی:

* Duplicate Code
* Orphan Modules
* Broken Imports
* Architecture Mismatch

---

# 16. گزارش اجباری فارسی

هر پایان Task باید شامل:

## خلاصه اجرا

## چه ساخته شد؟

## چگونه وصل شد؟

## فایل‌های تغییر یافته

## تست‌های اجرا شده

## مشکلات پیدا شده

## اصلاحات انجام شده

## بررسی Senior Architect

## وضعیت Repository

## Commit ایجاد شده

باشد.

---

# 17. وضعیت فعلی توسعه

بروزرسانی: 2026-08-18 — شاخه `arena/01a0118a-ahos` — PR [#2](https://github.com/mainmovement/ahos/pull/2)

`main` هنوز روی `62ecf04` («Add files via upload») است تا PR merge شود.

## Phase 4 — انجام‌شده

هدف:

Clean Repository + Intelligence Engine Integration

Commit:

```
5245c695d8d0ed11a64ae7439f2a32e7fa876bc3
AHOS v2: clean repository and integrate intelligence engine
```

ساخته شد:

```
architecture/intelligence/     Evidence, EvidenceBundle, IntelligenceEngine
architecture/features/         FeatureExtractor
architecture/risk/             RiskEngine (Evidence-only)
architecture/scoring/          OpportunityCalculator + facade
architecture/explanations/     WHY-law
```

تست: سوئیت کامل ۳ بار — **918 passed**.

---

## Phase 5 — انجام‌شده

هدف:

Security Intelligence + Whale Intelligence Foundation

Commit:

```
6d8d32baa70fbc4431ecb0ea22251827933ad356
AHOS v2: add security and whale intelligence foundation
```

ساخته شد:

```
architecture/security/
  hygiene.py                   (rename از architecture/security.py)
  contract_analysis.py
  liquidity_analysis.py
  holder_analysis.py
  manipulation_detection.py
  engine.py                    SecurityIntelligence

architecture/intelligence/whales/
  wallet_activity.py
  smart_money_detector.py
  whale_signals.py
```

قوانین اتصال:

* ورودی فقط `EvidenceBundle`
* خروجی `RiskFinding` + Evidence مشتق
* ادغام در `RiskEngine` با `risk_id` تا جریمه دوبل نشود
* ویژگی‌های نهنگ/مالکیت در `FeatureVector` با امتیاز صفر (کف تاریخی امتیاز حفظ شود)

تست: سوئیت کامل ۳ بار + بازبینی معمار — **938 passed**.

---

## شکاف‌های باز (صف بعدی، نه ادعا)

* Social Intelligence عمیق‌تر (X/TikTok/Instagram) پشت سقف `$0` و فیلترینگ
* کالیبراسیون عددی امتیاز فرصت تا E-01 ≥ ۸ هفته
* REAL Telegram و n8n live پشت بلاکر کاربر (توکن + VPS)
* معامله واقعی: ممنوع و بسته

---

# 18. قوانین تکامل دائمی

AHOS نباید متوقف شود.

هر مرحله باید:

* قوی‌تر شود.
* دقیق‌تر شود.
* تست بیشتری داشته باشد.
* معماری بهتر شود.
* دانش ذخیره کند.

---

# 19. مسئولیت Agent Mode

Agent Mode موظف است:

* این سند را بخواند.
* وضعیت Repository را بررسی کند.
* تغییرات لازم را انجام دهد.
* بعد از کار این سند را Update کند.
* گزارش فارسی ارائه دهد.

چک‌لیست شروع جلسه:

1. خواندن این فایل
2. خواندن `docs/canonical/MASTER_DIRECTIVE_v1.md` (دکترین)
3. `git status` + `git log -5`
4. شناسایی شکاف در §17
5. اجرای چرخه §2

---

# 20. اصل نهایی

هدف:

ساخت یکی از کامل‌ترین سیستم‌های شخصی Crypto Intelligence با تمرکز بر:

* کیفیت داده
* امنیت
* تحلیل چندلایه
* یادگیری
* توضیح‌پذیری
* کنترل ریسک

نه ساخت یک ابزار هیجانی یا قمارگونه.

---

End of Master Directive.
