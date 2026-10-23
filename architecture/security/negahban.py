"""M64 & M80 Part B (Negahban) defensive scan & white-hat security audit.
A secret-shaped string halts the action. Nothing is exploited.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET = re.compile(r"\bsk-[A-Za-z0-9]{8,}\b|BEGIN [A-Z ]*PRIVATE KEY")


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
    """Verify HOLD.flag is present in canonical directories."""
    candidates = [
        root / "HOLD.flag",
        root.parent / "ahos_arena" / "HOLD.flag",
    ]
    present = [str(p.name) for p in candidates if p.is_file()]
    missing = [str(p) for p in candidates if not p.is_file()]
    return {
        "check": "hold_flag_presence",
        "verdict": "CLEAN" if not missing else "FINDING",
        "present_count": len(present),
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
    """Run Negahban secret scan across config/ and architecture/."""
    findings = 0
    files_scanned = 0
    for sub in ("config", "architecture"):
        base = root / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in {".py", ".yaml", ".json"}:
                continue
            files_scanned += 1
            res = scan(p.read_text(encoding="utf-8", errors="ignore"))
            findings += res.findings
    return {
        "check": "secret_hygiene_scan",
        "verdict": "CLEAN" if findings == 0 else "HALT",
        "files_scanned": files_scanned,
        "findings": findings,
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
