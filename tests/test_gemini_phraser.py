"""Offline tests for the Gemini phraser helper (Phase 6). No network, no real key."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

from architecture.ai import gemini_phraser as g
from architecture.ai.credential_store import CredentialUnavailable, SecretValue

ROOT = Path(__file__).resolve().parents[1]
KEY = "AIza" + "Kq7" * 11            # synthetic, built at runtime
DRAFT = "وضعیت بازار\n• بیت‌کوین: ۶۴٬۲۰۰ دلار\n• داده کافی نیست"


class Store:
    def __init__(self, exc: str | None = None):
        self.exc = exc

    def get_secret(self, ref):
        assert ref.target == "AHOS/ai/gemini"
        if self.exc:
            raise CredentialUnavailable(self.exc)
        return SecretValue(KEY)


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok_payload(text: str) -> bytes:
    return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}, ensure_ascii=False).encode()


class Opener:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, req, timeout):
        self.calls.append({"url": req.full_url, "headers": dict(req.header_items()), "body": req.data,
                           "timeout": timeout})
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        if isinstance(step, int):
            raise urllib.error.HTTPError(req.full_url, step, "err", {},
                                         io.BytesIO(f"error with key {KEY}".encode()))
        return Resp(step)


def run(script, store=None, **req):
    op = Opener(script)
    out = g.phrase({"draft": DRAFT, "style": ["کوتاه"], **req}, store=store or Store(), opener=op)
    blob = json.dumps(out, ensure_ascii=False)
    assert KEY not in blob
    return out, op


def test_success_uses_header_key_primary_model_and_utf8_body():
    out, op = run([ok_payload("بازار امروز\n• بیت‌کوین: ۶۴٬۲۰۰ دلار")])
    assert out["ok"] and out["model"] == "gemini-flash-lite-latest" and out["status"] == "READY"
    c = op.calls[0]
    assert c["url"].endswith("/models/gemini-flash-lite-latest:generateContent")
    assert KEY not in c["url"]
    hdrs = {k.lower(): v for k, v in c["headers"].items()}
    assert hdrs["x-goog-api-key"] == KEY
    body = json.loads(c["body"].decode("utf-8"))
    assert "۶۴٬۲۰۰" in body["contents"][0]["parts"][0]["text"]
    assert "تصمیم نهایی" in body["systemInstruction"]["parts"][0]["text"]  # tells model not to write footer
    assert body["generationConfig"]["temperature"] <= 0.3
    assert c["timeout"] <= 8


@pytest.mark.parametrize("code,status", [(503, "UNAVAILABLE"), (404, "MODEL_UNAVAILABLE")])
def test_fallback_to_second_model_on_transient(code, status):
    out, op = run([code, ok_payload("متن")])
    assert out["ok"] and out["model"] == "gemini-3.5-flash-lite"
    assert [a["status"] for a in out["attempts"]] == [status, "READY"]
    assert len(op.calls) == 2


@pytest.mark.parametrize("code,status", [(401, "AUTH_FAILED"), (403, "AUTH_FAILED")])
def test_auth_failure_does_not_try_other_model(code, status):
    out, op = run([code, ok_payload("x")])
    assert not out["ok"] and out["status"] == status and len(op.calls) == 1


def test_quota_429_classified_and_redacted():
    out, op = run([429, 429])
    assert not out["ok"] and out["status"] in ("QUOTA_EXHAUSTED", "DEGRADED", "UNAVAILABLE")
    assert out["attempts"][0]["http_status"] == 429


def test_timeout_and_empty_completion():
    out, _ = run([TimeoutError("timed out " + KEY), ok_payload("")])
    assert not out["ok"]
    assert out["attempts"][0]["status"] == "UNAVAILABLE"
    assert out["attempts"][1]["reason_code"] == "EMPTY_COMPLETION"


@pytest.mark.parametrize("reason,status", [("NO_CREDENTIAL", "AUTH_FAILED"), ("NOT_WINDOWS", "UNAVAILABLE"),
                                           ("READ_FAILED", "UNAVAILABLE")])
def test_credential_problems_make_no_call(reason, status):
    out, op = run([], store=Store(reason))
    assert out == {**out, "ok": False, "reason_code": reason, "status": status}
    assert op.calls == []


def test_empty_draft_and_model_override_limited_to_two():
    out, op = run([], draft="  ")
    assert out["reason_code"] == "EMPTY_DRAFT" and op.calls == []
    out, op = run([503, 503], models=["a", "b", "c"])
    assert [a["model"] for a in out["attempts"]] == ["a", "b"]


def test_module_is_import_safe_and_never_prints_or_logs():
    src = (ROOT / "architecture" / "ai" / "gemini_phraser.py").read_text(encoding="utf-8")
    assert "print(" not in src and "logging" not in src and "os.environ" not in src
    assert ".env" not in src


def test_cli_round_trip_persian_bytes_without_credential(tmp_path):
    """Run the real helper as a subprocess: UTF-8 in, UTF-8 JSON out, never crashes.
    Off Windows (or without the credential) it must answer ok=false with a reason code."""
    if sys.platform == "win32":
        pytest.skip("on Windows the real credential may exist; the live smoke covers that path")
    req = json.dumps({"draft": DRAFT, "style": []}, ensure_ascii=False).encode("utf-8")
    p = subprocess.run([sys.executable, "-m", "architecture.ai.gemini_phraser"], input=req,
                       capture_output=True, cwd=str(ROOT), timeout=60)
    assert p.returncode == 0 and p.stderr == b""
    out = json.loads(p.stdout.decode("utf-8"))
    assert out["ok"] is False and out["reason_code"] == "NOT_WINDOWS"


def test_gateway_wiring_keeps_refusals_locked_and_key_out_of_node():
    chat = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert "getDefaultPhraser()" in chat
    assert 'locked: intent === "trade_signal"' in chat   # Phase 7: policy reply never phrased
    refusal_line = next(l for l in chat.splitlines() if "locked: true" in l)
    assert "phraser" not in refusal_line            # GM-04 refusals are never phrased
    ts = (ROOT / "gemini_phraser.ts").read_text(encoding="utf-8")
    assert "shell: false" in ts and '"-m", "architecture.ai.gemini_phraser"' in ts
    assert "x-goog-api-key" not in ts and "generativelanguage" not in ts   # key/endpoint only in the helper
    assert "DATABASE_URL" not in ts.split("export function helperEnv")[1].split("return env")[0].split("const keep")[1].split("];")[0]


def test_attempts_record_error_class_only_and_slow_first_attempt_leaves_room_for_fallback():
    clock_t = [0.0]

    def clock():
        return clock_t[0]

    class SlowThenOk:
        calls = 0

        def __call__(self, req, timeout):
            SlowThenOk.calls += 1
            if SlowThenOk.calls == 1:
                clock_t[0] += timeout            # first attempt burns its whole timeout
                raise urllib.error.URLError(TimeoutError("timed out " + KEY))
            clock_t[0] += 1.1
            return Resp(ok_payload("متن"))

    out = g.phrase({"draft": DRAFT}, store=Store(), opener=SlowThenOk(), clock=clock)
    assert out["ok"] and out["model"] == "gemini-3.5-flash-lite"
    assert out["attempts"][0]["error_kind"] == "URLError:TimeoutError"
    assert out["attempts"][0]["status"] == "UNAVAILABLE"
    assert KEY not in json.dumps(out)
