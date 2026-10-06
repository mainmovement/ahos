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
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1

_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None

if _KERNEL32 is not None:
    # Toolhelp32 process snapshot (pid + parent pid) for the parentage walk.
    _KERNEL32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    _KERNEL32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    _KERNEL32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _KERNEL32.Process32FirstW.restype = ctypes.c_int
    _KERNEL32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _KERNEL32.Process32NextW.restype = ctypes.c_int
    _KERNEL32.CloseHandle.argtypes = [ctypes.c_void_p]
    _KERNEL32.CloseHandle.restype = ctypes.c_int

TH32CS_SNAPPROCESS = 0x00000002
_NO_PARENT = 0  # a parent pid of 0 means the process has no recorded parent


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_uint32),
                ("cntUsage", ctypes.c_uint32),
                ("th32ProcessID", ctypes.c_uint32),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.c_uint32),
                ("cntThreads", ctypes.c_uint32),
                ("th32ParentProcessID", ctypes.c_uint32),
                ("pcPriClassBase", ctypes.c_int32),
                ("dwFlags", ctypes.c_uint32),
                ("szExeFile", ctypes.c_wchar * 260)]


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
        # A zombie (exited, not yet reaped) still answers kill(0); it is not running.
        try:
            stat = Path(f"/proc/{int(pid)}/stat").read_text()
            if stat[stat.rindex(")") + 2:].startswith("Z"):
                return False
        except (OSError, ValueError):
            pass
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
        # POSIX: /proc/<pid>/cmdline is NUL-separated argv (Linux). Elsewhere
        # (no /proc) we cannot confirm identity, so stay fail-closed: None.
        try:
            raw = Path(f"/proc/{int(pid)}/cmdline").read_bytes()
        except OSError:
            return None
        return raw.replace(b"\0", b" ").decode("utf-8", "replace").strip() or None
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


def process_snapshot(timeout: float = 20.0) -> dict[int, dict]:
    """One pid -> {pid, ppid, name, cmdline} snapshot of all processes.

    Replaces the old pattern of one powershell invocation *per candidate pid*,
    which made a sweep over every python/node/cmd process on the box cost dozens
    of process spawns. Toolhelp32 gives pid+ppid natively; the command line still
    needs one CIM query (kept), but only for the handful of candidates that
    survived the parentage filter.
    """
    if _KERNEL32 is None:
        return {}
    snap = _KERNEL32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap:
        return {}
    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        out: dict[int, dict] = {}
        ok = _KERNEL32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            pid = int(entry.th32ProcessID)
            out[pid] = {"pid": pid, "ppid": int(entry.th32ParentProcessID),
                        "name": entry.szExeFile or "", "cmdline": ""}
            ok = _KERNEL32.Process32NextW(snap, ctypes.byref(entry))
        return out
    except Exception:
        return {}
    finally:
        _KERNEL32.CloseHandle(snap)


def fill_cmdlines(procs: dict[int, dict], only: list[int],
                  timeout: float = 20.0) -> None:
    """Fill the ``cmdline`` of the listed pids with ONE CIM query (in place).

    Only the survivors of the parentage filter are queried — a marker check still
    runs on the command line as a second line of defence, but it no longer has to
    be the *only* one.
    """
    if not only or os.name != "nt":
        return
    pids = ",".join(str(int(p)) for p in only if p in procs)
    if not pids:
        return
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-CimInstance Win32_Process "
             f"-Filter \"ProcessId={pids.replace(',', ' OR ProcessId=')}\" "
             "| Select-Object ProcessId,CommandLine | "
             "ConvertTo-Csv -NoTypeInformation -Delimiter '`n'"],
            capture_output=True, text=True, timeout=timeout,
            creationflags=CREATE_NO_WINDOW)
    except Exception:
        return
    if res.returncode != 0:
        return
    # ConvertTo-Csv quotes each cell; line 1 is the header. Splitting on a
    # backtick-newline delimiter keeps a single record together even when a
    # command line itself contains newlines.
    for block in (res.stdout or "").split("`n"):
        block = block.strip()
        if not block or block.startswith('"ProcessId"'):
            continue
        parts = [c.strip().strip('"') for c in block.split(",", 1)]
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        if pid in procs:
            procs[pid]["cmdline"] = parts[1]


