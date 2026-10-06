"""Command-line entry: python -m launcher <action> [--json]

Actions: preflight | start | stop | status | restart | bootstrap-url

``bootstrap-url`` prints a fresh one-time dashboard login URL (5 min, single
use) for a browser opened by hand; the launcher's own `start` opens one
automatically. The URL is a short-lived credential: do not paste it anywhere.

The Persian progress lines go to stdout (UTF-8); the launcher console wrapper
sets chcp 65001 and PYTHONIOENCODING so they render correctly in the window the
desktop shortcut opens.
"""
from __future__ import annotations

import argparse
import json
import sys

from launcher import __version__
from launcher.orchestrator import AhosOrchestrator


def _emit(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:  # console without UTF-8: keep it readable
        print(line.encode("ascii", "replace").decode(), flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="launcher", description="AHOS one-click launcher")
    ap.add_argument("action", choices=["preflight", "start", "stop", "status", "restart",
                                       "bootstrap-url"])
    ap.add_argument("--json", action="store_true", help="emit the status report as JSON")
    ap.add_argument("--skip", action="append", default=[],
                    help="component to skip (repeatable): stores db_backend gateway telegram engine")
    ap.add_argument("--root", default=None, help="repository root (default: this checkout)")
    args = ap.parse_args(argv)

    orch = AhosOrchestrator(args.root, emit=_emit, skip=set(args.skip))

    if args.action == "bootstrap-url":
        url = orch.bootstrap_url()
        if orch.component_state("gateway") != "ours_running":
            print("note: no launcher-managed gateway is running; the URL works with a "
                  "gateway started from this checkout with the same AHOS_DATA_DIR.",
                  file=sys.stderr, flush=True)
        print(url, flush=True)  # stdout only: never written to a log or report
        return 0

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
