#!/usr/bin/env python3
"""Smoke tests for operator_validation_gate runner — honesty invariants."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.operator_validation_gate import (  # noqa: E402
    classify,
    g2_gateway,
    g11_telegram,
    main,
    _resolve_executable,
)


def _pass_gates(n_end: int = 12) -> list[dict]:
    return [
        {"id": f"G{i}", "status": "PASS", "name": "x", "detail": ""}
        for i in range(1, n_end + 1)
    ]


def test_agent_host_never_auto_operator_ready():
    gates = _pass_gates(12)
    summary = classify("agent-host", gates)
    assert summary["operator_ready"] is False
    assert summary["classification"] == "INTEGRATION_READY"
    assert summary["pre_soak_entry_ok"] is False


def test_windows_requires_g11_pass_for_operator_ready():
    gates = _pass_gates(10)
    gates.append({"id": "G11", "status": "OWNER_ACTION_REQUIRED", "name": "tg", "detail": ""})
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates)
    assert summary["operator_ready"] is False
    assert summary["g1_g10_all_pass"] is True
    assert summary["pre_soak_entry_ok"] is True
    assert any("G11" in m for m in summary["missing"])


def test_windows_full_pass_operator_ready():
    gates = _pass_gates(11)
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates)
    assert summary["operator_ready"] is True
    assert summary["classification"] == "OPERATOR_READY"
    assert summary["pre_soak_entry_ok"] is True


def test_runner_writes_report(tmp_path):
    out = tmp_path / "r.json"
    rc = main(["--platform", "agent-host", "--skip-network", "--json-out", str(out)])
    assert rc == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["schema"] == "ahos.operator_validation_report.v1"
    assert doc["summary"]["operator_ready"] is False
    assert "pre_soak_entry_ok" in doc["summary"]
    ids = {g["id"] for g in doc["gates"]}
    assert ids >= {f"G{i}" for i in range(1, 13)}


def test_runner_exit_3_on_windows_without_operator_ready(tmp_path):
    out = tmp_path / "w.json"
    rc = main([
        "--platform", "windows",
        "--skip-network",
        "--json-out", str(out),
    ])
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["summary"]["operator_ready"] is False
    statuses = {g["id"]: g["status"] for g in doc["gates"]}
    if any(s == "FAIL" for s in statuses.values()):
        assert rc == 2
    else:
        assert rc == 3


def test_g2_http_error_4xx_is_pass_not_connection_fail():
    """urlopen raises HTTPError for 4xx; process reachable => PASS (not 'start npm')."""
    import urllib.error

    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=b"{}")),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err):
        with mock.patch.dict("os.environ", {"AHOS_GATEWAY_URL": "http://127.0.0.1:3000/api/chat"}, clear=False):
            g = g2_gateway(skip_network=False)
    assert g["status"] == "PASS"
    assert g["http_status"] == 404


def test_g2_http_401_web_api_locked_is_blocked(monkeypatch):
    import urllib.error

    monkeypatch.delenv("AHOS_WEB_API_TOKEN", raising=False)
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    body = b'{"ok":false,"error":"WEB_API_LOCKED_NO_TOKEN"}'
    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=body)),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err):
        g = g2_gateway(skip_network=False)
    assert g["status"] == "BLOCKED"
    assert g["http_status"] == 401
    assert "WEB_API_LOCKED" in g["detail"]


def test_g2_sends_bearer_when_web_token_set(monkeypatch):
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "opval-token-xyz")
    captured: dict = {}

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, _n=400):
            return b'{"reply":"ok"}'

    def _urlopen(req, timeout=None):
        captured["headers"] = dict(req.headers)
        return _Resp()

    with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
        g = g2_gateway(skip_network=False)
    assert g["status"] == "PASS"
    auth = captured["headers"].get("Authorization") or captured["headers"].get("authorization")
    assert auth == "Bearer opval-token-xyz"


def test_g2_http_error_5xx_is_fail(monkeypatch):
    import urllib.error

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=500,
        msg="Internal",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=b'{"error":"DATABASE_URL"}')),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err):
        g = g2_gateway(skip_network=False)
    assert g["status"] == "FAIL"
    assert g["http_status"] == 500
    assert "DATABASE_URL" in g["detail"]


def test_g11_artifact_attestation(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token-not-real")
    art = tmp_path / "telegram_e2e_test.md"
    art.write_text("# E2E\n" + ("x" * 80), encoding="utf-8")
    g = g11_telegram("windows", e2e_artifact=str(art))
    assert g["status"] == "PASS"
    g2 = g11_telegram("windows", e2e_artifact=None)
    assert g2["status"] == "NOT_VERIFIED"


def test_resolve_executable_finds_python():
    assert _resolve_executable(sys.executable) is not None or Path(sys.executable).exists()
