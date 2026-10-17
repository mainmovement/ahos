"""M64 defensive scan. A secret-shaped string halts the action. Nothing is exploited."""
from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET = re.compile(r"sk-[A-Za-z0-9]{8,}|BEGIN [A-Z ]*PRIVATE KEY")


@dataclass(frozen=True, slots=True)
class Scan:
    level: str
    findings: int


def scan(text: str) -> Scan:
    found = _SECRET.findall(text)
    if found:
        return Scan("HALT", len(found))
    return Scan("READ", 0)
