"""The nightly science job stays out of the trader and skips a low-memory install."""
import json
from pathlib import Path

from architecture.research.nightly_science import (
    build_report,
    current_us,
    install_plan,
    peak_ram_mb,
    science_line,
    statsmodels_job,
    us_closes,
)


def test_low_memory_skips_and_heavy_libraries_are_refused() -> None:
    scipy = install_plan("scipy", free_mb=600)
    stats = install_plan("statsmodels", free_mb=600)
    assert scipy["action"] == "SKIPPED"
    assert stats["action"] == "SKIPPED"
    assert install_plan("torch", free_mb=8000)["action"] == "REFUSED"
    assert install_plan("tensorflow", free_mb=8000)["action"] == "REFUSED"


def test_five_us_closes_do_not_invent_a_sharpe(tmp_path: Path) -> None:
    rows = [
        {"desk": "US_EQUITIES", "realized_pnl_usd": 0.1, "entry_brain": {"composite": 0.3}},
        {"desk": "US_EQUITIES", "realized_pnl_usd": -0.2, "entry_brain": {"composite": 0.3}},
        {"desk": "US_EQUITIES", "realized_pnl_usd": 0.05, "entry_brain": {"composite": 0.3}},
        {"desk": "US_EQUITIES", "realized_pnl_usd": 0.02, "entry_brain": {"composite": 0.3}},
        {"desk": "US_EQUITIES", "realized_pnl_usd": -0.01, "entry_brain": {"composite": 0.3}},
    ]
    folder = tmp_path / "reports" / "grok" / "PAPER"
    folder.mkdir(parents=True)
    (folder / "paper_trades.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    loaded = us_closes(tmp_path)
    current = current_us(loaded)
    assert current["n"] == 5
    assert current["deflated_sharpe"] is None
    assert current["pbo"] is None
    assert current["brier"] is not None
    assert current["promoted"] is False
    report = build_report(tmp_path, [], [])
    assert report["judge"] == "NO_PROMOTION"
    assert report["libs_used"] is False
    assert report["new_us"]["deflated_sharpe"] is None
    assert science_line(tmp_path) == "کتابخانهٔ سبک به خاطر کمبود حافظه نصب نشد و عدد تازه نوشته نشد"
    assert not any(ch.isascii() and ch.isalpha() for ch in science_line(tmp_path))


def test_small_sample_uses_statsmodels_without_a_pass() -> None:
    rows = [
        {"realized_pnl_usd": 0.1, "entry_brain": {"composite": 0.3}},
        {"realized_pnl_usd": -0.2, "entry_brain": {"composite": 0.3}},
        {"realized_pnl_usd": 0.05, "entry_brain": {"composite": 0.3}},
        {"realized_pnl_usd": 0.02, "entry_brain": {"composite": 0.3}},
        {"realized_pnl_usd": -0.01, "entry_brain": {"composite": 0.3}},
    ]
    doc = statsmodels_job(rows)
    assert doc["status"] == "COMPUTED"
    assert doc["reason"] == "INSUFFICIENT_HOLDOUT"
    assert doc["brier"] == 0.24
    assert doc["promoted"] is False
    assert peak_ram_mb() is not None and peak_ram_mb() > 0


def test_trader_and_soak_do_not_import_the_job() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in (
        "architecture/markets/paper_trader.py",
        "architecture/markets/shadow_cycle.py",
        "scripts/m13_gold_soak.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "nightly_science" not in text
        assert "import scipy" not in text
        assert "import statsmodels" not in text
