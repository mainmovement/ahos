"""M38 paper gateway: bypass, live flag, and cap."""
from __future__ import annotations

from pathlib import Path

import pytest

from architecture.execution.gateway import PAPER_NOTIONAL_CAP_USD, PaperOrder, submit_paper


def _order(**kwargs) -> PaperOrder:
    base = dict(market="gold", side="buy", notional_usd=100.0, live=False)
    base.update(kwargs)
    return PaperOrder(**base)


def test_bypass_is_rejected():
    row = submit_paper(_order(), via_gateway=False)
    assert row.accepted is False
    assert row.paper_only is True


def test_live_flag_is_rejected():
    row = submit_paper(_order(live=True), via_gateway=True)
    assert row.accepted is False


def test_cap_edges():
    assert submit_paper(_order(notional_usd=PAPER_NOTIONAL_CAP_USD), via_gateway=True).accepted
    assert not submit_paper(_order(notional_usd=PAPER_NOTIONAL_CAP_USD + 0.01), via_gateway=True).accepted
    assert not submit_paper(_order(notional_usd=0), via_gateway=True).accepted
    assert not submit_paper(_order(notional_usd=-5), via_gateway=True).accepted


def test_side_and_market():
    assert not submit_paper(_order(side="short"), via_gateway=True).accepted
    assert not submit_paper(_order(market="  "), via_gateway=True).accepted


@pytest.mark.parametrize("notional", [0.01, 1, 250, 999.99, 1000])
def test_in_range_paper_orders_pass(notional: float):
    row = submit_paper(_order(notional_usd=notional), via_gateway=True)
    assert row.accepted is True
    assert row.paper_only is True


def test_gateway_source_has_no_model_client():
    text = (Path(__file__).resolve().parents[1] / "architecture" / "execution" / "gateway.py").read_text(encoding="utf-8")
    for banned in ("openai", "anthropic", "gemini", "import requests"):
        assert banned not in text.lower()
