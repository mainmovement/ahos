"""M65 integration for M57 weekly shadow hypothesis scorecard lessons."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.learning.teaching_mode_m65 import TeachingLessonFa, generate_teaching_journal_snapshot


def lessons_from_weekly_shadow_scorecard(repo: Path) -> list[TeachingLessonFa]:
    path = repo / "reports" / "grok" / "M57" / "weekly_research_shadow_scorecard.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: list[TeachingLessonFa] = []
    for h in doc.get("hypotheses") or []:
        if not isinstance(h, dict):
            continue
        hid = str(h.get("hypothesis_id") or "")
        n = int(h.get("counterfactual_scored_closes") or 0)
        if not hid or n <= 0:
            continue
        hr = h.get("counterfactual_hit_rate")
        pct = f"{float(hr) * 100:.0f}%" if hr is not None else "نامشخص"
        out.append(
            TeachingLessonFa(
                lesson_id=f"m57-shadow-{hid.lower()}",
                market="UNIVERSITY",
                symbol=hid,
                regime_tag="SHADOW_CALIBRATION",
                title_fa=f"کالیبراسیون سایهٔ {hid} (U-108)",
                why_entered_fa="فرضیه در composite وزن صفر دارد؛ با بازدهٔ قیمت entry→exit سنجیده می‌شود.",
                what_happened_fa=(
                    f"{n} بستن: counterfactual hit-rate={pct} "
                    f"(hits={h.get('counterfactual_hits')} misses={h.get('counterfactual_misses')})."
                ),
                mistake_or_strength_fa="آمار لبه یا promote نیست.",
                key_takeaway_fa="promote فقط PASS_STATS + SURVIVED_RED_TEAM.",
                glossary_keys=("DSR",),
            )
        )
    return out


def refresh_teaching_journal_with_shadow_scorecard(root: Path, weekly_doc: dict[str, Any] | None = None) -> dict[str, Any]:
    repo = Path(root)
    snap = generate_teaching_journal_snapshot(root=repo)
    extra = lessons_from_weekly_shadow_scorecard(repo)
    if extra:
        merged = list(snap.get("lessons") or [])
        ids = {x.get("lesson_id") for x in merged}
        for e in extra:
            if e.lesson_id in ids:
                continue
            merged.insert(
                0,
                {
                    "lesson_id": e.lesson_id,
                    "market": e.market,
                    "symbol": e.symbol,
                    "regime_tag": e.regime_tag,
                    "title_fa": e.title_fa,
                    "why_entered_fa": e.why_entered_fa,
                    "what_happened_fa": e.what_happened_fa,
                    "mistake_or_strength_fa": e.mistake_or_strength_fa,
                    "key_takeaway_fa": e.key_takeaway_fa,
                    "glossary_keys": list(e.glossary_keys),
                    "paper_only": True,
                    "source": "M57_WEEKLY_SHADOW_SCORECARD",
                },
            )
        snap["lessons"] = merged
        snap["lessons_count"] = len(merged)
        snap["m57_weekly_shadow"] = {"lessons_added": len(extra)}
    for rel in ("reports/grok/M65/teaching_journal_snapshot.json", "reports/grok/M65/teaching_snapshot.json"):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snap
