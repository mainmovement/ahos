#!/usr/bin/env python3
"""AHOS provider reachability probe — classified, honest, never optimistic.

WHY
---
M-GAP-007 ("provider success path unproven") is closed by an operator running a
probe on the target laptop and committing the result. The soak protocol and the
gap register both told the operator to run `--probe-providers`, but no such
command existed on the runtime entrypoint -- the flag lived only on
`scripts/system_state_snapshot.py`, and that probe covered 2 of 6 providers and
reported raw exception class names rather than a usable classification.

This module gives the operator one command whose output can settle the question
"does this laptop reach market data, and if not, exactly how does it fail?"

CLASSIFICATION LAW
------------------
A failure is never rounded up to a success. Statuses are disjoint and are
mapped from observed behaviour, never guessed:

    SUCCESS        provider answered AND returned >= 1 token
    EMPTY          provider answered cleanly but returned 0 tokens
                   (reachable -- NOT a success for M-GAP-007 purposes)
    TLS_ERROR      TLS/SSL handshake failure (the sandbox's signature failure)
    TIMEOUT        no answer within the deadline
    RATE_LIMIT     HTTP 429 / provider rate-limit envelope
    AUTH_REQUIRED  credential missing or rejected (HTTP 401/403, NO_KEY)
    UNSUPPORTED    provider honestly does not serve this chain
    ERROR          reached but failed (HTTP 5xx, bad payload, DOWN envelope)
    UNKNOWN        genuinely unclassifiable -- never used to mean "probably ok"

Only SUCCESS counts as a live success. `EMPTY` is called out separately because
"reachable but empty" is exactly the ambiguity that M-GAP-002 was raised for.
"""
from __future__ import annotations

import socket
import ssl
import time
from dataclasses import asdict, dataclass, field
from typing import Any

# Disjoint, ordered by operator severity.
STATUS_SUCCESS = "SUCCESS"
STATUS_EMPTY = "EMPTY"
STATUS_TLS_ERROR = "TLS_ERROR"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_RATE_LIMIT = "RATE_LIMIT"
STATUS_AUTH_REQUIRED = "AUTH_REQUIRED"
STATUS_UNSUPPORTED = "UNSUPPORTED"
STATUS_ERROR = "ERROR"
STATUS_UNKNOWN = "UNKNOWN"

ALL_STATUSES = (
    STATUS_SUCCESS, STATUS_EMPTY, STATUS_TLS_ERROR, STATUS_TIMEOUT,
    STATUS_RATE_LIMIT, STATUS_AUTH_REQUIRED, STATUS_UNSUPPORTED,
    STATUS_ERROR, STATUS_UNKNOWN,
)


@dataclass
class ProbeResult:
    provider_id: str
    status: str
    token_count: int = 0
    chain: str = "solana"
    latency_ms: float | None = None
    detail: str | None = None
    probed_at_utc: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProbeReport:
    probed_at_utc: str
    chain: str
    results: list[ProbeResult] = field(default_factory=list)

    @property
    def successes(self) -> list[ProbeResult]:
        return [r for r in self.results if r.status == STATUS_SUCCESS]

    @property
    def any_success(self) -> bool:
        return bool(self.successes)

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "ahos.provider_probe.v1",
            "probed_at_utc": self.probed_at_utc,
            "chain": self.chain,
            "results": [r.as_dict() for r in self.results],
            "status_counts": self.status_counts(),
            "any_success": self.any_success,
            # The single fact M-GAP-007 turns on, stated explicitly so no
            # reader has to infer it from a table.
            "m_gap_007_live_success_proven": self.any_success,
        }


def classify_exception(exc: BaseException) -> tuple[str, str]:
    """Map a raised exception onto a probe status. Never returns SUCCESS."""
    detail = f"{type(exc).__name__}: {exc}"[:300]

    if isinstance(exc, (ssl.SSLError, ssl.SSLCertVerificationError)):
        return STATUS_TLS_ERROR, detail
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return STATUS_TIMEOUT, detail

    text = f"{type(exc).__name__} {exc}".lower()
    # urllib wraps TLS failures in URLError, so inspect the message too.
    if "ssl" in text or "tls" in text or "certificate" in text or "eof occurred" in text:
        return STATUS_TLS_ERROR, detail
    if "timed out" in text or "timeout" in text:
        return STATUS_TIMEOUT, detail
    if "429" in text or "rate limit" in text or "too many requests" in text:
        return STATUS_RATE_LIMIT, detail
    if "401" in text or "403" in text or "unauthorized" in text or "forbidden" in text:
        return STATUS_AUTH_REQUIRED, detail
    return STATUS_ERROR, detail


