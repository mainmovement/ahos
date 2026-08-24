# AHOS Intelligent Web Command Center

این لایه، رابط عملیاتی وب برای مأموریت AHOS است. جایگزین موتور پایتونِ `mainmovement/ahos` نیست؛ همان قوانین را روی Next.js پیاده می‌کند و به چرخه‌های واقعی وصل است.

## واقعیت اجرا

- حالت اجرا: `PAPER_ONLY`
- معامله واقعی: `DISABLED`
- اصل داده: `UNKNOWN > fabricated`
- زبان رابط: فارسی / RTL
- شورا: ۱۰۰ نقش در ۱۰ تیم — مشورتی، بدون میانگین‌گیری کور
- حلقه: یک‌بار **شروع** → چرخه‌های مداوم (~۷۵s) تا **توقف**

## زنده در صورت دسترسی شبکه (رایگان / عمومی)

DexScreener, GeckoTerminal, CoinGecko, GoPlus, RugCheck, DefiLlama, Alternative.me, Binance public, CoinCap, CryptoCompare, CoinPaprika, Jupiter, Pump.fun, mempool.space, Blockchain.com, ۳۰+ منبع RSS خبری, Reddit RSS, Hacker News Algolia, MyMemory ترجمه.

## BLOCKED / صادقانه

| مورد | وضعیت |
|---|---|
| DEXTools | NO_KEY / COST_BLOCKED |
| CoinMarketCap بدون کلید | NO_KEY |
| X/Twitter | COST_BLOCKED |
| Instagram / TikTok scrape | OUT_OF_POLICY |
| Telegram scrape | OUT_OF_POLICY |
| مدل‌های پولی AI | NO_KEY مگر env |
| معامله واقعی | DISABLED |

## گفت‌وگو

چت مثل صحبت با یک همکار صریح است: intent تشخیص داده می‌شود و به موتور واقعی (بازار، فرصت، اخبار، شورا، واچ، کاغذی، سلامت) وصل می‌شود. اگر داده نباشد می‌گوید UNKNOWN — نه حدس زیبا.

## Master directive

ACTIVE (immutable): `docs/canonical/MASTER_DIRECTIVE_v1.md` (authority: `docs/canonical/master_directive_registry.json`).
Historical wave directive (reference-only, not the active doctrine): `docs/canonical/MASTER_DIRECTIVE_W43.md` — see `docs/canonical/RECONCILIATION_R1.md`.
