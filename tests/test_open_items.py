from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_open_items_keep_the_soak_and_the_edge_open():
    text = (ROOT / "reports" / "grok" / "PAPER" / "open_items.md").read_text(encoding="utf-8")
    assert "FULL_GAP_REGISTER" in text
    assert "M-GAP-003" in text and "OPEN" in text
    assert "M36" in text and "NOT_MET" in text
    assert "UNPROVEN_EDGE" in text
    assert "PRODUCTION_READY" not in text
    assert "OPERATOR_READY" not in text
