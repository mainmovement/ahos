# AHOS — STRATEGY RESEARCH LABORATORY v2.0 — FINDINGS REPORT
# Date: 2026-08-10 · Data: REAL 3.6y BinanceVision USDT-M (BTC/ETH/SOL 1h, 31,608 candles each;
# funding 3,924 points; OI 1,317 daily) · sha-pinned in research/data/MANIFEST.json
# Battery: Train(70%)/OOS(30%) + WF(12mo→3mo) + MonteCarlo(1000,seed=42) + Stress(2×costs)
# Gates: OOS PF>1.3 · expectancy>0 · OOS DD<15% · MC>70% positive · WF≥60% profitable windows · stress PF>1.1 · ≥30 OOS trades
# Method rule: hypotheses registered BEFORE results (strategy_lab/hypotheses.py), params = a-priori
# literature defaults, ZERO tuning. Evidence: research/experiments/exp_20260810_121055.json

## RESULT MATRIX (OOS window = final 30% ≈ 2025-04 → 2026-08)
| ID | Candidate | BTC PF | ETH PF | SOL PF | BTC WR | MC+ (BTC) | Stress PF (BTC) | Verdict |
|---|---|---|---|---|---|---|---|---|
| H1 | Donchian 55/20 trend | 0.61 | 1.23 | 0.81 | 27.6% | 16.8% | 0.53 | REJECTED |
| H2 | Bollinger z20 ±2 reversion | 0.31 | 0.22 | 0.34 | 25.0% | 0.1% | 0.21 | REJECTED |
| H3 | ATR squeeze breakout | 0.89 | 0.75 | 0.80 | 38.5% | 30.4% | 0.76 | REJECTED |
| H4 | ADX>25 EMA20 pullback | 0.71 | 0.67 | 0.39 | 35.1% | 9.2% | 0.46 | REJECTED |
| H5 | Extreme funding contrarian | 0.66 | 0.43 | 0.31 | 23.1% | 14.8% | 0.30 | REJECTED |
| H6 | OI expansion + price | 3.13 | 0.93 | 0.93 | 73.7% | 100.0% | 2.41 | REJECTED (unstable) |
| H7 | Volume shock continuation | 0.31 | 0.75 | 1.05 | 29.0% | 0.0% | 0.19 | REJECTED |
| H8 | Order-book imbalance | — | — | — | — | — | — | NOT TESTED (data-blocked) |
| H9 | Multi-factor composite | 1.38 | 1.01 | 0.61 | 45.9% | 86.5% | 0.93 | REJECTED (fragile) |

**ACCEPTED: 0 of 8 testable.** Live gate remains CLOSED. This is the process producing correct output.

## KEY SCIENTIFIC FINDINGS
1. **H6-BTC is a genuine anomaly, not an accepted strategy**: OOS PF 3.13 / WR 73.7% / DD 8.1% /
   MC 100% / stress 2.41 — BUT train PF 0.35 and ETH/SOL OOS ~0.93. Diagnosis: OI-flow edge on BTC
   appears regime-bound to the OOS period (2025-04→2026-08). Cross-asset instability + train-window
   failure = gate REJECT. **Research lead L1** (see below).
2. **H9-BTC profile is the strongest overall composite**: full-run 180 trades, WR 53.9%, PF 1.34,
   +76.5%, DD 17.3%; OOS PF 1.38, DD 7.3%, MC 86.5%. Failure: stress PF 0.93 (2×cost kills it) and
   ETH/SOL diverge. Diagnosis: thin per-trade edge eaten by frictions. **Research lead L2.**
3. **H1 trend: train PF 1.41 (BTC) vs OOS 0.61** — textbook regime rotation: breakout trend worked
   2023-2024, decayed from 2025. Confirms regime gating as prerequisite; H4's attempt to gate with
   ADX failed too (lag) → regime detection needs better mechanism. **Research lead L3.**
4. Mean reversion (H2) is structurally hostile on 1h majors in this dataset (train PF 0.035 on BTC).
   Funding contrarianism (H5) sparse + weak. Volume shocks (H7) mostly exhaustion, not continuation.

## RESEARCH LEADS REGISTERED (v2.1 candidates — MUST be registered as NEW hypotheses before any test)
- **L1 → H10 (candidate)**: OI expansion conditioned on BTC-specific liquidity regime + volatility filter;
  explain WHY train-window OI signals failed (crowded-side asymmetry?). Requires: hypothesis doc first.
