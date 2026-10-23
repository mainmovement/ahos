"""Tests for Progressive ACI -> AGI -> SI Brain Core and Whole-AHOS 8-Organ Research/University Evolution."""
from __future__ import annotations

from architecture.cognitive.aci_agi_si_brain import (
    DAY_1_AGI_CLAIMED,
    EVOLUTION_STAGES,
    run_aci_agi_si_evolution_cycle,
)
from architecture.university.whole_ahos_organ_evolution import (
    WHOLE_AHOS_ORGANS_8,
    build_whole_ahos_organ_evolution_snapshot,
)


def test_aci_agi_si_brain_four_loops_and_honest_progression() -> None:
    assert DAY_1_AGI_CLAIMED is False
    assert len(EVOLUTION_STAGES) == 4

    day1 = run_aci_agi_si_evolution_cycle(day_index=1)
    day12 = run_aci_agi_si_evolution_cycle(day_index=12)

    assert day12["paper_only"] is True
    assert day12["day_1_agi_claimed"] is False
    assert day12["compounding_capability_index"] > day1["compounding_capability_index"]
    assert day12["organs_monitored_count"] == 8

    loops = day12["loops"]
    assert loops["self_fault_finding"]["organs_scanned"] == 8
    assert loops["self_debugging"]["all_sandbox_tests_passed"] is True
    assert loops["self_deciding"]["decisions_count"] >= 2
    assert loops["self_updating"]["rollback_triggered"] is False
    assert len(day12["evolution_ledger_chain"]) == 5
    assert day12.get("four_brain_engine") is not None
    assert day12["four_brain_engine"]["persian_briefs_generated"] >= 1


def test_aci_agi_si_self_updating_loop_blocks_protected_safety_files() -> None:
    blocked = run_aci_agi_si_evolution_cycle(candidate_override_path="core/safety_lock.py")
    upd = blocked["loops"]["self_updating"]
    assert upd["rollback_triggered"] is True
    assert upd["rolled_back_count"] == 1
    assert upd["applied_count"] == 0


def test_whole_ahos_8_organs_covered_beyond_trading() -> None:
    assert len(WHOLE_AHOS_ORGANS_8) == 8
    snap = build_whole_ahos_organ_evolution_snapshot()
    assert snap["paper_only"] is True
    assert snap["auto_install"] is False
    assert snap["trading_only"] is False
    assert snap["organs_covered_count"] == 8
    assert set(snap["organ_ids"]) == set(WHOLE_AHOS_ORGANS_8)
    assert snap["average_university_exam_score_pct"] >= 90.0
