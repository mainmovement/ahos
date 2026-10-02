"""GM-09 - AI provider status model, error classification, credential-store
interface and ledger integration. Offline: fake providers only, no network,
no real credentials. Self-tests, not independent verification.
"""
from __future__ import annotations

import ast
import io
import json
import pickle
import socket
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.ai.clients import AIClient, AIResponse  # noqa: E402
from architecture.ai.credential_store import (  # noqa: E402
    CredentialRef, CredentialStore, FakeCredentialStore, NullCredentialStore, SecretValue,
    WindowsCredentialManagerStore, persian_new_key_message,
)
from architecture.ai.mission_guard import guard_provider_call  # noqa: E402
from architecture.ai.provider_status import (  # noqa: E402
    AIProviderStatus as S, classify_ai_response, classify_provider_error, safe_provider_call,
)
from architecture.mission.ledger import MissionLedger  # noqa: E402

FAKE_KEY = "gsk_" + "Zq9" * 16          # synthetic, built at runtime


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access attempted in offline test")
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket.socket, "connect", boom)


# ------------------------------------------------------------ classifier ---

@pytest.mark.parametrize("code,msg,expected", [
    (401, "", S.AUTH_FAILED),
    (403, "forbidden", S.AUTH_FAILED),
    (403, "unsupported_country_region_territory", S.BLOCKED),
    (403, "Country, region, or territory not supported", S.BLOCKED),
    (451, "", S.BLOCKED),
    (402, "", S.QUOTA_EXHAUSTED),
    (429, "", S.QUOTA_EXHAUSTED),
    (429, "You exceeded your current quota, please check your plan and billing details", S.QUOTA_EXHAUSTED),
    (429, "Rate limit reached for requests per min. Please try again in 20s", S.DEGRADED),
    (429, "rate limit; retry-after: 5 but insufficient_quota", S.QUOTA_EXHAUSTED),
    (200, "RESOURCE_EXHAUSTED: monthly spend limit", S.QUOTA_EXHAUSTED),
    (None, "insufficient_quota", S.QUOTA_EXHAUSTED),
    (404, "", S.MODEL_UNAVAILABLE),
    (400, "The model `llama-9000` does not exist", S.MODEL_UNAVAILABLE),
    (400, "model_decommissioned: model has been decommissioned", S.MODEL_UNAVAILABLE),
    (None, "Incorrect API key provided", S.AUTH_FAILED),
    (500, "", S.UNAVAILABLE),
    (503, "overloaded", S.UNAVAILABLE),
    (408, "", S.UNAVAILABLE),
    (None, "timed out", S.UNAVAILABLE),
    (None, "Connection refused", S.UNAVAILABLE),
    (400, "bad request", S.DEGRADED),
    (None, "", S.UNAVAILABLE),
])
def test_classification_table(code, msg, expected):
    a = classify_provider_error("p", http_status=code, message=msg)
    assert a.status == expected, (code, msg, a)
    assert a.needs_credential_action == (expected in (S.QUOTA_EXHAUSTED, S.AUTH_FAILED))
    assert a.retryable == (expected in (S.DEGRADED, S.UNAVAILABLE))


@pytest.mark.parametrize("weird", [object(), "429", -1, 10**9, "abc"])
def test_classifier_never_raises(weird):
    a = classify_provider_error("p", http_status=weird, message=weird)  # type: ignore[arg-type]
    assert isinstance(a.status, S)


def test_detail_is_redacted_and_truncated():
    a = classify_provider_error("p", http_status=401, message=f"invalid key {FAKE_KEY} " + "x" * 1000)
    assert FAKE_KEY not in a.detail and "[REDACTED:" in a.detail and len(a.detail) <= 300
    assert FAKE_KEY not in json.dumps(a.to_dict())


def test_all_seven_states_exist():
    assert {s.value for s in S} == {"READY", "DEGRADED", "UNAVAILABLE", "QUOTA_EXHAUSTED",
                                    "AUTH_FAILED", "MODEL_UNAVAILABLE", "BLOCKED"}


# ------------------------------------------- existing AIResponse mapping ---

@pytest.mark.parametrize("resp,expected", [
    (AIResponse("p", "m", "OK", content="hi"), S.READY),
    (AIResponse("p", "m", "NO_KEY", error_state={"kind": "no_key", "detail": "X is not set"}), S.AUTH_FAILED),
    (AIResponse("p", "m", "SKIPPED_PAID"), S.BLOCKED),
    (AIResponse("p", "m", "DOWN", http_status=429, error_state={"kind": "http_error", "detail": "429"}), S.QUOTA_EXHAUSTED),
    (AIResponse("p", "m", "DOWN", http_status=401, error_state={"kind": "http_error", "detail": "401"}), S.AUTH_FAILED),
    (AIResponse("p", "m", "DOWN", error_state={"kind": "empty_completion"}), S.DEGRADED),
    (AIResponse("p", "m", "DOWN", error_state={"kind": "URLError", "detail": "timed out"}), S.UNAVAILABLE),
])
def test_classify_existing_envelope(resp, expected):
    assert classify_ai_response(resp).status == expected


