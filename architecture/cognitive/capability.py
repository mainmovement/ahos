"""Capability-gap register for AGI/ACI evolution (Lane B, file-backed).

Operational AHOS_GAP_REGISTER.md is not rewritten here. These IDs live
in reports/agi_aci_evolution/GAP_REGISTER.md and optional JSONL.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CapabilityGap:
    gap_id: str
    description: str
    impact: str
    dependency: str
    priority: str
    evidence: str
    proposed_solution: str
    implementation_status: str
    validation_status: str
    closed: bool = False
    closed_evidence: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "description": self.description,
            "impact": self.impact,
            "dependency": self.dependency,
            "priority": self.priority,
            "evidence": self.evidence,
            "proposed_solution": self.proposed_solution,
            "implementation_status": self.implementation_status,
            "validation_status": self.validation_status,
            "closed": self.closed,
            "closed_evidence": self.closed_evidence,
        }


class CapabilityRegister:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, gap: CapabilityGap) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(gap.as_dict(), sort_keys=True) + "\n")

    def all(self) -> list[CapabilityGap]:
        rows: list[CapabilityGap] = []
        if not self.path.exists() or self.path.stat().st_size == 0:
            return rows
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            rows.append(
                CapabilityGap(
                    gap_id=str(raw["gap_id"]),
                    description=str(raw["description"]),
                    impact=str(raw.get("impact") or ""),
                    dependency=str(raw.get("dependency") or ""),
                    priority=str(raw.get("priority") or ""),
                    evidence=str(raw.get("evidence") or ""),
                    proposed_solution=str(raw.get("proposed_solution") or ""),
                    implementation_status=str(raw.get("implementation_status") or ""),
                    validation_status=str(raw.get("validation_status") or ""),
                    closed=bool(raw.get("closed")),
                    closed_evidence=str(raw.get("closed_evidence") or ""),
                )
            )
        return rows

    def close(self, gap_id: str, *, evidence: str) -> CapabilityGap:
        if not str(evidence).strip():
            raise ValueError("Cannot close a gap without evidence")
        found = False
        updated: list[CapabilityGap] = []
        for g in self.all():
            if g.gap_id == gap_id:
                found = True
                g.closed = True
                g.closed_evidence = evidence.strip()
                g.validation_status = "CLOSED_WITH_EVIDENCE"
            updated.append(g)
        if not found:
            raise KeyError(gap_id)
        self.path.write_text(
            "".join(json.dumps(g.as_dict(), sort_keys=True) + "\n" for g in updated),
            encoding="utf-8",
        )
        closed = next(g for g in updated if g.gap_id == gap_id)
        return closed

    def seed_baseline(self) -> int:
        """Append BASELINE_GAPS that are not already present. Never closes gaps."""
        existing = {g.gap_id for g in self.all()}
        added = 0
        for gap in BASELINE_GAPS:
            if gap.gap_id not in existing:
                self.append(gap)
                added += 1
        return added


BASELINE_GAPS: tuple[CapabilityGap, ...] = (
    CapabilityGap(
        gap_id="ACI-GAP-001",
        description="No unified provenance-bearing memory (working/episodic/semantic/procedural).",
        impact="Cannot retrieve, contradict, or decay beliefs as a cognitive system.",
        dependency="P2 Memory architecture",
        priority="P2",
        evidence="architecture/ has no MemoryStore; knowledge/VersionedClaimStore is claims-only.",
        proposed_solution="Design typed memory stores with provenance; do not dump unstructured logs.",
        implementation_status="OPEN",
        validation_status="UNVALIDATED",
    ),
    CapabilityGap(
        gap_id="ACI-GAP-002",
        description="No general causal world model; financial hindsight is not a causal engine.",
        impact="Cannot represent multi-domain alternative scenarios without overwriting observed outcomes.",
        dependency="P5 World Model",
        priority="P5",
        evidence="architecture/cognitive/world_model.py; architecture/evolution/hindsight.py (PARTIAL, trading-domain)",
        proposed_solution="Add isolated counterfactual records that never mutate observation tables.",
        implementation_status="OPEN",
        validation_status="UNVALIDATED",
    ),
    CapabilityGap(
        gap_id="ACI-GAP-003",
        description="Council members are not memory-bearing independent agents.",
        impact="No measurable agent reliability, error history, or tool use.",
        dependency="P6 Cognitive Society",
        priority="P6",
        evidence="contracts/ai_council_contract_v1.json; architecture/council.py",
        proposed_solution="Agent passports + later sandbox agent creation with human promotion.",
        implementation_status="PARTIAL",
        validation_status="PASSPORTS_ONLY",
    ),
    CapabilityGap(
        gap_id="ACI-GAP-004",
        description="Autonomous evolution remains doctrine-OFF; human gate required.",
        impact="Self-improvement cannot mean self-modification of production/Lane A.",
        dependency="P8 Controlled Evolution",
        priority="P8",
        evidence="docs/canonical/PROJECT_STATE.md Evolution A (OFF); architecture/evolution/engine.py",
        proposed_solution="Keep proposal ledger; never auto-promote; never modify Lane A from evolution.",
        implementation_status="PARTIAL",
        validation_status="HUMAN_GATE_REQUIRED",
    ),
    CapabilityGap(
        gap_id="ACI-GAP-005",
        description="M-GAP-003 ≥7-day soak is not closed by a 72-hour soak.",
        impact="Reliability questions remain after T+72h.",
        dependency="Operational soak / AHOS_GAP_REGISTER.md",
        priority="P0",
        evidence="AHOS_GAP_REGISTER.md M-GAP-003; owner soak T0 2026-09-10",
        proposed_solution="Post-soak proposal only; do not auto-calibrate or silently close M-GAP-003.",
        implementation_status="OPEN",
        validation_status="SOAK_IN_PROGRESS",
    ),
)
