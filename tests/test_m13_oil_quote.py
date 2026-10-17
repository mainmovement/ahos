"""M13.1 oil quotes do not trade."""
from pathlib import Path

from architecture.markets.oil_quote import witness


def test_oil_needs_two_agreeing_sources_and_never_trades():
    missing = witness(70.0, None)
    assert missing.state == "UNKNOWN"
    assert missing.trades is False
    clash = witness(70.0, 74.0)
    assert clash.state == "CONFLICT"
    assert clash.price_usd is None
    agreed = witness(70.0, 70.2)
    assert agreed.state == "VERIFIED"
    assert agreed.trades is False
    source = (Path(__file__).resolve().parents[1] / "architecture" / "markets" / "oil_quote.py").read_text(encoding="utf-8")
    assert "submit_paper" not in source
    assert "def order" not in source
