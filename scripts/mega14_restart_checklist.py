"""After the soak clock, restart the soak and the paper trader and print their call counts.

Before 2026-11-01T00:45:31Z this script prints WAIT and does not stop a process.
The Telegram listener is not a restart target. The soak window start is not reset.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.mega14_restart import (  # noqa: E402
    MIN_FREE_MB,
    due,
    is_restart_target,
)

PY = ROOT / ".venv" / "Scripts" / "python.exe"
SOAK_CMD = [str(PY), str(ROOT / "scripts" / "m13_gold_soak.py"), "--days", "0", "--interval-sec", "900"]
TRADER_CMD = [str(PY), "-u", str(ROOT / "scripts" / "paper_trader_cycle.py"), "--interval", "300"]
LOG = ROOT / "reports" / "grok" / "PAPER" / "shadow_cycle.jsonl"


def _free_mb() -> float | None:
    import ctypes
    from ctypes import wintypes

    class Stat(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_uint64),
            ("ullAvailPhys", ctypes.c_uint64),
            ("ullTotalPageFile", ctypes.c_uint64),
            ("ullAvailPageFile", ctypes.c_uint64),
            ("ullTotalVirtual", ctypes.c_uint64),
            ("ullAvailVirtual", ctypes.c_uint64),
            ("ullAvailExtendedVirtual", ctypes.c_uint64),
        ]

    stat = Stat()
    stat.dwLength = ctypes.sizeof(Stat)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
        return None
    return stat.ullAvailPhys / (1024 * 1024)


def _targets() -> list[int]:
    raw = subprocess.check_output(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.ProcessId.ToString() + '|' + $_.CommandLine }",
        ],
        text=True,
    )
    found = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        pid_text, command = line.split("|", 1)
        if is_restart_target(command):
            found.append(int(pid_text))
    return found


def _calls(pids: set[int]) -> int:
    if not LOG.is_file() or not pids:
        return 0
    count = 0
    for line in LOG.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if int(row.get("pid") or 0) in pids:
            count += 1
    return count


def restart_and_count() -> int:
    free = _free_mb()
    if free is None or free < MIN_FREE_MB:
        print("WAIT_RAM")
        return 0
    old = _targets()
    for pid in old:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False)
    subprocess.Popen(SOAK_CMD, cwd=str(ROOT))
    subprocess.Popen(TRADER_CMD, cwd=str(ROOT))
    time.sleep(5)
    fresh = [pid for pid in _targets() if pid not in set(old)]
    print("new_pids", ",".join(str(pid) for pid in fresh) or "none")
    print("call_count", _calls(set(fresh)))
    return 0


def main(now: datetime | None = None) -> int:
    if due(now or datetime.now(timezone.utc)) != "DUE":
        print("WAIT")
        return 0
    return restart_and_count()


if __name__ == "__main__":
    raise SystemExit(main())
