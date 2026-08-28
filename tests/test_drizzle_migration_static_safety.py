#!/usr/bin/env python3
"""Static safety checks for the additive Drizzle ahos_* migration (no live DB)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "drizzle" / "0000_ahos_canonical_tables.sql").read_text(encoding="utf-8")
SCHEMA = (ROOT / "schema.ts").read_text(encoding="utf-8")
JOURNAL = ROOT / "drizzle" / "meta" / "_journal.json"


def test_migration_has_exactly_19_create_table_and_no_destructive_sql():
    creates = re.findall(r'CREATE TABLE "([^"]+)"', SQL)
    assert len(creates) == 19
    assert all(n.startswith("ahos_") for n in creates)
    for bad in (r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bDELETE\b", r"\bUPDATE\b"):
        assert re.search(bad, SQL, re.I) is None, bad


def test_migration_table_set_matches_schema_ts():
    mig = set(re.findall(r'CREATE TABLE "([^"]+)"', SQL))
    schema = set(re.findall(r'pgTable\(\s*"([^"]+)"', SCHEMA))
    assert mig == schema
    assert len(mig) == 19


def test_journal_single_canonical_entry():
    import json
    j = json.loads(JOURNAL.read_text(encoding="utf-8"))
    assert len(j["entries"]) == 1
    assert j["entries"][0]["tag"] == "0000_ahos_canonical_tables"


def test_package_json_has_migrate_but_no_push():
    import json
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts") or {}
    assert "db:migrate" in scripts
    assert "db:push" not in scripts
    assert "drizzle-kit push" not in json.dumps(scripts)


def test_docker_init_sql_has_zero_ahos_tables():
    legacy = (ROOT / "database" / "postgresql_schema.sql").read_text(encoding="utf-8")
    assert "ahos_" not in legacy
