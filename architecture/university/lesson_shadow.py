"""Shadow replay of today's two lessons. PAPER_ONLY. Live weights stay put."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import loss_cause

OUT_REL = Path("reports") / "grok" / "PAPER" / "lesson_shadow.json"
PROMOTION_REL = Path("reports") / "grok" / "PAPER" / "lesson_promotion.json"
LIVE_REL = Path("reports") / "grok" / "PAPER" / "lesson_live_weight.json"
RED_REL = Path("reports") / "grok" / "PAPER" / "lesson_red_team.json"
RULES = ("NEWS_TRAP", "BAD_TIMING")
FURTHER_REQUIRED = 30


def _pnl(row: dict[str, Any]) -> float:
    return float(row.get("realized_pnl_usd") or 0)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def measure(closes: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    live = [_pnl(row) for row in ordered]
    kept = [_pnl(row) for row in ordered if loss_cause(row) not in RULES]
    dropped = [row for row in ordered if loss_cause(row) in RULES]
    split = int(len(live) * 0.6)
    live_oos = live[split:]
    kept_oos_rows = [row for row in ordered[split:] if loss_cause(row) not in RULES]
    kept_oos = [_pnl(row) for row in kept_oos_rows]
    live_mean = _mean(live)
    shadow_mean = _mean(kept)
    live_oos_mean = _mean(live_oos)
    shadow_oos_mean = _mean(kept_oos)
    return {
        "schema": "ahos.lesson_shadow.v1",
        "paper_only": True,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rules": list(RULES),
        "rule_text": (
            "Shadow skips a close whose cause is a news trap or a timing loss. "
            "The live book is unchanged."
        ),
        "n_live": len(live),
        "n_shadow": len(kept),
        "n_dropped": len(dropped),
        "dropped_by_cause": {cause: sum(1 for row in dropped if loss_cause(row) == cause) for cause in RULES},
        "expectancy_live_usd": live_mean,
        "expectancy_shadow_usd": shadow_mean,
        "delta_expectancy_usd": None if live_mean is None or shadow_mean is None else round(shadow_mean - live_mean, 6),
        "oos_expectancy_live_usd": live_oos_mean,
        "oos_expectancy_shadow_usd": shadow_oos_mean,
        "oos_delta_expectancy_usd": (
            None if live_oos_mean is None or shadow_oos_mean is None else round(shadow_oos_mean - live_oos_mean, 6)
        ),
        "pnl_live_usd": round(sum(live), 4),
        "pnl_shadow_usd": round(sum(kept), 4),
        "applied_to_live_weights": False,
        "decides": False,
    }


def decide_promotion(
    closes: list[dict[str, Any]],
    *,
    baseline_closed_at: str,
    red_team: str | None,
) -> dict[str, Any]:
    """Promote only after 30 newer closes keep a positive shadow OOS expectancy and the red team survived.

    A missing red-team file is not a pass. This does not raise a signal weight.
    """
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    further = [row for row in ordered if str(row.get("closed_at") or "") > baseline_closed_at]
    split = int(len(further) * 0.6)
    oos = [row for row in further[split:] if loss_cause(row) not in RULES]
    oos_mean = _mean([_pnl(row) for row in oos])
    reasons: list[str] = []
    if len(further) < FURTHER_REQUIRED:
        reasons.append("AWAITING_30_FURTHER_CLOSES")
    if oos_mean is None or oos_mean <= 0:
        reasons.append("OOS_EXPECTANCY_NOT_POSITIVE")
    if red_team != "SURVIVED_RED_TEAM":
        reasons.append("RED_TEAM_ABSENT")
    promote = not reasons
    return {
        "schema": "ahos.lesson_promotion.v1",
        "paper_only": True,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rules": list(RULES),
        "baseline_closed_at": baseline_closed_at,
        "further_closes": len(further),
        "further_required": FURTHER_REQUIRED,
        "oos_further_expectancy_usd": oos_mean,
        "red_team": red_team,
        "promote_to_live_weights": promote,
        "applied_to_live_weights": promote,
        "decision": "PROMOTED" if promote else "KEEP_SHADOW",
        "reasons": ["PROMOTED"] if promote else reasons,
        "news_weight": 0.0 if promote else None,
        "decides": False,
    }


def _read_red_team(root: Path) -> str | None:
    path = Path(root) / RED_REL
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    verdict = doc.get("verdict")
    return verdict if isinstance(verdict, str) else None


def lesson_is_live(root: Path) -> bool:
    path = Path(root) / LIVE_REL
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return doc.get("applied_to_live_weights") is True and doc.get("decision") == "PROMOTED"


def _write_live_weight(root: Path, decision: dict[str, Any]) -> None:
    path = Path(root) / LIVE_REL
    if not decision.get("promote_to_live_weights"):
        if path.is_file():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "ahos.lesson_live_weight.v1",
                "paper_only": True,
                "decision": "PROMOTED",
                "applied_to_live_weights": True,
                "news_weight": 0.0,
                "rules": list(RULES),
                "note": "The news weight stays at zero. No signal weight is raised.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


def export_promotion(root: Path, closes: list[dict[str, Any]], *, red_team: str | None = None) -> dict[str, Any]:
    path = Path(root) / PROMOTION_REL
    baseline = None
    if path.is_file():
        try:
            prior = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior = {}
        if isinstance(prior.get("baseline_closed_at"), str) and prior["baseline_closed_at"]:
            baseline = prior["baseline_closed_at"]
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    if baseline is None:
        baseline = str(ordered[-1].get("closed_at") or "") if ordered else ""
    if red_team is None:
        red_team = _read_red_team(root)
    decision = decide_promotion(closes, baseline_closed_at=baseline, red_team=red_team)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _write_live_weight(root, decision)
    return decision


def export_lesson_shadow(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    doc = measure(closes)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc
