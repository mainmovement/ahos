"""The single owner desktop shortcut, created with WScript.Shell (built into
Windows, no pywin32 needed).

One icon: ``AHOS.lnk`` (start). Status, Stop and Restart live *inside the
dashboard* (Parvaneh P1) — a second desktop surface would contradict the
owner rule of one icon, and three icons invite a click on "Stop" as the first
reflex. The shortcut runs the PowerShell console wrapper hidden, so no black
window appears at any point: ``-WindowStyle Hidden`` on the launcher is what
makes it invisible, while the .lnk's own ``WindowStyle = 7`` (minimised) is
only a fallback presentation hint for hosts that ignore the argument.

The command-line pieces are pure functions so they can be unit-tested without
touching the real desktop; ``create_shortcuts()`` performs the COM writes via a
short PowerShell invocation, and retires the two pre-M11.1 shortcuts by *moving*
them into ``launcher/_retired_shortcuts/`` (never deleting the owner's files).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PureWindowsPath

ACTIONS = {"start": "AHOS"}

# Shortcuts this module created before M11.1. If one of these is still on the
# desktop it is moved aside, not removed: the owner may have arranged them.
LEGACY_NAMES = ("AHOS Stop.lnk", "AHOS Status.lnk")

_PS_TEMPLATE = r"""
$ErrorActionPreference = 'Stop'
$ws = New-Object -ComObject WScript.Shell
$desktop = $out_dir
foreach ($spec in $specs) {
  $lnk = $ws.CreateShortcut((Join-Path $desktop $spec.Name))
  $lnk.TargetPath = $spec.TargetPath
  $lnk.Arguments = $spec.Arguments
  $lnk.WorkingDirectory = $spec.WorkingDirectory
  $lnk.IconLocation = $spec.IconLocation
  # 7 = minimised. The shortcut is invisible in practice because the arguments
  # carry -WindowStyle Hidden; this is only the hint a host falls back to.
  $lnk.WindowStyle = 7
  $lnk.Description = $spec.Description
  $lnk.Save()
}
"""


def shortcut_specs(root: Path, icon: Path,
                   user: str | None = None) -> list[dict]:
    """Pure: what each shortcut should point at. No filesystem writes."""
    root = Path(root).resolve()
    icon = Path(icon).resolve()
    # The .lnk target is always Windows PowerShell 5.1: it ships with every
    # supported Windows and is the only host the arguments below are valid for.
    # (The old fallback to sys.executable produced a shortcut that ran
    # ``python.exe -NoProfile -ExecutionPolicy Bypass ...``, which can never
    # start.) PureWindowsPath keeps the string correct even when the specs are
    # computed on a non-Windows host (tests, review boxes).
    powershell = PureWindowsPath(os.environ.get("SystemRoot") or r"C:\Windows") / \
        "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    target = str(powershell)
    script = str(root / "launcher" / "ahos.ps1")
    specs = []
    for action, label in ACTIONS.items():
        args = (f'-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden '
                f'-File "{script}" -Action {action}')
        specs.append({
            "name": f"{label}.lnk",
            "target_path": target,
            "arguments": args,
            "working_directory": str(root),
            "icon_location": f"{icon},0",
            "description": f"AHOS {action} (paper mode)",
        })
    return specs


def desktop_dir(user: str | None = None) -> Path:
    if user:
        return Path(os.environ.get("SystemDrive", "C:")) / "Users" / user / "Desktop"
    return Path(os.path.expanduser("~")) / "Desktop"


def retire_legacy_shortcuts(desktop: Path, retire_dir: Path) -> list[str]:
    """Move pre-M11.1 shortcuts into ``retire_dir``. Returns what was moved.

    Never deletes: the owner's desktop layout is theirs. A move is reversible,
    a delete is not, and a stale "AHOS Stop" icon left beside the new one would
    be exactly the duplicate surface M11.1 removes.
    """
    moved: list[str] = []
    retire_dir.mkdir(parents=True, exist_ok=True)
    for name in LEGACY_NAMES:
        src = Path(desktop) / name
        if not src.is_file():
            continue
        dst = retire_dir / f"{name}.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            shutil.move(str(src), str(dst))
        except OSError:
            continue
        moved.append(str(src))
    return moved


def create_shortcuts(root: Path | str | None = None, *,
                     icon: Path | str | None = None,
                     user: str | None = None,
                     desktop: Path | str | None = None) -> list[dict]:
    """Create the .lnk file(s) and report what was written."""
    root = Path(root) if root else Path(__file__).resolve().parent.parent
    icon = Path(icon) if icon else root / "launcher" / "ahos.ico"
    if not icon.exists():
        raise FileNotFoundError(f"icon missing: {icon}")
    specs = shortcut_specs(root, icon, user)
    out_dir = Path(desktop) if desktop else desktop_dir(user)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Marshal the specs into PowerShell as an array subexpression; the COM
    # object does the actual .lnk writing. (@(...) not [...]: a bare bracket
    # literal is a type cast in PowerShell and fails to parse.)
    ps_specs = "@(" + ",".join(
        '@{Name="%s";TargetPath="%s";Arguments="%s";WorkingDirectory="%s";'
        'IconLocation="%s";Description="%s"}' % (
            s["name"], s["target_path"], s["arguments"].replace('"', "`\""),
            s["working_directory"], s["icon_location"], s["description"])
        for s in specs) + ")"
    # A single-quoted PowerShell string needs its own apostrophes doubled, or a
    # desktop path containing one truncates the argument silently.
    ps_out_dir = str(out_dir).replace("'", "''")
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
           "-Command",
           f"$out_dir = '{ps_out_dir}'; $specs = {ps_specs}; {_PS_TEMPLATE}"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                         creationflags=0x08000000 if os.name == "nt" else 0)
    if res.returncode != 0:
        raise RuntimeError(f"shortcut creation failed ({res.returncode}): "
                           f"{(res.stderr or '').strip()[:400]}")
    return [{"path": str(out_dir / s["name"]), **{k: v for k, v in s.items()}}
            for s in specs]


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Create the AHOS desktop shortcut")
    ap.add_argument("--user", default=None, help="desktop owner (default: current user)")
    ap.add_argument("--root", default=None, help="repository root")
    ap.add_argument("--icon", default=None, help="path to ahos.ico")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the shortcut specs without writing anything")
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    icon = Path(args.icon) if args.icon else root / "launcher" / "ahos.ico"
    if args.dry_run:
        for s in shortcut_specs(root, icon, args.user):
            print(f"{s['name']}\n  target: {s['target_path']}\n  args:   {s['arguments']}\n"
                  f"  icon:   {s['icon_location']}")
        return 0
    for s in create_shortcuts(root, icon=icon, user=args.user):
        print(f"wrote {s['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
