# AHOS — RESEARCH META-ANALYSIS v1.0 (required gate before batch-4)
# Date: 2026-08-11 · Council: Quant Lead + Stats Expert + Regime Analyst + Backtest Specialist + Auditor
# Evidence: exp_20260810_121055 (batch-1) · exp_20260811_154550 (batch-2) · exp_20260811_165329 (batch-3)
# Data: REAL BinanceVision — 3.6y BTC/ETH/SOL + 6.6y BTC (ext) + funding + daily OI, sha-pinned

## Q1. What have we actually learned?
a) 1h-horizon single-signal strategies on BTC/ETH/SOL futures carry **no deployable edge under
   realistic costs** — 13 tested mechanisms, 0 accepted. This is consistent with published
   market-efficiency literature for liquid crypto majors at hourly scale.
b) The engineering machinery (causal engine, OOS/WF/MC/stress, gates) **works correctly and
   reproducibly** — verified by prefix-causality proofs, determinism tests, and honest rejections.
c) Small-sample results systematically overstate edge: H6/H10 BTC "PF 2.35–3.13 (n=16-38)" deflated
   to H13 "PF 1.27 (n=31, 24m OOS)" once the mechanism was given full history. **Sample inflation is now
   a documented, measured phenomenon in this lab.**
d) Costs decide everything at 1h: H9's OOS PF 1.38 → 0.93 under 2×cost. Any edge thinner than
   ~2×frictions is imaginary for execution purposes.

## Q2. What mechanisms repeatedly fail?
- Pure price-action patterns on 1h (Donchian H1/H12, squeeze H3, ADX pullback H4): all OOS PF < 1.0.
- Mean reversion on majors 1h (H2): catastrophic (train PF 0.035) — majors trend/impulse at 1h, don't revert.
- Funding contrarianism (H5): sparse, weak, unstable.
- Volume shock continuation (H7): mostly exhaustion at 1h.

## Q3. What mechanisms show partial (non-accepted) evidence?
- **OI × volatility-regime on BTC** (H10/H13): train PF 1.21 / OOS 1.27, MC 75.9%, DD 10.9%, WR 54.8%.
  Positive but marginal; dies at 2× costs (0.976) and at batch-bar 1.5. Classified: **CANDIDATE-GRADE anomaly,
  not a strategy.** (CANDIDATE = unresolved council disagreement statute: Quant sees residual edge,
  Stats says insufficient under multiplicity; resolution rule = do not spend more OOS looks on it.)
- **Composite multi-factor on BTC** (H9): PF 1.34 full-run, but no tail concentration (H11 falsified) and
  stress-fragile. Classified: **structurally capped, family closed.**

## Q4. Genuinely novel hypotheses?
H10 (OI×vol-state) and H13 (instrument-scoped OI) were novel within this lab. Others (H1–H4, H7) are
standard literature baselines — valuable as *calibrators that gates work*.

## Q5. Merely parameter variations?
H12 (Donchian 20 vs 55 + RV gate) — de facto a variation; its rejection closes the "rescue trend family
with more filters" direction. H11 was a legitimately different falsifiable question (edge density).

## Q6. Which missing data prevents meaningful research?
1. **Order book/L2 depth** (H8 blocked) — no free historical source exists; live collection only going forward.
2. **Liquidations history** — BinanceVision offers liquidation snapshots only from 2021 daily for some symbols;
   coverage gaps too large for backtests; useful for live-event engine (new architecture), not lab.
3. **Long/short account ratios** — BinanceVision daily metrics contain them only recent years; thin.
4. **Social/narrative series** — absent entirely; the new strategic direction depends on it (see §10).
5. **Early-token pools data** (post-launch DEX state) — irrelevant for majors lab, central for new mission.

## Q7. Is BTC-specific research scientifically justified?
**Yes, under declared instrument-scope (pre-registered), with these constraints:**
(a) scope declared BEFORE testing (done for H13 card);
(b) no transfer claims to other assets without separate cards;
(c) multiplicity bar applied (done: PF>1.5);
(d) economic rationale required (BTC = deepest OI pool → cleanest flow signal — documented).
H13 tested this exactly and still failed the bar → the lab's integrity held even for the strongest candidate.

## Q8. Should the next research cycle remain cross-asset?
**No for the trading-direction search; yes for methodology validation.**
The strategic correction (Opportunity Intelligence) shifts the unit of analysis from "1h signals on 3
majors" to "early-token event detection" — a SMALLER-EFFICIENCY environment where published inefficiencies
(monitoring delay, security information asymmetry, narrative formation) are structurally larger. Majors-lab
work continues only as machinery calibration, not as the edge hunt.

## Q9. What new data would materially increase information value?
Ranked by expected info-per-effort (free sources mandatory per cost constraint):
1. **DEX pool state + new-pair feeds** (DexScreener free API / GeckoTerminal free API) — enables the actual mission.
2. **On-chain token security checks** (GoPlus free API, RugCheck) — enables Security Veto (mandated).
3. **Holder distribution / top wallets** (public RPCs, Solana/Ethereum-indexed public endpoints) — whale engine.
4. **Kline/funding already have** ✓ (BinanceVision, 7y).
5. News velocity (RSS/CryptoPanic free tier) — narrative engine MVP.
Premium social APIs (X active-search) are cost-blocked → explicitly excluded until revenue exists.

## Q10. Minimum defensible next experiment?
**E-01 (observational, ZERO capital):** paper-level event study on early tokens — collect DexScreener new-pair
candidates for 8+ weeks; at detection time record the full feature vector (liquidity, vol, security flags,
holders when available, social counts when available); label each with realized +X%/Y-hour outcomes across
horizons (15m/1h/4h/12h/24h/72h/7d); then test whether ANY feature set separates positive from negative
outcomes with honest multiple-testing control. Only THEN may a scoring weight be fit (on train only).
Why defensible: (a) no backtest-narrative bias — forward paper collection, no hindsight selection;
(b) matches the TRUE mission; (c) produces the dataset the Opportunity Score needs before ANY weight exists.

## COUNCIL DISAGREEMENT RECORD (kept open, not hidden)
Quant Lead: "H13's PF 1.27 over 31 OOS trades with MC 75.9% is non-trivial; worth live-paper observation."
Stats Expert: "Under 3 consumed OOS looks and 13 prior candidates, p-value ~ (1-binom)… not significant;
paper observation acceptable ONLY as E-01-style forward logging, never as position signal."
Auditor ruling: recorded ACCEPTED-as-noted = hypothesis remains REJECTED for trading; paper logging allowed.
