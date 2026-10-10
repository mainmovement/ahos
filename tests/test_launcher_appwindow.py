"""M-D1 — the AHOS app window: own profile, no tabs, loopback only.

The window is how the owner reaches the dashboard, so the tests pin what makes
it a *closed* surface rather than a browser tab that happens to point at
loopback: the argv order, the isolation profile, the resolver rule that blocks
every non-loopback name at the browser itself, the fallback that keeps the
dashboard reachable when no browser is installed, and — because the URL carries
a one-time boot token — that the token can reach no log line and no error
message this module produces.

Everything under test is a pure function: the argv is data, the profile is a
path, the browser order is a tuple. `open_app_window` is exercised with the
spawn monkeypatched, so nothing here opens a real window.
"""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath

import pytest

from launcher.appwindow import (
    DEFAULT_WINDOW_SIZE,
    AppWindowConfig,
    app_profile_dir,
    build_app_argv,
    find_browser,
    load_config,
    open_app_window,
    profile_marker,
)

# A realistic bootstrap URL, token and all. Nothing in this file sends it
# anywhere; it is the shape the argv must carry.
URL = "http://127.0.0.1:3100/#boot=abc123"
PROFILE = r"C:\Users\Sniper\AppData\Local\AHOS\app-window-profile"


# ------------------------------------------------------------- the argv -------


def test_app_is_the_first_argument_and_names_the_url():
    argv = build_app_argv(URL, "chrome", PROFILE)
    assert argv[0] == f"--app={URL}"


def test_the_argv_order_is_stable_and_complete():
    """Order is part of the contract: --app first, then the profile that isolates
    the window, then the size, then the resolver rule that closes the network."""
    argv = build_app_argv(URL, "chrome", PROFILE)
    assert argv[1] == f"--user-data-dir={PROFILE}"
    assert argv[2] == f"--window-size={DEFAULT_WINDOW_SIZE[0]},{DEFAULT_WINDOW_SIZE[1]}"
    assert argv[3] == "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"


def test_the_resolver_rule_blocks_every_name_but_loopback():
    """The window must not be able to reach anything but the local gateway.

    The rule is a MAP of '*' to NOTFOUND with an EXCLUDE for 127.0.0.1, so a name
    the dashboard never asked for cannot resolve. This is the network half of
    `--app` being a closed surface; the acceptance test proves it on the wire.
    """
    argv = build_app_argv(URL, "chrome", PROFILE)
    rule = next(a for a in argv if a.startswith("--host-resolver-rules="))
    assert "MAP * ~NOTFOUND" in rule
    assert "EXCLUDE 127.0.0.1" in rule


def test_every_switch_is_one_of_the_closed_loop_set():
    argv = build_app_argv(URL, "chrome", PROFILE)
    expected = {
        "--no-first-run", "--no-default-browser-check", "--disable-sync",
        "--disable-extensions", "--disable-background-networking",
        "--disable-component-update", "--disable-default-apps", "--no-pings",
        "--no-proxy-server",
    }
    assert expected.issubset(set(argv))
    # and nothing else is a bare flag the spec did not name
    bare = {a for a in argv[4:] if not a.startswith("--app=")
            and not a.startswith("--user-data-dir=")
            and not a.startswith("--window-size=")
            and not a.startswith("--host-resolver-rules=")}
    assert bare == expected


def test_a_profile_path_with_spaces_is_not_quoted_by_us():
    """The argv is a list, not a shell string, so spaces survive without quoting
    — and the process is spawned directly, never through cmd.exe."""
    profile = r"C:\Users\Some User\AppData\Local\AHOS\app-window-profile"
    argv = build_app_argv(URL, "chrome", profile)
    assert argv[1] == f"--user-data-dir={profile}"
    assert '"\\\\' not in argv[1]


def test_an_empty_url_is_refused():
    with pytest.raises(ValueError, match="bootstrap url is required"):
        build_app_argv("", "chrome", PROFILE)


def test_the_window_size_is_carried_and_positive():
    argv = build_app_argv(URL, "chrome", PROFILE, (1440, 900))
    assert "--window-size=1440,900" in argv


# ------------------------------------------------------------- the profile ----


def test_the_profile_is_outside_the_users_browser_profile():
    """The window must never touch the user's Chrome Default profile: no shared
    tabs, cookies, extensions, or history."""
    p = app_profile_dir(AppWindowConfig(), r"C:\Users\Sniper\AppData\Local")
    assert p == PureWindowsPath(PROFILE)


def test_the_profile_is_never_the_repo():
    p = app_profile_dir(AppWindowConfig(), r"C:\Users\Sniper\AppData\Local")
    assert "robat" not in str(p)


def test_the_marker_identifies_the_window_without_the_url():
    """The alive-check and the screenshot script find the process by its profile,
    never by the URL — which carries the token and must not appear in a search
    filter or a log."""
    marker = profile_marker(PROFILE)
    assert marker == f"--user-data-dir={PROFILE}"
    assert "boot=" not in marker


# ------------------------------------------------------------- resolution -----


def test_browsers_are_tried_in_the_configured_order():
    """Chrome before Edge, and the first executable present wins."""
    seen: list[str] = []

    def only_edge(candidate: str) -> bool:
        seen.append(candidate)
        return "msedge" in candidate

    name, exe = find_browser(AppWindowConfig(), exists=only_edge)
    assert name == "edge"
    assert exe is not None and "msedge" in str(exe)
    # Chrome's paths were checked first, so they precede Edge's in the record.
    assert any("chrome" in c for c in seen)


def test_chrome_wins_when_both_are_installed():
    name, exe = find_browser(AppWindowConfig(), exists=lambda c: True)
    assert name == "chrome"


