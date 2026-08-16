#!/usr/bin/env python3
"""AHOS Controlled Self-Evolution & Improvement Proposal Engine (Phase XXII - Section 12).

Non-negotiable Laws:
  - AI may PROPOSE, but may NEVER self-approve, NEVER touch Lane A, and NEVER promote itself.
  - Stage-Skipping is Forbidden: Every proposal must pass all sequential validation gates.
  - Human Gate Mandatory: Any governance_touching proposal requires explicit human approval.
  - Rollback Plan Mandate: No proposal can advance to APPROVED without an explicit rollback plan.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from ..knowledge.contracts import VersionedClaim

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "improvement_proposal_v1.json"

VALID_STAGES = [
    "PROPOSED", "SANDBOXED", "REPLAYED", "CI_PASSED", "REDTEAMED", "COUNCIL_REVIEWED",
    "GOVERNANCE_CHECKED", "AWAITING_HUMAN", "APPROVED", "VERSION_BUMPED", "DEPLOYED",
    "MONITORING", "ROLLED_BACK", "REJECTED"
]


@dataclass
class ImprovementProposal:
    proposal_id: str
    created_ts: float
    detected_by: str                             # Agent ID or human
    diagnosis: str
    proposed_by: str                             # Agent ID | Human (AI proposals tagged is_ai=true)
    is_ai: bool
    target_scope: str                            # B_ONLY | SHARED_INFRA | LANE_A_FORBIDDEN
    governance_touching: bool
    requires_human: bool
    candidate_diff_ref: str
    replay_evidence: list[str]
    test_battery: list[str]
    redteam_verdict: str                         # ACCEPT | REJECT | INSUFFICIENT_EVIDENCE | NEEDS_MORE_DATA
    council_review: str                          # council report id or NONE
    research_basis: list[str] = field(default_factory=list) # K-02 claim IDs / Paper DOIs
    approvals: list[dict[str, Any]] = field(default_factory=list) # [{approver, is_human, ts}]
    rollback_plan: dict[str, str] = field(default_factory=dict)
    version_bump: str | None = None
    current_stage: str = "PROPOSED"
    provenance_sha256: str = ""


class SelfEvolutionEngine:
    def __init__(self, contract_path: Path | str = CONTRACT_PATH):
        self.contract = json.loads(Path(contract_path).read_text(encoding='utf-8')) if Path(contract_path).exists() else {}

    def create_proposal(self, *, detected_by: str, diagnosis: str,
                        proposed_by: str, is_ai: bool,
                        target_scope: str, governance_touching: bool,
                        candidate_diff_ref: str, test_battery: list[str],
                        rollback_plan: dict[str, str],
                        research_basis: list[str] | None = None,
                        now: float | None = None) -> ImprovementProposal:
        ts = time.time() if now is None else now
        pid = f"prop_{int(ts)}_{hashlib.sha256(diagnosis.encode()).hexdigest()[:8]}"

        # Hard Rule 1: target_scope=LANE_A_FORBIDDEN => immediate REJECT
        if target_scope == "LANE_A_FORBIDDEN":
            stage = "REJECTED"
        else:
            stage = "PROPOSED"

        # Governance touching always forces human requirement
        requires_human = True if (governance_touching or is_ai) else False

        prop = ImprovementProposal(
            proposal_id=pid,
            created_ts=ts,
            detected_by=detected_by,
            diagnosis=diagnosis,
            proposed_by=proposed_by,
            is_ai=is_ai,
            target_scope=target_scope,
            governance_touching=governance_touching,
            requires_human=requires_human,
            candidate_diff_ref=candidate_diff_ref,
            replay_evidence=[],
            test_battery=test_battery,
            redteam_verdict="NEEDS_MORE_DATA",
            council_review="NONE",
            research_basis=research_basis or [],
            approvals=[],
            rollback_plan=rollback_plan,
            current_stage=stage,
            provenance_sha256=hashlib.sha256(f"{pid}:{diagnosis}:{ts}".encode()).hexdigest()
        )
        return prop

    def advance_stage(self, proposal: ImprovementProposal, next_stage: str,
                      evidence_ref: str, approver: str | None = None,
                      is_human_approver: bool = False,
                      now: float | None = None) -> tuple[bool, str]:
        """Advances proposal through sequential stages validating all invariant gates."""
        ts = time.time() if now is None else now

        if proposal.current_stage in ("REJECTED", "ROLLED_BACK", "MONITORING"):
            return False, f"Proposal is in terminal stage: {proposal.current_stage}"

        if next_stage not in VALID_STAGES:
            return False, f"Invalid target stage: {next_stage}"

        curr_idx = VALID_STAGES.index(proposal.current_stage)
        next_idx = VALID_STAGES.index(next_stage)

        # Stage jump prevention (except rejection / rollback)
        if next_stage not in ("REJECTED", "ROLLED_BACK") and next_idx != curr_idx + 1:
            return False, f"Stage jump forbidden: {proposal.current_stage} -> {next_stage}"

        # Hard Rule: AI identity may NEVER be an approver
        if next_stage == "APPROVED":
            if not is_human_approver or not approver:
                return False, "EPISTEMIC VETO: Approval requires a verified HUMAN approver."
            if approver == proposal.proposed_by:
                return False, "GOVERNANCE VETO: Proposer cannot approve their own proposal."
            if not proposal.rollback_plan or not proposal.rollback_plan.get("trigger"):
                return False, "ROLLBACK VETO: Missing explicit rollback plan and trigger."

            proposal.approvals.append({"approver": approver, "is_human": True, "ts": ts})

        proposal.current_stage = next_stage
        return True, f"Successfully advanced to {next_stage}"
