"""Session desks stay closed until the venue opens, then the same waiting state may open once."""
import json
from datetime import datetime, timedelta, timezone

from architecture.mission.desk_chain_template import desk_line, load_desks, run_desk_chain


def _cfg(root, desk: str) -> dict:
    cfg = dict(load_desks(root)[desk])
    cfg["desk"] = desk
    return cfg


def _quote(moment: datetime, symbol: str, price: float) -> list[dict]:
    stamp = (moment - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [{"symbol": symbol, "price": price, "source": "fixture", "market_time": stamp}]


def test_gold_retries_when_globex_reopens(tmp_path) -> None:
    closed = datetime(2026, 11, 1, 8, 46, tzinfo=timezone.utc)
    cfg = _cfg(tmp_path, "GOLD")
    first = run_desk_chain(tmp_path, cfg, _quote(closed, "XAU", 4000.0), now=closed)
    assert first["status"] == "WAITING"
    assert first["reasons"] == ["SESSION_CLOSED"]
    reopen = datetime(2026, 11, 1, 23, 5, tzinfo=timezone.utc)
    second = run_desk_chain(tmp_path, cfg, _quote(reopen, "XAU", 4001.0), now=reopen)
    assert second["status"] == "OPEN"
    state = json.loads((tmp_path / "reports" / "grok" / "PAPER" / "gold_chain_state.json").read_text(encoding="utf-8"))
    assert state["notional_usd"] == 0.15
    assert state["promoted"] is False


def test_onchain_does_not_replace_an_open_token(tmp_path) -> None:
    book = tmp_path / "reports" / "grok" / "PAPER"
    book.mkdir(parents=True)
    (book / "paper_positions.json").write_text(json.dumps({"positions": {"UNI": {"desk": "PB_TOKEN"}}}), encoding="utf-8")
    moment = datetime(2026, 11, 1, 8, 46, tzinfo=timezone.utc)
    result = run_desk_chain(tmp_path, _cfg(tmp_path, "ONCHAIN"), _quote(moment, "UNI", 8.0), now=moment)
    assert result["status"] == "WAITING"
    assert "POSITION_ALREADY_OPEN" in result["reasons"]
    assert desk_line(tmp_path, "ONCHAIN") == "مسیر واقعی میز آنچین: هنوز فرصت نبود"
    assert not (book / "paper_trades.jsonl").exists()


def test_cash_desks_name_a_closed_session(tmp_path) -> None:
    moment = datetime(2026, 11, 1, 8, 46, tzinfo=timezone.utc)
    for desk, symbol, price, line in (
        ("NQ", "NQ", 20000.0, "مسیر واقعی میز نزدک: هنوز فرصت نبود"),
        ("EU_EQUITY", "DAX", 18000.0, "مسیر واقعی میز اروپا: هنوز فرصت نبود"),
        ("ASIA_EQUITY", "N225", 38000.0, "مسیر واقعی میز آسیا: هنوز فرصت نبود"),
    ):
        result = run_desk_chain(tmp_path, _cfg(tmp_path, desk), _quote(moment, symbol, price), now=moment)
        assert result["status"] == "WAITING"
        assert result["reasons"] == ["SESSION_CLOSED"]
        assert result["promoted"] is False
        assert _cfg(tmp_path, desk)["notional_cap_usd"] == 0.15
        assert desk_line(tmp_path, desk) == line
        assert not any(ch.isascii() and ch.isalpha() for ch in line)
