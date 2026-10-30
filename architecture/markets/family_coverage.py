"""Per-desk vote-family coverage. Design record, not a live score.

Gates are read from the constants. This module does not change them.
"""
from __future__ import annotations

from typing import Any

from architecture.markets.cftc_cot import CFTC_CURRENT_URL, selection_record
from architecture.markets.paper_trade_gates import (
    INDEPENDENT_VOTE_FAMILIES,
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)
from architecture.markets.research_desk_signal import DESK_TO_PIPELINE

_IN_CYCLE = {
    "news": "news_signal when two sources corroborate",
    "macro_central_bank": "macro_pressure and macro_event",
    "candle_wicks": "candle_patterns on closed bars",
}


def family_coverage() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for desk in DESK_TO_PIPELINE:
        for family, members in INDEPENDENT_VOTE_FAMILIES.items():
            rows.append(_row(desk, family, members))
    return {
        "schema": "ahos.family_coverage.v1",
        "paper_only": True,
        "gates_unchanged": {
            "min_agreeing_families": MIN_AGREEING_FAMILIES,
            "vote_score_floor": VOTE_SCORE_FLOOR,
            "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        },
        "rows": rows,
    }


def _row(desk: str, family: str, members: tuple[str, ...]) -> dict[str, Any]:
    base = {"desk": desk, "family": family, "members": list(members)}
    if family == "research":
        return {
            **base,
            "status": "ADVISORY_VOTE",
            "composite_weight": "0 unless PASS_STATS+SURVIVED_RED_TEAM",
            "source": "existing shadow-registry and strategy-switch predicted_score",
        }
    if family == "whales" and desk == "CRYPTO":
        return {
            **base,
            "status": "LIVE_FEEDS",
            "composite_weight": "exchange_netflow and whale_mempool are 0; large_trades keeps its existing weight",
            "source": "large_trades, exchange_netflow, whale_mempool",
        }
    if family == "whales":
        record = selection_record()
        contracts = {}
        if desk == "OIL":
            contracts = {"WTI": record["WTI"], "BRENT": record["BRENT"]}
        elif desk == "GOLD":
            contracts = {"XAU": record["XAU"]}
        if contracts:
            return {
                **base,
                "status": "CFTC_COT",
                "composite_weight": 0,
                "source": CFTC_CURRENT_URL,
                "contracts": contracts,
                "score": "tanh(z/2) versus the contract's own prior 52 weeks",
            }
        return {
            **base,
            "status": "ABSENT_BY_DESIGN",
            "composite_weight": 0,
            "source": None,
            "reason": "no verified free public positioning file is wired for this desk",
        }
    return {**base, "status": "IN_CYCLE", "source": _IN_CYCLE.get(family, "cycle signal")}
