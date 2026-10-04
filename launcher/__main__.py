"""Command-line entry: python -m launcher <action> [--json]

Actions: preflight | start | stop | status | restart

The Persian progress lines go to stdout (UTF-8); the launcher console wrapper
sets chcp 65001 and PYTHONIOENCODING so they render correctly in the window the
desktop shortcut opens.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from launcher import __version__
from launcher.orchestrator import AhosOrchestrator


class _Tee:
    """A stream that writes to two sinks: the log file first, then the console.

    The log file is written first on purpose. A hidden run's console may be a
    codepage that cannot render Persian, and the console write may raise; the
    log is UTF-8 and must never lose the line.
    """

    def __init__(self, stream, logf):
        self._stream = stream
        self._logf = logf

    def write(self, s):
        try:
            self._logf.write(s)
            self._logf.flush()
        except OSError:
            pass
        return self._stream.write(s)

    def flush(self):
        try:
            self._logf.flush()
        except OSError:
            pass
        return self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


def _install_log_tee() -> None:
    """Mirror stdout and stderr onto the path ``ahos.ps1`` names.

    ``ahos.ps1`` used to capture python's output through a PowerShell
    ``| Out-File`` pipe. A pipe ends when its write end closes, not when python
    exits -- and the launcher's detached children inherit that handle. A restart
    stops the very gateway that spawned the shell, python then exits, and the
    shell stays pinned on the pipe reader forever, holding the module lock the
    dashboard's next stop/restart needs (observed on this host: the wedged
    shell's only live child was conhost.exe). Python owns the log file instead:
    a file has no reader to block on, so the shell waits on nothing but python.
    The path is passed by the ps1 so both sides agree on it; unset means a
    direct CLI invocation (terminal, tests), where nothing is mirrored.
    """
    path = os.environ.get("AHOS_LAUNCHER_LOG")
    if not path:
        return
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        logf = open(p, "a", encoding="utf-8", errors="replace")
    except OSError:
        return
    sys.stdout = _Tee(sys.stdout, logf)
    sys.stderr = _Tee(sys.stderr, logf)


def _emit(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:  # console without UTF-8: keep it readable
        print(line.encode("ascii", "replace").decode(), flush=True)


def _skip_set(raw: list[str]) -> set[str]:
    """Exclusions requested on the command line.

    ``--skip`` is repeatable, but the dashboard route cannot repeat it:
    Start-Process re-parses -ArgumentList into one command line and PowerShell's
    binder rejects a repeated ``-Skip`` (the child then exits 1 before python
    ever starts). So the route sends its exclusions as ONE comma-joined value,
    which is split here; both shapes reach the same set.
    """
    parts = (p.strip() for value in raw for p in value.split(","))
    return {p for p in parts if p}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="launcher", description="AHOS one-click launcher")
    ap.add_argument("action", choices=["preflight", "start", "stop", "status", "restart"])
    ap.add_argument("--json", action="store_true", help="emit the status report as JSON")
    ap.add_argument("--skip", action="append", default=[],
                    help="component to skip (repeatable or comma-joined): stores db_backend gateway telegram engine")
    ap.add_argument("--root", default=None, help="repository root (default: this checkout)")
    args = ap.parse_args(argv)
    _install_log_tee()

    orch = AhosOrchestrator(args.root, emit=_emit, skip=_skip_set(args.skip))

    report: dict
    if args.action == "preflight":
        pf = orch.preflight()
        for chk in pf.checks:
            _emit(f"  {'OK  ' if chk['ok'] else 'FAIL'} {chk['name']}: {chk['detail']}")
        for w in pf.warnings:
            _emit(f"  WARN {w}")
        report = {"action": "preflight", "overall": "OK" if pf.ok else "FAILED",
                  "ok": pf.ok, "checks": pf.checks, "warnings": pf.warnings}
    elif args.action == "start":
        report = orch.start()
    elif args.action == "stop":
        report = orch.stop()
    elif args.action == "restart":
        orch.stop()
        import time
        time.sleep(1.0)
        report = orch.start()
    else:  # status
        report = orch.status()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _emit(f"overall: {report.get('overall')}")

    overall = report.get("overall")
    return {"ONLINE": 0, "DEGRADED": 0, "STOPPED": 0, "NOT_RUNNING": 0, "OK": 0}.get(overall, 1)


if __name__ == "__main__":
    sys.exit(main())
