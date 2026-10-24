"""M57 science scout -> research -> AHOS -> university desks pipeline."""
from __future__ import annotations

from architecture.university.science_to_desk_pipeline import GLOBAL_SOURCES, run_science_to_desk_pipeline


def test_pipeline_sources_research_university_desks() -> None:
    snap = run_science_to_desk_pipeline()
    assert len(GLOBAL_SOURCES) >= 10
    assert snap["sources_count"] >= 10
    assert snap["desks_trained"] == 7
    stages = snap["stages"]
    assert len(stages["scouts"]) >= 10
    assert stages["research_institute"]
    assert isinstance(stages["ahos_applied"], list)   # empty until a strategy passes the promotion switch
    assert all(s["status"] == "NOT_CONNECTED" or s["status"].startswith("LIVE") for s in stages["scouts"])
    uni = stages["university_desk_training"]
    assert len(uni) == 7
    assert all(row.get("syllabus_fa") for row in uni)
    organs = snap["whole_ahos_organs"]
    assert organs["organs_covered_count"] == 8
    assert organs["trading_only"] is False
    assert len(snap["stages"]["whole_ahos_organ_routing"]) == 8
    assert snap["paper_only"] is True
    assert snap["real_trading"] is False
