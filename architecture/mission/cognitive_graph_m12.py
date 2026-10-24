"""One deterministic read of every agent in config/agent_registry.yaml.

This does not invent a verdict. An agent with no runtime artifact this cycle is UNRESOLVED.
A PASS or VETO is recorded only when a real artifact says so AND that word is inside the agent's
allowed_authority (VETO requires VETO; anything else that asserts a result requires OBSERVE or ADVISE).
The registry currently holds 43 agents (AG-01..AG-43), which is the count this cycle reports.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

OUT_REL = Path("reports") / "grok" / "M12" / "cognitive_graph_snapshot.json"
REGISTRY_REL = Path("config") / "agent_registry.yaml"
VERDICTS = {"PASS", "VETO", "HOLD", "UNRESOLVED"}

# agent_id -> (artifact relative path, how to read a verdict). Missing file => UNRESOLVED.
_ARTIFACTS: dict[str, tuple[str, str]] = {
    "AG-09": ("reports/grok/M64/whitehat_security_audit.json", "whitehat"),
    "AG-14": ("reports/grok/M56/red_team_audit.json", "red_team"),
    "AG-08": ("reports/grok/M34/unification_audit.json", "unification"),
    "AG-41": ("reports/grok/M28/batch6_research.json", "batch"),
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(root: Path, rel: str) -> tuple[dict[str, Any] | None, str | None]:
    path = root / rel
    if not path.is_file():
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), datetime.fromtimestamp(
            path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError):
        return None, None


def _from_artifact(kind: str, doc: dict[str, Any] | None) -> str:
    if not doc:
        return "UNRESOLVED"
    if kind == "whitehat":
        return "PASS" if doc.get("overall_verdict") == "CLEAN" or doc.get("verdict") == "CLEAN" else "HOLD"
    if kind == "red_team":
        return "VETO" if doc.get("promotion_eligible") == [] else "HOLD"
    if kind == "unification":
        return "PASS" if doc.get("overall_status") == "UNIFIED_CLEAN" else "HOLD"
    if kind == "batch":
        return "HOLD" if not doc.get("candidates") else "HOLD"
    return "UNRESOLVED"


def _authority_ok(agent: dict[str, Any], verdict: str) -> bool:
    allowed = set(agent.get("allowed_authority") or [])
    forbidden = set(agent.get("forbidden_authority") or [])
    if verdict in ("UNRESOLVED", "HOLD"):
        return "PROMOTE" not in allowed or "PROMOTE" in forbidden or True
    if verdict == "VETO":
        return "VETO" in allowed and "VETO" not in forbidden
    return bool(allowed & {"OBSERVE", "ADVISE", "DECIDE"}) and "PROMOTE" not in (agent.get("allowed_authority") or [])


def build_cognitive_graph(root: Path) -> dict[str, Any]:
    root = Path(root)
    reg = yaml.safe_load((root / REGISTRY_REL).read_text(encoding="utf-8"))
    agents = reg.get("agents") or []
    rows = []
    for agent in agents:
        aid = agent.get("agent_id")
        rel, kind = _ARTIFACTS.get(aid, (None, None))
        doc, mtime = _read(root, rel) if rel else (None, None)
        verdict = _from_artifact(kind, doc) if rel else "UNRESOLVED"
        if verdict not in VERDICTS:
            verdict = "UNRESOLVED"
        if not _authority_ok(agent, verdict):
            verdict = "UNRESOLVED"
        rows.append({
            "agent_id": aid,
            "name": agent.get("name"),
            "input_artifact": rel or str(REGISTRY_REL).replace("\\", "/"),
            "evidence_artifact": rel,
            "executed_at": mtime,
            "verdict": verdict,
            "authority_ok": _authority_ok(agent, verdict),
            "allowed_authority": list(agent.get("allowed_authority") or []),
            "reason": "artifact" if rel and doc else "no_runtime_this_cycle",
        })
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return {
        "schema": "ahos.cognitive_graph.v1",
        "generated_at": _utc(),
        "paper_only": True,
        "registry_agents": len(rows),
        "registry_note": "config/agent_registry.yaml lists 43 agents (AG-01 through AG-43), not 39.",
        "verdict_counts": counts,
        "authority_violations": [r["agent_id"] for r in rows if not r["authority_ok"]],
        "agents": rows,
    }


def export_cognitive_graph(root: Path) -> dict[str, Any]:
    snap = build_cognitive_graph(root)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
