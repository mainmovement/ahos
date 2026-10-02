#!/usr/bin/env python3
"""GM-05 - single source of truth for the gateway URL + read-only diagnosis.

Self-tests, not independent verification. No .env is edited by any code
under test; loopback probes only.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import gateway_port as gp  # noqa: E402
from scripts.operator_validation_gate import _resolve_gateway, g2_gateway  # noqa: E402

D3000 = "http://127.0.0.1:3000/api/chat"


# ---------------------------------------------------------------- resolution --

def test_default_stays_3000():
    r = gp.resolve_gateway({})
    assert r["url"] == D3000 and r["port"] == 3000 and r["source"] == "DEFAULT"


def test_port_override_builds_loopback_url():
    r = gp.resolve_gateway({"AHOS_GATEWAY_PORT": "3500"})
    assert r["url"] == "http://127.0.0.1:3500/api/chat"
    assert r["source"] == "AHOS_GATEWAY_PORT"


def test_full_url_wins_over_port_and_warns_on_disagreement():
    r = gp.resolve_gateway({"AHOS_GATEWAY_URL": D3000, "AHOS_GATEWAY_PORT": "3500"})
    assert r["url"] == D3000 and r["source"] == "AHOS_GATEWAY_URL"
    assert "AHOS_GATEWAY_PORT_DISAGREES_WITH_URL" in r["warnings"]


def test_blank_url_is_treated_as_unset():
    assert gp.resolve_gateway({"AHOS_GATEWAY_URL": "   "})["source"] == "DEFAULT"


@pytest.mark.parametrize("bad", ["abc", "0", "65536", "-1", "3500x", "35 00"])
def test_invalid_port_override_is_ignored_with_warning(bad):
    r = gp.resolve_gateway({"AHOS_GATEWAY_PORT": bad})
    assert r["url"] == D3000
    assert "AHOS_GATEWAY_PORT_INVALID_IGNORED" in r["warnings"]


def test_unparseable_url_is_reported_not_rewritten():
    r = gp.resolve_gateway({"AHOS_GATEWAY_URL": "not a url"})
    assert r["url"] == "not a url" and r["port"] is None
    assert "AHOS_GATEWAY_URL_UNPARSEABLE" in r["warnings"]


def test_url_without_port_uses_scheme_default():
    assert gp.resolve_gateway({"AHOS_GATEWAY_URL": "https://example.invalid/api/chat"})["port"] == 443


def test_candidate_ports_parsing():
    assert gp.candidate_ports({}) == (3000, 3500)
    assert gp.candidate_ports({"AHOS_GATEWAY_CANDIDATE_PORTS": "4000, x ,4001"}) == (4000, 4001)
    assert gp.candidate_ports({"AHOS_GATEWAY_CANDIDATE_PORTS": "x,y"}) == (3000, 3500)


# ----------------------------------------------------------------- diagnosis --

def _probe(listening: set[int]):
    calls: list[tuple[str, int]] = []

    def probe(host, port):
        calls.append((host, port))
        return port in listening
    probe.calls = calls  # type: ignore[attr-defined]
    return probe


def test_diagnose_configured_port_listening():
    d = gp.diagnose({}, probe=_probe({3000}))
    assert d["verdict"] == "CONFIGURED_PORT_LISTENING"
    assert d["configured_listening"] is True


def test_diagnose_reports_configured_port_no_listener_with_alternative():
    # Today's laptop reality: .env -> 3000, gateway on 3500.
    d = gp.diagnose({"AHOS_GATEWAY_URL": D3000}, probe=_probe({3500}))
    assert d["verdict"] == "CONFIGURED_PORT_NO_LISTENER"
    assert d["listening_candidates"] == [3500]
    assert "OWNER_ACTION" in d["hint"] and "does not change .env" in d["hint"]


def test_diagnose_no_gateway():
    d = gp.diagnose({}, probe=_probe(set()))
    assert d["verdict"] == "NO_GATEWAY_LISTENING"


def test_diagnose_never_probes_non_loopback():
    def boom(host, port):
        raise AssertionError("must not probe non-loopback hosts")
    d = gp.diagnose({"AHOS_GATEWAY_URL": "http://10.0.0.5:3000/api/chat"}, probe=boom)
    assert d["verdict"] == "NON_LOCAL_URL_NOT_PROBED"


def test_diagnose_only_probes_loopback_host():
    p = _probe(set())
    gp.diagnose({"AHOS_GATEWAY_URL": "http://localhost:3000/api/chat"}, probe=p)
    assert {h for h, _ in p.calls} == {"127.0.0.1"}


def test_port_listening_real_socket():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        assert gp.port_listening("127.0.0.1", port) is True
    finally:
        srv.close()
    assert gp.port_listening("127.0.0.1", port) is False


# ------------------------------------------------------------------ env file --

def test_read_env_file_returns_only_gateway_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "TELEGRAM_BOT_TOKEN=fake-not-real\nAHOS_WEB_API_TOKEN=fake\n"
        "AHOS_GATEWAY_URL=\"http://127.0.0.1:3500/api/chat\"\n# AHOS_GATEWAY_PORT=1\n",
        encoding="utf-8")
    vals = gp.read_env_file(env)
    assert vals == {"AHOS_GATEWAY_URL": "http://127.0.0.1:3500/api/chat"}


def test_cli_is_read_only(tmp_path):
    env = tmp_path / ".env"
    env.write_text("AHOS_GATEWAY_PORT=3500\n", encoding="utf-8")
    before = env.read_bytes()
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gateway_port.py"), "--url-only", "--env-file", str(env)],
        capture_output=True, text=True, timeout=60, cwd=str(tmp_path),
        env={"PATH": "", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")},
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "http://127.0.0.1:3500/api/chat"
    assert env.read_bytes() == before
    js = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gateway_port.py"), "--json", "--env-file", str(env)],
        capture_output=True, text=True, timeout=60, cwd=str(tmp_path),
    )
    assert json.loads(js.stdout)["schema"] == "ahos.gateway_port_diagnosis.v1"
    assert env.read_bytes() == before


# ------------------------------------------------------------ gate wiring --

def test_gate_resolver_honours_port_override(monkeypatch):
    monkeypatch.delenv("AHOS_GATEWAY_URL", raising=False)
    monkeypatch.setenv("AHOS_GATEWAY_PORT", "3500")
    assert _resolve_gateway()["url"] == "http://127.0.0.1:3500/api/chat"
    monkeypatch.delenv("AHOS_GATEWAY_PORT")
    assert _resolve_gateway()["url"] == D3000


def test_g2_uses_resolved_url_when_gateway_url_empty(monkeypatch):
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("AHOS_GATEWAY_URL", "")
    monkeypatch.setenv("AHOS_GATEWAY_PORT", "3517")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        raise urllib.error.URLError("refused")
    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
            mock.patch("scripts.gateway_port.port_listening", return_value=False):
        g = g2_gateway(skip_network=False)
    assert seen["url"] == "http://127.0.0.1:3517/api/chat"
    assert g["status"] != "PASS"
    diag = g["gateway_port_diagnosis"]
    assert diag["verdict"] == "NO_GATEWAY_LISTENING"


def test_g2_failure_carries_no_listener_diagnosis_without_changing_status(monkeypatch):
    monkeypatch.setenv("AHOS_WEB_API_TOKEN", "probe-token")
    monkeypatch.setenv("AHOS_GATEWAY_URL", D3000)
    monkeypatch.delenv("AHOS_GATEWAY_PORT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")), \
            mock.patch("scripts.gateway_port.port_listening", side_effect=lambda h, p: p == 3500):
        g = g2_gateway(skip_network=False)
    assert g["status"] in {"FAIL", "BLOCKED", "NOT_VERIFIED"}
    assert g["gateway_port_diagnosis"]["verdict"] == "CONFIGURED_PORT_NO_LISTENER"
    assert g["gateway_port_diagnosis"]["listening_candidates"] == [3500]


def test_g2_skip_network_has_no_diagnosis():
    g = g2_gateway(skip_network=True)
    assert "gateway_port_diagnosis" not in g


# ------------------------------------------------------------- ps1 wiring --

def test_windows_gate_ps1_uses_single_resolution_and_keeps_encoding():
    raw = (ROOT / "scripts" / "windows_run_operator_gate.ps1").read_bytes()
    text = raw.decode("utf-8-sig")
    assert "gateway_port.py" in text and "--url-only" in text
    assert '"AHOS_GATEWAY_PORT"' in text
    # The old unconditional hard-coded assignment is gone.
    assert '$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"' not in text
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")   # CRLF only (.gitattributes)
