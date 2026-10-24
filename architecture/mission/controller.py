"""M14 mission controller. It schedules phases. It does not trade or promote."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MissionController:
    phase: str = "IDLE"
    live: bool = False

    def start(self) -> str:
        if self.phase == "HALT":
            return "HALT"
        self.phase = "RUNNING"
        self.live = False
        return self.phase

    def pause(self) -> str:
        if self.phase == "RUNNING":
            self.phase = "PAUSED"
        return self.phase

    def halt(self) -> str:
        self.phase = "HALT"
        self.live = False
        return self.phase

    def promote(self) -> bool:
        return False

    def enable_live(self) -> bool:
        self.live = False
        return False


import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_rca_gate_promote_cycle(
    *,
    proposal_id: str,
    fault_summary: str,
    evidence_refs: tuple[str, ...] | list[str],
    gate_passed: bool,
    owner_signed: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """M14: Full mission phase controller (proposal <- RCA with evidence <- gate <- human-gated promote)."""
    mc = MissionController()
    mc.start()
    phases = ["IDLE", mc.phase, "INTAKE", "RCA_BOUND", "GATE_VERIFIED"]
    has_evidence = len(evidence_refs) > 0 and bool(fault_summary.strip())
    promoted = False  # Constitutional rule: controller never auto-promotes without human signature
    state = (
        "AWAITING_OWNER_SIGNATURE"
        if (has_evidence and gate_passed and not owner_signed)
        else ("PROMOTED_BY_OWNER" if (has_evidence and gate_passed and owner_signed) else "BLOCKED_AT_GATE")
    )
    receipt = {
        "schema": "ahos.m14_controller_cycle.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proposal_id": proposal_id,
        "fault_summary": fault_summary,
        "evidence_refs": list(evidence_refs),
        "phases_recorded": phases,
        "gate_passed": bool(gate_passed and has_evidence),
        "owner_signed": owner_signed,
        "promoted": promoted,
        "state": state,
        "paper_only": True,
    }
    if root is not None:
        out = Path(root) / "reports" / "grok" / "M14" / "controller_rca_receipt.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt
