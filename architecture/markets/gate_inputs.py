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


def _default_replay_path() -> Path:
    root = get_project_root()
    replay = root / "reports" / "grok" / "M13_REPLAY" / "tier_gate_replay_inputs.json"
    soak = root / "reports" / "grok" / "M13_SOAK" / "tier_gate_replay_inputs.json"
    return replay if replay.is_file() else soak


def load_replay_inputs(path: Path | None = None) -> dict:
    p = path or _default_replay_path()
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return default_replay_inputs()


def _kwargs_from_block(block: dict) -> dict:
    out: dict = {}
    if block.get("declared_cost_model"):
        out["declared_cost_model"] = str(block["declared_cost_model"])
    if "walk_forward_evidence" in block:
        out["walk_forward_evidence"] = bool(block["walk_forward_evidence"])
    if block.get("backtest_max_drawdown_pct") is not None:
        out["backtest_max_drawdown_pct"] = float(block["backtest_max_drawdown_pct"])
    return out


def tier_gate_kwargs(path: Path | None = None, *, market: str = "gold") -> dict:
    data = load_replay_inputs(path)
    key = market.strip().lower()
    if key in data and isinstance(data[key], dict):
        return _kwargs_from_block(data[key])
    return _kwargs_from_block(data)


def load_replay_inputs_for_market(market: str, path: Path | None = None) -> dict:
    """Full replay block for one market (label + provenance)."""
    data = load_replay_inputs(path)
    key = market.strip().lower()
    if key in data and isinstance(data[key], dict):
        block = dict(data[key])
        block.setdefault("label", data.get("label", LABEL))
        block.setdefault("verdict", data.get("verdict", "NO_PROVEN_EDGE"))
        block.setdefault("source", data.get("source", ""))
        return block
    return dict(data)
