"""M70 research safety lock. Paper mode stays locked. Live mode halts."""
from __future__ import annotations


def safety_lock(*, paper_only: bool) -> str:
    if not paper_only:
        return "HALT"
    return "LOCKED_PAPER"
