"""Measure the 67 charter roles. This module does not change a weight or promote."""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from architecture.learning.calibration import brier_score
from architecture.mission.world_state import WorldStateStore
from architecture.security.negahban import scan

BUS_REL = Path("reports") / "grok" / "PAPER" / "charter_bus.jsonl"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
OUT_REL = Path("reports") / "grok" / "PAPER" / "role_scorecard.json"
ORG_REL = Path("reports") / "grok" / "PAPER" / "org_map.json"
WINDOW_H = 24.0
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

DESKS = ("GOLD", "OIL", "CRYPTO", "EU", "ASIA", "US", "NQ", "ONCHAIN")
TEAMS = ("NEWS", "SEC", "RED", "UNI", "RDI")
CHARTER_ROLES = (
    [f"{desk}-{i:02d}" for desk in DESKS for i in range(1, 6)]
    + [f"{team}-{i:02d}" for team in TEAMS for i in range(1, 6)]
    + ["JUDGE-01", "BRAIN-01"]
)
DECISION_STEPS = frozenset({
    "judge", "paper", "no_setup", "no_trade", "veto", "rank",
    "rejected", "red_team", "lesson", "outcome", "hypothesis", "analysis",
})
FAMILY = {
    "PAPER": lambda role: role.endswith("-05") and role.split("-", 1)[0] in DESKS,
    "RED": lambda role: role.startswith("RED-"),
    "SEC": lambda role: role.startswith("SEC-"),
    "NEWS": lambda role: role.startswith("NEWS-"),
    "JUDGE": lambda role: role == "JUDGE-01",
    "BRAIN": lambda role: role == "BRAIN-01",
    "UNI": lambda role: role.startswith("UNI-"),
    "RDI": lambda role: role.startswith("RDI-"),
    "DESK": lambda role: (
        role.split("-", 1)[0] in DESKS
        and not role.endswith("-05")
    ),
}


def _utc(moment: datetime | None = None) -> str:
    stamp = moment or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(stamp: str | None) -> datetime | None:
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        out = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if out.tzinfo is None:
        out = out.replace(tzinfo=timezone.utc)
    return out.astimezone(timezone.utc)


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _role_map(root: Path) -> dict[str, str]:
    doc = {}
    path = Path(root) / ORG_REL
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
    mapping = dict(doc.get("mapping_only") or {})
    for section_name in ("us_equity", "core_roles"):
        section = doc.get(section_name) or {}
        if not isinstance(section, dict):
            continue
        for key, value in section.items():
            if isinstance(value, str) and key in CHARTER_ROLES:
                mapping[key] = value
                continue
            if not isinstance(value, dict) or not value.get("agent"):
                continue
            role = str(value.get("charter") or key)
            if role in CHARTER_ROLES:
                mapping[role] = str(value["agent"])
    # Core chain seats that live outside mapping_only.
    mapping.setdefault("RED-01", "AG-14")
    mapping.setdefault("RED-02", "AG-19")
    mapping.setdefault("UNI-02", "AG-03")
    mapping.setdefault("JUDGE-01", "AG-11")
    mapping.setdefault("BRAIN-01", "AG-01")
    mapping.setdefault("UNI-01", "AG-42")
    mapping.setdefault("UNI-03", "AG-40")
    for role in CHARTER_ROLES:
        mapping.setdefault(role, "UNMAPPED")
    return {role: mapping[role] for role in CHARTER_ROLES}


def _family(role: str) -> str | None:
    for name, check in FAMILY.items():
        if check(role):
            return name
    return None


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def role_scorecard_line(root: Path) -> str:
    doc = {}
    path = Path(root) / OUT_REL
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
    active = int(doc.get("active") or 0)
    name_only = int(doc.get("name_only") or 0)
    overloaded = int(doc.get("overloaded") or 0)
    return (
        f"نقش‌های فعال {str(active).translate(_DIGITS)} از ۶۷، "
        f"فقط‌اسم {str(name_only).translate(_DIGITS)}، "
        f"پرکار {str(overloaded).translate(_DIGITS)}"
    )


