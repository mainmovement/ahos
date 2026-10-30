import json
from pathlib import Path

from datetime import datetime, timezone

from architecture.markets.multi_signal_block_counter import build_daily_block_counter, build_gate_window_report


def test_counts_missing_families_per_desk(tmp_path: Path):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True)
    rows = [
        {
            "event": "NO_TRADE",
            "reason": "MULTI_SIGNAL_AGREEMENT",
            "ts": "2026-10-30T01:00:00Z",
            "desk": "CRYPTO",
            "independent_votes": {
                "votes": [
                    {"family": "news", "vote": "UNAVAILABLE"},
                    {"family": "macro_central_bank", "vote": "AGREE"},
                    {"family": "whales", "vote": "FLAT"},
                    {"family": "candle_wicks", "vote": "DISAGREE"},
                    {"family": "research", "vote": "UNAVAILABLE"},
                ]
            },
        },
        {"event": "OPEN", "ts": "2026-10-30T01:05:00Z", "desk": "CRYPTO"},
        {
            "event": "NO_TRADE",
            "reason": "MULTI_SIGNAL_AGREEMENT",
            "ts": "2026-10-29T01:00:00Z",
            "desk": "GOLD",
            "independent_votes": {"votes": []},
        },
    ]
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    doc = build_daily_block_counter(tmp_path, "2026-10-30")
    assert doc["blocked_opens"] == 1
    crypto = doc["by_desk"][0]
    assert crypto["desk"] == "CRYPTO"
    assert crypto["missing_family_counts"]["news"] == 1
    assert crypto["missing_family_counts"]["macro_central_bank"] == 0
    assert crypto["missing_family_counts"]["whales"] == 1
    assert crypto["missing_family_counts"]["candle_wicks"] == 1
    assert crypto["missing_family_counts"]["research"] == 1


def test_six_hour_window_is_not_claimed_early(tmp_path: Path):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text(
        json.dumps(
            {
                "event": "NO_TRADE",
                "reason": "MULTI_SIGNAL_AGREEMENT",
                "ts": "2026-10-30T01:00:00Z",
                "desk": "CRYPTO",
                "independent_votes": {"votes": [{"family": "news", "vote": "AGREE"}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime(2026, 10, 30, 2, 0, tzinfo=timezone.utc)
    doc = build_gate_window_report(tmp_path, since="2026-10-30T00:40:16Z", now=now)
    assert doc["window_status"] == "INSUFFICIENT_WINDOW"
    assert doc["elapsed_hours"] < 6
    assert doc["blocks"] == 1
    assert doc["opens"] == 0
    crypto = doc["by_desk"][0]
    assert "macro_central_bank" in crypto["families_never_agreed_in_window"]
    assert "news" not in crypto["families_never_agreed_in_window"]
