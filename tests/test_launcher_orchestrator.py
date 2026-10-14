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

import os
import json
import socket
import struct
import sys
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import launcher.components as C  # noqa: E402
import launcher.persian as P  # noqa: E402
import launcher.processkit as pk  # noqa: E402
from launcher.smoke import _parse_report  # noqa: E402
from launcher.control_plane_bridge import LauncherControlPlane, build_config  # noqa: E402
from launcher.make_icon import build as build_icon  # noqa: E402
from launcher.orchestrator import AhosOrchestrator, _optional_action  # noqa: E402
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

    def test_action_placeholders_are_substituted(self):
        """An unsubstitated {port} would reach the owner literally."""
        busy = P.error("generic", action=P.ACTIONS["gateway_port_busy"], port=P.fa(3450))
        assert "{port}" not in busy and "۳۴۵۰" in busy
        down = P.error("generic", action=P.ACTIONS["gateway_down"], sec=P.fa(120))
        assert "{sec}" not in down and "۱۲۰" in down

    def test_action_without_placeholders_is_untouched(self):
        assert P.ACTIONS["telegram_missing_token"] in \
            P.error("generic", action=P.ACTIONS["telegram_missing_token"])

    def test_component_labels_cover_all_five(self):
        for name in C.START_ORDER:
            assert P.component_label(name) != name

    def test_panel_and_status_lexicons_cover_every_state(self):
        """Every status the orchestrator can emit has a Persian rendering, so the
        dashboard never falls back to an English enum the owner reads as noise."""
        for status in (C.HEALTHY, C.UNHEALTHY, C.UNAVAILABLE, C.UNKNOWN):
            assert status in P.STATUS_FA
        for name in C.START_ORDER:
            assert name in P.PANEL["labels"]

    def test_age_fa_is_coarse_and_persian(self):
        assert P.age_fa(0) == "۰ ثانیه"
        assert P.age_fa(59) == "۵۹ ثانیه"
        assert P.age_fa(120) == "۲ دقیقه"
        assert P.age_fa(5400) == "۱ ساعت"
        assert P.age_fa(90000) == "۱ روز"
        assert P.age_fa(None) == "۰ ثانیه"

    def test_dashboard_panel_lexicon_mirrors_the_persian_module(self):
        """CommandCenter.tsx cannot import Python, so it keeps its own copy of the
        labels/status lexicon. Left ungoverned the two drift apart silently and the
        owner reads a mix of Persian and Latin in the same panel; this pins the copy
        to launcher/persian.py."""
        import re
        cc = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")

        def flat_object(name: str) -> dict:
            start = cc.index(f"const {name}: Record<string, string> = {{")
            block = cc[start:cc.index("};", start)]
            return dict(re.findall(r'(\w+):\s*"([^"]*)"', block))

        assert flat_object("LAUNCHER_LABELS_FA") == P.PANEL["labels"]
        # STOPPED is both a component status and an overall one; STATUS_FA wins so
        # the component rows (the ones the owner scans) stay single-source.
        assert flat_object("LAUNCHER_STATUS_FA") == {**P.HEALTH_FA, **P.STATUS_FA}


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

    def test_break_immunity_handler_only_swallows_c_and_break(self):
        """R12: the handler must claim CTRL_C and CTRL_BREAK (return True) and
        nothing else, so a CLOSE/LOGOFF event still reaches the default handler."""
        assert pk._swallow_console_break(pk.CTRL_C_EVENT) is True
        assert pk._swallow_console_break(pk.CTRL_BREAK_EVENT) is True
        assert pk._swallow_console_break(5) is False

    def test_break_immunity_reports_unavailable_without_kernel32(self, monkeypatch):
        """No kernel32 (POSIX, or a stubbed build) means no console events to
        swallow: the call reports False instead of raising."""
        monkeypatch.setattr(pk, "_KERNEL32", None)
        monkeypatch.setattr(pk, "_CONSOLE_HANDLER", None)
        assert pk.arm_console_break_immunity() is False
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

    @pytest.mark.parametrize("url, data_dir", [
        ("pglite:G:/robat/ahos_runtime/pglite/ahos", "G:/robat/ahos_runtime/pglite/ahos"),
        ("pglite:/G:/somewhere/db", "G:/somewhere/db"),
        ("pglite://G:/somewhere/db", "G:/somewhere/db"),
        # POSIX absolute must stay absolute (regression: became cwd-relative).
        ("pglite:/tmp/ahos-pg", "/tmp/ahos-pg"),
        ("pglite:///tmp/ahos-pg", "/tmp/ahos-pg"),
        ("pglite:data/pglite", "data/pglite"),
    ])
    def test_database_target_pglite_data_dir_matches_ts_client(self, url, data_dir):
        assert C.database_target({"DATABASE_URL": url})["data_dir"] == data_dir

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

    def test_gateway_command_modes(self, tmp_path, monkeypatch):
        # The argv is this checkout's own next CLI — the script `npm run start`
        # resolves `next` to — so stand it up rather than depending on a checkout.
        cli = tmp_path / "node_modules" / "next" / "dist" / "bin" / "next"
        cli.parent.mkdir(parents=True, exist_ok=True)
        cli.write_text("#!/usr/bin/env node\n")
        monkeypatch.setattr(C, "node_executable", lambda: r"C:\Program Files\nodejs\node.exe")
        prod = C.gateway_command(tmp_path, "prod")
        dev = C.gateway_command(tmp_path, "dev")
        assert prod == [r"C:\Program Files\nodejs\node.exe", str(cli),
                        "start", "--hostname", "127.0.0.1"]
        assert dev[:3] == [r"C:\Program Files\nodejs\node.exe", str(cli), "dev"]
        # the package.json scripts' loopback bind is reproduced exactly
        assert dev[3:5] == ["--hostname", "127.0.0.1"]

    def test_gateway_command_is_empty_without_node_or_the_cli(self, tmp_path, monkeypatch):
        """``[]`` is reported UNAVAILABLE by the caller. Falling back to npm here
        would re-introduce the ``cmd /c npm`` wrapper whose command line carries
        nothing identifying — the exact defect M11.3 removes."""
        monkeypatch.setattr(C, "node_executable", lambda: None)
        assert C.gateway_command(tmp_path, "prod") == []
        monkeypatch.setattr(C, "node_executable", lambda: r"C:\Program Files\nodejs\node.exe")
        assert C.gateway_command(tmp_path, "prod") == []  # no node_modules/next

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

    def test_probe_stores_accepts_str_paths(self):
        """config.paths helpers return str; probe_stores must not assume Path."""
        status, _detail = C.probe_stores(0.0)
        assert status in (C.HEALTHY, C.UNAVAILABLE)

    def test_probe_gateway_probes_the_status_route_not_the_page(self, monkeypatch):
        """``/`` is the heaviest compile in the app; probing it made a gateway that
        had been serving API traffic for minutes read UNAVAILABLE. The probe must
        hit the route the dashboard polls."""
        seen = {}

        def _fake(url, timeout=5.0):
            seen["url"] = url
            return True, 200, "OK"

        monkeypatch.setattr(C.pk, "http_ok", _fake)
        C.probe_gateway("http://127.0.0.1:8300/", 0.0)
        assert seen["url"] == "http://127.0.0.1:8300/api/launcher"

    def test_probe_gateway_counts_a_401_as_listening(self, monkeypatch):
        # The status route demands a bearer token; an unauthenticated probe gets
        # 401 and that still proves the server is up.
        monkeypatch.setattr(C.pk, "http_ok", lambda url, timeout=5.0: (True, 401, ""))
        status, detail = C.probe_gateway("http://127.0.0.1:8300/", 0.0)
        assert status == C.HEALTHY

    def test_probe_gateway_refused_connection_is_unavailable(self, monkeypatch):
        monkeypatch.setattr(C.pk, "http_ok",
                            lambda url, timeout=5.0: (False, None, "TimeoutError"))
        status, detail = C.probe_gateway("http://127.0.0.1:8300/", 0.0)
        assert status == C.UNAVAILABLE
        assert "api/launcher" in detail

    def test_probe_gateway_rejects_a_404(self, monkeypatch):
        """A 404 means a Next server *is* up but this route is not registered in
        the server holding the port: a stale server from an older build or another
        checkout. Counting it HEALTHY made the panel announce ONLINE while every
        control returned 404, and a restart spent its whole budget waiting for an
        audit line the dead route could never write. ``http_ok`` must not paper
        over it here."""
        monkeypatch.setattr(C.pk, "http_ok",
                            lambda url, timeout=5.0: (True, 404, "Not Found"))
        status, detail = C.probe_gateway("http://127.0.0.1:8300/", 0.0)
        assert status == C.UNAVAILABLE
        assert "404" in detail
        assert "api/launcher" in detail

    def test_engine_heartbeat_age_takes_a_str_path(self, tmp_path):
        # A nonexistent file must yield None, never an AttributeError.
        assert C.engine_heartbeat_age(str(tmp_path / "nope.sqlite")) is None

    def test_engine_stale_heartbeat_during_our_own_cycle_is_healthy(self, monkeypatch):
        """The scheduler beats once per cycle; a long observation cycle ages the
        heartbeat legitimately. A RUNNING cycle begun by this pid is evidence
        the engine is working, not hung."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        now = time.time()
        # heartbeat 600s old, but a cycle we started 60s ago is still running
        healthy = C.probe_engine({"pid": 4242}, marker="engine",
                                 heartbeat_age=600.0,
                                 cycle=("RUNNING", now - 60.0),
                                 pid_started_ts=now - 600.0)
        assert healthy[0] == C.HEALTHY
        assert "in scheduler cycle" in healthy[1]

    def test_engine_stale_heartbeat_from_a_killed_daemon_is_not_healthy(self, monkeypatch):
        """A RUNNING row left behind by a previous (force-killed) daemon must
        not pass a freshly-spawned engine as healthy."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        now = time.time()
        # this engine started 30s ago, yet a cycle was "running" 120s ago — that
        # row belongs to the daemon we replaced, not to us.
        verdict = C.probe_engine({"pid": 4242}, marker="engine",
                                 heartbeat_age=3600.0,
                                 cycle=("RUNNING", now - 120.0),
                                 pid_started_ts=now - 30.0)
        assert verdict[0] == C.UNHEALTHY
        assert "stale" in verdict[1]

    def test_engine_wedged_cycle_is_reported_unhealthy(self, monkeypatch):
        """A RUNNING cycle that has outlived the cycle budget is a stall, not
        busy work."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        verdict = C.probe_engine({"pid": 4242}, marker="engine",
                                 heartbeat_age=7200.0,
                                 cycle=("RUNNING", 1000.0 + 60.0),
                                 pid_started_ts=1000.0,
                                 max_cycle_sec=60.0)
        assert verdict[0] == C.UNHEALTHY
        assert "wedged" in verdict[1]

    def test_engine_no_heartbeat_is_still_booting(self, monkeypatch):
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        verdict = C.probe_engine({"pid": 4242}, marker="engine",
                                 heartbeat_age=None,
                                 cycle=("RUNNING", time.time() - 10.0))
        assert verdict[0] == C.UNHEALTHY
        assert "still booting" in verdict[1]

    def test_engine_cycle_state_reads_the_scheduler_table(self, tmp_path):
        import sqlite3
        db = tmp_path / "ahos_local.sqlite"
        conn = sqlite3.connect(db)
        conn.executescript(
            "CREATE TABLE scheduler_runs(run_id TEXT, schedule_name TEXT, "
            "started_ts REAL, status TEXT);"
            "INSERT INTO scheduler_runs VALUES('r2','DAEMON_CYCLE',200.0,'RUNNING');"
            "INSERT INTO scheduler_runs VALUES('r1','DAEMON_CYCLE',100.0,'SUCCESS');")
        conn.commit()
        conn.close()
        assert C.engine_cycle_state(str(db)) == ("RUNNING", 200.0)
        assert C.engine_cycle_state(str(tmp_path / "nope.sqlite")) == (None, None)


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

    def test_gateway_port_we_cannot_bind_is_reported_without_spawning(self, tmp_path, monkeypatch):
        """A foreign listener that never ``accept`` makes the connect probe hang,
        so ``port_in_use`` reads the port as free while ``bind`` still fails. The
        launcher used to spawn the gateway anyway and spend its whole health
        budget on a listen error; it must classify the port as unusable first."""
        orch = make_orchestrator(tmp_path)
        spawned = []
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: False)
        monkeypatch.setattr("launcher.processkit.can_bind",
                            lambda host, port: False)
        monkeypatch.setattr(orch, "_start_process",
                            lambda name: spawned.append(name) or C.ComponentResult(
                                name, C.UNAVAILABLE, "should not have spawned"))
        res = orch._start_component("gateway")
        assert spawned == []
        assert res.status == C.UNHEALTHY
        assert res.detail == "port_not_bindable"
        # The owner-facing action names the OS reservation, not a rival program:
        # "occupied by another program" would be a guess, and UNKNOWN > fabricated.
        assert P.ACTIONS["gateway_port_reserved"] != P.ACTIONS["gateway_port_busy"]
        assert "Hyper-V" in P.ACTIONS["gateway_port_reserved"]
        assert _optional_action("gateway", res) == "gateway_port_reserved"

    def test_gateway_port_we_can_bind_still_spawns(self, tmp_path, monkeypatch):
        """The new bind check must not shadow the normal path: a port nobody holds
        and the OS releases is still spawned into."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: False)
        monkeypatch.setattr("launcher.processkit.can_bind", lambda host, port: True)
        res = orch._start_component("gateway")
        assert res.detail != "port_not_bindable"

    def test_idempotent_when_our_pid_is_alive(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)
        pk.write_pid(orch.state_dir, "engine", 4242, {"cmd": "x"})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        res = orch._start_component("engine")
        assert res.status == C.HEALTHY
        assert "idempotent" in res.detail
        assert res.pid == 4242

    def test_our_live_gateway_is_ours_not_foreign(self, tmp_path, monkeypatch):
        """The gateway used to be launched as ``cmd /c "npm run start --silent"``,
        whose command line carried no identifying substring, so a second
        ``start`` read our own live gateway as a foreign listener:
        ``foreign_busy``, a DEGRADED report, and a Persian line telling the owner
        some *other* program held the port. The gateway is now spawned as
        ``node <next cli> start``, whose own argv carries the marker like every
        other component, so a live recorded pid is recognised as ours through the
        marker and replayed idempotently (M11.3)."""
        orch = make_orchestrator(tmp_path)
        cli = C.next_cli(orch.root)
        assert cli is not None, "node_modules/next must be installed for this suite"
        # Get-CimInstance quotes the interpreter and the script; the marker must
        # survive that quoting, which is what the old cmdline-equality fallback
        # could not be trusted to do.
        live_cmd = (f'"C:\\Program Files\\nodejs\\node.exe" "{cli}" '
                    "start --hostname 127.0.0.1")
        assert orch.marker("gateway").lower() in live_cmd.lower()
        pk.write_pid(orch.state_dir, "gateway", 7332,
                     {"cmd": live_cmd, "port": 8300, "host": "127.0.0.1"})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        res = orch._start_component("gateway")
        assert res.status == C.HEALTHY
        assert "idempotent" in res.detail
        assert res.pid == 7332

    def test_reissued_gateway_pid_is_not_adopted(self, tmp_path, monkeypatch):
        """Windows re-issues pids, so a live pid is not evidence the recorded
        gateway is still that process: a foreign program handed our old pid must
        read as foreign, not as ours. The marker, not the pid number, decides."""
        orch = make_orchestrator(tmp_path)
        pk.write_pid(orch.state_dir, "gateway", 7332,
                     {"cmd": "node next start", "port": 8300})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: False)
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: True)
        res = orch._start_component("gateway")
        assert res.status == C.UNHEALTHY
        assert res.detail == "foreign_busy"

    def test_stale_gateway_404_is_down_not_ours(self, tmp_path, monkeypatch):
        """A gateway we spawned can outlive the app it was built from: a stale
        server from an older build keeps holding the port and 404s every route
        the dashboard needs. Its pid is still recorded and still ours, so every
        later start replayed it as "already running" and reported ONLINE while
        every control was dead. Past its boot budget it must be probed like
        anything else, and a route that is not served reads as ``down``."""
        now = 1_000_000.0
        orch = make_orchestrator(tmp_path, clock=lambda: now)
        live_cmd = 'node "G:\\robat\\ahos\\node_modules\\next\\dist\\bin\\next" start'
        pk.write_pid(orch.state_dir, "gateway", 7332,
                     {"cmd": live_cmd, "port": 8300, "host": "127.0.0.1",
                      "started_ts": now - 1000})  # past the 240s boot budget
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: True)
        monkeypatch.setattr("launcher.components.probe_gateway",
                            lambda url, t: (C.UNAVAILABLE, "answers 404"))
        assert orch.component_state("gateway") == "down"

    def test_booting_gateway_is_trusted_on_its_pid_record(self, tmp_path, monkeypatch):
        """The boot budget is not a loophole for the stale-gateway probe: a
        gateway that just bound has not compiled the launcher route yet, so the
        probe can legitimately fail for the first seconds. A young pid record
        that is still ours is evidence the gateway is ours — without this grace
        every start would spawn a second gateway while the first was booting."""
        now = 1_000_000.0
        orch = make_orchestrator(tmp_path, clock=lambda: now)
        live_cmd = 'node "G:\\robat\\ahos\\node_modules\\next\\dist\\bin\\next" start'
        pk.write_pid(orch.state_dir, "gateway", 7332,
                     {"cmd": live_cmd, "port": 8300, "host": "127.0.0.1",
                      "started_ts": now - 5})  # still inside the boot budget
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: True)
        monkeypatch.setattr("launcher.components.probe_gateway",
                            lambda url, t: (C.UNAVAILABLE, "route not compiled yet"))
        assert orch.component_state("gateway") == "ours_running"

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

    def test_start_adopts_our_live_gateway_port(self, tmp_path, monkeypatch):
        """The configured port is unbindable on this host and our own gateway is
        already serving on a candidate port. ``select_port`` cannot re-bind that
        port (our own listener holds it) and used to fall back to the configured
        port, advertising a URL nothing listens on while the dashboard was
        reachable elsewhere — the browser opened a closed port.

        Regression observed live: a second ``launcher start`` reported
        ``dashboard_url http://127.0.0.1:3000/`` (``CONFIGURED_UNUSABLE_KEPT_ANYWAY``)
        while the gateway served on 8300, so every probe and the browser missed.
        """
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(
            "launcher.components.select_gateway",
            lambda env: {"host": "127.0.0.1", "port": 3000, "url": "http://127.0.0.1:3000/api/chat",
                         "source": "AHOS_GATEWAY_URL", "configured_port": 3000,
                         "chosen_via": "CONFIGURED_UNUSABLE_KEPT_ANYWAY",
                         "tried": [], "notes": ["none bindable"], "warnings": ["NO_BINDABLE_PORT"]})
        # our gateway, live on the port we chose last time
        pk.write_pid(orch.state_dir, "gateway", 4242,
                     {"cmd": "next dev", "marker": orch.marker("gateway"), "port": 8300})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        # The recorded gateway must still be alive to adopt it; 4242 is a dummy,
        # so say it is alive and report the command line we recorded, rather than
        # depending on Windows having that pid open at the moment the suite runs.
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0: "next dev")
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: port == 8300)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "already running (idempotent)"))
        report = orch.start()
        assert report["gateway_port"] == 8300
        assert report["dashboard_url"] == "http://127.0.0.1:8300/"
        assert report["gateway_chosen_via"] == "ADOPTED_OUR_LIVE_LISTENER"

    def test_start_does_not_adopt_a_dead_pid_record(self, tmp_path, monkeypatch):
        """A pid record left behind by a crashed gateway must not be adopted:
        the port could since have been taken by another program."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(
            "launcher.components.select_gateway",
            lambda env: {"host": "127.0.0.1", "port": 3000, "url": "http://127.0.0.1:3000/api/chat",
                         "source": "AHOS_GATEWAY_URL", "configured_port": 3000,
                         "chosen_via": "CONFIGURED_UNUSABLE_KEPT_ANYWAY",
                         "tried": [], "notes": [], "warnings": []})
        pk.write_pid(orch.state_dir, "gateway", 4242,
                     {"cmd": "next dev", "marker": orch.marker("gateway"), "port": 8300})
        # the pid is no longer ours
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: False)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["gateway_port"] == 3000
        assert report["gateway_chosen_via"] == "CONFIGURED_UNUSABLE_KEPT_ANYWAY"

    def test_start_does_not_adopt_silent_listener(self, tmp_path, monkeypatch):
        """Our pid is alive but nothing accepts on the recorded port (it is
        mid-shutdown): adopting it would send the browser at a half-closed
        listener."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(
            "launcher.components.select_gateway",
            lambda env: {"host": "127.0.0.1", "port": 3000, "url": "http://127.0.0.1:3000/api/chat",
                         "source": "AHOS_GATEWAY_URL", "configured_port": 3000,
                         "chosen_via": "CONFIGURED_UNUSABLE_KEPT_ANYWAY",
                         "tried": [], "notes": [], "warnings": []})
        pk.write_pid(orch.state_dir, "gateway", 4242,
                     {"cmd": "next dev", "marker": orch.marker("gateway"), "port": 8300})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        monkeypatch.setattr("launcher.processkit.port_in_use",
                            lambda host, port, timeout=0.6: False)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["gateway_port"] == 3000

    def test_status_writes_latest_but_no_archive(self, tmp_path, monkeypatch):
        """A status poll refreshes `status.json` and writes NO timestamped
        archive (e5).

        Regression: the dashboard polls status every few seconds, and each poll
        wrote an immutable archive entry too — 51 receipts in 40 minutes, none of
        them a receipt. Archives are for state-changing actions only.
        """
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_component_probe",
                            lambda name, **kw: (C.HEALTHY, "simulated"))
        report = orch.status()
        latest = orch.report_dir / "status.json"
        assert latest.exists()
        assert json.loads(latest.read_text(encoding="utf-8")) == report
        assert not list(orch.report_dir.glob("status_*.json"))
        assert set(report["components"]) == set(C.START_ORDER)
        assert report["paper_only"] is True

    def test_status_archives_are_bounded(self, tmp_path, monkeypatch):
        """Only the newest ``MAX_STATUS_ARCHIVES`` receipts survive (e5).

        Without pruning, state-changing actions would bury the interesting
        receipts under the dashboard's poll cadence from the other direction:
        hundreds of identical start receipts, none prunable by hand.
        """
        orch = make_orchestrator(tmp_path)
        n = orch.MAX_STATUS_ARCHIVES + 5
        for i in range(n):
            # fixed sortable names: lexicographic order == chronological order
            (orch.report_dir / f"status_20260101T0000{i:02d}Z.json").write_text(
                "{}", encoding="utf-8")
        orch._prune_archives()
        kept = sorted(orch.report_dir.glob("status_*.json"))
        assert len(kept) == orch.MAX_STATUS_ARCHIVES
        # the newest survive, the oldest are dropped
        assert kept[0].name == f"status_20260101T0000{n - orch.MAX_STATUS_ARCHIVES:02d}Z.json"
        assert kept[-1].name == f"status_20260101T0000{n - 1:02d}Z.json"
        # an unreadable/foreign file in the directory must not raise
        (orch.report_dir / "status_19700101T000000Z.json").write_text("x", encoding="utf-8")
        orch._prune_archives()
        assert not (orch.report_dir / "status_19700101T000000Z.json").exists()

    def test_status_optional_down_is_degraded_not_down(self, tmp_path, monkeypatch):
        """The optional gateway being absent must not read DOWN.

        Regression: status ranked UNAVAILABLE below UNHEALTHY and mapped it to
        DOWN, so on this host — where port 3000 cannot be bound — `AHOS Status`
        reported a fully working stack as DOWN and exited 1 while the engine ran
        cycles. `start` already called this DEGRADED; status now matches it.
        """
        orch = make_orchestrator(tmp_path)

        def probe(name, **kw):
            return (C.UNAVAILABLE, "gateway not answering") if name == "gateway" \
                else (C.HEALTHY, "simulated")
        monkeypatch.setattr(orch, "_component_probe", probe)
        report = orch.status()
        assert report["overall"] == "DEGRADED"
        assert report["components"]["engine"]["status"] == C.HEALTHY

    def test_status_critical_down_is_down(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path)

        def probe(name, **kw):
            return (C.UNAVAILABLE, "no pid record") if name in C.CRITICAL \
                else (C.HEALTHY, "simulated")
        monkeypatch.setattr(orch, "_component_probe", probe)
        assert orch.status()["overall"] == "DOWN"

    def test_report_advertises_the_port_children_were_given(self, tmp_path, monkeypatch):
        """Scope (d): on a host where the configured port is Windows-reserved the
        launcher picks a bindable candidate. The report must advertise *that*
        port — sending the owner to the configured one would send them to a dead
        page — and every child must be handed the same address."""
        orch = make_orchestrator(tmp_path)
        selected = {"host": "127.0.0.1", "port": 8300,
                    "url": "http://127.0.0.1:8300/api/chat",
                    "source": "candidate", "configured_port": 3000,
                    "chosen_via": "CANDIDATE_BINDABLE",
                    "tried": [3000, 8300], "notes": [], "warnings": []}
        monkeypatch.setattr(C, "select_gateway", lambda env: selected)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["gateway_port"] == 8300
        assert report["gateway_chosen_via"] == "CANDIDATE_BINDABLE"
        assert report["dashboard_url"] == "http://127.0.0.1:8300/"
        env = orch._child_env()
        assert env["AHOS_GATEWAY_URL"] == "http://127.0.0.1:8300/api/chat"
        assert env["PORT"] == "8300"

    _SELECTED_8300 = {"host": "127.0.0.1", "port": 8300,
                      "url": "http://127.0.0.1:8300/api/chat",
                      "source": "candidate", "configured_port": 3000,
                      "chosen_via": "CANDIDATE_BINDABLE",
                      "tried": [3000, 8300], "notes": [], "warnings": []}

    def test_selected_port_survives_into_a_new_process_status(self, tmp_path, monkeypatch):
        """The dashboard's Status button and `ahos.ps1 status` run in a *new*
        process. If the start-time choice (fallback 8300) is not recorded, that
        process falls back to the configured 3000, probes a dead port, reports the
        gateway UNAVAILABLE and writes a dashboard_url that sends the owner to a
        dead page -- the very failure scope (d) exists to prevent."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(C, "select_gateway", lambda env: dict(self._SELECTED_8300))
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        orch.start()
        # Our gateway is still the live process the pid file names.
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        pk.write_pid(orch.state_dir, "gateway", 4242, {"cmd": "x"})
        later = make_orchestrator(tmp_path)  # fresh process, same state dir
        assert later.dashboard_url() == "http://127.0.0.1:8300/"
        monkeypatch.setattr(later, "_component_probe", lambda name: (C.HEALTHY, "ok"))
        assert later.status()["gateway_port"] == 8300
        assert later._child_env()["PORT"] == "8300"

    def test_second_start_reuses_our_running_gateway_port(self, tmp_path, monkeypatch):
        """Second start while our gateway still listens on the fallback: the
        configured port is still reserved and the fallback is now *busy* (ours),
        so a fresh select would walk on to the next candidate and hand the
        children a port nobody serves. The recorded choice must win."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(C, "select_gateway", lambda env: dict(self._SELECTED_8300))
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        orch.start()
        pk.write_pid(orch.state_dir, "gateway", 4242, {"cmd": "x"})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        moved = dict(self._SELECTED_8300, port=3100, url="http://127.0.0.1:3100/api/chat")
        monkeypatch.setattr(C, "select_gateway", lambda env: moved)
        again = make_orchestrator(tmp_path)
        monkeypatch.setattr(again, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "already running (idempotent)"))
        report = again.start()
        assert report["gateway_port"] == 8300
        assert report["dashboard_url"] == "http://127.0.0.1:8300/"

    def test_recorded_port_ignored_when_our_gateway_is_gone(self, tmp_path, monkeypatch):
        """A stale record must never pin a dead port: once our gateway process is
        gone the pure resolver applies again."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(C, "select_gateway", lambda env: dict(self._SELECTED_8300))
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        orch.start()
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: False)
        later = make_orchestrator(tmp_path)
        assert later.gateway.get("port") == C.resolve_gateway(later.env).get("port")

    def test_configured_port_that_binds_is_kept(self, tmp_path, monkeypatch):
        """The common case: the configured port binds, so nothing is substituted
        and the report says so."""
        orch = make_orchestrator(tmp_path)
        selected = {"host": "127.0.0.1", "port": 3000,
                    "url": "http://127.0.0.1:3000/api/chat",
                    "source": "env", "configured_port": 3000,
                    "chosen_via": "CONFIGURED_BINDABLE",
                    "tried": [3000], "notes": [], "warnings": []}
        monkeypatch.setattr(C, "select_gateway", lambda env: selected)
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["gateway_port"] == 3000
        assert report["gateway_chosen_via"] == "CONFIGURED_BINDABLE"

    def test_stop_reports_stopped_components_without_crashing(self, tmp_path, monkeypatch):
        """Regression: stop passed plain dicts into the report builder, which
        read ``res.status`` and raised AttributeError — so every real stop did
        its job and *then* exited 1, which the smoke scored as a failure."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_stop_components", lambda order: {
            "engine": {"pid": 5768, "how": "force", "secs": 0.6},
            "telegram": {"pid": 14544, "how": "ctrl-break", "secs": 0.4},
        })
        monkeypatch.setattr(orch, "_sweep_ours", lambda: [])
        monkeypatch.setattr(orch, "_control_plane",
                            lambda results: type("CP", (), {
                                "stop": lambda self: {"status": "SYSTEM_OFFLINE"}})())
        report = orch.stop()
        assert report["overall"] == "STOPPED"
        assert report["components"]["engine"]["status"] == "STOPPED"
        assert report["components"]["engine"]["detail"] == "stopped (force, 0.6s)"
        assert report["swept"] == []

    def test_skip_excludes_a_component(self, tmp_path, monkeypatch):
        orch = make_orchestrator(tmp_path, skip={"telegram"})
        monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(
            name, C.HEALTHY, "simulated"))
        report = orch.start()
        assert report["components"]["telegram"]["status"] == "SKIPPED"

    def test_stores_command_uses_existing_bootstrap(self):
        cmd = C.stores_command(Path(sys.executable))
        assert "init_databases.py" in cmd[-1] or any("init_databases" in a for a in cmd)

    # --------------------------------------------------------- port lifecycle --
    def _stopped_orch(self, tmp_path, monkeypatch):
        """An orchestrator whose stop path touches no real processes."""
        orch = make_orchestrator(tmp_path)
        monkeypatch.setattr(orch, "_stop_components", lambda order: {})
        monkeypatch.setattr(orch, "_sweep_ours", lambda: [])
        monkeypatch.setattr(orch, "_control_plane",
                            lambda results: type("CP", (), {
                                "stop": lambda self: {"status": "SYSTEM_OFFLINE"}})())
        # _wait_port_free's real sleep has no place in a unit test.
        monkeypatch.setattr("launcher.orchestrator.time.sleep", lambda _s: None)
        return orch

    def test_restart_waits_for_the_port_to_be_released(self, tmp_path, monkeypatch):
        """Regression (R12): restart used to ``sleep(1.0)`` between stop and
        start, but the killed gateway's socket is released around 1.1s after
        ``taskkill /F`` returns, so the new gateway raced it and came back
        ``port_not_bindable`` — DEGRADED, no gateway. Restart now polls the port
        and starts only once a real bind succeeds."""
        orch = self._stopped_orch(tmp_path, monkeypatch)
        pk.write_pid(orch.state_dir, "gateway", 4242,
                     {"port": 8300, "host": "127.0.0.1",
                      "cmd": "node next start"})
        monkeypatch.setattr(orch, "_reclaim_gateway_port",
                            lambda host, port: None)
        remaining = {"n": 2}

        def fake_bind(host, port):
            remaining["n"] -= 1
            return remaining["n"] <= 0

        monkeypatch.setattr("launcher.processkit.can_bind", fake_bind)
        started = []
        monkeypatch.setattr(orch, "start",
                            lambda: started.append(True) or {"overall": "ONLINE"})
        report = orch.restart()
        assert started == [True]                      # never started before the port freed
        assert report["overall"] == "ONLINE"

    def test_restart_returns_a_report_when_the_port_never_frees(self, tmp_path, monkeypatch):
        """The wait is bounded: a port nothing releases must not hang the owner's
        desktop icon. ``start`` still runs and reports its own honest failure."""
        orch = self._stopped_orch(tmp_path, monkeypatch)
        monkeypatch.setattr(orch, "_reclaim_gateway_port", lambda host, port: None)
        monkeypatch.setattr("launcher.processkit.can_bind", lambda host, port: False)
        monkeypatch.setattr(orch, "start", lambda: {"overall": "DEGRADED"})
        report = orch.restart()
        assert report["overall"] == "DEGRADED"

    def test_stop_reclaims_a_listener_the_pid_record_lost(self, tmp_path, monkeypatch):
        """A hard kill of the launcher (console close instead of ``AHOS Stop``)
        orphans the detached gateway: the pid record is gone or stale, so the
        parentage walk cannot reach the survivor and stop asks the TCP table who
        still owns the port and terminates that tree — otherwise one failed
        restart strands the port and every later start reads foreign_busy."""
        orch = self._stopped_orch(tmp_path, monkeypatch)
        monkeypatch.setattr("launcher.processkit.can_bind", lambda host, port: False)
        monkeypatch.setattr("launcher.processkit.port_owner",
                            lambda host, port, timeout=10.0: 5232)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0:
                            f"node {ROOT}\\node_modules\\next\\dist\\bin\\next start")
        terminated = []
        monkeypatch.setattr("launcher.processkit.terminate",
                            lambda pid, **kw: terminated.append(pid) or ("force", 0.1))
        report = orch.stop()
        assert terminated == [5232]
        assert report["overall"] == "STOPPED"
        assert report["reclaimed"] == 5232

    def test_stop_leaves_a_foreign_listener_on_our_port_alone(self, tmp_path, monkeypatch):
        """The reclaim is marker-gated: an unrelated program squatting on the port
        is reported, never killed — UNKNOWN > fabricated, and blind taskkill of a
        pid we cannot prove is ours is a destructive guess."""
        orch = self._stopped_orch(tmp_path, monkeypatch)
        monkeypatch.setattr("launcher.processkit.can_bind", lambda host, port: False)
        monkeypatch.setattr("launcher.processkit.port_owner",
                            lambda host, port, timeout=10.0: 777)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0: r"C:\Elsewhere\server.exe")
        terminated = []
        monkeypatch.setattr("launcher.processkit.terminate",
                            lambda pid, **kw: terminated.append(pid) or ("force", 0.1))
        report = orch.stop()
        assert terminated == []
        assert "reclaimed" not in report

    def test_stop_arms_break_immunity_before_it_signals(self, tmp_path, monkeypatch):
        """R12: the dashboard's stop/restart route launches this orchestrator as a
        descendant of the gateway it must stop, and terminate() signals the
        gateway's whole process group — CTRL_BREAK reaches the orchestrator too
        and kills it mid-stop, after the "stopping" header and before any report.
        Immunity must therefore be armed *before* the first signal goes out."""
        orch = self._stopped_orch(tmp_path, monkeypatch)
        order = []

        def fake_terminate(pid, **kw):
            order.append(("terminated", pid))
            return "force", 0.1

        def fake_stop_components(order_):
            # If immunity is armed after this runs, the orchestrator is already
            # dead in the real failure mode; the assertion below would still pass
            # while the bug persisted, so record what was armed when we ran.
            order.append(("stopped", None))
            return {}

        monkeypatch.setattr("launcher.processkit.terminate", fake_terminate)
        monkeypatch.setattr(orch, "_stop_components", fake_stop_components)
        monkeypatch.setattr("launcher.processkit.arm_console_break_immunity",
                            lambda: order.append(("immune", None)) or True)
        monkeypatch.setattr(orch, "_reclaim_gateway_port", lambda host, port: None)
        orch.stop()
        assert order[0][0] == "immune"                      # before anything is signalled
        assert [step for step, _ in order] == ["immune", "stopped"]

    def test_listen_addr_prefers_the_recorded_port(self, tmp_path):
        orch = make_orchestrator(tmp_path)
        pk.write_pid(orch.state_dir, "gateway", 4242,
                     {"port": 8300, "host": "127.0.0.1", "cmd": "node next start"})
        orch.gateway = {"host": "127.0.0.1", "port": 3000}
        assert orch._gateway_listen_addr() == ("127.0.0.1", 8300)

    def test_listen_addr_finds_our_live_listener_without_the_record(self, tmp_path, monkeypatch):
        """A stop that died after clearing the record (the R12 wedge) leaves the
        gateway listening on a candidate port the launcher chose at start time —
        never the configured one, which Windows reserves on this host. Stop has to
        find it in the TCP table or it can never reclaim the port again."""
        orch = make_orchestrator(tmp_path)
        orch.gateway = {"host": "127.0.0.1", "port": 3000}
        monkeypatch.setattr("launcher.components.candidate_ports",
                            lambda env, config_file=None: (3100, 3200, 8300))
        seen = []

        def fake_owner(host, port, timeout=10.0):
            seen.append(port)
            return 5232 if port == 8300 else None

        monkeypatch.setattr("launcher.processkit.port_owner", fake_owner)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0:
                            f"node {ROOT}\\node_modules\\next\\dist\\bin\\next dev")
        assert orch._gateway_listen_addr() == ("127.0.0.1", 8300)
        assert seen == [3100, 3200, 8300]                 # walked in order, stopped at the hit

    def test_listen_addr_ignores_a_foreign_listener_on_a_candidate(self, tmp_path, monkeypatch):
        """Only a listener the gateway marker proves is ours is adopted; a foreign
        server on a candidate port must not make stop claim an address that is not
        ours. The configured port remains the last resort."""
        orch = make_orchestrator(tmp_path)
        orch.gateway = {"host": "127.0.0.1", "port": 3000}
        monkeypatch.setattr("launcher.components.candidate_ports",
                            lambda env, config_file=None: (3100, 8300))
        monkeypatch.setattr("launcher.processkit.port_owner",
                            lambda host, port, timeout=10.0: 5232)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0: r"C:\Elsewhere\server.exe")
        assert orch._gateway_listen_addr() == ("127.0.0.1", 3000)

    def test_listen_addr_skips_the_tcp_scan_for_a_non_loopback_gateway(self, tmp_path, monkeypatch):
        """A non-loopback gateway address points at another machine: the TCP table
        of this host says nothing useful about it, so the scan is skipped and the
        configured address is used as-is."""
        orch = make_orchestrator(tmp_path)
        orch.gateway = {"host": "10.0.0.5", "port": 3000}
        monkeypatch.setattr("launcher.components.candidate_ports",
                            lambda env, config_file=None: (3100, 8300))
        monkeypatch.setattr("launcher.processkit.port_owner",
                            lambda host, port, timeout=10.0: pytest.fail("scanned"))
        assert orch._gateway_listen_addr() == ("10.0.0.5", 3000)


