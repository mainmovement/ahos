#!/usr/bin/env python3
"""Run Tracks 1–3 continuation receipts (PAPER_ONLY, 8GB-safe)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.exam import run_heldout_5domain_exam
from architecture.learning.memory_consolidation import consolidate_canonical_memory, run_pit_10k_benchmark
from architecture.markets import macro_calendar as mc
from architecture.learning.teaching_mode_m65 import generate_teaching_journal_snapshot
from architecture.markets.paper_trade_audit import export_paper_trade_audit_snapshot

import subprocess


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_weekday_witness_probe.py")], check=False)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "export_whitehat_audit.py")], check=False)
    paper = export_paper_trade_audit_snapshot(ROOT)
    probe_path = ROOT / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    probe = {}
    if probe_path.is_file():
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
    cal = mc.build_calendar(ROOT)
    mem = consolidate_canonical_memory(root=ROOT)
    pit = run_pit_10k_benchmark(root=ROOT, n_items=2000, n_queries=50)
    exam = run_heldout_5domain_exam(root=ROOT)
    m65 = generate_teaching_journal_snapshot(root=ROOT)
    m65_dir = ROOT / "reports" / "grok" / "M65"
    m65_dir.mkdir(parents=True, exist_ok=True)
    (m65_dir / "teaching_journal_snapshot.json").write_text(
        json.dumps(m65, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    payload = {
        "schema": "ahos.continuation_tracks.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "track1_paper_audit": paper["status"],
        "track1_weekend_tehran": paper.get("session_gate", {}).get("weekend_tehran"),
        "track1_tradable_desks": probe.get("tradable_asset_classes") or paper.get("tradable_asset_classes"),
        "track1_promotion_gate": paper.get("promotion_gate"),
        "track3_teaching_lessons": m65.get("lessons_count"),
        "track2_macro_ecb": cal["status"].get("ECB"),
        "track2_macro_opec": cal["status"].get("OPEC"),
        "track3_memory": mem.get("status", "OK"),
        "track3_pit_leaks": pit.get("future_leakage_count"),
        "track3_exam_score": exam.get("overall_score"),
        "track3_exam_leaked": exam.get("leaked"),
    }
    out = ROOT / "reports" / "grok" / "CONTINUATION" / "tracks_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
