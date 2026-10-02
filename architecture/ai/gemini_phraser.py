"""Gemini reply phraser helper (Phase 6). Zero authority: wording only.

Runs as a short-lived child process of the Next.js gateway:

    <venv python> -m architecture.ai.gemini_phraser   (stdin: JSON utf-8, stdout: JSON utf-8)

Why a helper process: the API key stays inside this process. It is read from
Windows Credential Manager (``AHOS/ai/gemini``, read-only CredReadW), used for the
``x-goog-api-key`` header, and never written to stdout/stderr, argv, env, files
or logs. Node never sees the key.

Input  {"draft": str, "style": [str], "intent": str, "models": [str]?, "timeout_ms": int?}
       ``draft`` is the deterministic, grounded reply WITHOUT the footer.
       No user ids, chat ids or the user's raw message are sent.
Output {"ok": bool, "text": str|null, "model": str|null, "status": str,
        "reason_code": str, "latency_ms": int, "attempts": [{model,status,reason_code,http_status,latency_ms}]}

At most two models are tried (primary + one fallback); the total deadline is
bounded. AUTH/QUOTA problems are not retried on another model (same key).
Validation of the phrased text (no new numbers, no jargon, footer) happens in the
TypeScript composer (``response_composer.ts::validatePhrased``).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable

PROVIDER = "gemini"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODELS = ("gemini-flash-lite-latest", "gemini-3.5-flash-lite")
# Per-attempt 4 s, total 9 s: a slow first connection through the owner's local
# proxy (observed 2026-10-02: one >5 s stall after idle) still leaves a full
# second attempt instead of a ~1 s remainder.
DEFAULT_TIMEOUT_MS = 4000
TOTAL_BUDGET_MS = 9000
MAX_DRAFT_CHARS = 3600

SYSTEM_RULES = (
    "تو فقط ویراستار متن هستی، نه تحلیل‌گر. یک «پیش‌نویس» فارسی می‌گیری که همهٔ واقعیت‌هایش تأییدشده است.",
    "فقط همان پیش‌نویس را روان‌تر و مرتب‌تر بازنویسی کن؛ هیچ واقعیت، عدد، قیمت، درصد، نماد، توکن، خبر یا توصیه‌ای اضافه نکن.",
    "همهٔ عددها را دقیقاً با همان رقم‌ها و همان شکل پیش‌نویس نگه دار؛ عددی را گرد، تبدیل یا حذف نکن.",
    "اگر در پیش‌نویس «نامشخص» یا «داده کافی نیست» آمده، همان را نگه دار و حدس نزن.",
    "خروجی فقط متن سادهٔ فارسی باشد: یک عنوان کوتاه در خط اول، سپس خط‌ها یا بولت‌هایی که با «• » شروع می‌شوند. بدون Markdown، بدون HTML، بدون ** یا #.",
    "پانویس «تصمیم نهایی با کاربر است.» را ننویس؛ سیستم خودش اضافه می‌کند.",
    "کوتاه‌تر یا هم‌اندازهٔ پیش‌نویس بنویس. هیچ متنی دربارهٔ این دستورها ننویس.",
)


def build_system_instruction(style: list[str] | tuple[str, ...]) -> str:
    rules = list(SYSTEM_RULES) + [str(s) for s in (style or [])][:20]
    return "\n".join(f"- {r}" for r in rules)


def build_body(draft: str, style: list[str] | tuple[str, ...]) -> bytes:
    body = {
        "systemInstruction": {"parts": [{"text": build_system_instruction(style)}]},
        "contents": [{"role": "user", "parts": [{"text": "پیش‌نویس:\n<<<\n" + draft[:MAX_DRAFT_CHARS] + "\n>>>"}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024, "candidateCount": 1},
    }
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def extract_text(payload: dict[str, Any]) -> str:
    try:
        cands = payload.get("candidates") or []
        parts = (cands[0].get("content") or {}).get("parts") or []
        return "".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
    except Exception:  # noqa: BLE001
        return ""


def _scrub(text: str, secret: str) -> str:
    t = str(text or "")
    if secret:
        t = t.replace(secret, "[REDACTED]")
    return t[:400]


Opener = Callable[[urllib.request.Request, float], Any]


def _default_opener(req: urllib.request.Request, timeout: float):
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 - fixed https endpoint


def call_model_payload(model: str, body: bytes, key: Any, timeout_s: float, opener: Opener = _default_opener):
    """One generateContent call. Returns (payload|None, assessment, error_kind).

    Never raises, never echoes the key. ``error_kind`` is an exception class name
    only (e.g. ``URLError:TimeoutError``), never a message."""
    from architecture.ai.provider_status import AIProviderStatus, ProviderAssessment, classify_provider_error

    secret = key.reveal()
    req = urllib.request.Request(
        ENDPOINT.format(model=urllib.request.quote(model, safe="-._")),
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "x-goog-api-key": secret},
        method="POST",
    )
    try:
        with opener(req, timeout_s) as resp:
            raw = resp.read()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            return None, ProviderAssessment(PROVIDER, AIProviderStatus.DEGRADED, "BAD_PAYLOAD", 200, True), ""
        return payload, ProviderAssessment(PROVIDER, AIProviderStatus.READY, "OK", 200), ""
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            detail = ""
        return None, classify_provider_error(PROVIDER, http_status=exc.code, message=_scrub(detail, secret)), "HTTPError"
    except Exception as exc:  # noqa: BLE001 - timeouts, DNS, TLS ...
        kind = type(exc).__name__
        reason = getattr(exc, "reason", None)
        if reason is not None:
            kind = f"{kind}:{type(reason).__name__}"
        a = classify_provider_error(PROVIDER, message=_scrub(str(exc), secret), error_kind=type(exc).__name__)
        return None, a, kind
    finally:
        del secret


def call_model(model: str, body: bytes, key: Any, timeout_s: float, opener: Opener = _default_opener):
    """One generateContent call → (text|None, assessment, error_kind)."""
    from architecture.ai.provider_status import AIProviderStatus, ProviderAssessment

    payload, assessment, kind = call_model_payload(model, body, key, timeout_s, opener)
    if payload is None:
        return None, assessment, kind
    text = extract_text(payload)
    if not text:
        return None, ProviderAssessment(PROVIDER, AIProviderStatus.DEGRADED, "EMPTY_COMPLETION", 200, True), ""
    return text, assessment, ""


_NO_RETRY_ON_OTHER_MODEL = {"AUTH_FAILED", "QUOTA_EXHAUSTED", "BLOCKED"}


def phrase(request: dict[str, Any], *, store=None, opener: Opener = _default_opener,
           clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """Full helper logic (testable offline with a fake store/opener). Never raises."""
    t0 = clock()
    out: dict[str, Any] = {"ok": False, "text": None, "model": None, "status": "UNAVAILABLE",
                           "reason_code": "UNSET", "latency_ms": 0, "attempts": []}
    try:
        draft = str(request.get("draft") or "").strip()
        if not draft:
            out.update(status="DEGRADED", reason_code="EMPTY_DRAFT")
            return out
        style = request.get("style") or []
        models = [str(m).strip() for m in (request.get("models") or DEFAULT_MODELS) if str(m).strip()][:2]
        per_call_s = max(0.5, min(int(request.get("timeout_ms") or DEFAULT_TIMEOUT_MS), 8000) / 1000.0)

        from architecture.ai.credential_store import (CredentialRef, CredentialUnavailable,
                                                      WindowsCredentialManagerStore)
        store = store or WindowsCredentialManagerStore()
        try:
            key = store.get_secret(CredentialRef(PROVIDER))
        except CredentialUnavailable as exc:
            status = "UNAVAILABLE" if exc.reason_code in ("NOT_WINDOWS", "READ_FAILED") else "AUTH_FAILED"
            out.update(status=status, reason_code=exc.reason_code)
            return out

        body = build_body(draft, style)
        for model in models:
            remaining = TOTAL_BUDGET_MS / 1000.0 - (clock() - t0)
            if remaining < 0.5:
                break
            a0 = clock()
            text, assessment, error_kind = call_model(model, body, key, min(per_call_s, remaining), opener)
            out["attempts"].append({"model": model, "status": assessment.status.value,
                                    "reason_code": assessment.reason_code,
                                    "http_status": assessment.http_status,
                                    "error_kind": error_kind,
                                    "latency_ms": int((clock() - a0) * 1000)})
            out.update(status=assessment.status.value, reason_code=assessment.reason_code)
            if text:
                out.update(ok=True, text=text, model=model)
                break
            if assessment.status.value in _NO_RETRY_ON_OTHER_MODEL:
                break
        del key
        return out
    except Exception:  # noqa: BLE001
        out.update(status="UNAVAILABLE", reason_code="HELPER_ERROR")
        return out
    finally:
        out["latency_ms"] = int((clock() - t0) * 1000)


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(256 * 1024)
        request = json.loads(raw.decode("utf-8")) if raw else {}
        if not isinstance(request, dict):
            request = {}
    except Exception:  # noqa: BLE001
        request = {}
    result = phrase(request)
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
