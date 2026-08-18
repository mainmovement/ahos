#!/usr/bin/env python3
"""Record a machine-readable AHOS command-run artifact.

Captures the exact command, UTC timestamp, git commit SHA, working-tree
cleanliness, exit code, duration, and stdout/stderr. Pytest -q summaries are
parsed when present. This is repository evidence; informal markdown counts
are not.

Usage:
    python scripts/record_test_run.py -- python scripts/validate_imports.py
    python scripts/record_test_run.py -- python -m pytest tests/ -q
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "ahos.test_run.v1"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git_meta(cwd: Path | None = None) -> dict:
    repo = cwd or ROOT

    def _run(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                args, cwd=str(repo), capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    porcelain = _run(["git", "status", "--porcelain"])
    return {
        "commit_sha": _run(["git", "rev-parse", "HEAD"]) or "UNKNOWN",
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "UNKNOWN",
        "working_tree_clean": porcelain == "",
    }

_PYTEST_SUMMARY = re.compile(
    r"(?P<failed>\d+) failed|"
    r"(?P<passed>\d+) passed|"
    r"(?P<skipped>\d+) skipped|"
    r"(?P<errors>\d+) error|"
    r"(?P<xfailed>\d+) xfailed|"
    r"(?P<xpassed>\d+) xpassed|"
    r"(?P<warnings>\d+) warning",
)


def parse_pytest_summary(text: str) -> dict | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    tail = lines[-1]
    if not any(token in tail for token in ("passed", "failed", "error", "skipped")):
        return None
    found = {k: int(v) for m in _PYTEST_SUMMARY.finditer(tail) for k, v in m.groupdict().items() if v}
    if not found:
        return None
    found["raw"] = tail
    return found


def record_run(command: list[str], out_path: Path, timeout: int = 1800) -> dict:
    meta = git_meta()
    started = time.time()
    started_utc = utc_now()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s"
        timed_out = True

    duration = round(time.time() - started, 3)
    artifact = {
        "schema": SCHEMA_VERSION,
        "timestamp_utc": started_utc,
        "finished_utc": utc_now(),
        "duration_sec": duration,
        "command": command,
        "command_str": " ".join(command),
        "cwd": str(ROOT),
        "executable": sys.executable,
        "git": meta,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "pytest_summary": parse_pytest_summary(stdout + "\n" + stderr),
        "stdout": stdout,
        "stderr": stderr,
        "verdict": "PASS" if exit_code == 0 and not timed_out else "FAIL",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def default_out_path(command: list[str]) -> Path:
    stamp = utc_now().replace(":", "").replace("-", "")
    label = "cmd"
    joined = " ".join(command)
    if "pytest" in joined:
        label = "pytest"
    elif "validate_imports" in joined:
        label = "validate_imports"
    return ROOT / "reports" / f"{label}_run_{stamp}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Record a command run as JSON evidence")
    ap.add_argument("--out", default=None, help="artifact path (default: reports/<label>_run_<ts>.json)")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("command", nargs=argparse.REMAINDER, help="command after --")
    args = ap.parse_args(argv)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("usage: python scripts/record_test_run.py -- <command>", file=sys.stderr)
        return 2

    out_path = Path(args.out) if args.out else default_out_path(command)
    artifact = record_run(command, out_path, timeout=args.timeout)
    print(json.dumps({
        "verdict": artifact["verdict"],
        "exit_code": artifact["exit_code"],
        "duration_sec": artifact["duration_sec"],
        "commit_sha": artifact["git"]["commit_sha"],
        "working_tree_clean": artifact["git"]["working_tree_clean"],
        "pytest_summary": artifact["pytest_summary"],
        "artifact": str(out_path),
    }, indent=2))
    return 0 if artifact["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
