#!/usr/bin/env python3
"""Team structure over the 100-mind registry.

`cognitive_registry_100.yaml` groups thinkers by academic discipline, which
answers "who are they?" but not "who decides what?". `config/council_teams.yaml`
re-organises the same 100 people into seven operational teams, each owning one
question that must be settled before money moves.

This module loads that structure and -- the part that matters -- reconciles it
against what is actually executable. A member marked ACTIVE whose lens has no
opinion function is a broken promise, so `validate()` reports exactly that
rather than letting the YAML assert a capability the code does not have.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from config.paths import get_config_dir

TEAMS_VERSION = "AHOS-TEAMS-v1"

# A member is one of:
#   ACTIVE       -- has an executable lens that votes on every candidate
#   ADVISORY     -- principle shapes the design; no per-token vote
#   PENDING_DATA -- duty is real but the evidence to perform it is not collected
VALID_STATUSES = frozenset({"ACTIVE", "ADVISORY", "PENDING_DATA"})


def _teams_path() -> Path:
    return Path(get_config_dir()) / "council_teams.yaml"


@dataclass
class TeamMember:
    thinker_id: str
    name: str
    duty: str
    duty_fa: str
    status: str
    lens_id: str | None = None

    @property
    def votes(self) -> bool:
        return self.status == "ACTIVE" and bool(self.lens_id)


@dataclass
class Team:
    team_id: str
    name_fa: str
    charter: str
    charter_fa: str
    lead: str
    veto_power: bool
    members: list[TeamMember] = field(default_factory=list)

    @property
    def voting_members(self) -> list[TeamMember]:
        return [m for m in self.members if m.votes]

    def lead_member(self) -> TeamMember | None:
        return next((m for m in self.members if m.thinker_id == self.lead), None)


@dataclass
class CouncilStructure:
    teams: list[Team] = field(default_factory=list)
    bench: list[dict[str, str]] = field(default_factory=list)
    # Lenses that vote but whose thinkers are outside the 100-registry. Kept
    # separate so the headline count is never inflated by them.
    external_lenses: list[dict[str, str]] = field(default_factory=list)
    evaluation_order: list[str] = field(default_factory=list)
    version: str = TEAMS_VERSION

    @property
    def total_members(self) -> int:
        return sum(len(t.members) for t in self.teams) + len(self.bench)

    @property
    def total_voting(self) -> int:
        return sum(len(t.voting_members) for t in self.teams)

    def team(self, team_id: str) -> Team | None:
        return next((t for t in self.teams if t.team_id == team_id), None)

    def team_for_lens(self, lens_id: str) -> Team | None:
        for t in self.teams:
            if any(m.lens_id == lens_id for m in t.members):
                return t
        for ext in self.external_lenses:
            if ext.get("lens_id") == lens_id:
                return self.team(ext.get("team", ""))
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "total_members": self.total_members,
            "total_voting": self.total_voting,
            "teams": [
                {"team_id": t.team_id, "name_fa": t.name_fa,
                 "charter": t.charter, "veto_power": t.veto_power,
                 "lead": t.lead, "members": len(t.members),
                 "voting": len(t.voting_members)}
                for t in self.teams],
            "bench": len(self.bench),
        }

    def report_persian(self) -> str:
        lines = ["🏛 ساختار تیمی شورا", ""]
        lines.append(f"مجموع اعضا: {self.total_members} | "
                     f"دارای رأی اجرایی: {self.total_voting}")
        lines.append("")
        for team_id in self.evaluation_order:
            t = self.team(team_id)
            if t is None:
                continue
            veto = "🛑 حق وتو" if t.veto_power else "💬 مشورتی"
            lead = t.lead_member()
            lines.append(f"▸ {t.name_fa} ({veto})")
            lines.append(f"   پرسش: {t.charter_fa}")
            if lead:
                lines.append(f"   سرپرست: {lead.name}")
            lines.append(f"   اعضا: {len(t.members)} | رأی‌دهنده: {len(t.voting_members)}")
            for m in t.members:
                mark = {"ACTIVE": "✅", "ADVISORY": "💭", "PENDING_DATA": "⏳"}[m.status]
                lines.append(f"     {mark} {m.name} — {m.duty_fa}")
            lines.append("")
        if self.bench:
            lines.append(f"🔧 نیمکت مهندسی ({len(self.bench)} نفر): سازندگان "
                         f"ابزارهایی که این سیستم با آن‌ها نوشته شده")
        return "\n".join(lines)


def load_structure(path: Path | str | None = None) -> CouncilStructure:
    src = Path(path) if path else _teams_path()
    with open(src, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    structure = CouncilStructure(
        evaluation_order=list(data.get("evaluation_order", [])))
    for block in data.get("teams", []):
        team = Team(
            team_id=block["team_id"], name_fa=block["name_fa"],
            charter=block["charter"], charter_fa=block["charter_fa"],
            lead=block["lead"], veto_power=bool(block.get("veto_power", False)))
        for m in block.get("members", []):
            team.members.append(TeamMember(
                thinker_id=m["id"], name=m["name"], duty=m["duty"],
                duty_fa=m["duty_fa"], status=m["status"],
                lens_id=m.get("lens_id")))
        structure.teams.append(team)
    structure.bench = list(
        data.get("engineering_bench", {}).get("members", []))
    structure.external_lenses = list(data.get("external_lenses", []))
    return structure


def validate(path: Path | str | None = None,
             registry_path: Path | str | None = None) -> list[str]:
    """Reconcile the declared structure against reality.

    Returns a list of problems; empty means the YAML tells the truth. This is
    the guard against the failure this whole file exists to prevent -- a
    roster that promises duties nothing performs.
    """
    from architecture.knowledge.panel import PANEL_LENSES, ALL_LENS_CARDS

    problems: list[str] = []
    structure = load_structure(path)

    reg_src = (Path(registry_path) if registry_path
               else Path(get_config_dir()) / "cognitive_registry_100.yaml")
    with open(reg_src, encoding="utf-8") as fh:
        registry = yaml.safe_load(fh)
    reg_names = {t["id"]: t["name"] for d in registry["domains"]
                 for t in d["thinkers"]}

    executable = {lens_id for lens_id, _ in PANEL_LENSES}
    seen: dict[str, str] = {}

    for team in structure.teams:
        if team.lead_member() is None:
            problems.append(f"{team.team_id}: lead {team.lead} is not a member")
        for m in team.members:
            if m.status not in VALID_STATUSES:
                problems.append(f"{m.thinker_id}: invalid status {m.status!r}")
            if m.thinker_id in seen:
                problems.append(
                    f"{m.thinker_id} assigned twice ({seen[m.thinker_id]}, {team.team_id})")
            seen[m.thinker_id] = team.team_id
            if m.thinker_id not in reg_names:
                problems.append(f"{m.thinker_id} is not in the 100-registry")
            elif reg_names[m.thinker_id] != m.name:
                problems.append(
                    f"{m.thinker_id}: named {m.name!r}, registry says "
                    f"{reg_names[m.thinker_id]!r}")
            # The check that matters: ACTIVE must mean it actually votes.
            if m.status == "ACTIVE":
                if not m.lens_id:
                    problems.append(f"{m.thinker_id} is ACTIVE with no lens_id")
                elif m.lens_id not in executable:
                    problems.append(
                        f"{m.thinker_id} is ACTIVE but {m.lens_id} has no "
                        f"executable opinion function")
                elif m.lens_id not in ALL_LENS_CARDS:
                    problems.append(
                        f"{m.lens_id} votes but has no data card with citations")

    for b in structure.bench:
        if b["id"] in seen:
            problems.append(f"{b['id']} is on both a team and the bench")
        seen[b["id"]] = "BENCH"
        if b["id"] not in reg_names:
            problems.append(f"{b['id']} (bench) is not in the 100-registry")

    missing = set(reg_names) - set(seen)
    if missing:
        problems.append(f"{len(missing)} registry thinkers unassigned: "
                        + ", ".join(sorted(missing)[:5]))

    # Every executable lens should belong to some team, or the team view is
    # not actually a view of the panel.
    orphans = [lid for lid in executable if structure.team_for_lens(lid) is None]
    if orphans:
        problems.append(f"{len(orphans)} voting lenses belong to no team: "
                        + ", ".join(sorted(orphans)[:5]))
    return problems
