#!/usr/bin/env python3
"""Automatic diagnostic findings (W37 phase 5) + finding->proposal (phase 6).

Derives ACTIONABLE findings from a canonical health snapshot:

  * repeated provider failure
  * rising UNKNOWN share
  * score drift
  * calibration degradation (a previously-DESCRIPTIVE_OK artifact gone
    INSUFFICIENT_DATA, or a schema change)
  * benchmark regression
  * storage growth anomaly
  * architecture cycle
  * orphan candidate
  * test regression

Every finding carries: finding_id, severity, subsystem, evidence, timestamp,
provenance, guard state, recommended investigation, and whether it is
actionable internally / requires human governance / requires external action.

findings_to_proposals(): a sufficiently actionable finding can produce a
GOVERNED proposal candidate through the canonical SelfEvolutionEngine —
never approved automatically, always requires the human gate.

Deduplication: propose_for_finding checks the proposals directory; if an
OPEN (non-terminal) proposal with the same `diagnosis_finding_id` exists it
returns EXISTING_PROPOSAL with a link instead of creating a duplicate.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SEVERITY = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
PRIORITY = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

#: Confidence -> evidence-strength rank (W38 Candidate D). OBSERVED evidence
#: is stronger than DERIVED; CORRELATED is weaker still (never causal);
#: UNKNOWN is weakest. Used to adjust severity into priority.
CONFIDENCE_RANK = {"OBSERVED": 3, "DERIVED": 2, "CORRELATED": 1, "UNKNOWN": 0}
_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _priority_of(severity: str, confidence: str) -> str:
    """Deterministic severity->priority with an evidence-strength modifier:

      priority = severity, downgraded one step when the evidence is weak
      (CORRELATED or UNKNOWN). OBSERVED/DERIVED evidence keeps the severity
      as-is — severity already encodes importance, so it is never
      double-counted. The formula is fixed (never tuned) and documented; the
      priority is DERIVED from severity+confidence, never an independent
      opinion.
    """
    s = _SEVERITY_RANK.get(severity, 1)
    c = CONFIDENCE_RANK.get(confidence, 0)
    rank = s - 1 if c <= 1 else s   # CORRELATED / UNKNOWN evidence weakens
    return PRIORITY[max(0, min(3, rank))]


@dataclass
class DiagnosticFinding:
    finding_id: str
    kind: str                       # PROVIDER_FAILURE | UNKNOWN_GROWTH | SCORE_DRIFT | CALIBRATION_DEGRADATION | BENCHMARK_REGRESSION | STORAGE_ANOMALY | ARCHITECTURE_CYCLE | ORPHAN | TEST_REGRESSION
    severity: str
    subsystem: str
    evidence: str
    timestamp_utc: str
    confidence: str                 # OBSERVED | DERIVED | CORRELATED | UNKNOWN
    guard_state: str | None = None
    recommended_investigation: str = ""
    actionable_internally: bool = False
    requires_governance: bool = False
    requires_external: bool = False
    priority: str = "MEDIUM"        # W38 D: derived from severity + confidence

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _finding(kind: str, severity: str, subsystem: str, evidence: str,
             ts: float, confidence: str, guard: str | None = None,
             investigation: str = "", internal: bool = False,
             governance: bool = False, external: bool = False) -> DiagnosticFinding:
    fid = hashlib.sha256(f"{kind}:{evidence}".encode("utf-8")).hexdigest()[:12]
    return DiagnosticFinding(
        finding_id=fid, kind=kind, severity=severity, subsystem=subsystem,
        evidence=evidence, timestamp_utc=_utc(ts), confidence=confidence,
        guard_state=guard, recommended_investigation=investigation,
        actionable_internally=internal, requires_governance=governance,
        requires_external=external,
        priority=_priority_of(severity, confidence),
    )


def derive_findings(health: dict[str, Any], graph: dict[str, Any] | None = None,
                    now: float | None = None,
                    experiment_ledger: Any | None = None) -> list[DiagnosticFinding]:
    """Derive deterministic findings from a health snapshot (dict form, as
    produced by HealthSnapshotEngine.generate_snapshot / the package).

    experiment_ledger: optional ExperimentLedger used for recurrence
    detection (W39 P14): a finding whose recommended investigation matches a
    previously-attempted change is marked RECURRING_FINDING so the same
    failed optimization is not proposed again blindly.
    """
    ts = time.time() if now is None else now
    out: list[DiagnosticFinding] = []
    so = health.get("self_observation", {})

    # 1. provider failures
    pf = so.get("provider_failure_rates", {})
    if isinstance(pf, dict) and pf.get("total_failure_events"):
        n = pf["total_failure_events"]
        out.append(_finding(
            "PROVIDER_FAILURE", "MEDIUM" if n < 10 else "HIGH",
            "architecture/collector",
            f"{n} durable provider failure event(s): {pf.get('by_provider_kind')}",
            ts, "OBSERVED", guard="provider_failure_events table",
            investigation="check provider_failure_events and breaker state; "
                          "verify egress or provider status",
            internal=True, external=n >= 10))

    # 2. UNKNOWN share
    comp = so.get("data_completeness", {})
    if isinstance(comp, dict) and comp.get("unknown_share") is not None:
        share = comp["unknown_share"]
        if share > 0.5:
            out.append(_finding(
                "UNKNOWN_GROWTH", "MEDIUM" if share < 0.8 else "HIGH",
                "architecture/providers",
                f"UNKNOWN share {share:.1%} of "
                f"{comp.get('production_observations')} observations",
                ts, "OBSERVED", guard="pre-declared 50% budget",
                investigation="identify which fields are UNKNOWN and which "
                              "provider could fill them",
                internal=True))

    # 3. score drift
    drift = so.get("score_drift", {})
    if drift.get("verdict") == "DRIFT_DETECTED":
        out.append(_finding(
            "SCORE_DRIFT", "MEDIUM", "architecture/learning",
            f"score stream drifted (ADWIN trigger at sample "
            f"{drift.get('first_trigger_at_sample')})",
            ts, "OBSERVED", guard="StreamingDriftDetector",
            investigation="time-segment calibration rates; investigate what "
                          "changed in the scoring population",
            internal=True, governance=True))

    # 4. calibration degradation (schema change or status flip)
    cal = so.get("calibration_state", {})
    latest = cal.get("latest_artifact") if isinstance(cal, dict) else None
    if latest and isinstance(latest, dict):
        status = latest.get("calibration_status")
        if status and status not in ("DESCRIPTIVE_OK", "INSUFFICIENT_DATA"):
            out.append(_finding(
                "CALIBRATION_DEGRADATION", "HIGH", "architecture/learning",
                f"calibration artifact {latest.get('artifact')} status "
                f"{status} (schema {latest.get('schema')})",
                ts, "OBSERVED", guard="calibration guards",
                investigation="inspect the calibration artifact and its "
                              "exclusion census",
                internal=True, governance=True))

    # 5. storage anomaly
    storage = so.get("storage_growth", {})
    if isinstance(storage, dict) and storage.get("total_bytes") is not None:
        tb = storage["total_bytes"]
        if tb > 4 * 1024**3:
            out.append(_finding(
                "STORAGE_ANOMALY", "MEDIUM", "data stores",
                f"total store size {tb/1024**3:.1f} GiB exceeds the 4 GiB "
                f"laptop bound",
                ts, "OBSERVED", guard="4 GiB pre-declared bound",
                investigation="review store growth and backup/rotation policy",
                internal=True))

    # 6. architecture cycle
    if graph and graph.get("cycles"):
        out.append(_finding(
            "ARCHITECTURE_CYCLE", "MEDIUM", "architecture",
            f"{len(graph['cycles'])} import cycle(s): {graph['cycles']}",
            ts, "OBSERVED", guard="architecture_graph",
            investigation="review cycle members; extraction to a neutral "
                          "module is the usual remedy",
            internal=True, governance=True))

    # 7. orphans
    orphans = []
    if graph and graph.get("isolated_modules"):
        orphans = graph["isolated_modules"]
    if orphans:
        out.append(_finding(
            "ORPHAN", "LOW", "architecture",
            f"{len(orphans)} isolated module(s): {orphans[:5]}...",
            ts, "OBSERVED", guard="architecture_graph",
            investigation="classify per ORPHAN_ANALYSIS policy; removal is "
                          "a governance decision",
            internal=True, governance=True))

    # 8. test regression
    test = so.get("test_health", {})
    for key in ("pytest", "validate"):
        entry = test.get(key)
        if entry and entry.get("present") and entry.get("exit_code") not in (0, None):
            out.append(_finding(
                "TEST_REGRESSION", "HIGH", "tests",
                f"{key} gate exit {entry.get('exit_code')}",
                ts, "OBSERVED", guard="committed gate artifact",
                investigation="read the gate output; fix the regression",
                internal=True))

    # 9. configuration drift (W37 P14): the config-health dimension in the
    #    snapshot reflects the validate_imports gate + offline-mode state; a
    #    degraded gate or an active offline mode is a config condition worth
    #    surfacing (never prints secret values — only status/evidence).
    cfg = so.get("config_health", {})
    if isinstance(cfg, dict) and cfg.get("status") == "DEGRADED":
        out.append(_finding(
            "CONFIG_DRIFT", "MEDIUM", "config",
            f"config health DEGRADED: {cfg.get('evidence')}",
            ts, "OBSERVED", guard="validate_imports env-key invariant",
            investigation="run scripts/validate_imports.py and fix the "
                          "documented/consumed env-key drift",
            internal=True))
    om = cfg.get("offline_mode") if isinstance(cfg, dict) else None
    if isinstance(om, dict) and om.get("active"):
        out.append(_finding(
            "CONFIG_DRIFT", "LOW", "config",
            "AHOS_OFFLINE_MODE=1 is active (external HTTP disabled)",
            ts, "OBSERVED", guard="AHOS_OFFLINE_MODE env",
            investigation="confirm offline mode is intentional; it is "
                          "currently observed state only",
            internal=False, external=True))

    # 10. benchmark regression
    bench = so.get("benchmark_health", {})
    if isinstance(bench, dict) and bench.get("baseline_present") is False:
        out.append(_finding(
            "BENCHMARK_REGRESSION", "LOW", "benchmarks",
            "no benchmark baseline artifact recorded",
            ts, "UNKNOWN", guard="benchmark_run.v1",
            investigation="run scripts/benchmark_performance.py run",
            internal=True))

    # W39 P14: recurrence detection — a finding whose recommended
    # investigation was already attempted (recorded in the experiment ledger)
    # is marked RECURRING_FINDING so the same failed change is not silently
    # re-proposed. Investigate why the previous intervention failed instead.
    if experiment_ledger is not None:
        try:
            for f in out:
                probe = (f.recommended_investigation or f.evidence)[:60]
                # a finding is RECURRING when a previously-recorded
                # hypothesis/change is a PREFIX of its investigation (the
                # recommended action overlaps what was already attempted)
                for rec in experiment_ledger.read_all():
                    for key in ("hypothesis", "attempted_change"):
                        prev = str(rec.get(key) or "")
                        if len(prev) >= 12 and probe.startswith(prev):
                            f.recommended_investigation = (
                                f"{f.recommended_investigation} "
                                "[RECURRING_FINDING: previously attempted — "
                                "investigate why it failed before re-proposing]")
                            break
                    else:
                        continue
                    break
        except Exception:
            pass

    # W38 Candidate D: return findings ordered by priority (highest first);
    # deterministic tie-break on (priority rank desc, kind, finding_id).
    return sorted(out, key=lambda f: (
        -_SEVERITY_RANK.get(f.priority, 1), f.kind, f.finding_id))


#: finding kind -> suggested leverage/impact for a candidate built from it.
#: Leverage encodes the intelligence-multiplication principle: a finding
#: whose fix strengthens several downstream layers outranks an isolated fix.
_KIND_LEVERAGE = {
    "PROVIDER_FAILURE": "HIGH",     # better data -> better evidence -> better scoring
    "UNKNOWN_GROWTH": "HIGH",       # fewer UNKNOWNs -> better features -> better calibration
    "SCORE_DRIFT": "HIGH",          # drift fix -> better calibration -> better learning
    "CALIBRATION_DEGRADATION": "HIGH",
    "BENCHMARK_REGRESSION": "MEDIUM",
    "STORAGE_ANOMALY": "MEDIUM",
    "ARCHITECTURE_CYCLE": "HIGH",   # less coupling -> better maintainability -> faster evolution
    "ORPHAN": "LOW",
    "TEST_REGRESSION": "HIGH",      # fixed gate -> better regression protection
    "CONFIG_DRIFT": "MEDIUM",
}


def candidates_from_findings(findings: list[DiagnosticFinding],
                             classification_override: dict[str, str] | None = None
                             ) -> list["ImprovementCandidate"]:
    """Derive improvement candidates from findings (W39): one candidate per
    finding, carrying the finding's evidence links and kind-derived leverage.
    Candidates are the input to ImprovementSelectionEngine.evaluate — the
    system can compare possible improvements WITHOUT implementing them.
    """
    from .selection import ImprovementCandidate, candidate_id

    out = []
    for f in findings:
        classification = KIND_TO_CLASSIFICATION.get(f.kind, "ARCHITECTURE")
        if classification_override and f.kind in classification_override:
            classification = classification_override[f.kind]
        out.append(ImprovementCandidate(
            candidate_id=candidate_id(f.evidence),
            finding_id=f.finding_id,
            classification=classification,
            subsystem=f.subsystem,
            problem=f.evidence,
            proposed_change=f.recommended_investigation,
            expected_benefit=f"resolve {f.kind}",
            evidence_links={"diagnostic_finding": f.finding_id},
            confidence=f.confidence,
            reversibility="HIGH",   # findings-derived changes are test-gated
            governance_requirement=f.requires_governance,
            benchmark_requirement=(f.kind == "BENCHMARK_REGRESSION"
                                   or f.kind == "SCORE_DRIFT"),
            validation_requirement="full pytest + regression report",
            leverage=_KIND_LEVERAGE.get(f.kind, "MEDIUM"),
            impact=f.priority,      # severity-derived priority is the impact proxy
        ))
    return out


def select_improvement(findings: list[DiagnosticFinding]) -> dict[str, Any]:
    """One-call convenience: findings -> candidates -> selection. The output
    is the single highest-value INTERNAL improvement candidate, or an honest
    INSUFFICIENT_EVIDENCE when nothing is comparable. Selection never
    approves or implements anything.
    """
    from .selection import ImprovementSelectionEngine

    candidates = candidates_from_findings(findings)
    return ImprovementSelectionEngine.evaluate(candidates)


#: finding kind -> proposal classification (W36 classification vocabulary)
KIND_TO_CLASSIFICATION = {
    "PROVIDER_FAILURE": "RELIABILITY",
    "UNKNOWN_GROWTH": "DATA_QUALITY",
    "SCORE_DRIFT": "LEARNING",
    "CALIBRATION_DEGRADATION": "LEARNING",
    "BENCHMARK_REGRESSION": "PERFORMANCE",
    "STORAGE_ANOMALY": "RELIABILITY",
    "ARCHITECTURE_CYCLE": "ARCHITECTURE",
    "ORPHAN": "ARCHITECTURE",
    "TEST_REGRESSION": "CORRECTNESS",
}

TERMINAL_STAGES = {"REJECTED", "ROLLED_BACK", "MONITORING", "DEPLOYED"}


def propose_for_finding(finding: DiagnosticFinding, *,
                        engine: Any = None,
                        proposals_dir: Path | str | None = None,
                        now: float | None = None) -> dict[str, Any]:
    """Convert a finding into a governed proposal candidate (phase 6).

    Deduplication: if a non-terminal proposal already references this
    finding_id, returns EXISTING_PROPOSAL with the existing id — no endless
    duplicate proposals. Otherwise creates a PROPOSED proposal via the
    canonical SelfEvolutionEngine (requires_human=True, never approved).
    """
    from .engine import SelfEvolutionEngine

    eng = engine or SelfEvolutionEngine()
    out_dir = Path(proposals_dir) if proposals_dir else eng.default_proposals_dir(ROOT)

    # dedup across persisted proposals
    if out_dir.is_dir():
        for path in sorted(out_dir.glob("prop_*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if data.get("current_stage") in TERMINAL_STAGES:
                continue
            links = data.get("evidence_links") or {}
            if links.get("diagnostic_finding") == finding.finding_id:
                return {"result": "EXISTING_PROPOSAL",
                        "proposal_id": data.get("proposal_id"),
                        "existing_artifact": path.name,
                        "finding_id": finding.finding_id}

    classification = KIND_TO_CLASSIFICATION.get(finding.kind, "ARCHITECTURE")
    prop = eng.create_proposal(
        detected_by="diagnostic-engine",
        diagnosis=f"[{finding.kind}] {finding.evidence[:120]}",
        proposed_by="diagnostic-engine",
        is_ai=True,                       # human gate mandatory
        target_scope="SHARED_INFRA",
        governance_touching=finding.requires_governance,
        # W38 E: proposal-quality requires a diff ref; a finding-derived
        # proposal references its own subsystem until a candidate diff is
        # prepared after approval (never applied to Lane A).
        candidate_diff_ref=(f"finding:{finding.finding_id} — candidate diff "
                            f"to be prepared for {finding.subsystem} after "
                            "approval; never touches Lane A"),
        test_battery=[],
        rollback_plan={"trigger": "finding persists after change",
                       "action": "revert the change"},
        analysis={
            "problem": finding.evidence,
            "evidence": f"finding {finding.finding_id} ({finding.confidence}) "
                        f"from health snapshot",
            "subsystem": finding.subsystem,
            "expected_benefit": "resolve the diagnostic condition",
            "risk": "change touches the affected subsystem; regression risk "
                    "mitigated by the test/benchmark gate",
            "affected_contracts": "see subsystem",
            "benchmark_baseline": "scripts/benchmark_performance.py run",
            "proposed_change": finding.recommended_investigation,
            "validation_method": "full pytest + benchmark compare + "
                                 "regression report",
        },
        classification=classification,
        evidence_links={"diagnostic_finding": finding.finding_id},
        now=now,
    )
    path = eng.save_proposal(prop, out_dir)
    return {"result": "CREATED", "proposal_id": prop.proposal_id,
            "artifact": path.name, "finding_id": finding.finding_id,
            "requires_human": True}


def main(argv: list[str] | None = None) -> int:
    import sys as _sys

    args = list(argv) if argv is not None else _sys.argv[1:]
    if len(args) != 1:
        print("usage: python -m architecture.evolution.findings "
              "<canonical_health_*.json>")
        return 2
    try:
        health = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}")
        return 2
    findings = derive_findings(health)
    if not findings:
        print("no diagnostic findings derived from this snapshot")
    for f in findings:
        print(f"[{f.severity:<7}] {f.kind}: {f.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
