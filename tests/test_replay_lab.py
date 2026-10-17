"""Replay lab refuses to call a short sample an edge."""
from architecture.markets.replay_lab import replay


def test_short_replay_has_no_proven_edge():
    report = replay([70, 71, 69, 72])
    assert report.proven_edge is False
    assert report.verdict == "NO_PROVEN_EDGE"
    long = replay([float(i) for i in range(1, 40)])
    assert long.marks >= 30
    assert long.proven_edge is False
    assert long.verdict == "SAMPLE_ONLY"
