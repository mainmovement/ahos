"""The nightly note is plain Persian and does not claim a live trade."""
from datetime import datetime, timezone
from pathlib import Path

from architecture.mission.mehrdad_digest import compose_mehrdad_digest


def test_digest_has_no_codes_and_stays_paper(tmp_path: Path) -> None:
    paper = tmp_path / "reports" / "grok" / "PAPER"
    soak = tmp_path / "reports" / "grok" / "M13_SOAK"
    paper.mkdir(parents=True)
    soak.mkdir(parents=True)
    (paper / "paper_trader_status.json").write_text(
        '{"mark_to_market_equity_usd": 99.18, "open_positions": {"BTC-SWAP": {"side": "LONG"}, "XAU": {"side": "SHORT"}}, '
        '"performance": {"max_drawdown_pct": 1.88}}',
        encoding="utf-8",
    )
    (paper / "daily_diagnosis.json").write_text(
        '{"day": "2026-10-30", "primary_cause": "NEWS_TRAP", "applied_to_live": false}',
        encoding="utf-8",
    )
    (paper / "intelligence_metric.json").write_text('{"weeks": []}', encoding="utf-8")
    (soak / "soak_status.json").write_text(
        '{"window_started_utc": "2026-10-29T00:45:31Z"}',
        encoding="utf-8",
    )
    (paper / "paper_trades.jsonl").write_text(
        '{"event":"CLOSE","closed_at":"2026-10-30T12:00:00Z","realized_pnl_usd":0.16}\n',
        encoding="utf-8",
    )
    text = compose_mehrdad_digest(
        tmp_path, now=datetime(2026, 10, 30, 15, 0, tzinfo=timezone.utc)
    )
    assert not any(ch.isascii() and ch.isalpha() for ch in text)
    assert "BTC" not in text
    assert "بیت‌کوین" in text
    assert "طلا" in text
    assert "کلید زنده خاموش" in text
    assert "مشکل:" in text
    assert "۹۹٫۱۸" in text
