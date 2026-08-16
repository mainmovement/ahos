#!/usr/bin/env python3
"""Tests for AHOS Update Governance & Version Manager."""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from engine.update_manager import AHOSUpdateManager, UpdatePlan


def test_update_manager_check_only_mode():
    manager = AHOSUpdateManager()
    plan = manager.check_updates()
    assert plan.mode == "CHECK_ONLY"
    assert plan.requires_human_approval is True
    assert len(plan.proposed_actions) >= 1


def test_update_manager_apply_without_confirmation_rejected():
    manager = AHOSUpdateManager()
    plan = manager.check_updates()
    ok, msg = manager.apply_update(plan, approver="lead_human", confirmed=False)
    assert ok is False
    assert "Human approver name and explicit --confirm" in msg


def test_update_manager_apply_with_confirmation_approved():
    manager = AHOSUpdateManager()
    plan = manager.check_updates()
    # Force governance_touching = False for benign plan
    plan.governance_touching = False
    ok, msg = manager.apply_update(plan, approver="lead_architect_human", confirmed=True)
    assert ok is True
    assert plan.human_approved is True
    assert plan.approved_by == "lead_architect_human"
