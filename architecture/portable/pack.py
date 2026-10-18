"""Stage a portable AHOS folder.

Copies an allowlist, drops secret-shaped files, and writes a health script
plus a data-move note. It does not download Python or Node, does not read
.env, and does not write a destination on a fixed drive letter.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

INCLUDE_DIRS: tuple[str, ...] = (
    "core/idea_shelf",
    "architecture/health",
)
INCLUDE_FILES: tuple[str, ...] = (
    "core/__init__.py",
    "architecture/__init__.py",
    "config/paths.py",
    "config/idea_shelf.json",
    "config/university/sources.yaml",
)

DENY_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "cookies.txt",
}
DENY_SUFFIXES = {".pem", ".key"}
OWNER_PATH_MARKERS = ("C:\\Users\\Sniper", "C:/Users/Sniper")


@dataclass(frozen=True, slots=True)
class BundleReport:
    dest: str
    copied: tuple[str, ...]
    skipped_secrets: tuple[str, ...]
    health_ok: bool
    paper_only: bool
    env_present: bool
    owner_path_leaks: tuple[str, ...]


def _denied(path: Path) -> bool:
    name = path.name.lower()
    if name in DENY_NAMES or name.startswith(".env"):
        return True
    return path.suffix.lower() in DENY_SUFFIXES


def _iter_includes(src: Path) -> list[Path]:
    found: list[Path] = []
    for rel in INCLUDE_FILES:
        path = src / rel
        if path.is_file():
            found.append(path)
    for rel in INCLUDE_DIRS:
        root = src / rel
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                found.append(path)
    return found


def _leaks(path: Path) -> bool:
    if path.suffix.lower() not in {".py", ".md", ".txt", ".ps1", ".json"}:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return any(marker in text for marker in OWNER_PATH_MARKERS)


def build_bundle(src: Path, dest: Path) -> BundleReport:
    src = Path(src).resolve()
    dest = Path(dest).resolve()
    if dest == src or src in dest.parents:
        raise ValueError("destination must sit outside the source tree")
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("destination must be an empty directory")
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []
    for path in _iter_includes(src):
        rel = path.relative_to(src).as_posix()
        if _denied(path):
            skipped.append(rel)
            continue
        target = dest / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(rel)

    (dest / "config").mkdir(parents=True, exist_ok=True)
    init = dest / "config" / "__init__.py"
    if not init.exists():
        init.write_text('"""Portable config package."""\n', encoding="utf-8")
        copied.append("config/__init__.py")

    (dest / "portable_health.py").write_text(_HEALTH_PY, encoding="utf-8")
    (dest / "AHOS_Portable_Health.ps1").write_text(_HEALTH_PS1, encoding="utf-8")
    (dest / "DATA_MOVE.txt").write_text(_DATA_MOVE, encoding="utf-8")
    (dest / "PAPER_ONLY").write_text("paper_only=true\n", encoding="utf-8")
    copied.extend([
        "portable_health.py",
        "AHOS_Portable_Health.ps1",
        "DATA_MOVE.txt",
        "PAPER_ONLY",
    ])
    return inspect_bundle(dest, copied=tuple(copied), skipped=tuple(skipped))


def inspect_bundle(
    dest: Path,
    *,
    copied: tuple[str, ...] = (),
    skipped: tuple[str, ...] = (),
) -> BundleReport:
    dest = Path(dest)
    env_present = any(p.name.lower().startswith(".env") for p in dest.rglob("*") if p.is_file())
    leaks = tuple(
        p.relative_to(dest).as_posix()
        for p in dest.rglob("*")
        if p.is_file() and _leaks(p)
    )
    paper = (dest / "PAPER_ONLY").is_file() and "paper_only=true" in (dest / "PAPER_ONLY").read_text(encoding="utf-8")
    health_ok = paper and not env_present and not leaks and (dest / "portable_health.py").is_file()
    return BundleReport(
        dest=str(dest),
        copied=copied,
        skipped_secrets=skipped,
        health_ok=health_ok,
        paper_only=paper,
        env_present=env_present,
        owner_path_leaks=leaks,
    )


_HEALTH_PY = '''"""Post-move health check. Paper only. Does not read secrets."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.idea_shelf.hardware import detect_hardware


def main() -> int:
    if any(p.name.lower().startswith(".env") for p in ROOT.rglob("*") if p.is_file()):
        print("FAIL secret-shaped env file is inside the bundle")
        return 1
    marker = ROOT / "PAPER_ONLY"
    if not marker.is_file():
        print("FAIL PAPER_ONLY marker missing")
        return 1
    probe = detect_hardware()
    print(f"paper_only=true tier={probe.tier} source={probe.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

_HEALTH_PS1 = """# Portable health shortcut. Uses this folder, never a fixed drive path.
Set-Location -LiteralPath $PSScriptRoot
$py = Join-Path $PSScriptRoot "python\\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }
& $py (Join-Path $PSScriptRoot "portable_health.py")
exit $LASTEXITCODE
"""

_DATA_MOVE = """AHOS portable data move (paper only)

1. Copy this folder to the new machine. Do not copy .env, cookies, or key files.
2. Put data you choose to move in a data folder next to this bundle.
3. Secrets stay out of the folder. Enter them again in Windows Credential Manager yourself.
4. Do not change DATABASE_URL. That switch is an owner act.
5. Run AHOS_Portable_Health.ps1. It must print paper_only=true.
6. This bundle does not include a vendored Python or Node runtime.
"""
