"""Versioned, reversible promotion switch: the ONLY path from research to the live paper trader.

reports/grok/PAPER/strategy_switch.json = {"version": n, "active": {signal_name: weight}, "history": [...]}.
promote() refuses unless the candidate passed the stats gate (OOS>=30, DSR>0.95 with all trials, PBO<0.5) in
the batch snapshot AND survived strategy_red_team. rollback(v) restores any earlier version. PAPER_ONLY.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SWITCH_REL = Path("reports") / "grok" / "PAPER" / "strategy_switch.json"
B4_REL = Path("reports") / "grok" / "M28" / "batch4_research.json"
B5_REL = Path("reports") / "grok" / "M28" / "batch5_research.json"
B6_REL = Path("reports") / "grok" / "M28" / "batch6_research.json"
BATCH_RELS = (B4_REL, B5_REL, B6_REL)
RED_REL = Path("reports") / "grok" / "M56" / "strategy_red_team_snapshot.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(root: Path) -> dict[str, Any]:
    try:
        s = json.loads((Path(root) / SWITCH_REL).read_text(encoding="utf-8"))
        if isinstance(s, dict) and "active" in s:
            return s
    except Exception:
        pass
    return {"version": 0, "active": {}, "history": [], "paper_only": True,
            "rule": "promote only with PASS_STATS + red-team survival; every change versioned; rollback restores"}


def _save(root: Path, s: dict[str, Any]) -> None:
    p = Path(root) / SWITCH_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def promote(root: Path, strategy_id: str, signal: str, weight: float, *, actor: str) -> dict[str, Any]:
    cand = None
    for rel in BATCH_RELS:
        try:
            snap = json.loads((Path(root) / rel).read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
        cand = next((c for c in snap.get("candidates") or [] if c["strategy_id"] == strategy_id), None)
        if cand:
            break
    if not cand or cand.get("gate") != "PASS_STATS" or int(cand.get("oos_trades") or 0) < 30:
        raise PermissionError(f"{strategy_id}: stats gate not passed ({(cand or {}).get('gate_detail')})")
    red = json.loads((Path(root) / RED_REL).read_text(encoding="utf-8"))
    row = next((r for r in red.get("reports") or [] if r.get("strategy_id") == strategy_id), None)
    if not row or row.get("verdict") != "SURVIVED_RED_TEAM":
        raise PermissionError(f"{strategy_id}: did not survive strategy_red_team")
    if not 0 < weight <= 0.3:
        raise ValueError("weight must be in (0, 0.3]")
    s = load(root)
    s["history"].append({"version": s["version"], "active": dict(s["active"]), "at": _now()})
    s["active"][signal] = round(float(weight), 4)
    s["version"] += 1
    s["last_change"] = {"at": _now(), "actor": actor, "promoted": strategy_id, "signal": signal, "weight": weight,
                        "evidence": cand.get("gate_detail")}
    _save(root, s)
    return s


def rollback(root: Path, version: int, *, actor: str) -> dict[str, Any]:
    s = load(root)
    old = next((h for h in s["history"] if h["version"] == version), None)
    if old is None:
        raise KeyError(f"no switch version {version}")
    s["history"].append({"version": s["version"], "active": dict(s["active"]), "at": _now()})
    s["active"] = dict(old["active"])
    s["version"] += 1
    s["last_change"] = {"at": _now(), "actor": actor, "rollback_to": version}
    _save(root, s)
    return s


def apply(weights: dict[str, float], root: Path) -> tuple[dict[str, float], int]:
    s = load(root)
    out = dict(weights)
    out.update(s.get("active") or {})
    return out, int(s.get("version", 0))