class TestGatewayPortReconcile:
    """`next dev` walks to a free port when the one it was asked for is held,
    and tells nobody. The boot loop reads the address it printed back out of its
    own log so the probe, the recorded selection and the owner's app window all
    point at the port actually serving (M-D2.1).
    """

    @staticmethod
    def _orch_with_log(tmp_path, text: str, offset: int | None = None):
        orch = make_orchestrator(tmp_path)
        orch.log_dir.mkdir(parents=True, exist_ok=True)
        (orch.log_dir / "gateway.log").write_text(text, encoding="utf-8")
        port = 3000
        orch.gateway = {**orch.gateway, "port": port,
                        "url": C.gateway_url_at("127.0.0.1", port)}
        extra = {"port": port, "started_ts": 1.0}
        if offset is not None:
            extra["log_offset"] = offset
        pk.write_pid(orch.state_dir, "gateway", 999, extra)
        return orch

    def test_adopts_the_port_next_actually_bound(self, tmp_path):
        orch = self._orch_with_log(tmp_path, (
            "▲ Next.js 16.3.8 (Turbopack)\n"
            "- Local:        http://127.0.0.1:3199\n"
            "- Network:      http://127.0.0.1:3199\n"
            "✓ Ready in 18.8s\n"))
        assert orch._reconcile_gateway_port() == 3199
        assert orch.gateway["port"] == 3199
        assert orch.gateway["chosen_via"] == "ADOPTED_NEXT_BOUND_PORT"
        assert orch.dashboard_url() == "http://127.0.0.1:3199/"
        # Both records a later start reads name the serving port.
        assert json.loads((orch.state_dir / "gateway_selected.json").read_text(
            encoding="utf-8"))["port"] == 3199
        assert pk.read_pid(orch.state_dir, "gateway")["port"] == 3199

    def test_matching_port_is_a_no_op(self, tmp_path):
        orch = self._orch_with_log(tmp_path, (
            "▲ Next.js 16.3.8 (Turbopack)\n"
            "- Local:        http://127.0.0.1:3000\n"
            "✓ Ready in 3.1s\n"))
        assert orch._reconcile_gateway_port() is None
        assert orch.gateway["port"] == 3000
        assert orch.gateway.get("chosen_via") != "ADOPTED_NEXT_BOUND_PORT"

    def test_no_ready_line_yet_is_not_an_error(self, tmp_path):
        orch = self._orch_with_log(tmp_path, "▲ Next.js 16.3.8 (Turbopack)\n")
        assert orch._reconcile_gateway_port() is None

    def test_an_earlier_boot_line_is_not_adopted(self, tmp_path):
        """The log is append-only across restarts; only this spawn's bytes count,
        or a port nothing serves now would be adopted from a previous boot."""
        before = ("- Local:        http://127.0.0.1:3199\n✓ Ready in 12s\n")
        after = ("▲ Next.js 16.3.8 (Turbopack)\n- Local:        http://127.0.0.1:3000\n")
        orch = self._orch_with_log(tmp_path, before + after, offset=len(before))
        assert orch._reconcile_gateway_port() is None
        assert orch.gateway["port"] == 3000

    def test_missing_log_is_not_an_error(self, tmp_path):
        orch = make_orchestrator(tmp_path)
        pk.write_pid(orch.state_dir, "gateway", 999, {"port": 3000})
        assert orch._reconcile_gateway_port() is None


