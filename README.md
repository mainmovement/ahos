# AHOS — Intelligent Web Command Center

**Artificial Hybrid Opportunity Scoring System**

Evidence-first crypto opportunity intelligence. Persian-first. Paper-only.  
No fabricated prices, news, confidence, or live-trading claims.

## Quick truth

| Principle | Value |
|-----------|--------|
| Data honesty | `UNKNOWN > fabricated` |
| Execution | `PAPER_ONLY` — real trading DISABLED |
| UI language | فارسی / RTL |
| Council | 100 roles in 10 teams (advisory, disagreement preserved) |
| Start once | Cycles continue until Stop |

## Start (laptop)

```bash
# install deps (Node + Python as needed)
npm install
# configure .env from .env.example (optional keys only)
npm run dev
```

Open the site → press **شروع پروژه**.  
The engine runs continuous cycles (~75s) until you press **توقف**.

Python runtime (core intelligence):

```bash
python3 -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

## What is live in code

- Discovery via DexScreener / GeckoTerminal / CoinGecko / Pump.fun (when network allows)
- Multi-factor ranking (anti-hype)
- Independent security gate
- News from 30+ free RSS/API sources → Persian rewrite + provenance
- Conversational chat (intent → real subsystems)
- Watchlist + paper positions + hindsight lessons
- Self-observation, findings, evolution proposals

## Honest BLOCKED / REQUIRES USER ACTION

| Item | Status |
|------|--------|
| DEXTools full API | NO_KEY / COST_BLOCKED |
| CoinMarketCap without key | NO_KEY |
| X / Twitter | COST_BLOCKED |
| Instagram / TikTok / Telegram scrape | OUT_OF_POLICY |
| Paid AI models | NO_KEY unless you set env |
| Real trading / wallet signing | DISABLED |
| Live Telegram bot | needs BotFather token |
| Long soak (168h) | run on your laptop |

## Docs

- Master directive: `docs/canonical/MASTER_DIRECTIVE_W43.md`
- Gap register: `AHOS_GAP_REGISTER.md`
- Web command center notes: `AHOS_WEB_COMMAND_CENTER.md`

## Safety

No secrets in git. No real orders. No private keys.  
If evidence is missing, AHOS says **UNKNOWN** — that is a feature.
