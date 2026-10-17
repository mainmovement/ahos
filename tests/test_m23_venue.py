"""M23 venue admission stays paper-only."""
from architecture.markets.venue import admit


def test_venue_live_and_unknown_are_refused():
    assert admit("UNKNOWN", live=False).allowed is False
    assert admit("ELIGIBLE", live=True).allowed is False
    paper = admit("ELIGIBLE", live=False)
    assert paper.allowed is True
    assert paper.live is False
