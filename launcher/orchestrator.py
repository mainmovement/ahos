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
# The gateway's budget has to cover a *cold* dev compile: the probe targets
# /api/launcher (the cheapest route in the app) but on a slow filesystem
# Turbopack's first compile of even that one route has been measured past the
# 120s this once allowed, so a healthy gateway read UNAVAILABLE and an OPTIONAL
# failure degraded a boot whose only defect was the compile. The smoke pins dev
# mode, so this is the cost a real cold boot pays, not a hypothetical.
HEALTH_WAIT = {"stores": 60, "db_backend": 10, "gateway": 240, "telegram": 25,
               "engine": 420,
               # Telegram health requires the bot to have *survived* its own
               # preflight, not merely to have started (M11.4): how many seconds
               # a recorded pid must have been alive before HEALTHY is even
               # possible. The boot loop also waits for run_bot.py's readiness
               # line; this is the minimum bar, and it is shorter than the
               # "telegram" budget so a healthy bot is not held hostage to it.
               "telegram_stable": 8}


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
        # A later process (dashboard Status/Stop, `ahos.ps1 status`) must see the
        # port the start-time selection actually handed the children, not the
        # configured one -- but only while our gateway is the live listener.
        recorded = self._recorded_gateway()
        if recorded is not None:
            self.gateway = recorded

    # ------------------------------------------------------- gateway record --
    GATEWAY_RECORD = "gateway_selected.json"

    def _gateway_record_path(self) -> Path:
        return self.state_dir / self.GATEWAY_RECORD

    def _write_gateway_record(self, sel: dict) -> None:
        keep = {k: sel.get(k) for k in ("host", "port", "url", "source",
                                         "configured_port", "chosen_via")}
        keep["recorded_ts"] = self.clock()
        try:
            self._gateway_record_path().write_text(
                json.dumps(keep, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # a missing record degrades to the pure resolver; never fatal

    def _clear_gateway_record(self) -> None:
        try:
            self._gateway_record_path().unlink()
        except OSError:
            pass

    def _recorded_gateway(self) -> dict | None:
        """The start-time selection, if our gateway process is still the one the
        pid file names. A record whose gateway is gone is ignored (never pins a
        dead port)."""
        try:
            rec = json.loads(self._gateway_record_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(rec, dict) or not isinstance(rec.get("port"), int):
            return None
        info = self._pid_info("gateway")
        if not (info and pk.pid_is_ours(info.get("pid"), self.marker("gateway"))):
            return None
        rec.setdefault("warnings", [])
        return rec

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

    def bootstrap_url(self) -> str:
        """A fresh one-time dashboard login URL (``#boot=<token>``).

        Used when the launcher opens the browser, and by
        ``python -m launcher bootstrap-url`` for a browser opened by hand.
        Callers must not log the result; it is a short-lived credential.
        """
        token = C.issue_dashboard_boot_token(C.dashboard_boot_file(self.state_dir))
        return C.bootstrap_url(self.dashboard_url(), token)

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
            # The argv we actually spawn (M11.3): the next CLI path, which every
            # component's marker is derived from. Never hand-written — an earlier
            # hand-written engine marker never matched the live command line and
            # broke identification wholesale; see docs/ONE_CLICK.md,
            # "Process identification".
            gw_cmd = C.gateway_command(self.root, "prod")
            return gw_cmd[1] if len(gw_cmd) > 1 else str(self.root / "node_modules")
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

    def _our_live_gateway_port(self) -> int | None:
        """The port our own running gateway bound, or None if it is not ours.

        ``select_port`` can only ask "could I bind this?"; a port held by our own
        listener answers no, even though it is perfectly serviceable. This reads
        the port recorded when the gateway was spawned and accepts it only when
        that pid is still ours and still alive — a stale pid record left by a
        crashed gateway is not adopted.
        """
        info = self._pid_info("gateway") or {}
        pid = info.get("pid")
        port = info.get("port")
        if not pid or not isinstance(port, int) or port < 1:
            return None
        if not pk.pid_alive(pid):
            return None
        # The gateway is spawned as ``node <next cli> start``, so its live command
        # line carries the same marker the engine and the bot are identified by
        # (M11.3). Before that it ran as ``cmd /c npm run start``, whose command
        # line carried no repo substring at all, and this check was a cmdline
        # comparison against the record instead; that fallback is gone because a
        # true marker makes it unnecessary — and because its quoting/casing
        # normalisation would now compete with a check that already answers.
        if not pk.pid_is_ours(pid, self.marker("gateway")):
            return None
        return port if pk.port_in_use(info.get("host") or "127.0.0.1", port) else None

    def _pid_is_recorded_or_marked(self, name: str, info: dict) -> bool:
        """The recorded pid is still the process we spawned.

        Every long-lived component is spawned with an argv whose own command line
        carries its marker — including the gateway, which was the last one still
        launched through a ``cmd /c npm`` wrapper whose command line carried
        nothing identifying (M11.3). Without a true marker, a second ``start``
        read our own live gateway as a foreign listener (``foreign_busy``), told
        the owner some other program held the port, and went DEGRADED; the
        stop-gap was a recorded-vs-live cmdline comparison, which a true marker
        makes redundant — and which would now be a second, stricter opinion on a
        question the marker already answers, so it is gone. Windows re-issues
        pids, but a re-issued pid's command line does not contain this checkout's
        next CLI path.
        """
        return pk.pid_is_ours(info.get("pid"), self.marker(name))


    def _adopted_gateway(self, sel: dict) -> dict:
        """``sel`` with our own already-running listener's port substituted in.

        ``select_port`` can only ask "could I bind this?"; a port held by our own
        listener answers no, so a *start* that re-runs while our gateway is up
        walks off the configured port and every candidate, and a *status* poll
        probes the configured address and reports the gateway down while the
        dashboard is in fact serving on the port chosen last time. The pid record
        written at spawn time names that port, and is accepted only when the pid
        is still ours and still listening — a stale record left by a crashed
        gateway is not adopted. ``start`` and ``status`` both route through here
        so the probe and the owner's browser always open the address serving.
        """
        live = self._our_live_gateway_port()
        configured = int(sel.get("port") or 3000)
        if not live or live == configured:
            return sel
        via = sel.get("chosen_via")
        if via not in (None, "CONFIGURED_UNUSABLE_KEPT_ANYWAY"):
            return sel
        return {**sel, "port": live,
                "url": C.gateway_url_at(sel.get("host") or "127.0.0.1", live),
                "chosen_via": "ADOPTED_OUR_LIVE_LISTENER",
                "notes": list(sel.get("notes") or [])
                + [f"adopted port {live} from our already-running gateway"]}

    def component_state(self, name: str) -> str:
        """ours_running | foreign_busy | down — the idempotency primitive."""
        if name not in PROCESS_COMPONENTS:
            # No long-lived process to track: "ours" means the probe passes.
            return "ours_running" if self._component_probe(name)[0] == C.HEALTHY else "down"
        info = self._pid_info(name)
        if info and self._pid_is_recorded_or_marked(name, info):
            if name == "gateway":
                # The pid record proves we *spawned* something still alive, not
                # that it is still serving our app. A stale server left over from
                # an older build or another checkout holds the port, answers the
                # probe, and 404s every route the dashboard needs — and because
                # it is recorded as ours it is replayed as "already running" on
                # every later start, so the real gateway is never restarted and
                # the panel reads ONLINE while every control is dead. Once the
                # gateway has had its boot budget, require the route probe as
                # well: during boot the compile can legitimately outrun the
                # probe, so a young gateway is trusted on its pid record alone.
                started = info.get("started_ts")
                budget = self.health_wait.get("gateway", 60)
                if started is None or self.clock() - float(started) > budget:
                    if self._component_probe("gateway")[0] != C.HEALTHY:
                        return "down"
            return "ours_running"
        if name == "gateway":
            info_gw = self.gateway
            host = info_gw.get("host") or "127.0.0.1"
            port = int(info_gw.get("port") or 3000)
            if pk.port_in_use(host, port):
                return "foreign_busy"
            # Nothing accepts — but if we cannot bind either, the port is still
            # not ours to serve on. A foreign listener that never accepts makes
            # the connect probe above hang and read as free, and a Windows
            # excluded range fails bind with nobody listening at all. Spawning in
            # either case just burns the whole health budget on a listen error
            # ``select_gateway`` had already diagnosed. (Had the listener been
            # ours, the pid check above would have said "ours_running".)
            if not pk.can_bind(host, port):
                return "unusable"
        return "down"

    def _telegram_stable_sec(self) -> float:
        return float(self.health_wait.get("telegram_stable", C.TELEGRAM_STABLE_SEC))

    def _component_probe(self, name: str, *, heartbeat_age: float | None = None):
        if name == "stores":
            return C.probe_stores(self.clock())
        if name == "db_backend":
            return C.probe_db_backend(C.database_target(self.env), self.clock(), root=self.root)
        if name == "gateway":
            return C.probe_gateway(self.dashboard_url(), self.clock())
        if name == "telegram":
            # Read-only path: a bot that has served for hours may have had its
            # log rotated by hand, so the readiness mark is not required here —
            # but liveness and the stability window always are. Nothing weaker
            # than probe_process can ever decide telegram health again (M11.4).
            return C.probe_telegram(self._pid_info("telegram"),
                                    self.marker("telegram"),
                                    now=self.clock(),
                                    min_uptime=self._telegram_stable_sec(),
                                    require_ready=False)
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
        return C.read_log_tail(self.log_path(name), lines=lines)

    # ------------------------------------------------------------- components --
    def _spawn(self, name: str, cmd: list[str], env: dict,
               extra: dict | None = None) -> int:
        self.emit(P.PROGRESS[name] if name in P.PROGRESS else f"{name} …")
        pid = pk.spawn_detached(cmd, cwd=self.root, env=env,
                                log_path=self.log_path(name))
        pk.write_pid(self.state_dir, name, pid,
                     {"cmd": " ".join(cmd), "marker": self.marker(name),
                      "log": str(self.log_path(name)),
                      "started_ts": self.clock(), **(extra or {})})
        return pid

    def _start_component(self, name: str) -> C.ComponentResult:
        # Idempotent: if one of ours is already up, keep it and say so.
        state = self.component_state(name)
        if state == "ours_running":
            info = self._pid_info(name) or {}
            self.emit(f"  {P.component_label(name)}: از قبل در حال اجراست (pid {info.get('pid')})")
            if name == "telegram":
                # "One of ours is alive" is not "healthy": a bot a few seconds
                # old is still inside its own preflight, and asserting HEALTHY
                # here would announce ONLINE for a bot about to exit (M11.4).
                # Probe it by the same rule the boot loop uses, so a second
                # concurrent start reports what the bot actually is.
                status, detail = C.probe_telegram(
                    info, self.marker("telegram"), now=self.clock(),
                    min_uptime=self._telegram_stable_sec(), require_ready=False)
                return C.ComponentResult(name, status, detail,
                                         pid=info.get("pid"),
                                         started_ts=info.get("started_ts"))
            return C.ComponentResult(name, C.HEALTHY, "already running (idempotent)",
                                     pid=info.get("pid"), started_ts=info.get("started_ts"))
        if state == "foreign_busy":
            return C.ComponentResult(name, C.UNHEALTHY, "foreign_busy")
        if state == "unusable":
            # Distinguished from foreign_busy because the Persian action for a
            # port another program holds would be a lie here: the OS reserves it.
            return C.ComponentResult(name, C.UNHEALTHY, "port_not_bindable")

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
        """Bring up / verify the DB backend before the gateway (M10.1).

        PGlite: when PG_VERSION is missing, run schema-only
        ``scripts/pglite_restore.ts`` once (no --dump), CREATE_NO_WINDOW on
        Windows. Postgres: probe only — never db:migrate / db:push (STATE B).
        """
        self.emit(P.PROGRESS["db_backend"])
        target = C.database_target(self.env)
        if not target["configured"]:
            return C.ComponentResult("db_backend", C.UNKNOWN,
                                     "DATABASE_URL not configured; gateway will fail closed")

        evidence: dict = {"scheme": target.get("scheme"),
                          "init_action": C.decide_pglite_init_action(target)}
        action = evidence["init_action"]

        if action == "noop_not_pglite":
            status, detail = C.probe_db_backend(target, self.clock(), root=self.root)
            return C.ComponentResult("db_backend", status, detail, evidence=evidence)

        if action == "noop_no_dir":
            return C.ComponentResult(
                "db_backend", C.UNHEALTHY,
                "pglite scheme without a data dir", evidence=evidence)

        ddir = target.get("data_dir")
        if action == "restore":
            self.emit("  داده‌ی PGlite خالی است؛ اسکیما اعمال می‌شود.")
            argv = (self.command_overrides.get("db_backend_restore")
                    or C.pglite_restore_argv(self.root, ddir))
            if not argv:
                return C.ComponentResult(
                    "db_backend", C.UNAVAILABLE,
                    "node not on PATH; cannot run pglite schema restore",
                    evidence=evidence)
            runner = self.command_overrides.get("db_backend_restore_runner")
            try:
                if callable(runner):
                    code, tail = runner(argv, str(self.root), self._child_env())
                    evidence["restore"] = {"returncode": code, "detail": tail[:400]}
                    if code != 0:
                        return C.ComponentResult(
                            "db_backend", C.UNAVAILABLE,
                            f"pglite schema restore failed ({code}): {tail[:300]}",
                            evidence=evidence)
                else:
                    res = C.run_pglite_tool(
                        argv, cwd=self.root, env=self._child_env(), timeout=600.0)
                    tail = ((res.stdout or "") + (res.stderr or "")).strip()
                    evidence["restore"] = {
                        "returncode": res.returncode,
                        "detail": tail[-400:],
                    }
                    if res.returncode != 0:
                        return C.ComponentResult(
                            "db_backend", C.UNAVAILABLE,
                            f"pglite schema restore failed ({res.returncode}): "
                            f"{tail[-300:]}",
                            evidence=evidence)
            except Exception as e:
                evidence["restore"] = {"error": type(e).__name__}
                return C.ComponentResult(
                    "db_backend", C.UNAVAILABLE,
                    f"restore exception: {type(e).__name__}: {e}",
                    evidence=evidence)
            evidence["restore_ran"] = True
        else:
            evidence["restore_ran"] = False

        # After optional restore: real table probe via --check (injectable).
        check_runner = self.command_overrides.get("db_backend_check_runner")
        status, detail = C.probe_db_backend(
            target, self.clock(), root=self.root,
            check_runner=check_runner if callable(check_runner) else None)
        evidence["probe"] = {"status": status, "detail": detail[:300]}
        return C.ComponentResult("db_backend", status, detail, evidence=evidence)

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
                if not cmd:
                    # node or node_modules/next is missing. The old fallback was
                    # the ``cmd /c npm`` wrapper, which is exactly the argv this
                    # component's identity is built on (M11.3): spawning it
                    # anyway would put up a dashboard the launcher can never
                    # recognise as its own. Report it, do not paper over it.
                    return C.ComponentResult(
                        name, C.UNAVAILABLE,
                        "node or node_modules/next not found; cannot start the gateway "
                        "(install node and run `npm install`)")
            elif name == "engine":
                cmd = C.engine_command(py)
            elif name == "telegram":
                cmd = C.telegram_command(py)
            else:
                return C.ComponentResult(name, C.UNKNOWN, "no command")
        env = self._child_env(extra={} if name == "gateway" else {})
        # Record the port the gateway was told to bind. The next `start` process
        # cannot re-bind it (our own listener holds it), so it reads this record
        # and adopts the live port instead of reporting the dead configured one.
        spawn_extra = {"port": int(self.gateway.get("port") or 0)} \
            if name == "gateway" else None
        if name == "telegram":
            # The readiness search must ignore everything a *previous* bot wrote:
            # the log is append-only across restarts, so a mark from the last run
            # would satisfy it while this bot is still failing preflight. The
            # byte offset at spawn is where this bot's output begins.
            lp = self.log_path("telegram")
            spawn_extra = {"log_offset": lp.stat().st_size if lp.exists() else 0}
        try:
            pid = self._spawn(name, cmd, env, extra=spawn_extra)
        except Exception as e:
            return C.ComponentResult(name, C.UNAVAILABLE, f"spawn failed: {type(e).__name__}: {e}")

        t0 = self.clock()
        deadline = t0 + self.health_wait.get(name, 60)
        last: tuple[str, str] | None = None
        booting_note = False
        while self.clock() < deadline:
            if name == "telegram":
                # run_bot.py exits fast when its own preflight fails; catch that
                # and report it with its last lines instead of letting the loop
                # run out the clock on a pid that is already gone (M11.4).
                if pk.pid_alive(pid) is False:
                    tail, kinds = C.redact_log(self._log_tail("telegram", lines=3))
                    note = (" (a stored secret was redacted from this log)"
                            if kinds else "")
                    return C.ComponentResult(
                        "telegram", C.UNAVAILABLE,
                        f"exited during its own preflight{note}; last log lines: {tail}",
                        pid=pid, fresh=True)
                status, detail = C.probe_telegram(
                    self._pid_info("telegram"), self.marker("telegram"),
                    now=self.clock(), min_uptime=self._telegram_stable_sec(),
                    require_ready=True)
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
        if name == "telegram":
            # The bot's log can carry the token in a preflight echo; the tail
            # reaches the owner-facing report, so redact it (M11.4).
            tail = C.redact_log(tail)[0]
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
        recorded = self._recorded_gateway()
        if recorded is not None:
            # Our gateway already listens on the recorded port. A fresh select
            # would see that port busy (ours) and walk on to the next candidate,
            # handing the children an address nobody serves.
            sel = dict(recorded, chosen_via="RECORDED_RUNNING")
        else:
            sel = self._adopted_gateway(sel)
            self._write_gateway_record(sel)
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
            # Soft findings (pf.warnings, e.g. no Gemini credential) are not a
            # failed service; printing "a service did not run" for them made a
            # fully ONLINE start open with an error line.
            if not chk["ok"] and chk["detail"] not in pf.warnings:
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
        # Record the exclusions this start was asked to honour, before the
        # results loop makes them invisible: a component never spawned has no pid
        # record, so the next read-only poll reads it as UNAVAILABLE, the marker
        # is lost, and a dashboard restart brings up the whole stack. ``status``
        # and ``stop`` both read this record back.
        self._persist_skips(self.skip)
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
                        fmt["port"] = P.fa(self.gateway.get("port") or 3000)
                    elif res.detail != "port_not_bindable":
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
            pk.open_url(self.bootstrap_url())

        self.emit(P.PROGRESS["done_online"] if overall == "ONLINE"
                  else P.PROGRESS["done_degraded"])
        return self._report("start", overall, results, pf, cp_status=cp_status,
                            cp_run=cp_run, duration=self.clock() - t0)

    # -------------------------------------------------------------------- stop --
    def stop(self) -> dict:
        self.emit(P.PROGRESS["stopping"])
        # R12: when the dashboard's stop/restart route launched this orchestrator
        # it is a descendant of the gateway it must stop, and terminate() signals
        # the gateway's whole process group. Immunity has to be armed before a
        # single signal goes out, or this process dies mid-stop and strands the
        # listener (the wedge behind every failed dashboard-api receipt).
        pk.arm_console_break_immunity()
        t0 = self.clock()
        # The gateway's listening socket can outlive its pid record: a hard kill
        # of the launcher (console close, harness timeout) orphans the detached
        # children, ``launcher start`` exits as soon as the health probe passes,
        # and a record cleared while the listener still runs makes it unreachable
        # by the parentage sweep below. Capture the address before anything clears
        # the record, so a stranded listener can still be reclaimed.
        gw_addr = self._gateway_listen_addr()
        order = [n for n in reversed(C.START_ORDER) if n in PROCESS_COMPONENTS]
        stopped = self._stop_components(order)
        # Sweep for AHOS processes that lost their pid bookkeeping.
        swept = self._sweep_ours()
        self._clear_gateway_record()
        # And the listener itself, which no pid record may still name.
        reclaimed = self._reclaim_gateway_port(*gw_addr) if gw_addr else None
        cp = self._control_plane({})
        cp_stop = cp.stop()
        if stopped or swept or reclaimed:
            self.emit(P.PROGRESS["stopped"])
        else:
            self.emit(P.PROGRESS["nothing_to_stop"])
        # The stop receipt is also the status.json the dashboard's restart reads
        # next, so the carried-forward exclusions must survive it too: without
        # them the restart after a stop would start everything.
        report_results = self._stop_results(stopped)
        report_results.update(self._report_skips())
        return self._report("stop", "STOPPED" if (stopped or swept or reclaimed) else "NOT_RUNNING",
                            report_results, cp_status=cp_stop.get("status"),
                            swept=swept, reclaimed=reclaimed,
                            duration=self.clock() - t0)

    # ----------------------------------------------------------------- restart --
    def restart(self) -> dict:
        """Stop, wait for the gateway's port to be released, then start.

        A fixed sleep cannot do this: the listening socket is freed about a
        second after ``taskkill /F`` returns (measured 1.1s here), so starting
        the next gateway immediately raced it and came back
        ``port_not_bindable`` — the stack restarted DEGRADED with no gateway,
        and the stranded listener then blocked every later start. The port is
        only safe to rebind once a real ``bind`` succeeds, so that is what we
        wait for, bounded: a port that never frees still returns a report
        instead of hanging the owner's desktop icon.
        """
        gw_addr = self._gateway_listen_addr()
        self.stop()
        if gw_addr:
            self._wait_port_free(gw_addr[0], gw_addr[1], 20.0)
        return self.start()

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

    def _skips_path(self) -> Path:
        return self.state_dir / "skips.json"

    def _gateway_listen_addr(self) -> tuple[str, int] | None:
        """The address our gateway bound, to be reclaimed on stop.

        Read from the pid record while it is still authoritative. When the record
        is gone — a stop that cleared it before dying, which is exactly the R12
        wedge this class now survives, or a crash — the *configured* port is the
        wrong answer on a host where Windows reserves it: the gateway is actually
        listening on a candidate port the launcher selected at start time. Ask
        the TCP table which candidate our own process holds and reclaim that, so
        a stranded listener stays reachable by ``stop``. Falls back to the
        configured port last, for a non-loopback or unrecognised setup.
        """
        info = self._pid_info("gateway") or {}
        port = info.get("port")
        if not isinstance(port, int) or port < 1:
            port = self._live_our_gateway_port()
        if not isinstance(port, int) or port < 1:
            port = self.gateway.get("port")
        if not isinstance(port, int) or port < 1:
            return None
        host = info.get("host") or self.gateway.get("host") or "127.0.0.1"
        return str(host), int(port)

    def _live_our_gateway_port(self) -> int | None:
        """A candidate port our own gateway is listening on right now.

        Only the TCP table can answer this once the pid record is gone, and only
        a listener we can prove is ours by the gateway marker counts — a foreign
        server on a candidate port is reported by the caller, not adopted here.
        """
        host = str(self.gateway.get("host") or "127.0.0.1")
        if host.lower() not in ("127.0.0.1", "localhost"):
            return None
        markers = [m for m, name in self.sweep_markers() if name == "gateway" and m]
        for cand in C.candidate_ports(self.env, config_file=C.GATEWAY_PORTS_CONFIG):
            owner = pk.port_owner(host, int(cand))
            if not owner:
                continue
            cmdline = pk.process_cmdline(owner) or ""
            if any(m.lower() in cmdline.lower() for m in markers):
                return int(cand)
        return None

    def _wait_port_free(self, host: str, port: int, timeout: float) -> bool:
        """Poll until ``host:port`` is bindable again. Returns the bind verdict.

        A fixed ``sleep`` races the kernel: the listening socket is released
        roughly a second after ``taskkill /F`` returns (measured 1.1s on this
        host), so a restart that starts immediately finds its own just-killed
        port still occupied and reports ``port_not_bindable`` for a gateway it
        had stopped cleanly. Only a real ``bind`` proves the port is ours again.
        """
        deadline = self.clock() + timeout
        while self.clock() < deadline:
            if pk.can_bind(host, port):
                return True
            time.sleep(0.2)
        return pk.can_bind(host, port)

    def _reclaim_gateway_port(self, host: str, port: int) -> int | None:
        """Stop a gateway listener that survived the shutdown of its recorded pid.

        The gateway runs as ``node <next cli> start``, so the recorded pid *is*
        the server and stopping the record's tree already stops the listener.
        What still strands one is a hard kill of the launcher itself (console
        close, harness timeout) rather than ``AHOS Stop``: the detached children
        survive with no parent to issue the tree kill, the pid record goes stale,
        and every later ``start`` then reports ``foreign_busy`` forever. Windows
        names the socket's owner, so after the recorded tree is stopped we ask
        the TCP table who is still listening and stop that tree too.

        Returns the reclaimed pid, or None when the port is already free — or
        when the survivor is not provably ours, which is left running and named
        in the receipt rather than killed blindly.
        """
        if pk.can_bind(host, port):
            return None
        owner = pk.port_owner(host, port)
        if not owner:
            return None
        # Never kill a process we cannot prove is ours: the gateway marker is this
        # checkout's own next CLI path, which only our gateway's command line
        # carries. A foreign server squatting on the same port is reported, not
        # terminated.
        cmdline = pk.process_cmdline(owner) or ""
        markers = [m for m, n in self.sweep_markers() if n == "gateway"]
        markers.append(str(self.root))
        if not any(m and m.lower() in cmdline.lower() for m in markers):
            self.emit(f"  {P.component_label('gateway')}: پورت هنوز توسط فرآیند "
                      f"ناشناس در استفاده است (pid {owner})؛ متوقف نشد")
            return None
        pk.terminate(owner)
        self._wait_port_free(host, port, 10.0)
        self.emit(f"  {P.component_label('gateway')}: شنود رها‌شدهٔ متروک متوقف شد "
                  f"(pid {owner})")
        return owner

    def _persist_skips(self, names) -> None:
        """Record the components a start was asked to skip (DEFECT A).

        A skipped component is never spawned, so it leaves no pid record; the
        next ``status`` poll then reads it as UNAVAILABLE and reports the stack
        wider than the owner asked. Writing the request down here lets ``status``
        and ``stop`` restore the SKIPPED marker so the dashboard's restart
        re-applies the same exclusions instead of silently widening the stack.
        An empty set clears the record: a start with no skips wants everything.
        """
        path = self._skips_path()
        keep = sorted(n for n in (names or []) if n in C.START_ORDER)
        try:
            if keep:
                path.write_text(json.dumps({"skipped": keep}, ensure_ascii=False,
                                           indent=2), encoding="utf-8")
            elif path.exists():
                path.unlink()
        except OSError:
            pass

    def _applied_skips(self) -> set[str]:
        """The exclusions the last start honoured (empty when it wanted all)."""
        path = self._skips_path()
        if not path.exists():
            return set()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        return {n for n in (data.get("skipped") or []) if n in C.START_ORDER}

    def _report_skips(self) -> dict[str, C.ComponentResult]:
        """SKIPPED entries for the exclusions the last start honoured."""
        return {n: C.ComponentResult(n, "SKIPPED",
                                     "skipped by request (carried forward)")
                for n in self._applied_skips()}

    # ------------------------------------------------------------------ status --
    def status(self) -> dict:
        # Probe the address actually serving, not the configured one. The
        # configured port is Windows-reserved on this host; the gateway chose a
        # bindable candidate at spawn time and has served on it since. A
        # read-only poll that opens the configured port reports the gateway down
        # while the dashboard is in fact reachable — see the companion adoption
        # in ``start``, which must agree with this on the address it reports.
        self.gateway = self._adopted_gateway(self.gateway)
        results: dict[str, C.ComponentResult] = {}
        for name in C.START_ORDER:
            status, detail = self._component_probe(name)
            info = self._pid_info(name)
            results[name] = C.ComponentResult(name, status, detail,
                                              pid=info.get("pid") if info else None,
                                              started_ts=info.get("started_ts") if info else None)
        # Restore the SKIPPED marker the probe cannot see: a component the last
        # start was asked to skip has no pid record, so it probes UNAVAILABLE and
        # the dashboard's restart would widen the stack. Only a component that
        # probes UNAVAILABLE or UNKNOWN is relabelled — a live one keeps whatever
        # the probe said, even if it was started by hand.
        for name, res in self._report_skips().items():
            if results.get(name) and results[name].status in (C.UNAVAILABLE, C.UNKNOWN):
                results[name] = res
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
            if getattr(res, "evidence", None):
                comp[name]["evidence"] = res.evidence
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
        if res.detail == "port_not_bindable":
            return "gateway_port_reserved"
        return "gateway_down"
    if name == "telegram":
        return "telegram_missing_token"
    return "unknown"
