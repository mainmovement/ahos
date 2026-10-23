"""Tests for M30 Canonical Memory Consolidation."""
from __future__ import annotations

from pathlib import Path

from architecture.learning.memory_consolidation import (
    consolidate_canonical_memory,
    verify_canonical_memory_chain,
)


def test_consolidate_canonical_memory_and_verify_hash_chain(tmp_path: Path) -> None:
    store_file = tmp_path / "canonical_memory_store.jsonl"
    snap_file = tmp_path / "memory_consolidation_snapshot.json"
    res = consolidate_canonical_memory(
        extra_records=[
            {
                "memory_id": "m49:dup-check",
                "origin_subsystem": "M49_LESSONS",
                "category": "lesson",
                "market": "GOLD",
                "summary": "first instance",
                "evidence_ref": "test",
            },
            {
                "memory_id": "m49:dup-check",
                "origin_subsystem": "M49_LESSONS",
                "category": "lesson",
                "market": "GOLD",
                "summary": "duplicate instance ignored",
                "evidence_ref": "test",
            },
        ],
        store_path=store_file,
        snapshot_path=snap_file,
    )
    assert store_file.is_file()
    assert snap_file.is_file()
    assert res["chain_ok"] is True
    assert res["total_entries"] >= 6

    entries = [dict(e) for e in res["entries"]]
    ok, count, msg = verify_canonical_memory_chain(entries)
    assert ok is True
    assert count == len(entries)
    assert msg == "CHAIN_VERIFIED"

    # Tamper with an entry and confirm chain verification catches it
    entries[0]["summary"] = "tampered summary"
    ok_tampered, _, msg_tampered = verify_canonical_memory_chain(entries)
    assert ok_tampered is False
    assert "mismatch" in msg_tampered
