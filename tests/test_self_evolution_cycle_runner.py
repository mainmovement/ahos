from __future__ import annotations

from architecture.cognitive.self_evolution_cycle_runner import run_self_evolution_cycle_snapshot


def test_four_stage_cycle_honest_agi() -> None:
    snap = run_self_evolution_cycle_snapshot()
    assert snap["day_1_agi_claimed"] is False
    assert snap["paper_only"] is True
    ids = [s["stage_id"] for s in snap["stages"]]
    assert ids == [
        "DISCOVER_BOTTLENECK",
        "SYNTHESIZE_PATCH",
        "QUARANTINE_VERIFY",
        "PROMOTE_OR_ROLLBACK",
    ]
    assert snap["stages"][0]["organs_scanned"] == 8
    assert "persian_cycle_summary_fa" in snap
