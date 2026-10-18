from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_export_self_eval_from_summary(tmp_path: Path):
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "label": "REPLAY_NOT_LIVE",
                "markets": {"gold": {"tier": "T0", "measurable_pass": "4/10", "unmeasurable": ["regime_coverage"]}},
                "replay": {"verdict": "NO_PROVEN_EDGE"},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "self.json"
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "export_self_eval_snapshot.py"),
            "--summary",
            str(summary),
            "--out",
            str(out),
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    sc = payload["selfEvaluation"]["scorecards"][0]
    assert sc["decisionsWithEvidence"] == 4
    assert sc["decisionsReviewed"] == 10
    assert payload["selfEvaluation"]["demo"] is False
