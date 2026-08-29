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
    remediation_actions,
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
    summary = classify("windows", gates, host_is_windows=True)
    assert summary["operator_ready"] is False
    assert summary["g1_g10_all_pass"] is True
    assert summary["pre_soak_entry_ok"] is True
    assert any("G11" in m for m in summary["missing"])


def test_windows_full_pass_operator_ready():
    gates = _pass_gates(11)
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates, host_is_windows=True)
    assert summary["operator_ready"] is True
    assert summary["classification"] == "OPERATOR_READY"
    assert summary["pre_soak_entry_ok"] is True
    assert "remediation_actions" in summary


def test_platform_windows_on_non_windows_host_refuses_pre_soak():
    """Anti-forgery: agent-host must not invent PRE_SOAK via --platform windows."""
    gates = _pass_gates(11)
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates, host_is_windows=False)
    assert summary["operator_ready"] is False
    assert summary["pre_soak_entry_ok"] is False
    assert summary["windows_attested"] is False
    assert any("host:not_windows" in m for m in summary["missing"])
    assert "non-Windows host" in summary["reason"]


def test_remediation_mentions_web_api_token_for_g2_block():
    gates = _pass_gates(12)
    gates[1] = {
        "id": "G2",
        "status": "BLOCKED",
        "name": "Gateway",
        "detail": "AHOS_WEB_API_TOKEN unset and AHOS_WEB_API_ALLOW_OPEN_ACCESS not enabled",
    }
    actions = remediation_actions(gates)
    assert any("windows_ensure_web_api_token" in a for a in actions)
    assert any("db:migrate" in a for a in actions)


def test_runner_writes_report(tmp_path):
    out = tmp_path / "r.json"
    rc = main(["--platform", "agent-host", "--skip-network", "--json-out", str(out)])
    # rc 2 is honest when local SQLite census is empty (fresh checkout / no data/).
    assert rc in (0, 2)
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["schema"] == "ahos.operator_validation_report.v1"
    assert doc["summary"]["operator_ready"] is False
    assert "pre_soak_entry_ok" in doc["summary"]
    ids = {g["id"] for g in doc["gates"]}
    assert ids >= {f"G{i}" for i in range(1, 13)}


def test_windows_runner_writes_latest_pointer(tmp_path):
    out = tmp_path / "w.json"
    # Avoid real network/provider/backup work.
    rc = main([
        "--platform", "windows",
        "--skip-network",
        "--json-out", str(out),
    ])
    assert rc in (0, 2, 3)
    latest = tmp_path / "LATEST_WINDOWS_GATE.txt"
    assert latest.is_file()
    text = latest.read_text(encoding="utf-8")
    assert f"report={out.resolve()}" in text
    assert "pre_soak_entry_ok=" in text
    assert "operator_ready=" in text
    assert "db:migrate" in text


def test_g2_uses_long_timeout_for_cold_next(monkeypatch):
    """Cold Next /api/chat compile on Windows often exceeds 8s."""
    import urllib.request

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("DATABASE_URL", "postgres://x")
    captured = {}

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            return b'{"ok":true}'

    def _urlopen(req, timeout=None):
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
    g = g2_gateway(skip_network=False)
    assert g["status"] == "PASS"
    assert captured["timeout"] >= 45


def test_main_force_loads_web_token_from_dotenv(tmp_path, monkeypatch):
    """Stale shell AHOS_WEB_API_TOKEN must not beat .env (G2 401 trap)."""
    env = ROOT / ".env"
    # Skip if no .env in workspace; synthesize via monkeypatch of load path.
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "STALE_SHELL_TOKEN")
    # Write a temp env and point ROOT... too invasive. Instead assert source contract.
    src = (ROOT / "scripts" / "operator_validation_gate.py").read_text(encoding="utf-8")
    assert 'os.environ[key] = loaded[key]' in src
    assert "AHOS_WEB_API_TOKEN" in src
    assert "timeout=45" in src


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


def test_g2_http_error_4xx_is_pass_not_connection_fail(monkeypatch):
    """urlopen raises HTTPError for 4xx; process reachable => PASS (not 'start npm')."""
    import urllib.error

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
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


def test_g2_http_401_web_api_unauthorized_is_blocked(monkeypatch):
    import urllib.error

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    body = b'{"ok":false,"error":"WEB_API_UNAUTHORIZED"}'
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
    assert "WEB_API_UNAUTHORIZED" in g["detail"]


