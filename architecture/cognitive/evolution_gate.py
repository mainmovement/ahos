"""Lane-B evolution proposals reuse SelfEvolutionEngine. No second brain.

Cognitive evolution may propose B_ONLY changes. Lane-A or soak-affecting
changes must stop and become a LANE_A_CHANGE_PROPOSAL — they are not
created through this gate.
"""

from __future__ import annotations

from typing import Any

from architecture.evolution.engine import ImprovementProposal, SelfEvolutionEngine

from architecture.cognitive.sandbox import DEFAULT_SANDBOX, assert_sandbox_holds


class LaneAChangeRequired(RuntimeError):
    """Raised when a cognitive evolution request would touch Lane A or soak semantics."""


def propose_lane_b_evolution(
    *,
    diagnosis: str,
    detected_by: str,
    proposed_by: str,
    is_ai: bool,
    candidate_diff_ref: str,
    test_battery: list[str],
    rollback_plan: dict[str, str],
    analysis: dict[str, Any] | None = None,
    target_scope: str = "B_ONLY",
    governance_touching: bool = False,
    engine: SelfEvolutionEngine | None = None,
) -> ImprovementProposal:
    """Create a governed improvement proposal. Never self-approves."""
    assert_sandbox_holds(DEFAULT_SANDBOX)
    if target_scope != "B_ONLY":
        raise LaneAChangeRequired(
            f"Cognitive evolution refuses target_scope={target_scope!r}. "
            "File reports/agi_aci_evolution/LANE_A_CHANGE_PROPOSAL.md and stop. "
            "Do not modify Lane A, soak T0, or production observation semantics "
            "from this package."
        )
    eng = engine or SelfEvolutionEngine()
    return eng.create_proposal(
        detected_by=detected_by,
        diagnosis=diagnosis,
        proposed_by=proposed_by,
        is_ai=is_ai,
        target_scope="B_ONLY",
        governance_touching=governance_touching,
        candidate_diff_ref=candidate_diff_ref,
        test_battery=test_battery,
        rollback_plan=rollback_plan,
        analysis=analysis,
        classification="INTELLIGENCE",
    )