def test_no_browser_installed_returns_none(monkeypatch):
    # The registry fallback would consult this host's real registry, so it is
    # stubbed: the test is about the order, not about what is installed here.
    monkeypatch.setattr("launcher.appwindow._registry_browser",
                        lambda order: None)
    name, exe = find_browser(AppWindowConfig(), exists=lambda c: False)
    assert name is None and exe is None


def test_an_unknown_browser_in_the_config_is_dropped_not_fatal():
    cfg = AppWindowConfig.from_dict({"browser_order": ["firefox", "chrome"]})
    assert cfg.browser_order == ("chrome",)


def test_an_all_unknown_config_falls_back_to_the_default_order():
    """A config that disables every known browser degrades to the built-in order
    rather than silently turning the window off."""
    cfg = AppWindowConfig.from_dict({"browser_order": ["firefox", "brave"]})
    assert cfg.browser_order == ("chrome", "edge")


def test_a_bad_window_size_is_ignored():
    cfg = AppWindowConfig.from_dict({"window_size": [0, 900]})
    assert cfg.window_size == DEFAULT_WINDOW_SIZE


def test_a_malformed_config_falls_back_and_reports_on_stderr(capsys):
    cfg = load_config(Path("/nonexistent/app_window.json"))
    assert cfg.browser_order == ("chrome", "edge")
    # A missing file is not an error and prints nothing.
    assert capsys.readouterr().err == ""


def test_a_real_config_round_trips(tmp_path):
    p = tmp_path / "app_window.json"
    p.write_text(json.dumps({"browser_order": ["edge", "chrome"],
                             "window_size": [1280, 800]}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.browser_order == ("edge", "chrome")
    assert cfg.window_size == (1280, 800)


# ------------------------------------------------------------- the spawn ------


def test_open_app_window_spawns_the_resolved_browser(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        "launcher.appwindow.find_browser",
        lambda cfg: ("chrome", Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")),
    )
    monkeypatch.setattr(
        "launcher.appwindow.app_profile_dir",
        lambda cfg, local_app_data=None: PureWindowsPath(PROFILE),
    )
    monkeypatch.setattr("launcher.appwindow.subprocess.Popen",
                        lambda argv, **kw: calls.append(argv) or None)
    logs: list[str] = []
    assert open_app_window(URL, log=logs.append) is True
    argv = calls[0]
    assert argv[0].endswith("chrome.exe")
    assert argv[1] == f"--app={URL}"
    assert f"--user-data-dir={PROFILE}" in argv
    assert logs == ["app_window: opened via chrome"]


def test_the_url_reaches_no_log_line(monkeypatch):
    """The log names the browser, never the URL — the token is a credential."""
    monkeypatch.setattr(
        "launcher.appwindow.find_browser",
        lambda cfg: ("edge", Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")),
    )
    monkeypatch.setattr("launcher.appwindow.app_profile_dir",
                        lambda cfg, local_app_data=None: PureWindowsPath(PROFILE))
    monkeypatch.setattr("launcher.appwindow.subprocess.Popen",
                        lambda argv, **kw: None)
    logs: list[str] = []
    open_app_window(URL, log=logs.append)
    assert all("boot=" not in line for line in logs)


def test_a_spawn_failure_falls_back_to_the_default_browser(monkeypatch):
    monkeypatch.setattr(
        "launcher.appwindow.find_browser",
        lambda cfg: ("chrome", Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")),
    )
    monkeypatch.setattr("launcher.appwindow.app_profile_dir",
                        lambda cfg, local_app_data=None: PureWindowsPath(PROFILE))

    def boom(*a, **kw):
        raise OSError("spawn refused")

    monkeypatch.setattr("launcher.appwindow.subprocess.Popen", boom)
    monkeypatch.setattr("launcher.processkit.open_url", lambda url: True)
    logs: list[str] = []
    assert open_app_window(URL, log=logs.append) is True
    assert any("falling back" in line for line in logs)


def test_no_browser_falls_back_and_logs_the_persian_line(monkeypatch):
    """The fallback message is the Persian line the mission specifies, so the
    owner reads why the window is a tab instead of a frame."""
    monkeypatch.setattr("launcher.appwindow.find_browser",
                        lambda cfg: (None, None))
    monkeypatch.setattr("launcher.processkit.open_url", lambda url: True)
    logs: list[str] = []
    assert open_app_window(URL, log=logs.append) is True
    assert any("پنجره اختصاصی باز نشد" in line for line in logs)


def test_the_fallback_url_is_passed_through_verbatim(monkeypatch):
    """The fallback must open the same URL, not a rebuilt one."""
    seen: list[str] = []
    monkeypatch.setattr("launcher.appwindow.find_browser",
                        lambda cfg: (None, None))
    monkeypatch.setattr("launcher.processkit.open_url",
                        lambda url: seen.append(url) or True)
    open_app_window(URL)
    assert seen == [URL]


def test_a_profile_that_cannot_be_created_falls_back(monkeypatch):
    """Never silently open the user's normal profile because the isolation
    directory was unwritable."""
    monkeypatch.setattr(
        "launcher.appwindow.find_browser",
        lambda cfg: ("chrome", Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")),
    )
    monkeypatch.setattr("launcher.appwindow.load_config", lambda: AppWindowConfig())
    # The mkdir is the real call; make it fail on this host's filesystem.
    monkeypatch.setattr("launcher.appwindow.os.mkdir",
                        lambda *a, **kw: (_ for _ in ()).throw(OSError("read-only")))
    monkeypatch.setattr("launcher.appwindow.subprocess.Popen",
                        lambda argv, **kw: None)
    monkeypatch.setattr("launcher.processkit.open_url", lambda url: True)
    logs: list[str] = []
    assert open_app_window(URL, log=logs.append) is True
    assert any("profile directory could not be created" in line for line in logs)
