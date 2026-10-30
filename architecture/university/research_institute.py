"""Weekly research ideas stay shadow until the same DSR/PBO gate passes.

arXiv papers already on disk are ranked by publication date. SSRN has no
keyless feed on this host, so that source is ABSENT and no paper is invented.
A predicted score is copied only from a number the record already carries.
A missing number stays null on every desk.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.markets.research_desk_signal import DESK_TO_PIPELINE
from architecture.university.learning_loop import stats_gate

SCOUT_REL = Path("reports") / "grok" / "M44" / "arxiv_scout.json"
WEEKLY_REL = Path("reports") / "grok" / "PAPER" / "research_weekly.json"
DESKS = list(DESK_TO_PIPELINE) + ["LISTED_FUTURES"]
SSRN_STATUS = "ABSENT_NO_FEED"


def _published(paper: dict[str, Any]) -> str:
    return str(paper.get("published") or "")


def top_ideas(scout: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """The newest distinct papers in the scout. No score is added."""
    found: dict[str, dict[str, Any]] = {}
    groups = scout.get("papers_by_hypothesis") if isinstance(scout.get("papers_by_hypothesis"), dict) else {}
    for hypothesis, papers in groups.items():
        if not isinstance(papers, list):
            continue
        for paper in papers:
            if not isinstance(paper, dict):
                continue
            arxiv_id = str(paper.get("arxiv_id") or "")
            if not arxiv_id or arxiv_id in found:
                continue
            found[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": paper.get("title"),
                "published": paper.get("published"),
                "hypothesis": hypothesis,
                "predicted_score": paper.get("predicted_score") if isinstance(paper.get("predicted_score"), (int, float)) else None,
            }
    ranked = sorted(found.values(), key=lambda item: (_published(item), item["arxiv_id"]), reverse=True)
    return ranked[:limit]


def shadow_hypotheses(ideas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One shadow row per idea per desk. The score is the paper's own number or null."""
    rows: list[dict[str, Any]] = []
    for idea in ideas:
        for desk in DESKS:
            rows.append({
                "schema": "ahos.shadow_hypothesis.v1",
                "paper_only": True,
                "arxiv_id": idea.get("arxiv_id"),
                "title": idea.get("title"),
                "hypothesis": idea.get("hypothesis"),
                "desk": desk,
                "predicted_score": idea.get("predicted_score"),
                "status": "SHADOW",
                "reason": "NO_NUMERIC_PREDICTED_SCORE" if idea.get("predicted_score") is None else "AWAITING_COUNTERFACTUAL",
                "applied_to_live_weights": False,
            })
    return rows


def score_counterfactual(hypothesis: dict[str, Any], later_return: float) -> dict[str, Any]:
    score = hypothesis.get("predicted_score")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or float(score) == 0.0:
        return {"status": "UNSCORED", "reason": "NO_NUMERIC_PREDICTED_SCORE", "applied_to_live_weights": False}
    sign = "LONG" if float(score) > 0 else "SHORT"
    up = float(later_return) > 0
    hit = (sign == "LONG" and up) or (sign == "SHORT" and not up)
    return {"status": "SCORED", "hit": hit, "sign": sign, "applied_to_live_weights": False}


def decide_hypothesis(
    hypothesis: dict[str, Any],
    oos_returns: list[float],
    trial_returns: list[list[float]],
    red_team: str | None,
) -> dict[str, Any]:
    """Promote only when stats and the red team both pass. Otherwise kill or keep shadow."""
    if hypothesis.get("predicted_score") is None:
        return {"status": "KEEP_SHADOW", "reason": "NO_NUMERIC_OOS", "gate": "SHADOW", "applied_to_live_weights": False}
    gate = stats_gate(oos_returns, trial_returns)
    if gate["gate"] == "PASS_STATS" and red_team == "SURVIVED_RED_TEAM":
        return {
            "status": "PROMOTE_ELIGIBLE",
            "reason": "PASS_STATS_AND_SURVIVED_RED_TEAM",
            "gate": gate["gate"],
            "dsr": gate["dsr"],
            "pbo": gate["pbo"],
            "applied_to_live_weights": False,
        }
    if gate["dsr"] is not None and gate["pbo"] is not None and gate["gate"] != "PASS_STATS":
        return {
            "status": "KILL",
            "reason": "FAILED_OOS",
            "gate": "SHADOW",
            "dsr": gate["dsr"],
            "pbo": gate["pbo"],
            "applied_to_live_weights": False,
        }
    reason = "RED_TEAM_PENDING" if gate["gate"] == "PASS_STATS" else "DSR_OR_PBO_UNMEASURED"
    return {
        "status": "KEEP_SHADOW",
        "reason": reason,
        "gate": "SHADOW",
        "dsr": gate["dsr"],
        "pbo": gate["pbo"],
        "applied_to_live_weights": False,
    }


def weekly_report(scout: dict[str, Any]) -> dict[str, Any]:
    ideas = top_ideas(scout)
    return {
        "schema": "ahos.research_weekly.v1",
        "paper_only": True,
        "ssrn": SSRN_STATUS,
        "ideas": ideas,
        "hypotheses": shadow_hypotheses(ideas),
        "applied_to_live_weights": False,
    }


def export_weekly(root: Path, scout: dict[str, Any] | None = None) -> dict[str, Any]:
    if scout is None:
        path = Path(root) / SCOUT_REL
        scout = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"papers_by_hypothesis": {}}
    doc = weekly_report(scout)
    out = Path(root) / WEEKLY_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc
