# T0 -> T1 promotion gate — oil

Tier today: **T0** (paper only, no execution).
Promoted by this evaluation: **False** — promotion is an owner act plus the three gate agents (قاسم AG-16, رضا AG-19, سپهر AG-03), never a code decision.

2/4 measurable criteria passed; 7 unmeasurable.

| Criterion | Required | Measured | Pass | Detail |
|---|---|---|---|---|
| `data_depth_months` | >=6 months | 0.00 | FAIL | 0.00 months of real data |
| `trade_count` | >=200 trades | 0 | FAIL | 0 recorded trades |
| `regime_coverage` | >=3 of 4 regimes, >=30 trades each | 3 regimes defined | UNMEASURABLE | UNMEASURABLE as specified: architecture/intel/regimes.py defines 3 regimes (BULL_TREND, BEAR_VOLATILE, NEUTRAL_CHOP) but the exit gate requires >=3 of 4. A fourth regime has no label in code -- MarketRegimeClassifier(n_regimes=4) would relabel the extra state to NEUTRAL_CHOP via the REGIME_LABELS.get fallback at regimes.py:92 -- so it is not invented here. |
| `cost_model` | net of fees and funding with 2x slippage | REPLAY_NOT_LIVE: net of fees and funding with 2x slippage — oil 13 bps/side (26 bps RT per CL=F replay); stress grid in results.md | PASS | declared cost model: REPLAY_NOT_LIVE: net of fees and funding with 2x slippage — oil 13 bps/side (26 bps RT per CL=F replay); stress grid in results.md |
| `max_drawdown_pct` | <=15.0% | — | UNMEASURABLE | no trades recorded, drawdown undefined |
| `drawdown_vs_backtest_multiple` | <=1.5x backtest | — | UNMEASURABLE | no paper drawdown recorded to compare |
| `sharpe` | >=1.0 | — | UNMEASURABLE | fewer than two trades, Sharpe undefined |
| `dsr_psr` | >=0.95 | — | UNMEASURABLE | no Sharpe, so DSR/PSR is undefined |
| `profit_factor` | >=1.3 | — | UNMEASURABLE | no losing trades recorded, PF undefined |
| `month_profit_share_pct` | no month >40.0% | — | UNMEASURABLE | no profitable month recorded yet |
| `walk_forward` | walk-forward and out-of-sample evidence required | supplied | PASS | walk-forward and out-of-sample splits present |

## Owner questions

- M-REGIME-4: the exit gate's >=3-of-4 regime coverage cannot be evaluated because only 3 regimes are defined (architecture/intel/regimes.py). Owner act: either name the fourth regime the gate intends, or amend the gate to 3.

## Unmeasurable criteria

These block readiness rather than being waived:
- `regime_coverage`
- `max_drawdown_pct`
- `drawdown_vs_backtest_multiple`
- `sharpe`
- `dsr_psr`
- `profit_factor`
- `month_profit_share_pct`

**Not ready for owner review.** Measurable criteria must all pass and every criterion must be evaluable before the T1 act is available.
