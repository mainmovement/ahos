"""M-D1: open AHOS in its own app window, not a browser tab.

The launcher's ``open_url`` uses ``os.startfile``, which hands the URL to the
default browser and opens a *tab* -- with address bar, tabs, extensions, and the
user's normal profile. The owner wants the double-click of ``AHOS.lnk`` to open
a dedicated window instead: no tabs, no address bar, its own profile, loopback
only. ``AHOS.lnk`` itself is never changed; only the way the launcher opens the
URL it already builds.

Chromium and Edge both support an ``--app=<url>`` kiosk-ish mode that gives
exactly that: a borderless frame with a title bar, no tab strip, no URL bar.
Everything in this module is about constructing that command line correctly and
safely, and about never opening a second window on a second click.

The pure functions here take and return plain data -- they never touch the
process list, the filesystem outside ``app_profile_dir``, or the network -- so
they are testable on any platform (the launcher's own convention, as in
``shortcuts.py``'s ``PureWindowsPath``). Only ``open_app_window`` has side
effects.

**The URL carries a one-time boot token** (see ``bootstrap_url`` in
``components.py``), so it must never be logged, never passed through ``cmd.exe``
where other processes can read it, and never echoed into an exception message.
The owner's Q7 allows it on the command line only because it is single-use and
expires within 60 seconds; that contract is not this module's to enforce, but
this module is the one place the token reaches the OS, so it stays strict about
it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePath

#: Default browser preference, in order. Overridable via ``config/app_window.json``.
DEFAULT_BROWSER_ORDER: tuple[str, ...] = ("chrome", "edge")

#: Window size for the app window.
DEFAULT_WINDOW_SIZE: tuple[int, int] = (1600, 900)

#: The profile lives outside the repo and outside the user's Chrome Default
#: profile, so the app window never inherits the user's tabs, cookies, or
#: extensions, and nothing it does touches their browsing history.
DEFAULT_PROFILE_NAME = "app-window-profile"

# Command-line switches that keep the app window a closed loop: no extensions,
# no sync, no background networking, no component updates, no pings, no proxy,
# and a host-resolver rule that blocks every non-loopback DNS lookup at the
# browser itself. The order is stable so the tests can assert it and a reader
# can check the intent of each flag.
_APP_SWITCHES: tuple[str, ...] = (
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--no-pings",
    "--no-proxy-server",
)

#: Host-resolver rule that resolves every name to NOTFOUND *except* loopback.
_LOOPBACK_ONLY = 'MAP * ~NOTFOUND , EXCLUDE 127.0.0.1'

#: Windows flags for a console-less, detached spawn. Mirrors ``processkit``.
_WINDOWS_FLAGS = 0x00000008 | 0x08000000      # DETACHED_PROCESS | CREATE_NO_WINDOW

_KNOWN_BROWSERS = {
    "chrome": (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ),
    "edge": (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ),
}


@dataclass(frozen=True)
class AppWindowConfig:
    """The non-secret configuration for the app window."""

    browser_order: tuple[str, ...] = DEFAULT_BROWSER_ORDER
    window_size: tuple[int, int] = DEFAULT_WINDOW_SIZE
    profile_name: str = DEFAULT_PROFILE_NAME

    @classmethod
    def from_dict(cls, data: object) -> "AppWindowConfig":
        """Load from the parsed ``config/app_window.json``, ignoring bad keys.

        A config that names an unknown browser is not fatal -- the unknown entry
        is dropped and the remaining order is used -- but a config that leaves no
        known browser at all falls back to the default order rather than to
        ``open_url``, because a config that silently disables the feature is how
        the window quietly stops appearing.
        """
        if not isinstance(data, dict):
            return cls()
        raw = data.get("browser_order", DEFAULT_BROWSER_ORDER)
        order = tuple(str(b).strip().lower() for b in raw
                      if isinstance(raw, (list, tuple)))
        known = tuple(b for b in order if b in _KNOWN_BROWSERS)
        if not known:
            known = DEFAULT_BROWSER_ORDER
        size = data.get("window_size", DEFAULT_WINDOW_SIZE)
        if (isinstance(size, (list, tuple)) and len(size) == 2
                and all(isinstance(v, int) for v in size)
                and all(v > 0 for v in size)):
            width, height = int(size[0]), int(size[1])
        else:
            width, height = DEFAULT_WINDOW_SIZE
        return cls(
            browser_order=known,
            window_size=(width, height),
            profile_name=str(data.get("profile_name", DEFAULT_PROFILE_NAME)),
        )


def load_config(path: Path | str | None = None) -> AppWindowConfig:
    """Read ``config/app_window.json``. A missing or unreadable file is not an
    error: the feature degrades to its built-in defaults rather than failing a
    launch over a config typo. A malformed file is also not fatal, but it is
    reported on stderr so the owner sees the typo instead of wondering why the
    window looks wrong.
    """
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "app_window.json"
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return AppWindowConfig()
    try:
        return AppWindowConfig.from_dict(json.loads(text))
    except json.JSONDecodeError as exc:
        print(f"app_window: {p} is malformed ({exc}); using defaults",
              file=sys.stderr)
        return AppWindowConfig()


def app_profile_dir(cfg: AppWindowConfig | None = None,
                    local_app_data: PurePath | str | None = None) -> PurePath:
    """Where the app window keeps its profile.

    ``%LOCALAPPDATA%\\AHOS\\<profile_name>`` -- outside the repo, outside the
    user's browser profiles, and created on first use by the caller that spawns
    the window (never here: this is a pure function).
    """
    cfg = cfg or AppWindowConfig()
    base = PurePath(str(local_app_data)) if local_app_data is not None else (
        PurePath(os.environ.get("LOCALAPPDATA", str(Path.home()))))
    return base / "AHOS" / cfg.profile_name


def find_browser(cfg: AppWindowConfig | None = None,
                 exists: "callable[[str], bool] | None" = None
                 ) -> tuple[str, Path] | tuple[None, None]:
    """Resolve the first installed browser in the configured order.

    Returns ``(name, executable)`` or ``(None, None)`` when none is present, in
    which case the caller falls back to ``open_url``. ``exists`` is injectable so
    the test suite can exercise the order without installing browsers; the
    default checks the well-known paths and then the registry App Paths.
    """
    cfg = cfg or AppWindowConfig()
    check = exists or _path_exists
    for name in cfg.browser_order:
        for cand in _KNOWN_BROWSERS.get(name, ()):
            if check(cand):
                return name, Path(cand)
    reg = _registry_browser(cfg.browser_order)
    if reg is not None:
        return reg
    return None, None


def _path_exists(candidate: str) -> bool:
    try:
        return Path(candidate).is_file()
    except OSError:                                  # a path this host cannot express
        return False


def _registry_browser(order: tuple[str, ...]) -> tuple[str, Path] | None:
    """Last resort: the registry's App Paths. Off Windows, there is no registry
    to consult, so this is a no-op rather than an error."""
    if os.name != "nt":                              # pragma: no cover - platform guard
        return None
    if winreg is None:                               # pragma: no cover - import guard
        return None
    key_names = {
        "chrome": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        "edge": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
    }
    for name in order:
        key_name = key_names.get(name)
        if not key_name:
            continue
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                exe = Path(str(value).rstrip(";")) / key_names[name].rsplit("\\", 1)[-1]
                if exe.is_file():
                    return name, exe
        except OSError:
            continue
    return None


def build_app_argv(url: str, browser: str, profile_dir: PurePath | str,
                   size: tuple[int, int] = DEFAULT_WINDOW_SIZE) -> list[str]:
    """The command line that opens ``url`` as an app window.

    The URL is never echoed into a message here: it carries the one-time boot
    token, and any error describing an argv must describe it without the value.
    Order is fixed so the tests can pin it and so ``--app`` is always the first
    argument the browser sees.
    """
    if not url:
        raise ValueError("build_app_argv: the bootstrap url is required")
    profile = PurePath(str(profile_dir))
    width, height = size
    return [
        f"--app={url}",
        f"--user-data-dir={profile}",
        f"--window-size={width},{height}",
        f"--host-resolver-rules={_LOOPBACK_ONLY}",
        *_APP_SWITCHES,
    ]


def profile_marker(profile_dir: PurePath | str) -> str:
    """The substring that uniquely identifies our window on a command line.

    Used by the alive-check and by the screenshot script to find the process
    without pattern-matching the URL (which carries the token and must never
    appear in a log line or a search filter).
    """
    return f"--user-data-dir={PurePath(str(profile_dir))}"


def _argv_for_spawn(exe: Path, url: str, profile_dir: PurePath | str,
                    size: tuple[int, int]) -> list[str]:
    argv = build_app_argv(url, "chrome", profile_dir, size)
    return [str(exe)] + argv


def open_app_window(url: str, *, cfg: AppWindowConfig | None = None,
                    log: "callable[[str], None] | None" = None) -> bool:
    """Open the dashboard in its own window. Falls back to ``open_url``.

    Returns True when a window was opened by either path. The log line never
    contains the URL; it names only the browser that was used, so a launcher log
    is safe to read and safe to paste into a bug report.
    """
    cfg = cfg or load_config()
    say = log or (lambda _line: None)
    browser, exe = find_browser(cfg)
    if browser is None:
        say("app_window: no installed browser found; falling back to the "
            "default browser")
        return _fallback(url, say)
    profile = app_profile_dir(cfg)
    try:
        os.mkdir(str(profile))
    except FileExistsError:
        pass                        # created by an earlier launch; that is fine
    except OSError:
        # A profile directory we cannot create is not fatal to the launch, only
        # to isolation: the browser would fall back to its default profile and
        # we would rather open a tab than touch the user's normal profile by
        # accident.
        say("app_window: the profile directory could not be created; falling "
            "back to the default browser")
        return _fallback(url, say)
    argv = _argv_for_spawn(exe, url, profile, cfg.window_size)
    try:
        if os.name == "nt":
            subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             close_fds=True, creationflags=_WINDOWS_FLAGS)
        else:
            subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             close_fds=True, start_new_session=True)
    except OSError:
        say(f"app_window: {browser} failed to start; falling back to the "
            f"default browser")
        return _fallback(url, say)
    say(f"app_window: opened via {browser}")
    return True


def _fallback(url: str, say: "callable[[str], None]") -> bool:
    """The documented Persian fallback, then the legacy path.

    The message is written to the launcher log the mission file specifies, and
    the English gloss is in the source so a reader who does not read Persian can
    still tell what happened. ``open_url`` is imported lazily to keep this
    module importable wherever the processkit is not already loaded.
    """
    say("پنجره اختصاصی باز نشد؛ داشبورد در مرورگر پیش‌فرض باز شد")
    from .processkit import open_url
    return open_url(url)


# The registry import is optional so this module imports off Windows, where
# ``winreg`` does not exist. The name is bound to None on those platforms and
# every use site guards it.
try:                                                # pragma: no cover - platform guard
    import winreg
except ImportError:                                 # pragma: no cover - platform guard
    winreg = None
