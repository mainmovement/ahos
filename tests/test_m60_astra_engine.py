"""Tests for M60 (M60.1-M60.8) Astra Self-Optimization & Evolution Engine."""
from __future__ import annotations

from architecture.learning.astra_engine import ASTRA_STAGES, run_astra_evolution_cycle


def test_m60_all_eight_stages_pass_in_shadow_paper_mode() -> None:
    assert len(ASTRA_STAGES) == 8
    res = run_astra_evolution_cycle()
    assert res["paper_only"] is True
    assert res["live_promotion"] is False
    assert res["rollback_triggered"] is False
    assert res["overall_status"] == "SHADOW_PAPER_ACTIVE"
    assert res["stages_count"] == 8
    assert res["stages_passed"] == 8


def test_m60_triggers_automatic_rollback_on_safety_lock_or_drift_violation() -> None:
    # 1. Attempt to target a protected safety file -> M60.8 must trigger automatic rollback
    blocked = run_astra_evolution_cycle(candidate_target_path="architecture/markets/risk.py")
    assert blocked["rollback_triggered"] is True
    assert blocked["overall_status"] == "ROLLBACK_ENFORCED"

    # 2. Excessive shadow drift -> M60.8 must trigger automatic rollback
    drifted = run_astra_evolution_cycle(
        telemetry={
            "brier_baseline": 0.168,
            "brier_candidate": 0.155,
            "replay_dsr": 1.7,
            "stress_drawdown_pct": 3.5,
            "shadow_drift_bps": 85.0,
            "max_allowed_drift_bps": 35.0,
        }
    )
    assert drifted["rollback_triggered"] is True
    assert drifted["overall_status"] == "ROLLBACK_ENFORCED"
