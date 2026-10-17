"""M48 update proposal. A bad hash, a CVE, or a missing rollback is refused.

This module does not edit a lockfile and does not install a package.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateProposal:
    accepted: bool
    reason: str
    lockfile_changed: bool


def propose(*, expected_hash: str, actual_hash: str, cve: bool, rollback: str) -> UpdateProposal:
    if cve:
        return UpdateProposal(False, "known cve", False)
    if expected_hash != actual_hash or not actual_hash:
        return UpdateProposal(False, "hash mismatch", False)
    if not rollback.strip():
        return UpdateProposal(False, "rollback required", False)
    return UpdateProposal(True, "proposal only", False)
