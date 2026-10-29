"""EDGE_REPORT → desk size policy (PAPER_ONLY). Merged conservatively with static haircuts in paper_trade_gates."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DESK_POLICY_REL = Path("reports") / "grok" / "PAPER" / "desk_policy.json"
EDGE_REPORT_REL = Path("reports") / "grok" / "PAPER" / "edge_report.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def notional_mult_from_desk_row(row: dict[str, Any]) -> float:
    """Advisory mult in [0.15, 1.0] from closed-trade desk PnL (after fees in log)."""
    closes = int(row.get("closes") or 0)
    pnl = float(row.get("realized_pnl_usd") or 0)
    if closes < 3:
        return 1.0
    if pnl >= 0:
        return 1.0
    severity = min(1.0, abs(pnl) / 2.0)
    return round(max(0.15, 0.5 - 0.35 * severity), 4)


def build_desk_policy_from_edge_report(edge: dict[str, Any]) -> dict[str, Any]:
    shrink_names = {
        str(d.get("desk"))
        for d in (edge.get("desks_recommend_shrink") or [])
        if isinstance(d, dict) and d.get("desk")
    }
    desk_rows: list[dict[str, Any]] = []
    for d in edge.get("desks") or []:
        if not isinstance(d, dict) or not d.get("desk"):
            continue
        desk = str(d["desk"])
        mult = notional_mult_from_desk_row(d)
        desk_rows.append(
            {
                "desk": desk,
                "notional_mult": mult,
                "shadow_only_advisory": desk in shrink_names and mult < 1.0,
                "closes": d.get("closes"),
                "realized_pnl_usd": d.get("realized_pnl_usd"),
                "source": "edge_report",
            }
        )
    by_desk = {r["desk"]: r["notional_mult"] for r in desk_rows}
    return {
        "schema": "ahos.desk_policy.v1",
        "generated_at": edge.get("generated_at") or _utc_now(),
        "edge_report_generated_at": edge.get("generated_at"),
        "paper_only": True,
        "edge_status": edge.get("edge_status"),
        "desks": desk_rows,
        "notional_mult_by_desk": by_desk,
        "honesty_note": (
            "Advisory size haircuts from the live closed book. shadow_only_advisory is telemetry only "
            "until owner enables a block; opens still respect merged notional_mult."
        ),
    }


def load_desk_policy(root: Path) -> dict[str, Any] | None:
    path = Path(root) / DESK_POLICY_REL
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict) or doc.get("schema") != "ahos.desk_policy.v1":
        return None
    return doc


def export_desk_policy(root: Path, edge_report: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    if edge_report is None:
        edge_path = root / EDGE_REPORT_REL
        edge_report = json.loads(edge_path.read_text(encoding="utf-8"))
    policy = build_desk_policy_from_edge_report(edge_report)
    policy["generated_at"] = _utc_now()
    out = root / DESK_POLICY_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return policy


def shadow_block_opens_enabled() -> bool:
    """Opt-in via AHOS_PAPER_DESK_SHADOW_BLOCK=1 — default off (size haircuts only)."""
    return os.environ.get("AHOS_PAPER_DESK_SHADOW_BLOCK", "").strip().lower() in ("1", "true", "yes", "on")


def desk_row(root: Path, desk: str) -> dict[str, Any] | None:
    pol = load_desk_policy(root)
    if not pol:
        return None
    for d in pol.get("desks") or []:
        if isinstance(d, dict) and d.get("desk") == desk:
            return d
    return None


def desk_entry_blocked_by_shadow_policy(root: Path, desk: str) -> tuple[bool, str | None]:
    if not shadow_block_opens_enabled():
        return False, None
    row = desk_row(root, desk)
    if row and row.get("shadow_only_advisory"):
        return True, "DESK_EDGE_SHADOW_BLOCK"
    return False, None
