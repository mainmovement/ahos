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


def test_docker_init_sql_has_zero_ahos_tables():
    init = (ROOT / "database" / "postgresql_schema.sql").read_text(encoding="utf-8")
    # Explicit: no CREATE TABLE ahos_* (comments may mention ahos_ without creating).
    assert re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?ahos_', init, re.I) is None
    legacy = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", init, re.I)
    assert len(legacy) == 8


def test_windows_compose_mounts_legacy_init_not_drizzle():
    compose = (ROOT / "deployment" / "docker-compose.windows.yml").read_text(encoding="utf-8")
    assert "postgresql_schema.sql" in compose
    assert "0000_ahos_canonical_tables.sql" not in compose
    assert "db:migrate" not in compose


def test_drizzle_config_requires_database_url_and_filters_ahos():
    cfg = (ROOT / "drizzle.config.ts").read_text(encoding="utf-8")
    assert "DATABASE_URL" in cfg
    assert 'tablesFilter' in cfg and "ahos_*" in cfg
    assert 'schema: "./schema.ts"' in cfg or "schema: './schema.ts'" in cfg


def test_migration_snapshot_json_table_count_matches():
    import json
    snap = json.loads((ROOT / "drizzle" / "meta" / "0000_snapshot.json").read_text(encoding="utf-8"))
    tables = [k for k in (snap.get("tables") or {}) if "ahos_" in k]
    assert len(tables) == 19


def test_no_if_not_exists_on_ahos_create_table():
    """Bare CREATE TABLE fails loudly if tables already exist — safer than silent IF NOT EXISTS."""
    assert re.search(r'CREATE TABLE IF NOT EXISTS "ahos_', SQL, re.I) is None
