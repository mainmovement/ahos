# E. SECURITY GATE DESIGN v0.1 — Mission v1.1 §9 — 2026-08-11
# LAW: Security can veto opportunity. UNKNOWN ≠ PASS. Veto precedes ranking.
# Code: discovery/security_gate.py (STEP 7). Verdict rows immutable (append-only, new supersede old by ts).

## 1. Gate order (deterministic evaluator)
```
INPUT: token_id, chain_id, address, evidence {provider check rows}  
STEP1 normalize evidence → check[] (per check: value TRUE|FALSE|UNKNOWN, severity CRITICAL|HIGH|INFO, provider, ts)
STEP2 any CRITICAL TRUE        → verdict=SECURITY_VETO (reasons listed)
STEP3 else unknown-critical ⇒ verdict=PASS_WITH_UNKNOWN (coverage recorded)  [recommendation cap ≤ WATCH]
STEP4 else                     → verdict=PASS (coverage=1.0 of available checks)
OUTPUT: security_verdict rows + gate_summary(token_id, ts, verdict, veto_reasons[], coverage, evidence_refs[])
```

## 2. Check registry (v1; registry, not hard-code)
| check_key | severity | chain | provider(s) | rule → TRUE means BAD |
|---|---|---|---|---|
| honeypot | CRITICAL | all | GoPlus† / RugCheck signals | cannot sell / sell-sim fail |
| sell_tax_extreme | CRITICAL | all | GoPlus† (>25% or dynamic) | tax abuse |
| blacklist_function | CRITICAL | EVM+SOL | GoPlus†/RugCheck | can freeze traders |
| mint_authority_active | CRITICAL | SOL | RugCheck (mintable) | hidden mint possible |
| freeze_authority_active | CRITICAL | SOL | RugCheck | balances freezable |
| lp_not_locked_fresh_pool | CRITICAL | all | RugCheck lpLockedPct==0 && age<7d | rug window |
| proxy_risk_upgradeable | HIGH | EVM | GoPlus† | drains possible |
| deployer_prior_rug | CRITICAL | all | RugCheck creator history / watchlist | repeat offender |
| ownership_renounced_absent | HIGH | EVM | GoPlus† owner alive | soft→veto only w/ mint |
| holder_concentration_high | HIGH | all | RPC Phase-3 | top10>50% (threshold lab-tested later) |
† GoPlus UNAVAILABLE from sandbox (probe A.3): adapter written, marked DEGRADED until probe passes;
  SOL tokens meanwhile always get RugCheck (VERIFIED) + UNKNOWN for GoPlus-only checks (never inferred).

## 3. UNKNOWN discipline (binding)
- Each check missing evidence ⇒ check row value=UNKNOWN with provider+reason; gate coverage = #resolved/#registered-for-chain.
- ANY UNKNOWN among CRITICAL set ⇒ verdict PASS_WITH_UNKNOWN and downstream recommendation ceiling = WATCH.
- Gate NEVER upgrades UNKNOWN→PASS silently; re-verification only with fresher evidence (new row, old kept).

## 4. Replayability & fixtures
- Veto fixtures: synthetic contracts emulating known patterns (honeypot sim response, mint-active RugCheck payload, LP-unlocked young pool, prior-rug creator) — target 100% veto on fixture set (Phase-3 exit; labeled FIXTURE forever, never "real scam detection rate").
- Raw provider responses → raw_payloads (sha256), verdict rows reference hashes.

## 5. Failure modes (council security role)
| Mode | Mitigation |
|---|---|
| Provider false-positive veto | verdict explains; user-visible; feedback register; no auto-un-veto |
| Provider compromised/wrong | two-provider rule planned Phase-3; single-provider verdicts carry confidence=MED |
| Evasion (fresh deployer, renamed contract) | similarity features DEFERRED; documented limitation |
| Rate-limit starvation | PAL breaker returns error_state; coverage drops honestly; recommendations cap themselves |
