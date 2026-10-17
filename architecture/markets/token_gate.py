"""M33 / M55 paper token gate. Paid sources and unknown security do not enter."""
from __future__ import annotations

from dataclasses import dataclass

FREE = frozenset({"dexscreener", "geckoterminal", "goplus", "rugcheck"})


@dataclass(frozen=True, slots=True)
class TokenDecision:
    state: str
    trades: bool


def consider(*, source: str, security: str) -> TokenDecision:
    if source.strip().lower() not in FREE:
        return TokenDecision("REFUSED_SOURCE", False)
    if security != "PASS":
        return TokenDecision("REFUSED_SECURITY", False)
    return TokenDecision("PAPER_WATCH", False)