def descendant_of(pid: int, roots, procs: dict[int, dict],
                  *, max_depth: int = 64) -> bool:
    """Is ``pid`` reachable by walking parents from ``pid`` up to one of ``roots``?

    Strict parentage: the only processes we ever stop are ones this launcher
    (or a recorded component pid) actually spawned. A substring marker cannot
    prove that, which is why the sweep used to match foreign editor/node
    processes that merely happened to run from this checkout.
    """
    roots = set(int(r) for r in roots if r)
    pid = int(pid)
    if pid in roots:
        return True
    seen: set[int] = set()
    cur = pid
    for _ in range(max_depth):
        if cur in seen:
            return False  # cycle guard; process trees are acyclic, so be safe
        seen.add(cur)
        info = procs.get(cur)
        if not info:
            return False
        parent = info.get("ppid") or _NO_PARENT
        if parent == _NO_PARENT:
            return False
        if parent in roots:
            return True
        cur = parent
    return False


def pid_is_ours(pid: int, marker: str) -> bool:
    """A live pid whose command line contains our marker (repo path / module)."""
    if not pid_alive(pid):
        return False
    if not marker:
        return pid_alive(pid)
    cmdline = process_cmdline(pid)
    return bool(cmdline) and marker.lower() in cmdline.lower()


# ---------------------------------------------------------------- terminate ---
def send_ctrl_break(pid: int, *, group: bool = False) -> bool:
    """CTRL_BREAK_EVENT to a child created with CREATE_NEW_PROCESS_GROUP.

    POSIX: SIGINT to the verified group (``group=True``, see
    ``posix_group_ok``) -- signalling `npm` alone orphaned its `next-server`
    child, which kept the gateway port -- or to the pid alone."""
    if _KERNEL32 is None:
        import signal
        return _posix_signal(pid, signal.SIGINT, group)
    return bool(_KERNEL32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, int(pid)))


def arm_console_break_immunity() -> bool:
    """Make this process ignore console CTRL_C/BREAK events (Windows).

    ``GenerateConsoleCtrlEvent`` targets a *process group*, not one process, and
    every descendant of the gateway inherits its group. The dashboard's
    stop/restart route launches this orchestrator as a descendant of the very
    gateway ``stop()`` must terminate, so ``send_ctrl_break`` on the gateway
    delivers a SIGBREAK to the orchestrator as well — which has no handler and
    dies mid-stop, right after emitting the "stopping" header, leaving the
    gateway listener alive and its port stranded (R12). Installing a handler
    that returns TRUE for both events stops the default handler from ever
    running, so the orchestrator survives its own shutdown signal. No-op and
    harmless everywhere else: the desktop-icon ``stop`` is not in the gateway's
    group, and a foreground console loses Ctrl-C/Break only while a launcher
    stop is in flight, which is what an interactive abort should not do anyway.
    """
    global _CONSOLE_HANDLER
    if _KERNEL32 is None or _CONSOLE_HANDLER is not None:
        return _CONSOLE_HANDLER is not None
    try:
        proto = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
        cb = proto(_swallow_console_break)
        if _KERNEL32.SetConsoleCtrlHandler(cb, True):
            _CONSOLE_HANDLER = cb
            return True
    except OSError:
        pass
    return False


def _swallow_console_break(ctrl_type: int) -> bool:
    return ctrl_type in (CTRL_C_EVENT, CTRL_BREAK_EVENT)


def taskkill(pid: int, force: bool = False, *, group: bool = False) -> bool:
    if os.name != "nt":
        # POSIX equivalent of `taskkill /T [/F]`: the verified group only.
        import signal
        return _posix_signal(pid, signal.SIGKILL if force else signal.SIGTERM, group)
    args = ["taskkill", "/PID", str(int(pid)), "/T"]
    if force:
        args.append("/F")
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=20,
                             creationflags=CREATE_NO_WINDOW)
    except Exception:
        return False
    return res.returncode == 0


def posix_group_ok(pid: int, marker: str | None, recorded_start: int | None) -> bool:
    """May ``pid``'s whole process group be signalled? (REDTEAM-19 F3, POSIX.)

    Only when ALL hold: ``pid`` leads its own group (spawn_detached starts each
    child as a session leader), that group is not the caller's own, the pid
    passes the ownership check, and its kernel start time equals the one
    recorded at spawn. A stale pid file whose pid was reused by a non-leader
    would otherwise have ``getpgid`` hand back a foreign group, or ours.
    """
    if os.name == "nt" or recorded_start is None:
        return False
    try:
        pgid = os.getpgid(int(pid))
        if pgid != int(pid) or pgid == os.getpgid(0):
            return False
    except OSError:
        return False
    if not owned(pid, marker, recorded_start):
        return False
    return process_start_time(pid) == recorded_start


