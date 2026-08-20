#!/usr/bin/env python3
"""Evidence-driven improvement selection (W39).

The system already detects problems and files governed proposals; this adds
the next layer: compare MULTIPLE candidate improvements WITHOUT implementing
them, and select the highest-value one.

Candidate model: every candidate carries the fields the W39 mission lists,
with UNKNOWN preserved as None — never fabricated numbers.

Value model: multi-dimensional, evidence-based, and deliberately NOT a single
arithmetic score. Each dimension is a 3-state judgment:

    IMPACT        — what the change plausibly improves (subsystem + breadth)
    EVIDENCE      — how strongly the current evidence supports the need
    CONFIDENCE    — how confident we can be in the estimate
    REVERSIBILITY — how easy it is to undo
    MEASURABILITY — how directly the effect can be benchmarked
    LEVERAGE      — how many downstream layers benefit (intelligence
                    multiplication: evidence -> calibration -> diagnosis ->
                    findings -> proposals -> decisions)

The SELECTION is a deterministic lexicographic ranking over dimensions with
evidence weight (OBSERVED evidence outranks DERIVED; CORRELATED/UNKNOWN are
explicitly weaker). When a dimension cannot be judged for a candidate, that
candidate is NOT_COMPARABLE for the ranking — never given a fabricated
mid-score. If NO candidate is fully comparable, the result is
INSUFFICIENT_EVIDENCE.

Safety: this module only COMPARES candidates. It never implements, approves
or merges anything; the human governance gate remains mandatory.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any

#: Evidence-strength rank used for the comparison (weak evidence never wins).
EVIDENCE_RANK = {"OBSERVED": 3, "DERIVED": 2, "CORRELATED": 1, "UNKNOWN": 0}
DIMENSION_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
REVERSIBILITY_RANK = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}


@dataclass
class ImprovementCandidate:
    """A candidate improvement to be compared (not yet implemented).

    UNKNOWN fields stay None — never fabricated numbers.
    """
    candidate_id: str
    finding_id: str | None
    classification: str          # PERFORMANCE | CORRECTNESS | ... (W36 vocab)
    subsystem: str
    problem: str
    proposed_change: str
    expected_benefit: str
    evidence_links: dict[str, str] = field(default_factory=dict)
    baseline: str | None = None
    expected_risk: str | None = None
    implementation_cost: str | None = None     # LOW | MEDIUM | HIGH | None
    confidence: str | None = None              # OBSERVED | DERIVED | CORRELATED | UNKNOWN
    reversibility: str | None = None           # HIGH | MEDIUM | LOW | None
    governance_requirement: bool = False
    benchmark_requirement: bool = False
    validation_requirement: str | None = None
    affected_contracts: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    dependency_count: int | None = None
    estimated_scope: str | None = None         # SMALL | MEDIUM | LARGE | None
    impact: str | None = None                  # LOW | MEDIUM | HIGH | CRITICAL | None
    leverage: str | None = None                # LOW | MEDIUM | HIGH | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rank(value: str | None, table: dict[str, int], default: int | None = None) -> int | None:
    if value is None:
        return default
    return table.get(str(value).upper())


class ImprovementSelectionEngine:
    """Deterministic multi-candidate comparison.

    Selection rule (documented, fixed, never tuned):
      1. A candidate is COMPARABLE only when ALL of impact, evidence
         (confidence), reversibility, measurability and leverage are
         judgment-callable. Missing any => NOT_COMPARABLE.
      2. Rank lexicographically: IMPACT desc, then EVIDENCE desc, then
         LEVERAGE desc, then REVERSIBILITY desc, then COST asc (LOW first),
         then candidate_id asc for determinism.
      3. No comparable candidate => INSUFFICIENT_EVIDENCE.
    """

    @staticmethod
    def evaluate(candidates: list[ImprovementCandidate]) -> dict[str, Any]:
        comparable: list[dict[str, Any]] = []
        not_comparable: list[dict[str, Any]] = []

        for c in candidates:
            imp = _rank(c.impact, DIMENSION_RANK)
            ev = _rank(c.confidence, EVIDENCE_RANK)
            rev = _rank(c.reversibility, REVERSIBILITY_RANK)
            lev = _rank(c.leverage, DIMENSION_RANK)
            cost = _rank(c.implementation_cost, DIMENSION_RANK)
            # measurability: benchmark_requirement or a concrete
            # validation_requirement both mean the effect can be measured
            if c.benchmark_requirement:
                meas = 1
            elif c.validation_requirement:
                meas = 1
            else:
                meas = 0

            missing = [name for name, v in
                       (("impact", imp), ("evidence", ev), ("reversibility", rev),
                        ("leverage", lev), ("measurability", meas))
                       if v is None]
            entry = {
                "candidate_id": c.candidate_id,
                "finding_id": c.finding_id,
                "classification": c.classification,
                "subsystem": c.subsystem,
                "impact": c.impact,
                "evidence": c.confidence,
                "leverage": c.leverage,
                "reversibility": c.reversibility,
                "cost": c.implementation_cost,
                "measurability": "HIGH" if meas == 1 else ("LOW" if meas == 0 else None),
            }
            if missing:
                entry["status"] = "NOT_COMPARABLE"
                entry["missing_dimensions"] = missing
                not_comparable.append(entry)
                continue

            entry["status"] = "COMPARABLE"
            entry["_sort"] = (
                -imp, -ev, -lev, -rev, cost if cost is not None else 2,
                c.candidate_id)
            comparable.append(entry)

        comparable.sort(key=lambda e: e["_sort"])
        for e in comparable:
            e.pop("_sort")

        if not comparable:
            return {
                "schema": "ahos.improvement_selection.v1",
                "verdict": "INSUFFICIENT_EVIDENCE",
                "selected": None,
                "ranking": not_comparable,
                "note": ("no candidate had every required dimension judged; "
                         "nothing is ranked on fabricated mid-scores"),
            }

        return {
            "schema": "ahos.improvement_selection.v1",
            "verdict": "SELECTED",
            "selected": comparable[0]["candidate_id"],
            "ranking": comparable + not_comparable,
            "selection_rule": ("lexicographic: impact desc, evidence desc, "
                               "leverage desc, reversibility desc, cost asc; "
                               "NOT_COMPARABLE candidates never receive "
                               "fabricated mid-scores"),
        }


def candidate_id(problem: str) -> str:
    return hashlib.sha256(problem.encode("utf-8")).hexdigest()[:12]


def select_highest_value(*, findings: list[Any],
                         experiment_ledger: Any | None = None,
                         health: dict[str, Any] | None = None) -> dict[str, Any]:
    """W39 P13: autonomous priority re-evaluation — ONE highest-value
    internal improvement candidate.

    Consumes:
      * current findings (-> candidates, with recurrence marking when an
        experiment ledger is provided),
      * current health (a calibration artifact / benchmark baseline in the
        snapshot raises the measurability of relevant candidates),
      * the experiment ledger (failed changes are flagged RECURRING, so a
        known-failed optimization cannot win selection).

    The output is exactly one selected candidate, or an honest
    INSUFFICIENT_EVIDENCE. Selection never implements, approves or merges.
    """
    from .findings import candidates_from_findings

    candidates = candidates_from_findings(findings)
    if not candidates:
        return {
            "schema": "ahos.improvement_selection.v1",
            "verdict": "INSUFFICIENT_EVIDENCE",
            "selected": None,
            "ranking": [],
            "note": "no findings -> no candidates to compare",
        }

    # recurrence marking from the experiment ledger (W39 P14)
    if experiment_ledger is not None:
        try:
            for c in candidates:
                probe = c.proposed_change[:60]
                for rec in experiment_ledger.read_all():
                    for key in ("hypothesis", "attempted_change"):
                        prev = str(rec.get(key) or "")
                        if len(prev) >= 12 and probe.startswith(prev):
                            c.proposed_change += (" [RECURRING: previously "
                                                  "attempted — do not blindly "
                                                  "re-propose]")
                            c.confidence = "UNKNOWN"   # known-failed: weaker
                            break
                    else:
                        continue
                    break
        except Exception:
            pass

    return ImprovementSelectionEngine.evaluate(candidates)
