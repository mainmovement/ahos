from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from architecture.learning.lessons_ledger import LessonsLedger


def test_export_writes_json_from_sqlite(tmp_path: Path):
    db = tmp_path / "m49_lessons.sqlite"
    store = LessonsLedger(db)
    store.append(
        lesson_id="L-test-1",
        source="unit",
        market="gold",
        taxonomy="test",
        evidence_refs=("ev-1",),
        claim="mistake claim",
        counterfactual="lesson text",
        status="UNVERIFIED",
        valid_from="2026-01-01",
    )
    store.close()
    out = tmp_path / "out.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts" / "export_m49_lessons_snapshot.py"),
            "--sqlite",
            str(db),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["paper_only"] is True
    assert len(payload["lessons"]) == 1
    assert payload["lessons"][0]["id"] == "L-test-1"
