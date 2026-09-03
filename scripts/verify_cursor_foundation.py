#!/usr/bin/env python3
"""Phase 0 foundation verification wrapper.

Does not initialize databases, start servers, or write evidence stores.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def main() -> int:
    steps = [
        [sys.executable, "-B", str(ROOT / "scripts" / "freeze_lane_a.py")],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_cursor_engineering_foundation.py",
            "tests/test_cursor_hook_guard.py",
        ],
    ]
    for cmd in steps:
        rc = run(cmd)
        if rc != 0:
            return rc
    print("FOUNDATION VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
