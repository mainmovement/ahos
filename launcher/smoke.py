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
        C.candidate_ports(env, config_file=ROOT / "config" / "gateway_ports.json"))
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
    ap.add_argument("case", choices=["idempotent", "port-busy"],
                    help="which smoke scenario to run")
    ap.add_argument("--mode", default="dev",
                    help="AHOS_GATEWAY_MODE for the run (default dev)")
    ap.add_argument("--skip", action="append", default=[],
                    help="component to skip (repeatable); port-busy defaults to"
                         " skipping telegram and engine to keep the injection fast")
    args = ap.parse_args(argv)

    if not PY.exists():
        raise SystemExit(f"venv python missing: {PY}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if args.case == "idempotent":
        result = smoke_idempotent(args.mode)
    else:
        skip = tuple(args.skip) or ("telegram", "engine")
        result = smoke_port_busy(args.mode, skip=skip)

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
