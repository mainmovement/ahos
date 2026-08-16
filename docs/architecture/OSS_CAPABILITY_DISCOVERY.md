# AHOS — OPEN-SOURCE CAPABILITY DISCOVERY (subsystem spec) + AG-25 spec
W12 PART E/F · status: DESIGNED + first read-only audit EXECUTED (reports/oss_capability_audit_1.json,
probe W12A-OSS-1) · no installation, no external side effects (PART O).

## 1. Constitutional law for external code
- GitHub Repository = **CANDIDATE** — never truth, never dependency.
- No repository enters production directly (law 8).
- No capability accepted on reputation (law 9) — claims need probe_id + evidence + test (law 10).
- Every change versioned, replayable, rollbackable (law 11).
- Unprovable ⇒ recorded UNKNOWN / UNVERIFIED / PARTIAL (law 12). No silent anything (law 13).

## 2. Capability lanes (discovery targets)
Multi-agent Systems · Agent Runtime · Workflow/Orchestration · Temporal · Event Sourcing ·
AI Routing · Model Evaluation · Long Context · RAG · Memory · Red Team · Security ·
Crypto Intelligence · On-chain analytics · Liquidity analysis · Risk engines · Backtesting ·
Replay · Fault Injection · Observability · PostgreSQL · Distributed systems · Self-healing ·
Autonomous systems.

## 3. Candidate pipeline (mandatory stage law)
DISCOVER → IDENTIFY → LICENSE AUDIT → SECURITY AUDIT → DEPENDENCY AUDIT →
MAINTENANCE/MATURITY AUDIT → ARCHITECTURE AUDIT → BENCHMARK → AHOS COMPARISON → RED TEAM →
REPLAY → CI → ImprovementProposal → HUMAN GATE → VERSIONED INTEGRATION.
- Stage-skipping ⇒ proposal INVALID (improvement_proposal_v1 law).
- Provenance/license/security not trustworthy ⇒ REJECT/UNVERIFIED.
- Not better than current implementation ⇒ NO_INTEGRATION (recorded, kept as evidence).

## 4. Evidence tiers for this subsystem (what each stage may use)
- Tier-1 (read-only now): public API metadata (license, stars, pushes, issues, org) — what the
  first audit used. Produces CANDIDATE registers only.
- Tier-2 (host-gated): source inspection in sandbox clone (no install), SBOM/dependency listing,
  license full-text check, test-suite presence.
- Tier-3 (owner-gated): benchmark execution inside quarantined sandbox env, replay vs AHOS
  baseline, CI pack — only these can lift a candidate past UNVERIFIED.

## 5. AG-25 — Open-Source Capability Intelligence (registry: PLANNED, ADVISORY)
Duties (10, per PART F): github discovery · repository ranking · capability extraction ·
license analysis · dependency/security analysis · architecture comparison · benchmark design ·
candidate scoring · improvement proposal generation · evidence packaging.
Authority: OBSERVE/ANALYZE/ADVISE ONLY — **no direct integration right**; promotion exclusively
via Governance/Red-Team/Human Approval. Failure law: untrusted provenance/license/security ⇒
REJECT/UNVERIFIED; not-better ⇒ NO_INTEGRATION. Registry entry live (ops block; orchestrated=false
honest). Principles bound: ENG-10 (license discipline), CRYPTO-11 (trust topology), SCI-01,
SEC-03 (provider-compromise realism applies to upstream code too).

## 6. First audit findings (read-only, 3 candidates — full JSON in reports/)
| Candidate | Lane | License | Verdict |
|---|---|---|---|
| temporalio/sdk-python | orchestration | MIT | NO_INTEGRATION (host-gated; aligns with target decision) |
| promptfoo/promptfoo | red team / model eval | MIT | CANDIDATE_HELD_UNVERIFIED (TS runtime boundary; revisit at host time) |
| crewAIInc/crewAI | multi-agent runtime | MIT | CANDIDATE_HELD_UNVERIFIED (persona-culture mismatch risk; audits pending) |
All maintenance/maturity signals ACTIVE (measured via API 2026-08-13). All security/dependency
postures UNVERIFIED by construction of read-only mode. Nothing integrated.

## 7. Loop closure (PART N master loop)
The self-reinforcing-but-governed loop now has both halves contracted: OSS discovery feeds
ImprovementProposal (same contract as AI-council proposals); both converge on the single human
gate; deployment is versioned; audit/rollback via versioned cards + run-ledger.
