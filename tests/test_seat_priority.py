from pathlib import Path

import yaml

from architecture.mission.org_lifecycle import build_org_lifecycle
from architecture.mission.seat_priority import PRIORITY, rank_unfilled
from architecture.university.learning_loop import university_case
from architecture.university.self_diagnosis import diagnose_day

ROOT = Path(__file__).resolve().parents[1]


def test_learning_and_diagnosis_are_filled_and_the_rest_of_the_priority_is_not_a_label():
    doc = build_org_lifecycle(ROOT)
    filled = {row["agent_id"] for row in doc["agents"] if row["seat_filled"]}
    assert doc["registry_agents"] == 43
    assert doc["filled_seats"] < 43
    assert "AG-18" in filled
    assert "AG-19" in filled
    assert "AG-01" not in filled
    assert rank_unfilled(doc) == []
    assert [agent_id for agent_id, _why in PRIORITY] == ["AG-18", "AG-19"]
    reg = yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text(encoding="utf-8"))
    by_id = {agent["agent_id"]: agent for agent in reg["agents"]}
    assert "learning_loop.py" in by_id["AG-18"]["evidence"]
    assert "self_diagnosis.py" in by_id["AG-19"]["evidence"]
    assert "PROMOTE" in by_id["AG-18"]["forbidden_authority"]
    assert "PROMOTE" in by_id["AG-19"]["forbidden_authority"]
    case = university_case({
        "symbol": "BTC", "desk": "CRYPTO", "side": "LONG", "realized_pnl_usd": 1.0,
        "fees_usd": 0.01, "reason": "TAKE_PROFIT", "closed_at": "2026-10-30T00:00:00Z",
        "entry_brain": {"signals": []},
    })
    assert case["outcome"] == "WIN" and case["applied_to_live_weights"] is False
    report = diagnose_day([], "2026-10-30")
    assert report["applied_to_live"] is False