class TestProcessMarkers:
    """The marker must be a substring of the command line we actually spawn.

    Regression: the engine marker was written as
    ``python.exe architecture.runtime`` while the real argv is
    ``python.exe -m architecture.runtime --daemon ...``. The missing ``-m`` made
    ``pid_is_ours`` return False forever, so the engine always looked dead,
    every start spawned a second one, and stop never reclaimed either. Telegram
    (no ``-m`` in its argv) probed healthy the whole time, which is what
    isolated the cause.
    """

    def test_engine_marker_matches_the_spawned_command(self, tmp_path):
        orch = make_orchestrator(tmp_path)
        py = C.venv_python(orch.root) or Path(sys.executable)
        cmd = " ".join(C.engine_command(py))
        assert orch.marker("engine").lower() in cmd.lower()

    def test_telegram_marker_matches_the_spawned_command(self, tmp_path):
        orch = make_orchestrator(tmp_path)
        py = C.venv_python(orch.root) or Path(sys.executable)
        cmd = " ".join(C.telegram_command(py))
        assert orch.marker("telegram").lower() in cmd.lower()

    @pytest.mark.parametrize("mode", ["prod", "dev"])
    def test_gateway_marker_matches_the_spawned_command(self, tmp_path, mode):
        """M11.3: the gateway marker used to be ``<root>/node_modules`` — a
        directory the ``cmd /c npm run start`` argv never contained, so it could
        never match. It is now derived from the argv the launcher spawns, like
        every other component."""
        orch = make_orchestrator(tmp_path)
        cmd = " ".join(C.gateway_command(orch.root, mode))
        assert "npm" not in cmd and "cmd /c" not in cmd   # no wrapper in the argv
        assert orch.marker("gateway").lower() in cmd.lower()

    def test_gateway_marker_is_not_the_node_modules_directory(self, tmp_path):
        """The old marker was the whole ``node_modules`` path; a marker that wide
        matched any node process started from this checkout (R3). The new one
        names this checkout's own next CLI, so it does not match a foreign node
        process that merely happens to run under the repo, nor the wrapper that
        used to be spawned."""
        orch = make_orchestrator(tmp_path)
        cli = C.next_cli(orch.root)
        assert cli is not None, "node_modules/next must be installed for this suite"
        marker = orch.marker("gateway").lower()
        assert marker == str(cli).lower()
        foreign = r"C:\Program Files\nodejs\node.exe G:\robat\ahos\scripts\tool.js"
        assert marker not in foreign.lower()
        assert marker not in 'cmd /c "npm run start --silent"'.lower()

    def test_engine_marker_matches_the_base_interpreter_relaunch(self, tmp_path):
        """The .venv python is a launcher that re-execs the base interpreter, so
        the real child command line has no venv path — the sweep needs a marker
        that still matches it."""
        orch = make_orchestrator(tmp_path)
        base = (r'"C:\Users\Sniper\AppData\Local\Programs\Python\Python311\python.exe" '
                r"-m architecture.runtime --daemon --interval-sec 60 "
                r"--observation-cycle --evidence-source local")
        marks = [m for m, name in orch.sweep_markers() if name == "engine"]
        assert any(m.lower() in base.lower() for m in marks), marks

    def test_sweep_markers_still_identify_the_repo(self, tmp_path):
        """A foreign project's python must never match any sweep marker."""
        orch = make_orchestrator(tmp_path)
        foreign = r"C:\other\project\.venv\Scripts\python.exe app.py"
        assert not any(m.lower() in foreign.lower() for m, _ in orch.sweep_markers())


