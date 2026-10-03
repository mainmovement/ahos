"""M11: the one-click launcher — orchestrator logic, process kit, and the
control-plane bridge that routes START/STOP/STATUS through the existing
operator surface.

These are unit tests of the *decision logic*: idempotency, ordered rollback on
a critical failure, honest reporting of an occupied port, secret-free env
resolution, and shortcut/icon generation. They never start a real server, so
the reality ladder for this artefact caps at TESTED; the real
start → status → stop evidence lives under reports/launcher/.
"""
from __future__ import annotations

import json
import socket
import struct
import sys
import threading
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import launcher.components as C  # noqa: E402
import launcher.persian as P  # noqa: E402
import launcher.processkit as pk  # noqa: E402
from launcher.control_plane_bridge import LauncherControlPlane, build_config  # noqa: E402
from launcher.make_icon import build as build_icon  # noqa: E402
from launcher.orchestrator import AhosOrchestrator  # noqa: E402
from launcher.shortcuts import shortcut_specs  # noqa: E402


# ------------------------------------------------------------------- persian ---
class TestPersian:
    def test_fa_digits(self):
        assert P.fa(3000) == "۳۰۰۰"
        assert P.fa("127.0.0.1") == "۱۲۷.۰.۰.۱"

    def test_error_names_failure_and_action(self):
        msg = P.error("venv", action=P.ACTIONS["no_venv"])
        assert "محیط پایتون" in msg
        assert "install_windows.ps1" in msg

    def test_error_falls_back_to_generic_action(self):
        assert P.error("engine") == P.error("engine", action=P.ACTIONS["unknown"])

    def test_component_labels_cover_all_five(self):
        for name in C.START_ORDER:
            assert P.component_label(name) != name


# ---------------------------------------------------------------- processkit ---
class TestProcessKit:
    def test_pid_roundtrip(self, tmp_path):
        assert pk.read_pid(tmp_path, "engine") is None
        pk.write_pid(tmp_path, "engine", 4242, {"cmd": "x"})
        info = pk.read_pid(tmp_path, "engine")
        assert info["pid"] == 4242 and info["cmd"] == "x"
        pk.clear_pid(tmp_path, "engine")
        assert pk.read_pid(tmp_path, "engine") is None

    def test_clear_pid_is_idempotent(self, tmp_path):
        pk.clear_pid(tmp_path, "engine")  # no file: must not raise

    def test_pid_alive_rejects_garbage(self):
        assert pk.pid_alive(0) is False
        assert pk.pid_alive(-1) is False

    def test_port_in_use(self, tmp_path):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            assert pk.port_in_use("127.0.0.1", port) is True
            assert pk.port_in_use("127.0.0.1", port + 1) is False
        finally:
            srv.close()

    def test_http_ok(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            ok, code, _ = pk.http_ok(f"http://127.0.0.1:{port}/", timeout=3)
            assert ok and code == 200
            ok, _, _ = pk.http_ok(f"http://127.0.0.1:{port + 1}/", timeout=1)
            assert ok is False
        finally:
            srv.shutdown()
            srv.server_close()


# ---------------------------------------------------------------- components ---
class TestComponents:
    @pytest.mark.parametrize("url, scheme, host, port", [
        ("", "none", None, None),
        ("pglite:/tmp/ahos-pg", "pglite", "127.0.0.1", 5432),
        ("postgres://u:p@127.0.0.1:5432/ahos", "postgres", "127.0.0.1", 5432),
        ("not-a-url", "unknown", None, None),
    ])
    def test_database_target_scheme(self, url, scheme, host, port):
        env = {"DATABASE_URL": url}
        t = C.database_target(env)
        assert t["scheme"] == scheme and t["host"] == host and t["port"] == port

    def test_database_target_never_returns_credentials(self):
        t = C.database_target({"DATABASE_URL": "postgres://user:SEKRIT@db:5432/x"})
        dumped = json.dumps(t)
        assert "SEKRIT" not in dumped
        assert "user" not in dumped

    def test_load_repo_env_only_reads_launcher_keys(self, tmp_path):
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "# comment\n"
            "DATABASE_URL=postgres://localhost:5432/ahos\n"
            'AHOS_GATEWAY_PORT="3100"\n'
            "TELEGRAM_BOT_TOKEN=0000000000:AAAA-secret-token\n"
            "GEMINI_API_KEY=AIza-secret\n",
            encoding="utf-8")
        env = C.load_repo_env(tmp_path, {"DATABASE_URL": "from-env"})
        assert env["DATABASE_URL"] == "from-env"  # process env wins
        assert env["AHOS_GATEWAY_PORT"] == "3100"
        assert "TELEGRAM_BOT_TOKEN" not in env
        assert "GEMINI_API_KEY" not in env

    def test_build_stale_detects_newer_sources(self, tmp_path):
        import time
        old = tmp_path / ".next" / "BUILD_ID"
        old.parent.mkdir(parents=True)
        old.write_text("old")
        (tmp_path / "app").mkdir()
        fresh = tmp_path / "app" / "page.tsx"
        time.sleep(0.05)
        fresh.write_text("export default () => null")
        stale, why = C.build_stale(tmp_path)
        assert stale is True
        assert "source files newer" in why

    def test_build_current(self, tmp_path):
        old = tmp_path / ".next" / "BUILD_ID"
        old.parent.mkdir(parents=True)
        old.write_text("fresh")
        stale, _ = C.build_stale(tmp_path)
        assert stale is False

    def test_gateway_command_modes(self, tmp_path):
        assert "start" in C.gateway_command(tmp_path, "prod")[2]
        assert "dev" in C.gateway_command(tmp_path, "dev")[2]

    def test_engine_command_is_paper_and_local(self):
        py = C.venv_python(ROOT) or sys.executable
        cmd = C.engine_command(Path(py))
        assert "--daemon" in cmd and "--evidence-source" in cmd

    def test_child_env_hardens_engine(self):
        env = C.child_env(ROOT, {})
        assert env["AHOS_PAPER_ONLY"] == "1"
        assert env["AHOS_TELEGRAM_POLL"] == "0"
        assert env["PYTHONIOENCODING"] == "utf-8"

    def test_preflight_rejects_wrong_root(self, tmp_path):
        pf = C.preflight(tmp_path, {})
        assert pf.ok is False
        names = {c["name"] for c in pf.checks if not c["ok"]}
        assert "repo" in names

    def test_preflight_passes_on_real_repo(self):
        pf = C.preflight(ROOT, C.load_repo_env(ROOT, {}))
        assert pf.ok is True


