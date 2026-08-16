#!/usr/bin/env python3
"""Tests for K-04 Open-Source & GitHub Intelligence Pipeline (Phase XXII)."""
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.knowledge.oss_pipeline import (
    OSSIntelligencePipeline, OSSCandidateRecord, CAPABILITY_CATEGORIES
)


def test_oss_pipeline_permissive_license_and_lift():
    pipeline = OSSIntelligencePipeline()
    rec = pipeline.evaluate_candidate(
        repo_full_name="pytest-dev/pytest",
        category="testing",
        license_spdx="MIT",
        stars_count=11000,
        has_known_vulnerabilities=False,
        benchmark_lift=1.35,
        ahos_comparison="Robust automated test runner."
    )
    assert rec.license_verdict == "PASS"
    assert rec.security_verdict == "PASS"
    assert rec.is_better_than_current is True
    assert rec.current_stage == "ARCH_REVIEWED"
    assert rec.rejection_reason is None


def test_oss_pipeline_restrictive_license_reject():
    pipeline = OSSIntelligencePipeline()
    rec = pipeline.evaluate_candidate(
        repo_full_name="gpl-tool/restricted",
        category="orchestration",
        license_spdx="GPL-3.0",
        stars_count=50000,  # High stars do NOT override license veto
        has_known_vulnerabilities=False,
        benchmark_lift=2.0,
        ahos_comparison="High performance but carries copyleft restriction."
    )
    assert rec.license_verdict == "RESTRICTIVE"
    assert rec.current_stage == "REJECTED"
    assert "License incompatibility" in rec.rejection_reason


def test_oss_pipeline_security_vulnerability_reject():
    pipeline = OSSIntelligencePipeline()
    rec = pipeline.evaluate_candidate(
        repo_full_name="vuln-lib/unsafe",
        category="security",
        license_spdx="Apache-2.0",
        stars_count=5000,
        has_known_vulnerabilities=True,  # Critical CVE detected
        benchmark_lift=1.5,
        ahos_comparison="Useful utility but has active remote execution CVE."
    )
    assert rec.security_verdict == "HIGH_RISK"
    assert rec.current_stage == "REJECTED"
    assert "Security audit failed" in rec.rejection_reason


def test_oss_pipeline_no_benchmark_lift_reject():
    pipeline = OSSIntelligencePipeline()
    rec = pipeline.evaluate_candidate(
        repo_full_name="mediocre/db",
        category="data_infrastructure",
        license_spdx="MIT",
        stars_count=8000,
        has_known_vulnerabilities=False,
        benchmark_lift=0.90,  # Slower than current SQLite
        ahos_comparison="Alternative storage with higher query latency."
    )
    assert rec.current_stage == "REJECTED"
    assert "Does not improve over current" in rec.rejection_reason


def test_oss_pipeline_unknown_category_raises():
    pipeline = OSSIntelligencePipeline()
    with pytest.raises(ValueError):
        pipeline.evaluate_candidate(
            repo_full_name="random/x",
            category="INVALID_CATEGORY",
            license_spdx="MIT",
            stars_count=10,
            has_known_vulnerabilities=False,
            benchmark_lift=1.0,
            ahos_comparison="x"
        )
