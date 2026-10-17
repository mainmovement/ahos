"""M27 withdrawal stays a request. Without the owner present it is refused."""
from __future__ import annotations

from architecture.treasury.requests import RequestVerdict, TransferRequest, submit_request


def request_withdrawal(request: TransferRequest, *, owner_present: bool, **kwargs) -> RequestVerdict:
    if not owner_present:
        return RequestVerdict(False, "owner absent", False)
    verdict = submit_request(request, **kwargs)
    if verdict.accepted:
        return RequestVerdict(True, "request only", False)
    return verdict
