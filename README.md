# AHOS — Intelligent Web Command Center

**Artificial Hybrid Opportunity Scoring System** · W44 Intelligence Tier

Evidence-first crypto opportunity intelligence. Persian-first. Paper-only.  
No fabricated prices, news, confidence, or live-trading claims.

## Quick truth

| Principle | Value |
|-----------|--------|
| Data honesty | `UNKNOWN > fabricated` |
| Execution | `PAPER_ONLY` — real trading DISABLED |
| UI language | فارسی / RTL |
| Council | 100 roles · 10 teams (disagreement preserved) |
| Start once | Cycles continue (~70s) until Stop |
| Ranking | Multi-factor · anti-hype · security gate first |

## W44 upgrades

- **Smarter scoring:** age, buy/sell flow, vol/liq ratio, multi-source evidence
- **Faster cycles:** parallel security (×4), adaptive HTTP timeouts, 70s interval
- **Harder anti-hype:** paid promo + thin book, extreme momentum, wash-trade-like ratios → REJECT
- **30+ free news sources** → Persian rewrite + provenance

## Start (laptop)

```bash
npm install
npm run dev
```

Open the site → **شروع پروژه** once. Engine runs continuous cycles until **توقف**.

Python core (optional parallel path):

```bash
python3 -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

### Windows PRE_SOAK entry (PAPER_ONLY)

Last gate paste (`20260828_220318`) was one G2 flip from PRE_SOAK (empty gateway; paste predated #45 on main). **Do not invent READY.**

Merge order: slim **#59** (OPS evidence wake) then full tip **#58**. Keep paste-sink **#56 OPEN**.

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/b11c7994fcd6108eb3f61ecea532c87f26da7753/AHOS_MAIN_CLEAR_G2.cmd
AHOS_MAIN_CLEAR_G2.cmd
```

Or tip runner: `AHOS_RUN_TIP.cmd` from `cursor/windows-main-evidence-push-4bde`.

Paste `reports\OWNER_PASTE_WINDOWS_GATE.txt` to PR **#56** or **#38**. STATE B: no `db:migrate` / `db:push`. Details: `docs/OWNER_ACTION_REQUIRED.md` · `OWNER_ONE_LINER.txt`.

## Live in code (when network allows)

DexScreener · GeckoTerminal · CoinGecko · Pump.fun · GoPlus · RugCheck · DefiLlama · Alternative.me · Binance public · CoinCap · CryptoCompare · CoinPaprika · Jupiter · mempool · 30+ RSS

## Honest BLOCKED

| Item | Status |
|------|--------|
| DEXTools full | NO_KEY / COST_BLOCKED |
| CMC without key | NO_KEY |
| X / IG / TikTok scrape | COST_BLOCKED / OUT_OF_POLICY |
| Real trading | DISABLED |
| Telegram bot | needs BotFather token |

## Project classification

**`INTEGRATION_READY`** (agent-host verified). **`OPERATOR_READY` = NOT_VERIFIED** until Windows gates produce real artifacts (`docs/WINDOWS_OPERATOR_HANDOFF.md`).

See [`docs/FINAL_TRUTH_AUDIT.md`](docs/FINAL_TRUTH_AUDIT.md) · [`docs/CURRENT_TRUTH_SNAPSHOT.md`](docs/CURRENT_TRUTH_SNAPSHOT.md) · Owner: [`docs/OWNER_ACTION_REQUIRED.md`](docs/OWNER_ACTION_REQUIRED.md).

**Not claimed:** Production Ready · Operator Ready · Telegram E2E · n8n Operational · Soak Passed · Calibration Validated.

## Docs

| Role | Path |
|------|------|
| Windows operator handoff | `docs/WINDOWS_OPERATOR_HANDOFF.md` |
| Merge / transfer audit | `docs/MERGE_READINESS_AUDIT.md` |
| Operator validation protocol | `docs/OPERATOR_VALIDATION_PROTOCOL.md` |
| Pre-soak (after Windows G1–G10) | `docs/PRE_SOAK_PROTOCOL.md` |
| Document truth map | `docs/DOC_TRUTH_MAP.md` |
| Implementation matrix | `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` |
| Final truth audit | `docs/FINAL_TRUTH_AUDIT.md` |
| Next-phase backlog | `docs/NEXT_DEVELOPMENT_BACKLOG.md` |
| Owner actions | `docs/OWNER_ACTION_REQUIRED.md` |
| Immutable master doctrine | `docs/canonical/MASTER_DIRECTIVE_v1.md` |
| Wave ops directive | `docs/canonical/MASTER_DIRECTIVE_W43.md` |
| Open gaps (honesty) | `AHOS_GAP_REGISTER.md` |
| Windows operator soak gate | `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` |
| W44 report | `reports/W44_INTELLIGENCE_SPEED_UPGRADE.md` |

**Not current truth:** `AHOS_FINAL_STATUS.md` / `AHOS_PRODUCTION_READINESS_REPORT.md` (`READY_FOR_DEPLOYMENT` — superseded).

**AHOS does not pretend to be smart — it tightens evidence and measures what it can.**
