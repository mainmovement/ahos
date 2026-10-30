"""Our KL-robust expected return. PAPER_ONLY.

The idea is the worst-case mean of a desk's own closed paper returns inside a
KL ball around the empirical distribution. The dual is the standard one: the
supremum over a fixed lambda grid of -lambda * rho - lambda * log(mean(exp(-r/lambda))).
No paper repository is cloned and no upstream code is executed. The shadow
sign is that robust mean. A live weight is not written.
"""
from __future__ import annotations

import math
from typing import Any

from architecture.university.research_institute import DESKS

RHO_PRIMARY = 0.05
RHO_ALT = 0.15
WARMUP = 8
N_BLOCKS = 8
LAMBDAS = (0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
HYPOTHESIS = (
    "The shadow sign on a desk is the sign of the KL-robust expected return "
    "of that desk's own closed paper returns. Radius 0.05 is the scored path. "
    "Radius 0.15 is the second trial. Both use a fixed lambda grid."
)


def kl_robust_mean(returns: list[float], rho: float, lambdas: tuple[float, ...] = LAMBDAS) -> float | None:
    """Worst-case mean inside a KL ball. Equal returns stay equal. A wider ball cannot raise the mean."""
    xs = [float(x) for x in returns if isinstance(x, (int, float)) and not isinstance(x, bool)]
    n = len(xs)
    if n == 0 or rho < 0:
        return None
    if rho == 0 or n == 1:
        return sum(xs) / n
    best: float | None = None
    for lam in lambdas:
        if lam <= 0:
            continue
        scaled = [-x / lam for x in xs]
        peak = max(scaled)
        log_mean = peak + math.log(sum(math.exp(item - peak) for item in scaled) / n)
        value = -lam * rho - lam * log_mean
        if best is None or value > best:
            best = value
    return best


def _return_of(close: dict[str, Any]) -> tuple[str, str, float] | None:
    notional = close.get("notional_usd")
    pnl = close.get("realized_pnl_usd")
    desk = close.get("desk")
    if not isinstance(desk, str) or desk not in DESKS:
        return None
    if not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
        return None
    if not isinstance(notional, (int, float)) or isinstance(notional, bool) or float(notional) <= 0:
        return None
    return desk, str(close.get("closed_at") or ""), float(pnl) / float(notional)


def _ordered(closes: list[dict[str, Any]]) -> list[tuple[str, float]]:
    parsed = [row for row in (_return_of(close) for close in closes) if row is not None]
    parsed.sort(key=lambda item: item[1])
    return [(desk, ret) for desk, _when, ret in parsed]


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def strategy_path(closes: list[dict[str, Any]], rho: float) -> tuple[list[float], dict[str, int]]:
    """Each step uses only earlier closes on that desk. The step return is sign(score) times the close."""
    history: dict[str, list[float]] = {}
    path: list[float] = []
    counts = {"hits": 0, "misses": 0, "flat": 0}
    for desk, ret in _ordered(closes):
        prior = history.get(desk) or []
        if len(prior) >= WARMUP:
            score = kl_robust_mean(prior, rho)
            side = 0 if score is None else _sign(score)
            path.append(side * ret)
            realized = _sign(ret)
            if side == 0 or realized == 0:
                counts["flat"] += 1
            elif side == realized:
                counts["hits"] += 1
            else:
                counts["misses"] += 1
        history.setdefault(desk, []).append(ret)
    return path, counts


def block_sums(path: list[float], n_blocks: int = N_BLOCKS) -> list[float] | None:
    """Eight equal contiguous sums covering the tail of the path. Shorter paths stay unmeasured."""
    if len(path) < n_blocks:
        return None
    size = len(path) // n_blocks
    used = path[-(n_blocks * size):]
    return [sum(used[i * size:(i + 1) * size]) for i in range(n_blocks)]


def predicted_scores(closes: list[dict[str, Any]], rho: float = RHO_PRIMARY) -> dict[str, float | None]:
    grouped: dict[str, list[float]] = {desk: [] for desk in DESKS}
    for desk, ret in _ordered(closes):
        grouped[desk].append(ret)
    scores: dict[str, float | None] = {}
    for desk in DESKS:
        sample = grouped[desk]
        scores[desk] = None if not sample else round(float(kl_robust_mean(sample, rho)), 6)
    return scores


def evaluate(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk-forward path, trailing 40 percent as the DSR sample, two radii as the PBO trials."""
    primary, counts = strategy_path(closes, RHO_PRIMARY)
    alternate, _ignored = strategy_path(closes, RHO_ALT)
    split = int(len(primary) * 0.6)
    oos = primary[split:]
    blocks_a = block_sums(primary)
    blocks_b = block_sums(alternate)
    trials = [blocks_a, blocks_b] if blocks_a is not None and blocks_b is not None else []
    scored = counts["hits"] + counts["misses"]
    grouped: dict[str, int] = {desk: 0 for desk in DESKS}
    for desk, _ret in _ordered(closes):
        grouped[desk] += 1
    return {
        "hypothesis": HYPOTHESIS,
        "predicted_score": predicted_scores(closes),
        "sample_n": grouped,
        "oos_returns": oos,
        "trial_returns": trials,
        "rho": {"primary": RHO_PRIMARY, "alternate": RHO_ALT},
        "n_steps": len(primary),
        "n_oos": len(oos),
        "counterfactual": {
            "hits": counts["hits"],
            "misses": counts["misses"],
            "flat": counts["flat"],
            "hit_rate": round(counts["hits"] / scored, 4) if scored else None,
            "applied_to_live_weights": False,
        },
        "upstream_executed": False,
        "applied_to_live_weights": False,
    }
