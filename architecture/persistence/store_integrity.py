"""Read-only integrity_check for the stores a soak snapshot must name.

A missing file is NO_DATA. The check runs in a child process so a large store
cannot hold the caller. A store that exceeds the time limit is INTERRUPTED, not ok.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def integrity_check(path: Path | None, timeout_s: float = 20.0) -> str:
    if path is None or not Path(path).is_file():
        return "NO_DATA"
    script = Path(__file__).resolve().parents[2] / "scripts" / "integrity_one.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), str(path)],
            cwd=str(script.parents[1]),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "INTERRUPTED"
    except OSError as exc:
        return type(exc).__name__
    if proc.returncode != 0:
        return "ERROR"
    word = (proc.stdout or "").strip().splitlines()
    return word[-1] if word else "NO_DATA"


def check_known_stores(paths: dict[str, Path], timeout_s: float = 20.0) -> dict[str, str]:
    return {name: integrity_check(path, timeout_s) for name, path in paths.items()}
