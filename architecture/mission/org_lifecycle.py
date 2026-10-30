"""Observable agent lifecycle and unfilled-seat census. Read-only. PAPER_ONLY."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agent_org.contracts import AgentLifecycleState
from architecture.mission.cognitive_graph_m12 import _ARTIFACTS

OUT_REL = Path("reports") / "grok" / "M12" / "org_lifecycle_snapshot.json"
REGISTRY_REL = Path("config") / "agent_registry.yaml"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_agent(agent: dict[str, Any], artifact_exists: bool) -> AgentLifecycleState:
    status = str(agent.get("status") or "")
    ops = ((agent.get("ops") or {}).get("operability") or {})
    implemented = bool(ops.get("implemented"))
    live = bool(ops.get("live"))
    if status == "MISSING" and not implemented:
        return AgentLifecycleState.DESIGNED if agent.get("evidence") else AgentLifecycleState.ABSENT
    if not artifact_exists:
        return AgentLifecycleState.DESIGNED if status in {"PLANNED", "MISSING", "PARTIAL"} else AgentLifecycleState.ABSENT
    if live and implemented:
        return AgentLifecycleState.LIVE_OBSERVED
    if status == "PARTIAL" or not live:
        return AgentLifecycleState.ARTIFACT_PRESENT
    return AgentLifecycleState.ARTIFACT_PRESENT


def build_org_lifecycle(root: Path) -> dict[str, Any]:
    root = Path(root)
    reg = yaml.safe_load((root / REGISTRY_REL).read_text(encoding="utf-8"))
    rows = []
    for agent in reg.get("agents") or []:
        aid = str(agent.get("agent_id") or "")
        rel, _kind = _ARTIFACTS.get(aid, (None, None))
        exists = bool(rel and (root / rel).is_file())
        state = classify_agent(agent, exists)
        ops = ((agent.get("ops") or {}).get("operability") or {})
        rows.append(
            {
                "agent_id": aid,
                "name": agent.get("name"),
                "registry_status": agent.get("status"),
                "lifecycle_state": state.value,
                "artifact": rel,
                "artifact_present": exists,
                "implemented": bool(ops.get("implemented")),
                "live_flag": bool(ops.get("live")),
                "seat_filled": agent.get("status") == "EXISTS" and exists and bool(ops.get("implemented")),
            }
        )
    unfilled = [r for r in rows if not r["seat_filled"]]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["lifecycle_state"]] = counts.get(row["lifecycle_state"], 0) + 1
    return {
        "schema": "ahos.org_lifecycle.v1",
        "generated_at": _utc(),
        "paper_only": True,
        "registry_agents": len(rows),
        "filled_seats": sum(1 for r in rows if r["seat_filled"]),
        "unfilled_seats": [
            {
                "agent_id": r["agent_id"],
                "name": r["name"],
                "registry_status": r["registry_status"],
                "lifecycle_state": r["lifecycle_state"],
                "why_unfilled": _why(r),
            }
            for r in unfilled
        ],
        "lifecycle_counts": counts,
        "agents": rows,
        "honesty": (
            "A seat is filled only when the registry says EXISTS, operability.implemented is true, "
            "and the wired artifact file is on disk. PLANNED and MISSING stay unfilled even if a later snapshot exists. "
            "Lifecycle states are observations, not promotions."
        ),
    }


def _why(row: dict[str, Any]) -> str:
    if row["registry_status"] in {"PLANNED", "MISSING"}:
        return f"registry status {row['registry_status']}"
    if not row["artifact_present"]:
        return "wired artifact file absent"
    if not row["implemented"]:
        return "operability.implemented is false"
    if row["registry_status"] != "EXISTS":
        return f"registry status {row['registry_status']}"
    return "not filled"


def export_org_lifecycle(root: Path) -> dict[str, Any]:
    doc = build_org_lifecycle(root)
    out = Path(root) / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