def _http_error_transport(code, body=b""):
    def t(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, code, "err", {}, io.BytesIO(body))
    return t


@pytest.mark.parametrize("code,expected", [(429, S.QUOTA_EXHAUSTED), (401, S.AUTH_FAILED),
                                           (403, S.AUTH_FAILED), (503, S.UNAVAILABLE), (404, S.MODEL_UNAVAILABLE)])
def test_real_aiclient_with_fake_transport(monkeypatch, code, expected):
    monkeypatch.setenv("FAKE_PROVIDER_KEY", FAKE_KEY)
    c = AIClient("fake", {"kind": "openai_compatible", "base_url": "https://fake.invalid/v1",
                          "model": "m", "key_env": "FAKE_PROVIDER_KEY"}, transport=_http_error_transport(code))
    resp = c.ask([{"role": "user", "content": "hi"}])
    a = classify_ai_response(resp)
    assert a.status == expected
    assert FAKE_KEY not in json.dumps(resp.to_dict()) and FAKE_KEY not in json.dumps(a.to_dict())


# ---------------------------------------------------- outage never crashes ---

@pytest.mark.parametrize("exc,expected", [
    (ConnectionRefusedError("Connection refused"), S.UNAVAILABLE),
    (TimeoutError("timed out"), S.UNAVAILABLE),
    (RuntimeError("boom"), S.UNAVAILABLE),
    (urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None), S.QUOTA_EXHAUSTED),
    (urllib.error.HTTPError("u", 401, "Unauthorized", {}, None), S.AUTH_FAILED),
    (KeyError("x"), S.UNAVAILABLE),
])
def test_safe_call_converts_exceptions(exc, expected):
    def call():
        raise exc
    result, a = safe_provider_call("p", call)
    assert result is None and a.status == expected


def test_safe_call_ready_and_empty():
    assert safe_provider_call("p", lambda: "answer")[1].status == S.READY
    assert safe_provider_call("p", lambda: "")[1].status == S.DEGRADED


# ------------------------------------------------------- credential store ---

def test_secret_value_never_leaks():
    v = SecretValue(FAKE_KEY)
    for s in (repr(v), str(v), f"{v}", f"{v!r}", "%s" % v, json.dumps({"k": str(v)})):
        assert FAKE_KEY not in s
    with pytest.raises(TypeError):
        pickle.dumps(v)
    with pytest.raises(AttributeError):
        v._v = "x"  # type: ignore[misc]
    assert v.reveal() == FAKE_KEY


def test_interface_has_no_raw_getter_and_stores_conform():
    for store in (NullCredentialStore(), FakeCredentialStore()):
        assert isinstance(store, CredentialStore)
        assert not any(n in dir(store) for n in ("get_secret", "get_key", "read", "write", "set_secret"))
    assert NullCredentialStore().has_credential(CredentialRef("groq")) is None


