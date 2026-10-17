"""M47 health monitor: READ / DOWNGRADE / HALT from soak evidence (read-only)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from config.paths import get_project_root

HealthLevel = Literal["READ", "DOWNGRADE", "HALT", "UNKNOWN"]


@dataclass(frozen=True, slots=True)
class HealthReport:
    level: HealthLevel
    reasons: tuple[str, ...]
    paper_only: bool | None
    soak_path: str


def default_soak_status_path() -> Path:
    return get_project_root() / "reports" / "grok" / "M13_SOAK" / "soak_status.json"


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except ValueError:
        return None


def assess_soak_health(
    status: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    stale_after_sec: float = 3600.0,
) -> HealthReport:
    now = now or datetime.now(timezone.utc)
    if status is None:
        return HealthReport("UNKNOWN", ("soak status missing",), None, "")

    reasons: list[str] = []
    level: HealthLevel = "READ"

    paper = status.get("paper_only")
    if paper is not True:
        return HealthReport("HALT", ("paper_only is not true",), False if paper is False else None, "")

    failed = int(status.get("cycles_failed") or 0)
    if failed > 0:
        level = "DOWNGRADE"
        reasons.append(f"cycles_failed={failed}")

    last = status.get("last_cycle") or {}
    if last.get("ok") is False:
        level = "DOWNGRADE"
        reasons.append("last_cycle not ok")

    breaker = last.get("breaker") or {}
    if breaker.get("allowed") is False:
        return HealthReport("HALT", ("circuit breaker disallowed",), True, "")

    ts = _parse_ts(last.get("ts") if isinstance(last, dict) else None)
    if ts is None:
        level = "DOWNGRADE"
        reasons.append("last_cycle timestamp missing")
    else:
        age = (now - ts).total_seconds()
        if age > stale_after_sec:
            level = "DOWNGRADE"
            reasons.append(f"last_cycle stale ({int(age)}s)")

    ledger_err = last.get("ledger_error") if isinstance(last, dict) else None
    if ledger_err:
        level = "DOWNGRADE"
        reasons.append(f"ledger_error present")

    if not reasons:
        reasons.append("soak readable and paper-only")
    return HealthReport(level, tuple(reasons), True, "")


def load_and_assess(path: Path | None = None, **kwargs: Any) -> HealthReport:
    p = path or default_soak_status_path()
    if not p.is_file():
        return HealthReport("UNKNOWN", ("soak_status.json missing",), None, str(p))
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return HealthReport("UNKNOWN", (f"unreadable: {exc}",), None, str(p))
    if not isinstance(data, dict):
        return HealthReport("UNKNOWN", ("soak status not an object",), None, str(p))
    rep = assess_soak_health(data, **kwargs)
    return HealthReport(rep.level, rep.reasons, rep.paper_only, str(p))
