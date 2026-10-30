"""Our one-dimensional latent return. PAPER_ONLY.

The shadow sign is the sign of an exponential average of that desk's own
closed paper returns. Two fixed speeds are the two trials. No upstream
model is downloaded or run. The live weight is not written.
"""
from __future__ import annotations

from typing import Any

from architecture.university.kl_dro_shadow import _ordered, block_sums
from architecture.university.research_institute import DESKS

ALPHA_SLOW = 0.2
ALPHA_FAST = 0.5
WARMUP = 8
HYPOTHESIS = (
    "The shadow sign is the sign of a latent state that is an exponential "
    "average of that desk's earlier paper returns. Speed 0.2 is the scored "
    "path. Speed 0.5 is the second trial. No upstream world model is run."
)


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def strategy_path(closes: list[dict[str, Any]], alpha: float) -> tuple[list[float], dict[str, int]]:
    history: dict[str, list[float]] = {}
    latent: dict[str, float] = {}
    path: list[float] = []
    counts = {"hits": 0, "misses": 0, "flat": 0}
    for desk, ret in _ordered(closes):
        prior = history.get(desk) or []
        if len(prior) >= WARMUP:
            state = latent.get(desk, 0.0)
            side = _sign(state)
            path.append(side * ret)
            realized = _sign(ret)
            if side == 0 or realized == 0:
                counts["flat"] += 1
            elif side == realized:
                counts["hits"] += 1
            else:
                counts["misses"] += 1
            latent[desk] = (1.0 - alpha) * state + alpha * ret
        history.setdefault(desk, []).append(ret)
        if len(history[desk]) == WARMUP and desk not in latent:
            latent[desk] = sum(history[desk]) / WARMUP
    return path, counts


def _latent_scores(closes: list[dict[str, Any]], alpha: float) -> dict[str, float | None]:
    grouped: dict[str, list[float]] = {desk: [] for desk in DESKS}
    for desk, ret in _ordered(closes):
        grouped[desk].append(ret)
    scores: dict[str, float | None] = {}
    for desk, sample in grouped.items():
        if not sample:
            scores[desk] = None
            continue
        state = 0.0
        for ret in sample:
            state = (1.0 - alpha) * state + alpha * ret
        scores[desk] = round(state, 6)
    return scores


def evaluate(closes: list[dict[str, Any]]) -> dict[str, Any]:
    primary, counts = strategy_path(closes, ALPHA_SLOW)
    alternate, _ignored = strategy_path(closes, ALPHA_FAST)
    split = int(len(primary) * 0.6)
    oos = primary[split:]
    blocks_a = block_sums(primary)
    blocks_b = block_sums(alternate)
    trials = [blocks_a, blocks_b] if blocks_a is not None and blocks_b is not None else []
    scored = counts["hits"] + counts["misses"]
    grouped = {desk: 0 for desk in DESKS}
    for desk, _ret in _ordered(closes):
        grouped[desk] += 1
    return {
        "hypothesis": HYPOTHESIS,
        "predicted_score": _latent_scores(closes, ALPHA_SLOW),
        "sample_n": grouped,
        "oos_returns": oos,
        "trial_returns": trials,
        "rho": {"slow": ALPHA_SLOW, "fast": ALPHA_FAST},
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
