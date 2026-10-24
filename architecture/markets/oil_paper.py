"""Oil paper cycle on its own mission id. It never writes the gold mission."""
from __future__ import annotations

from dataclasses import dataclass

from architecture.execution.gateway import PaperOrder
from architecture.markets.margin import assess
from architecture.markets.oil_quote import OilQuote, witness
from architecture.markets.oms import route
from architecture.mission.ledger import MissionLedger

OIL_PAPER_MISSION = "M13-OIL-PAPER"
OIL_NOTIONAL_USD = 100.0
OIL_PAPER_BANKROLL_USD = 100.0


@dataclass(frozen=True, slots=True)
class OilCycle:
    quote: OilQuote
    oms: str
    live: bool


def run_oil_cycle(ledger: MissionLedger, *, left: float | None, right: float | None) -> OilCycle:
    if ledger.latest(OIL_PAPER_MISSION) is None:
        ledger.start(
            OIL_PAPER_MISSION,
            phase="paper_trading",
            task="oil paper quote cycle",
            agent="AG:AG-28",
        )
    latest = ledger.latest(OIL_PAPER_MISSION)
    prev = (latest or {}).get("CHECKPOINT") or {}
    cycle = int(prev.get("cycle", 0)) + 1 if isinstance(prev.get("cycle"), int) else 1
    quote = witness(left, right)
    oms_state = "NO_ENTRY"
    if quote.state == "VERIFIED":
        oms_state = route(
            PaperOrder("oil", "buy", OIL_NOTIONAL_USD, False),
            "ELIGIBLE",
        ).state
        if oms_state != "ACCEPTED_PAPER":
            oms_state = "REJECTED"
    margin = assess(equity_usd=OIL_PAPER_BANKROLL_USD, notional_usd=OIL_NOTIONAL_USD)
    ledger.checkpoint(
        OIL_PAPER_MISSION,
        {
            "market": "oil",
            "cycle": cycle,
            "quote_state": quote.state,
            "price_usd": quote.price_usd,
            "oms": oms_state,
            "margin_event": margin.event,
            "margin_leverage": margin.leverage,
            "bankroll_usd": OIL_PAPER_BANKROLL_USD,
            "equity_usd": OIL_PAPER_BANKROLL_USD,
            "closed_trades": 0,
            "cumulative_realized_pnl_usd": 0.0,
            "paper_only": True,
            "live": False,
            "trades": False,
        },
        LAST_EVIDENCE=f"oil paper {quote.state}",
    )
    return OilCycle(quote, oms_state, False)
