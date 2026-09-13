# پیام بیدارباش برای ایجنت Ahos cursor configuration

این متن را **کپی و در چت ایجنت Ahos** paste کنید.

---

```
Owner vision ثبت شد: docs/supervision/OWNER_VISION_REGISTRY.md
Directive زنده: docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md

قانون کار:
1. اول ahos-governance-context skill را بخوان
2. Charter §38/39/42 و AGENTS.md را رعایت کن
3. Status directive را رعایت کن (الان: PROCEED_AFTER_W2)

ترتیب اجرا (بدون پرش):

فاز A — foundation (الان)
- W1.3 identity spoof hardening
- merge W2 (#95)
- DOSSIER.md + DOC_TRUTH_MAP
- سپس rebase W4 stack؛ حداکثر 3 PR

فاز B — owner P1 (بعد از W2 on main)
- Chat سایت: conversational FA/EN via gateway
- Telegram Sun Sniper: فقط از .env (TELEGRAM_BOT_TOKEN) — هرگز token در git
- Alerts: canonical overlay PASS + صدا در سایت و تلگرام
- Contract address: canonical identity — هر آدرس باید VERIFIED باشد

فاز C — experience (موج‌های کوچک)
- Environment Engine spec (بدون شکستن Command Center)
- 3D/audio/themes incremental

Skills:
governance → token-identity → security → domain-backend → web-experience → ai-council → change-verification

Models:
معماری/امنیت: Opus یا GPT-5.6 Sol High
پیاده‌سازی: Sonnet یا Composer
مکانیکی: Grok Fast

ممنوع:
- Lane A edit
- live trading / L6+
- merge W4 قبل از W2
- secret در commit
- ادعای AGI/ACI تحویل‌شده
- یک PR غول‌آسا برای "همه چیز"

هر commit: pytest + freeze_lane_a + evidence artifact
```

---

**امنیت:** توکن تلگرام را در چت عمومی فرستادید. فوراً در BotFather rotate کنید و فقط در `.env` محلی بگذارید.