def test_windows_backend_is_design_only_and_touches_nothing():
    w = WindowsCredentialManagerStore()
    with pytest.raises(NotImplementedError, match="DESIGN_ONLY"):
        w.has_credential(CredentialRef("groq"))
    with pytest.raises(NotImplementedError, match="DESIGN_ONLY"):
        w.get_secret(CredentialRef("groq"))
    req = w.request_new_credential(CredentialRef("groq"), "QUOTA_EXHAUSTED", "M1")
    assert req.target == "AHOS/ai/groq"
    src = (ROOT / "architecture" / "ai" / "credential_store.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not imported & {"ctypes", "keyring", "win32cred", "subprocess", "os", "winreg"}


def test_target_name_is_sanitised():
    assert CredentialRef("../evil name;rm").target == "AHOS/ai/.._evil_name_rm"


def test_persian_message_contract():
    m = persian_new_key_message("groq_llama", "AHOS/ai/groq_llama", "QUOTA_EXHAUSTED", "GM-09")
    assert "سهمیه" in m and "Windows Credential Manager" in m and "AHOS/ai/groq_llama" in m
    assert "GM-09" in m and "از صفر" in m and "PAPER_ONLY" in m
    assert "در چت" in m                     # tells the owner NOT to paste the key in chat
    assert "کلید" in persian_new_key_message("x", "AHOS/ai/x", "AUTH_FAILED")


# --------------------------------------------------- ledger integration ---

@pytest.fixture()
def led(tmp_path):
    L = MissionLedger(tmp_path / "ml.jsonl")
    L.start("GM-09", phase="P3", task="ask AI", agent="engineering:grok")
    L.checkpoint("GM-09", {"step": 4, "pending": ["q5"]})
    return L


def test_quota_pauses_with_checkpoint_and_persian_request(led):
    store = FakeCredentialStore()
    def call():
        raise urllib.error.HTTPError("u", 429, f"insufficient_quota for key {FAKE_KEY}", {}, None)
    out = guard_provider_call(led, "GM-09", "groq_llama", call, credential_store=store)
    assert out.mission_status == "PAUSED" and out.assessment.status == S.QUOTA_EXHAUSTED
    assert out.owner_message_fa and "سهمیه" in out.owner_message_fa
    st = led.latest("GM-09")
    assert st["CHECKPOINT"] == {"step": 4, "pending": ["q5"]}
    assert st["AI_PROVIDER"]["status"] == "QUOTA_EXHAUSTED"
    assert "AHOS/ai/groq_llama" in st["NEXT_ACTION"]
    assert len(store.requests) == 1
    assert FAKE_KEY not in led.path.read_text(encoding="utf-8")
    # resume after the owner stores a new key: checkpoint intact, never from zero
    r = led.resume("GM-09")
    assert r["CHECKPOINT"] == {"step": 4, "pending": ["q5"]}
    out2 = guard_provider_call(led, "GM-09", "groq_llama", lambda: "ok", credential_store=store)
    assert out2.mission_status == "RUNNING" and out2.result == "ok"
    assert led.verify()["verdict"] == "CHAIN_INTACT"


def test_auth_failed_pauses(led):
    out = guard_provider_call(led, "GM-09", "openai", lambda: AIResponse(
        "openai", "m", "DOWN", http_status=401, error_state={"kind": "http_error", "detail": "401"}))
    assert out.mission_status == "PAUSED" and "نامعتبر" in out.owner_message_fa


def test_no_key_pauses_with_no_key_message(led):
    out = guard_provider_call(led, "GM-09", "groq", lambda: AIResponse("groq", "m", "NO_KEY"))
    assert out.mission_status == "PAUSED" and "ثبت نشده" in out.owner_message_fa


@pytest.mark.parametrize("exc", [ConnectionRefusedError("refused"), TimeoutError("timed out"),
                                 RuntimeError("provider exploded")])
def test_outage_waits_for_ai_without_crashing(led, exc):
    def call():
        raise exc
    out = guard_provider_call(led, "GM-09", "ollama_local", call)
    assert out.mission_status == "WAIT_FOR_AI" and out.owner_message_fa is None
    assert led.latest("GM-09")["CHECKPOINT"] == {"step": 4, "pending": ["q5"]}


def test_repeated_failures_stay_consistent(led):
    for _ in range(3):
        guard_provider_call(led, "GM-09", "p", lambda: (_ for _ in ()).throw(TimeoutError("t")))
    out = guard_provider_call(led, "GM-09", "p", lambda: (_ for _ in ()).throw(
        urllib.error.HTTPError("u", 402, "Payment Required", {}, None)))
    assert out.mission_status == "PAUSED"
    assert led.verify()["verdict"] == "CHAIN_INTACT"


def test_unknown_mission_is_an_error_not_a_silent_start(tmp_path):
    L = MissionLedger(tmp_path / "x.jsonl")
    with pytest.raises(LookupError):
        guard_provider_call(L, "NOPE", "p", lambda: "ok")
    assert not L.path.exists()


# --------------------------------------------------------- non-authority ---

def test_gm09_modules_import_no_trading_or_decision_code():
    for name in ("provider_status.py", "credential_store.py", "mission_guard.py"):
        tree = ast.parse((ROOT / "architecture" / "ai" / name).read_text(encoding="utf-8"))
        mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        bad = [m for m in mods if m.split(".")[0] in {"discovery", "paper_trading", "engine", "telegram_ai"}
               or m.startswith(("architecture.decision", "architecture.risk", "architecture.positions"))]
        assert bad == [], (name, bad)


def test_existing_clients_module_unchanged_behaviour():
    # GM-09 is additive: AIClient still returns NO_KEY without attempting a call.
    c = AIClient("x", {"key_env": "AHOS_TEST_ABSENT_KEY_ENV", "base_url": "https://fake.invalid"})
    assert c.ask([{"role": "user", "content": "q"}]).availability == "NO_KEY"
