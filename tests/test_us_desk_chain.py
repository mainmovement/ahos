"""A US equity round trip waits for a real later close. A closed session does not trade."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from architecture.mission.us_desk_chain import real_us_line, run_us_desk_chain


def _quote(moment: datetime, price: float = 5000.0) -> list[dict]:
    stamp = (moment - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [{"symbol": "SPX", "price": price, "source": "fixture", "market_time": stamp}]


def test_sunday_session_is_no_setup_and_writes_no_trade(tmp_path: Path) -> None:
    moment = datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc)
    doc = run_us_desk_chain(tmp_path, _quote(moment), [], now=moment)
    assert doc["status"] == "WAITING"
    assert "SESSION_CLOSED" in doc["reasons"]
    assert doc["promoted"] is False
    assert not (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").exists()
    again = run_us_desk_chain(tmp_path, _quote(moment), [], now=moment + timedelta(minutes=10))
    assert again["status"] == "WAITING"
    assert again["reasons"]
    assert real_us_line(tmp_path) == "مسیر واقعی میز آمریکا: هنوز فرصت نبود"
    assert not any(ch.isascii() and ch.isalpha() for ch in real_us_line(tmp_path))


def test_round_trip_close_is_later_and_updates_the_lesson(tmp_path: Path) -> None:
    opened = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
    first = run_us_desk_chain(tmp_path, _quote(opened), [], now=opened)
    assert first["status"] == "OPEN"
    assert first["promoted"] is False
    early = run_us_desk_chain(
        tmp_path, _quote(opened + timedelta(minutes=5), 5010.0), [], now=opened + timedelta(minutes=5)
    )
    assert early["status"] == "OPEN"
    closed_at = opened + timedelta(minutes=12)
    done = run_us_desk_chain(tmp_path, _quote(closed_at, 5010.0), [], now=closed_at)
    assert done["status"] == "CLOSED"
    assert done["promoted"] is False
    lesson = done["lesson"]
    assert lesson["closed_at"] > lesson["opened_at"]
    assert lesson["close_id"]
    assert isinstance(lesson["realized_pnl_usd"], float)
    assert lesson["applied_to_live_weights"] is False
    assert lesson["brier_after"] is not None
    rows = [
        json.loads(line)
        for line in (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["event"] for row in rows] == ["OPEN", "CLOSE"]
    assert rows[1]["closed_at"] > rows[0]["ts"]
    assert real_us_line(tmp_path) == "مسیر واقعی میز آمریکا: یک معامله کامل شد"


def test_an_existing_position_blocks_a_second_entry(tmp_path: Path) -> None:
    moment = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
    folder = tmp_path / "reports" / "grok" / "PAPER"
    folder.mkdir(parents=True)
    (folder / "paper_positions.json").write_text(
        json.dumps({"positions": {"SPX": {"desk": "US_EQUITIES", "notional_usd": 1}}}),
        encoding="utf-8",
    )
    doc = run_us_desk_chain(tmp_path, _quote(moment), [], now=moment)
    assert doc["status"] == "WAITING"
    assert "POSITION_ALREADY_OPEN" in doc["reasons"]
    assert not (folder / "paper_trades.jsonl").exists()
