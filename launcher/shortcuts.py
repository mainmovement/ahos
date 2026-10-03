"""Desktop shortcuts for the owner, created with WScript.Shell (built into
Windows, no pywin32 needed).

Three shortcuts on the desktop of the user named in ``--user`` (default: the
current user): AHOS (start), AHOS Stop, AHOS Status. Each runs the PowerShell
console wrapper, which keeps the window UTF-8 and delegates to the Python
orchestrator.

The command-line pieces are pure functions so they can be unit-tested without
touching the real desktop; ``create_shortcuts()`` performs the COM writes via a
short PowerShell invocation.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ACTIONS = {"start": "AHOS", "stop": "AHOS Stop", "status": "AHOS Status"}

_PS_TEMPLATE = r"""
$ErrorActionPreference = 'Stop'
$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
foreach ($spec in $specs) {
  $lnk = $ws.CreateShortcut((Join-Path $desktop $spec.Name))
  $lnk.TargetPath = $spec.TargetPath
  $lnk.Arguments = $spec.Arguments
  $lnk.WorkingDirectory = $spec.WorkingDirectory
  $lnk.IconLocation = $spec.IconLocation
  $lnk.WindowStyle = 1
  $lnk.Description = $spec.Description
  $lnk.Save()
}
"""


def shortcut_specs(root: Path, icon: Path,
                   user: str | None = None) -> list[dict]:
    """Pure: what each shortcut should point at. No filesystem writes."""
    root = Path(root).resolve()
    icon = Path(icon).resolve()
    ps = Path(sys.executable).resolve()
    # Prefer the Windows PowerShell console for the .lnk target so a double
    # click opens a readable window with the right code page.
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / \
        "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    target = str(powershell) if powershell.exists() else str(ps)
    script = str(root / "launcher" / "ahos.ps1")
    specs = []
    for action, label in ACTIONS.items():
        args = f'-NoProfile -ExecutionPolicy Bypass -File "{script}" -Action {action}'
        if action == "status":
            args += " -Json"
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


def create_shortcuts(root: Path | str | None = None, *,
                     icon: Path | str | None = None,
                     user: str | None = None,
                     desktop: Path | str | None = None) -> list[dict]:
    """Create the .lnk files and report what was written."""
    root = Path(root) if root else Path(__file__).resolve().parent.parent
    icon = Path(icon) if icon else root / "launcher" / "ahos.ico"
    if not icon.exists():
        raise FileNotFoundError(f"icon missing: {icon}")
    specs = shortcut_specs(root, icon, user)
    out_dir = Path(desktop) if desktop else desktop_dir(user)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Marshal the specs into PowerShell as a here-string; the COM object does
    # the actual .lnk writing.
    ps_specs = "[" + ",".join(
        '@{Name="%s";TargetPath="%s";Arguments="%s";WorkingDirectory="%s";'
        'IconLocation="%s";Description="%s"}' % (
            s["name"], s["target_path"], s["arguments"].replace('"', "`\""),
            s["working_directory"], s["icon_location"], s["description"])
        for s in specs) + "]"
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
           "-Command", f"$specs = {ps_specs}; {_PS_TEMPLATE}"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"shortcut creation failed ({res.returncode}): "
                           f"{(res.stderr or '').strip()[:400]}")
    return [{"path": str(out_dir / s["name"]), **{k: v for k, v in s.items()}}
            for s in specs]


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Create the AHOS desktop shortcuts")
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
