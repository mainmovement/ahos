"""Gemini conversational turn helper (Phase 7b). Zero authority.

    <venv python> -m architecture.ai.gemini_chat   (stdin: JSON utf-8, stdout: JSON utf-8)

One model step with function calling: the TypeScript agent (chat_agent.ts) owns
the loop, executes whitelisted READ tools itself, and turns PROPOSE tools into
confirm-gated pending actions. This helper only relays one generateContent call.
The API key is read here (Windows Credential Manager ``AHOS/ai/gemini``, read-only)
and never leaves this process (same rules as gemini_phraser.py).

Input  {"system": str, "contents": [gemini contents], "tools": [functionDeclarations],
        "models": [str]?, "timeout_ms": int?, "temperature": float?}
Output {"ok": bool, "parts": [ {text} | {functionCall:{name,args}} (+thoughtSignature) ],
        "finish_reason": str|null, "model": str|null, "status", "reason_code",
        "latency_ms", "attempts": [...]}
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Callable

from architecture.ai import gemini_phraser as gp

MAX_REQUEST_BYTES = 256 * 1024
ALLOWED_PART_KEYS = ("text", "functionCall", "functionResponse", "thoughtSignature")
TOTAL_BUDGET_MS = 9000


def _clean_parts(parts: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in parts or []:
        if not isinstance(p, dict) or p.get("thought") is True:
            continue
        q = {k: p[k] for k in ALLOWED_PART_KEYS if k in p}
        if q:
            out.append(q)
    return out


def _sanitize_contents(contents: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in contents or []:
        if not isinstance(c, dict):
            continue
        role = c.get("role")
        if role not in ("user", "model"):
            continue
        parts = _clean_parts(c.get("parts"))
        if parts:
            out.append({"role": role, "parts": parts})
    return out[-40:]


def build_chat_body(req: dict[str, Any]) -> bytes:
    body: dict[str, Any] = {
        "contents": _sanitize_contents(req.get("contents")),
        "generationConfig": {
            "temperature": max(0.0, min(float(req.get("temperature", 0.3) or 0.3), 1.0)),
            "maxOutputTokens": 1024,
            "candidateCount": 1,
        },
    }
    system = str(req.get("system") or "").strip()
    if system:
        body["systemInstruction"] = {"parts": [{"text": system[:12000]}]}
    tools = [t for t in (req.get("tools") or []) if isinstance(t, dict) and t.get("name")]
    if tools:
        body["tools"] = [{"functionDeclarations": tools[:24]}]
        body["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


_NO_RETRY = {"AUTH_FAILED", "QUOTA_EXHAUSTED", "BLOCKED"}


def chat_step(request: dict[str, Any], *, store=None, opener: gp.Opener = gp._default_opener,
              clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    t0 = clock()
    out: dict[str, Any] = {"ok": False, "parts": [], "finish_reason": None, "model": None,
                           "status": "UNAVAILABLE", "reason_code": "UNSET", "latency_ms": 0, "attempts": []}
    try:
        body = build_chat_body(request)
        if not json.loads(body.decode("utf-8")).get("contents"):
            out.update(status="DEGRADED", reason_code="EMPTY_CONTENTS")
            return out
        models = [str(m).strip() for m in (request.get("models") or gp.DEFAULT_MODELS) if str(m).strip()][:2]
        per_call_s = max(0.5, min(int(request.get("timeout_ms") or gp.DEFAULT_TIMEOUT_MS), 8000) / 1000.0)
        from architecture.ai.credential_store import (CredentialRef, CredentialUnavailable,
                                                      WindowsCredentialManagerStore)
        store = store or WindowsCredentialManagerStore()
        try:
            key = store.get_secret(CredentialRef(gp.PROVIDER))
        except CredentialUnavailable as exc:
            status = "UNAVAILABLE" if exc.reason_code in ("NOT_WINDOWS", "READ_FAILED") else "AUTH_FAILED"
            out.update(status=status, reason_code=exc.reason_code)
            return out
        for model in models:
            remaining = TOTAL_BUDGET_MS / 1000.0 - (clock() - t0)
            if remaining < 0.5:
                break
            a0 = clock()
            payload, assessment, kind = gp.call_model_payload(model, body, key, min(per_call_s, remaining), opener)
            parts: list[dict[str, Any]] = []
            finish = None
            status, reason = assessment.status.value, assessment.reason_code
            if payload is not None:
                cands = payload.get("candidates") or []
                if cands and isinstance(cands[0], dict):
                    parts = _clean_parts((cands[0].get("content") or {}).get("parts"))
                    finish = cands[0].get("finishReason")
                if not parts:
                    status, reason = "DEGRADED", "EMPTY_COMPLETION"
            out["attempts"].append({"model": model, "status": status, "reason_code": reason,
                                    "http_status": assessment.http_status, "error_kind": kind,
                                    "latency_ms": int((clock() - a0) * 1000)})
            out.update(status=status, reason_code=reason)
            if parts:
                out.update(ok=True, parts=parts, finish_reason=finish, model=model)
                break
            if status in _NO_RETRY:
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
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        request = json.loads(raw.decode("utf-8")) if raw and len(raw) <= MAX_REQUEST_BYTES else {}
        if not isinstance(request, dict):
            request = {}
    except Exception:  # noqa: BLE001
        request = {}
    result = chat_step(request)
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
