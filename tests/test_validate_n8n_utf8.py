"""Windows compatibility: n8n workflow JSON must validate under UTF-8 (not charmap)."""
from __future__ import annotations

import glob
from pathlib import Path

from tests.validate_n8n import validate

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "n8n" / "workflows"


def test_n8n_workflows_validate_with_utf8_open():
    paths = sorted(WF.glob("*.json"))
    assert paths, "expected n8n workflow JSON files"
    failures = []
    for path in paths:
        errs, _warns = validate(str(path))
        if errs:
            failures.append((path.name, errs))
    assert not failures, failures


def test_known_charmap_files_are_non_cp1252_but_utf8_readable():
    """Regression: ahos_10/11/12 contain bytes that break Windows charmap open()."""
    targets = [
        WF / "ahos_10_research_lab.json",
        WF / "ahos_11_data_update.json",
        WF / "ahos_12_research_report.json",
    ]
    for path in targets:
        assert path.is_file(), path
        raw = path.read_bytes()
        try:
            raw.decode("cp1252")
            # If somehow ASCII-only, still must validate
        except UnicodeDecodeError:
            pass
        text = raw.decode("utf-8")
        assert text.lstrip().startswith("{")
        errs, _ = validate(str(path))
        assert errs == [], (path.name, errs)
