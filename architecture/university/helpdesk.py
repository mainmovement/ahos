"""Agent help desk. Advisory retrieval only. It cannot raise a decision or a certification."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from architecture.university.registry import ask_university
from config.paths import connect_sqlite_ro, get_knowledge_db_path, get_project_root


def _knowledge_hits(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    words = [w.lower() for w in query.split() if len(w) > 2][:6]
    if not words:
        return []
    db = get_knowledge_db_path()
    if not Path(db).is_file():
        return []
    conn = connect_sqlite_ro(db)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT claim_id, version, category, statement, provenance_sha256, author_source_id "
            "FROM knowledge_claims ORDER BY version DESC LIMIT 400"
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    hits = []
    for row in rows:
        text = str(row["statement"] or "").lower()
        if not any(w in text for w in words):
            continue
        hits.append(
            {
                "claim_id": row["claim_id"],
                "version": row["version"],
                "category": row["category"],
                "statement": str(row["statement"])[:400],
                "provenance_sha256": row["provenance_sha256"],
                "author_source_id": row["author_source_id"],
            }
        )
        if len(hits) >= limit:
            break
    return hits


def ask(query: str, *, root: Path | None = None) -> dict[str, Any]:
    """Help-desk entry for agents. Wraps ask_university and the knowledge store."""
    base = Path(root) if root else get_project_root()
    uni = ask_university(query, root=base)
    return {
        "schema": "ahos.university.helpdesk.v1",
        "paper_only": True,
        "decides": False,
        "authority": "ADVISORY_ONLY",
        "query": query,
        "asku_ref": uni.get("asku_ref"),
        "sufficient_university_claims": uni.get("sufficient_claims"),
        "top_university_claims": uni.get("top_claims") or [],
        "knowledge_hits": _knowledge_hits(query),
        "honesty": "Citations are retrieval. They do not promote a strategy or certify an agent.",
    }