def classify_response(resp: Any) -> tuple[str, int, str | None]:
    """Map a provider envelope onto a probe status.

    The adapters already fail closed with a normalized envelope, so this
    translates their vocabulary rather than second-guessing it.
    """
    status = str(getattr(resp, "status", "") or "").upper()
    tokens = list(getattr(resp, "tokens", []) or [])
    message = getattr(resp, "error_message", None)

    if status == "OK":
        if tokens:
            return STATUS_SUCCESS, len(tokens), message
        # Reachable but empty is NOT a success -- this is precisely the
        # ambiguity between "no market" and "broken provider" that the
        # collector's failure-event table exists to disambiguate.
        return STATUS_EMPTY, 0, message or "provider returned 0 tokens"
    if status in ("NO_KEY", "AUTH_REQUIRED"):
        return STATUS_AUTH_REQUIRED, 0, message or "credential not configured"
    if status == "UNSUPPORTED":
        return STATUS_UNSUPPORTED, 0, message or "provider does not serve this chain"
    if status == "RATE_LIMIT":
        return STATUS_RATE_LIMIT, 0, message
    if status == "TIMEOUT":
        return STATUS_TIMEOUT, 0, message
    if status in ("DOWN", "ERROR"):
        blob = f"{status} {message or ''}".lower()
        if "ssl" in blob or "tls" in blob or "eof occurred" in blob:
            return STATUS_TLS_ERROR, 0, message
        if "429" in blob or "rate limit" in blob:
            return STATUS_RATE_LIMIT, 0, message
        if "401" in blob or "403" in blob:
            return STATUS_AUTH_REQUIRED, 0, message
        return STATUS_ERROR, 0, message
    if not status:
        return STATUS_UNKNOWN, 0, message or "provider returned no status"
    return STATUS_UNKNOWN, 0, message or f"unmapped provider status {status!r}"


def _utc(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def probe_providers(chain: str = "solana",
                    providers: dict[str, Any] | None = None) -> ProbeReport:
    """Probe every registered provider for live reachability.

    Read-only: discovery endpoints only, no persistence, no scoring. A probe
    must never mutate operational state or emit predictions.
    """
    if providers is None:
        from .adapters import (
            DexScreenerAdapter,
            GeckoTerminalAdapter,
            GoPlusSecurityAdapter,
            RugCheckSecurityAdapter,
        )
        from .chain_explorer import ChainExplorerAdapter
        from .coingecko import CoinGeckoAdapter

        providers = {
            "dexscreener": DexScreenerAdapter(),
            "geckoterminal": GeckoTerminalAdapter(),
            "coingecko": CoinGeckoAdapter(),
            "goplus": GoPlusSecurityAdapter(),
            "rugcheck": RugCheckSecurityAdapter(),
            "chain_explorer": ChainExplorerAdapter(),
        }

    report = ProbeReport(probed_at_utc=_utc(time.time()), chain=chain)

    for pid in sorted(providers):
        provider = providers[pid]
        started = time.time()
        probed_at = _utc(started)
        try:
            # Security-only adapters have no discovery endpoint: their
            # `fetch_candidate_tokens` returns an empty list WITHOUT any network
            # call. Reporting that as EMPTY would claim reachability that was
            # never tested -- a fabricated success in all but name.
            capabilities = list(getattr(provider, "capabilities", []) or [])
            if capabilities and "discovery" not in capabilities:
                report.results.append(ProbeResult(
                    provider_id=pid, status=STATUS_UNSUPPORTED, chain=chain,
                    detail=(f"no discovery capability (has {capabilities}); "
                            "reachability not tested by this probe"),
                    probed_at_utc=probed_at,
                    latency_ms=round((time.time() - started) * 1000.0, 1)))
                continue

            fetch = getattr(provider, "fetch_candidate_tokens", None)
            if fetch is None:
                report.results.append(ProbeResult(
                    provider_id=pid, status=STATUS_UNSUPPORTED, chain=chain,
                    detail="provider exposes no discovery endpoint",
                    probed_at_utc=probed_at,
                    latency_ms=round((time.time() - started) * 1000.0, 1)))
                continue
            resp = fetch(chain, limit=2)
            status, count, detail = classify_response(resp)
            report.results.append(ProbeResult(
                provider_id=pid, status=status, token_count=count, chain=chain,
                latency_ms=round((time.time() - started) * 1000.0, 1),
                detail=detail, probed_at_utc=probed_at))
        except Exception as exc:
            status, detail = classify_exception(exc)
            report.results.append(ProbeResult(
                provider_id=pid, status=status, chain=chain,
                latency_ms=round((time.time() - started) * 1000.0, 1),
                detail=detail, probed_at_utc=probed_at))

    return report


def render_table(report: ProbeReport) -> str:
    """Operator-facing summary. States the M-GAP-007 verdict explicitly."""
    lines = [
        f"Provider probe — chain={report.chain}  at {report.probed_at_utc}",
        f"{'provider':<16} {'status':<14} {'tokens':>6}  {'ms':>7}  detail",
        "-" * 88,
    ]
    for r in report.results:
        detail = (r.detail or "")[:38]
        latency = f"{r.latency_ms:.0f}" if r.latency_ms is not None else "-"
        lines.append(f"{r.provider_id:<16} {r.status:<14} {r.token_count:>6}  "
                     f"{latency:>7}  {detail}")
    lines.append("-" * 88)
    lines.append(f"counts: {report.status_counts()}")
    if report.any_success:
        names = ", ".join(r.provider_id for r in report.successes)
        lines.append(f"LIVE SUCCESS: {names} — this host reaches market data.")
        lines.append("M-GAP-007 evidence: commit this snapshot from the laptop.")
    else:
        lines.append("NO LIVE SUCCESS on this host. Failure classes above are the "
                     "evidence; nothing is fabricated.")
        lines.append("M-GAP-007 remains OPEN — USER-ACTION-REQUIRED on the laptop.")
    return "\n".join(lines)
