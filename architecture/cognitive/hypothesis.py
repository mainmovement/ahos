"""Persistent hypothesis records with fail-closed lifecycle.

IDs: HYP-000001 … sequential per store. JSONL append-only.
SUPPORTED requires a linked experiment_id. No silent promotion to knowledge.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .contracts import HypothesisState

ALLOWED_TRANSITIONS: dict[HypothesisState, frozenset[HypothesisState]] = {
    HypothesisState.PROPOSED: frozenset({
        HypothesisState.UNDER_REVIEW, HypothesisState.REJECTED, HypothesisState.UNCERTAIN,
    }),
    HypothesisState.UNDER_REVIEW: frozenset({
        HypothesisState.TESTING, HypothesisState.REJECTED, HypothesisState.UNCERTAIN,
        HypothesisState.SUPERSEDED,
    }),
    HypothesisState.TESTING: frozenset({
        HypothesisState.SUPPORTED, HypothesisState.WEAKENED, HypothesisState.REJECTED,
        HypothesisState.UNCERTAIN, HypothesisState.SUPERSEDED,
    }),
    HypothesisState.SUPPORTED: frozenset({
        HypothesisState.WEAKENED, HypothesisState.SUPERSEDED, HypothesisState.UNCERTAIN,
    }),
    HypothesisState.WEAKENED: frozenset({
        HypothesisState.TESTING, HypothesisState.REJECTED, HypothesisState.SUPERSEDED,
        HypothesisState.UNCERTAIN,
    }),
    HypothesisState.REJECTED: frozenset({HypothesisState.SUPERSEDED}),
    HypothesisState.UNCERTAIN: frozenset({
        HypothesisState.UNDER_REVIEW, HypothesisState.TESTING, HypothesisState.REJECTED,
        HypothesisState.SUPERSEDED,
    }),
    HypothesisState.SUPERSEDED: frozenset(),
}


class HypothesisTransitionError(ValueError):
    pass


@dataclass
class HypothesisRecord:
    hypothesis_id: str
    statement: str
    state: str
    created_ts: float
    updated_ts: float
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    domain: str = "COGNITIVE_CORE"
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class HypothesisStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> list[HypothesisRecord]:
        if not self.path.is_file():
            return []
        out: list[HypothesisRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            out.append(HypothesisRecord(**raw))
        return out

    def _rewrite(self, rows: list[HypothesisRecord]) -> None:
        payload = "\n".join(json.dumps(r.as_dict(), ensure_ascii=False, sort_keys=True) for r in rows)
        if payload:
            payload += "\n"
        self.path.write_text(payload, encoding="utf-8")

    def next_id(self) -> str:
        n = len(self._load_all()) + 1
        return f"HYP-{n:06d}"

    def propose(self, statement: str, *, domain: str = "COGNITIVE_CORE",
                provenance: dict[str, Any] | None = None,
                now: float | None = None) -> HypothesisRecord:
        ts = time.time() if now is None else now
        rec = HypothesisRecord(
            hypothesis_id=self.next_id(),
            statement=statement.strip(),
            state=HypothesisState.PROPOSED.value,
            created_ts=ts,
            updated_ts=ts,
            domain=domain,
            provenance=dict(provenance or {}),
        )
        if not rec.statement:
            raise ValueError("hypothesis statement required")
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec.as_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return rec

    def get(self, hypothesis_id: str) -> HypothesisRecord | None:
        for rec in self._load_all():
            if rec.hypothesis_id == hypothesis_id:
                return rec
        return None

    def transition(
        self,
        hypothesis_id: str,
        new_state: HypothesisState,
        *,
        experiment_id: str | None = None,
        evidence_ref: str | None = None,
        against: bool = False,
        now: float | None = None,
    ) -> HypothesisRecord:
        rows = self._load_all()
        idx = next((i for i, r in enumerate(rows) if r.hypothesis_id == hypothesis_id), None)
        if idx is None:
            raise KeyError(hypothesis_id)
        rec = rows[idx]
        current = HypothesisState(rec.state)
        allowed = ALLOWED_TRANSITIONS[current]
        if new_state not in allowed:
            raise HypothesisTransitionError(
                f"{rec.state} -> {new_state.value} forbidden"
            )
        if new_state == HypothesisState.SUPPORTED:
            exp_ids = list(rec.experiment_ids)
            if experiment_id:
                exp_ids.append(experiment_id)
            if not exp_ids:
                raise HypothesisTransitionError(
                    "SUPPORTED requires experiment_id (no untested promotion)"
                )
            rec.experiment_ids = exp_ids
        elif experiment_id:
            rec.experiment_ids = list(rec.experiment_ids) + [experiment_id]
        if evidence_ref:
            if against:
                rec.evidence_against = list(rec.evidence_against) + [evidence_ref]
            else:
                rec.evidence_for = list(rec.evidence_for) + [evidence_ref]
        rec.state = new_state.value
        rec.updated_ts = time.time() if now is None else now
        rows[idx] = rec
        self._rewrite(rows)
        return rec

    def attach_experiment(self, hypothesis_id: str, experiment_id: str) -> HypothesisRecord:
        rows = self._load_all()
        idx = next((i for i, r in enumerate(rows) if r.hypothesis_id == hypothesis_id), None)
        if idx is None:
            raise KeyError(hypothesis_id)
        rec = rows[idx]
        if experiment_id not in rec.experiment_ids:
            rec.experiment_ids = list(rec.experiment_ids) + [experiment_id]
            rec.updated_ts = time.time()
            rows[idx] = rec
            self._rewrite(rows)
        return rec
