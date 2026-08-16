# AHOS — AI ADVISORY COUNCIL + PROVIDER ROUTER (architecture)
W10 §7–§11 / W11 §10–§15 · contracts: ai_provider_contract_v1, ai_council_contract_v1 ·
code: architecture/provider_router.py + architecture/council.py (IMPLEMENTED, test-pinned) ·
config: config/ai_provider_registry.yaml

## 1. Constitutional position
AI is ADVISORY ONLY. The council is not a decision authority and can never become one:
- Contract enums make DECIDE/PROMOTE impossible for AI (agent registry pins: AI may only
  ANALYZE/ADVISE/CHALLENGE; only AG-15/AG-16 — deterministic — hold DECIDE).
- AI output may never become authoritative evidence, market data, numeric truth, financial
  decisions, governance changes, or frozen-rule modifications.
- AI cannot skip protocol steps, cannot self-approve code, cannot promote its own proposal.

## 2. Router (provider_router.py)
Routing chain per task: CAPABILITY FILTER → HEALTH → COST → CONTEXT → PROBE RESULTS → SELECTION.
- FREE_FIRST: cost=0 first where capability permits; paid providers excluded by default
  (allow_paid=false; cost budget explicit; provider registry: no paid dependency may appear silently).
- NO provider superiority is hard-coded. Strengths count only with probe_ref evidence
  (test: unprobed "best coding" claims lose to a probed free provider). "Claude best coding /
  Gemini best long context / ChatGPT best classification" are NOT believed — they are lanes
  waiting for AHOS task probes.
- Health law: availability=OK is not enough — a provider without a fresh probe is UNKNOWN and
  NOT routable (unprobed is not routable, test-pinned).
- Circuit breaker per provider: failures≥threshold ⇒ OPEN (excluded); cooldown ⇒ HALF_OPEN;
  success ⇒ CLOSED (implemented + tested; closes W10 finding F9's breaker leg).
- DETERMINISTIC FLOOR: no eligible provider ⇒ DETERMINISTIC_ONLY envelope — floor LIVE-VERIFIED
  (PRB-20260811-AI-001: all six tiers down/no-key in sandbox; system degraded gracefully).

## 3. Provider registry truth table (config/ai_provider_registry.yaml, all probe-anchored)
| Provider | cost | availability (measured) | evidence |
|---|---|---|---|
| ollama_local | $0 | NO_HOST | PRB-20260811-AI-001 network_error |
| github_models / groq / gemini_free / openrouter | $0 | NEEDS_USER_KEY | PRB-20260811-AI-001 no_key |
| pollinations_text | $0 | REFUTED (402 keyless dead) | PRB-20260811-AI-001 http_error |
| chatgpt/claude/gemini (paid targets) | DECLARED_PAID | NEEDS_USER_KEY, strengths UNPROBED | none — no claims |
Capabilities registered (9): code_reasoning, long_doc_audit, persian_nlp, classification_bulk,
adversarial_critique, numeric_care, architecture_reasoning, test_generation, failure_diagnosis.

## 4. Council protocol (council.py)
PROBLEM → diagnostic classification → router → INDEPENDENT provider responses (envelopes
validated: provider, model, probe_id, timestamp, input_hash, evidence_refs, confidence,
version) → evidence validation → disagreement analysis → red team → proposal/report.
Verdicts: CONSENSUS · DISAGREEMENT · INSUFFICIENT_EVIDENCE · NEEDS_MORE_DATA.
Hard laws (test-pinned):
- NO averaging, NO blind majority voting, NO invented consensus — agreement is reported WITH
  evidence overlap; "consensus ≠ truth" is a standing unresolved-question row in every report.
- Pairwise categorical agreement matrix; silent providers ⇒ PARTIAL ⇒ NEEDS_MORE_DATA.
- Numeric provenance: any AI number without evidence_refs ⇒ INVALID (red team), and the
  offending response is EXCLUDED from agreement analysis (never silently tolerated).
- Authority-leak attempt (AI requesting authority) ⇒ REJECT. Confidence inflation ⇒ REJECT.
- OFFLINE council ⇒ INSUFFICIENT_EVIDENCE + deterministic floor ACTIVE; AHOS continues.

## 5. Red Team (in-council stage today; AG-14)
Deterministic lints live now: numeric-provenance (INVALID), confidence-inflation (REJECT),
authority-leak (REJECT), each carrying probe_id. Verdict enum: REJECT/INVALID/
INSUFFICIENT_EVIDENCE/NEEDS_MORE_DATA. Red team vetoes CLAIMS/promotions — never rewrites
evidence. Fail-closed for promotions: red team down ⇒ no promotion proceeds.

## 6. Self-improvement loop (W11 §12) — contracted, governance-gated
DETECT → DIAGNOSE → AI COUNCIL → ImprovementProposal (improvement_proposal_v1) → BRANCH/SANDBOX
→ REPLAY → CI → RED TEAM → COUNCIL REVIEW → GOVERNANCE CHECK → HUMAN APPROVAL (mandatory when
governance-touching — validator-forced) → VERSION → DEPLOY → MONITOR → ROLLBACK.
Stage machine is contracted (14 stages); skip ⇒ INVALID; proposer-as-approver ⇒ INVALID;
Lane-A-targeted proposals ⇒ immediate REJECT. AI may diagnose/propose/write candidate code+tests/
critique; AI may NOT execute any stage alone.
