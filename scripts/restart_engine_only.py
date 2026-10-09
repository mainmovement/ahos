#!/usr/bin/env python3
"""Restart ONLY the decision runtime (engine), the way the launcher starts it.

Why not `launcher restart`: that stops and starts every component (gateway,
telegram, stores), which the instruction explicitly rules out. Why not
`launcher start --skip ...`: `_persist_skips` would record the other components
as intentionally skipped, changing the launcher's durable state for later
status/stop runs.

Instead this drives the launcher's own single-component path: terminate the
recorded engine pid (gentle first, force last, same windows as the launcher),
clear its pid record, then call the same `_start_process("engine")` the
orchestrator's start loop calls -- same command, same env, same log path, same
pid-record bookkeeping, same health wait.

Nothing else is touched. No .env edit, no DATABASE_URL change, no Lane A.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from launcher import components as C  # noqa: E402
from launcher import orchestrator as O  # noqa: E402
from launcher import processkit as pk  # noqa: E402


def main() -> int:
    orch = O.AhosOrchestrator(emit=lambda _line: None)
    name = "engine"

    info = orch._pid_info(name)
    pid = (info or {}).get("pid")
    print(f"recorded engine pid: {pid}")
    if pid:
        how, secs = pk.terminate(
            pid,
            marker=(info or {}).get("marker"),
            recorded_start=(info or {}).get("started_ts"),
        )
        print(f"stopped engine pid {pid}: {how} in {secs:.1f}s")
        if how == "failed":
            print("ABORT: engine would not stop; leaving it running.", file=sys.stderr)
            return 1
        pk.clear_pid(orch.state_dir, name)

    # Confirm nothing answering to the engine survived: the daemon spawns a
    # child (observed: a second `architecture.runtime` under the system
    # interpreter), and `terminate` uses taskkill /T on the tree, but verify
    # rather than assume before we respawn.
    leftover = _live_runtime_pids(exclude={pid} if pid else set())
    if leftover:
        print(f"WARNING: runtime processes still live after stop: {sorted(leftover)}")

    res = orch._start_process(name)
    print(f"engine status: {res.status} detail={res.detail} pid={res.pid}")
    return 0 if res.status == C.HEALTHY else 2


def _live_runtime_pids(exclude: set[int]) -> set[int]:
    """Pids of any live process whose command line still runs the runtime."""
    try:
        import subprocess
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process | Where-Object "
             "{ $_.CommandLine -like '*architecture.runtime*' } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=45)
        return {int(line) for line in out.stdout.split() if line.strip().isdigit()
                and int(line) not in exclude}
    except Exception as exc:  # noqa: BLE001 -- a failed scan must not block restart
        print(f"(could not scan for leftover runtimes: {exc})")
        return set()


if __name__ == "__main__":
    sys.exit(main())
