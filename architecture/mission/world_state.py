"""One versioned paper world state and one advisory message log. PAPER_ONLY.

The mission ledger stays the fill record. This store is the shared projection
modules read. It does not decide, promote, or trade. Inter-agent traffic is
only an AgentMessage from agent_org.contracts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage

SCHEMA = "ahos.world_state.v1"
STATE_REL = Path("reports") / "grok" / "PAPER" / "world_state.json"
HISTORY_REL = Path("reports") / "grok" / "PAPER" / "world_state.jsonl"
BUS_REL = Path("reports") / "grok" / "PAPER" / "agent_bus.jsonl"

SECTIONS = (
    "positions",
    "signals",
    "family_votes",
    "regime",
    "news",
    "risk",
    "lessons",
    "hypotheses",
    "council",
    "security",
    "kill_switch",
    "traces",
)


def _utc(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


class WorldStateStore:
    """The only writer of world_state.json. Callers pass sections; they do not open the file."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path(self) -> Path:
        return self.root / STATE_REL

    def read(self) -> dict[str, Any]:
        doc = _read_json(self.path())
        if doc and doc.get("schema") == SCHEMA:
            return doc
        return {
            "schema": SCHEMA,
            "version": 0,
            "paper_only": True,
            "decides": False,
            "sections": {},
            "writers": {},
        }

    def commit(self, sections: dict[str, Any], writers: dict[str, str], *, now: datetime | None = None) -> dict[str, Any]:
        unknown = [key for key in sections if key not in SECTIONS]
        if unknown:
            raise ValueError(f"unknown world-state section: {unknown[0]}")
        prev = self.read()
        version = int(prev.get("version") or 0) + 1
        merged = dict(prev.get("sections") or {})
        merged.update(sections)
        doc = {
            "schema": SCHEMA,
            "version": version,
            "paper_only": True,
            "decides": False,
            "live_trading": False,
            "generated_at": _utc(now),
            "sections": merged,
            "writers": {**dict(prev.get("writers") or {}), **writers},
        }
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        history = self.root / HISTORY_REL
        with history.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "schema": SCHEMA,
                "version": version,
                "generated_at": doc["generated_at"],
                "writers": writers,
                "decides": False,
                "paper_only": True,
            }, ensure_ascii=False) + "\n")
        return doc


class MessageBus:
    """Append-only audit of AgentMessage envelopes. A dict that is not a message is refused."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path(self) -> Path:
        return self.root / BUS_REL

    def deliver(self, message: AgentMessage, *, now: datetime | None = None) -> dict[str, Any]:
        if not isinstance(message, AgentMessage):
            raise TypeError("the bus accepts only AgentMessage")
        row = {
            **message.as_dict(),
            "logged_at": _utc(now),
            "delivered": True,
        }
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def read(self) -> list[dict[str, Any]]:
        path = self.path()
        if not path.is_file():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict):
                rows.append(item)
        return rows
