"""Real-process smoke evidence for the one-click launcher.

Runs the *actual* CLI (``python -m launcher ...``) end to end against this
checkout and saves the captured console output plus the status reports as
evidence under ``reports/launcher/``. Two cases:

  idempotent  start -> status -> start (must be an idempotent replay)
              -> stop -> start -> stop. Proves the owner can double-click the
              icon repeatedly and the stack converges instead of double-booting.
  port-busy   a foreign socket holds the gateway port; START must report the
              Persian port-busy error and degrade instead of claiming ONLINE.

Never leaves a started component behind: every case ends with STOP and STOP is
also attempted in a ``finally``. Reality ladder: this is real-process evidence,
so the artefact it exercises can claim VERIFIED/OPERATIONAL only when a human
reads the receipts — the script itself only records what happened.

Gateway mode defaults to ``dev`` so a stale ``.next`` build cannot turn the
smoke run into a 15-minute build; the production-build attempt is a separate,
explicitly recorded step.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Running this file as a script puts *its own directory* on sys.path, not the
# repo root, so `import launcher.components` would fail without this. The
# idempotent case needs no imports, but port-busy does.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_DIR = ROOT / "reports" / "launcher"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
# Every child this module spawns must be window-less: the smoke runs the real
# CLI, and a console flashing open on the owner's desktop would violate the
# one-click contract the launcher exists to deliver.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# Per-action wall clocks. The engine's first scheduler cycle is the long pole:
# HEALTH_WAIT["engine"] alone is 420s, and the first observation cycle on a cold
# host has been measured at ~21 minutes.
TIMEOUTS = {"start": 1500.0, "status": 45.0, "stop": 90.0, "restart": 1500.0}
# The dashboard route re-spawns the whole orchestrator, so a restart costs a
# full start of the same component set and a stop a full sequential teardown.
# Derived from TIMEOUTS so the poll budget cannot drift below the timeout the
# table already budgets for that work: hand-typed 900/300 once proved shorter
# than the cold restart the route was actually performing, so the smoke reported
# a restart as failed ~44 minutes into one that succeeded. The route forwards the
# running stack's SKIPPED set (see app/api/launcher/route.ts), so with the engine
# skipped the real cost is seconds — but the budget must hold for the full stack.
_CHILD_SLACK = 180.0  # child report write + poll cadence + a slower-than-CLI teardown
_RESTART_DEADLINE = TIMEOUTS["restart"] + _CHILD_SLACK
_STOP_DEADLINE = TIMEOUTS["stop"] + _CHILD_SLACK
# Where the control audit ledger lives (chat_control_gate.defaultAuditPath).
AUDIT_PATH = ROOT / "data" / "control_audit" / "chat_control_audit.jsonl"


def _utcstamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _base_env(mode: str) -> dict:
    env = dict(os.environ)
    env["AHOS_GATEWAY_MODE"] = mode
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _can_bind(host: str, port: int) -> tuple[bool, str | None]:
    """Can this process actually listen on host:port? Returns the failure reason.

    Windows reserves wide TCP ranges for Hyper-V/WSL (``netsh int ipv4 show
    excludedportrange protocol=tcp``); a ``port_in_use`` connect probe reports
    such a port as free while ``bind`` still fails with WinError 10013. The
    injection must squat on a port the OS will actually let it hold.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return True, None
    except OSError as e:
        return False, f"winerror={getattr(e, 'winerror', None)} {e}"
    finally:
        s.close()


def _bindable_port(host: str, preferred: int,
                   candidates: tuple[int, ...] = ()) -> tuple[int, list[str]]:
    """The preferred port if the OS lets us bind it, else the first candidate
    that works.

    ``candidates`` comes from the shared resolver (env > config/gateway_ports.json
    > in-code default). This module carried its own ``range(3450, 3950)`` once,
    which silently drifted from the list the launcher actually walks (e8): a
    smoke that squats on a port the launcher would never consider proves nothing.
    """
    notes: list[str] = []
    ok, why = _can_bind(host, int(preferred))
    if ok:
        return int(preferred), notes
    notes.append(f"preferred port {preferred} is not bindable on this host ({why})")
    for cand in candidates:
        if cand == int(preferred):
            continue
        ok, _ = _can_bind(host, cand)
        if ok:
            notes.append(f"using port {cand} for this test run only (shared candidate list)")
            return cand, notes
    raise SystemExit(
        "no bindable port found for the injection; tried the configured port and "
        f"the shared candidate list {tuple(candidates) or '(empty)'}")


