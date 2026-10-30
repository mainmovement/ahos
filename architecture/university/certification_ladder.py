"""L0–L4 certification dry-run. Observes evidence. Does not raise the autonomy ceiling."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.cognitive.contracts import CURRENT_AUTONOMY_CEILING, AutonomyLevel

RECEIPT_REL = Path("reports") / "grok" / "M59" / "certification_ladder_dry_run.json"


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).is_file()


def run_l0_l4_dry_run(root: Path) -> dict[str, Any]:
    root = Path(root)
    levels = [
        {
            "level": AutonomyLevel.L0_OBSERVE.value,
            "observed": _exists(root, "reports/grok/M13_SOAK/soak_heartbeat.json"),
            "evidence": "reports/grok/M13_SOAK/soak_heartbeat.json",
            "granted": False,
        },
        {
            "level": AutonomyLevel.L1_ANALYZE.value,
            "observed": _exists(root, "reports/grok/PAPER/edge_report.json"),
            "evidence": "reports/grok/PAPER/edge_report.json",
            "granted": CURRENT_AUTONOMY_CEILING == AutonomyLevel.L1_ANALYZE,
            "note": "Granted only as the existing cognitive ceiling, not as a new promotion.",
        },
        {
            "level": AutonomyLevel.L2_RECOMMEND.value,
            "observed": _exists(root, "architecture/markets/council_gate.py"),
            "evidence": "architecture/markets/council_gate.py",
            "granted": False,
            "note": "Council output stays advisory.",
        },
        {
            "level": AutonomyLevel.L3_AUTONOMOUS_EXPERIMENT.value,
            "observed": _exists(root, "strategy_lab/registry.json"),
            "evidence": "strategy_lab/registry.json",
            "granted": False,
            "note": "Experiments stay unpromoted while strategy_switch is version 0.",
        },
        {
            "level": AutonomyLevel.L4_PAPER_TRADING.value,
            "observed": _exists(root, "architecture/markets/paper_trader.py"),
            "evidence": "architecture/markets/paper_trader.py",
            "granted": False,
            "note": "Paper trading is a separate PAPER_ONLY engine. This dry-run does not grant L4 to the cognitive core.",
        },
    ]
    edge_eligible = None
    edge_path = root / "reports" / "grok" / "PAPER" / "edge_report.json"
    if edge_path.is_file():
        try:
            edge_eligible = json.loads(edge_path.read_text(encoding="utf-8")).get("promotion_gate", {}).get("eligible")
        except json.JSONDecodeError:
            edge_eligible = None
    return {
        "schema": "ahos.certification_ladder_dry_run.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "autonomy_ceiling": CURRENT_AUTONOMY_CEILING.value,
        "ceiling_unchanged": True,
        "promotion_eligible": edge_eligible,
        "levels": levels,
        "honesty": "Dry-run only. L2–L4 are observed, not certified.",
    }


def export_l0_l4_dry_run(root: Path) -> dict[str, Any]:
    doc = run_l0_l4_dry_run(root)
    out = Path(root) / RECEIPT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
