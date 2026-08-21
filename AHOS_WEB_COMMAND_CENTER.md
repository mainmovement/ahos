# AHOS Intelligent Web Command Center

این لایه، رابط عملیاتی وب برای مأموریت AHOS است. جایگزین موتور پایتونِ `mainmovement/ahos` نیست؛ همان قوانین را روی Next.js + PostgreSQL پیاده می‌کند.

## واقعیت اجرا

- حالت اجرا: `PAPER_ONLY`
- معامله واقعی: `DISABLED`
- اصل داده: `UNKNOWN > fabricated`
- زبان رابط: فارسی / RTL
- شورا: ۱۰۰ نقش در ۱۰ تیم — مشورتی، بدون میانگین‌گیری کور

## زنده در صورت دسترسی شبکه

DexScreener, GeckoTerminal, CoinGecko, GoPlus, RugCheck, DefiLlama, Alternative.me, Binance, CoinCap, CryptoCompare, CoinPaprika, Jupiter, Pump.fun, mempool.space, Blockchain.com, RSS خبری (۲۰+ منبع), Reddit RSS, Hacker News Algolia, MyMemory ترجمه.

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
| پوش به GitHub `mainmovement/ahos` | نیازمند credential کاربر |

## حلقه

`شروع` → چرخه فوری → interval ~75s تا `توقف`. استارت دوباره لازم نیست.
