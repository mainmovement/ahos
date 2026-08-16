# AHOS — EXACT BACKTEST RE-COMPUTATION REPORT (Agent-09 QA + Agent-07 LeadEng)
# Date: 2026-08-10 | Engine: ahos_backtest.py v1.0 | Data: REAL, audited
# Supersedes approximate Phase-2 numbers with exact, reproducible metrics.

## DATA BASIS (audited by engine/data_audit.py)
| Symbol | File | Rows | Span | Integrity |
|---|---|---|---|---|
| BTCUSDT | LBANK_BTCUSDT_1h_2000_clean.csv | 1997 | 2026-05-17 → 2026-08-09 (~83d) | PASS (2 bad rows removed, REGISTERED, 2 known 2h gaps) |
| ETHUSDT | LBANK_ETHUSDT_1h_2000.csv | 2000 | 2026-05-17 → 2026-08-09 | PASS (0% missing, 0 gaps) |
| SOLUSDT | LBANK_SOLUSDT_1h_2000.csv | 2000 | 2026-05-17 → 2026-08-09 | PASS (0% missing, 0 gaps) |

LIMITATION (unchanged, not hidden): ~83 days, NOT the 3-year requirement (~26,000 candles).
Therefore OOS/WF/MC below are ENGINE-VERIFICATION results, not production evidence.

## EXACT RESULTS — Frozen Baseline v1.0 (fees 0.055%/side + slippage 0.02%/side, lev 2x, risk 2%)
## v1.1 RUN (2026-08-10): DD-cap permanent-stop FIX applied — engine now enforces the 20% rule it always documented.

| Metric | BTCUSDT | ETHUSDT | SOLUSDT | Gate (Phase-2 criteria) |
|---|---|---|---|---|
| Trades (run stopped at DD-breach) | 85 | 26 | 30 | — |
| Win Rate | 44.7% | 23.1% | 30.0% | FAIL (<48%) ✗ all 3 |
| Profit Factor | 0.890 | 0.362 | 0.476 | FAIL (<1.3) ✗ all 3 |
| Expectancy/trade | −0.107 | −0.787 | −0.724 | FAIL (negative) ✗ |
| Total Return | −9.1% | −20.5% | −21.7% | FAIL ✗ |
| Max Drawdown (now enforced ≤20%) | 20.4% | 20.5% | 21.7% | FAIL (<15% required) ✗ |
| Sharpe (ann.) | −0.97 | −4.65 | −4.04 | FAIL ✗ |
| MC positive (1000 sims) | 30.4% | 0.8% | 3.4% | FAIL (<70%) ✗ |

Historical note: pre-fix v1.0 run (2026-08-09 figures: 234/275/253 trades, PF 0.74/0.72/0.78,
MaxDD 51–59%) is superseded but archived in git-history-equivalent (reports never deleted).
Meaning of the delta: the risk layer was SUPPOSED to stop at 20% DD; the audit found it only
recorded the breach. With enforcement active, capital survives (~9–22% loss vs 48–59%) and the
no-edge conclusion becomes stronger (PF still <1 on every symbol; expectancy negative on all).

Train/OOS(70/30, fixed rules) PF: BTC 0.890/0.417 · ETH 0.362/0.668 · SOL 0.476/0.729 → all OOS PF < 1.0.
Walk-Forward (4 windows × 3 symbols): every test window PF ∈ 0.249–0.925, ALL < 1.0 → FAIL every window.
Monte Carlo (1000 sims, seeded, with enforced DD stop): positive outcomes BTC 30.4% / ETH 0.8% / SOL 3.4%;
P(DD>20%) = 60.4% / 60.3% / 67.5% → FAIL (<70% positive required) ✗✗✗
Raw JSON evidence: reports/validation_results.json (reproducible: engine/run_validation.py, MC seed=42).

## VERDICT (Agent-10 binding)
**FROZEN BASELINE STRATEGY v1.0 HAS NO EDGE ON AVAILABLE REAL DATA. LIVE GATE: CLOSED.**
This CONTRADICTS the earlier approximate Phase-2 report (54 trades, PF ~1.1, "+0.09%"). See ISSUES_REGISTER.md #C1 for the technical explanation of the discrepancy — neither datasets nor strategy changed; the earlier figures were approximations from a thinner cost model.

## WHAT THIS MEANS (honest, per the 12 rules)
1. The strategy must be REDESIGNED (new hypothesis → backtest → OOS → WF → MC) before
   even PAPER proceeds. This is the process working as designed, not a failure of process.
2. The engine itself is validated: deterministic, no look-ahead (pytest proven),
   risk caps enforced, MC seeded/reproducible.
3. No parameter tuning may be applied to v1.0 using this OOS window (OOS-untouched law):
   any v2.0 strategy needs a fresh split and full 3yr data.
4. Recommended next actions (start of Phase 2-rebuild):
   a) Acquire 3yr dataset (VPS + Bybit chunked loop, or verified CSV export) — top blocker.
   b) Rebuild strategy hypothesis with regime filter + funding/OI features (data currently absent).
   c) Re-run full Phase 2/3 battery on 3yr before any paper/live discussion.
