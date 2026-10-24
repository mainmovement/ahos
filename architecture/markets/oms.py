"""M20 paper OMS & Sandbox Broker Adapters (CCXT & IBKR paper-only).
An order is accepted only through the gateway and the venue gate. Live flags or withdraw scopes are refused.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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


@dataclass(frozen=True, slots=True)
class AdapterOrderReceipt:
    adapter: str
    venue_id: str
    symbol: str
    side: str
    notional_usd: float
    oms_state: str
    reason: str
    sandbox: bool
    paper_only: bool
    live: bool


class BrokerAdapter(Protocol):
    adapter_name: str
    sandbox: bool

    def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        notional_usd: float,
        venue_verdict: str = "ELIGIBLE",
        live: bool = False,
    ) -> AdapterOrderReceipt: ...


class CCXTPaperAdapter:
    """M20 CCXT sandbox/paper adapter. Strictly forbids mainnet live orders or withdrawal permissions."""

    adapter_name = "ccxt_paper_sandbox"

    def __init__(self, exchange_id: str = "okx_paper", *, sandbox: bool = True, allow_withdraw: bool = False) -> None:
        self.exchange_id = exchange_id
        self.sandbox = sandbox
        self.allow_withdraw = allow_withdraw

    def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        notional_usd: float,
        venue_verdict: str = "ELIGIBLE",
        live: bool = False,
    ) -> AdapterOrderReceipt:
        if live or not self.sandbox or self.allow_withdraw:
            return AdapterOrderReceipt(
                adapter=self.adapter_name,
                venue_id=self.exchange_id,
                symbol=symbol,
                side=side,
                notional_usd=notional_usd,
                oms_state="REJECTED_LIVE_FORBIDDEN",
                reason="CCXTPaperAdapter refuses live=True, sandbox=False, or allow_withdraw=True",
                sandbox=self.sandbox,
                paper_only=True,
                live=False,
            )
        oms = route(PaperOrder("crypto", side.lower(), float(notional_usd), False), venue_verdict)
        return AdapterOrderReceipt(
            adapter=self.adapter_name,
            venue_id=self.exchange_id,
            symbol=symbol,
            side=side,
            notional_usd=float(notional_usd),
            oms_state=oms.state,
            reason=oms.reason,
            sandbox=True,
            paper_only=True,
            live=False,
        )


class IBKRPaperAdapter:
    """M20 Interactive Brokers (IBKR) paper account adapter (DU-prefix paper account only)."""

    adapter_name = "ibkr_paper_account"

    def __init__(self, account_id: str = "DU000000_PAPER", *, sandbox: bool = True) -> None:
        self.account_id = account_id
        self.sandbox = sandbox

    def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        notional_usd: float,
        venue_verdict: str = "ELIGIBLE",
        live: bool = False,
    ) -> AdapterOrderReceipt:
        if live or not self.sandbox or not self.account_id.upper().startswith("DU"):
            return AdapterOrderReceipt(
                adapter=self.adapter_name,
                venue_id=self.account_id,
                symbol=symbol,
                side=side,
                notional_usd=notional_usd,
                oms_state="REJECTED_LIVE_FORBIDDEN",
                reason="IBKRPaperAdapter requires DU* paper account and sandbox=True, live=False",
                sandbox=self.sandbox,
                paper_only=True,
                live=False,
            )
        oms = route(PaperOrder("equities_fx", side.lower(), float(notional_usd), False), venue_verdict)
        return AdapterOrderReceipt(
            adapter=self.adapter_name,
            venue_id=self.account_id,
            symbol=symbol,
            side=side,
            notional_usd=float(notional_usd),
            oms_state=oms.state,
            reason=oms.reason,
            sandbox=True,
            paper_only=True,
            live=False,
        )