def run_role_scorecard(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    cutoff = moment - timedelta(hours=WINDOW_H)
    role_agents = _role_map(root)
    agent_roles: dict[str, list[str]] = defaultdict(list)
    for role, agent in role_agents.items():
        agent_roles[agent].append(role)

    by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in CHARTER_ROLES}
    for row in _rows(root / BUS_REL):
        role = str(row.get("sender_id") or "")
        if role not in by_role:
            continue
        stamp = _parse(row.get("timestamp_utc") if isinstance(row.get("timestamp_utc"), str) else None)
        if stamp is None or stamp < cutoff:
            continue
        by_role[role].append(row)

    closes: dict[str, dict[str, Any]] = {}
    for row in _rows(root / TRADES_REL):
        if str(row.get("event") or "") != "CLOSE":
            continue
        experiment = row.get("chain_experiment_id")
        if not experiment and isinstance(row.get("entry_brain"), dict):
            experiment = row["entry_brain"].get("chain_experiment_id")
        if not isinstance(experiment, str) or not experiment:
            continue
        if not isinstance(row.get("realized_pnl_usd"), (int, float)) or isinstance(row.get("realized_pnl_usd"), bool):
            continue
        closes[experiment] = row

    roles_out = []
    flags_name = 0
    flags_over = 0
    flags_harm = 0
    for role in CHARTER_ROLES:
        messages = by_role[role]
        messages.sort(key=lambda row: str(row.get("timestamp_utc") or ""))
        decisions = [row for row in messages if str(row.get("step") or "") in DECISION_STEPS]
        gaps = []
        for left, right in zip(messages, messages[1:]):
            a = _parse(left.get("timestamp_utc") if isinstance(left.get("timestamp_utc"), str) else None)
            b = _parse(right.get("timestamp_utc") if isinstance(right.get("timestamp_utc"), str) else None)
            if a is None or b is None:
                continue
            delta = (b - a).total_seconds()
            if delta >= 0:
                gaps.append(delta)
        probs: list[float] = []
        outcomes: list[float] = []
        right = 0
        wrong = 0
        for row in decisions:
            experiment = str(row.get("experiment_id") or "")
            base = experiment.split("-reject", 1)[0]
            close = closes.get(base)
            if close is None:
                continue
            pnl = float(close["realized_pnl_usd"])
            win = pnl > 0
            conf = row.get("confidence")
            if isinstance(conf, (int, float)) and not isinstance(conf, bool):
                probs.append(float(conf))
                outcomes.append(1.0 if win else 0.0)
            step = str(row.get("step") or "")
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            predicted_win = None
            if step in {"paper", "judge"}:
                entry = str(payload.get("paper_entry") or "")
                if entry == "ALLOWED" or step == "paper":
                    predicted_win = True
            elif step == "lesson":
                case = str(payload.get("university_case") or "")
                if case == "WIN":
                    predicted_win = True
                elif case in {"LOSS", "BAD_TIMING"}:
                    predicted_win = False
            elif step in {"no_setup", "no_trade", "veto", "rejected"}:
                continue
            if predicted_win is None:
                continue
            if predicted_win == win:
                right += 1
            else:
                wrong += 1
        agent = role_agents[role]
        held = agent_roles.get(agent) or [role]
        families = {name for name in (_family(item) for item in held) if name}
        flags = []
        if not messages:
            flags.append("NAME_ONLY")
            flags_name += 1
        if len(held) >= 3 and len(families) >= 2:
            flags.append("OVERLOADED")
            flags_over += 1
        if (right + wrong) >= 10 and wrong > right:
            flags.append("HARMFUL")
            flags_harm += 1
        roles_out.append({
            "role": role,
            "agent": agent,
            "messages_24h": len(messages),
            "decisions_24h": len(decisions),
            "proven_right": right,
            "proven_wrong": wrong,
            "brier": None if not probs else round(float(brier_score(probs, outcomes) or 0.0), 4),
            "avg_time_s": _avg(gaps),
            "flags": flags,
            "agent_role_count": len(held),
            "families": sorted(families),
        })

    active = sum(1 for row in roles_out if row["messages_24h"] > 0)
    doc = {
        "schema": "ahos.role_scorecard.v1",
        "paper_only": True,
        "promoted": False,
        "applied_to_live_weights": False,
        "decides": False,
        "window_h": WINDOW_H,
        "generated_at": _utc(moment),
        "pid": os.getpid(),
        "roles": roles_out,
        "active": active,
        "name_only": flags_name,
        "overloaded": flags_over,
        "harmful": flags_harm,
        "role_count": 67,
    }
    text = json.dumps(doc, ensure_ascii=False, indent=1)
    if scan(text).level == "HALT":
        raise RuntimeError("role scorecard failed the secret scan")
    path = root / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["role_scorecard"] = {
            "active": active,
            "name_only": flags_name,
            "overloaded": flags_over,
            "harmful": flags_harm,
            "pid": os.getpid(),
            "promoted": False,
            "applied_to_live_weights": False,
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-22"})
    except Exception:
        pass
    return doc
