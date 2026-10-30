"""Honest remaining-gap table. PAPER_ONLY. Does not close a wall-clock gap."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_REL = Path("reports") / "grok" / "PAPER" / "owner_gap_table.json"
_STATUS = re.compile(r"\*\*(OPEN|MITIGATED|CLOSED|OPTIONAL)[^*]*\*\*")
_TRACE = re.compile(r"\*\*(REAL|PARTIAL|MISSING|PLACEHOLDER)\*\*")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def parse_gap_register(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if not line.startswith("| M-GAP-"):
            continue
        cells = _cells(line)
        if len(cells) < 2:
            continue
        found = _STATUS.search(cells[-1])
        label = found.group(1) if found else "UNKNOWN"
        kind = {"CLOSED": "REAL", "MITIGATED": "PARTIAL", "OPTIONAL": "PARTIAL", "OPEN": "PARTIAL"}.get(label, "MISSING")
        rows.append({"id": cells[0], "register_status": label, "kind": kind, "evidence": "AHOS_GAP_REGISTER.md"})
    return rows


def parse_trace(text: str) -> dict[str, int]:
    counts = {"REAL": 0, "PARTIAL": 0, "MISSING": 0, "PLACEHOLDER": 0}
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        found = _TRACE.search(line)
        if found:
            counts[found.group(1)] += 1
    return counts


def parse_vision_audit(text: str) -> list[dict[str, str]]:
    """P0 and P1 rows from the 2026-09-12 alignment audit. Operational column is the evidence column."""
    rows = []
    for line in text.splitlines():
        if not line.startswith("| **"):
            continue
        cells = _cells(line)
        if len(cells) < 11:
            continue
        priority = cells[10]
        if priority not in {"P0", "P1"}:
            continue
        operational = cells[7]
        if operational in {"IMPL", "YES"}:
            kind = "REAL"
        elif operational in {"NO", "DES", "—", "-"}:
            kind = "MISSING"
        else:
            kind = "PARTIAL"
        rows.append({
            "capability": cells[0].replace("**", ""),
            "priority": priority,
            "operational": operational,
            "kind": kind,
            "gap": cells[9] if len(cells) > 9 else "",
            "evidence": "docs/supervision/AHOS_VISION_ALIGNMENT_AUDIT.md",
        })
    return rows


def build_census(root: Path) -> dict[str, Any]:
    root = Path(root)
    register = (root / "AHOS_GAP_REGISTER.md").read_text(encoding="utf-8") if (root / "AHOS_GAP_REGISTER.md").is_file() else ""
    trace = (root / "SPEC_TRACE.md").read_text(encoding="utf-8") if (root / "SPEC_TRACE.md").is_file() else ""
    audit_path = root / "docs" / "supervision" / "AHOS_VISION_ALIGNMENT_AUDIT.md"
    audit = audit_path.read_text(encoding="utf-8") if audit_path.is_file() else ""
    gaps = parse_gap_register(register)
    vision = parse_vision_audit(audit)
    trace_counts = parse_trace(trace)
    p0p1 = [row for row in vision if row["priority"] in {"P0", "P1"}]
    operational_real = [row["capability"] for row in p0p1 if row["kind"] == "REAL"]
    open_gaps = [row["id"] for row in gaps if row["register_status"] != "CLOSED"]
    return {
        "schema": "ahos.owner_gap_census.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "full_gap_register_file": False,
        "production_register": "AHOS_GAP_REGISTER.md",
        "gaps": gaps,
        "open_or_mitigated_ids": open_gaps,
        "trace_counts": trace_counts,
        "vision_p0_p1": p0p1,
        "vision_p0_p1_operational_real": operational_real,
        "vision_p0_p1_working_pct": round(100.0 * len(operational_real) / len(p0p1), 1) if p0p1 else None,
        "closed_this_mission": [],
        "not_closed_reason": (
            "P0 and P1 rows in the owner audit are not operationally IMPL. "
            "M-GAP-003, M-GAP-004, M-GAP-005, M-GAP-008, M-GAP-009 and the 72h soak "
            "still need time, a credential, or an external permission. This census does not relabel them."
        ),
        "decides": False,
    }


def export_census(root: Path) -> dict[str, Any]:
    doc = build_census(root)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc
