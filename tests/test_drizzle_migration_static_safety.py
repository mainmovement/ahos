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


def test_migration_column_sets_match_schema_ts():
    """Structural equality beyond table names: column sets must match."""
    import re
    sql = (ROOT / "drizzle" / "0000_ahos_canonical_tables.sql").read_text(encoding="utf-8")
    schema = (ROOT / "schema.ts").read_text(encoding="utf-8")
    creates = dict(re.findall(r'CREATE TABLE "([^"]+)" \((.*?)\);', sql, re.S))
    sql_cols = {}
    for t, body in creates.items():
        cols = []
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            m = re.match(r'"([^"]+)"\s+\w+', line)
            if m:
                cols.append(m.group(1))
        sql_cols[t] = set(cols)
    schema_cols = {}
    for m in re.finditer(
        r'pgTable\(\s*"([^"]+)"\s*,\s*\{(.*?)\}\s*(?:,\s*\(.*?\)\s*=>|\);)',
        schema,
        re.S,
    ):
        tname, body = m.group(1), m.group(2)
        # Only column builders:  name: pgType("col"
        schema_cols[tname] = set(
            re.findall(
                r'^\s*\w+\s*:\s*(?:serial|text|integer|bigint|boolean|timestamp|numeric|real|doublePrecision|jsonb|uuid|varchar)\("([^"]+)"',
                body,
                re.M,
            )
        )
    assert set(sql_cols) == set(schema_cols)
    for t in sql_cols:
        assert sql_cols[t] == schema_cols[t], (t, sql_cols[t] ^ schema_cols[t])
