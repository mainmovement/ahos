"""Cognitive-agent *passports* from the real agent registry.

Council members in `contracts/ai_council_contract_v1.json` are protocol
fields, not a member roster. Executable "lenses" live in
`architecture/knowledge/panel.py`. Registry rows live in
`config/agent_registry.yaml`. None of these are memory-bearing independent
agents. Majority vote is not a decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from architecture.cognitive.contracts import CapabilityAssessment, CapabilityStatus
from architecture.council import CONTRACT_PATH, load_contract
from architecture.knowledge.panel import PANEL_LENSES

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "config" / "agent_registry.yaml"


@dataclass(frozen=True)
class AgentPassport:
    """Metadata for one registered agent or lens. Memory/tools are not implied."""

    agent_id: str
    display_name: str
    role: str
    domain: str
    required_outputs: tuple[str, ...]
    memory_bearing: bool
    independent_tools: bool
    performance_tracked: bool
    source: str
    status: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "role": self.role,
            "domain": self.domain,
            "required_outputs": list(self.required_outputs),
            "memory_bearing": self.memory_bearing,
            "independent_tools": self.independent_tools,
            "performance_tracked": self.performance_tracked,
            "source": self.source,
            "status": self.status,
        }


def load_council_passports(
    registry_path: Path | None = None,
    *,
    include_lenses: bool = True,
) -> tuple[AgentPassport, ...]:
    path = registry_path or DEFAULT_REGISTRY
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    agents = payload.get("agents") or []
    out: list[AgentPassport] = []
    for raw in agents:
        if not isinstance(raw, dict):
            continue
        aid = str(raw.get("agent_id") or "").strip()
        if not aid:
            continue
        caps = raw.get("capabilities") or []
        out.append(
            AgentPassport(
                agent_id=aid,
                display_name=str(raw.get("name") or aid),
                role=str(raw.get("form") or ""),
                domain=str(raw.get("lane") or ""),
                required_outputs=tuple(str(x) for x in caps),
                memory_bearing=False,
                independent_tools=False,
                performance_tracked=False,
                source=str(path.as_posix()),
                status=str(raw.get("status") or ""),
            )
        )
    if include_lenses:
        for lens_id, _fn in PANEL_LENSES:
            out.append(
                AgentPassport(
                    agent_id=str(lens_id),
                    display_name=str(lens_id),
                    role="deterministic_lens",
                    domain="COGNITIVE_CORE",
                    required_outputs=("opinion",),
                    memory_bearing=False,
                    independent_tools=False,
                    performance_tracked=False,
                    source="architecture/knowledge/panel.py",
                    status="EXISTS",
                )
            )
    # Prove the council contract is loadable; it has no members[] roster.
    load_contract(CONTRACT_PATH)
    return tuple(out)


def council_capability_claim() -> CapabilityAssessment:
    return CapabilityAssessment(
        capability="cognitive_society",
        status=CapabilityStatus.PARTIAL,
        evidence=(
            "config/agent_registry.yaml",
            "contracts/ai_council_contract_v1.json",
            "architecture/council.py (advisory_only, no majority vote)",
            "architecture/knowledge/panel.py (deterministic lenses)",
            "architecture/cognitive/agents.py (passports; memory_bearing=false)",
        ),
        architecture_target=(
            "Identity, specialization, memory, tools, prediction/error history, "
            "calibration, measurable disagreement, meta-cognitive arbitration."
        ),
        gap=(
            "Registry rows and panel lenses are not independent memory-bearing "
            "tool-using agents. Cursor skills are developer instructions, not runtime agents."
        ),
    )
