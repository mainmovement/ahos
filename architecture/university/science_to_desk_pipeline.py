"""M57 Science scout -> Research Institute -> AHOS core -> University desk training. PAPER_ONLY."""
from __future__ import annotations

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


def run_science_to_desk_pipeline() -> dict[str, Any]:
    scouts = [
        {
            "source_id": s["id"],
            "title_en": f"{s['name_en']} signal batch",
            "status": "ADMITTED_SANDBOX",
            "paper_only": True,
        }
        for s in GLOBAL_SOURCES
    ]
    research = [
        {
            "artifact_id": f"RI-{s['id']}-2026",
            "sandbox_verdict": "VALIDATED_PAPER",
            "module_target": "architecture.learning",
            "paper_only": True,
        }
        for s in GLOBAL_SOURCES[:8]
    ]
    ahos_applied = [
        {
            "module_id": f"ahos.upgrade.{s['id']}",
            "applied": True,
            "live_promotion": False,
            "paper_only": True,
        }
        for s in GLOBAL_SOURCES[:6]
    ]
    university = []
    for desk in DESKS:
        university.append(
            {
                "desk": desk,
                "curriculum_modules": 4,
                "syllabus_fa": f"سیلابس آموزشی {desk}: الگوریتم‌های پذیرفته‌شده در مؤسسهٔ پژوهش، فقط کاغذی و بدون ارتقای زنده.",
                "paper_only": True,
            }
        )

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
