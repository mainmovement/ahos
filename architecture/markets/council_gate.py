"""M15 & M58.3 council advice and Devil's Advocate mandatory dissent gate.
Votes cannot change the tier. Missing devil's advocate dissent halts paper approval (HOLD_FOR_REVIEW).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class CouncilAdvice:
    tier: str
    promoted: bool


def advise(*, votes_to_promote: int, votes: int, tier: str) -> CouncilAdvice:
    if votes < 1 or votes_to_promote > votes:
        return CouncilAdvice(tier, False)
    return CouncilAdvice(tier, False)


def evaluate_council_with_dissent(
    *,
    proposal_id: str,
    votes_for: int,
    votes_total: int,
    devils_advocate_dissent: str | None,
    failure_modes: Sequence[str] = (),
    tier: str = "T0",
) -> dict[str, Any]:
    """M58.3: Require a dedicated Devil's Advocate dissent record listing failure modes on every proposed trade."""
    dissent_clean = (devils_advocate_dissent or "").strip()
    modes = [m.strip() for m in failure_modes if m and m.strip()]
    if not dissent_clean or len(modes) == 0:
        return {
            "proposal_id": proposal_id,
            "status": "HOLD_FOR_REVIEW",
            "approved_paper": False,
            "promoted": False,
            "tier": tier,
            "reason": "missing_devils_advocate_dissent",
            "failure_modes": modes,
        }
    quorum_ok = votes_total >= 3 and votes_for > (votes_total // 2)
    return {
        "proposal_id": proposal_id,
        "status": "APPROVED_PAPER" if quorum_ok else "REJECTED_BY_COUNCIL",
        "approved_paper": quorum_ok,
        "promoted": False,
        "tier": tier,
        "devils_advocate_dissent": dissent_clean,
        "failure_modes": modes,
        "reason": "dissent_recorded_paper_only",
    }


import math


def _logit(p: float) -> float:
    p_c = max(1e-4, min(1.0 - 1e-4, float(p)))
    return math.log(p_c / (1.0 - p_c))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def soroush_blind_debate_and_bl(
    *,
    symbol: str,
    bull_prob: float,
    bear_prob: float,
    bull_evidence_refs: Sequence[str],
    bear_evidence_refs: Sequence[str],
    devils_advocate_dissent: str,
    prior_prob: float = 0.50,
    market_prior_return: float = 0.0005,
    prior_var: float = 0.0004,
    view_confidence_omega: float = 0.0002,
    tau: float = 0.05,
) -> dict[str, Any]:
    """M15 debate arithmetic. Swap consistency of a commutative blend is not a calibration, and no Brier is stored unless a held-out scorecard measured it."""
    if not bull_evidence_refs or not bear_evidence_refs or not devils_advocate_dissent.strip():
        return {
            "symbol": symbol,
            "approved_paper": False,
            "status": "HOLD_MISSING_EVIDENCE_OR_DISSENT",
            "swap_consistency": 0.0,
            "paper_only": True,
        }

    # Anonymized blind judge scoring: order 1 (A=Bull, B=Bear) vs order 2 (A=Bear, B=Bull)
    w_bull = min(1.0, 0.5 + 0.1 * len(bull_evidence_refs))
    w_bear = min(1.0, 0.5 + 0.1 * len(bear_evidence_refs))
    lo_prior = _logit(prior_prob)
    # Order 1: Bull first, Bear second (bear_prob is probability of down move -> up prob = 1 - bear_prob)
    lo_1 = lo_prior + 0.5 * (w_bull * (_logit(bull_prob) - lo_prior) + w_bear * (_logit(1.0 - bear_prob) - lo_prior))
    # Order 2 (swapped labels): Bear first, Bull second
    lo_2 = lo_prior + 0.5 * (w_bear * (_logit(1.0 - bear_prob) - lo_prior) + w_bull * (_logit(bull_prob) - lo_prior))
    p_1 = _sigmoid(lo_1)
    p_2 = _sigmoid(lo_2)
    swap_diff = abs(p_1 - p_2)
    swap_consistency = round(max(0.0, 1.0 - swap_diff), 4)
    p_posterior = round(0.5 * (p_1 + p_2), 4)

    # Black-Litterman 1D scalar view update:
    # posterior_precision = 1/(tau * prior_var) + 1/omega
    tau_sigma = max(1e-8, tau * prior_var)
    omega = max(1e-8, view_confidence_omega)
    view_q = (p_posterior - 0.5) * 0.02  # implied expected return view from log-odds posterior
    bl_post_var = 1.0 / ((1.0 / tau_sigma) + (1.0 / omega))
    bl_post_ret = bl_post_var * ((market_prior_return / tau_sigma) + (view_q / omega))

    # Seat Brier and ECE are not measured here. Constants are not a calibration.
    return {
        "symbol": symbol,
        "approved_paper": False,
        "status": "HOLD_CALIBRATION_NOT_MEASURED",
        "posterior_prob_up": p_posterior,
        "log_odds": round(_logit(p_posterior), 4),
        "swap_consistency": swap_consistency,
        "swap_gate_passed": swap_consistency >= 0.95,
        "swap_note": "The two orders add the same two terms, so this swap check cannot fail. It is not evidence of an independent judge.",
        "bl_prior_return": round(market_prior_return, 6),
        "bl_view_return": round(view_q, 6),
        "bl_posterior_return": round(bl_post_ret, 6),
        "bl_prior_status": "ASSUMED_SCALAR_PRIOR_NOT_A_FORECAST",
        "brier_judge": None,
        "brier_bull": None,
        "brier_bear": None,
        "brier_best_analyst": None,
        "ece_judge": None,
        "calibration_status": "NOT_MEASURED_NO_HELD_OUT_SCORECARD",
        "devils_advocate_dissent": devils_advocate_dissent.strip(),
        "bull_refs_count": len(bull_evidence_refs),
        "bear_refs_count": len(bear_evidence_refs),
        "paper_only": True,
    }


COUNCIL_SYMBOLS = (
    "BTC", "ETH", "SOL", "UNI", "XAU", "WTI", "BRENT", "SPX", "QQQ", "DAX", "N225", "HSI", "EURUSD", "USDJPY",
)
_DESK = {
    "BTC": "CRYPTO", "ETH": "CRYPTO", "SOL": "CRYPTO", "UNI": "PB_TOKEN",
    "XAU": "GOLD", "WTI": "OIL", "BRENT": "OIL", "SPX": "US_EQUITIES", "QQQ": "US_EQUITIES",
    "DAX": "EU_EQUITIES", "N225": "ASIA_EQUITIES", "HSI": "ASIA_EQUITIES", "EURUSD": "FOREX", "USDJPY": "FOREX",
}
_TOPIC = {
    "CRYPTO": ("crypto", "bitcoin", "btc"),
    "PB_TOKEN": ("token", "defi", "uni"),
    "GOLD": ("gold", "xau"),
    "OIL": ("oil", "wti", "brent"),
    "US_EQUITIES": ("equity", "stock", "spx"),
    "EU_EQUITIES": ("dax", "europe"),
    "ASIA_EQUITIES": ("nikkei", "hang", "asia"),
    "FOREX": ("fx", "euro", "yen"),
}
SKILL_MIN_N = 30


def council_row_problems(row: dict[str, Any]) -> list[str]:
    """A judge Brier that was not measured on the judge's own forecasts is a failure."""
    problems = []
    if row.get("paper_only") is False:
        problems.append("paper_only is false")
    if row.get("approved_paper") is True and row.get("calibration_status") != "MEASURED":
        problems.append("approved without a measured calibration")
    if row.get("brier_judge") is not None or row.get("ece_judge") is not None:
        problems.append("judge score is present and this builder has no judge forecast history")
    if row.get("swap_gate_passed") is True:
        problems.append("label swap was marked as a passed test")
    if row.get("bl_prior_status") not in ("ASSUMED_SCALAR_PRIOR_NOT_A_FORECAST", "ESTIMATED_FROM_RETURNS"):
        problems.append("prior status is unlabeled")
    seats = row.get("seats")
    if not isinstance(seats, list) or len(seats) != 5:
        problems.append("row does not have five seats")
    return problems


def _read_json(root: Path, rel: str) -> dict[str, Any] | None:
    import json
    path = Path(root) / rel
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _events(root: Path) -> list[dict[str, Any]]:
    import json
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _top(scores: dict[str, Any], sign: int) -> list[dict[str, Any]]:
    picked = []
    for name, value in scores.items():
        if not isinstance(value, (int, float)):
            continue
        if sign > 0 and value > 0:
            picked.append((float(value), name))
        if sign < 0 and value < 0:
            picked.append((float(value), name))
    picked.sort(key=lambda item: abs(item[0]), reverse=True)
    return [{"signal": name, "score": round(value, 4), "unit": "composite_score"} for value, name in picked[:3]]


def _skill_for(table: dict[str, dict[str, Any]], names: list[str]) -> dict[str, Any]:
    usable = []
    for name in names:
        row = table.get(name)
        if not row or not isinstance(row.get("n_eff"), int) or row["n_eff"] < SKILL_MIN_N:
            continue
        if not isinstance(row.get("brier"), (int, float)):
            continue
        usable.append(row)
    if not usable:
        return {"brier": None, "n_eff": None, "status": "NO_SIGNAL_WITH_N_EFF_GE_30"}
    best = min(usable, key=lambda row: float(row["brier"]))
    return {"brier": best["brier"], "n_eff": best["n_eff"], "brier_skill": best.get("brier_skill"),
            "status": "SCORECARD_SIGNAL_BRIER"}


def build_council_debate_matrix(root: Path) -> dict[str, Any]:
    """Five seats per paper instrument. The judge has no forecast history, so the judge Brier stays null."""
    import json
    from datetime import datetime, timezone
    from architecture.markets.crisis import HISTORICAL_CRISES_10

    root = Path(root)
    events = _events(root)
    last: dict[str, dict[str, Any]] = {}
    for row in events:
        sym = str(row.get("symbol") or "")
        if sym in COUNCIL_SYMBOLS and isinstance(row.get("signal_scores"), dict):
            last[sym] = row
    card = _read_json(root, "reports/grok/M28/shadow_forward_scorecard.json") or {}
    skills = {}
    for sig in card.get("signals") or []:
        if isinstance(sig, dict) and sig.get("signal"):
            skills[str(sig["signal"])] = sig
    cal = _read_json(root, "reports/grok/M19/macro_calendar.json") or {}
    banks = cal.get("status") if isinstance(cal.get("status"), dict) else {}
    banks_ok = sorted(k for k, v in banks.items() if str(v).startswith("OK"))
    news = _read_json(root, "reports/grok/M18/newsroom_snapshot.json") or {}
    clusters = news.get("rssClusters") if isinstance(news.get("rssClusters"), list) else []
    corroborated = []
    for cluster in clusters:
        if not isinstance(cluster, dict) or cluster.get("state") != "CORROBORATED":
            continue
        domains = cluster.get("independent_domains") or []
        if isinstance(domains, list) and len(domains) >= 2:
            corroborated.append(str(cluster.get("topic") or "").lower())
    rows = []
    for sym in COUNCIL_SYMBOLS:
        event = last.get(sym) or {}
        scores = event.get("signal_scores") if isinstance(event.get("signal_scores"), dict) else {}
        bull = _top(scores, 1)
        bear = _top(scores, -1)
        bull_skill = _skill_for(skills, [d["signal"] for d in bull])
        bear_skill = _skill_for(skills, [d["signal"] for d in bear])
        matches = [c for c in HISTORICAL_CRISES_10 if c.get("asset") == sym]
        analogue = max(matches, key=lambda c: float(c["peak_to_trough_drop"])) if matches else None
        desk = _DESK[sym]
        topics = _TOPIC[desk]
        desk_clusters = [t for t in corroborated if any(k in t for k in topics)]
        seats = [
            {"seat": 1, "role": "bull", "drivers": bull, "brier": bull_skill["brier"], "n_eff": bull_skill["n_eff"],
             "brier_status": bull_skill["status"]},
            {"seat": 2, "role": "bear", "drivers": bear, "brier": bear_skill["brier"], "n_eff": bear_skill["n_eff"],
             "brier_status": bear_skill["status"]},
            {"seat": 3, "role": "devils_advocate",
             "analogue": None if analogue is None else {
                 "id": analogue["id"], "drop": analogue["peak_to_trough_drop"], "match": "asset_label",
             },
             "distance_kind": "asset_label_match" if analogue else "no_labelled_crisis",
             "tail_veto": bool(analogue and float(analogue["peak_to_trough_drop"]) >= 0.30),
             "brier": None},
            {"seat": 4, "role": "macro_osint", "calendar_ok": banks_ok, "corroborated_topics": desk_clusters[:3],
             "shock_score": None, "shock_status": "NO_ESTIMATED_CAUSAL_COEFFICIENT", "brier": None},
            {"seat": 5, "role": "judge", "brier": None, "ece": None,
             "status": "NOT_MEASURED_NO_JUDGE_FORECAST_HISTORY"},
        ]
        rows.append({
            "symbol": sym,
            "desk": desk,
            "paper_only": True,
            "approved_paper": False,
            "source_event": event.get("event"),
            "source_ts": event.get("ts"),
            "seats": seats,
            "brier_judge": None,
            "ece_judge": None,
            "brier_inequality": "NOT_TESTABLE_JUDGE_UNMEASURED",
            "calibration_status": "NOT_MEASURED_NO_HELD_OUT_SCORECARD",
            "swap_gate_passed": False,
            "swap_note": "Skill weights stay on the evidence. Swapping seat labels does not move the blend, so the swap cannot fail.",
            "bl_prior_status": "ASSUMED_SCALAR_PRIOR_NOT_A_FORECAST",
            "bl_posterior_return": None,
            "bl_posterior_variance": None,
        })
    snap = {
        "schema": "ahos.m15.council_debate_matrix.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "symbols": list(COUNCIL_SYMBOLS),
        "omitted": [{"symbol": "LINK", "reason": "not in the paper instrument map"}],
        "skill_min_n_eff": SKILL_MIN_N,
        "judge_brier": None,
        "ece_judge": None,
        "rows": rows,
    }
    path = root / "reports" / "grok" / "M15" / "council_debate_matrix.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
