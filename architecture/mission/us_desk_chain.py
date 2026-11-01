"""US equity desk chain. The steps live in the shared template."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import json

from architecture.mission.desk_chain_template import BUS_REL, desk_line, load_desks, run_desk_chain


def us_desk_line(root: Path) -> str:
    """Persian status. Works only after a live soak or trader pid logged nine steps."""
    from architecture.markets.shadow_cycle import live_pids

    allowed = live_pids(root)
    path = Path(root) / BUS_REL
    if not allowed or not path.is_file():
        return "مسیر کامل میز آمریکا: نمی‌کند"
    groups: dict[str, set[str]] = {}
    pids: dict[str, set[int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[-80:]:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("rejected") is True:
            continue
        exp = str(row.get("experiment_id") or "")
        step = str(row.get("step") or "")
        if not exp or not step:
            continue
        groups.setdefault(exp, set()).add(step)
        pids.setdefault(exp, set()).add(int(row.get("pid") or 0))
    for exp, steps in groups.items():
        if len(steps) >= 9 and pids.get(exp, set()) & allowed:
            return "مسیر کامل میز آمریکا: کار می‌کند"
    return "مسیر کامل میز آمریکا: نمی‌کند"


def run_us_desk_chain(
    root: Path,
    quotes: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    del events
    cfg = dict(load_desks(root)["US_EQUITIES"])
    cfg["desk"] = "US_EQUITIES"
    return run_desk_chain(root, cfg, quotes, now=now)


def real_us_line(root: Path) -> str:
    return desk_line(root, "US_EQUITIES")
