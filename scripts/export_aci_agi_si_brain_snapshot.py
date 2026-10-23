#!/usr/bin/env python3
"""Export Progressive ACI -> AGI -> SI Brain snapshot (M60/M70) and Whole-AHOS 8-Organ Evolution snapshot (M57)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.cognitive.aci_agi_si_brain import run_aci_agi_si_evolution_cycle
from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle
from architecture.university.whole_ahos_organ_evolution import (
    build_whole_ahos_organ_evolution_snapshot,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    brain = run_aci_agi_si_evolution_cycle(root=ROOT)
    coder = run_autonomous_coder_cycle(root=ROOT)
    coder_path = ROOT / "reports" / "grok" / "M60" / "autonomous_coder_snapshot.json"
    _write_json(coder_path, coder)
    if not brain.get("four_brain_engine"):
        brain = {**brain, "four_brain_engine": coder.get("four_brain_engine")}
    brain_path = ROOT / "reports" / "grok" / "M60" / "aci_agi_si_brain_snapshot.json"
    _write_json(brain_path, brain)

    organs = build_whole_ahos_organ_evolution_snapshot()
    organs_path = ROOT / "reports" / "grok" / "M57" / "whole_ahos_organ_evolution.json"
    _write_json(organs_path, organs)

    print(
        f"wrote {brain_path.name} (stage={brain['current_stage_id']}, index={brain['compounding_capability_index']}) "
        f"and {organs_path.name} (organs={organs['organs_covered_count']}, avg_exam={organs['average_university_exam_score_pct']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
