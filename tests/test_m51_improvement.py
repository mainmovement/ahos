"""M51 one proposal per cycle, never a merge, never a gate edit."""
from architecture.evolution.improvement import propose


def test_one_clean_proposal_does_not_merge():
    row = propose(
        cycle_id="c1",
        seen_cycles=set(),
        target="docs/prompt_note.md",
        based_on_own_output=False,
    )
    assert row.accepted is True
    assert row.merge is False


def test_second_cycle_self_output_and_gate_are_refused():
    assert propose(
        cycle_id="c1", seen_cycles={"c1"}, target="docs/note.md", based_on_own_output=False
    ).reason == "one proposal per cycle"
    assert propose(
        cycle_id="c2", seen_cycles=set(), target="docs/note.md", based_on_own_output=True
    ).reason == "cannot train on its own output"
    assert propose(
        cycle_id="c3", seen_cycles=set(), target="architecture/risk/daily_cap.py", based_on_own_output=False
    ).reason == "gate policy or cap is closed"
