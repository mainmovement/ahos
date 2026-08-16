# 15-AGENT COUNCIL — WAVE-7 DECISION LOG (Deliverable K) — 2026-08-11
# Real review loop: PROPOSAL → CRITIC → QUANT → SECURITY → RED TEAM → QA → AUDITOR → decision.
# Disagreements are recorded, not smoothed over. Roster: docs/canonical/AGENT_COUNCIL.md.

## D1 Telegram authority: AI-first vs deterministic-first
Producer(Architect): parser+dispatcher deterministic-first; AI advisory polish only.
Critic(AI/ML Eng): argued LLM-first routing for coverage of long-tail Persian phrasing.
Security(Cybersec): VETO on LLM-first for any finite-impact action (tool-call injection surface);
ledger writes must be unreachable from AI.
Red Team: demonstrated ambiguity case («نصفش رو بفروشم؟» is a QUESTION, not an order) —
proves guessing risk. Decision: DETERMINISTIC-FIRST ADOPTED; INFO_ONLY intents test-pinned;
LLM-first deferred to design review after Phase-6 mileage. DISAGREEMENT RECORDED: AI/ML Eng
dissent noted (coverage concern valid; mitigation = UNKNOWN→clarify UX, logged for learning set).

## D2 Free-AI reality check (pollinations 402)
Producer(Data Eng): keyless pollinations drafted as chain #2.
QA probe (PRB-20260811-AI-001 + direct GET): HTTP 402 — keyless tier GONE.
Decision: removed from chains same-day; registry keeps a visible REFUTED comment; matrix updated;
no silent replacement. Status honesty: AI layer = C Tested with DETERMINISTIC_ONLY as the verified
operating mode from sandbox. This is the §21/§26 discipline applied to AI.

## D3 H20 strict vs relaxed
Quant: proposed registering H20 as ≥3-of-4 (higher expected incidence).
Critic(Statistician): relaxation AFTER seeing incidence would be threshold-mining; strict 4-of-4
is the honest pre-registration; if incidence≈0 the card dies with a recorded reason (= success).
Decision: STRICT registered; relaxation would require a NEW card (H21) with its own budget.
No dissent remaining after multiplicity-budget math shown.

## D4 Uploads exact-dupes: autonomous archive vs user wait
Wave-6 deferred 3 exact-dup groups to the user; directive §10 now grants council autonomy for
obvious exact dupes. Security asked for reversibility proof. Decision: ARCHIVE (not delete),
pre/post sha verification in manifest — 11/11 OK; idempotency gate added after Auditor caught a
re-planning bug (archived files re-entered the dup groups; fixed + re-verified plan=0).
(Auditor finding resolved same-wave; policy v2 §4 amended: *_archive_* paths excluded from planning.)

## D5 GoPlus EVM re-probe upgrade
R-13 marked goplus DEGRADED (timeout ×3). Wave-7 battery: PRB-20260811-004 OK 361ms.
Decision: reachability upgraded to live-verified-2026-08-11 in providers.yaml (probe id recorded);
EVM security coverage widens in Phase-3 sweeps; single-OK probes are NOT stability claims
(daily probes continue; breaker/cooldown config unchanged).

## D6 Materializer direction-law check
Red Team: verify gluing features+outcomes in one module doesn't violate L2 (feature_store must not
import outcomes). QA: grep-verified + existing architecture test passes; materialize is a caller of
both, not an import edge between them. Decision: ACCEPTED; 80-test CI green (exit 0) is the evidence.

## Sign-off
Architect ✓ Quant ✓ Critic ✓ Security ✓ Red Team ✓ QA ✓ Auditor ✓ — items D1(dissent noted), D3
recorded with disagreement trail. All other items unanimous AFTER evidence was shown.
