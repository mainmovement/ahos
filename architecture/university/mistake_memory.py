"""Before an open, look up repeated losses on the same desk and side.

Three or more matching losses shrink the paper size. A repeated news trap
or bad-data loss vetoes the open. A single loss does not match. The live
weight is not changed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import CASES_REL, loss_cause

MIN_MATCHES = 3
SHRINK = 0.5
VETO_CAUSES = frozenset({"NEWS_TRAP", "BAD_DATA"})


def _cases(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / CASES_REL
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def review_open(
    root: Path,
    desk: str,
    side: str,
    agreeing_families: list[str],
    *,
    witness_verdict: str | None = None,
) -> dict[str, Any]:
    """Match stored loss cases. Fewer than three matches leaves the size alone."""
    families = {str(name) for name in agreeing_families}
    counts: dict[str, int] = {}
    for case in _cases(root):
        if float(case.get("realized_pnl_usd") or 0) > 0:
            continue
        if str(case.get("desk") or "") != desk or str(case.get("side") or "") != side:
            continue
        cause = str(case.get("cause") or "") or loss_cause(case)
        wrong = {str(name) for name in (case.get("families_wrong") or [])}
        matched = False
        if cause == "BAD_DATA" and witness_verdict == "CONFLICT":
            matched = True
        elif cause == "NEWS_TRAP" and "news" in families:
            matched = True
        elif cause not in VETO_CAUSES and wrong & families:
            matched = True
        if matched:
            counts[cause] = counts.get(cause, 0) + 1
    armed = {cause: n for cause, n in counts.items() if n >= MIN_MATCHES}
    if not armed:
        return {"action": "NONE", "factor": 1.0, "cause": None, "matches": 0, "applied_to_live_weights": False}
    cause = max(armed, key=lambda name: (armed[name], name in VETO_CAUSES))
    action, factor = ("VETO", 0.0) if cause in VETO_CAUSES else ("SHRINK", SHRINK)
    return {"action": action, "factor": factor, "cause": cause, "matches": armed[cause], "applied_to_live_weights": False}
