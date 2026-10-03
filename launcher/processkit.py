"""Windows process plumbing for the launcher: pid files, liveness, graceful stop.

Nothing here is AHOS-specific beyond the pid-file naming so it stays unit-testable
without a real running stack (all probes take an injectable clock/runner).
"""
from __future__ import annotations

import ctypes
import json
import os
import socket
import subprocess
import time
from pathlib import Path

# CREATE_NEW_PROCESS_GROUP: lets the launcher send a CTRL_BREAK_EVENT to the
# child's own group so a Python child's signal handler shuts it down cleanly.
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008
CREATE_NO_WINDOW = 0x08000000
CTRL_BREAK_EVENT = 1

_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None


# ---------------------------------------------------------------- pid files ---
def pid_path(state_dir: Path, name: str) -> Path:
    return state_dir / f"{name}.pid.json"


def write_pid(state_dir: Path, name: str, pid: int, info: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {"pid": int(pid), "started_ts": time.time(), **info}
    pid_path(state_dir, name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_pid(state_dir: Path, name: str) -> dict | None:
    path = pid_path(state_dir, name)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_pid(state_dir: Path, name: str) -> None:
    try:
        pid_path(state_dir, name).unlink()
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------- liveness ---
def pid_alive(pid: int) -> bool:
    """True only if a process with this pid currently exists."""
    if not pid or pid < 1:
        return False
    if _KERNEL32 is None:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    SYNCHRONIZE = 0x00100000
    h = _KERNEL32.OpenProcess(SYNCHRONIZE, False, int(pid))
    if not h:
        return False
    _KERNEL32.CloseHandle(h)
    return True


def process_cmdline(pid: int, timeout: float = 5.0) -> str | None:
    """Command line of a running pid (CIM; returns None if unavailable).

    Used only to confirm a pid is *ours* before touching it — never to read
    secrets out of another process.
    """
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"ProcessId={int(pid)}\" "
             f"| Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=timeout,
            creationflags=CREATE_NO_WINDOW)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    line = (out.stdout or "").strip().splitlines()
    return line[0] if line else None


def pid_is_ours(pid: int, marker: str) -> bool:
    """A live pid whose command line contains our marker (repo path / module)."""
    if not pid_alive(pid):
        return False
    if not marker:
        return pid_alive(pid)
    cmdline = process_cmdline(pid)
    return bool(cmdline) and marker.lower() in cmdline.lower()


# ---------------------------------------------------------------- terminate ---
def send_ctrl_break(pid: int) -> bool:
    """CTRL_BREAK_EVENT to a child created with CREATE_NEW_PROCESS_GROUP."""
    if _KERNEL32 is None:
        try:
            os.kill(pid, 2)  # SIGINT on POSIX
            return True
        except OSError:
            return False
    return bool(_KERNEL32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, int(pid)))


def taskkill(pid: int, force: bool = False) -> bool:
    args = ["taskkill", "/PID", str(int(pid)), "/T"]
    if force:
        args.append("/F")
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=20,
                             creationflags=CREATE_NO_WINDOW)
    except Exception:
        return False
    return res.returncode == 0


def terminate(pid: int, *, graceful_timeout: float = 15.0,
              _sleep=time.sleep) -> tuple[str, float]:
    """Stop one of our processes: gentle first, force only as a last resort.

    Returns (how, seconds_taken): how ∈ {'already_gone','signal','force','failed'}.
    """
    if not pid_alive(pid):
        return "already_gone", 0.0
    t0 = time.time()
    if send_ctrl_break(pid):
        deadline = t0 + graceful_timeout
        while time.time() < deadline:
            _sleep(0.5)
            if not pid_alive(pid):
                return "signal", time.time() - t0
    if taskkill(pid, force=False):
        deadline = t0 + graceful_timeout
        while time.time() < deadline:
            _sleep(0.5)
            if not pid_alive(pid):
                return "signal", time.time() - t0
    if taskkill(pid, force=True):
        deadline = t0 + 10.0
        while time.time() < deadline:
            _sleep(0.5)
            if not pid_alive(pid):
                return "force", time.time() - t0
    return "failed" if pid_alive(pid) else "force", time.time() - t0


# ------------------------------------------------------------------- spawn ---
def spawn_detached(cmd: list[str], *, cwd: Path, env: dict, log_path: Path) -> int:
    """Start a long-lived child whose stdout/stderr lands in log_path.

    The child gets its own process group (needed for graceful stop) and a
    detached handle so it survives the launcher console closing.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "ab", buffering=0)
    flags = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
    if os.name == "nt":
        flags |= CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd), env=env, stdout=logf, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, close_fds=True, creationflags=flags,
            restore_signals=False)
    finally:
        try:
            logf.close()
        except Exception:
            pass
    return proc.pid


# ------------------------------------------------------------------ network ---
def port_in_use(host: str, port: int, timeout: float = 0.6) -> bool:
    """TCP connect probe; loopback only in practice (the gateway binds 127.0.0.1)."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def http_ok(url: str, timeout: float = 5.0) -> tuple[bool, int | None, str]:
    """Plain GET; returns (ok, status_code, reason). Uses urllib (no extra deps)."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ahos-launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, int(r.status), r.reason or ""
    except urllib.error.HTTPError as e:
        # a reachable endpoint answering non-2xx is still a *listening* server
        return (200 <= e.code < 500), int(e.code), e.reason or ""
    except Exception as e:
        return False, None, type(e).__name__


def open_url(url: str) -> bool:
    if os.name == "nt":
        try:
            os.startfile(url)  # noqa: S606,S607 - default browser, standard on Windows
            return True
        except OSError:
            return False
    for prog in ("xdg-open", "open"):
        try:
            subprocess.run([prog, url], check=False, timeout=10)
            return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------- credential check ---
def credential_present(target: str, timeout: float = 8.0) -> bool:
    """PRESENCE ONLY. Never prints or returns the stored value.

    Uses `cmdkey /list:<target>`; the output is scanned for the target name and
    discarded. Used for the Windows Credential Manager entries AHOS relies on.
    """
    if os.name != "nt":
        return False
    try:
        res = subprocess.run(["cmdkey", f"/list:{target}"], capture_output=True,
                             text=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    except Exception:
        return False
    out = (res.stdout or "") + (res.stderr or "")
    return target.lower() in out.lower()
