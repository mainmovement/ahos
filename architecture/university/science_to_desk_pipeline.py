"""M57 Science scout -> Research Institute -> AHOS core -> University desk training. PAPER_ONLY."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.university.whole_ahos_organ_evolution import (
    WHOLE_AHOS_ORGANS_8,
    build_whole_ahos_organ_evolution_snapshot,
)

PAPER_ONLY: bool = True

GLOBAL_SOURCES: tuple[dict[str, str], ...] = (
    {"id": "github", "name_en": "GitHub OSS", "name_fa": "گیت‌هاب"},
    {"id": "mit_ocw", "name_en": "MIT OpenCourseWare", "name_fa": "MIT OCW"},
    {"id": "arxiv", "name_en": "arXiv", "name_fa": "آرکایو"},
    {"id": "ssrn", "name_en": "SSRN", "name_fa": "SSRN"},
    {"id": "quantpedia", "name_en": "Quantpedia", "name_fa": "کوانت‌پدیا"},
    {"id": "stanford", "name_en": "Stanford Online", "name_fa": "استنفورد"},
    {"id": "oxford", "name_en": "Oxford ML", "name_fa": "آکسفورد"},
    {"id": "cme", "name_en": "CME Education", "name_fa": "CME"},
    {"id": "eia", "name_en": "EIA Data", "name_fa": "EIA"},
    {"id": "bis", "name_en": "BIS Research", "name_fa": "BIS"},
    {"id": "world_bank", "name_en": "World Bank Open Data", "name_fa": "بانک جهانی"},
    {"id": "nber", "name_en": "NBER Working Papers", "name_fa": "NBER"},
)

DESKS: tuple[str, ...] = (
    "GOLD_DESK",
    "OIL_DESK",
    "CRYPTO_UNIVERSE_DESK",
    "US_EQUITIES_DESK",
    "EU_EQUITIES_DESK",
    "ASIA_EQUITIES_DESK",
    "FOREX_DESK",
)


DESK_OF_HYP = {"H14": ["CRYPTO_UNIVERSE_DESK"], "H15": ["CRYPTO_UNIVERSE_DESK"], "H16": ["US_EQUITIES_DESK"],
               "H17": ["OIL_DESK"], "H18": list(DESKS), "H19": list(DESKS), "H20": list(DESKS),
               "H21": ["CRYPTO_UNIVERSE_DESK"], "H22": list(DESKS)}
PAPER_DESK = {"crypto": "CRYPTO_UNIVERSE_DESK", "gold": "GOLD_DESK", "oil": "OIL_DESK", "us": "US_EQUITIES_DESK",
              "eu": "EU_EQUITIES_DESK", "asia": "ASIA_EQUITIES_DESK", "fx": "FOREX_DESK"}


def _read(root: Path, rel: str) -> Any:
    try:
        return json.loads((root / rel).read_text(encoding="utf-8"))
    except Exception:
        return None


def run_science_to_desk_pipeline(root: Path | None = None) -> dict[str, Any]:
    """Stage 3: every stage is read from real artifacts (arXiv scout, strategy_lab registry, promotion switch,
    M49 lessons from closed paper trades). Sources with no connector are reported NOT_CONNECTED."""
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    ax = _read(root, "reports/grok/M44/arxiv_scout.json") or {}
    reg = (_read(root, "strategy_lab/registry.json") or {}).get("candidates", {})
    switch = _read(root, "reports/grok/PAPER/strategy_switch.json") or {"active": {}, "version": 0}
    papers = ax.get("papers_by_hypothesis") or {}
    scouts = []
    for src in GLOBAL_SOURCES:
        live = src["id"] == "arxiv" and ax.get("paper_count")
        scouts.append({"source_id": src["id"], "title_en": src["name_en"],
                       "status": f"LIVE ({ax.get('paper_count')} papers, {ax.get('generated_at')})" if live else "NOT_CONNECTED",
                       "paper_only": True})
    research = []
    for hid in sorted(DESK_OF_HYP, key=lambda h: int(h[1:])):
        r = reg.get(hid) or {}
        research.append({"artifact_id": hid, "name": r.get("name"), "sandbox_verdict": r.get("verdict", "NOT_RUN"),
                         "evidence": r.get("evidence"),
                         "papers": [{"arxiv_id": p["arxiv_id"], "title": p["title"], "url": p["url"]} for p in papers.get(hid, [])[:3]],
                         "module_target": "architecture.learning.walk_forward", "paper_only": True})
    ahos_applied = [{"module_id": f"switch:{k}", "applied": True, "weight": v, "live_promotion": False, "paper_only": True}
                    for k, v in (switch.get("active") or {}).items()]
    lessons_by_desk: dict[str, int] = {d: 0 for d in DESKS}
    try:
        from architecture.learning.lessons_ledger import LessonsLedger
        db = root / "data" / "mission_ledger" / "m49_lessons.sqlite"
        if db.is_file():
            led = LessonsLedger(db)
            try:
                for row in led.all_rows():
                    d = PAPER_DESK.get(str(getattr(row, "market", "")).lower())
                    if d and getattr(row, "source", "") == "paper_trader":
                        lessons_by_desk[d] += 1
            finally:
                led.close()
    except Exception:
        pass
    university = []
    for desk in DESKS:
        tested = [f"{h} {reg.get(h, {}).get('verdict', 'NOT_RUN')}" for h, ds in DESK_OF_HYP.items() if desk in ds]
        university.append({"desk": desk, "curriculum_modules": len(tested),
                           "real_trade_lessons": lessons_by_desk[desk],
                           "syllabus_fa": f"درس‌های {desk}: فرضیه‌های آزموده‌شده ({'، '.join(tested)}) و {lessons_by_desk[desk]} درس از معاملات کاغذی بسته‌شده.",
                           "paper_only": True})

    organs_snap = build_whole_ahos_organ_evolution_snapshot()
    organ_routes = []
    for organ in organs_snap.get("organs") or []:
        if not isinstance(organ, dict):
            continue
        organ_id = str(organ.get("organ_id") or "")
        organ_routes.append(
            {
                "organ_id": organ_id,
                "organ_title_fa": organ.get("organ_title_fa"),
                "scouted_discovery_title": organ.get("scouted_discovery_title"),
                "research_lab_validation": organ.get("research_lab_validation"),
                "university_curriculum_module_fa": organ.get("university_curriculum_module_fa"),
                "held_out_exam_score_pct": organ.get("held_out_exam_score_pct"),
                "route_status": "ADMITTED_SANDBOX",
                "paper_only": True,
            }
        )

    whole_ahos_organs = {
        "organs_covered_count": organs_snap.get("organs_covered_count", len(WHOLE_AHOS_ORGANS_8)),
        "organ_ids": organs_snap.get("organ_ids", list(WHOLE_AHOS_ORGANS_8)),
        "trading_only": organs_snap.get("trading_only", False),
        "average_university_exam_score_pct": organs_snap.get("average_university_exam_score_pct"),
        "summary_fa": organs_snap.get("summary_fa"),
        "organ_discovery_routes": organ_routes,
        "desks_also_trained": list(DESKS),
    }

    return {
        "schema": "ahos.science_to_desk_pipeline.v1",
        "paper_only": PAPER_ONLY,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live": False,
        "sources_count": len(GLOBAL_SOURCES),
        "stages": {
            "scouts": scouts,
            "research_institute": research,
            "ahos_applied": ahos_applied,
            "university_desk_training": university,
            "whole_ahos_organ_routing": organ_routes,
        },
        "whole_ahos_organs": whole_ahos_organs,
        "desks_trained": len(DESKS),
    }
