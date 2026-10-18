from __future__ import annotations

from architecture.university.registry import SCHEMA_V1, load_sources, parse_sources_yaml


def test_parse_sources_yaml_reads_seed_format():
    text = f"""schema: {SCHEMA_V1}
sources:
  - url: https://example.org/a
    license: CC0
    faculty: quant
"""
    schema, rows = parse_sources_yaml(text)
    assert schema == SCHEMA_V1
    assert len(rows) == 1
    assert rows[0].domain == "example.org"
    assert rows[0].faculty == "quant"


def test_load_sources_from_repo_seed():
    rows = load_sources()
    assert len(rows) >= 3
    assert all(r.url.startswith("http") for r in rows)