# --------------------------------------------------------- telegram readiness ---
# M11.4: telegram health is a stable, polling process — not "pid alive at
# spawn". run_bot.py's own preflight (token, stores, a live get_me() through a
# tunnel) can take many seconds, and the child is *alive* for every one of them,
# so a liveness-only probe reported HEALTHY the instant it spawned and a start
# announced ONLINE for a bot that was already dying.
class TestTelegramReadiness:
    # the exact line run_bot.py prints once its poll loop starts; copied from
    # run_bot.run_polling, and pinned here so a silent wording change there
    # breaks this suite instead of quietly un-fixing M11.4.
    READY = "🤖 AHOS در حال گوش دادن است (offset=0). برای توقف: Ctrl+C"

    def _rec(self, tmp_path, started, *, offset=0):
        return {"pid": 4242, "started_ts": started, "log": str(tmp_path / "telegram.log"),
                "log_offset": offset}

    def test_a_pid_alive_for_one_second_is_still_booting(self, monkeypatch, tmp_path):
        """The bug: a pid alive at spawn was reported HEALTHY."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        verdict = C.probe_telegram(self._rec(tmp_path, 1000.0), "telegram", now=1001.0)
        assert verdict[0] == C.UNHEALTHY
        assert "preflight" in verdict[1]

    def test_stable_and_marked_is_healthy(self, monkeypatch, tmp_path):
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        log = tmp_path / "telegram.log"
        log.write_text(f"preflight note\n{self.READY}\n", encoding="utf-8")
        verdict = C.probe_telegram(self._rec(tmp_path, 1000.0), "telegram", now=1010.0)
        assert verdict[0] == C.HEALTHY
        assert "polling" in verdict[1]

    def test_stable_but_no_mark_yet_is_still_booting(self, monkeypatch, tmp_path):
        """Alive past the stability window but the poll loop has not started."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        log = tmp_path / "telegram.log"
        log.write_text("still in preflight\n", encoding="utf-8")
        verdict = C.probe_telegram(self._rec(tmp_path, 1000.0), "telegram", now=1010.0)
        assert verdict[0] == C.UNHEALTHY
        assert "readiness line" in verdict[1]

    def test_a_previous_run_s_mark_does_not_satisfy_this_boot(self, monkeypatch, tmp_path):
        """The log is append-only across restarts, so the whole-file search the
        naive fix implies would read the *last* bot's readiness line while this
        bot is still failing preflight — announcing ONLINE for the same dying
        process the fix was written for."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        log = tmp_path / "telegram.log"
        log.write_text(f"{self.READY}\n", encoding="utf-8")
        rec = self._rec(tmp_path, 1000.0, offset=log.stat().st_size)
        # this spawn has written nothing yet
        verdict = C.probe_telegram(rec, "telegram", now=1001.0)
        assert verdict[0] == C.UNHEALTHY

    def test_the_status_poll_does_not_require_a_live_log(self, monkeypatch, tmp_path):
        """A bot that has served for hours can have had its log rotated or
        removed by hand; a read-only ``status`` must not then report a working
        bot as sick. Liveness and the stability window still apply."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        rec = self._rec(tmp_path, 1000.0)  # no log file at all
        assert C.probe_telegram(rec, "telegram", now=2000.0,
                                require_ready=False)[0] == C.HEALTHY
        # ...but a young one is still booting, even without a log to check
        assert C.probe_telegram(rec, "telegram", now=1001.0,
                                require_ready=False)[0] == C.UNHEALTHY

    def test_stability_threshold_is_configurable(self, monkeypatch, tmp_path):
        """``min_uptime`` is the knob HEALTH_WAIT surfaces."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        rec = self._rec(tmp_path, 1000.0)
        assert C.probe_telegram(rec, "telegram", now=1002.0,
                                min_uptime=1.0, require_ready=False)[0] == C.HEALTHY

    def test_a_dead_pid_is_unavailable_not_booting(self, monkeypatch, tmp_path):
        """The stability rule must not swallow the exit: a recorded pid that is
        no longer ours is UNAVAILABLE."""
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: False)
        verdict = C.probe_telegram(self._rec(tmp_path, 1000.0), "telegram", now=1010.0)
        assert verdict[0] == C.UNAVAILABLE

    def test_log_tail_never_splits_a_multibyte_character(self, tmp_path):
        log = tmp_path / "telegram.log"
        log.write_text("خط یک\nخط دو\nخط سه\n", encoding="utf-8")
        assert C.read_log_tail(log, lines=2) == "خط دو\nخط سه"
        assert C.read_log_tail(tmp_path / "absent.log", lines=3) == ""

    def test_redact_log_strips_a_token_echo_and_is_idempotent(self):
        once, kinds = C.redact_log("TELEGRAM_BOT_TOKEN=1234567890:ABC-def_ghI")
        assert "1234567890:ABC" not in once
        assert "REDACTED" in once
        assert kinds  # at least one pattern fired
        twice, _ = C.redact_log(once)
        assert twice == once, "redacting twice must not double-wrap"

    def test_redact_log_leaves_plain_text_alone(self):
        clean, kinds = C.redact_log("❌ پیش‌نیازها کامل نیست.")
        assert clean == "❌ پیش‌نیازها کامل نیست."
        assert kinds == []

    # --- start-level, with a real child the boot loop really has to watch ---
    def _fake_child(self, marker, body):
        """A real interpreter whose command line carries ``marker`` (so
        ``pid_is_ours`` matches it) and which runs ``body``."""
        code = f"import time, sys\n{body}"
        return [sys.executable, "-c", code, marker]

    @staticmethod
    def _only_telegram_is_real(orch, monkeypatch):
        """Run the REAL telegram boot path (real spawn, real pid, real loop)
        while every other component is simulated healthy, so the overall verdict
        reflects telegram alone instead of a SAFE_HALT for a missing daemon."""
        real = orch._start_component
        monkeypatch.setattr(orch, "_start_component",
                            lambda name: real("telegram") if name == "telegram"
                            else C.ComponentResult(name, C.HEALTHY, "simulated"))
        monkeypatch.setattr("launcher.processkit.open_url", lambda url: True)

    def test_a_child_exiting_after_one_second_reports_unavailable_and_degraded(
            self, tmp_path, monkeypatch):
        """M11.4 acceptance: a fake child that exits after 1 s -> start reports
        telegram UNAVAILABLE, overall DEGRADED (not ONLINE)."""
        orch = make_orchestrator(tmp_path,
                                 health_wait={"telegram": 30, "telegram_stable": 600})
        marker = "_ahos_fake_telegram_child_"
        cmd = self._fake_child(marker, "time.sleep(1.0); sys.exit(1)\n")
        orch.command_overrides["telegram"] = cmd
        monkeypatch.setattr(orch, "marker", lambda name: marker)
        # the fake child's live command line carries our marker
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0: " ".join(cmd))
        self._only_telegram_is_real(orch, monkeypatch)
        report = orch.start()
        assert report["components"]["telegram"]["status"] == C.UNAVAILABLE
        assert "exited during its own preflight" in report["components"]["telegram"]["detail"]
        assert report["overall"] == "DEGRADED"

    def test_a_child_that_reaches_the_poll_loop_is_healthy(self, tmp_path, monkeypatch):
        """The happy path through the same loop: the child survives the stability
        window and prints the readiness line, so it is reported HEALTHY."""
        orch = make_orchestrator(tmp_path,
                                 health_wait={"telegram": 60, "telegram_stable": 2})
        marker = "_ahos_fake_telegram_child_"
        ready = C.TELEGRAM_READY_MARK
        # sleep past the 2 s stability bar, then print the real readiness line,
        # then stay alive long enough for the loop to see it
        cmd = self._fake_child(
            marker,
            "time.sleep(3.0)\n"
            f"print({ready!r}, flush=True)\n"
            "time.sleep(120.0)\n")
        orch.command_overrides["telegram"] = cmd
        monkeypatch.setattr(orch, "marker", lambda name: marker)
        monkeypatch.setattr("launcher.processkit.process_cmdline",
                            lambda pid, timeout=5.0: " ".join(cmd))
        self._only_telegram_is_real(orch, monkeypatch)
        try:
            report = orch.start()
        finally:
            # the fake poller outlives the boot loop by design; stop it by pid
            info = pk.read_pid(orch.state_dir, "telegram")
            if info:
                pk.taskkill(info["pid"], force=True)
        assert report["components"]["telegram"]["status"] == C.HEALTHY
        assert "polling" in report["components"]["telegram"]["detail"]

    def test_a_concurrent_start_reports_the_bot_as_it_is(self, tmp_path, monkeypatch):
        """``already running`` must not assert HEALTHY for a bot still in its own
        preflight — the second ``start`` would announce ONLINE for the same dying
        bot the fix was written for. The idempotency decision (do not spawn a
        second bot on the same token) is untouched."""
        orch = make_orchestrator(tmp_path, health_wait={"telegram_stable": 600})
        monkeypatch.setattr("launcher.processkit.pid_is_ours", lambda pid, marker: True)
        monkeypatch.setattr("launcher.processkit.pid_alive", lambda pid: True)
        pk.write_pid(orch.state_dir, "telegram", 4242,
                     {"cmd": "run_bot.py", "marker": orch.marker("telegram"),
                      "log": str(orch.log_path("telegram")),
                      "started_ts": time.time()})
        assert orch.component_state("telegram") == "ours_running"  # no second spawn
        res = orch._start_component("telegram")
        assert res.status == C.UNHEALTHY
        assert "preflight" in res.detail


class TestSmokeReportParsing:
    """The smoke harness must be able to read the report the CLI prints.

    Regression: ``--json`` still prints the Persian progress lines first and the
    report pretty-printed with ``indent=2`` afterwards, so taking the last line
    of stdout yielded ``}`` and the parse always failed. That left
    ``report: null`` on every step, and the smoke scored a genuinely idempotent
    second start as ``second_start_was_idempotent_replay: false`` — the smoke
    had never been able to see its own result.
    """

    def test_parses_report_after_persian_progress_lines(self):
        stdout = (
            "بررسی پیش‌نیازها…\n"
            "  موتور کاغذی: ✓\n"
            "AHOS با هشدار روشن است.\n"
            '{\n  "action": "start",\n  "overall": "DEGRADED",\n'
            '  "paper_only": true\n}\n'
        )
        report = _parse_report(stdout)
        assert report == {"action": "start", "overall": "DEGRADED",
                          "paper_only": True}

    def test_returns_none_when_no_report_is_printed(self):
        assert _parse_report("همهٔ سرویس‌های AHOS متوقف شدند.\n") is None

    def test_skips_a_brace_in_progress_text(self):
        """A stray brace in the progress text is not mistaken for the report."""
        stdout = "پیکربندی {port} OK\n" '{\n  "action": "status"\n}\n'
        assert _parse_report(stdout) == {"action": "status"}


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
        # One icon only (owner rule): Status/Stop/Restart live in the dashboard.
        assert [s["name"] for s in specs] == ["AHOS.lnk"]
        for s in specs:
            assert s["target_path"].endswith("powershell.exe")
            assert "ahos.ps1" in s["arguments"]
            assert s["icon_location"].endswith("ahos.ico,0")
            assert "ExecutionPolicy Bypass" in s["arguments"]
            # -WindowStyle Hidden is what makes the launch invisible; the .lnk
            # WindowStyle of 7 is only a fallback hint.
            assert "-WindowStyle Hidden" in s["arguments"]
        assert "-Action start" in specs[0]["arguments"]

    def test_create_shortcuts_writes_real_lnk_files(self, tmp_path):
        """The marshalled PowerShell must actually parse and save (a bare ``[``
        array literal is a cast in PowerShell and silently breaks this)."""
        import launcher.shortcuts as S
        icon = tmp_path / "ahos.ico"
        build_icon(icon, sizes=(32,))
        desktop = tmp_path / "Desktop"
        # A stale pre-M11.1 pair on the desktop must be retired, not deleted.
        legacy = []
        for name in S.LEGACY_NAMES:
            f = desktop / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"not a real lnk, just a placeholder")
            legacy.append(f)
        retire = tmp_path / "retired"
        moved = S.retire_legacy_shortcuts(desktop, retire)
        assert sorted(Path(m).name for m in moved) == sorted(S.LEGACY_NAMES)
        assert all(not p.exists() for p in legacy)
        assert len(list(retire.glob("*.lnk.*"))) == 2

        # Same precedent as tests/test_phase18_launchers.py (skip when pwsh is
        # absent): the .lnk write needs Windows PowerShell + WScript.Shell COM.
        # The retire assertions above still run on every host.
        import shutil
        if os.name != "nt" or not shutil.which("powershell"):
            pytest.skip("Windows PowerShell + WScript.Shell COM not available on this host")
        wrote = S.create_shortcuts(tmp_path, icon=icon, desktop=desktop)
        assert [w["name"] for w in wrote] == ["AHOS.lnk"]
        # Re-resolve through WScript.Shell: the .lnk must point at the wrapper.
        import subprocess
        lnk = str(desktop / "AHOS.lnk")
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
             "$s.TargetPath + ' ' + $s.Arguments + ' | style=' + $s.WindowStyle" % lnk],
            capture_output=True, text=True, timeout=60)
        assert res.returncode == 0, res.stderr
        assert "ahos.ps1" in res.stdout and "-Action start" in res.stdout
        assert "-WindowStyle Hidden" in res.stdout
        assert res.stdout.rstrip().endswith("style=7")


# --------------------------------------------------------------------- cli ---
class TestCli:
    def test_preflight_bad_root_exits_nonzero(self, monkeypatch, capsys):
        from launcher.__main__ import main
        rc = main(["--root", str(ROOT / "launcher"), "preflight"])
        assert rc == 1

    def test_skip_accepts_repeated_and_comma_joined(self):
        """The dashboard route cannot emit a repeated -Skip: Start-Process
        re-parses -ArgumentList into one command line and PowerShell's binder
        rejects it, so the exclusions arrive as a single comma-joined value.
        Both spellings must resolve to the same set."""
        from launcher.__main__ import _skip_set
        assert _skip_set([]) == set()
        assert _skip_set(["engine"]) == {"engine"}
        assert _skip_set(["engine", "telegram"]) == {"engine", "telegram"}
        assert _skip_set(["engine,telegram"]) == {"engine", "telegram"}
        assert _skip_set([" telegram , engine ,", "", "  "]) == {"telegram", "engine"}

@pytest.mark.skipif(os.name == "nt", reason="POSIX branch of processkit")
class TestPosixProcessKit:
    """The launcher's process layer must not crash off Windows: a non-zero
    creationflags raises ValueError on POSIX, so every spawn used to fail
    with 'creationflags is only supported on Windows platforms'."""

    def test_spawn_identify_and_terminate_a_real_child(self, tmp_path):
        marker = f"ahos-posix-selftest-{os.getpid()}"
        pid = pk.spawn_detached(
            [sys.executable, "-c", "import time,sys; time.sleep(60)", marker],
            cwd=tmp_path, env=dict(os.environ), log_path=tmp_path / "child.log")
        try:
            assert pk.pid_alive(pid)
            assert pk.pid_is_ours(pid, marker)
            assert not pk.pid_is_ours(pid, "some-other-marker")
            how, _secs = pk.terminate(pid, graceful_timeout=5.0)
            assert how in ("signal", "force")
            assert not pk.pid_alive(pid)
        finally:
            if pk.pid_alive(pid):
                os.kill(pid, 9)


def test_soft_preflight_warning_is_not_reported_as_failed_service(tmp_path, monkeypatch):
    """A non-fatal preflight finding (e.g. no Gemini credential) must not print
    the generic 'a service did not run' error at the top of an ONLINE start."""
    lines = []
    orch = AhosOrchestrator(ROOT, env=C.load_repo_env(ROOT, {}), state_dir=tmp_path / "s",
                            log_dir=tmp_path / "l", report_dir=tmp_path / "r",
                            ledger_path=tmp_path / "ledger.sqlite", emit=lines.append,
                            open_dashboard=False)
    pf = C.Preflight(ok=True, checks=[{"name": "gemini_cred", "ok": False, "detail": "cred missing"}],
                     warnings=["cred missing"])
    monkeypatch.setattr(orch, "preflight", lambda: pf)
    monkeypatch.setattr(orch, "_start_component", lambda name: C.ComponentResult(name, C.HEALTHY, "sim"))
    assert orch.start()["overall"] == "ONLINE"
    generic = P.error("generic", action=P.ACTIONS["unknown"]).split("{")[0][:12]
    assert not any(l.startswith(generic) for l in lines), lines


class TestPgliteInitM101:
    """M10.1: decision logic + probe with a fake runner (no real PGlite)."""

    def test_decide_restore_when_pg_version_missing(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        (d / "junk.txt").write_text("x", encoding="utf-8")
        target = {"scheme": "pglite", "data_dir": str(d), "configured": True}
        assert C.decide_pglite_init_action(target) == "restore"
        assert C.pglite_needs_schema_init(d) is True

    def test_decide_skip_when_pg_version_present(self, tmp_path):
        d = tmp_path / "store"
        d.mkdir()
        (d / "PG_VERSION").write_text("15\n", encoding="utf-8")
        target = {"scheme": "pglite", "data_dir": str(d), "configured": True}
        assert C.decide_pglite_init_action(target) == "skip_already_init"
        assert C.pglite_needs_schema_init(d) is False

    def test_decide_never_restore_postgres(self):
        target = {"scheme": "postgres", "host": "127.0.0.1", "port": 5432,
                  "configured": True}
        assert C.decide_pglite_init_action(target) == "noop_not_pglite"

    def test_decide_no_dir(self):
        target = {"scheme": "pglite", "data_dir": None, "configured": True}
        assert C.decide_pglite_init_action(target) == "noop_no_dir"

    def test_restore_argv_is_schema_only_node_strip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(C, "node_executable", lambda: "node")
        argv = C.pglite_restore_argv(tmp_path, "G:/data/pglite")
        assert argv[0] == "node"
        assert "--experimental-strip-types" in argv
        assert argv[-2:] == ["--dataDir", "G:/data/pglite"]
        assert "--dump" not in argv
        assert "--check" not in argv

    def test_check_argv_adds_check_flag(self, tmp_path, monkeypatch):
        monkeypatch.setattr(C, "node_executable", lambda: "node")
        argv = C.pglite_check_argv(tmp_path, "/tmp/store")
        assert argv[-3:] == ["--dataDir", "/tmp/store", "--check"]

    def test_probe_unavailable_without_pg_version(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        target = {"scheme": "pglite", "data_dir": str(d), "configured": True,
                  "host": "127.0.0.1", "port": 5432}
        status, detail = C.probe_db_backend(target, 0.0, root=tmp_path)
        assert status == C.UNAVAILABLE
        assert "PG_VERSION" in detail

    def test_probe_healthy_when_check_runner_ok(self, tmp_path):
        d = tmp_path / "store"
        d.mkdir()
        (d / "PG_VERSION").write_text("15\n", encoding="utf-8")
        target = {"scheme": "pglite", "data_dir": str(d), "configured": True,
                  "host": "127.0.0.1", "port": 5432}

        def ok_runner(root, data_dir):
            assert data_dir == str(d)
            return 0, "check OK"

        status, detail = C.probe_db_backend(
            target, 0.0, root=tmp_path, check_runner=ok_runner)
        assert status == C.HEALTHY
        assert "ahos_system_state" in detail

    def test_probe_unavailable_when_check_runner_fails(self, tmp_path):
        d = tmp_path / "store"
        d.mkdir()
        (d / "PG_VERSION").write_text("15\n", encoding="utf-8")
        target = {"scheme": "pglite", "data_dir": str(d), "configured": True,
                  "host": "127.0.0.1", "port": 5432}

        def bad_runner(root, data_dir):
            return 1, "table ahos_system_state missing"

        status, detail = C.probe_db_backend(
            target, 0.0, root=tmp_path, check_runner=bad_runner)
        assert status == C.UNAVAILABLE
        assert "ahos_system_state" in detail

    def test_start_runs_restore_once_via_fake_runner(self, tmp_path, monkeypatch):
        from launcher.orchestrator import AhosOrchestrator

        d = tmp_path / "pglite"
        d.mkdir()
        calls = []

        def fake_restore_runner(argv, cwd, env):
            calls.append(list(argv))
            assert "--dump" not in argv
            assert "--dataDir" in argv
            # Simulate successful schema init.
            (d / "PG_VERSION").write_text("15\n", encoding="utf-8")
            return 0, "migration: applied 33 statements"

        def fake_check(root, data_dir):
            return 0, "check OK: ahos_system_state present"

        monkeypatch.setattr(C, "node_executable", lambda: "node")
        # Avoid real preflight / other components.
        orch = AhosOrchestrator(
            root=tmp_path, state_dir=tmp_path / "state",
            report_dir=tmp_path / "reports",
            env={"DATABASE_URL": f"pglite:{d.as_posix()}"},
            clock=lambda: 1_700_000_000.0,
            open_dashboard=False,
        )
        orch.command_overrides["db_backend_restore_runner"] = fake_restore_runner
        orch.command_overrides["db_backend_check_runner"] = fake_check

        res = orch._start_db_backend()
        assert res.status == C.HEALTHY, res.detail
        assert len(calls) == 1
        assert res.evidence.get("init_action") == "restore"
        assert res.evidence.get("restore_ran") is True

        # Second start: PG_VERSION present -> skip restore.
        calls.clear()
        res2 = orch._start_db_backend()
        assert res2.status == C.HEALTHY, res2.detail
        assert calls == []
        assert res2.evidence.get("init_action") == "skip_already_init"
        assert res2.evidence.get("restore_ran") is False

    def test_start_never_restores_postgres(self, tmp_path, monkeypatch):
        from launcher.orchestrator import AhosOrchestrator

        calls = []

        def fake_restore_runner(argv, cwd, env):
            calls.append(argv)
            return 0, "should not run"

        orch = AhosOrchestrator(
            root=tmp_path, state_dir=tmp_path / "state",
            report_dir=tmp_path / "reports",
            env={"DATABASE_URL": "postgres://u:p@127.0.0.1:5432/ahos"},
            clock=lambda: 1_700_000_000.0,
            open_dashboard=False,
        )
        orch.command_overrides["db_backend_restore_runner"] = fake_restore_runner
        # Avoid depending on processkit.port_in_use (probe path); we only assert
        # that the restore runner is never invoked for postgres (STATE B).
        monkeypatch.setattr(C, "probe_db_backend",
                            lambda *a, **k: (C.HEALTHY, "postgres reachable (stub)"))
        res = orch._start_db_backend()
        assert calls == []
        assert res.evidence.get("init_action") == "noop_not_pglite"
        assert res.status == C.HEALTHY

