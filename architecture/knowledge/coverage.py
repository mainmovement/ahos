#!/usr/bin/env python3
"""What the 100-mind registry actually contributes -- measured, not asserted.

The problem
-----------
`config/cognitive_registry_100.yaml` lists 100 thinkers across mathematics,
computing, security, crypto, economics and statistics. Its only consumer in
the entire codebase was a test asserting the list contains 100 unique names.
Nothing read a principle from it, and no decision changed because a name was
in the file. A registry nothing reads is a claim, not a capability.

`lenses.LENS_PILOT_REGISTRY` was a second layer of the same problem: thirty
lens data cards, ten with an executable opinion function and twenty inert.

This module makes the gap measurable. It reports, per domain, how many
thinkers have a lens card and how many of those cards actually vote, so the
distance between "listed" and "operational" is a number in a report rather
than a comfortable assumption.

It is deliberately read-only and stdlib-plus-PyYAML: an audit that could
mutate the thing it audits is not an audit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from config.paths import get_config_dir
from .lenses import LENS_PILOT_REGISTRY
from .panel import PANEL_LENSES

COVERAGE_VERSION = "AHOS-COGCOV-v1"


def _registry_path() -> Path:
    return Path(get_config_dir()) / "cognitive_registry_100.yaml"


def _surname(identity: str) -> str:
    """'Claude Shannon (1916-2001)' -> 'claude shannon'."""
    return identity.split("(")[0].strip().lower()


@dataclass
class DomainCoverage:
    domain: str
    total_thinkers: int = 0
    with_lens_card: list[str] = field(default_factory=list)
    executable: list[str] = field(default_factory=list)

    @property
    def card_fraction(self) -> float:
        return len(self.with_lens_card) / self.total_thinkers if self.total_thinkers else 0.0

    @property
    def executable_fraction(self) -> float:
        return len(self.executable) / self.total_thinkers if self.total_thinkers else 0.0


@dataclass
class CognitiveCoverageReport:
    total_thinkers: int = 0
    total_cards: int = 0
    total_executable: int = 0
    domains: list[DomainCoverage] = field(default_factory=list)
    cards_outside_registry: list[str] = field(default_factory=list)
    inert_cards: list[str] = field(default_factory=list)
    version: str = COVERAGE_VERSION

    @property
    def executable_fraction(self) -> float:
        return self.total_executable / self.total_thinkers if self.total_thinkers else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "total_thinkers": self.total_thinkers,
            "total_cards": self.total_cards,
            "total_executable": self.total_executable,
            "executable_fraction": round(self.executable_fraction, 4),
            "inert_cards": self.inert_cards,
            "cards_outside_registry": self.cards_outside_registry,
            "domains": [
                {"domain": d.domain, "total": d.total_thinkers,
                 "cards": len(d.with_lens_card),
                 "executable": len(d.executable),
                 "executable_names": d.executable}
                for d in self.domains],
        }

    def report_persian(self) -> str:
        lines = ["🧠 پوشش شورای ۱۰۰ ذهن برتر", ""]
        lines.append(f"• ثبت‌شده در رجیستری: {self.total_thinkers} نفر")
        lines.append(f"• دارای کارت دیدگاه: {self.total_cards}")
        lines.append(f"• دارای رأی اجرایی: {self.total_executable} "
                     f"({self.executable_fraction:.0%})")
        lines.append("")
        lines.append("به تفکیک حوزه:")
        for d in sorted(self.domains, key=lambda x: -x.executable_fraction):
            bar = "█" * len(d.executable) + "·" * max(
                0, len(d.with_lens_card) - len(d.executable))
            lines.append(f"  {d.domain:34} {len(d.executable):2}/{d.total_thinkers:2} {bar}")
        if self.inert_cards:
            lines.append("")
            lines.append("کارت‌های بدون رأی اجرایی (داده‌ی خاموش):")
            lines.append("  " + "، ".join(sorted(self.inert_cards)))
        return "\n".join(lines)


def analyze_coverage(registry_path: Path | str | None = None) -> CognitiveCoverageReport:
    """Measure how much of the declared council is actually wired in."""
    path = Path(registry_path) if registry_path else _registry_path()
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    executable_ids = {lens_id for lens_id, _ in PANEL_LENSES}
    card_by_name = {_surname(card.identity): lens_id
                    for lens_id, card in LENS_PILOT_REGISTRY.items()}

    report = CognitiveCoverageReport()
    matched_cards: set[str] = set()

    for domain_block in data.get("domains", []):
        dc = DomainCoverage(domain=domain_block.get("domain", "UNKNOWN"))
        for thinker in domain_block.get("thinkers", []):
            dc.total_thinkers += 1
            lens_id = card_by_name.get(thinker.get("name", "").strip().lower())
            if lens_id is None:
                continue
            matched_cards.add(lens_id)
            dc.with_lens_card.append(thinker["name"])
            if lens_id in executable_ids:
                dc.executable.append(thinker["name"])
        report.domains.append(dc)
        report.total_thinkers += dc.total_thinkers
        report.total_cards += len(dc.with_lens_card)
        report.total_executable += len(dc.executable)

    report.cards_outside_registry = sorted(
        set(LENS_PILOT_REGISTRY) - matched_cards)
    report.inert_cards = sorted(set(LENS_PILOT_REGISTRY) - executable_ids)
    return report