# -------------------------------------------------------------- orchestrator ---
def make_orchestrator(tmp_path, **kw):
    return AhosOrchestrator(
        ROOT,
        env=C.load_repo_env(ROOT, {}),
        state_dir=tmp_path / "state",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        ledger_path=tmp_path / "ledger.sqlite",
        emit=lambda _line: None,
        open_dashboard=False,
        **kw)


class TestOrchestrator:
    def test_gateway_port_busy_is_reported_not_hidden(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: True)
        res = orch._start_component("gateway")
        assert res.status == C.UNHEALTHY
        assert res.detail == "foreign_busy"
        assert "AHOS_GATEWAY_PORT" in P.ACTIONS["gateway_port_busy"]

    def test_idempotent_when_our_pid_is_alive(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        pk.write_pid(orch.state_dir, "engine", 4242, {"cmd": "x"})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        res = orch._start_component("engine")
        assert res.status == C.HEALTHY
        assert "idempotent" in res.detail
        assert res.pid == 4242

    def test_critical_failure_rolls_back_and_halts(self, tmp_path, monkeypatch):
        """A dead engine must not leave a half-booted stack behind: the gateway
        and bot we just spawned are stopped, a service already running before us
        is left alone."""
        orch = make_orchestrator(tmp_path, health_wait={"engine": 1.5})
        calls = {"stopped": []}
        monkeypatch.setattr(orch, "_stop_components",
                            lambda order: calls["stopped"].append(list(order)))
        # gateway + telegram freshly started and healthy, engine dead
        def fake_start(name):
            fresh = name in ("gateway", "telegram")
            return C.ComponentResult(
                name, C.UNHEALTHY if name == "engine" else C.HEALTHY, "simulated",
                fresh=fresh)
        monkeypatch.setattr(orch, "_start_component", fake_start)
        report = orch.start()
        assert report["overall"] == "FAILED"
        assert calls["stopped"] == [["telegram", "gateway"]]  # reverse boot order
        assert report["failure"] == "engine"

    def test_critical_failure_leaves_preexisting_services_alone(self, tmp_path, monkeypatch):
        """A service that was already healthy before this run is NOT rolled back."""
        orch = make_orchestrator(tmp_path, health_wait={"engine": 1.5})
        calls = {"stopped": []}
        monkeypatch.setattr(orch, "_stop_components",
                            lambda order: calls["stopped"].append(list(order)))
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.UNAVAILABLE if name == "engine" else C.HEALTHY,
            "already running (idempotent)"))
        report = orch.start()
        assert report["overall"] == "FAILED"
        assert calls["stopped"] == [[]]

    def test_optional_failure_degrades_but_starts(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.UNAVAILABLE if name == "gateway" else C.HEALTHY, "simulated"))
        monkeypatch.setattr("launcher.processkit.open_url", lambda url: True)
        report = orch.start()
        assert report["overall"] == "DEGRADED"
        assert report["components"]["gateway"]["status"] == C.UNAVAILABLE
        assert report["components"]["engine"]["status"] == C.HEALTHY

    def test_start_reports_already_running(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "already running (idempotent)"))
        report = orch.start()
        assert report["overall"] == "ONLINE"

    def test_status_writes_latest_and_archived_reports(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_component_probe",
                            lambda name, **kw: (C.HEALTHY, "simulated"))
        report = orch.status()
        latest = orch.report_dir / "status.json"
        assert latest.exists()
        assert json.loads(latest.read_text(encoding="utf-8")) == report
        archives = list(orch.report_dir.glob("status_*.json"))
        assert len(archives) == 1
        assert set(report["components"]) == set(C.START_ORDER)
        assert report["paper_only"] is True

    def test_skip_excludes_a_component(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path, skip={"telegram"})
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["components"]["telegram"]["status"] == "SKIPPED"

    def test_stores_command_uses_existing_bootstrap(self):
        cmd = C.stores_command(Path(sys.executable))
        assert "init_databases.py" in cmd[-1] or any("init_databases" in a for a in cmd)


