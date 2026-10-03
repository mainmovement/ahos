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

    def test_probe_stores_accepts_str_paths(self):
        """config.paths helpers return str; probe_stores must not assume Path."""
        status, _detail = C.probe_stores(0.0)
        assert status in (C.HEALTHY, C.UNAVAILABLE)

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
