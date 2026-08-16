#!/usr/bin/env python3
"""AHOS Lane-B P1 — agent registry builder.
Reads config/agent_registry.yaml → isolated append-only store data/architecture_registry.sqlite.
ISOLATION: never touches discovery/paper_trading/ahos_local stores (enforced by path + tests).
Idempotent rebuilds: UNIQUE(agent_id, version) + INSERT OR IGNORE; UPDATE/DELETE aborted by triggers.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import yaml

from .contracts import load_schema, validate_spec

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_YAML = ROOT / "config" / "agent_registry.yaml"
DEFAULT_STORE = ROOT / "data" / "architecture_registry.sqlite"

DDL = """
CREATE TABLE IF NOT EXISTS agent (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  version TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  lane TEXT NOT NULL,
  form TEXT NOT NULL,
  cadence TEXT NOT NULL,
  criticality TEXT NOT NULL,
  spec_json TEXT NOT NULL,
  registered_utc TEXT NOT NULL,
  UNIQUE(agent_id, version)
);
CREATE TABLE IF NOT EXISTS registry_meta (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  event TEXT NOT NULL,
  detail TEXT NOT NULL,
  created_utc TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS ar_no_update BEFORE UPDATE ON agent BEGIN SELECT RAISE(ABORT,'append-only: agent'); END;
CREATE TRIGGER IF NOT EXISTS ar_no_delete BEFORE DELETE ON agent BEGIN SELECT RAISE(ABORT,'append-only: agent'); END;
CREATE TRIGGER IF NOT EXISTS rm_no_update BEFORE UPDATE ON registry_meta BEGIN SELECT RAISE(ABORT,'append-only: registry_meta'); END;
CREATE TRIGGER IF NOT EXISTS rm_no_delete BEFORE DELETE ON registry_meta BEGIN SELECT RAISE(ABORT,'append-only: registry_meta'); END;
"""


def load_registry_yaml(path: str | Path = REGISTRY_YAML) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def validate_registry(doc: dict, schema: dict | None = None) -> dict[str, list[str]]:
    """spec validation per agent; {} = fully conformant."""
    schema = schema or load_schema()
    out: dict[str, list[str]] = {}
    for spec in doc.get("agents", []):
        errs = validate_spec(spec, schema)
        if errs:
            out[spec.get("agent_id", "<unknown>")] = errs
    return out


def build_registry(store: str | Path = DEFAULT_STORE, yaml_path: str | Path = REGISTRY_YAML,
                   now: float | None = None) -> dict:
    now = time.time() if now is None else now
    doc = load_registry_yaml(yaml_path)
    problems = validate_registry(doc)
    if problems:
        return {"built": False, "violations": problems}
    conn = sqlite3.connect(str(store))
    conn.executescript(DDL)
    inserted = 0
    for spec in doc["agents"]:
        cur = conn.execute(
            """INSERT OR IGNORE INTO agent(agent_id,version,name,status,lane,form,cadence,
                   criticality,spec_json,registered_utc) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (spec["agent_id"], spec["version"], spec["name"], spec["status"], spec["lane"],
             spec["form"], spec["cadence"], spec["criticality"],
             json.dumps(spec, sort_keys=True), _utc(now)))
        inserted += cur.rowcount
    conn.execute("INSERT INTO registry_meta(ts,event,detail,created_utc) VALUES (?,?,?,?)",
                 (now, "BUILD", f"agents={len(doc['agents'])} inserted_new={inserted} "
                                f"matrix={doc.get('matrix_version')}", _utc(now)))
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM agent").fetchone()[0]
    conn.close()
    return {"built": True, "agents": len(doc["agents"]), "inserted_new": inserted,
            "total_rows": total, "store": str(store)}


def _utc(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")
