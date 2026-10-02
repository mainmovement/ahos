"""AI provider status model + error classification (GM-09).

Pure, offline, stdlib only. Maps what a provider did (HTTP status, error text,
exception, or an existing ``AIResponse`` envelope) to one honest status:

    READY | DEGRADED | UNAVAILABLE | QUOTA_EXHAUSTED | AUTH_FAILED |
    MODEL_UNAVAILABLE | BLOCKED

LAWS
  * Classification never raises: unknown input becomes UNAVAILABLE.
  * Error detail is redacted (the same rules as the mission ledger) and truncated
    before it is stored anywhere, so a key echoed back by a provider never leaks.
  * Advisory only. A status never decides, approves or gates trading; it only
    tells the mission layer whether to wait, pause, or ask the owner for a new key.

HTTP mapping
  401 -> AUTH_FAILED
  403 -> AUTH_FAILED (BLOCKED when the text says geo/region/country/policy block)
  402 -> QUOTA_EXHAUSTED
  429 -> QUOTA_EXHAUSTED, except an explicitly transient rate limit
         (retry-after / per-minute / RPM / TPM, with no quota/billing words) -> DEGRADED
  404 or model-not-found text -> MODEL_UNAVAILABLE
  451 -> BLOCKED
  408, 5xx, timeouts, connection errors -> UNAVAILABLE
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable


class AIProviderStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    AUTH_FAILED = "AUTH_FAILED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    BLOCKED = "BLOCKED"


# Statuses that need the OWNER to act on a credential (new key / top-up).
CREDENTIAL_ACTION_STATUSES = frozenset({AIProviderStatus.QUOTA_EXHAUSTED, AIProviderStatus.AUTH_FAILED})

_QUOTA = re.compile(r"(?i)(insufficient[_ ]quota|exceeded your current quota|quota (?:exceeded|exhausted)|"
                    r"out of credits?|insufficient (?:credits?|balance|funds)|billing|payment required|"
                    r"credit balance is too low|RESOURCE_EXHAUSTED|monthly (?:limit|spend)|usage limit)")
_TRANSIENT = re.compile(r"(?i)(retry[- ]after|per minute|requests per min|\brpm\b|\btpm\b|tokens per minute|"
                        r"try again in \d+(?:\.\d+)?\s*(?:ms|s|sec|seconds))")
_AUTH = re.compile(r"(?i)(invalid[_ ]api[_ ]key|incorrect api key|unauthori[sz]ed|authentication|"
                   r"api key (?:not valid|expired|revoked)|permission[_ ]denied|invalid x-api-key|"
                   r"PERMISSION_DENIED|UNAUTHENTICATED)")
_GEO = re.compile(r"(?i)(unsupported[_ ](?:country|region|location)|not available in your (?:country|region)|"
                  r"country,? region,? or territory|geo[- ]?block|region (?:is )?not supported|"
                  r"blocked by (?:proxy|firewall|policy)|sanction)")
_MODEL = re.compile(r"(?i)(model[_ ]not[_ ]found|model .{0,60}(?:does not exist|not found|decommissioned|deprecated)|"
                    r"unknown model|no such model|invalid model|model is not available)")
_NET = re.compile(r"(?i)(timed? ?out|timeout|connection (?:refused|reset|aborted)|name or service not known|"
                  r"getaddrinfo|network is unreachable|temporary failure in name resolution|"
                  r"ssl|tls|eof occurred|remote end closed)")


@dataclass(frozen=True)
class ProviderAssessment:
    provider: str
    status: AIProviderStatus
    reason_code: str
    http_status: int | None = None
    retryable: bool = False
    needs_credential_action: bool = False
    detail: str = ""                     # redacted + truncated

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def _redact(text: str) -> str:
    from architecture.mission.ledger import redact_secrets
    clean, _ = redact_secrets(str(text or ""))
    return clean[:300]


def _mk(provider: str, status: AIProviderStatus, reason: str, http: int | None, detail: str) -> ProviderAssessment:
    retryable = status in (AIProviderStatus.DEGRADED, AIProviderStatus.UNAVAILABLE)
    return ProviderAssessment(provider=provider, status=status, reason_code=reason, http_status=http,
                              retryable=retryable,
                              needs_credential_action=status in CREDENTIAL_ACTION_STATUSES,
                              detail=_redact(detail))


def classify_provider_error(provider: str = "unknown", *, http_status: int | None = None,
                            message: str = "", error_kind: str = "") -> ProviderAssessment:
    """Classify one failed provider interaction. Never raises."""
    try:
        text = f"{error_kind} {message}".strip()
        code = int(http_status) if http_status is not None and str(http_status).lstrip("-").isdigit() else None
        S = AIProviderStatus
        if code == 451 or _GEO.search(text):
            return _mk(provider, S.BLOCKED, "GEO_OR_POLICY_BLOCK", code, text)
        if code == 402:
            return _mk(provider, S.QUOTA_EXHAUSTED, "HTTP_402_PAYMENT_REQUIRED", code, text)
        if code == 429:
            if _TRANSIENT.search(text) and not _QUOTA.search(text):
                return _mk(provider, S.DEGRADED, "HTTP_429_TRANSIENT_RATE_LIMIT", code, text)
            return _mk(provider, S.QUOTA_EXHAUSTED, "HTTP_429_QUOTA", code, text)
        if code in (401, 403):
            return _mk(provider, S.AUTH_FAILED, f"HTTP_{code}_AUTH", code, text)
        if _QUOTA.search(text):
            return _mk(provider, S.QUOTA_EXHAUSTED, "QUOTA_MESSAGE", code, text)
        if code == 404 or _MODEL.search(text):
            return _mk(provider, S.MODEL_UNAVAILABLE, "MODEL_NOT_FOUND", code, text)
        if _AUTH.search(text):
            return _mk(provider, S.AUTH_FAILED, "AUTH_MESSAGE", code, text)
        if code is not None and (code == 408 or 500 <= code <= 599):
            return _mk(provider, S.UNAVAILABLE, f"HTTP_{code}_SERVER_OR_TIMEOUT", code, text)
        if _NET.search(text):
            return _mk(provider, S.UNAVAILABLE, "NETWORK", code, text)
        if code is not None and 400 <= code <= 499:
            return _mk(provider, S.DEGRADED, f"HTTP_{code}_CLIENT_ERROR", code, text)
        return _mk(provider, S.UNAVAILABLE, "UNCLASSIFIED", code, text)
    except Exception:  # noqa: BLE001 - classification must never crash the runtime
        return ProviderAssessment(provider=str(provider), status=AIProviderStatus.UNAVAILABLE,
                                  reason_code="CLASSIFIER_ERROR", retryable=True)


def classify_ai_response(resp: Any) -> ProviderAssessment:
    """Map an existing ``architecture.ai.clients.AIResponse`` (duck-typed) to a status."""
    try:
        provider = str(getattr(resp, "provider", "unknown"))
        avail = str(getattr(resp, "availability", "") or "")
        err = getattr(resp, "error_state", None) or {}
        kind = str(err.get("kind", "")) if isinstance(err, dict) else ""
        detail = str(err.get("detail", "")) if isinstance(err, dict) else ""
        http = getattr(resp, "http_status", None)
        S = AIProviderStatus
        if avail == "OK" and getattr(resp, "content", None):
            return _mk(provider, S.READY, "OK", http, "")
        if avail == "NO_KEY":
            return _mk(provider, S.AUTH_FAILED, "NO_KEY", None, detail)
        if avail == "SKIPPED_PAID":
            return _mk(provider, S.BLOCKED, "PAID_EXCLUDED_BY_POLICY", None, detail)
        if kind == "empty_completion":
            return _mk(provider, S.DEGRADED, "EMPTY_COMPLETION", http, "")
        return classify_provider_error(provider, http_status=http, message=detail, error_kind=kind)
    except Exception:  # noqa: BLE001
        return ProviderAssessment(provider="unknown", status=AIProviderStatus.UNAVAILABLE,
                                  reason_code="CLASSIFIER_ERROR", retryable=True)


def safe_provider_call(provider: str, call: Callable[[], Any]) -> tuple[Any | None, ProviderAssessment]:
    """Run a provider call; any exception becomes an assessment instead of a crash.

    ``call`` may return an AIResponse-like envelope (classified) or any truthy value
    (READY). HTTP errors that carry ``code`` are classified by status code.
    """
    try:
        result = call()
    except Exception as exc:  # noqa: BLE001 - provider outage must not crash the runtime
        code = getattr(exc, "code", None) or getattr(exc, "status", None) or getattr(exc, "status_code", None)
        return None, classify_provider_error(provider, http_status=code if isinstance(code, int) else None,
                                             message=str(exc), error_kind=type(exc).__name__)
    if hasattr(result, "availability"):
        a = classify_ai_response(result)
        return (result if a.status == AIProviderStatus.READY else None), a
    if result:
        return result, _mk(provider, AIProviderStatus.READY, "OK", None, "")
    return None, _mk(provider, AIProviderStatus.DEGRADED, "EMPTY_RESULT", None, "")
