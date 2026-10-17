"""M49 lessons ledger: append-only hash chain, paper only.

A lesson is evidence. It never changes a gate, a limit, or HOLD.
UNVERIFIED lessons have retrieval weight 0. A review is a new row, not an edit.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

GENESIS = "0" * 64
STATUS_UNVERIFIED = "UNVERIFIED"
REVIEWER_QA = "16"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lesson (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    market TEXT NOT NULL,
    taxonomy TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    claim TEXT NOT NULL,
    counterfactual TEXT NOT NULL,
    status TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS ahos_guard_no_update_lesson
  BEFORE UPDATE ON lesson
  BEGIN SELECT RAISE(ABORT, 'append-only: lesson'); END;
CREATE TRIGGER IF NOT EXISTS ahos_guard_no_delete_lesson
  BEFORE DELETE ON lesson
  BEGIN SELECT RAISE(ABORT, 'append-only: lesson'); END;
"""


@dataclass(frozen=True, slots=True)
class Lesson:
    lesson_id: str
    source: str
    market: str
    taxonomy: str
    evidence_refs: tuple[str, ...]
    claim: str
    counterfactual: str
    status: str
    valid_from: str
    reviewer: str
    prev_hash: str
    entry_hash: str


def _canon(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _chain_hash(prev_hash: str, payload: dict) -> str:
    body = prev_hash + "\n" + _canon(payload)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _payload(row: Lesson) -> dict:
    return {
        "lesson_id": row.lesson_id,
        "source": row.source,
        "market": row.market,
        "taxonomy": row.taxonomy,
        "evidence_refs": list(row.evidence_refs),
        "claim": row.claim,
        "counterfactual": row.counterfactual,
        "status": row.status,
        "valid_from": row.valid_from,
        "reviewer": row.reviewer,
    }


class LessonsLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def append(
        self,
        *,
        lesson_id: str,
        source: str,
        market: str,
        taxonomy: str,
        evidence_refs: tuple[str, ...] | list[str],
        claim: str,
        counterfactual: str,
        valid_from: str,
        reviewer: str = "",
        status: str = STATUS_UNVERIFIED,
    ) -> Lesson:
        if status != STATUS_UNVERIFIED:
            raise ValueError("new lessons are UNVERIFIED")
        if reviewer:
            raise ValueError("a new lesson has no reviewer")
        refs = tuple(sorted(str(r) for r in evidence_refs))
        prev = self._head_hash()
        draft = Lesson(
            lesson_id=lesson_id,
            source=source,
            market=market,
            taxonomy=taxonomy,
            evidence_refs=refs,
            claim=claim,
            counterfactual=counterfactual,
            status=STATUS_UNVERIFIED,
            valid_from=valid_from,
            reviewer="",
            prev_hash=prev,
            entry_hash="",
        )
        entry_hash = _chain_hash(prev, _payload(draft))
        row = Lesson(
            lesson_id=draft.lesson_id,
            source=draft.source,
            market=draft.market,
            taxonomy=draft.taxonomy,
            evidence_refs=draft.evidence_refs,
            claim=draft.claim,
            counterfactual=draft.counterfactual,
            status=draft.status,
            valid_from=draft.valid_from,
            reviewer="",
            prev_hash=prev,
            entry_hash=entry_hash,
        )
        self._conn.execute(
            """INSERT INTO lesson (
                lesson_id, source, market, taxonomy, evidence_refs, claim,
                counterfactual, status, valid_from, reviewer, prev_hash, entry_hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row.lesson_id, row.source, row.market, row.taxonomy,
                json.dumps(list(row.evidence_refs), ensure_ascii=False),
                row.claim, row.counterfactual, row.status, row.valid_from,
                row.reviewer, row.prev_hash, row.entry_hash,
            ),
        )
        self._conn.commit()
        return row

    def review(self, lesson_id: str, *, reviewer: str, valid_from: str) -> Lesson:
        """Record a review as a new row. Only reviewer 16 may do this."""
        if reviewer != REVIEWER_QA:
            raise PermissionError("only reviewer 16 may mark a lesson reviewed")
        target = self.get(lesson_id)
        if target is None:
            raise KeyError(lesson_id)
        review_id = f"review:{lesson_id}:{valid_from}"
        return self._append_review(
            lesson_id=review_id,
            target_id=lesson_id,
            valid_from=valid_from,
        )

    def _append_review(self, *, lesson_id: str, target_id: str, valid_from: str) -> Lesson:
        prev = self._head_hash()
        draft = Lesson(
            lesson_id=lesson_id,
            source="review",
            market="meta",
            taxonomy="review",
            evidence_refs=(target_id,),
            claim="REVIEWED",
            counterfactual="review does not change any gate",
            status=STATUS_UNVERIFIED,
            valid_from=valid_from,
            reviewer=REVIEWER_QA,
            prev_hash=prev,
            entry_hash="",
        )
        # Review rows are still inserted as UNVERIFIED chain rows; the reviewer
        # field is what retrieval_weight reads. append() forbids a reviewer, so
        # the insert is local.
        entry_hash = _chain_hash(prev, _payload(draft))
        row = Lesson(
            lesson_id=draft.lesson_id,
            source=draft.source,
            market=draft.market,
            taxonomy=draft.taxonomy,
            evidence_refs=draft.evidence_refs,
            claim=draft.claim,
            counterfactual=draft.counterfactual,
            status=draft.status,
            valid_from=draft.valid_from,
            reviewer=REVIEWER_QA,
            prev_hash=prev,
            entry_hash=entry_hash,
        )
        self._conn.execute(
            """INSERT INTO lesson (
                lesson_id, source, market, taxonomy, evidence_refs, claim,
                counterfactual, status, valid_from, reviewer, prev_hash, entry_hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row.lesson_id, row.source, row.market, row.taxonomy,
                json.dumps(list(row.evidence_refs), ensure_ascii=False),
                row.claim, row.counterfactual, row.status, row.valid_from,
                row.reviewer, row.prev_hash, row.entry_hash,
            ),
        )
        self._conn.commit()
        return row

    def get(self, lesson_id: str) -> Lesson | None:
        cur = self._conn.execute("SELECT * FROM lesson WHERE lesson_id=?", (lesson_id,))
        raw = cur.fetchone()
        if raw is None:
            return None
        return _from_row(raw)

    def all_rows(self) -> list[Lesson]:
        cur = self._conn.execute("SELECT * FROM lesson ORDER BY id")
        return [_from_row(r) for r in cur.fetchall()]

    def visible(self, as_of: str) -> list[Lesson]:
        """Lessons whose valid_from is at or before as_of. Future rows stay hidden."""
        return [row for row in self.all_rows() if row.valid_from <= as_of and row.source != "review"]

    def retrieval_weight(self, lesson_id: str, *, as_of: str) -> float:
        subject = self.get(lesson_id)
        if subject is None or subject.valid_from > as_of:
            return 0.0
        if subject.status != STATUS_UNVERIFIED:
            return 0.0
        for row in self.all_rows():
            if (
                row.source == "review"
                and row.reviewer == REVIEWER_QA
                and lesson_id in row.evidence_refs
                and row.valid_from <= as_of
            ):
                return 1.0
        return 0.0

    def verify(self) -> bool:
        prev = GENESIS
        for row in self.all_rows():
            if row.prev_hash != prev:
                return False
            expect = _chain_hash(prev, _payload(row))
            if row.entry_hash != expect:
                return False
            prev = row.entry_hash
        return True

    def _head_hash(self) -> str:
        cur = self._conn.execute("SELECT entry_hash FROM lesson ORDER BY id DESC LIMIT 1")
        raw = cur.fetchone()
        if raw is None:
            return GENESIS
        return str(raw["entry_hash"])


def apply_gate(limit: float, _lessons: list[Lesson] | tuple[Lesson, ...]) -> float:
    """Lessons are not allowed to move a gate. The input limit is the output."""
    return float(limit)


def _from_row(raw: sqlite3.Row) -> Lesson:
    refs = json.loads(raw["evidence_refs"])
    return Lesson(
        lesson_id=raw["lesson_id"],
        source=raw["source"],
        market=raw["market"],
        taxonomy=raw["taxonomy"],
        evidence_refs=tuple(refs),
        claim=raw["claim"],
        counterfactual=raw["counterfactual"],
        status=raw["status"],
        valid_from=raw["valid_from"],
        reviewer=raw["reviewer"],
        prev_hash=raw["prev_hash"],
        entry_hash=raw["entry_hash"],
    )
