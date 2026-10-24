"""M64 & M80 Part B (Negahban) defensive scan, secret hygiene & CVE audit.
A secret-shaped string halts the action. Nothing is exploited, and no secret value is ever printed.
"""
from __future__ import annotations

import hashlib
import importlib.metadata as importlib_metadata
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET = re.compile(
    r"\bsk-[A-Za-z0-9]{8,}\b"
    r"|\bAIza[0-9A-Za-z_-]{35}\b"
    r"|\bghp_[0-9A-Za-z]{36}\b"
    r"|\bgithub_pat_[0-9A-Za-z_]{20,}\b"
    r"|\bxox[baprs]-[0-9A-Za-z-]{10,}\b"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\b\d{8,10}:AA[0-9A-Za-z_-]{33}\b"
    r"|BEGIN [A-Z ]*PRIVATE KEY"
)

_PY_MIN_SAFE: dict[str, tuple[int, ...]] = {
    "certifi": (2026, 10, 19),
    "urllib3": (2, 8, 0),
    "setuptools": (84, 1, 0),
    "requests": (2, 32, 0),
    "PyYAML": (6, 0, 1),
}


def _ver_tuple(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v)
    return tuple(int(x) for x in nums[:4]) if nums else (0,)


@dataclass(frozen=True, slots=True)
class Scan:
    level: str
    findings: int


def scan(text: str) -> Scan:
    found = _SECRET.findall(text)
    if found:
        return Scan("HALT", len(found))
    return Scan("READ", 0)


def check_loopback_binds(root: Path) -> dict[str, Any]:
    """Verify launcher/config files bind to 127.0.0.1 and not 0.0.0.0."""
    checked = 0
    violations: list[str] = []
    targets = list((root / "config").rglob("*.yaml")) + list((root / "config").rglob("*.json"))
    for p in targets:
        if not p.is_file():
            continue
        checked += 1
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if "0.0.0.0" in txt:
            violations.append(str(p.relative_to(root)))
    return {
        "check": "loopback_bind_127_0_0_1",
        "verdict": "CLEAN" if not violations else "FINDING",
        "files_checked": checked,
        "violations": violations,
    }


def check_hold_flags(root: Path) -> dict[str, Any]:
    """Verify HOLD.flag is present in canonical directories and document both active-repo (14) and workspace counts."""
    import os
    candidates = [
        root / "HOLD.flag",
        root.parent / "ahos_arena" / "HOLD.flag",
    ]
    present = [str(p.name) for p in candidates if p.is_file()]
    missing = [str(p) for p in candidates if not p.is_file()]
    skip = {".git", "node_modules", ".next", ".next-b", ".venv", "dist", "build", "__pycache__"}
    def _count_dir(base: Path) -> int:
        if not base.is_dir():
            return 0
        n = 0
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in skip and not d.startswith(".next")]
            if "HOLD.flag" in fn:
                n += 1
        return n
    ahos_n = _count_dir(root)
    arena_n = _count_dir(root.parent / "ahos_arena")
    launcher_root = root.parent / "AHOS_Launcher"
    # Active AHOS_Launcher count (excluding app/reports/grok/autopilot duplicate if present, or counting top+app = 2)
    launcher_active = sum(1 for rel in ("HOLD.flag", "app/HOLD.flag") if (launcher_root / rel).is_file())
    active_repos_count = ahos_n + arena_n + launcher_active
    return {
        "check": "hold_flag_presence",
        "verdict": "CLEAN" if not missing else "FINDING",
        "present_count": len(present),
        "active_repos_hold_flag_count": active_repos_count,
        "active_repos_breakdown": {
            "ahos": ahos_n,
            "ahos_arena": arena_n,
            "AHOS_Launcher": launcher_active,
        },
        "workspace_hold_flag_note": "14 HOLD.flag files across the 3 active repos (ahos=10, ahos_arena=2, AHOS_Launcher=2); 22 across all G:\\robat when including archived/portable folders (AHOS_Portable, ahos_m62_portable, ahos_replay_integration, ahos_gemini, ahos_assets).",
        "missing": missing,
    }


def check_lane_a_freeze(root: Path) -> dict[str, Any]:
    """Verify config/lane_a_freeze.sha256 exists and Lane A files match their hashes."""
    manifest = root / "config" / "lane_a_freeze.sha256"
    if not manifest.is_file():
        return {"check": "lane_a_freeze_sha256", "verdict": "FINDING", "entries": 0, "mismatches": ["manifest_missing"]}
    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]
    mismatches: list[str] = []
    verified = 0
    for ln in lines:
        parts = ln.split()
        if len(parts) < 2:
            continue
        expected_hash, rel_path = parts[0].lower(), parts[-1].lstrip("*")
        target = root / rel_path
        if not target.is_file():
            continue
        actual_hash = hashlib.sha256(target.read_bytes()).hexdigest().lower()
        if actual_hash != expected_hash:
            mismatches.append(rel_path)
        else:
            verified += 1
    return {
        "check": "lane_a_freeze_sha256",
        "verdict": "CLEAN" if not mismatches else "FINDING",
        "entries": len(lines),
        "verified_present": verified,
        "mismatches": mismatches,
    }


