"""M20 paper OMS. An order is accepted only through the gateway and the venue gate."""
from __future__ import annotations

from dataclasses import dataclass

from architecture.execution.gateway import PaperOrder, submit_paper
from architecture.markets.venue import admit


@dataclass(frozen=True, slots=True)
class OmsResult:
    state: str
    reason: str
    live: bool


def route(order: PaperOrder, venue_verdict: str) -> OmsResult:
    gated = submit_paper(order, via_gateway=True)
    if not gated.accepted:
        return OmsResult("REJECTED", gated.reason, False)
    venue = admit(venue_verdict, live=order.live)
    if not venue.allowed:
        return OmsResult("REJECTED", venue.reason, False)
    return OmsResult("ACCEPTED_PAPER", "paper order booked", False)
