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
