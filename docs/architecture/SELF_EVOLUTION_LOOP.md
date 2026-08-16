# AHOS — CONTROLLED SELF-EVOLUTION LOOP (W12 PART K)
Status: **DESIGNED + CONTRACTED (improvement_proposal_v1)** · enforcement pins: contract law
text + authority lints (CI) · live loop execution: BLOCKED_NO_HOST for sandbox-branch stages
(in-repo dry execution possible for Lane-B pure-Python candidates, evidence-tagged as such).
Supreme law: **AI → directly modify AHOS is FORBIDDEN** — contract law sentence: "AI may
diagnose/propose/write candidate code and tests/critique but may NEVER self-approve, NEVER
touch Lane A, and NEVER promote itself" (contracts/improvement_proposal_v1.json);
`target_scope` enum forces LANE_A_FORBIDDEN awareness; approvals rule: "AI identity may NEVER
be an approver"; validator FORCES requires_human=true when governance_touching=true.

## 1. The owner-mandated loop, stage-mapped (directive stage → AHOS machinery → status)
```
Observation           → cycle reports / probes / drift counters (Lane A + control plane ledger)   IMPLEMENTED (standing)
Diagnosis             → AG-14 (linted findings) / council advisory / human note                   PARTIAL (AG-14 PARTIAL)
Candidate Capability  → AG-25 OSS discovery (spec PART E/F) OR internal research                 PARTIAL (spec + 1st audit done)
ImprovementProposal   → contracts/improvement_proposal_v1.json (14 stages, no-skip law)           CONTRACTED + TESTED
Sandbox Branch        → isolated copy of Lane-B artifact set (manifest + RoStore discipline)      DESIGNED (host-grade isolation BLOCKED_NO_HOST)
Tests                 → pytest battery (current 198 + new-per-proposal, PART M discipline)        IMPLEMENTED
Replay                → REPLAY_PROBE / replay parity battery (frozen-window byte-identity)        IMPLEMENTED (Lane-A replay tests)
Benchmark             → baseline_stats + pre-registered thresholds (multiplicity budget aware)    IMPLEMENTED (B1/B2 machinery)
Red Team              → AG-14 + redteam_verdict stage in proposal (fail-closed for promotions)    CONTRACTED
Council               → architecture/council.py (advisory only; no votes/averages)                IMPLEMENTED + TESTED
Human Approval        → AWAITING_HUMAN → APPROVED (AI never approver; proposer never approver)    HUMAN GATE (never software)
Version               → registry matrix_version bump / versioned strategy cards only              IMPLEMENTED (versioning practiced)
Deploy                → Lane-B activation path; Lane-A changes only via frozen-card process       GOVERNED (P4 host-gated)
Audit                 → run-ledger + evidence pack + register entry (R-series append-only)        IMPLEMENTED (practiced W9–W12)
Rollback              → per-change rollback plan mandatory in proposal; f1_s1 rollback = exemplar IMPLEMENTED pattern (drill-proven exemplar)
```
Terminal stages of the contract: ROLLED_BACK / REJECTED / MONITORING — a proposal that cannot
reach MONITORING with evidence is a proposal that does not ship.

## 2. Connection to PART E pipeline (external capabilities)
GitHub/GitLab candidates never enter this loop directly: AG-25 (DISCOVERY→ANALYSIS→PROPOSAL)
emits an ImprovementProposal ONLY after the 15-stage OSS pipeline passes (license, security,
dependency, maintenance, architecture, benchmark, AHOS-comparison, red-team, replay, CI).
Untrusted provenance/license/security ⇒ REJECT/UNVERIFIED recorded; not-better-than-current ⇒
NO_INTEGRATION recorded (both are kept evidence, never deleted).

## 3. Connection to PART N master loop
This document is the governed inner loop of the master loop registered in
`docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` §7. The master loop may be
self-reinforcing in OBSERVATION only; every reinforcing WRITE passes this gate.
That sentence is the entire safety property, and it is contract-pinned.
