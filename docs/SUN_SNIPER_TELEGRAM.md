# Sun Sniper (@sun_sniperbot) — اتصال به AHOS

## امنیت (اجباری)

توکن ربات را **هرگز** داخل git نگذار.

اگر توکن را در چت عمومی فرستاده‌ای، همین الان از @BotFather:

1. `/revoke` یا Invalidate token
2. توکن جدید بگیر
3. فقط در `.env` محلی بگذار

```bash
cp .env.example .env
# ویرایش .env:
TELEGRAM_BOT_TOKEN=YOUR_NEW_TOKEN_ONLY_HERE
TELEGRAM_ALLOWED_CHAT_IDS=YOUR_CHAT_ID
# اگر تلگرام فیلتر است:
ALL_PROXY=socks5://127.0.0.1:10808
```

شناسه چت: به @userinfobot پیام بده.

## اجرای ربات

```bash
python scripts/run_sun_sniper_bot.py
```

باید ببینی: `Sun Sniper online as @sun_sniperbot`

سپس در تلگرام به ربات پیام بده:

- سلام
- امروز بازار چه خبر؟
- بهترین فرصت‌ها؟
- راهنما

پاسخ‌ها از همان موتور دامنه AHOS (کاغذی، evidence-first) می‌آیند.

## آلارم پامپ

ماژول `telegram_ai/pump_alert.py`:

- فقط وقتی امتیاز بالا + امنیت قابل قبول
- cooldown ۱۵ دقیقه per token
- پیام با notification روشن (صدای گوشی)
- state در `reports/pump_alert_state.json` برای بنر وب

فراخوانی از چرخه پایتون یا اسکریپت جدا:

```python
from telegram_ai.pump_alert import maybe_alert_opportunity
maybe_alert_opportunity({...})
```

## چت وب

مسیر: داشبورد → ستون گفت‌وگو با AHOS

API: `POST /api/chat` با `{ "message": "..." }`

Intentها: سلام، راهنما، شروع، توقف، بازار، فرصت، خبر، واچ، کاغذی، شورا، سلامت، …

## محدودیت صادقانه

- خرید واقعی وجود ندارد (PAPER ONLY)
- بدون DATABASE_URL چت وب ممکن است بخش state را خالی ببیند
- بدون پروکسی در ایران ممکن است api.telegram.org DOWN باشد
