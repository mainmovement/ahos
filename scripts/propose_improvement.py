#!/usr/bin/env python3
"""AHOS governed improvement-proposal generator (evolution mission §4C).

Turns a detected weakness into a structured, persisted, reviewable proposal
via the canonical SelfEvolutionEngine — never an auto-approved change.

Every proposal carries the full review surface:
  problem, evidence, affected subsystem, expected benefit, risk,
  affected contracts, benchmark baseline, proposed change, validation
  method, rollback strategy, governance state.

Governance laws (enforced by architecture/evolution/engine.py, test-pinned):
  - AI proposals (is_ai=true, the default here) REQUIRE a human approval
    later; this tool NEVER approves anything.
  - target_scope=LANE_A_FORBIDDEN => proposal is born REJECTED.
  - A proposal without a rollback trigger cannot advance past CI_PASSED.

Usage:
    python scripts/propose_improvement.py --diagnosis "..." \\
        --problem "..." --evidence "..." --subsystem "architecture/..." \\
        --expected-benefit "..." --risk "..." --affected-contracts "..." \\
        --benchmark-baseline "..." --proposed-change "..." \\
        --validation-method "..." --rollback-trigger "..." --rollback-action "..."
    python scripts/propose_improvement.py --list

Exit codes:
    0 = proposal written (or list shown)
    2 = invocation error / missing required fields
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.engine import SelfEvolutionEngine  # noqa: E402

REQUIRED_ANALYSIS_FIELDS = (
    "problem", "evidence", "subsystem", "expected_benefit", "risk",
    "affected_contracts", "benchmark_baseline", "proposed_change",
    "validation_method",
)
# rollback strategy is enforced structurally (trigger/action) by the engine.


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS governed improvement proposal")
    ap.add_argument("--list", action="store_true",
                    help="list persisted proposals and exit")
    ap.add_argument("--proposals-dir", default=None,
                    help="proposals directory (default: <repo>/proposals)")
    ap.add_argument("--detected-by", default="arena-agent",
                    help="who detected the weakness (default: arena-agent)")
    ap.add_argument("--proposed-by", default="arena-agent",
                    help="who proposes (default: arena-agent)")
    ap.add_argument("--diagnosis", required=False,
                    help="one-line diagnosis (required unless --list)")
    ap.add_argument("--target-scope", default="B_ONLY",
                    choices=["B_ONLY", "SHARED_INFRA", "LANE_A_FORBIDDEN"],
                    help="affected scope; LANE_A_FORBIDDEN is born REJECTED")
    ap.add_argument("--governance-touching", action="store_true",
                    help="mark as governance-touching (forces human gate)")
    ap.add_argument("--classification", default="ARCHITECTURE",
                    choices=["PERFORMANCE", "CORRECTNESS", "DATA_QUALITY",
                             "INTELLIGENCE", "LEARNING", "ARCHITECTURE",
                             "RELIABILITY", "DOCUMENTATION", "SECURITY"],
                    help="proposal classification (W36 phase 5)")
    ap.add_argument("--evidence-link-health", default="",
                    help="health snapshot artifact reference that supports this proposal")
    ap.add_argument("--evidence-link-diagnostic", default="",
                    help="diagnostic finding reference that supports this proposal")
    ap.add_argument("--evidence-link-benchmark", default="",
                    help="benchmark baseline/diff artifact reference")
    ap.add_argument("--candidate-diff-ref", default="",
                    help="reference to the candidate diff (branch/PR/commit)")
    ap.add_argument("--test-battery", default="",
                    help="comma-separated test names that must pass")
    ap.add_argument("--rollback-trigger", default="",
                    help="condition that triggers rollback (required later)")
    ap.add_argument("--rollback-action", default="revert",
                    help="rollback action (default: revert)")
    # mission §4C analysis fields
    for field in REQUIRED_ANALYSIS_FIELDS:
        ap.add_argument(f"--{field.replace('_', '-')}", default="",
                        help=f"analysis: {field}")
    args = ap.parse_args(argv)

    engine = SelfEvolutionEngine()
    proposals_dir = args.proposals_dir or engine.default_proposals_dir(ROOT)

    if args.list:
        props = engine.list_proposals(proposals_dir)
        if not props:
            print("no proposals persisted yet")
            return 0
        for p in props:
            print(f"{p['proposal_id']}  {p['current_stage']:>18}  "
                  f"{p['created_ts']}  {p['diagnosis']}")
        return 0

    if not args.diagnosis:
        print("ERROR: --diagnosis is required (or use --list)")
        return 2

    analysis = {f: getattr(args, f) for f in REQUIRED_ANALYSIS_FIELDS}
    missing = [f for f, v in analysis.items() if not v]
    if missing:
        print("ERROR: analysis fields required but empty: "
              + ", ".join(missing))
        return 2

    evidence_links = {}
    for link_key, flag_val in (
        ("health_snapshot", args.evidence_link_health),
        ("diagnostic_finding", args.evidence_link_diagnostic),
        ("benchmark", args.evidence_link_benchmark),
    ):
        if flag_val:
            evidence_links[link_key] = flag_val

    prop = engine.create_proposal(
        detected_by=args.detected_by,
        diagnosis=args.diagnosis,
        proposed_by=args.proposed_by,
        is_ai=True,                       # agent proposals require a human gate
        target_scope=args.target_scope,
        governance_touching=args.governance_touching,
        candidate_diff_ref=args.candidate_diff_ref,
        test_battery=[t.strip() for t in args.test_battery.split(",") if t.strip()],
        rollback_plan={"trigger": args.rollback_trigger or "unset",
                       "action": args.rollback_action},
        analysis=analysis,
        classification=args.classification,
        evidence_links=evidence_links,
    )

    path = engine.save_proposal(prop, proposals_dir)
    print(f"proposal_id : {prop.proposal_id}")
    print(f"stage       : {prop.current_stage}")
    print(f"requires_human: {prop.requires_human}")
    print(f"classification: {prop.classification}")
    if prop.evidence_links:
        print(f"evidence_links: {prop.evidence_links}")
    print(f"artifact    : {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    print("NOTE: this tool only proposes. Approval requires an explicit human "
          "gate via SelfEvolutionEngine.advance_stage (never automatic).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
