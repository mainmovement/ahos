"""Phase 7b: Gemini function-calling relay helper (zero authority, no network in tests)."""
from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from architecture.ai import gemini_chat as gc
from tests.test_gemini_phraser import KEY, Opener, Store

ROOT = Path(__file__).resolve().parents[1]
TOOLS = [{"name": "get_market", "description": "market snapshot"}]


def payload(parts, finish="STOP") -> bytes:
    return json.dumps({"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": finish}]},
                      ensure_ascii=False).encode()


def req(**kw):
    base = {"system": "فقط فارسی", "contents": [{"role": "user", "parts": [{"text": "قیمت بیت کوین؟"}]}],
            "tools": TOOLS, "models": ["m-primary", "m-fallback"], "timeout_ms": 4000}
    base.update(kw)
    return base


def run(script, store=None, **kw):
    op = Opener(script)
    out = gc.chat_step(req(**kw), store=store or Store(), opener=op)
    assert KEY not in json.dumps(out, ensure_ascii=False)
    return out, op


def test_function_call_relayed_with_thought_signature_and_tools_declared():
    out, op = run([payload([{"functionCall": {"name": "get_market", "args": {}}, "thoughtSignature": "SIG"}])])
    assert out["ok"] is True and out["model"] == "m-primary"
    assert out["parts"] == [{"functionCall": {"name": "get_market", "args": {}}, "thoughtSignature": "SIG"}]
    body = json.loads(op.calls[0]["body"].decode("utf-8"))
    assert body["tools"] == [{"functionDeclarations": TOOLS}]
    assert body["toolConfig"]["functionCallingConfig"]["mode"] == "AUTO"
    assert body["systemInstruction"]["parts"][0]["text"] == "فقط فارسی"
    assert op.calls[0]["headers"].get("X-goog-api-key") == KEY
    assert KEY not in op.calls[0]["url"]


def test_thought_parts_dropped_and_contents_sanitized():
    contents = [
        {"role": "system", "parts": [{"text": "x"}]},
        {"role": "user", "parts": [{"text": "a", "evil": 1}]},
        {"role": "model", "parts": [{"text": "secret plan", "thought": True}, {"functionCall": {"name": "get_market"}}]},
        {"role": "user", "parts": [{"functionResponse": {"name": "get_market", "response": {"result": {"p": 1}}}}]},
    ]
    out, op = run([payload([{"text": "plan", "thought": True}, {"text": "پاسخ"}])], contents=contents)
    assert out["parts"] == [{"text": "پاسخ"}]
    sent = json.loads(op.calls[0]["body"].decode("utf-8"))["contents"]
    assert [c["role"] for c in sent] == ["user", "model", "user"]
    assert sent[0]["parts"] == [{"text": "a"}]
    assert sent[1]["parts"] == [{"functionCall": {"name": "get_market"}}]


def test_fallback_model_on_transient_error_but_not_on_quota_or_auth():
    out, op = run([urllib.error.URLError(TimeoutError()), payload([{"text": "ok"}])])
    assert out["ok"] and out["model"] == "m-fallback" and len(op.calls) == 2
    out, op = run([429, payload([{"text": "ok"}])])
    assert not out["ok"] and out["status"] == "QUOTA_EXHAUSTED" and len(op.calls) == 1
    out, op = run([401])
    assert not out["ok"] and out["status"] == "AUTH_FAILED"


def test_empty_completion_and_missing_credential_and_empty_contents():
    out, _ = run([payload([]), payload([])])
    assert not out["ok"] and out["reason_code"] == "EMPTY_COMPLETION"
    out, op = run([], store=Store("NOT_FOUND"))
    assert not out["ok"] and out["reason_code"] == "NOT_FOUND" and op.calls == []
    out, op = run([], contents=[])
    assert out["reason_code"] == "EMPTY_CONTENTS" and op.calls == []


def test_helper_has_no_authority_and_is_whitelisted_from_typescript():
    src = (ROOT / "architecture/ai/gemini_chat.py").read_text(encoding="utf-8")
    for forbidden in ("subprocess", "os.environ", "print(", "logging", "open(", "requests"):
        assert forbidden not in src, forbidden
    ts = (ROOT / "gemini_phraser.ts").read_text(encoding="utf-8")
    assert '"architecture.ai.gemini_chat"' in ts and "HELPER_MODULES" in ts
    agent = (ROOT / "chat_agent.ts").read_text(encoding="utf-8")
    assert 'spawnPythonJson' in agent and '"architecture.ai.gemini_chat"' in agent
