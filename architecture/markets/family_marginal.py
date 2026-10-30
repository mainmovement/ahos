"""Walk-forward marginal contribution of each signal family. Shadow only.

The split is pre-registered: the last 40 percent of closes is the score
window. Nothing here changes a live weight. A zero-weight family that never
appears in a contribution list is WEIGHT_ZERO, not a measured edge.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_account import LEDGER_REL

REGISTRY_REL = Path("reports") / "grok" / "PAPER" / "family_marginal_registry.json"
OUT_REL = Path("reports") / "grok" / "PAPER" / "family_marginal.json"

FAMILIES = {
    "mtf_trend": "mtf_trend",
    "news": "news",
    "macro": "macro",
    "whales": "large_trades",
    "wicks": "candles",
    "breadth": "crypto_breadth",
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_REL
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    doc = {
        "schema": "ahos.family_marginal_registry.v1",
        "paper_only": True,
        "registered_at": _utc(),
        "families": FAMILIES,
        "oos_fraction": 0.4,
        "applied_to_live_weights": False,
        "promotable": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def _closes(root: Path) -> list[dict[str, Any]]:
    path = root / LEDGER_REL
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
            rows.append(row)
    return rows


def _contrib(row: dict[str, Any]) -> dict[str, float]:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    out: dict[str, float] = {}
    for item in brain.get("contributions") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("signal")
        value = item.get("contribution")
        if isinstance(name, str) and isinstance(value, (int, float)) and not isinstance(value, bool):
            out[name] = float(value)
    return out


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def measure(closes: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = [row for row in closes if _contrib(row)]
    dominant = 0
    for row in ranked:
        contrib = _contrib(row)
        if contrib and max(contrib, key=lambda name: abs(contrib[name])) == "mtf_trend":
            dominant += 1
    oos = closes[int(len(closes) * 0.6):]
    families = []
    for label, signal in FAMILIES.items():
        present = []
        absent = []
        for row in oos:
            contrib = _contrib(row)
            pnl = float(row["realized_pnl_usd"])
            if signal in contrib and contrib[signal] != 0:
                present.append(pnl)
            else:
                absent.append(pnl)
        base = _mean([float(row["realized_pnl_usd"]) for row in oos])
        got = _mean(present)
        families.append({
            "family": label,
            "signal": signal,
            "oos_closes": len(oos),
            "oos_with_nonzero_contribution": len(present),
            "oos_expectancy_usd": base,
            "with_family_expectancy_usd": got,
            "marginal_usd": None if got is None or base is None else round(got - base, 6),
            "reason": None if present else "WEIGHT_ZERO_OR_ABSENT",
        })
    return {
        "closes": len(closes),
        "closes_with_contributions": len(ranked),
        "mtf_trend_dominant": dominant,
        "mtf_trend_dominant_share": None if not ranked else round(dominant / len(ranked), 4),
        "families": families,
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
        "applied_to_live_weights": False,
        "reasons": ["LOOKBACK_NOT_A_FRESH_SAMPLE", "RED_TEAM_ABSENT"],
    }


def export_measure(root: Path) -> dict[str, Any]:
    registry = write_registry(root)
    doc = {
        "schema": "ahos.family_marginal.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "registered_at": registry.get("registered_at"),
        **measure(_closes(root)),
    }
    (root / OUT_REL).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
