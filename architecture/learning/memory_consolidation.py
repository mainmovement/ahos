"""M30 Canonical Memory Consolidation.
Consolidates M49 lessons, M58 self-evaluation records, and M35.1 Kian audit records into a single
deduplicated, SHA-256 hash-chained canonical memory store (`data/memory/canonical_memory_store.jsonl`).
Strictly PAPER_ONLY = True; memory records never auto-promote tiers or bypass risk gates.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from config.paths import get_project_root

GENESIS_HASH = "0" * 64


@dataclass(frozen=True, slots=True)
class CanonicalMemoryEntry:
    seq: int
    memory_id: str
    origin_subsystem: str  # "M49_LESSONS" | "M58_SELF_EVAL" | "M35_KIAN_AUDIT"
    category: str
    market: str
    summary: str
    evidence_ref: str
    timestamp_iso: str
    prev_hash: str
    entry_hash: str
    paper_only: bool = True


def _compute_entry_hash(payload_without_hash: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload_without_hash, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_canonical_memory_chain(entries: Sequence[Mapping[str, Any]]) -> tuple[bool, int, str]:
    """Verify the SHA-256 hash chain across all canonical memory entries."""
    prev = GENESIS_HASH
    for idx, row in enumerate(entries, start=1):
        if int(row.get("seq", -1)) != idx:
            return False, idx - 1, f"seq_mismatch_at_{idx}"
        if str(row.get("prev_hash") or "") != prev:
            return False, idx - 1, f"prev_hash_mismatch_at_{idx}"
        check_body = {k: v for k, v in row.items() if k != "entry_hash"}
        expected = _compute_entry_hash(check_body)
        if str(row.get("entry_hash") or "") != expected:
            return False, idx - 1, f"entry_hash_mismatch_at_{idx}"
        prev = expected
    return True, len(entries), "CHAIN_VERIFIED"


def consolidate_canonical_memory(
    *,
    root: Path | None = None,
    extra_records: Sequence[Mapping[str, Any]] | None = None,
    store_path: Path | None = None,
    snapshot_path: Path | None = None,
) -> dict[str, Any]:
    """Consolidate M49, M58, and M35.1 records into the canonical hash-chained memory store."""
    repo = root or get_project_root()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw_candidates: list[dict[str, Any]] = []

    # 1. Load M49 lessons snapshot
    m49_path = repo / "reports" / "grok" / "M49" / "lessons_snapshot.json"
    if m49_path.is_file():
        try:
            m49_data = json.loads(m49_path.read_text(encoding="utf-8"))
            for lesson in m49_data.get("lessons") or []:
                lid = str(lesson.get("id") or "")
                if not lid:
                    continue
                raw_candidates.append(
                    {
                        "memory_id": f"m49:{lid}",
                        "origin_subsystem": "M49_LESSONS",
                        "category": str(lesson.get("reason") or "trade_lesson"),
                        "market": str(lesson.get("market") or "GOLD").upper(),
                        "summary": f"{lesson.get('mistake', '')} -> {lesson.get('lesson', '')}",
                        "evidence_ref": str(lesson.get("sourceReplayId") or "reports/grok/M49/lessons_snapshot.json"),
                        "timestamp_iso": str(m49_data.get("generated_at") or now_iso),
                    }
                )
        except (OSError, json.JSONDecodeError):
            pass

    # 2. Load M58 self-evaluation snapshot
    m58_path = repo / "reports" / "grok" / "M58" / "self_eval_snapshot.json"
    if m58_path.is_file():
        try:
            m58_data = json.loads(m58_path.read_text(encoding="utf-8"))
            se = m58_data.get("selfEvaluation") or {}
            scorecards = se.get("scorecards") or []
            decisions = (scorecards[0].get("allDecisions") if scorecards else None) or []
            for dec in decisions:
                did = str(dec.get("id") or "")
                if not did:
                    continue
                raw_candidates.append(
                    {
                        "memory_id": f"m58:{did}",
                        "origin_subsystem": "M58_SELF_EVAL",
                        "category": str(dec.get("reviewState") or "REVIEWED"),
                        "market": str(dec.get("market") or "GOLD").upper(),
                        "summary": str(dec.get("rationaleSummary") or ""),
                        "evidence_ref": "reports/grok/M58/self_eval_snapshot.json",
                        "timestamp_iso": str(m58_data.get("generated_at") or now_iso),
                    }
                )
        except (OSError, json.JSONDecodeError):
            pass

    # 3. Load M35.1 / Kian message hub audit summary
    m35_path = repo / "reports" / "grok" / "M35" / "message_hub_snapshot.json"
    if m35_path.is_file():
        try:
            m35_data = json.loads(m35_path.read_text(encoding="utf-8"))
            hub = m35_data.get("messageHub") or {}
            for ch in hub.get("channels") or []:
                cname = str(ch.get("channel") or "")
                if not cname:
                    continue
                raw_candidates.append(
                    {
                        "memory_id": f"m35:{cname.lower().replace(' ', '_')}",
                        "origin_subsystem": "M35_KIAN_AUDIT",
                        "category": str(ch.get("status") or "AUDIT"),
                        "market": "GOVERNANCE",
                        "summary": f"Channel {cname}: status={ch.get('status')} lastError={ch.get('lastError') or 'none'}",
                        "evidence_ref": "reports/grok/M35/message_hub_snapshot.json",
                        "timestamp_iso": str(hub.get("generatedAt") or now_iso),
                    }
                )
        except (OSError, json.JSONDecodeError):
            pass

    if extra_records:
        for rec in extra_records:
            raw_candidates.append(dict(rec))

    # Deduplicate deterministically by memory_id while preserving order
    seen_ids: set[str] = set()
    chained_rows: list[dict[str, Any]] = []
    prev_hash = GENESIS_HASH

    for item in raw_candidates:
        mid = str(item.get("memory_id") or "").strip()
        if not mid or mid in seen_ids:
            continue
        seen_ids.add(mid)
        seq = len(chained_rows) + 1
        body = {
            "seq": seq,
            "memory_id": mid,
            "origin_subsystem": str(item.get("origin_subsystem") or "M30_MEMORY"),
            "category": str(item.get("category") or "GENERAL"),
            "market": str(item.get("market") or "GLOBAL"),
            "summary": str(item.get("summary") or ""),
            "evidence_ref": str(item.get("evidence_ref") or "canonical"),
            "timestamp_iso": str(item.get("timestamp_iso") or now_iso),
            "paper_only": True,
            "prev_hash": prev_hash,
        }
        ehash = _compute_entry_hash(body)
        full_row = {**body, "entry_hash": ehash}
        chained_rows.append(full_row)
        prev_hash = ehash

    chain_ok, verified_count, verify_msg = verify_canonical_memory_chain(chained_rows)

    target_store = store_path or (repo / "data" / "memory" / "canonical_memory_store.jsonl")
    target_store.parent.mkdir(parents=True, exist_ok=True)
    target_store.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in chained_rows),
        encoding="utf-8",
    )

    by_origin: dict[str, int] = {}
    for r in chained_rows:
        orig = r["origin_subsystem"]
        by_origin[orig] = by_origin.get(orig, 0) + 1

    snapshot_payload = {
        "schema": "ahos.memory_consolidation.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "store_path": "data/memory/canonical_memory_store.jsonl",
        "chain_ok": chain_ok,
        "chain_status": verify_msg,
        "total_entries": verified_count,
        "head_hash": prev_hash,
        "counts_by_origin": by_origin,
        "entries": chained_rows,
    }

    target_snap = snapshot_path or (repo / "reports" / "grok" / "M30" / "memory_consolidation_snapshot.json")
    target_snap.parent.mkdir(parents=True, exist_ok=True)
    target_snap.write_text(json.dumps(snapshot_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_payload
