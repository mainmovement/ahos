"""Crypto uses the same chain template. The pause stays, and the ticket stays at the size cap."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from architecture.mission.desk_chain_template import desk_line, load_desks, run_desk_chain


def _cfg(root: Path) -> dict:
    cfg = dict(load_desks(root)["CRYPTO"])
    cfg["desk"] = "CRYPTO"
    return cfg


def _quote(moment: datetime, symbol: str = "BTC", price: float = 60000.0) -> list[dict]:
    stamp = (moment - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [{"symbol": symbol, "price": price, "source": "fixture", "market_time": stamp}]


def test_a_stale_crypto_quote_does_not_trade(tmp_path: Path) -> None:
    moment = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)
    old = [{"symbol": "BTC", "price": 60000.0, "source": "fixture", "market_time": "2026-11-01T06:00:00Z"}]
    doc = run_desk_chain(tmp_path, _cfg(tmp_path), old, now=moment)
    assert doc["status"] == "WAITING"
    assert "QUOTE_STALE" in doc["reasons"]
    assert doc["promoted"] is False
    assert not (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").exists()
    assert desk_line(tmp_path, "CRYPTO") == "مسیر واقعی میز رمزارز: هنوز فرصت نبود"
    assert not any(ch.isascii() and ch.isalpha() for ch in desk_line(tmp_path, "CRYPTO"))


def test_one_capped_ticket_closes_later_and_writes_the_lesson(tmp_path: Path) -> None:
    moment = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)
    first = run_desk_chain(tmp_path, _cfg(tmp_path), _quote(moment), now=moment)
    assert first["status"] == "OPEN"
    assert first["promoted"] is False
    early = run_desk_chain(tmp_path, _cfg(tmp_path), _quote(moment + timedelta(minutes=5), price=60100.0), now=moment + timedelta(minutes=5))
    assert early["reasons"] == ["WAITING_FOR_EXIT"]
    done = run_desk_chain(
        tmp_path, _cfg(tmp_path), _quote(moment + timedelta(minutes=12), price=60100.0), now=moment + timedelta(minutes=12)
    )
    assert done["status"] == "CLOSED"
    assert done["promoted"] is False
    lesson = done["lesson"]
    assert lesson["closed_at"] > lesson["opened_at"]
    assert lesson["applied_to_live_weights"] is False
    assert lesson["brier_after"] is not None
    rows = [json.loads(line) for line in (tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["notional_usd"] == 0.15
    assert rows[0]["desk_pause_respected"] is True
    assert rows[1]["event"] == "CLOSE"
    assert rows[1]["closed_at"] > rows[0]["ts"]
    assert isinstance(rows[1]["realized_pnl_usd"], float)
    assert desk_line(tmp_path, "CRYPTO") == "مسیر واقعی میز رمزارز: یک معامله کامل شد"


def test_an_open_symbol_is_skipped_for_a_flat_one(tmp_path: Path) -> None:
    moment = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)
    folder = tmp_path / "reports" / "grok" / "PAPER"
    folder.mkdir(parents=True)
    (folder / "paper_positions.json").write_text(
        json.dumps({"positions": {"BTC": {"desk": "CRYPTO", "notional_usd": 2}}}),
        encoding="utf-8",
    )
    stamp = (moment - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    quotes = [
        {"symbol": "BTC", "price": 60000.0, "source": "fixture", "market_time": stamp},
        {"symbol": "ETH", "price": 3000.0, "source": "fixture", "market_time": stamp},
    ]
    doc = run_desk_chain(tmp_path, _cfg(tmp_path), quotes, now=moment)
    assert doc["status"] == "OPEN"
    rows = [json.loads(line) for line in (folder / "paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["symbol"] == "ETH"
    book = json.loads((folder / "paper_positions.json").read_text(encoding="utf-8"))
    assert "BTC" in book["positions"]
    assert book["positions"]["ETH"]["notional_usd"] == 0.15
