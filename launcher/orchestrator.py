"""The one-click orchestrator: preflight → ordered idempotent start → health →
status/stop, all recorded through the control plane.

Design notes that matter for honesty:

* Idempotency is per component. A second `start` finds the pid records, verifies
  each pid is still one of ours, and reports ALREADY_RUNNING without spawning.
* A component that cannot start is reported, never papered over: CRITICAL
  failures (stores, engine) abort the boot and SAFE-HALT the run; OPTIONAL
  failures (db_backend, gateway, telegram) degrade it — which is exactly what
  the gateway and bot already implement themselves.
* "Ours" is decided by strict parentage (one process snapshot, walking ppid
  chains to the launcher or a recorded component pid) plus a command-line marker
  as a second check, so `stop` never touches a process that does not belong to
  this launcher run — including editor-spawned node/tsc processes that merely
  happen to run from this checkout.
* Nothing here reads the Telegram token, the Gemini secret, or DATABASE_URL's
  credentials; only schemes, hosts, ports and key *presence*.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from config.paths import get_data_dir, get_local_db_path, get_project_root

import launcher.components as C
import launcher.persian as P
import launcher.processkit as pk
from launcher.control_plane_bridge import LauncherControlPlane

PROCESS_COMPONENTS = ["gateway", "telegram", "engine"]
# The engine's cold boot (runtime init + first scheduler cycle) can take a few
# minutes on a loaded host; the probe turns healthy the moment the first
# DAEMON_CYCLE heartbeat lands.
HEALTH_WAIT = {"stores": 60, "db_backend": 10, "gateway": 120, "telegram": 25, "engine": 420}


class AhosOrchestrator:
    def __init__(self, root: Path | str | None = None, *,
                 env: dict | None = None,
                 clock: Callable[[], float] = time.time,
                 emit: Callable[[str], None] = print,
                 state_dir: Path | None = None,
                 log_dir: Path | None = None,
                 report_dir: Path | None = None,
                 skip: set[str] | None = None,
                 command_overrides: dict[str, list[str]] | None = None,
                 health_wait: dict[str, float] | None = None,
                 open_dashboard: bool | None = None,
                 ledger_path: Path | None = None):
        self.root = Path(root) if root else get_project_root()
        self.env = C.load_repo_env(self.root, os.environ if env is None else env)
        self.clock = clock
        self.emit = emit
        self.state_dir = Path(state_dir) if state_dir else Path(get_data_dir()) / "launcher"
        self.log_dir = Path(log_dir) if log_dir else self.root / "logs" / "launcher"
        self.report_dir = Path(report_dir) if report_dir else self.root / "reports" / "launcher"
        self.skip = set(skip or [])
        self.command_overrides = dict(command_overrides or {})
        self.health_wait = dict(HEALTH_WAIT)
        if health_wait:
            self.health_wait.update(health_wait)
        self.open_dashboard = True if open_dashboard is None else open_dashboard
        self.ledger_path = (Path(ledger_path) if ledger_path
                            else Path(get_data_dir()) / "control_plane_ledger.sqlite")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        # The gateway the launcher will actually use on this host. Selected once
        # per START (the Windows reserved-port ranges move across reboots, so the
        # choice is not cacheable) and pushed to every child so they agree. Falls
        # back to the pure resolver for read-only paths (status) and for tests
        # that inject their own resolution.
        self.gateway = C.resolve_gateway(self.env)

    # ------------------------------------------------------------------ paths --
    def log_path(self, name: str) -> Path:
        return self.log_dir / f"{name}.log"

    def dashboard_url(self) -> str:
        """The dashboard address, from the *selected* gateway.

        Everything that displays or probes the gateway goes through here, so the
        port the children were actually handed is the port the report names. A
        report that advertised the configured port while the gateway listened on
        the fallback would send the owner to a dead page.
        """
        host = self.gateway.get("host") or "127.0.0.1"
        port = int(self.gateway.get("port") or 3000)
        return f"http://{host}:{port}/"

    def report_name(self) -> str:
        ts = datetime.fromtimestamp(self.clock(), timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"status_{ts}.json"

    # ---------------------------------------------------------------- markers --
    def marker(self, name: str) -> str:
        """A substring of the *live* command line that identifies our process.

        Derived from the command we actually spawn, never hand-written: the
        engine is launched as ``python -m architecture.runtime``, and a marker
        written without the ``-m`` never matched the live command line. That
        made every probe say the engine "is not a live AHOS process" even while
        it was running cycles, so it was re-spawned on every start and never
        reclaimed by stop. See docs/ONE_CLICK.md, "Process identification".
        """
        py = C.venv_python(self.root)
        if name == "engine":
            return ((str(py) + " -m architecture.runtime")
                    if py else "-m architecture.runtime")
        if name == "telegram":
            return (str(py) + " run_bot.py") if py else "run_bot.py"
        if name == "gateway":
            return str(self.root / "node_modules")
        return str(self.root)

    def sweep_markers(self) -> list[tuple[str, str]]:
        """Markers the orphan sweep matches, each paired with its component.

        The primary marker is the venv one above. The venv ``python.exe`` is a
        launcher that re-execs the base interpreter, and that base child's
        command line carries no repo path at all — so an engine whose shim has
        already died matches nothing above. The fallback is the canonical daemon
        argv, which no other project on this machine uses.
        """
        out = [(self.marker("engine"), "engine"), (self.marker("telegram"), "telegram")]
        # contiguous in both the shim's and the base interpreter's argv
        out.append(("-m architecture.runtime --daemon", "engine"))
        out.append((self.marker("gateway"), "gateway"))
        return [(m, n) for m, n in out if m]

    # ------------------------------------------------------------- live state --
    def _pid_info(self, name: str) -> dict | None:
        return pk.read_pid(self.state_dir, name)

    def component_state(self, name: str) -> str:
        """ours_running | foreign_busy | down — the idempotency primitive."""
        if name not in PROCESS_COMPONENTS:
            # No long-lived process to track: "ours" means the probe passes.
            return "ours_running" if self._component_probe(name)[0] == C.HEALTHY else "down"
        info = self._pid_info(name)
        if info and pk.pid_is_ours(info.get("pid"), self.marker(name)):
            return "ours_running"
        if name == "gateway":
            info_gw = self.gateway
            host = info_gw.get("host") or "127.0.0.1"
            port = int(info_gw.get("port") or 3000)
            if pk.port_in_use(host, port):
                return "foreign_busy"
        return "down"

    def _component_probe(self, name: str, *, heartbeat_age: float | None = None):
        if name == "stores":
            return C.probe_stores(self.clock())
        if name == "db_backend":
            return C.probe_db_backend(C.database_target(self.env), self.clock())
        if name == "gateway":
            return C.probe_gateway(self.dashboard_url(), self.clock())
        if name == "telegram":
            return C.probe_process(self._pid_info("telegram"), self.marker("telegram"))
        if name == "engine":
            if heartbeat_age is None:
                heartbeat_age = C.engine_heartbeat_age(get_local_db_path())
            info = self._pid_info("engine")
            return C.probe_engine(info, self.marker("engine"),
                                  heartbeat_age=heartbeat_age,
                                  cycle=C.engine_cycle_state(get_local_db_path()),
                                  pid_started_ts=(info or {}).get("started_ts"))
        return C.UNKNOWN, f"unknown component {name}"

    # --------------------------------------------------------------- preflight --
    def preflight(self) -> C.Preflight:
        return C.preflight(self.root, self.env)

    # ------------------------------------------------------------- log helpers --
    def _log_tail(self, name: str, lines: int = 6) -> str:
        path = self.log_path(name)
        if not path.exists():
            return ""
        try:
            data = path.read_bytes()[-4000:]
            txt = data.decode("utf-8", errors="replace").strip().splitlines()
            return "\n".join(txt[-lines:])
        except Exception:
            return ""

    # ------------------------------------------------------------- components --
    def _spawn(self, name: str, cmd: list[str], env: dict) -> int:
        self.emit(P.PROGRESS[name] if name in P.PROGRESS else f"{name} …")
        pid = pk.spawn_detached(cmd, cwd=self.root, env=env,
                                log_path=self.log_path(name))
        pk.write_pid(self.state_dir, name, pid,
                     {"cmd": " ".join(cmd), "marker": self.marker(name),
                      "log": str(self.log_path(name)),
                      "started_ts": self.clock()})
        return pid

    def _start_component(self, name: str) -> C.ComponentResult:
        # Idempotent: if one of ours is already up, keep it and say so.
        state = self.component_state(name)
        if state == "ours_running":
            info = self._pid_info(name) or {}
            self.emit(f"  {P.component_label(name)}: از قبل در حال اجراست (pid {info.get('pid')})")
            return C.ComponentResult(name, C.HEALTHY, "already running (idempotent)",
                                     pid=info.get("pid"), started_ts=info.get("started_ts"))
        if state == "foreign_busy":
            return C.ComponentResult(name, C.UNHEALTHY, "foreign_busy")

        if name == "stores":
            return self._start_stores()
        if name == "db_backend":
            return self._start_db_backend()
        return self._start_process(name)

    def _start_stores(self) -> C.ComponentResult:
        self.emit(P.PROGRESS["stores"])
        py = C.venv_python(self.root)
        if py is None:
            return C.ComponentResult("stores", C.UNAVAILABLE, "no venv")
        cmd = self.command_overrides.get("stores") or C.stores_command(py)
        try:
            res = subprocess.run(cmd, cwd=str(self.root), env=self._child_env(),
                                 capture_output=True, text=True, timeout=120,
                                 creationflags=pk.CREATE_NO_WINDOW if os.name == "nt" else 0)
            ok = res.returncode == 0
            detail = (res.stdout or res.stderr or "").strip().splitlines()
            tail = " | ".join(detail[-3:])[:300]
        except Exception as e:
            return C.ComponentResult("stores", C.UNAVAILABLE, f"{type(e).__name__}: {e}")
        status, detail = C.probe_stores(self.clock())
        if not ok:
            status = C.UNAVAILABLE
            detail = f"init_databases exit {res.returncode}: {tail}"
        return C.ComponentResult("stores", status, detail)

    def _start_db_backend(self) -> C.ComponentResult:
        self.emit(P.PROGRESS["db_backend"])
        target = C.database_target(self.env)
        if not target["configured"]:
            return C.ComponentResult("db_backend", C.UNKNOWN,
                                     "DATABASE_URL not configured; gateway will fail closed")
        if target["scheme"] == "pglite":
            ddir = target.get("data_dir")
            if ddir and not (Path(ddir).exists() and any(Path(ddir).iterdir())):
                # Stage-3 restore path already exists; initialise the data dir once.
                self.emit("  در حال مقداردهی اولیهٔ پایگاه دادهٔ توکار…")
                try:
                    res = subprocess.run(
                        ["cmd", "/c", "npm run db:restore-pglite -- --dataDir", ddir],
                        cwd=str(self.root), env=self._child_env(),
                        capture_output=True, text=True, timeout=600,
                        creationflags=pk.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    if res.returncode != 0:
                        return C.ComponentResult(
                            "db_backend", C.UNAVAILABLE,
                            f"db:restore-pglite failed ({res.returncode})")
                except Exception as e:
                    return C.ComponentResult("db_backend", C.UNAVAILABLE,
                                             f"restore exception: {type(e).__name__}")
        status, detail = C.probe_db_backend(target, self.clock())
        return C.ComponentResult("db_backend", status, detail)

    def _gateway_mode(self) -> str:
        """prod | dev, with a one-time production build when the owner asks for
        production and the build is stale. Build failure degrades to `dev`
        (dashboard still reachable) and is reported, never hidden."""
        mode = (self.env.get("AHOS_GATEWAY_MODE") or "auto").strip().lower()
        if mode == "prod":
            stale, _ = C.build_stale(self.root)
            if stale:
                ok, _tail = self._npm_build()
                if not ok:
                    return "dev"
            return "prod"
        if mode == "auto":
            stale, _ = C.build_stale(self.root)
            if not stale:
                return "prod"
            self.emit(P.PROGRESS["build"])
            ok, _tail = self._npm_build()
            return "prod" if ok else "dev"
        return "dev"

    def _npm_build(self, timeout: float = 900.0) -> tuple[bool, str]:
        try:
            res = subprocess.run(C._npm_cmd("build"), cwd=str(self.root),
                                 env=self._child_env(), capture_output=True,
                                 text=True, timeout=timeout,
                                 creationflags=pk.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except subprocess.TimeoutExpired:
            self.emit("  ساخت داشبورد زمان‌بر بود؛ از حالت توسعه استفاده می‌شود.")
            return False, "build timed out"
        except Exception as e:
            return False, f"build exception: {type(e).__name__}"
        if res.returncode != 0:
            tail = "\n".join((res.stdout or "")[-800:].splitlines()[-6:])
            self.emit("  ساخت نسخهٔ تولیدی ناموفق بود؛ حالت توسعه (dev) استفاده می‌شود.")
            return False, f"next build exit {res.returncode}\n{tail}"
        return True, "build ok"

    def _start_process(self, name: str) -> C.ComponentResult:
        py = C.venv_python(self.root)
        if name != "gateway" and py is None:
            return C.ComponentResult(name, C.UNAVAILABLE, "no venv")
        cmd = self.command_overrides.get(name)
        if not cmd:
            if name == "gateway":
                mode = self._gateway_mode()
                cmd = C.gateway_command(self.root, mode)
            elif name == "engine":
                cmd = C.engine_command(py)
            elif name == "telegram":
                cmd = C.telegram_command(py)
            else:
                return C.ComponentResult(name, C.UNKNOWN, "no command")
        env = self._child_env(extra={} if name == "gateway" else {})
        try:
            pid = self._spawn(name, cmd, env)
        except Exception as e:
            return C.ComponentResult(name, C.UNAVAILABLE, f"spawn failed: {type(e).__name__}: {e}")

        t0 = self.clock()
        deadline = t0 + self.health_wait.get(name, 60)
        last: tuple[str, str] | None = None
        booting_note = False
        while self.clock() < deadline:
            if name == "telegram":
                # run_bot.py exits fast when its own preflight fails; catch that.
                if pk.pid_alive(pid) is False:
                    tail = self._log_tail("telegram")
                    hint = "توکن" if "توکن" in tail or "token" in tail.lower() else ""
                    return C.ComponentResult("telegram", C.UNAVAILABLE,
                                             f"exited during preflight; {tail[-160:]}",
                                             pid=pid, fresh=True)
                status, detail = C.probe_process(self._pid_info("telegram"),
                                                 self.marker("telegram"))
                if status == C.HEALTHY:
                    return C.ComponentResult("telegram", status, detail, pid=pid,
                                             fresh=True)
                last = (status, detail)
            else:
                status, detail = self._component_probe(name)
                if status == C.HEALTHY:
                    return C.ComponentResult(name, status, detail, pid=pid,
                                             started_ts=self.clock(), fresh=True)
                last = (status, detail)
            # The engine's boot can run minutes; say so once after the first
            # minute instead of leaving the owner staring at a frozen line.
            if (name == "engine" and not booting_note
                    and self.clock() - t0 > 45.0 and last and last[0] != C.HEALTHY):
                booting_note = True
                self.emit(P.PROGRESS["engine_booting"])
            time.sleep(1.0)
        tail = self._log_tail(name)
        # A live process that simply never turned healthy (the engine's first
        # scheduler cycle can take longer than the wait) is UNHEALTHY, not
        # UNAVAILABLE — the owner is told what it was last seen doing.
        alive = pk.pid_alive(pid)
        if alive and last and last[0] != C.UNAVAILABLE:
            return C.ComponentResult(
                name, C.UNHEALTHY,
                f"still not healthy after {self.health_wait.get(name, 60)}s"
                f" (process alive; last probe: {last[1]})"
                + (f"; log tail: {tail[-200:]}" if tail else ""),
                pid=pid, started_ts=self.clock(), fresh=True)
        return C.ComponentResult(name, C.UNAVAILABLE,
                                 f"health check timed out after {self.health_wait.get(name, 60)}s"
                                 + (f"; log tail: {tail[-200:]}" if tail else ""),
                                 pid=pid, started_ts=self.clock(), fresh=True)

    def _child_env(self, *, extra: dict | None = None) -> dict:
        env = C.child_env(self.root, self.env, gateway=self.gateway)
        if extra:
            env.update(extra)
        return env

    # ------------------------------------------------------------------- start --
    def start(self) -> dict:
        t0 = self.clock()
        # Pick the gateway address before anything spawns: the configured port
        # can be Windows-reserved on this host, and children must all be told the
        # same address. A warning here is reported, never fatal — the gateway
        # reports its own real bind failure honestly if nothing bound at all.
        sel = C.select_gateway(self.env)
        self.gateway = sel
        gw_note = None
        if sel.get("chosen_via") == "CANDIDATE_BINDABLE":
            gw_note = (f"configured port {sel.get('configured_port')} was not "
                       f"bindable on this host; using {sel.get('port')}")
        if sel.get("warnings"):
            gw_note = (gw_note + "; " if gw_note else "") + "; ".join(sel["warnings"])
        if gw_note:
            self.emit(f"  {P.component_label('gateway')}: {gw_note}")
        self.emit(P.PROGRESS["preflight"])
        pf = self.preflight()
        for chk in pf.checks:
            if not chk["ok"]:
                kind = {"venv": "venv", "node_modules": "node", "repo": "repo"}.get(
                    chk["name"], "generic")
                self.emit(P.error(kind, action=P.ACTIONS.get(
                    {"venv": "no_venv", "node_modules": "no_node_modules",
                     "repo": "no_repo"}.get(chk["name"], "unknown"))))
        if not pf.ok:
            report = self._report("start", "FAILED", {}, pf)
            self.emit(P.error("generic", action=P.ACTIONS["unknown"]))
            return report

        results: dict[str, C.ComponentResult] = {}
        started_stack: list[str] = []  # long-lived processes THIS run spawned
        for name in C.START_ORDER:
            if name in self.skip:
                results[name] = C.ComponentResult(name, "SKIPPED", "skipped by request")
                continue
            res = self._start_component(name)
            results[name] = res
            if res.fresh:
                started_stack.append(name)
            if res.status == C.HEALTHY:
                self.emit(f"  {P.component_label(name)}: ✓")
                continue
            # Report honestly, then decide severity.
            if name in C.CRITICAL:
                self.emit(f"  {P.component_label(name)}: ✗ " +
                          P.error({"stores": "db", "engine": "engine"}.get(name, "generic"),
                                  action=P.ACTIONS.get(
                                      {"stores": "db", "engine": "engine_down"}.get(name, "unknown"))))
            else:
                # The Persian templates carry {port}/{sec} placeholders; a
                # substitution left out would reach the owner literally.
                fmt: dict = {}
                if name == "gateway":
                    if res.detail == "foreign_busy":
                        gw = self.gateway
                        fmt["port"] = P.fa(gw.get("port") or 3000)
                    else:
                        fmt["sec"] = P.fa(int(self.health_wait.get(name, 60)))
                self.emit(f"  {P.component_label(name)}: ⚠ " +
                          P.error("generic",
                                  action=P.ACTIONS.get(_optional_action(name, res), "unknown"),
                                  **fmt))
            if name in C.CRITICAL:
                # Roll back the processes we brought up; leave nothing half-alive.
                # Components that were already running before us are left alone.
                self._stop_components([n for n in reversed(started_stack) if n != name])
                cp = self._control_plane(results)
                cp.safe_halt(f"critical component {name} failed: {res.detail}")
                return self._report("start", "FAILED", results, pf,
                                    cp_status="SAFE_HALT", failure=name)

        self.emit(P.PROGRESS["health"])
        cp = self._control_plane(results)
        cp_run = cp.start()
        cp_status = cp_run.get("status", "UNKNOWN")
        idle = cp_run.get("idempotent_replay", False)
        if idle:
            self.emit(P.PROGRESS["already_running"])

        # The control plane owns the halt decision; the launcher owns the honest
        # owner-facing verdict. An OPTIONAL component that is down leaves the
        # local stack degraded even though the canonical plane still reports the
        # system online, so the snapshot is folded in here rather than in the
        # canonical surface (which never sees gateway/telegram as authoritative).
        down = [n for n, r in results.items()
                if r.status in (C.UNHEALTHY, C.UNAVAILABLE)]
        if cp_status == "SAFE_HALT":
            overall = "FAILED"
        elif down:
            overall = "DEGRADED"
        else:
            overall = "ONLINE"
        if cp_status == "SAFE_HALT":
            self._stop_components([n for n in PROCESS_COMPONENTS
                                   if results.get(n) and results[n].status == C.HEALTHY])
            cp.safe_halt("control plane declared SAFE_HALT after component health snapshot")

        # Dashboard only when the gateway is actually serving.
        if overall in ("ONLINE", "DEGRADED") and results.get("gateway") and \
                results["gateway"].status == C.HEALTHY and self.open_dashboard and not idle:
            self.emit(P.PROGRESS["dashboard"])
            pk.open_url(self.dashboard_url())

        self.emit(P.PROGRESS["done_online"] if overall == "ONLINE"
                  else P.PROGRESS["done_degraded"])
        return self._report("start", overall, results, pf, cp_status=cp_status,
                            cp_run=cp_run, duration=self.clock() - t0)

    # -------------------------------------------------------------------- stop --
    def stop(self) -> dict:
        self.emit(P.PROGRESS["stopping"])
        t0 = self.clock()
        order = [n for n in reversed(C.START_ORDER) if n in PROCESS_COMPONENTS]
        stopped = self._stop_components(order)
        # Sweep for AHOS processes that lost their pid bookkeeping.
        swept = self._sweep_ours()
        cp = self._control_plane({})
        cp_stop = cp.stop()
        if stopped or swept:
            self.emit(P.PROGRESS["stopped"])
        else:
            self.emit(P.PROGRESS["nothing_to_stop"])
        return self._report("stop", "STOPPED" if (stopped or swept) else "NOT_RUNNING",
                            self._stop_results(stopped), cp_status=cp_stop.get("status"),
                            swept=swept, duration=self.clock() - t0)

    def _stop_results(self, stopped: dict[str, dict]) -> dict[str, C.ComponentResult]:
        """``_stop_components`` returns plain dicts; the report builder needs
        ``ComponentResult`` objects. A component we just stopped is reported as
        ``STOPPED`` with the termination method as its detail, so the receipt
        names what was halted instead of crashing on the dict."""
        out: dict[str, C.ComponentResult] = {}
        for name, info in stopped.items():
            out[name] = C.ComponentResult(
                name, "STOPPED",
                f"stopped ({info.get('how', '?')}, {info.get('secs', '?')}s)",
                pid=info.get("pid"))
        return out

    def _stop_components(self, order: list[str]) -> dict[str, dict]:
        stopped: dict[str, dict] = {}
        for name in order:
            info = self._pid_info(name)
            pid = info.get("pid") if info else None
            if not pid or not pk.pid_alive(pid):
                pk.clear_pid(self.state_dir, name)
                continue
            how, secs = pk.terminate(pid)
            pk.clear_pid(self.state_dir, name)
            stopped[name] = {"pid": pid, "how": how, "secs": round(secs, 1)}
            self.emit(f"  {P.component_label(name)}: متوقف شد ({P.fa(round(secs, 1))}s, {how})")
        return stopped

    def _sweep_ours(self) -> list[int]:
        """Stop processes this launcher (or a recorded component) actually spawned.

        Identification is strict **parentage**, not a substring marker: one
        Toolhelp32 snapshot gives pid+ppid for the whole system, and a candidate
        qualifies only if walking its parents reaches the launcher pid or one of
        the recorded component pids. A marker alone cannot prove ownership — the
        old sweep matched editor-spawned ``next dev``/``tsc``/vitest processes
        that merely ran from this checkout (Rostam R3). The marker check survives
        as a second line of defence on the handful of candidates that passed.
        """
        roots = {(self._pid_info(n) or {}).get("pid") for n in PROCESS_COMPONENTS}
        roots.add(os.getpid())
        markers = [m for m, _ in self.sweep_markers() if m]

        procs = pk.process_snapshot()
        if not procs:
            return []
        candidates = []
        for pid, info in procs.items():
            if pid in roots or not pk.pid_alive(pid):
                continue
            if (info.get("name") or "").lower() not in ("python.exe", "node.exe",
                                                        "cmd.exe", "pythonw.exe"):
                continue
            if pk.descendant_of(pid, roots, procs):
                candidates.append(pid)
        if not candidates:
            return []
        pk.fill_cmdlines(procs, candidates)
        found: list[int] = []
        for pid in candidates:
            cmdline = procs.get(pid, {}).get("cmdline") or ""
            if any(m.lower() in cmdline.lower() for m in markers):
                pk.terminate(pid)
                found.append(pid)
        return found

    # ------------------------------------------------------------------ status --
    def status(self) -> dict:
        results: dict[str, C.ComponentResult] = {}
        for name in C.START_ORDER:
            status, detail = self._component_probe(name)
            info = self._pid_info(name)
            results[name] = C.ComponentResult(name, status, detail,
                                              pid=info.get("pid") if info else None,
                                              started_ts=info.get("started_ts") if info else None)
        cp = self._control_plane(results)
        cp_status = cp.status()
        # The same ladder as ``start``: an OPTIONAL component that is down leaves
        # the stack degraded, not down. Mapping UNAVAILABLE to DOWN made a fully
        # working stack report DOWN and exit 1 whenever the (optional, and on
        # this host unbindable) gateway was absent, so `AHOS Status` looked red
        # while the engine was healthy.
        down = [n for n, r in results.items()
                if r.status in (C.UNHEALTHY, C.UNAVAILABLE)]
        critical_down = [n for n in down if n in C.CRITICAL]
        if critical_down:
            overall = "DOWN"
        elif down:
            overall = "DEGRADED"
        else:
            overall = "ONLINE"
        return self._report("status", overall, results, None,
                            archive=False, cp_status=cp_status.get("system"))

    # ------------------------------------------------------- control plane wiring --
    def _control_plane(self, results: dict[str, C.ComponentResult]) -> LauncherControlPlane:
        """Probers read live state at call time, so a START records what is
        actually running rather than what we hoped to start."""
        probers = {}
        for name in C.START_ORDER:
            res = results.get(name)
            probers[name] = (lambda now, r=res: (r.status if r else C.UNKNOWN,
                                                 (r.detail if r else "no probe result")))
        return LauncherControlPlane(probers, ledger_path=self.ledger_path, clock=self.clock)

    # ----------------------------------------------------------------- reports --
    # How many timestamped status archives we keep. Only state-changing actions
    # (start/stop/restart) archive anything, so this bounds the receipt history;
    # a plain status poll refreshes `status.json` alone, otherwise the dashboard's
    # few-second poll cadence would bury the receipts under thousands of copies
    # (e5).
    MAX_STATUS_ARCHIVES = 12

    def _prune_archives(self, keep: int = MAX_STATUS_ARCHIVES) -> None:
        """Keep the newest ``keep`` timestamped status archives."""
        try:
            archives = sorted(self.report_dir.glob("status_*.json"))
        except OSError:
            return
        for old in archives[:-keep]:
            try:
                old.unlink()
            except OSError:
                continue

    def _report(self, action: str, overall: str,
                results: dict[str, object], pf: C.Preflight | None = None, *,
                archive: bool = True, **extra) -> dict:
        comp = {}
        for name, res in (results or {}).items():
            comp[name] = {"status": res.status, "detail": res.detail[:400],
                          "pid": res.pid, "critical": name in C.CRITICAL}
            if res.started_ts is not None:
                comp[name]["started_ts"] = res.started_ts
        ts = datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()
        report = {
            "action": action,
            "ts": ts,
            "overall": overall,
            "paper_only": True,
            "components": comp,
            "dashboard_url": self.dashboard_url(),
            # The port children were actually handed. Need not equal the
            # configured one on a host where it is Windows-reserved (scope d).
            "gateway_port": self.gateway.get("port"),
            "gateway_chosen_via": self.gateway.get("chosen_via") or "RESOLVED",
            "gateway_warnings": list(self.gateway.get("warnings") or []),
            "db_backend": C.database_target(self.env),
            "preflight": ([{"name": c["name"], "ok": c["ok"], "detail": c["detail"]}
                           for c in pf.checks] if pf else None),
        }
        report.update({k: v for k, v in extra.items() if v is not None})
        # status.json is the mutable "latest"; a timestamped archive is the
        # receipt. Only state-changing actions get a receipt.
        (self.report_dir / "status.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if archive:
            (self.report_dir / self.report_name()).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            self._prune_archives()
        return report


def _optional_action(name: str, res: C.ComponentResult) -> str:
    if name == "db_backend":
        return "db_pg_unreachable"
    if name == "gateway":
        if res.detail == "foreign_busy":
            return "gateway_port_busy"
        return "gateway_down"
    if name == "telegram":
        return "telegram_missing_token"
    return "unknown"