- **L2 → H11 (candidate)**: composite score with cost-aware entry threshold + per-asset stability constraints;
  investigate funding term contribution (ablation WITHOUT weight re-fitting? document protocol).
- **L3 → H12 (candidate)**: regime layer via realized-vol state machine (3-state) as preconditioner for H1-style
  trend entries; regime definition fixed a-priori; test as separate hypothesis with own Train/OOS.
- Data note: funding coverage ends 2026-07-31 (9 CDN files absent — manifest-logged, none fabricated).
- H8 remains data-blocked until L2 order-book source is acquired.

## BATCH-2 ADDENDUM (2026-08-10, raised bar: OOS PF>1.5 — multiplicity guard for second look at OOS)
Three NEW hypotheses built strictly from batch-1's documented failure modes. Registered in
hypotheses.py before any run. Evidence: research/experiments/exp_20260811_154550.json

| ID | Candidate | BTC PF(oos) | ETH | SOL | Note | Verdict |
|---|---|---|---|---|---|---|
| H10 | OI expansion, HIGH-vol regime only | **2.35** (WR 68.8%, DD 8.1%, stress 1.78, MC 95.2%) | 0.50 | 0.72 | BTC-only effect; 16 OOS trades (<30 gate) → fails cross-asset + sample | REJECTED |
| H11 | Composite conviction-extremes |S|≥0.8 | 0 trades | 0 | 0 | Falsified by zero-signal (score never reaches extremes on this scale) | REJECTED |
| H12 | RV 3-state Donchian 20h | 0.69 | 1.16 | 0.95 | RV gating ≠ regime fix; ETH streaky (wf 70%) but unstable | REJECTED |

Scientific read:
1. The H6→H10 refinement CONFIRMED the mechanism: regime-gating improves BTC OOS from 3.13-ish noisy to
   robust stress-surviving 2.35 — but ONLY for BTC. The effect is instrument-specific, not asset-class.
   Batch-1 lead L1 is thereby exhausted under current gates (cross-asset stability is mandatory).
2. Composite-score edge density does NOT concentrate at |S|≥0.8 extremes (zero entries) — the H9 family
   ceiling is structural on this feature scaling. L2 closed.
3. Regime rotation remains the field problem: neither ADX lag (H4) nor RV terciles (H12) fix trend entry decay.
   L3 partially falsified; remaining lead: same-week/weekend seasonality & funding-TREND interaction, or longer
   evaluation scope on BTC-only instrument with a-priori instrument declaration (future H13 card required).
No live path opened. Gates held.

## REPRODUCIBILITY
`python3 strategy_lab/run_lab.py` → new timestamped experiment log; `bash engine/run_all_checks.sh` covers
integrity, tests, dry-runs, telegram harness, workflow validation. Registry: strategy_lab/registry.json.

---
## ADDENDUM (2026-08-11) — Batch-3 closed, program point reached
- **H13 (BTC-scoped OI × high-RV regime, 6.6y ext data): REJECTED** at pre-registered batch-3 bar (OOS PF>1.5).
  train PF 1.214 · OOS PF 1.274 · WR 54.84% · DD 10.86% · MC 75.9% · stress 0.976 · WF 50% · 31 OOS trades.
  H10's OOS PF 2.35 confirmed as small-sample inflation (n=16→31). Evidence: exp_20260811_165329.json · Issue R-07.
- Post-H13 structured review (mandated, executed BEFORE any further hypothesis work):
  **RESEARCH_META_ANALYSIS_v1.md** — 10 questions, council disagreement recorded, falsification ledger updated.
- FINAL LAB VERDICT: H1–H13 → 0 ACCEPTED (H8 never testable: L2 order-book data).
  The minimum defensible forward experiment is NOT another backtest — it is **E-01: forward paper event study
  on early tokens** (≥8 weeks pre-registration, 7 horizons: 15m/1h/4h/12h/24h/72h/7d; defined in Meta-Analysis Q10).
- Consequence for the platform: scoring weights in OPPORTUNITY_SCORE_DESIGN_v0.1 stay rank-only (unvalidated
  hypotheses) until E-01 evidence exists. UNKNOWN stays UNKNOWN.
