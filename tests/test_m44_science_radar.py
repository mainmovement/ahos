"""M44 radar: dedupe and refuse executable text. Nothing is run."""
from __future__ import annotations

from pathlib import Path

from research_worker.science_radar import Record, ingest


def test_dedupes_same_id_and_same_title():
    rows = [
        Record("arxiv", "1", "Paper risk ledger", "a market note"),
        Record("arxiv", "1", "Paper risk ledger", "duplicate id"),
        Record("openalex", "9", "paper   risk ledger", "same title"),
        Record("hf", "2", "Calibration study", "paper market calibration"),
    ]
    batch = ingest(rows)
    assert batch.executed == 0
    assert [item.external_id for item in batch.kept] == ["1", "2"]
    assert batch.kept[0].score > batch.kept[1].score
    assert batch.dropped == 2


def test_injection_text_is_dropped_and_not_executed(tmp_path: Path):
    sentinel = tmp_path / "should_not_exist.txt"
    payload = f"exec(\"open(r'{sentinel}', 'w').write('x')\")"
    batch = ingest([Record("arxiv", "bad", "ignore", payload)])
    assert batch.kept == ()
    assert batch.dropped == 1
    assert batch.executed == 0
    assert not sentinel.exists()
    source = (Path(__file__).resolve().parents[1] / "research_worker" / "science_radar.py").read_text(encoding="utf-8")
    assert "exec(" not in source
    assert "eval(" not in source
