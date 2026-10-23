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
    assert stages["ahos_applied"]
    uni = stages["university_desk_training"]
    assert len(uni) == 7
    assert all(row.get("syllabus_fa") for row in uni)
    assert snap["paper_only"] is True
    assert snap["real_trading"] is False
