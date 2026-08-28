#!/usr/bin/env python3
"""Tests for Controlled Self-Evolution & Improvement Proposal Engine (Phase XXII)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.evolution.engine import SelfEvolutionEngine, ImprovementProposal


def test_proposal_lane_a_forbidden_immediate_reject():
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="AG-14",
        diagnosis="Attempting to rewrite Lane A E-01 baseline definitions",
        proposed_by="AG-20",
        is_ai=True,
        target_scope="LANE_A_FORBIDDEN",
        governance_touching=True,
        candidate_diff_ref="diff_01",
        test_battery=["test_01"],
        rollback_plan={"trigger": "coverage_drop", "action": "revert"}
    )
    assert prop.current_stage == "REJECTED"


def test_proposal_requires_human_approval_cannot_be_approved_by_ai(monkeypatch):
    monkeypatch.setenv("AHOS_HUMAN_APPROVER_IDS", "lead_architect_human")
    monkeypatch.delenv("AHOS_ALLOW_UNBOUND_HUMAN_APPROVAL", raising=False)
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="human_lead",
        diagnosis="Optimize Redis cache layer for Lane B",
        proposed_by="AG-20",
        is_ai=True,
        target_scope="B_ONLY",
        governance_touching=False,
        candidate_diff_ref="diff_02",
        test_battery=["test_02"],
        rollback_plan={"trigger": "latency_increase", "action": "disable_cache"}
    )
    assert prop.current_stage == "PROPOSED"

    # Advance step-by-step through required stages
    for stg in ["SANDBOXED", "REPLAYED", "CI_PASSED", "REDTEAMED", "COUNCIL_REVIEWED", "GOVERNANCE_CHECKED", "AWAITING_HUMAN"]:
        ok, msg = engine.advance_stage(prop, stg, evidence_ref="ev_ref")
        assert ok is True, f"Failed at {stg}: {msg}"

    # AI attempting to approve its own proposal -> REJECTED by Epistemic Veto
    ok_ai_approve, err_msg = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev_ai", approver="AI_AGENT_20", is_human_approver=False
    )
    assert ok_ai_approve is False
    assert "HUMAN approver" in err_msg

    # Proposer approving their own proposal -> REJECTED by Governance Veto
    ok_self_approve, err_msg2 = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev_human", approver="AG-20", is_human_approver=True
    )
    assert ok_self_approve is False
    assert "Proposer cannot approve" in err_msg2 or "AI/agent pattern" in err_msg2

    # Spoofed human boolean with AI-shaped identity -> veto
    ok_spoof, err_spoof = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev_spoof", approver="AI_AGENT_X", is_human_approver=True
    )
    assert ok_spoof is False
    assert "AI/agent pattern" in err_spoof or "allowlist" in err_spoof

    # Non-allowlisted "human" -> veto
    ok_outside, err_out = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev_out", approver="random_person", is_human_approver=True
    )
    assert ok_outside is False
    assert "allowlist" in err_out

    # Legitimate independent human approval -> APPROVED
    ok_human, msg_ok = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev_human_lead", approver="lead_architect_human", is_human_approver=True
    )
    assert ok_human is True
    assert prop.current_stage == "APPROVED"


def test_unbound_human_approval_refused_without_allowlist(monkeypatch):
    monkeypatch.delenv("AHOS_HUMAN_APPROVER_IDS", raising=False)
    monkeypatch.delenv("AHOS_ALLOW_UNBOUND_HUMAN_APPROVAL", raising=False)
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="human_lead",
        diagnosis="Add telemetry probe",
        proposed_by="lead_human",
        is_ai=False,
        target_scope="B_ONLY",
        governance_touching=False,
        candidate_diff_ref="diff_03",
        test_battery=["test_03"],
        rollback_plan={"trigger": "error", "action": "revert"}
    )
    for stg in ["SANDBOXED", "REPLAYED", "CI_PASSED", "REDTEAMED", "COUNCIL_REVIEWED", "GOVERNANCE_CHECKED", "AWAITING_HUMAN"]:
        ok, msg = engine.advance_stage(prop, stg, evidence_ref="ev_ref")
        assert ok is True, msg
    ok, err = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev", approver="lead_architect_human", is_human_approver=True
    )
    assert ok is False
    assert "AHOS_HUMAN_APPROVER_IDS unset" in err


def test_proposal_stage_jump_forbidden():
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="human_lead",
        diagnosis="Add telemetry probe",
        proposed_by="lead_human",
        is_ai=False,
        target_scope="B_ONLY",
        governance_touching=False,
        candidate_diff_ref="diff_03",
        test_battery=["test_03"],
        rollback_plan={"trigger": "error", "action": "revert"}
    )
    # Attempting to jump directly from PROPOSED to APPROVED without sandboxing/testing
    ok, err_msg = engine.advance_stage(prop, "APPROVED", evidence_ref="fake", approver="lead", is_human_approver=True)
    assert ok is False
    assert "Stage jump forbidden" in err_msg
