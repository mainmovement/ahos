"""M13 Edge Expectancy Bootstrap Gate & CME Micro (MGC/MCL) margin education simulator. PAPER_ONLY."""
from __future__ import annotations

import math
import random
from typing import Any, Mapping, Sequence

PAPER_ONLY: bool = True

LEVERAGE_TIERS: tuple[int, ...] = (1, 2, 3, 5, 10, 25)
BOOTSTRAP_DRAWS: int = 500
BOOTSTRAP_SEED: int = 42


def evaluate_expectancy_bootstrap(
    trade_returns: Sequence[float],
    *,
    cost_per_trade: float = 0.0,
    seed: int = BOOTSTRAP_SEED,
    draws: int = BOOTSTRAP_DRAWS,
) -> dict[str, Any]:
    """E = Pw*W - Pl*L - C with seeded bootstrap CI; hold unless n>=30 and ci95_lower>0."""
    n = len(trade_returns)
    if n == 0:
        return {
            "sample_size": 0,
            "expectancy_per_trade": 0.0,
            "ci95_lower": 0.0,
            "ci95_upper": 0.0,
            "verdict": "NO_PROVEN_EDGE_HOLD",
            "paper_only": True,
            "live": False,
        }

    wins = [float(r) for r in trade_returns if float(r) > 0]
    losses = [float(r) for r in trade_returns if float(r) <= 0]
    pw = len(wins) / n
    pl = 1.0 - pw
    mean_w = sum(wins) / len(wins) if wins else 0.0
    mean_l = abs(sum(losses) / len(losses)) if losses else 0.0
    expectancy = pw * mean_w - pl * mean_l - float(cost_per_trade)

    rng = random.Random(seed)
    boot: list[float] = []
    for _ in range(draws):
        sample = [float(trade_returns[rng.randrange(n)]) for _ in range(n)]
        boot.append(sum(sample) / n - float(cost_per_trade))
    boot.sort()
    lo_idx = max(0, int(0.025 * draws))
    hi_idx = min(draws - 1, int(0.975 * draws))
    ci_lower = boot[lo_idx]
    ci_upper = boot[hi_idx]

    if n < 30 or ci_lower <= 0.0:
        verdict = "NO_PROVEN_EDGE_HOLD"
    else:
        verdict = "STATISTICAL_EDGE_CANDIDATE_PAPER"

    return {
        "sample_size": n,
        "expectancy_per_trade": round(expectancy, 6),
        "win_rate_pct": round(pw * 100.0, 2),
        "avg_win": round(mean_w, 6),
        "avg_loss": round(mean_l, 6),
        "cost_per_trade": round(float(cost_per_trade), 6),
        "ci95_lower": round(ci_lower, 6),
        "ci95_upper": round(ci_upper, 6),
        "verdict": verdict,
        "paper_only": True,
        "live": False,
    }


def _classification_for_leverage(leverage: int) -> tuple[str, str]:
    if leverage <= 3:
        return (
            "SAFE_PAPER_BAND",
            "اهرم تا ۳× در محدودهٔ آموزشی کاغذی؛ فاصلهٔ نقدشوندگی معمولاً از نوسان ATR بیشتر است.",
        )
    if leverage == 5:
        return (
            "CAUTION_ELEVATED_RISK",
            "اهرم ۵× ریسک مارجین‌کال را بالا می‌برد؛ فقط برای آزمایش کاغذی با سقف سرمایهٔ ثابت.",
        )
    return (
        "VETO_RUIN_DANGER",
        "اهرم ۱۰× یا بالاتر در شوک ۳×ATR احتمال مارجین‌کال و ریسک نابودی سرمایه را به‌شدت افزایش می‌دهد (فقط آموزشی — وتوی کاغذی).",
    )


def simulate_instrument_leverage_ladder(
    symbol: str,
    *,
    atr_pct: float = 1.25,
    maintenance_margin_pct: float = 50.0,
    tail_shock_atr: float = 3.0,
) -> list[dict[str, Any]]:
    """Educational liquidation distance table for CME micro contracts (not live trading)."""
    rows: list[dict[str, Any]] = []
    for lev in LEVERAGE_TIERS:
        liq_dist_pct = max(0.1, (100.0 / lev) * (1.0 - maintenance_margin_pct / 100.0))
        atr_mult = liq_dist_pct / atr_pct if atr_pct > 0 else 999.0
        shock_move = tail_shock_atr * atr_pct
        margin_call_under_shock = shock_move >= liq_dist_pct
        band, warning_fa = _classification_for_leverage(lev)
        rows.append(
            {
                "symbol": symbol,
                "leverage": lev,
                "liquidation_distance_pct": round(liq_dist_pct, 4),
                "atr_multiple_to_liquidation": round(atr_mult, 2),
                "maintenance_margin_pct": maintenance_margin_pct,
                "margin_call_prob_3atr_shock": "HIGH" if margin_call_under_shock else "LOW",
                "classification": band,
                "warning_fa": warning_fa,
                "paper_only": True,
                "live": False,
            }
        )
    return rows


def build_edge_margin_snapshot(
    trade_returns: Sequence[float] | None = None,
    *,
    cost_per_trade: float = 0.0008,
) -> dict[str, Any]:
    """Canonical deterministic snapshot for Arena bridge (educational fixtures)."""
    rets = list(trade_returns) if trade_returns is not None else [
        0.0042,
        -0.0021,
        0.0035,
        -0.0018,
        0.0029,
        0.0011,
        -0.0032,
        0.0024,
        -0.0015,
        0.0030,
        0.0018,
        -0.0025,
        0.0022,
        0.0016,
        -0.0012,
        0.0027,
        0.0033,
        -0.0019,
        0.0020,
        0.0014,
        -0.0028,
        0.0031,
        0.0025,
        -0.0016,
        0.0028,
        0.0019,
        -0.0022,
        0.0034,
        0.0021,
        -0.0011,
    ]
    expectancy = evaluate_expectancy_bootstrap(rets, cost_per_trade=cost_per_trade)
    small_sample = evaluate_expectancy_bootstrap(rets[:12], cost_per_trade=cost_per_trade)
    return {
        "schema": "ahos.edge_margin_sim.v1",
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "expectancy_gate": expectancy,
        "expectancy_gate_small_sample_demo": small_sample,
        "instruments": {
            "MGC": {
                "name_en": "CME Micro Gold (MGC, 10 troy oz)",
                "atr_pct": 1.25,
                "leverage_ladder": simulate_instrument_leverage_ladder("MGC", atr_pct=1.25),
            },
            "MCL": {
                "name_en": "CME Micro WTI Crude (MCL, 100 barrels)",
                "atr_pct": 2.10,
                "leverage_ladder": simulate_instrument_leverage_ladder("MCL", atr_pct=2.10),
            },
        },
    }
