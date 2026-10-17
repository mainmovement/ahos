"""M38 paper execution gateway.

Deterministic. No model client. A live flag or a bypass is rejected.
"""
from __future__ import annotations

from dataclasses import dataclass

PAPER_NOTIONAL_CAP_USD = 1_000.0


@dataclass(frozen=True, slots=True)
class PaperOrder:
    market: str
    side: str
    notional_usd: float
    live: bool = False


@dataclass(frozen=True, slots=True)
class GatewayResult:
    accepted: bool
    reason: str
    paper_only: bool


def submit_paper(order: PaperOrder, *, via_gateway: bool) -> GatewayResult:
    if not via_gateway:
        return GatewayResult(False, "order outside the gateway", True)
    if order.live:
        return GatewayResult(False, "live orders are refused", True)
    if order.side not in {"buy", "sell"}:
        return GatewayResult(False, "side must be buy or sell", True)
    if not order.market.strip():
        return GatewayResult(False, "market is empty", True)
    if order.notional_usd <= 0 or order.notional_usd > PAPER_NOTIONAL_CAP_USD:
        return GatewayResult(False, "notional outside the paper cap", True)
    return GatewayResult(True, "paper order accepted", True)
