"""M15 & M58.3 council advice and Devil's Advocate mandatory dissent gate.
Votes cannot change the tier. Missing devil's advocate dissent halts paper approval (HOLD_FOR_REVIEW).
"""
from __future__ import annotations

from dataclasses import dataclass
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
