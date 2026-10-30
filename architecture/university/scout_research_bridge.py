"""Turn an M44 scout snapshot into one deduped ResearchTask. No code execution. PAPER_ONLY."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research_worker.protocol import PROTOCOL_VERSION
from research_worker.research_task import validate_research_task

SCOUT_REL = Path("reports") / "grok" / "M44" / "arxiv_scout.json"
OUT_REL = Path("reports") / "grok" / "M44" / "scout_research_tasks.json"


def _item_id(arxiv_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", arxiv_id)
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "a" + cleaned
    return ("arxiv" + cleaned.replace(".", "-"))[:64]


def dedupe_papers(snap: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    buckets = []
    buckets.extend((snap.get("papers_by_hypothesis") or {}).values())
    buckets.extend((snap.get("papers_by_pillar") or {}).values())
    for bucket in buckets:
        if not isinstance(bucket, list):
            continue
        for paper in bucket:
            if not isinstance(paper, dict):
                continue
            aid = str(paper.get("arxiv_id") or "").strip()
            if not aid or aid in seen:
                continue
            seen.add(aid)
            out.append(paper)
    return out


def build_research_task(papers: list[dict[str, Any]], *, limit: int = 8) -> dict[str, Any]:
    items = []
    for paper in papers[:limit]:
        title = re.sub(r"https?://\S+", "", str(paper.get("title") or paper.get("abstract_snippet") or "untitled"))[:240]
        items.append(
            {
                "item_id": _item_id(str(paper.get("arxiv_id") or "unknown")),
                "item_type": "OBSERVATION",
                "text": title,
                "provenance_ref": "m44-arxiv",
            }
        )
    task = {
        "protocol_version": PROTOCOL_VERSION,
        "task_id": "M44ScoutDedupe",
        "agent_context_id": "research-context.m44-scout",
        "mission_id": None,
        "objective": "Read deduped arXiv observations. Do not execute code and do not promote a hypothesis.",
        "supplied_items": items,
        "constraints": {
            "max_observations": max(1, len(items)),
            "max_claims": 0,
            "max_hypotheses": 0,
            "max_predictions": 0,
            "max_contradictions": 0,
            "max_experiments": 0,
            "max_reviews": 0,
        },
    }
    return validate_research_task(task)


def export_scout_research_tasks(root: Path) -> dict[str, Any]:
    root = Path(root)
    path = root / SCOUT_REL
    if not path.is_file():
        doc = {"schema": "ahos.m44_research_tasks.v1", "status": "NO_SCOUT_FILE", "code_execution": False, "send": "BLOCKED"}
    else:
        snap = json.loads(path.read_text(encoding="utf-8"))
        papers = dedupe_papers(snap)
        task = build_research_task(papers) if papers else None
        doc = {
            "schema": "ahos.m44_research_tasks.v1",
            "status": "DEDUPED" if task else "EMPTY_SCOUT",
            "papers_in": sum(len(v) for v in (snap.get("papers_by_hypothesis") or {}).values() if isinstance(v, list))
            + sum(len(v) for v in (snap.get("papers_by_pillar") or {}).values() if isinstance(v, list)),
            "papers_deduped": len(papers),
            "task": task,
            "code_execution": False,
            "decides": False,
            "send": "BLOCKED",
        }
    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
