#!/usr/bin/env python3
"""Tests for AHOS Logical AI Assistant Roles & Task Contracts."""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.knowledge.assistants import load_assistant_roles, get_assistant


def test_ai_assistants_loads_9_roles():
    roles = load_assistant_roles()
    assert len(roles) == 9
    expected = ["architect", "researcher", "auditor", "developer", "data_scientist", "risk_manager", "historian", "documentation_manager", "guardian"]
    for r in expected:
        assert r in roles, f"Role {r} missing from config"


def test_ai_assistants_guardian_authority_and_vetoes():
    guardian = get_assistant("guardian")
    assert guardian is not None
    assert guardian["authority"] == "FINAL_HUMAN_APPROVAL"
    assert "delegate_to_ai" in guardian["prohibited_actions"]

    risk_mgr = get_assistant("risk_manager")
    assert risk_mgr is not None
    assert risk_mgr["authority"] == "VETO_ONLY"
    assert "permit_unverified_contracts" in risk_mgr["prohibited_actions"]
