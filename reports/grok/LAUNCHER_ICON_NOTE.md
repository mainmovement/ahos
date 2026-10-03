# Launcher icon + single desktop shortcut

Written to this file instead of CLAUDE_CONTINUATION_GUIDE.md because launcher/shortcuts.py had uncommitted M11 changes from Claude (PID 12464) when the icon was installed.

**Rule for all launcher work (owner decision):**
- **One desktop icon only:** `AHOS.lnk` -> `launcher\ahos.ps1 -Action start`. No `AHOS Status.lnk` / `AHOS Stop.lnk`.
- **Status and stop belong inside the dashboard**, not on the desktop.
- **No visible console windows anywhere in the launcher** (shortcuts, child processes, restarts): use
  `-WindowStyle Hidden` for powershell.exe, `CREATE_NO_WINDOW` / `pythonw.exe` for Python children.

**Done by Grok on 2026-10-03, about 20:08 Tehran (desktop, not in git):** `AHOS Status.lnk` and `AHOS Stop.lnk` moved to
`launcher\_retired_shortcuts\` (not deleted). `AHOS.lnk` now has IconLocation `G:\robat\ahos\launcher\ahos.ico,0`,
WindowStyle 7 (minimized) and args
`-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "G:\robat\ahos\launcher\ahos.ps1" -Action start`.
New icon committed: `launcher\ahos.ico` (16-256 px, transparent rounded corners) + `launcher\assets\ahos_icon_1024.png`.

**Pending change for `launcher/shortcuts.py` (NOT edited by Grok: the file had uncommitted M11 changes from Claude, PID 12464):**
1. `ACTIONS = {"start": "AHOS"}` (drop stop/status); update the module docstring ("One shortcut ... AHOS (start)").
2. In `shortcut_specs()`, build args as
   `-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{script}" -Action start`
   and remove the `-Json` status branch.
3. In `_PS_TEMPLATE`, set `$lnk.WindowStyle = 7` (minimized) instead of `1`.
4. Keep the icon default `root / "launcher" / "ahos.ico"` (already the new icon).
5. Optional: in `create_shortcuts()`, if `AHOS Status.lnk` / `AHOS Stop.lnk` exist on the target desktop, move
   them to `launcher\_retired_shortcuts\` rather than leaving or deleting them.
6. Update `tests/` expectations that assume three specs (grep `shortcut_specs`), and check `ahos.ps1` itself
   doesn't spawn visible consoles (`Start-Process ... -WindowStyle Hidden`).

Old 260-byte icon kept (untracked) as `launcher\ahos.ico.old-20261003-200745`.
