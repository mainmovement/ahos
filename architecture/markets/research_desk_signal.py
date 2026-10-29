"""M57 research / strategy_switch overlay as an advisory signal on paper desks (PAPER_ONLY)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.markets import signal_brain as sb

DESK_TO_PIPELINE = {
    "CRYPTO": "CRYPTO_UNIVERSE_DESK",
    "PB_TOKEN": "CRYPTO_UNIVERSE_DESK",
    "GOLD": "GOLD_DESK",
    "OIL": "OIL_DESK",
    "US_EQUITIES": "US_EQUITIES_DESK",
    "EU_EQUITIES": "EU_EQUITIES_DESK",
    "ASIA_EQUITIES": "ASIA_EQUITIES_DESK",
    "FOREX": "FOREX_DESK",
}

# Hypothesis -> pipeline desk tags (subset of science_to_desk_pipeline.DESK_OF_HYP)
_HYP_DESKS: dict[str, list[str]] = {
    "H14": ["CRYPTO_UNIVERSE_DESK"],
    "H15": ["CRYPTO_UNIVERSE_DESK"],
    "H16": ["US_EQUITIES_DESK"],
    "H17": ["OIL_DESK"],
    "H18": list(DESK_TO_PIPELINE.values()),
    "H19": list(DESK_TO_PIPELINE.values()),
    "H20": list(DESK_TO_PIPELINE.values()),
    "H21": ["CRYPTO_UNIVERSE_DESK"],
    "H22": list(DESK_TO_PIPELINE.values()),
}


def _read_switch(root: Path) -> dict[str, Any]:
    path = root / "reports" / "grok" / "PAPER" / "strategy_switch.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"active": {}, "version": 0}


def _hypothesis_from_strategy_id(strategy_id: str) -> str | None:
    for part in str(strategy_id).split("-"):
        if part.startswith("H") and len(part) > 1 and part[1:].isdigit():
            return part
    return None


def _batch_pass_stats_overlay(
    root: Path, pipe: str
) -> tuple[float, float, list[str], list[dict[str, Any]]]:
    """Advisory direction from M28 batch*_research PASS_STATS candidates mapped to this pipeline desk."""
    contrib = 0.0
    weight_sum = 0.0
    keys: list[str] = []
    rows: list[dict[str, Any]] = []
    m28 = root / "reports" / "grok" / "M28"
    if not m28.is_dir():
        return contrib, weight_sum, keys, rows
    for path in sorted(m28.glob("batch*_research.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for cand in doc.get("candidates") or []:
            if not isinstance(cand, dict) or cand.get("gate") != "PASS_STATS":
                continue
            sid = str(cand.get("strategy_id") or "")
            hid = _hypothesis_from_strategy_id(sid)
            if not hid or pipe not in (_HYP_DESKS.get(hid) or []):
                continue
            metric = cand.get("oos_sharpe")
            if metric is None:
                metric = cand.get("deflated_sharpe")
            if metric is None:
                continue
            f = float(metric)
            w = min(1.0, abs(f))
            if w <= 0:
                continue
            weight_sum += w
            contrib += (1.0 if f >= 0 else -1.0) * w
            keys.append(sid)
            rows.append(
                {
                    "strategy_id": sid,
                    "batch_file": path.name,
                    "metric": round(f, 4),
                    "gate": "PASS_STATS",
                    "paper_only": True,
                }
            )
    return contrib, weight_sum, keys, rows


def research_overlay_for_desk(root: Path, desk: str) -> dict[str, Any]:
    """Score in [-1,1] from strategy_switch + batch PASS_STATS research (advisory only; not promotion)."""
    pipe = DESK_TO_PIPELINE.get(desk)
    if not pipe:
        return sb._sig("research_overlay", None, {"desk": desk, "reason": "unknown_desk"}, "strategy_switch", "M57")
    sw = _read_switch(root)
    active = sw.get("active") if isinstance(sw.get("active"), dict) else {}

    contrib = 0.0
    weight_sum = 0.0
    switch_keys: list[str] = []
    for key, w in (active or {}).items():
        if not isinstance(w, (int, float)):
            continue
        raw = str(key)
        hid = raw.split(":", 1)[0] if ":" in raw else raw
        if hid.startswith("H") and pipe in (_HYP_DESKS.get(hid) or []):
            weight_sum += abs(float(w))
            contrib += float(w)
            switch_keys.append(str(key))

    batch_c, batch_w, batch_keys, batch_rows = _batch_pass_stats_overlay(root, pipe)
    contrib += batch_c
    weight_sum += batch_w

    sources: list[str] = []
    if switch_keys:
        sources.append("strategy_switch")
    if batch_rows:
        sources.append("batch_research")

    if weight_sum <= 0:
        score = None
    else:
        score = max(-1.0, min(1.0, contrib / weight_sum))

    return sb._sig(
        "research_overlay",
        score,
        {
            "pipeline_desk": pipe,
            "switch_version": sw.get("version"),
            "active_keys": switch_keys,
            "batch_pass_stats_keys": batch_keys,
            "batch_pass_stats": batch_rows[:8],
            "overlay_sources": sources,
            "paper_only": True,
            "not_promotion": True,
        },
        "research_overlay",
        "M57",
    )


def append_research_signal(root: Path, desk: str, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    overlay = research_overlay_for_desk(root, desk)
    return signals + [overlay]
