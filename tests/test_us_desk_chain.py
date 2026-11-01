"""The US desk chain records nine steps and one rejection. It does not promote."""
import json
from datetime import datetime, timezone
from pathlib import Path

from architecture.mission.us_desk_chain import run_us_desk_chain, us_desk_line


def test_one_chain_passes_and_one_hypothesis_is_rejected(tmp_path: Path) -> None:
    doc = run_us_desk_chain(
        tmp_path,
        [{"symbol": "SPX", "price": 5000.0, "source": "fixture", "market_time": "2026-11-01T04:00:00Z"}],
        [],
        now=datetime(2026, 11, 1, 5, 0, tzinfo=timezone.utc),
    )
    assert doc["steps"] == 9
    assert doc["promoted"] is False
    lines = (tmp_path / "reports" / "grok" / "PAPER" / "charter_bus.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines]
    main = [row for row in rows if row["experiment_id"] == doc["experiment_id"]]
    assert [row["step"] for row in main] == [
        "data", "analysis", "hypothesis", "experiment", "red_team", "judge", "paper", "outcome", "lesson",
    ]
    for earlier, later in zip(main, main[1:]):
        assert later["parent_message_id"] == earlier["message_id"]
        assert later["sender_id"]
        assert later["evidence_status"] in {"FACT", "INFERENCE", "HYPOTHESIS"}
    assert main[5]["payload"]["verdict"] == "NO_PROMOTION"
    assert main[6]["payload"]["opened_by_this_path"] is False
    rejected = [row for row in rows if row.get("rejected") is True]
    assert rejected and rejected[0]["payload"]["reason"] == "LOOKAHEAD"
    assert not (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").exists()
    assert us_desk_line(tmp_path) == "مسیر کامل میز آمریکا: نمی‌کند"
    folder = tmp_path / "reports" / "grok" / "M13_SOAK"
    folder.mkdir(parents=True)
    (folder / "soak_pid.txt").write_text(str(rows[0]["pid"]) + "\n", encoding="utf-8")
    assert us_desk_line(tmp_path) == "مسیر کامل میز آمریکا: کار می‌کند"
    assert not any(ch.isascii() and ch.isalpha() for ch in us_desk_line(tmp_path))