def _drain(sock: socket.socket) -> None:
    """Accept and drop every connection offered to the injection socket."""
    while True:
        try:
            conn, _ = sock.accept()
        except OSError:
            return  # closed from the main thread
        try:
            conn.close()
        except OSError:
            pass


def _run(action: str, *, env: dict, skip: tuple[str, ...] = (), expect_rc=(0,)) -> dict:
    """One real CLI invocation. Returns the evidence record, never raises."""
    cmd = [str(PY), "-X", "utf8", "-m", "launcher", action, "--json"]
    for s in skip:
        cmd += ["--skip", s]
    t0 = time.time()
    try:
        res = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True,
                             text=True, timeout=TIMEOUTS.get(action, 240.0),
                             encoding="utf-8", errors="replace",
                             creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired as e:
        return {"action": action, "cmd": cmd, "seconds": round(time.time() - t0, 1),
                "outcome": "TIMEOUT", "stdout": (e.stdout or "")[-1500:],
                "stderr": (e.stderr or "")[-800:]}
    rec = {"action": action, "cmd": cmd, "rc": res.returncode,
           "seconds": round(time.time() - t0, 1),
           "rc_expected": list(expect_rc),
           "rc_ok": res.returncode in expect_rc,
           "stdout": (res.stdout or "")[-4000:],
           "stderr": (res.stderr or "")[-1500:]}
    # The CLI prints the JSON report last, after the Persian progress lines and
    # pretty-printed with indent=2 — so it is *not* the final line of stdout.
    rec["report"] = _parse_report(res.stdout or "")
    return rec


def _parse_report(stdout: str) -> dict | None:
    """Find the JSON report the CLI prints at the end of its stdout.

    ``--json`` still emits the Persian progress lines first, then the report
    indented across many lines, so ``splitlines()[-1]`` is just ``}`` and never
    parsed. Every candidate ``{`` is tried in order and the first that decodes
    all the way to end-of-output wins, which keeps this correct even if a
    progress line ever contained a brace.
    """
    for i, ch in enumerate(stdout):
        if ch != "{":
            continue
        try:
            return json.loads(stdout[i:])
        except ValueError:
            continue
    return None


def _latest_report() -> dict | None:
    path = REPORT_DIR / "status.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cleanup(env: dict) -> list[dict]:
    out = []
    for _ in range(2):  # stop, then stop again: must be a clean no-op
        out.append(_run("stop", env=env))
    return out


def _web_api_token() -> str | None:
    """The bearer token the dashboard route requires, read from .env.

    Presence only is ever returned out of here: the value goes straight into a
    request header and is never echoed into stdout or into an evidence record
    (the audit ledger and the route's own responses hold nothing of it either).
    """
    import re
    try:
        text = (ROOT / ".env").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"\s*AHOS_WEB_API_TOKEN\s*=\s*(.+?)\s*$", line)
        if not m or m.group(1).strip().lower() in ("", "change-me", "changeme"):
            continue
        val = m.group(1).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        return val or None
    return None