def _posix_signal(pid: int, sig: int, group: bool) -> bool:
    """Signal the verified group ``pid`` leads, or the single pid.

    ``group`` must come from ``posix_group_ok``: the group id used is ``pid``
    itself (never ``getpgid(pid)``, which for a non-leader is someone else's
    group -- possibly the user's terminal or the launcher's own)."""
    try:
        if group:
            os.killpg(int(pid), sig)
        else:
            os.kill(int(pid), sig)
        return True
    except OSError:
        return False


def terminate(pid: int, *, marker: str | None = None,
              recorded_start: int | None = None,
              graceful_timeout: float = 15.0,
              force_timeout: float = 10.0, _sleep=time.sleep,
              _clock=time.time) -> tuple[str, float]:
    """Stop one of our processes: gentle first, force only as a last resort.

    Returns (how, seconds_taken), how in:
      already_gone  nothing was alive
      not_ours      POSIX: the pid failed the ownership check (stale pid file,
                    reused pid) -- nothing was signalled
      signal        it exited on SIGINT/CTRL_BREAK or SIGTERM
      force         it ignored those and died only on SIGKILL / taskkill /F
      failed        still alive after every stage, or (POSIX group) members
                    of its group survived SIGKILL -- NOT stopped

    Each stage gets its own wait window (f149e68). Liveness is re-checked after
    every window before escalating (REDTEAM-19 F4), so a process that ignores
    SIGTERM is never reported as stopped by a signal.

    POSIX (REDTEAM-19 F3): when ``marker``/``recorded_start`` are given, the
    pid must pass ``owned`` first. The process GROUP is signalled only when
    ``posix_group_ok`` holds (own leader, not our group, owned, start time
    matches); otherwise only the pid is signalled. Windows behaviour is
    unchanged (taskkill /T on the pid).
    """
    if not pid_alive(pid):
        return "already_gone", 0.0
    posix = os.name != "nt"
    checked = marker is not None or recorded_start is not None
    if posix and checked and not owned(pid, marker, recorded_start):
        return "not_ours", 0.0
    group = posix and checked and posix_group_ok(pid, marker, recorded_start)
    t0 = _clock()

    def _wait(window: float) -> bool:
        deadline = _clock() + window
        while _clock() < deadline:
            _sleep(0.5)
            if not pid_alive(pid):
                return True
        return not pid_alive(pid)

    def _done(how: str) -> tuple[str, float]:
        if group and not _drain_posix_group(pid, force_timeout, _sleep, _clock):
            return "failed", _clock() - t0
        return how, _clock() - t0

    if send_ctrl_break(pid, group=group) and _wait(graceful_timeout):
        return _done("signal")
    if taskkill(pid, force=False, group=group) and _wait(min(5.0, graceful_timeout)):
        return _done("signal")
    if taskkill(pid, force=True, group=group) and _wait(force_timeout):
        return _done("force")
    if pid_alive(pid):
        return "failed", _clock() - t0
    return _done("force")


def can_bind(host: str, port: int) -> bool:
    """Can THIS process actually listen on host:port? A real ``bind``, then close.

    A connect probe is not a substitute on Windows: wide port ranges are reserved
    for Hyper-V/WSL, so ``bind`` fails with ``WinError 10013`` while a connect
    probe reports the port as free — and a foreign listener that never calls
    ``accept`` makes a connect probe *hang*, which reads as "nothing there".
    Mirrors ``scripts/gateway_port.py`` (kept in sync because the launcher and
    the resolver must agree about the same port).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        s.close()


def port_owner(host: str, port: int, timeout: float = 10.0) -> int | None:
    """The pid owning the LISTEN socket on ``port``, or None if none does.

    The gateway is spawned directly as ``node <next cli> start`` (M11.3) — the
    pid we record is the server — but a hard kill of the launcher (console close)
    instead of ``AHOS Stop`` still orphans the detached children, so the pid
    record can go stale while the listener is still very much alive. Windows
    keeps the owner in the TCP table, which is the only authoritative answer
    here — a parentage sweep can never reach an orphaned process.
    """
    if os.name != "nt":
        return None
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-NetTCPConnection -LocalPort %d -ErrorAction SilentlyContinue "
             "| Where-Object { $_.State -eq 2 } | Select-Object -First 1"
             ").OwningProcess" % int(port)],
            capture_output=True, text=True, timeout=timeout,
            creationflags=CREATE_NO_WINDOW)
    except Exception:
        return None
    v = (res.stdout or "").strip()
    return int(v) if v.isdigit() else None


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
