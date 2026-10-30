"""Run every shadow module and publish one advisory message each."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore
from science.block_bootstrap import run_shadow as m10
from science.chronos_shadow import run_shadow as m12
from science.conformal import run_shadow as m03
from science.cost_model import run_shadow as m04
from science.expert_weighting import run_shadow as m09
from science.feature_lab import run_shadow as m08
from science.hrp_allocator import run_shadow as m06
from science.kelly_ceiling import run_shadow as m07
from science.memory import within_cap
from science.prereg import hash_ok, trial_counts
from science.pump_anomaly import run_shadow as m11
from science.purged_cv import run_shadow as m02
from science.red_team import review
from science.regime_engine import run_shadow as m05
from science.triple_barrier import run_shadow as m01

RUNNERS = (m01, m02, m03, m04, m05, m06, m07, m08, m09, m10, m11, m12)


def run_all(root: Path) -> dict[str, Any]:
    root = Path(root)
    rows = [fn() for fn in RUNNERS]
    for row in rows:
        row["ram_within_cap"] = within_cap(row.get("peak_mb"))
    red = review()
    doc = {
        "schema": "ahos.mega9_status.v1",
        "paper_only": True,
        "hash_ok": hash_ok(root) if (root / "docs" / "prereg" / "MEGA9.yaml").is_file() else False,
        "trial_counts": trial_counts(root) if (root / "docs" / "prereg" / "MEGA9.yaml").is_file() else {},
        "rows": rows,
        "red_team": red,
        "feed": {
            "university": "shadow_note",
            "mistake_memory": "not_applied",
            "family_reliability": "not_applied",
            "brier": None,
            "applied_to_live": False,
        },
        "promoted": 0,
        "applied_to_live": False,
    }
    return doc


def publish(root: Path, doc: dict[str, Any]) -> dict[str, Any]:
    """One OBSERVE message per module. The claim cannot promote."""
    root = Path(root)
    bus = MessageBus(root)
    for row in doc["rows"]:
        bus.deliver(AgentMessage(
            sender="AG-33",
            receiver="AG-09",
            evidence=(f"mega9:{row['id']}",),
            claim=f"{row['id']} stays {row['state']} and does not open a trade",
            confidence=0.2,
            required_action=RequiredAction.OBSERVE,
        ))
    store = WorldStateStore(root)
    prev = store.read()
    traces = dict((prev.get("sections") or {}).get("traces") or {})
    traces["mega9"] = {
        "hash_ok": doc["hash_ok"],
        "promoted": 0,
        "states": {row["id"]: row["state"] for row in doc["rows"]},
    }
    store.commit({"traces": traces}, {"MEGA9": "shadow"})
    out = root / "reports" / "grok" / "PAPER" / "mega9_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
