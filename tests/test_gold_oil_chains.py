"""Gold and oil are config rows on the shared chain. A closed session does not trade."""
from datetime import datetime, timedelta, timezone

from architecture.mission.desk_chain_template import desk_line, load_desks, run_desk_chain


def _cfg(root, desk: str) -> dict:
    cfg = dict(load_desks(root)[desk])
    cfg["desk"] = desk
    return cfg


def _quote(moment: datetime, symbol: str, price: float) -> list[dict]:
    stamp = (moment - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [{"symbol": symbol, "price": price, "source": "fixture", "market_time": stamp}]


def test_sunday_gold_and_oil_stay_no_setup_with_separate_ids(tmp_path) -> None:
    moment = datetime(2026, 11, 1, 8, 30, tzinfo=timezone.utc)
    gold = run_desk_chain(tmp_path, _cfg(tmp_path, "GOLD"), _quote(moment, "XAU", 4000.0), now=moment)
    oil = run_desk_chain(tmp_path, _cfg(tmp_path, "OIL"), _quote(moment, "WTI", 70.0), now=moment)
    assert gold["status"] == "WAITING"
    assert oil["status"] == "WAITING"
    assert "SESSION_CLOSED" in gold["reasons"]
    assert "SESSION_CLOSED" in oil["reasons"]
    assert gold["promoted"] is False and oil["promoted"] is False
    assert gold["experiment_id"] != oil["experiment_id"]
    assert gold["experiment_id"].startswith("exp-gold-")
    assert oil["experiment_id"].startswith("exp-oil-")
    assert _cfg(tmp_path, "GOLD")["notional_cap_usd"] == 0.15
    assert _cfg(tmp_path, "OIL")["notional_cap_usd"] == 0.15
    assert desk_line(tmp_path, "GOLD") == "مسیر واقعی میز طلا: هنوز فرصت نبود"
    assert desk_line(tmp_path, "OIL") == "مسیر واقعی میز نفت: هنوز فرصت نبود"
    assert not any(ch.isascii() and ch.isalpha() for ch in desk_line(tmp_path, "GOLD") + desk_line(tmp_path, "OIL"))
    assert not (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").exists()
