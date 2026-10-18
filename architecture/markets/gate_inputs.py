"""Tier-gate supplements from offline replay. Labelled REPLAY_NOT_LIVE."""
from __future__ import annotations

import json
from pathlib import Path

from config.paths import get_project_root

LABEL = "REPLAY_NOT_LIVE"


def default_replay_inputs() -> dict:
    return {
        "label": LABEL,
        "declared_cost_model": (
            f"{LABEL}: gold 10 bps/side round-trip 20 bps (GC=F replay protocol)"
        ),
        "walk_forward_evidence": True,
        "backtest_max_drawdown_pct": 25.0,
        "verdict": "NO_PROVEN_EDGE",
        "source": "G:/robat/ahos_replay/results.md",
    }


def load_replay_inputs(path: Path | None = None) -> dict:
    p = path or (get_project_root() / "reports" / "grok" / "M13_SOAK" / "tier_gate_replay_inputs.json")
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return default_replay_inputs()


def tier_gate_kwargs(path: Path | None = None) -> dict:
    data = load_replay_inputs(path)
    out = {}
    if data.get("declared_cost_model"):
        out["declared_cost_model"] = str(data["declared_cost_model"])
    if "walk_forward_evidence" in data:
        out["walk_forward_evidence"] = bool(data["walk_forward_evidence"])
    if data.get("backtest_max_drawdown_pct") is not None:
        out["backtest_max_drawdown_pct"] = float(data["backtest_max_drawdown_pct"])
    return out
