#!/usr/bin/env python3
"""Learning from failed improvements (W39 section 10) + knowledge compression
(section 11).

AHOS should remember not only what worked but what did NOT work, so the same
failed optimization is never rediscovered. This is a durable, append-only
experiment record:

    hypothesis -> baseline -> attempted change -> result -> failure reason
    -> reusable lesson

Result vocabulary (fixed, documented):
    IMPROVED / NO_MEANINGFUL_CHANGE / REGRESSION / NOT_COMPARABLE /
    INSUFFICIENT_DATA / GOVERNANCE_BLOCKED
Failure-reason vocabulary (for REGRESSION / NO_MEANINGFUL_CHANGE):
    OPTIMIZATION_BELOW_NOISE_FLOOR / NO_MEANINGFUL_GAIN /
    OUTPUT_PARITY_FAILED / REGRESSION_DETECTED / INSUFFICIENT_DATA /
    GOVERNANCE_BLOCKED

Persistence: append-only JSONL under proposals/experiments.jsonl (same
governance-adjacent area as proposals; no new subsystem, no vector DB —
SQLite/JSONL is the existing lightweight knowledge architecture).

record_experiment() never approves or implements anything: it only records.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

RESULTS = ("IMPROVED", "NO_MEANINGFUL_CHANGE", "REGRESSION", "NOT_COMPARABLE",
           "INSUFFICIENT_DATA", "GOVERNANCE_BLOCKED")
FAILURE_REASONS = ("OPTIMIZATION_BELOW_NOISE_FLOOR", "NO_MEANINGFUL_GAIN",
                   "OUTPUT_PARITY_FAILED", "REGRESSION_DETECTED",
                   "INSUFFICIENT_DATA", "GOVERNANCE_BLOCKED")


@dataclass
class ExperimentRecord:
    experiment_id: str
    hypothesis: str
    baseline: str
    attempted_change: str
    result: str                       # RESULTS vocabulary
    failure_reason: str | None = None # FAILURE_REASONS for non-improvements
    reusable_lesson: str = ""
    evidence_refs: list[str] = field(default_factory=list)   # benchmark/regression artifacts
    classification: str = "PERFORMANCE"
    subsystem: str = ""
    recorded_utc: str = ""
    sha256: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExperimentLedger:
    """Append-only JSONL ledger of optimization experiments (W39 §10/§11).

    record() computes the integrity sha256 over the record; a future reader
    can detect tampering. lookup() enables dedup: the same hypothesis +
    attempted change already recorded is returned as EXISTING, so a failed
    optimization is not silently retried.
    """

    def __init__(self, ledger_path: Path | str | None = None):
        self.path = Path(ledger_path) if ledger_path else (
            ROOT / "proposals" / "experiments.jsonl")

    def record(self, *, hypothesis: str, baseline: str, attempted_change: str,
               result: str, failure_reason: str | None = None,
               reusable_lesson: str = "", evidence_refs: list[str] | None = None,
               classification: str = "PERFORMANCE", subsystem: str = "",
               now: float | None = None) -> ExperimentRecord:
        if result not in RESULTS:
            raise ValueError(
                f"unknown experiment result {result!r}; "
                f"valid: {sorted(RESULTS)}")
        if failure_reason is not None and failure_reason not in FAILURE_REASONS:
            raise ValueError(
                f"unknown failure reason {failure_reason!r}; "
                f"valid: {sorted(FAILURE_REASONS)}")
        ts = time.time() if now is None else now
        rec = ExperimentRecord(
            experiment_id=hashlib.sha256(
                f"{hypothesis}:{attempted_change}".encode("utf-8")).hexdigest()[:12],
            hypothesis=hypothesis, baseline=baseline,
            attempted_change=attempted_change, result=result,
            failure_reason=failure_reason, reusable_lesson=reusable_lesson,
            evidence_refs=evidence_refs or [], classification=classification,
            subsystem=subsystem,
            recorded_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
        )
        rec.sha256 = hashlib.sha256(
            json.dumps({k: v for k, v in asdict(rec).items() if k != "sha256"},
                       sort_keys=True).encode("utf-8")).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec.as_dict(), sort_keys=True) + "\n")
        return rec

    def lookup(self, hypothesis: str, attempted_change: str) -> ExperimentRecord | None:
        """Dedup: return the existing record for the same hypothesis+change,
        or None. A failed optimization is thereby remembered, not retried."""
        want = hashlib.sha256(
            f"{hypothesis}:{attempted_change}".encode("utf-8")).hexdigest()[:12]
        for rec in self.read_all():
            if rec["experiment_id"] == want:
                return ExperimentRecord(**rec)
        return None

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out

    def count(self) -> int:
        return len(self.read_all())
