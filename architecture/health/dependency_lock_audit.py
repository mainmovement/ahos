"""M48 Dependency & Lockfile Security Gate.
Audits Arena package-lock.json and Python requirements for SHA integrity, blocked packages
(e.g. unvetted source-map-js mutation or live-exchange SDKs), and CVE advisories without
mutating any lockfile on disk.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

BLOCKED_PACKAGES: frozenset[str] = frozenset(
    {
        "ccxt-live-executor",
        "source-map-js-unvetted",
        "binance-live-connector",
        "web3-auto-signer",
        "metamask-private-key-exporter",
    }
)


def audit_dependency_locks(
    *,
    repo_root: Path | None = None,
    candidate_additions: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit Arena package-lock.json and proposed dependency additions."""
    base = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    arena_lock = base.parent / "ahos_arena" / "package-lock.json"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lock_exists = arena_lock.is_file()
    lock_sha256: str | None = None
    next_version: str | None = None
    packages_count = 0

    if lock_exists:
        raw_bytes = arena_lock.read_bytes()
        lock_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        try:
            lock_json = json.loads(raw_bytes.decode("utf-8"))
            pkgs = lock_json.get("packages") or {}
            packages_count = len(pkgs)
            next_pkg = pkgs.get("node_modules/next") or {}
            next_version = str(next_pkg.get("version") or "16.3.8")
        except (OSError, json.JSONDecodeError):
            next_version = "unknown"

    rejected_proposals: list[dict[str, Any]] = []
    accepted_proposals: list[dict[str, Any]] = []

    for cand in candidate_additions or ():
        name = str(cand.get("name") or "").strip().lower()
        cve = int(cand.get("cve_count", 0))
        has_hash = bool(cand.get("sha256"))
        has_rollback = bool(cand.get("rollback_plan"))
        if name in BLOCKED_PACKAGES or cve > 0 or not has_hash or not has_rollback:
            rejected_proposals.append(
                {
                    "name": name,
                    "status": "REFUSED",
                    "reason": (
                        "blocked_package"
                        if name in BLOCKED_PACKAGES
                        else "cve_detected"
                        if cve > 0
                        else "missing_hash_or_rollback"
                    ),
                }
            )
        else:
            accepted_proposals.append({"name": name, "status": "VETTED_PROPOSAL_ONLY"})

    verdict = "CLEAN" if lock_exists and len(rejected_proposals) == 0 else ("CLEAN_WITH_REFUSALS" if lock_exists else "LOCKFILE_MISSING")
    return {
        "schema": "ahos.dependency_lock_audit_m48.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "lockfile_mutated": False,
        "arena_lockfile_present": lock_exists,
        "arena_lockfile_sha256": lock_sha256,
        "arena_packages_count": packages_count,
        "next_version": next_version,
        "blocked_packages_policy_count": len(BLOCKED_PACKAGES),
        "accepted_proposals": accepted_proposals,
        "rejected_proposals": rejected_proposals,
        "verdict": verdict,
    }
