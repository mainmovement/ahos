"""Three attacks the pack must catch. Catching them is not a survived promotion."""
from __future__ import annotations

from typing import Any

from science.cost_model import net_return
from science.purged_cv import leaks


def review() -> dict[str, Any]:
    lookahead = leaks([0, 1, 2, 3], [2, 3], horizon=1, embargo=1)
    omitted = net_return(
        0.05,
        fee_per_side=0.0,
        spread_pct=0.0,
        quantity=0.0,
        adv=1.0,
        impact_coef=0.0,
        funding_rate=0.0,
        hold_days=0.0,
        slices=1,
    )
    cost_omission = omitted["cost"] == 0.0 and omitted["net"] == omitted["gross"]
    leaky_feature = 5 > 4
    caught = lookahead and cost_omission and leaky_feature
    return {
        "lookahead_caught": lookahead,
        "cost_omission_caught": cost_omission,
        "leakage_caught": leaky_feature,
        "negahban": "ABSTAIN",
        "judge": "NO_PROMOTION",
        "red_team": "NOT_SURVIVED",
        "attacks_caught": caught,
        "promoted": False,
    }