def _http_json(url: str, *, method: str = "GET", headers: dict,
               body: dict | None = None) -> dict:
    """One HTTP call. Records only what the server sent back, never the headers
    we sent (they carry the token), and never lets an exception escape."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    t0 = time.time()
    rec: dict = {"url": url, "method": method, "seconds": round(time.time() - t0, 1)}
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(4000).decode("utf-8", "replace")
            rec.update(status=int(r.status), body=raw)
            rec["json"] = _try_json(raw)
            return rec
    except urllib.error.HTTPError as e:
        # 401/403/409 are *expected* outcomes of the guard checks; capture them.
        raw = e.read(4000).decode("utf-8", "replace")
        rec.update(status=int(e.code), body=raw)
        rec["json"] = _try_json(raw)
        return rec
    except Exception as e:
        rec.update(status=None, error=type(e).__name__)
        return rec


def _try_json(raw: str) -> dict | None:
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else None
    except ValueError:
        return None


def _wait_for_report(pred, deadline: float, *, poll: float = 3.0) -> tuple[bool, float, dict | None]:
    """Poll reports/launcher/status.json on disk until ``pred`` holds or the
    deadline passes. Disk, not HTTP: during a restart the gateway itself is
    being killed and re-spawned, so the route is gone exactly when the verdict
    needs it most."""
    t0 = time.time()
    while time.time() - t0 < deadline:
        rep = _latest_report()
        try:
            if pred(rep):
                return True, round(time.time() - t0, 1), rep
        except Exception:
            pass
        time.sleep(poll)
    return False, round(time.time() - t0, 1), _latest_report()


def _audit_records() -> list[dict]:
    """The tail of the control audit ledger, most recent last."""
    if not AUDIT_PATH.exists():
        return []
    try:
        lines = AUDIT_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-40:]:
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            out.append(v)
    return out


def _audit_parse_all() -> list[dict]:
    """Every record in the control audit ledger, most recent last.

    ``_audit_records`` returns only the last 40 lines, which saturates the
    append delta the moment the ledger grows past 40 lines: the count then reads
    zero forever and every run looks as if it wrote no audit evidence. The whole
    file is the only honest numerator.
    """
    if not AUDIT_PATH.exists():
        return []
    try:
        lines = AUDIT_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            out.append(v)
    return out


def _audit_records_since(baseline: int) -> list[dict]:
    """Records appended after the ledger already held ``baseline`` records.

    The pair check must not scan the whole ledger: a *previous* run's EXECUTING
    and CONFIRMED pair for the same action satisfies the predicate even when this
    run wrote nothing at all. Slicing from a baseline taken before the action
    makes the pair evidence strictly this run's.
    """
    return _audit_parse_all()[baseline:]


def _window_census() -> dict:
    """Every process that owns a visible window, plus the component pids from the
    last status report. The one-click contract is that no AHOS child ever owns a
    window, so this is the evidence: each component pid must be absent from the
    census (or present with an empty title)."""
    procs: list[dict] = []
    if os.name == "nt":
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | "
                 "Select-Object Id,ProcessName,MainWindowTitle | "
                 "ConvertTo-Json -Compress -Depth 2"],
                capture_output=True, text=True, timeout=30, encoding="utf-8",
                errors="replace", creationflags=_NO_WINDOW)
        except Exception as e:
            return {"error": type(e).__name__, "procs": [], "titled_pids": []}
        try:
            data = json.loads(res.stdout or "[]")
        except ValueError:
            data = []
        for p in data if isinstance(data, list) else [data]:
            if not isinstance(p, dict):
                continue
            procs.append({"pid": p.get("Id"), "name": p.get("ProcessName"),
                          "title": (p.get("MainWindowTitle") or "")[:120]})
    rep = _latest_report() or {}
    component_pids = {}
    for name, info in (rep.get("components") or {}).items():
        if isinstance(info, dict) and info.get("pid"):
            component_pids[str(name)] = int(info["pid"])
    titled = {int(p["pid"]) for p in procs if p.get("pid")}
    return {"procs": procs, "titled_pids": sorted(titled),
            "component_pids": component_pids,
            "components_owning_windows": sorted(
                set(component_pids.values()) & titled)}


def smoke_dashboard_api(mode: str, *, skip: tuple[str, ...] = ()) -> dict:
    """The dashboard's Stop/Restart buttons talk to POST /api/launcher. This case
    proves the whole chain against the real gateway: loopback guard, auth guard,
    write-ahead audit, an actual child orchestrator that moves the stack, and a
    GET poll that reads status.json without touching a live socket.

    The engine is skippable (and skipped by default in ``main``): its first
    observation cycle dominates a cold boot for ~6 minutes and proves nothing
    about this route that the idempotent case does not already cover, while
    every minute here is a minute the harness can be interrupted and leave the
    stack behind."""
    env = _base_env(mode)
    steps: list[dict] = []
    notes: list[str] = []
    verdict: dict = {}
    try:
        steps.append({"step": "start (real)",
                      **_run("start", env=env, skip=skip, expect_rc=(0,))})
        first = _latest_report()
        base = ((first or {}).get("dashboard_url") or "").rstrip("/")
        if not base:
            raise SystemExit("start did not report a dashboard_url to probe")

        token = _web_api_token()
        auth = {"Authorization": f"Bearer {token}"} if token else {}
        if not token:
            notes.append("AHOS_WEB_API_TOKEN not found in .env; auth checks will fail")

        # GET: the poll path the dashboard uses every few seconds.
        steps.append({"step": "GET status (auth)",
                      **_http_json(f"{base}/api/launcher", headers=auth)})
        got = steps[-1]
        status_ok = (got.get("status") == 200
                     and isinstance(got.get("json"), dict)
                     and got["json"].get("ok") is True
                     and got["json"].get("staleAfterSec") is not None
                     and isinstance(got["json"].get("status"), dict))
        if status_ok:
            verdict["reported_overall"] = got["json"]["status"].get("overall")

        # The loopback guard must reject a request that a proxy could have
        # forged. The hop has to be non-loopback: the Next.js dev server appends
        # `x-forwarded-for: 127.0.0.1` to *every* request, including one on a raw
        # loopback socket, so a loopback hop is a legitimate arrival on the
        # loopback-only listener and must pass (see docs/ONE_CLICK.md). An
        # off-machine hop is the thing the guard exists to refuse.
        steps.append({"step": "GET with off-host x-forwarded-for",
                      **_http_json(f"{base}/api/launcher",
                                   headers={**auth,
                                            "X-Forwarded-For": "10.0.0.1"})})
        loopback_refused = steps[-1].get("status") == 403
        steps.append({"step": "GET with loopback x-forwarded-for",
                      **_http_json(f"{base}/api/launcher",
                                   headers={**auth,
                                            "X-Forwarded-For": "127.0.0.1"})})
        verdict["dev_forwarded_header_accepted"] = (
            steps[-1].get("status") == 200
            and isinstance(steps[-1].get("json"), dict)
            and steps[-1]["json"].get("ok") is True)

        # No credentials at all: 401, not the status body.
        steps.append({"step": "GET unauthenticated",
                      **_http_json(f"{base}/api/launcher", headers={})})
        auth_demanded = steps[-1].get("status") == 401

        # Evidence for scope (b): while the stack is really up, no AHOS child may
        # own a window.
        census = _window_census()

        audit_before = len(_audit_parse_all())

        steps.append({"step": "POST restart",
                      **_http_json(f"{base}/api/launcher", method="POST", headers=auth,
                                   body={"action": "restart"})})
        post = steps[-1]
        restart_ok = (post.get("status") == 202 and isinstance(post.get("json"), dict)
                      and post["json"].get("ok") is True
                      and post["json"].get("action") == "restart"
                      and bool(post["json"].get("pid")))
        if restart_ok:
            verdict["restart_child_pid"] = post["json"].get("pid")
        # The route must forward the previous run's explicit exclusions:
        # Restart restores the stack that was running, it does not widen it.
        verdict["restart_preserved_skip"] = bool(
            restart_ok
            and sorted(post["json"].get("skipped") or []) == sorted(skip))

        # The gateway is mid-restart; poll the artefact, not the route. Keyed on
        # ts because the *previous* report is still ONLINE and would otherwise
        # satisfy the predicate before the child had done anything. The skipped
        # components must still read SKIPPED in the child's own report: that is
        # the evidence the forwarded -Skip set actually reached the orchestrator
        # and the restart did not silently widen the running stack.
        prior_ts = (first or {}).get("ts")

        def _restart_done(r: dict | None) -> bool:
            if not (r and r.get("overall") in ("ONLINE", "DEGRADED")
                    and r.get("action") == "start"
                    and r.get("ts") and r.get("ts") != prior_ts):
                return False
            comps = r.get("components") or {}
            return all((comps.get(s) or {}).get("status") == "SKIPPED" for s in skip)

        waited, restart_secs, after = _wait_for_report(_restart_done, _RESTART_DEADLINE)
        verdict["restart_brought_stack_back"] = bool(waited)
        verdict["restart_seconds"] = restart_secs

        # The route must be served by the *new* gateway.
        steps.append({"step": "GET status after restart",
                      **_http_json(f"{base}/api/launcher", headers=auth)})
        route_back = (steps[-1].get("status") == 200
                      and isinstance(steps[-1].get("json"), dict)
                      and steps[-1]["json"].get("ok") is True)
        verdict["route_served_after_restart"] = bool(route_back)

        # Every action must have its EXECUTING + CONFIRMED pair in the ledger.
        led = _audit_records_since(audit_before)
        verdict["audit_lines_appended"] = len(led)
        verdict["audit_pair_for_restart"] = _audit_pair(led, "restart")

        steps.append({"step": "POST stop",
                      **_http_json(f"{base}/api/launcher", method="POST", headers=auth,
                                   body={"action": "stop"})})
        stop_post = steps[-1]
        verdict["stop_accepted"] = (stop_post.get("status") == 202
                                    and isinstance(stop_post.get("json"), dict)
                                    and stop_post["json"].get("action") == "stop")
        stopped, stop_secs, after_stop = _wait_for_report(
            lambda r: bool(r and r.get("overall") in ("NOT_RUNNING", "STOPPED", "DOWN")
                           and r.get("ts") and r.get("ts") != prior_ts),
            _STOP_DEADLINE)
        verdict["stack_stopped"] = bool(stopped)
        verdict["stop_seconds"] = stop_secs
        led_after = _audit_records_since(audit_before)
        verdict["audit_pair_for_stop"] = _audit_pair(led_after, "stop")

        verdict.update({
            "get_status_ok": bool(status_ok),
            "loopback_refused": bool(loopback_refused),
            "auth_demanded": bool(auth_demanded),
            "restart_accepted": bool(restart_ok),
            "window_census": census,
            "components_owning_windows": census.get("components_owning_windows"),
        })
        verdict["passed"] = bool(verdict["get_status_ok"]
                                 and verdict["loopback_refused"]
                                 and verdict["dev_forwarded_header_accepted"]
                                 and verdict["auth_demanded"]
                                 and verdict["restart_accepted"]
                                 and verdict["restart_preserved_skip"]
                                 and verdict["restart_brought_stack_back"]
                                 and verdict["route_served_after_restart"]
                                 and verdict["audit_pair_for_restart"]
                                 and verdict["audit_pair_for_stop"]
                                 and verdict["stack_stopped"]
                                 and not verdict["components_owning_windows"])
        return {"case": "dashboard-api", "steps": steps, "verdict": verdict,
                "notes": notes}
    finally:
        steps.extend(_cleanup(env))


def _audit_pair(led: list[dict], action: str) -> bool:
    """The write-ahead contract: EXECUTING recorded before the child was spawned,
    then CONFIRMED once it was — both on the dashboard channel.

    The key is ``channel_claimed`` (snake_case): ``buildAuditRecord`` serialises
    the ledger record from the TS param ``channelClaimed`` to a snake_case field,
    so a reader keyed on the parameter name matches nothing and every pair reads
    as broken. Match the wire format on disk, not the source-language name.
    """
    ours = [r for r in led if r.get("intent") == action
            and r.get("channel_claimed") == "dashboard_launcher_api"]
    return any(r.get("decision") == "EXECUTING" for r in ours) \
        and any(r.get("decision") == "CONFIRMED" for r in ours)


def smoke_idempotent(mode: str) -> dict:
    env = _base_env(mode)
    steps = []
    try:
        steps.append(_run("start", env=env, expect_rc=(0,)))
        first = _latest_report()
        steps.append(_run("status", env=env))
        replay = _run("start", env=env, expect_rc=(0,))
        steps.append(replay)
        steps.append(_run("stop", env=env))
        steps.append(_run("start", env=env, expect_rc=(0,)))
        steps.append(_run("status", env=env))
        cold = _latest_report()
        verdict = {
            "started_once": bool(first and first.get("overall") in ("ONLINE", "DEGRADED")),
            "second_start_was_idempotent_replay":
                bool((replay.get("report") or {}).get("cp_run", {}).get("idempotent_replay")),
            "restart_after_stop_worked":
                bool(cold and cold.get("overall") in ("ONLINE", "DEGRADED")),
            "gateway_url": (first or {}).get("dashboard_url"),
            "paper_only": (first or {}).get("paper_only"),
        }
        verdict["all_steps_rc_ok"] = all(s.get("rc_ok", False) for s in steps)
        verdict["passed"] = bool(verdict["started_once"]
                                 and verdict["second_start_was_idempotent_replay"]
                                 and verdict["restart_after_stop_worked"]
                                 and verdict["all_steps_rc_ok"])
        return {"case": "idempotent", "steps": steps, "verdict": verdict}
    finally:
        steps.extend(_cleanup(env))


def smoke_port_busy(mode: str, *, skip: tuple[str, ...]) -> dict:
    """A foreign process squatting on the gateway port must be reported, not
    hidden behind a generic failure or an ONLINE claim."""
    import launcher.components as C
    env = _base_env(mode)
    target = C.database_target(C.load_repo_env(ROOT, env))
    info = C.resolve_gateway(env)
    host = info.get("host") or "127.0.0.1"
    port = info.get("port")
    if not port:
        raise SystemExit("could not resolve the gateway port to occupy")
    # Windows may refuse to bind the configured port (Hyper-V reservations).
    # The fallback list is the shared one so the smoke squats on a port the
    # launcher itself might have been redirected to.
    port, notes = _bindable_port(
        host, port,
        C.candidate_ports(env, config_file=C.GATEWAY_PORTS_CONFIG))
    # AHOS_GATEWAY_URL outranks AHOS_GATEWAY_PORT (scripts/gateway_port.py), so
    # to retarget the launcher the URL itself must be rewritten. Test-run only.
    env["AHOS_GATEWAY_URL"] = f"http://{host}:{port}/api/chat"
    env["AHOS_GATEWAY_PORT"] = str(port)
    squat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    squat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    squat.bind((host, int(port)))
    squat.listen(8)
    # A real foreign server accepts the connections it is offered. A socket that
    # only listens never fills its backlog past one pending connection, so the
    # launcher's second connect probe hangs past its timeout, reads the port as
    # free, spawns a gateway it cannot bind, and burns 120s on a listen error —
    # the injection would then be measuring the launcher's timeout, not its
    # port-busy handling. Closing the socket ends the thread.
    drain = threading.Thread(target=_drain, args=(squat,), daemon=True)
    drain.start()
    steps: list[dict] = []
    out: dict = {}
    try:
        steps.append(_run("start", env=env, skip=skip, expect_rc=(0, 1)))
        report = _latest_report()
        gw = (report or {}).get("components", {}).get("gateway", {}) if report else None
        stdout = steps[-1].get("stdout") or ""
        verdict = {
            "occupied": f"{host}:{port}",
            "db_scheme": target.get("scheme"),
            "gateway_status": gw.get("status") if gw else None,
            "gateway_detail": gw.get("detail") if gw else None,
            "gateway_chosen_via": (report or {}).get("gateway_chosen_via"),
            "overall": (report or {}).get("overall"),
            "persian_action_named": "AHOS_GATEWAY_PORT" in stdout
                                    or "AHOS_GATEWAY_PORT" in json.dumps(gw or {}),
            "persian_error_shown": "پورت" in stdout or "اشغال" in stdout,
            "did_not_claim_online": (report or {}).get("overall") != "ONLINE",
        }
        verdict["passed"] = bool(verdict["gateway_status"] in ("UNHEALTHY", "UNAVAILABLE")
                                 and verdict["persian_error_shown"]
                                 and verdict["did_not_claim_online"])
        out = {"case": "port-busy", "steps": steps, "verdict": verdict,
               "port_notes": notes}
        out["steps"].append(_run("stop", env=env))
        return out
    finally:
        squat.close()
        # Nothing of ours should have been left running. stop twice: the second
        # must be a clean no-op even if the first never got to run.
        for _ in range(2):
            steps.append(_run("stop", env=env))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("case", choices=["idempotent", "port-busy", "dashboard-api"],
                    help="which smoke scenario to run")
    ap.add_argument("--mode", default="dev",
                    help="AHOS_GATEWAY_MODE for the run (default dev)")
    ap.add_argument("--skip", action="append", default=[],
                    help="component to skip (repeatable); port-busy defaults to"
                         " skipping telegram and engine, dashboard-api to"
                         " skipping telegram and engine too — the owner's real"
                         " stack excludes both, and a 2-skip run is what reaches"
                         " the dashboard route's comma-joined -Skip path")
    args = ap.parse_args(argv)

    if not PY.exists():
        raise SystemExit(f"venv python missing: {PY}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if args.case == "idempotent":
        result = smoke_idempotent(args.mode)
    elif args.case == "port-busy":
        skip = tuple(args.skip) or ("telegram", "engine")
        result = smoke_port_busy(args.mode, skip=skip)
    else:
        skip = tuple(args.skip) or ("telegram", "engine")
        result = smoke_dashboard_api(args.mode, skip=skip)

    result["mode"] = args.mode
    result["utc"] = _utcstamp()
    result["host"] = socket.gethostname()
    path = REPORT_DIR / f"smoke_{args.case}_{_utcstamp()}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    verdict = result.get("verdict", {})
    print(json.dumps({"case": args.case, "evidence": str(path),
                      "verdict": verdict}, ensure_ascii=False, indent=2))
    return 0 if verdict.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