# ------------------------------------------------------- control plane bridge ---
class TestControlPlaneBridge:
    def test_config_topology_matches_boot_order(self):
        cfg = build_config()
        comps = {c["component"]: c for c in cfg["infrastructure"]}
        assert {c["component"] for c in cfg["infrastructure"]} == set(C.START_ORDER)
        assert comps["engine"]["boot_class"] == "CRITICAL"
        assert comps["gateway"]["boot_class"] == "OPTIONAL"
        assert comps["engine"]["requires"] == ["stores"]

    def _plane(self, tmp_path, statuses):
        def make(name, status):
            return lambda now: (status, f"simulated {name}")
        return LauncherControlPlane(
            {name: make(name, st) for name, st in statuses.items()},
            ledger_path=tmp_path / "ledger.sqlite")

    def test_start_then_status_then_idempotent_replay(self, tmp_path):
        healthy = {n: C.HEALTHY for n in C.START_ORDER}
        plane = self._plane(tmp_path, healthy)
        first = plane.start(now=1000.0)
        assert first["status"] == "SYSTEM_ONLINE"
        status = plane.status(now=1001.0)
        assert status["system"] == "SYSTEM_ONLINE"
        second = plane.start(now=1002.0)
        assert second["idempotent_replay"] is True

    def test_critical_unhealthy_halts(self, tmp_path):
        statuses = {n: C.HEALTHY for n in C.START_ORDER}
        statuses["engine"] = C.UNAVAILABLE
        plane = self._plane(tmp_path, statuses)
        assert plane.start(now=1000.0)["status"] == "SAFE_HALT"

    def test_missing_prober_never_fabricated(self, tmp_path):
        plane = LauncherControlPlane({}, ledger_path=tmp_path / "ledger.sqlite")
        status, _why = plane.cp.probe("engine", now=1.0)
        assert status == "UNKNOWN"


# ------------------------------------------------------------- icon + shortcuts ---
class TestIconAndShortcuts:
    def test_icon_is_parseable(self, tmp_path):
        path = build_icon(tmp_path / "ahos.ico", sizes=(32, 16))
        data = path.read_bytes()
        assert struct.unpack_from("<HHH", data, 0) == (0, 1, 2)
        blobs = []
        for i in range(2):
            w, h, _c, _r, _p, _b, size, off = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
            blobs.append((w, h, data[off:off + size]))
        for w, h, blob in blobs:
            assert blob[:8] == b"\x89PNG\r\n\x1a\n"
            # the image data must actually decode
            pos, idat, hdr = 8, b"", b""
            while pos < len(blob):
                ln = struct.unpack_from(">I", blob, pos)[0]
                kind = blob[pos + 4:pos + 8]
                pos += 8
                if kind == b"IHDR":
                    hdr = blob[pos:pos + ln]
                if kind == b"IDAT":
                    idat += blob[pos:pos + ln]
                pos += ln + 4
            iw, ih = struct.unpack_from(">II", hdr)
            assert (iw, ih) == (w, h)
            assert len(zlib.decompress(idat)) == ih * (1 + iw * 3)

    def test_shortcut_specs_target_the_console_wrapper(self):
        specs = shortcut_specs(ROOT, ROOT / "launcher" / "ahos.ico", user="sniper")
        assert [s["name"] for s in specs] == ["AHOS.lnk", "AHOS Stop.lnk", "AHOS Status.lnk"]
        for s in specs:
            assert s["target_path"].endswith("powershell.exe")
            assert "ahos.ps1" in s["arguments"]
            assert s["icon_location"].endswith("ahos.ico,0")
            assert "ExecutionPolicy Bypass" in s["arguments"]
        assert "-Action start" in specs[0]["arguments"]
        assert "-Action stop" in specs[1]["arguments"]
        assert "-Action status" in specs[2]["arguments"]


# --------------------------------------------------------------------- cli ---
class TestCli:
    def test_preflight_bad_root_exits_nonzero(self, monkeypatch, capsys):
        from launcher.__main__ import main
        rc = main(["--root", str(ROOT / "launcher"), "preflight"])
        assert rc == 1
