"""Pre-register, then write the board. A missing path is not a DSR."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.learning.walk_forward import deflated_sharpe, pbo_cscv, sharpe
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)
from architecture.strategies.library import SPECS
from architecture.strategies.meta_brain import thompson_weights
from architecture.strategies.signals import apply_cost, shadow_round_trips, sign_on_closes
from architecture.strategies.wisdom import review_book

REGISTRY_REL = Path("reports") / "grok" / "PAPER" / "strategy_library_registry.json"
OUT_REL = Path("reports") / "grok" / "PAPER" / "strategy_leaderboard.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_registry(root: Path) -> dict[str, Any]:
    path = Path(root) / REGISTRY_REL
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    doc = {
        "schema": "ahos.strategy_library_registry.v1",
        "paper_only": True,
        "registered_at": _utc(),
        "strategies": [row["id"] for row in SPECS],
        "oos_fraction": 0.4,
        "min_oos": 30,
        "dsr_min": 0.95,
        "pbo_max": 0.5,
        "after_fees": True,
        "min_agreeing_families": MIN_AGREEING_FAMILIES,
        "vote_score_floor": VOTE_SCORE_FLOOR,
        "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        "promotion_rule": (
            "A strategy stays shadow until fresh closes after this stamp "
            "have DSR above 0.95, PBO under 0.5, a walk-forward out-of-sample "
            "window of at least 30, fees deducted, and a red team that survived."
        ),
        "applied_to_live": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def gate(
    *,
    dsr: float | None,
    pbo: float | None,
    oos_n: int,
    after_fees: bool,
    fresh: bool,
    red_team_survived: bool,
) -> bool:
    return bool(
        fresh
        and red_team_survived
        and after_fees
        and oos_n >= 30
        and dsr is not None
        and dsr > 0.95
        and pbo is not None
        and pbo < 0.5
    )


def score_path(gross: list[float], alternate: list[float], cost: dict[str, float]) -> dict[str, Any]:
    """Walk-forward on a path this strategy actually produced. Fees are deducted."""
    net = [apply_cost(value, cost["fee_per_side"], cost["slippage_per_side"]) for value in gross]
    alt = [apply_cost(value, cost["fee_per_side"], cost["slippage_per_side"]) for value in alternate]
    split = int(len(net) * 0.6)
    oos = net[split:]
    dsr = deflated_sharpe(oos, 2, [sharpe(oos), sharpe(alt[int(len(alt) * 0.6):] or [0.0])])
    blocks = _blocks(net) 
    blocks_alt = _blocks(alt)
    pbo = pbo_cscv([blocks, blocks_alt]) if blocks and blocks_alt else None
    expectancy = round(sum(oos) / len(oos), 6) if oos else None
    return {
        "closes": len(net),
        "oos_n": len(oos),
        "expectancy_after_fees": expectancy,
        "dsr": dsr,
        "pbo": pbo,
        "after_fees": True,
    }


def _blocks(path: list[float], n_blocks: int = 8) -> list[float] | None:
    if len(path) < n_blocks:
        return None
    size = len(path) // n_blocks
    used = path[-(n_blocks * size):]
    return [sum(used[i * size:(i + 1) * size]) for i in range(n_blocks)]


def _closes(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if '"CLOSE"' not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("event") == "CLOSE":
            rows.append(row)
    return rows


def _scout(root: Path) -> dict[str, Any]:
    path = Path(root) / "reports" / "grok" / "M44" / "arxiv_scout.json"
    present = path.is_file()
    papers = path.read_text(encoding="utf-8").count('"arxiv_id"') if present else 0
    return {
        "sources": ("arXiv q-fin", "SSRN", "GitHub"),
        "arxiv_snapshot_present": present,
        "arxiv_titles_in_snapshot": papers,
        "fetched_this_pass": False,
        "upstream_executed": False,
        "state": "shadow",
        "note": "A scout title is not a strategy until it has the same pre-registered gate.",
    }


def _price(row: dict[str, Any]) -> float | None:
    for key in ("exit_price", "price", "fill_price", "mark_price"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            return float(value)
    return None


def _series_by_desk(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[float]]]:
    """Close prices already on the paper file, grouped by desk and stored regime."""
    grouped: dict[str, dict[str, list[float]]] = {}
    ordered = sorted(rows, key=lambda row: str(row.get("closed_at") or row.get("ts") or ""))
    for row in ordered:
        price = _price(row)
        if price is None:
            continue
        desk = str(row.get("desk") or "UNASSIGNED")
        regime = str(row.get("regime") or "UNLABELED")
        grouped.setdefault(desk, {}).setdefault(regime, []).append(price)
    return grouped


def _row_for(spec: dict[str, Any], desk: str, regime: str, prices: list[float]) -> dict[str, Any]:
    cost = spec["cost"]
    signs = sign_on_closes(spec["id"], prices)
    base = {
        "id": spec["id"],
        "family": spec["family"],
        "citation": spec["citation"],
        "params": spec["params"],
        "regimes": list(spec["regimes"]),
        "cost": cost,
        "desk": desk,
        "regime": regime,
        "state": "shadow",
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
        "applied_to_live": False,
        "fresh": False,
        "family_vote": {
            "family": "strategy_shadow",
            "name": spec["id"],
            "composite_weight": 0.0,
            "counts_toward_entry_gate": False,
            "shadow": True,
        },
    }
    if signs is None:
        base.update(closes=0, expectancy_after_fees=None, dsr=None, pbo=None, reason="MISSING_INPUTS")
        return base
    trips = shadow_round_trips(signs, prices, float(cost["fee_per_side"]), float(cost["slippage_per_side"]))
    if not trips:
        base.update(closes=0, expectancy_after_fees=None, dsr=None, pbo=None, reason="NO_SHADOW_ROUND_TRIP")
        return base
    scored = score_path(trips, trips, cost)
    base.update(
        closes=scored["closes"],
        expectancy_after_fees=scored["expectancy_after_fees"],
        dsr=scored["dsr"],
        pbo=scored["pbo"],
        reason="SHADOW_LOOKBACK",
        wins=sum(1 for value in trips if value > 0),
        losses=sum(1 for value in trips if value <= 0),
    )
    base["pass_stats"] = gate(
        dsr=scored["dsr"], pbo=scored["pbo"], oos_n=scored["oos_n"],
        after_fees=True, fresh=False, red_team_survived=False,
    )
    return base


def export_leaderboard(root: Path) -> dict[str, Any]:
    root = Path(root)
    registry = write_registry(root)
    series = _series_by_desk(_closes(root))
    rows = []
    outcomes: dict[str, tuple[int, int]] = {}
    if not series:
        for spec in SPECS:
            rows.append(_row_for(spec, "UNASSIGNED", "UNLABELED", []))
    else:
        for spec in SPECS:
            wins = losses = 0
            for desk, regimes in series.items():
                for regime, prices in regimes.items():
                    row = _row_for(spec, desk, regime, prices)
                    wins += int(row.get("wins") or 0)
                    losses += int(row.get("losses") or 0)
                    rows.append(row)
            outcomes[spec["id"]] = (wins, losses)
    vote_path = root / "reports" / "grok" / "PAPER" / "strategy_shadow_votes.jsonl"
    vote_path.parent.mkdir(parents=True, exist_ok=True)
    with vote_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "id": row["id"],
                "desk": row["desk"],
                "regime": row.get("regime"),
                "closes": row["closes"],
                "vote": row["family_vote"],
                "applied_to_live": False,
            }, ensure_ascii=False) + "\n")
    doc = {
        "schema": "ahos.strategy_leaderboard.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "registered_at": registry.get("registered_at"),
        "rows": rows,
        "meta_brain": thompson_weights([spec["id"] for spec in SPECS], outcomes=outcomes),
        "wisdom": review_book(_closes(root)),
        "research": _scout(root),
        "live_promoted": 0,
        "pass_stats": False,
        "applied_to_live": False,
    }
    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
