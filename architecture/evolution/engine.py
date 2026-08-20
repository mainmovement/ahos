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
    # Mission §4C structured analysis: every proposal must carry problem /
    # evidence / subsystem / expected benefit / risk / affected contracts /
    # benchmark baseline / proposed change / validation method / rollback
    # strategy / governance state. Optional at creation, REQUIRED by the CLI
    # (scripts/propose_improvement.py) — a proposal without these cannot be
    # meaningfully reviewed.
    analysis: dict[str, Any] = field(default_factory=dict)
    # W36 phase 5: classification + evidence links.
    classification: str = "ARCHITECTURE"
    evidence_links: dict[str, str] = field(default_factory=dict)   # health snapshot / diagnostic / benchmark refs

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SelfEvolutionEngine:
    def __init__(self, contract_path: Path | str = CONTRACT_PATH):
        self.contract = json.loads(Path(contract_path).read_text(encoding='utf-8')) if Path(contract_path).exists() else {}

    def create_proposal(self, *, detected_by: str, diagnosis: str,
                        proposed_by: str, is_ai: bool,
                        target_scope: str, governance_touching: bool,
                        candidate_diff_ref: str, test_battery: list[str],
                        rollback_plan: dict[str, str],
                        research_basis: list[str] | None = None,
                        analysis: dict[str, Any] | None = None,
                        classification: str = "ARCHITECTURE",
                        evidence_links: dict[str, str] | None = None,
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
            provenance_sha256=hashlib.sha256(f"{pid}:{diagnosis}:{ts}".encode()).hexdigest(),
            analysis=analysis or {},
            classification=self._validate_classification(classification),
            evidence_links=evidence_links or {},
        )
        return prop

    @staticmethod
    def _validate_classification(value: str) -> str:
        """Proposal classification (W36 phase 5). Unknown values are rejected
        loudly so a mislabelled proposal cannot slip into review."""
        allowed = {
            "PERFORMANCE", "CORRECTNESS", "DATA_QUALITY", "INTELLIGENCE",
            "LEARNING", "ARCHITECTURE", "RELIABILITY", "DOCUMENTATION",
            "SECURITY",
        }
        v = str(value).strip().upper()
        if v not in allowed:
            raise ValueError(
                f"unknown proposal classification {value!r}; "
                f"valid: {sorted(allowed)}")
        return v

    # ------------------------------------------------------------ quality --

    #: Contract-required analysis fields (mission 4C / W36 CLI enforcement).
    REQUIRED_ANALYSIS_FIELDS: tuple[str, ...] = (
        "problem", "evidence", "subsystem", "expected_benefit", "risk",
        "affected_contracts", "benchmark_baseline", "proposed_change",
        "validation_method",
    )

    def validate_proposal(self, proposal: ImprovementProposal) -> dict[str, Any]:
        """Deterministic proposal-quality report for the human gate (W38 E).

        Checks, in order:
          1. contract-required top-level fields are present and non-empty;
          2. the mission-4C analysis surface is complete;
          3. rollback plan has a trigger and an action;
          4. is_ai=True and governance_touching=True both force requires_human;
          5. target_scope / classification are in the allowed sets;
          6. a PERFORMANCE classification requires a benchmark evidence link
             (a performance claim without benchmark evidence is invalid).

        Returns PASS / INCOMPLETE with an explicit missing-fields list and
        contract violations — never a numeric "quality score" (a proposal is
        either complete enough to review or not).
        """
        missing: list[str] = []
        violations: list[str] = []

        # 1. top-level contract fields (must be present and non-empty)
        for field, value in (
            ("diagnosis", proposal.diagnosis),
            ("detected_by", proposal.detected_by),
            ("proposed_by", proposal.proposed_by),
            ("target_scope", proposal.target_scope),
            ("candidate_diff_ref", proposal.candidate_diff_ref),
        ):
            if not str(value or "").strip():
                missing.append(f"top-level.{field}")

        # 2. analysis surface
        for field in self.REQUIRED_ANALYSIS_FIELDS:
            if not str((proposal.analysis or {}).get(field) or "").strip():
                missing.append(f"analysis.{field}")

        # 3. rollback plan
        rp = proposal.rollback_plan or {}
        if not str(rp.get("trigger") or "").strip():
            missing.append("rollback_plan.trigger")
        if not str(rp.get("action") or "").strip():
            missing.append("rollback_plan.action")

        # 4. governance invariants
        if proposal.is_ai and not proposal.requires_human:
            violations.append("is_ai=True must set requires_human=True")
        if proposal.governance_touching and not proposal.requires_human:
            violations.append("governance_touching=True must set requires_human=True")

        # 5. enum membership
        if proposal.target_scope not in ("B_ONLY", "SHARED_INFRA", "LANE_A_FORBIDDEN"):
            violations.append(f"invalid target_scope {proposal.target_scope!r}")
        try:
            self._validate_classification(proposal.classification)
        except ValueError as e:
            violations.append(str(e))

        # 6. PERFORMANCE classification needs benchmark evidence
        if proposal.classification == "PERFORMANCE":
            links = proposal.evidence_links or {}
            if not links.get("benchmark"):
                missing.append("evidence_links.benchmark (required for "
                               "PERFORMANCE classification)")

        verdict = "PASS" if not missing and not violations else "INCOMPLETE"
        return {
            "proposal_id": proposal.proposal_id,
            "verdict": verdict,
            "missing_fields": missing,
            "contract_violations": violations,
            "note": ("proposal-quality is binary (complete enough to review "
                     "or not); it never approves anything — the human gate "
                     "remains mandatory"),
        }

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

    # ------------------------------------------------------------ persistence

    @staticmethod
    def default_proposals_dir(root: Path | str | None = None) -> Path:
        """Canonical proposals directory (committed governance artifacts)."""
        base = Path(root) if root else Path(__file__).resolve().parents[2]
        return base / "proposals"

    def save_proposal(self, proposal: ImprovementProposal,
                      proposals_dir: Path | str | None = None) -> Path:
        """Persist a proposal as a committed JSON artifact + append an
        integrity line to proposals/ledger.jsonl.

        The ledger line carries the artifact sha256 so tampering after the
        fact is detectable (append-only discipline, mirroring the F1-S1
        history tables' intent).
        """
        out_dir = Path(proposals_dir) if proposals_dir else self.default_proposals_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        payload = proposal.to_dict()
        payload["sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        path = out_dir / f"{proposal.proposal_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

        ledger = out_dir / "ledger.jsonl"
        ledger_entry = json.dumps({
            "proposal_id": proposal.proposal_id,
            "created_ts": proposal.created_ts,
            "current_stage": proposal.current_stage,
            "sha256": payload["sha256"],
            "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, sort_keys=True)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(ledger_entry + "\n")
        return path

    def load_proposal(self, proposal_id: str,
                      proposals_dir: Path | str | None = None) -> ImprovementProposal:
        """Load a persisted proposal back into the engine (for stage
        advancement). Raises FileNotFoundError when absent."""
        out_dir = Path(proposals_dir) if proposals_dir else self.default_proposals_dir()
        path = out_dir / f"{proposal_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.pop("sha256", None)
        return ImprovementProposal(**payload)

    def list_proposals(self, proposals_dir: Path | str | None = None) -> list[dict[str, Any]]:
        """Summaries of all persisted proposals (id, stage, created_ts)."""
        out_dir = Path(proposals_dir) if proposals_dir else self.default_proposals_dir()
        if not out_dir.is_dir():
            return []
        summaries = []
        for path in sorted(out_dir.glob("prop_*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            summaries.append({
                "proposal_id": data.get("proposal_id"),
                "current_stage": data.get("current_stage"),
                "created_ts": data.get("created_ts"),
                "diagnosis": (data.get("diagnosis") or "")[:120],
                "sha256": data.get("sha256"),
            })
        return summaries
