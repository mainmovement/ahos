#!/usr/bin/env python3
"""GM-03 static pins: dashboard health must not hard-code green.

Complements ``npm run test:dashboard-truth`` (behaviour). Self-tests, not
independent verification.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (ROOT / "snapshot.ts").read_text(encoding="utf-8")
CC = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
TRUTH = (ROOT / "dashboard_truth.ts").read_text(encoding="utf-8")


def test_policy_dims_are_not_hard_coded_ok():
    # The two dims that used to be dim("...", "OK", ...) literals.
    assert not re.search(r'dim\(\s*"پورتفوی کاغذی",\s*"OK"', SNAPSHOT)
    assert not re.search(r'dim\(\s*"صفرپولی",\s*"OK"', SNAPSHOT)
    assert "executionModeStatus(state.executionMode)" in SNAPSHOT
    assert "paperPortfolioStatus(state.executionMode" in SNAPSHOT


def test_no_health_dim_uses_a_literal_ok_status():
    assert not re.search(r'dim\(\s*"[^"]+",\s*"OK"\s*,', SNAPSHOT)


def test_freshness_applied_to_evidence_dims():
    assert "freshnessStatus(cycle?.finishedAt" in SNAPSHOT
    assert "lastCycleStatusHealth(state.lastCycleStatus, state.lastCycleAt" in SNAPSHOT


def test_command_center_downgrades_green_when_stale():
    assert "deriveViewTruth(" in CC
    assert "presentStatus(d.status, viewStale)" in CC
    assert "presentRunning(running, viewStale)" in CC
    assert "<StatusPill status={d.status} />" not in CC


def test_truth_module_is_pure_and_non_authoritative():
    assert not re.search(r"^\s*import\s", TRUTH, re.M)
    for forbidden in ("fetch(", "BUY", "PAPER_CANDIDATE", "WATCH", "process.env"):
        assert forbidden not in TRUTH, forbidden
