"""Start the paper soak, the paper trader, and the Telegram listener if they are down.

This does not read an env file. The listener process loads its own config.
A second copy is not started while one of these commands is already running.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
PID_FILE = ROOT / "reports" / "grok" / "M13_SOAK" / "soak_pid.txt"
MARKS = ("m13_gold_soak.py", "paper_trader_cycle.py", "run_bot.py")
COMMANDS = {
    "m13_gold_soak.py": [str(PY), str(ROOT / "scripts" / "m13_gold_soak.py"), "--days", "0", "--interval-sec", "900"],
    "paper_trader_cycle.py": [str(PY), "-u", str(ROOT / "scripts" / "paper_trader_cycle.py"), "--interval", "300"],
    "run_bot.py": [str(PY), str(ROOT / "run_bot.py")],
}


def _running() -> dict[str, int]:
    raw = subprocess.check_output(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.ProcessId.ToString() + '|' + $_.CommandLine }",
        ],
        text=True,
        timeout=30,
    )
    found: dict[str, int] = {}
    for line in raw.splitlines():
        if "|" not in line:
            continue
        pid_text, command = line.split("|", 1)
        if not pid_text.strip().isdigit():
            continue
        for mark in MARKS:
            if mark in command and mark not in found:
                found[mark] = int(pid_text.strip())
    return found


def _spawn(command: list[str]) -> None:
    subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def start_missing() -> dict[str, int]:
    found = _running()
    for mark in MARKS:
        if mark not in found:
            _spawn(COMMANDS[mark])
    time.sleep(4)
    found = _running()
    lines = [str(found[mark]) for mark in MARKS if mark in found]
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return found


def main() -> int:
    found = start_missing()
    print("soak", found.get("m13_gold_soak.py"))
    print("trader", found.get("paper_trader_cycle.py"))
    print("listener", found.get("run_bot.py"))
    return 0 if all(mark in found for mark in MARKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
