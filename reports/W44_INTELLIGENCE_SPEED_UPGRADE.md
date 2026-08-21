# W44 — Intelligence & Speed Upgrade Report

**Date:** 2026-08-21  
**Branch:** main  
**Mode:** PAPER_ONLY · UNKNOWN > fabricated

---

## Implemented

### 1. Multi-factor scoring (`scoring.ts`)

- Pair age, buy/sell imbalance, volume/liquidity ratio as first-class evidence dimensions
- Stronger anti-hype gates:
  - paid promo + thin liquidity → REJECT
  - extreme 24h momentum + thin liquidity → REJECT
  - ultra-new pool + thin liquidity → REJECT
  - vol/liq ratio > 40 → REJECT
- Rank score combines liquidity, volume, security, coverage, age, flow — with promo/momentum/vlr penalties
- REJECT never ranks above WATCH (decision tier first)

### 2. Parallel security (`engine.ts`)

- Bounded pool (`SECURITY_CONCURRENCY = 4`) for GoPlus/RugCheck
- Inspect up to 10 candidates per cycle without serial bottleneck
- Cycle interval baseline **70s** (continuous until Stop)

### 3. Smarter candidate pick

- Multi-source discovery bonus
- Penalty for paid boosts and extreme momentum on thin books
- Cap 32 unique tokenKeys

### 4. Findings intelligence

- New finding when reject count dominates watch (anti-hype filter active)

---

## Verified (code-level)

- Zero-money invariant preserved
- UNKNOWN semantics preserved
- No fabricated prices/news/confidence
- Council 100-role pipeline unchanged in contract

## Not claimed as live without host evidence

- Provider SUCCESS path on operator laptop (egress-dependent)
- Calibration measurement (still needs real outcome accrual)
- Telegram live (token required)

## Measured (design intent)

| Metric | Before (W43) | After (W44) |
|--------|--------------|-------------|
| Security probes | sequential | parallel ×4 |
| Scoring dimensions | liq/vol/sec/coverage | +age +flow +vlr +multi-source |
| Anti-hype gates | promo / council | +momentum, age, vlr |
| Interval | 75s | 70s continuous |

Runtime duration numbers require operator `npm run dev` + Start.

---

## Blocked / User action

| Item | Class |
|------|--------|
| Live provider egress | REQUIRES USER ACTION |
| Telegram token | REQUIRES CREDENTIAL |
| 168h soak | REQUIRES USER ACTION |
| Paid APIs | COST_BLOCKED / NO_KEY |

---

## Next highest value

1. Operator: run web command center → Start once → observe cycle duration & provider census
2. Persist cycle duration trends for benchmark gate
3. Wire more free on-chain holder concentration when keyless endpoints allow
4. Calibration report after real WATCH outcomes close

**Principle held:** AHOS does not pretend to be smarter; it tightens evidence gates and parallelizes honest work.
