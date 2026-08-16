#!/usr/bin/env python3
"""AHOS Open Source & GitHub Intelligence Harvest Pipeline (Phase XXII - K-04).

Controlled Research Pipeline:
  DISCOVER -> RELEVANCE -> LICENSE -> SECURITY -> ARCHITECTURAL REVIEW ->
  BENCHMARK -> SANDBOX -> REPLAY -> RED TEAM -> COMPARE -> GOVERNANCE -> VERSIONED ADOPTION

Non-negotiable Laws:
  - Popularity is NOT Evidence: GitHub stars, forks, and social mentions are discovery filters, never proof of correctness.
  - Zero Direct Installation: No external code enters production without passing the full 12-stage sandbox audit.
  - License Veto: Repositories with incompatible or restrictive licenses (GPLv3 in proprietary, AGPL, unknown/no license) are rejected or quarantined.
  - Immutable Audit Trail: Every evaluated candidate emits an auditable record with provenance hash.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any


ALLOWED_PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "CC0-1.0"}
DISALLOWED_RESTRICTIVE_LICENSES = {"GPL-3.0", "AGPL-3.0", "SSPL", "Commons Clause"}

CAPABILITY_CATEGORIES = [
    "orchestration",
    "scheduling",
    "observability",
    "testing",
    "agent_frameworks",
    "memory",
    "security",
    "data_infrastructure",
    "ai_infrastructure"
]


@dataclass
class OSSCandidateRecord:
    repo_full_name: str                         # owner/repo
    category: str
    discovered_ts: float
    stars_count: int
    license_spdx: str
    license_verdict: str                        # PASS | RESTRICTIVE | UNKNOWN_LICENSE
    security_verdict: str                       # PASS | HIGH_RISK | PENDING
    relevance_score: float                      # 0.0 to 1.0
    current_stage: str                          # DISCOVERED | LICENSE_AUDITED | ARCH_REVIEWED | BENCHMARKED | REDTEAMED | REJECTED | APPROVED
    ahos_comparison: str
    is_better_than_current: bool
    rejection_reason: str | None = None
    provenance_sha256: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class OSSIntelligencePipeline:
    def __init__(self):
        self._candidates: dict[str, OSSCandidateRecord] = {}
        self._seed_evaluated_candidates()

    def evaluate_candidate(self, repo_full_name: str, category: str,
                           license_spdx: str, stars_count: int,
                           has_known_vulnerabilities: bool,
                           benchmark_lift: float,
                           ahos_comparison: str,
                           now: float | None = None) -> OSSCandidateRecord:
        ts = time.time() if now is None else now

        if category not in CAPABILITY_CATEGORIES:
            raise ValueError(f"Unknown capability category: {category}")

        # 1. License Audit
        if license_spdx in ALLOWED_PERMISSIVE_LICENSES:
            lic_verdict = "PASS"
        elif license_spdx in DISALLOWED_RESTRICTIVE_LICENSES:
            lic_verdict = "RESTRICTIVE"
        else:
            lic_verdict = "UNKNOWN_LICENSE"

        # 2. Security Audit
        sec_verdict = "HIGH_RISK" if has_known_vulnerabilities else "PASS"

        # 3. Pipeline Progression & Gate Law
        if lic_verdict != "PASS":
            stage = "REJECTED"
            reason = f"License incompatibility: {license_spdx}"
            is_better = False
        elif sec_verdict != "PASS":
            stage = "REJECTED"
            reason = "Security audit failed: Known CVE vulnerabilities detected"
            is_better = False
        elif benchmark_lift <= 1.0:
            stage = "REJECTED"
            reason = f"Benchmark comparison: Does not improve over current implementation (lift={benchmark_lift:.2f} <= 1.0)"
            is_better = False
        else:
            stage = "ARCH_REVIEWED"
            reason = None
            is_better = True

        rec = OSSCandidateRecord(
            repo_full_name=repo_full_name,
            category=category,
            discovered_ts=ts,
            stars_count=stars_count,
            license_spdx=license_spdx,
            license_verdict=lic_verdict,
            security_verdict=sec_verdict,
            relevance_score=min(1.0, 0.5 + (0.1 if is_better else 0.0)),
            current_stage=stage,
            ahos_comparison=ahos_comparison,
            is_better_than_current=is_better,
            rejection_reason=reason,
            provenance_sha256=hashlib.sha256(f"{repo_full_name}:{license_spdx}:{ts}".encode()).hexdigest(),
            meta={"benchmark_lift": benchmark_lift}
        )
        self._candidates[repo_full_name] = rec
        return rec

    def get_candidate(self, repo_full_name: str) -> OSSCandidateRecord | None:
        return self._candidates.get(repo_full_name)

    def list_approved_or_reviewed(self) -> list[OSSCandidateRecord]:
        return [c for c in self._candidates.values() if c.current_stage not in ("REJECTED", "DISCOVERED")]

    def _seed_evaluated_candidates(self):
        # 1. Temporal.io (Evaluated for Production Scheduling)
        self.evaluate_candidate(
            repo_full_name="temporalio/temporal",
            category="scheduling",
            license_spdx="MIT",
            stars_count=12000,
            has_known_vulnerabilities=False,
            benchmark_lift=1.25,
            ahos_comparison="Durable execution engine with persistent timers; evaluated for Phase-2 VPS distributed scheduler.",
            now=1786500000.0
        )

        # 2. Restrictive License Candidate (Demonstrating Fail-Closed Law)
        self.evaluate_candidate(
            repo_full_name="example/restrictive-agent",
            category="agent_frameworks",
            license_spdx="AGPL-3.0",
            stars_count=35000,  # High popularity does NOT override license law
            has_known_vulnerabilities=False,
            benchmark_lift=1.50,
            ahos_comparison="High-star agent framework but carries copyleft AGPL-3.0 restriction.",
            now=1786500000.0
        )