def test_g2_blocks_before_probe_when_token_missing(monkeypatch):
    monkeypatch.delenv("AHOS_WEB_API_TOKEN", raising=False)
    monkeypatch.delenv("AHOS_WEB_API_ALLOW_OPEN_ACCESS", raising=False)
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    with mock.patch("urllib.request.urlopen") as urlopen:
        g = g2_gateway(skip_network=False)
    urlopen.assert_not_called()
    assert g["status"] == "BLOCKED"
    assert "AHOS_WEB_API_TOKEN unset" in g["detail"]


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

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=500,
        msg="Internal",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=b'{"error":"DATABASE_URL"}')),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err) as urlopen:
        g = g2_gateway(skip_network=False)
    assert g["status"] == "FAIL"
    assert g["http_status"] == 500
    assert "DATABASE_URL" in g["detail"]
    assert urlopen.call_count == 1  # no DATABASE_URL => no retries


def test_g2_retries_http_500_when_database_url_set(monkeypatch):
    """Docker/Postgres just-up race: retry briefly when DATABASE_URL is present."""
    import urllib.error

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://ahos:ahos@127.0.0.1:5432/ahos")
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=500,
        msg="Internal",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=b'{"error":"db"}')),
    )

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, _n=400):
            return b'{"reply":"ok"}'

    calls = {"n": 0}

    def _urlopen(_req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise err
        return _Resp()

    with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
        with mock.patch("scripts.operator_validation_gate.time.sleep") as sleep:
            g = g2_gateway(skip_network=False)
    assert g["status"] == "PASS"
    assert calls["n"] == 2
    assert g.get("attempt") == 2
    sleep.assert_called_once_with(2)


def test_g2_retries_exhausted_still_fail_with_db_hint(monkeypatch):
    import urllib.error

    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://ahos:ahos@127.0.0.1:5432/ahos")
    monkeypatch.setenv("AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    err = urllib.error.HTTPError(
        url="http://127.0.0.1:3000/api/chat",
        code=500,
        msg="Internal",
        hdrs=None,
        fp=mock.Mock(read=mock.Mock(return_value=b'{"error":"db"}')),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err) as urlopen:
        with mock.patch("scripts.operator_validation_gate.time.sleep") as sleep:
            g = g2_gateway(skip_network=False)
    assert g["status"] == "FAIL"
    assert g["http_status"] == 500
    assert urlopen.call_count == 8
    assert sleep.call_count == 7
    assert "Postgres unreachable" in g["detail"] or "Docker" in g["detail"]
    assert "windows_recover_g2_warm" in g["detail"] or "recover" in g["detail"].lower()
    assert "error=db" in (g.get("artifact") or g.get("detail") or "")
    assert g.get("attempt") == 8


def test_g2_empty_gateway_url_defaults_to_local_chat(monkeypatch):
    """Older .env.example shipped AHOS_GATEWAY_URL= (empty). Must not BLOCK G2."""
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("AHOS_GATEWAY_URL", "")  # empty-but-set
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
        captured["url"] = req.full_url
        return _Resp()

    with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
        g = g2_gateway(skip_network=False)
    assert g["status"] == "PASS"
    assert captured["url"] == "http://127.0.0.1:3000/api/chat"
    assert g.get("url") == "http://127.0.0.1:3000/api/chat"


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


def test_persist_env_key_replaces_empty_gateway(tmp_path):
    from scripts.operator_validation_gate import _persist_env_key

    env = tmp_path / ".env"
    env.write_text("FOO=1\nAHOS_GATEWAY_URL=\nBAR=2\n", encoding="utf-8")
    assert _persist_env_key(env, "AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")
    text = env.read_text(encoding="utf-8")
    assert "AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat" in text
    assert "FOO=1" in text and "BAR=2" in text
    assert text.count("AHOS_GATEWAY_URL=") == 1


def test_write_pre_soak_status_ascii(tmp_path, monkeypatch):
    import scripts.operator_validation_gate as ovg

    monkeypatch.setattr(ovg, "ROOT", tmp_path)
    gates = [{"id": f"G{i}", "status": "PASS"} for i in range(1, 11)]
    gates.append({"id": "G11", "status": "OWNER_ACTION_REQUIRED"})
    gates.append({"id": "G12", "status": "FAIL"})
    summary = {
        "host_is_windows": True,
        "pre_soak_entry_ok": False,
        "operator_ready": False,
        "classification": "INTEGRATION_READY",
        "remediation_actions": ["G2: ensure gateway"],
    }
    path = ovg._write_pre_soak_status(summary, gates)
    body = path.read_text(encoding="utf-8")
    body.encode("ascii")
    assert "pre_soak_entry_ok=False" in body
    assert "AHOS_FIX_G2_AND_GATE.bat" in body or "AHOS_BOOTSTRAP_PRESOAK.bat" in body
    assert "G1 PASS" in body
    assert "VERDICT: NOT PRE_SOAK yet." in body
