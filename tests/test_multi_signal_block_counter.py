import json
from pathlib import Path

from architecture.markets.multi_signal_block_counter import build_daily_block_counter


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
