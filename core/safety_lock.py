"""M70.6 Cryptographic Safety Lock.
Verifies SHA-256 integrity of all constitutional safety files at startup and blocks any write
attempt by self-debug (M46) or self-improvement (M51) loops to safety files, HOLD.flag, .env, or Lane A.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

PROTECTED_SAFETY_FILES: tuple[str, ...] = (
    "architecture/markets/risk.py",
    "architecture/markets/judge.py",
    "architecture/markets/tier_gate.py",
    "architecture/mission/ledger.py",
    "architecture/health/safety_lock.py",
    "core/safety_lock.py",
    "config/lane_a_freeze.sha256",
    "HOLD.flag",
)

FORBIDDEN_WRITE_PREFIXES: tuple[str, ...] = (
    "discovery/",
    "paper_trading/",
    ".env",
)


def _repo_root(root: Path | None = None) -> Path:
    return (root or Path(__file__).resolve().parents[1]).resolve()


def compute_safety_manifest(root: Path | None = None) -> dict[str, str]:
    """Compute SHA-256 hashes of all protected safety files."""
    base = _repo_root(root)
    manifest: dict[str, str] = {}
    for rel in PROTECTED_SAFETY_FILES:
        p = base / rel
        if p.is_file():
            manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return manifest


def verify_safety_lock(
    root: Path | None = None,
    expected: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify all protected safety files exist and match expected SHA-256 hashes."""
    base = _repo_root(root)
    current = compute_safety_manifest(base)
    missing = [rel for rel in PROTECTED_SAFETY_FILES if rel not in current]
    mismatched: list[str] = []
    if expected is not None:
        for rel, exp_hash in expected.items():
            if current.get(rel) != exp_hash:
                mismatched.append(rel)
    ok = len(missing) == 0 and len(mismatched) == 0
    return {
        "status": "LOCKED_CLEAN" if ok else "HALT_TAMPERED",
        "ok": ok,
        "verified_files": len(current),
        "missing": missing,
        "mismatched": mismatched,
        "manifest": current,
    }


def guard_autonomous_write(
    target_path: str | Path,
    *,
    actor: str = "autonomous_loop",
    root: Path | None = None,
) -> bool:
    """Block any autonomous loop from modifying safety files, HOLD.flag, .env, or Lane A."""
    base = _repo_root(root)
    t = Path(target_path)
    rel = t.resolve().relative_to(base).as_posix() if t.is_absolute() and base in t.resolve().parents else t.as_posix().removeprefix("./")
    if (
        rel in PROTECTED_SAFETY_FILES
        or rel.endswith("HOLD.flag")
        or rel.endswith(".env")
        or any(rel.startswith(pref) for pref in FORBIDDEN_WRITE_PREFIXES)
    ):
        raise PermissionError(
            f"M70.6 SAFETY LOCK: {actor} is forbidden from modifying protected path {rel!r}"
        )
    return True
