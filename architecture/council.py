#!/usr/bin/env python3
"""AHOS W11 Lane-B — AI Advisory Council (contract ai_council_contract_v1).

Laws implemented:
- ADVISORY ONLY. The council never DECIDEs; output is a report, not a decision.
- NO averaging, NO blind majority vote, NO invented consensus.
- Categorical claim keys compared pairwise; DISAGREEMENT is a first-class verdict.
- INSUFFICIENT_EVIDENCE wins when evidence is thin.
- OFFLINE law: zero available providers => verdict INSUFFICIENT_EVIDENCE + council_status OFFLINE
  + deterministic floor ACTIVE (AHOS continues safely without any LLM).
- Red-team stage: numeric claims lacking evidence_refs => INVALID (ai_council redteam_verdicts).
- AI can never be an approver of anything; reports carry advisory_only=true.

No Lane-A imports (test-pinned). No network I/O — responses are injected envelopes.
Deterministic: same inputs => same report (given injected timestamps).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "ai_council_contract_v1.json"


def load_contract(path: str | Path = CONTRACT_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _claims_of(resp: dict) -> dict:
    """Categorical claims only (label -> category). Numbers are NOT comparable by averaging —
    they only participate through evidence_refs (numeric provenance law)."""
    return dict(resp.get("claims") or {})


def _agreement_matrix(responses: list[dict]) -> dict:
    """Pairwise categorical agreement per claim key. Never averages; records conflicts."""
    keys = set()
    for r in responses:
        keys |= set(_claims_of(r))
    matrix = {}
    for k in sorted(keys):
        vals = {}
        for r in responses:
            c = _claims_of(r)
            vals[r.get("provider", "?")] = c.get(k, "NO_CLAIM")
        distinct = set(vals.values()) - {"NO_CLAIM"}
        if len(distinct) > 1:
            state = "CONFLICT"
        elif len(distinct) == 1 and any(v == "NO_CLAIM" for v in vals.values()):
            state = "PARTIAL"          # some providers silent — not agreement
        elif len(distinct) == 1:
            state = "AGREE"
        else:
            state = "NO_EVIDENCE"
        matrix[k] = {"state": state, "positions": vals}
    return matrix


def _evidence_overlap(responses: list[dict]) -> dict:
    sets = {r.get("provider", "?"): set(r.get("evidence_refs") or []) for r in responses}
    shared = set.intersection(*sets.values()) if sets else set()
    union = set.union(*sets.values()) if sets else set()
    conflicts = []
    for r in responses:
        for contra in (r.get("contradicts") or []):
            conflicts.append({"provider": r.get("provider"), "contradicts": contra})
    return {"shared": sorted(shared), "union": sorted(union), "conflicts": conflicts}


def red_team(responses: list[dict]) -> list[dict]:
    """Deterministic red-team lints (verdicts enum from contract; probe-tagged)."""
    verdicts = []
    for r in responses:
        pid = r.get("provider", "?")
        numerics = r.get("numeric_claims") or []
        refs = r.get("evidence_refs") or []
        if numerics and not refs:
            verdicts.append({"target": pid, "verdict": "INVALID",
                             "probe_id": "REDTEAM-NUMERIC-PROVENANCE",
                             "reason": "numeric claims with empty evidence_refs"})
        for nc in numerics:
            if not nc.get("evidence_ref"):
                verdicts.append({"target": pid, "verdict": "INVALID",
                                 "probe_id": "REDTEAM-NUMERIC-PROVENANCE",
                                 "reason": f"untraced numeric claim: {nc.get('label', '?')}"})
        conf = (r.get("confidence") or "").upper()
        if conf in ("CERTAIN", "GUARANTEED", "PROVEN_BY_AI"):
            verdicts.append({"target": pid, "verdict": "REJECT",
                             "probe_id": "REDTEAM-CONFIDENCE-INFLATION",
                             "reason": f"unsupported confidence wording: {conf}"})
        if (r.get("authority_requested") or None) is not None:
            verdicts.append({"target": pid, "verdict": "REJECT",
                             "probe_id": "REDTEAM-AUTHORITY-LEAK",
                             "reason": "AI attempted to request authority — forbidden"})
    return verdicts


def run_council(*, artifact_ref: str, task_class: str, responses: list[dict],
                deterministic_checks: list[dict] | None = None,
                provider_health: dict | None = None, now: float | None = None,
                version: str = "council-W11") -> dict:
    """Full council protocol. responses must be validated provider envelopes.
    Returns a contract-shaped report; verdict in {CONSENSUS, DISAGREEMENT,
    INSUFFICIENT_EVIDENCE, NEEDS_MORE_DATA}."""
    contract = load_contract()
    now = time.time() if now is None else now
    checks = deterministic_checks or []
    health = provider_health or {}

    base = {"report_id": f"council-{int(now)}", "artifact_ref": artifact_ref,
            "task_class": task_class, "provider_responses": responses,
            "deterministic_checks": checks, "provider_health": health,
            "advisory_only": True, "version": version, "timestamp": now,
            "council_status": "ONLINE" if responses else "OFFLINE"}

    if not responses:
        return {**base, "verdict": "INSUFFICIENT_EVIDENCE",
                "deterministic_floor": "ACTIVE",
                "unresolved_questions": ["no AI provider available — council offline by design"],
                "agreement_matrix": {}, "evidence_overlap": {"shared": [], "union": [], "conflicts": []},
                "evidence_conflicts": [],
                "redteam": [], "note": "DETERMINISTIC_ONLY floor: AHOS continues safely"}

    rt = red_team(responses)
    tainted = {v["target"] for v in rt if v["verdict"] in ("INVALID", "REJECT")}
    valid = [r for r in responses if r.get("provider") not in tainted]
    matrix = _agreement_matrix(valid)
    overlap = _evidence_overlap(valid)
    conflicts = [k for k, v in matrix.items() if v["state"] == "CONFLICT"]
    evidence_thin = not overlap["union"] and all(not (r.get("evidence_refs")) for r in valid)

    if not valid:
        verdict, final = "ALL_RESPONSES_INVALIDATED", "INSUFFICIENT_EVIDENCE"
    elif conflicts:
        verdict, final = "CONFLICT_RECORDED", "DISAGREEMENT"
    elif evidence_thin:
        verdict, final = "EVIDENCE_THIN", "INSUFFICIENT_EVIDENCE"
    elif any(v["state"] in ("PARTIAL", "NO_EVIDENCE") for v in matrix.values()):
        verdict, final = "PARTIAL_POSITIONS", "NEEDS_MORE_DATA"
    else:
        verdict, final = "ALL_AGREE_WITH_EVIDENCE", "CONSENSUS"

    return {**base, "verdict": final, "verdict_detail": verdict,
            "responses_considered": [r.get("provider") for r in valid],
            "responses_invalidated": sorted(tainted),
            "agreement_matrix": matrix, "evidence_overlap": overlap,
            "evidence_conflicts": overlap["conflicts"], "redteam": rt,
            "unresolved_questions": ([f"conflicting claim: {k}" for k in conflicts] +
                                     ([f"invalidated provider output: {p}" for p in sorted(tainted)]) +
                                     ["consensus reported as agreement-with-evidence-overlap, never truth"]),
            "law": contract["law"]}


from .knowledge.anti_echo import AntiEchoEngine, EchoChamberAuditResult


def synthesize_multi_mind_council(
    *,
    artifact_ref: str,
    task_class: str,
    provider_responses: list[dict],
    lens_insights: list[dict] | None = None,
    deterministic_checks: list[dict] | None = None,
    provider_health: dict | None = None,
    now: float | None = None
) -> dict:
    """Full Multi-Mind + Multi-AI Council Synthesis (Phase XXII).
    Integrates: Evidence + Agent Analysis + Lens Insights + Model Outputs.
    Enforces Anti-Echo-Chamber correlation checks and strict evidence-over-consensus law.
    """
    now = time.time() if now is None else now
    lenses = lens_insights or []
    checks = deterministic_checks or []

    # 1. Base Council Run (Agreement Matrix, Overlap, Red Team)
    base_report = run_council(
        artifact_ref=artifact_ref,
        task_class=task_class,
        responses=provider_responses,
        deterministic_checks=checks,
        provider_health=provider_health,
        now=now,
        version="council-PhaseXXII"
    )

    # 2. Anti-Echo-Chamber Correlation & Monoculture Audit
    anti_echo_engine = AntiEchoEngine()
    ev_count = len(base_report.get("evidence_overlap", {}).get("union", []))
    echo_audit: EchoChamberAuditResult = anti_echo_engine.audit_responses(
        agent_or_model_responses=provider_responses,
        evidence_count=ev_count,
        min_required_evidence=1 if provider_responses else 0
    )

    # 3. Evidence Over Consensus Law:
    # If 10 models / lenses agree but evidence is weak -> REJECT / INSUFFICIENT_EVIDENCE
    final_verdict = base_report["verdict"]
    if echo_audit.epistemic_verdict == "INSUFFICIENT_EVIDENCE" or base_report["verdict"] == "INSUFFICIENT_EVIDENCE":
        final_verdict = "INSUFFICIENT_EVIDENCE"
    elif echo_audit.epistemic_verdict in ("MONOCULTURE_REJECT", "SUSPECTED_ECHO_CHAMBER") and final_verdict == "CONSENSUS":
        final_verdict = "DISAGREEMENT"  # Monoculture cannot claim true consensus

    return {
        **base_report,
        "verdict": final_verdict,
        "lens_insights_integrated": len(lenses),
        "lens_insights": lenses,
        "anti_echo_audit": {
            "correlation_score": echo_audit.correlation_score,
            "copied_reasoning_detected": echo_audit.copied_reasoning_detected,
            "source_monoculture_detected": echo_audit.source_monoculture_detected,
            "contrarian_thesis": echo_audit.contrarian_thesis,
            "epistemic_verdict": echo_audit.epistemic_verdict
        },
        "epistemic_law": "EVIDENCE > OPINION; consensus without empirical evidence yields INSUFFICIENT_EVIDENCE"
    }
def validate_report(rep: dict) -> list[str]:
    """Contract conformance + safety lints on a council report. [] = conformant."""
    contract = load_contract()
    errs: list[str] = []
    for f in contract["report_fields"]:
        if f not in rep:
            errs.append(f"missing report field: {f}")
    if rep.get("verdict") not in contract["council_verdicts"]:
        errs.append(f"verdict={rep.get('verdict')} not in council_verdicts enum")
    for v in rep.get("redteam") or []:
        if v.get("verdict") not in contract["redteam_verdicts"]:
            errs.append(f"redteam verdict={v.get('verdict')} not in enum")
        if not v.get("probe_id"):
            errs.append("redteam verdict without probe_id")
    if rep.get("advisory_only") is not True:
        errs.append("advisory_only must be true (council never DECIDES)")
    # no-averaging lint: verdict must never derive from numeric averaging of provider numbers
    if rep.get("verdict_method") == "average":
        errs.append("averaged verdicts are forbidden")
    return errs
