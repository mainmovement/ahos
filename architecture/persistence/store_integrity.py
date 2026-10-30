"""Read-only integrity_check for the stores a soak snapshot must name.

A missing file is NO_DATA. The check runs in a child process so a large store
cannot hold the caller. A store that exceeds the time limit is INTERRUPTED, not ok.

The two large stores are checked on a backup-API snapshot, not on the live file,
and the child is killed if it exceeds the bound.
"""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LARGE_STORES = ("ahos_local", "e01_discovery")
SNAPSHOT_TIMEOUT_S = 240.0
FRESH_S = 6 * 3600


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


def _stamp_age(stamp: str | None) -> float | None:
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - moment).total_seconds()


def stamp_is_fresh(stamp: str | None, *, limit_s: float = FRESH_S) -> bool:
    age = _stamp_age(stamp)
    return age is not None and age < limit_s


def snapshot_integrity(source: Path, dest: Path, timeout_s: float = SNAPSHOT_TIMEOUT_S) -> str:
    """Copy `source` with the backup API and integrity_check the copy.

    The child is killed at `timeout_s`. The copy is removed either way.
    """
    if not Path(source).is_file():
        return "NO_DATA"
    script = Path(__file__).resolve().parents[2] / "scripts" / "integrity_snapshot_one.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [sys.executable, str(script), str(source), str(dest)],
            cwd=str(script.parents[1]),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        dest.unlink(missing_ok=True)
        return "INTERRUPTED"
    except OSError as exc:
        dest.unlink(missing_ok=True)
        return type(exc).__name__
    dest.unlink(missing_ok=True)
    if proc.returncode != 0:
        return "ERROR"
    word = (proc.stdout or "").strip().splitlines()
    return word[-1] if word else "NO_DATA"


def merge_store_integrity(
    previous: dict | None,
    snapshot: dict | None,
    small: dict[str, str],
    *,
    now: str,
) -> dict:
    """Keep a fresh result. A large store without a fresh snapshot is RUNNING, not INTERRUPTED."""
    prior = {}
    if isinstance(previous, dict) and isinstance(previous.get("store_integrity"), dict):
        prior = previous["store_integrity"]
    prior_stores = prior.get("stores") if isinstance(prior.get("stores"), dict) else {}
    large_open = any(prior_stores.get(name) in ("INTERRUPTED", "RUNNING") for name in LARGE_STORES)
    if (
        stamp_is_fresh(str(prior.get("checked_at") or ""))
        and isinstance(prior.get("stores"), dict)
        and not large_open
    ):
        return prior
    stores = dict(small)
    snap_stores = snapshot.get("stores") if isinstance(snapshot, dict) and isinstance(snapshot.get("stores"), dict) else {}
    snap_at = str(snapshot.get("checked_at") or "") if isinstance(snapshot, dict) else ""
    if stamp_is_fresh(snap_at):
        for name in LARGE_STORES:
            if isinstance(snap_stores.get(name), str):
                stores[name] = snap_stores[name]
    else:
        for name in LARGE_STORES:
            stores.setdefault(name, "RUNNING")
    return {
        "checked_at": now,
        "stores": stores,
        "large_store_method": "snapshot_copy",
        "snapshot_timeout_s": SNAPSHOT_TIMEOUT_S,
    }


def spawn_snapshot_job(root: Path) -> int | None:
    """Start the large-store snapshot job unless one is already inside its time bound."""
    pid_path = root / "data" / "integrity_snapshots" / "job.pid"
    if pid_path.is_file():
        age = time.time() - pid_path.stat().st_mtime
        if age < SNAPSHOT_TIMEOUT_S * 2 + 60:
            return None
    script = root / "scripts" / "integrity_snapshot_job.py"
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid
