"""M40 treasury transfer requests. Paper only.

The system may record a request. It never sends funds. A replay, a cap breach,
an expired request, an address inside the message, or the wrong network is
rejected.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

AHOS_DAILY_CAP_USD = 1_000.0
BROKER_DAILY_CAP_USD = 1_000.0
ALLOWED_NETWORK = "owner-whitelist"

_ADDRESS = re.compile(r"0x[a-fA-F0-9]{40}|bc1[a-z0-9]{20,}|T[1-9A-HJ-NP-Za-km-z]{33}")


@dataclass(frozen=True, slots=True)
class TransferRequest:
    request_id: str
    amount_usd: float
    network: str
    message: str
    now_ts: str
    expires_ts: str


@dataclass(frozen=True, slots=True)
class RequestVerdict:
    accepted: bool
    reason: str
    executes: bool


def submit_request(
    request: TransferRequest,
    *,
    seen_ids: set[str],
    spent_ahos_usd: float,
    spent_broker_usd: float,
) -> RequestVerdict:
    if request.request_id in seen_ids:
        return RequestVerdict(False, "replay", False)
    if request.now_ts >= request.expires_ts:
        return RequestVerdict(False, "expired", False)
    if request.network != ALLOWED_NETWORK:
        return RequestVerdict(False, "wrong network", False)
    if _ADDRESS.search(request.message):
        return RequestVerdict(False, "address in message", False)
    if request.amount_usd <= 0:
        return RequestVerdict(False, "amount not positive", False)
    if spent_ahos_usd + request.amount_usd > AHOS_DAILY_CAP_USD:
        return RequestVerdict(False, "ahos daily cap", False)
    if spent_broker_usd + request.amount_usd > BROKER_DAILY_CAP_USD:
        return RequestVerdict(False, "broker daily cap", False)
    return RequestVerdict(True, "request recorded for the owner", False)
