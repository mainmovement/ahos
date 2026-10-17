"""M22 testnet request. Mainnet is refused. Nothing is sent."""
from __future__ import annotations

from architecture.treasury.requests import TransferRequest, submit_request


def submit_testnet(request: TransferRequest, **kwargs):
    if request.network != "testnet":
        from architecture.treasury.requests import RequestVerdict
        return RequestVerdict(False, "testnet network required", False)
    paper = TransferRequest(
        request_id=request.request_id,
        amount_usd=request.amount_usd,
        network="owner-whitelist",
        message=request.message,
        now_ts=request.now_ts,
        expires_ts=request.expires_ts,
    )
    verdict = submit_request(paper, **kwargs)
    return verdict
