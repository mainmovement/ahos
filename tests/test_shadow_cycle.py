"""The shadow pass logs a cycle and does not promote."""
from datetime import datetime, timezone
from pathlib import Path

from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, VOTE_SCORE_FLOOR
from architecture.markets.shadow_cycle import running_counts_fa, shadow_tick


def test_a_manual_tick_is_not_the_running_soak(tmp_path: Path) -> None:
    origin = Path(__file__).resolve().parents[1] / "docs" / "prereg" / "MEGA12.yaml"
    dest = tmp_path / "docs" / "prereg"
    dest.mkdir(parents=True)
    (dest / "MEGA12.yaml").write_bytes(origin.read_bytes())
    row = shadow_tick(
        tmp_path,
        cycle_id=7,
        pid=999,
        source="manual",
        inputs={"closes": [float(i) for i in range(1, 40)], "reasons": {}},
        now=datetime(2026, 10, 30, 22, 0, tzinfo=timezone.utc),
    )
    assert row["promoted"] is False
    assert row["applied_to_live"] is False
    assert row["strategies_signaled"] + row["strategies_no_source"] == 26
    assert row["floors"]["min_agreeing_families"] == MIN_AGREEING_FAMILIES == 2
    assert row["floors"]["vote_score_floor"] == VOTE_SCORE_FLOOR == 0.05
    text = running_counts_fa(tmp_path, now=datetime(2026, 10, 30, 22, 30, tzinfo=timezone.utc))
    assert "سایهٔ زنده ۰" in text
    assert not any(ch.isascii() and ch.isalpha() for ch in text)