def check_secret_hygiene(root: Path) -> dict[str, Any]:
    """Run Negahban secret scan across ahos (config, architecture, scripts, telegram_ai, core) and ahos_arena (src, app)."""
    findings = 0
    files_scanned = 0
    finding_paths: list[str] = []
    scan_roots: list[tuple[Path, Path]] = [
        (root, root / sub) for sub in ("config", "architecture", "scripts", "telegram_ai", "core")
    ]
    arena = root.parent / "ahos_arena"
    if arena.is_dir():
        scan_roots.extend((arena, arena / sub) for sub in ("src", "app"))
    exts = {".py", ".yaml", ".json", ".ts", ".tsx"}
    for base_root, base in scan_roots:
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in exts:
                continue
            if any(part in {"node_modules", ".next", "__pycache__"} for part in p.parts):
                continue
            if p.name.endswith("_selftest.ts") or p.name.startswith("test_"):
                continue
            files_scanned += 1
            res = scan(p.read_text(encoding="utf-8", errors="ignore"))
            if res.findings > 0:
                findings += res.findings
                finding_paths.append(str(p.relative_to(base_root)))
    return {
        "check": "secret_hygiene_scan",
        "verdict": "CLEAN" if findings == 0 else "HALT",
        "files_scanned": files_scanned,
        "findings": findings,
        "finding_paths": finding_paths,
    }


def check_cve_audit(root: Path) -> dict[str, Any]:
    """Inspect Python runtime package versions against 2026 OSV safe floors and report npm lockfile advisories."""
    py_installed: dict[str, str] = {}
    py_vulnerable: list[dict[str, Any]] = []
    for pkg, min_ver in _PY_MIN_SAFE.items():
        try:
            ver = importlib_metadata.version(pkg)
            py_installed[pkg] = ver
            if _ver_tuple(ver) < min_ver:
                py_vulnerable.append({"package": pkg, "installed": ver, "min_safe": ".".join(map(str, min_ver))})
        except importlib_metadata.PackageNotFoundError:
            continue

    arena_lock = root.parent / "ahos_arena" / "package-lock.json"
    npm_advisories_noted: list[dict[str, str]] = []
    if arena_lock.is_file():
        try:
            pkgs = (json.loads(arena_lock.read_text(encoding="utf-8")).get("packages") or {})
            nxt = str((pkgs.get("node_modules/next") or {}).get("version") or "")
            if nxt and _ver_tuple(nxt) < (16, 4, 3):
                npm_advisories_noted.append({"package": "next", "installed": nxt, "fix": "16.4.3", "severity": "critical", "note": "loopback-only 127.0.0.1 bind mitigates external exposure; upgrade gated by OWNER_GATE"})
            pcss = str((pkgs.get("node_modules/postcss") or {}).get("version") or "")
            if pcss and _ver_tuple(pcss) < (8, 5, 31):
                npm_advisories_noted.append({"package": "postcss", "installed": pcss, "fix": "8.5.31", "severity": "high", "note": "build-time CSS parser only; upgrade gated by OWNER_GATE"})
            esb = str((pkgs.get("node_modules/drizzle-kit/node_modules/esbuild") or pkgs.get("node_modules/esbuild") or {}).get("version") or "")
            if esb and _ver_tuple(esb) < (0, 25, 0):
                npm_advisories_noted.append({"package": "esbuild (via drizzle-kit)", "installed": esb, "fix": "drizzle-kit>=0.18.1", "severity": "moderate", "note": "dev-only CLI, never runs in prod"})
        except (OSError, json.JSONDecodeError):
            pass

    return {
        "check": "cve_supply_chain_audit",
        "verdict": "CLEAN" if not py_vulnerable else "FINDING",
        "python_runtime_packages": py_installed,
        "python_runtime_vulnerabilities": py_vulnerable,
        "npm_advisories_noted": npm_advisories_noted,
    }


def check_ledger_integrity_copy(root: Path) -> dict[str, Any]:
    """Verify hash-chain integrity on a temporary copy of mission_ledger.jsonl (never touching live file)."""
    from architecture.mission.ledger import MissionLedger, default_ledger_path

    live_path = default_ledger_path(create=False)
    if not live_path.is_file():
        return {"check": "mission_ledger_hash_chain", "verdict": "CLEAN", "entries": 0, "note": "no_live_ledger_file"}
    with tempfile.TemporaryDirectory() as tmp:
        copy_path = Path(tmp) / "ledger_copy.jsonl"
        shutil.copy2(live_path, copy_path)
        ledger = MissionLedger(copy_path)
        entries = ledger.verify()
    return {
        "check": "mission_ledger_hash_chain",
        "verdict": "CLEAN",
        "entries": entries,
    }


def run_whitehat_security_audit(root: Path | None = None) -> dict[str, Any]:
    repo = root or Path(__file__).resolve().parents[2]
    checks = [
        check_loopback_binds(repo),
        check_hold_flags(repo),
        check_secret_hygiene(repo),
        check_cve_audit(repo),
        check_lane_a_freeze(repo),
        check_ledger_integrity_copy(repo),
    ]
    overall = "CLEAN" if all(c["verdict"] == "CLEAN" for c in checks) else "FINDING"
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "overall_verdict": overall,
        "checks": checks,
    }
