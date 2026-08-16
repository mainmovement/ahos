# AHOS MASTER DIRECTIVE v1 — PERMANENT OPERATING STATUS

- artifact: MASTER_DIRECTIVE_v1.md
- version: 1
- status: ACTIVE (authoritative status pointer: docs/canonical/master_directive_registry.json)
- ratified_utc: 2026-08-13T04:55:00Z — by OWNER directive, verbatim below (unedited, unabridged)
- relationship: REINFORCES the pre-existing Master Operating Contract (reality-first priority
  chain, two-lane law, freeze law, forbidden actions, E-01 gate discipline). No governance rule
  is weakened, narrowed, or reinterpreted by this directive or by its registration.
- on conflict: if a future OWNER-issued newer versioned doctrine conflicts with anything here or
  with the Master Operating Contract, the newer versioned doctrine wins — and the transition
  MUST be recorded in AHOS_ISSUE_REGISTER.md (R-series) in the SAME wave, with both sha256.
- change law: THIS FILE IS IMMUTABLE ONCE RATIFIED. Any doctrinal change = a NEW file
  MASTER_DIRECTIVE_v{n+1}.md + a registry transition (v{n} → SUPERSEDED, v{n+1} → ACTIVE) +
  a register entry. Silent change of doctrine = governance violation, CI-enforced
  (tests/test_master_directive.py).
- registration: R-42 (AHOS_ISSUE_REGISTER.md) · ledger phase P29 · pinned by CI.

---

## VERBATIM RATIFIED TEXT (OWNER, 2026-08-13)

PERMANENT OPERATING STATUS

This Master Directive is not a one-wave task prompt.

It is the permanent operating doctrine of AHOS.

Every future execution cycle, architecture change, experiment cycle,

agent creation, file modification, GitHub evaluation, AI-provider

evaluation, self-healing action, and self-evolution proposal must be

checked against this doctrine.

The doctrine remains active across future waves unless explicitly

superseded by a newer versioned Master Directive.

When a newer version exists:

OLD DOCTRINE → SUPERSEDED

NEW DOCTRINE → ACTIVE

Never silently change the doctrine.

Never silently weaken a governance rule.

Lane A continues independently while Lane B evolves.

At the beginning of every future wave:

1. VERIFY WORKSPACE

2. VERIFY MASTER VERSION

3. VERIFY EXPERIMENT STATE

4. VERIFY GOVERNANCE

5. VERIFY OPEN RISKS

6. SELECT HIGHEST-VALUE SAFE NEXT ACTION

7. EXECUTE

8. TEST

9. RED TEAM

10. VERIFY

11. RECORD

12. CONTINUE

The goal is not to finish the roadmap once.

The goal is to operate AHOS according to the doctrine continuously.

---

## OPERATIONAL REGISTRATION (Project Lead — execution mechanics, not doctrine amendment)

1. VERSION SEMANTICS: doctrine text is immutable per version. ACTIVE/SUPERSEDED status lives ONLY
   in docs/canonical/master_directive_registry.json (exactly one ACTIVE; ACTIVE = highest version).
2. REGISTRATION LAW: every versioned directive's sha256 must appear in AHOS_ISSUE_REGISTER.md on
   the wave of its ratification. Unregistered doctrine = not in force and a CI failure.
3. WAVE PROTOCOL BINDING: the 12 steps above are executed and evidenced at every session/wave
   start before any other work; the verification facts are logged in the wave's ledger entry
   (PHASE_STATE.md + register).
4. SCOPE EXAMPLES (non-exhaustive binding list): Lane-A cycles, Lane-B architecture, agent
   creation/edits (agent_registry.yaml), contract edits, provider/AI evaluations (pal_probe,
   oss_audit), GitHub evaluations, self-healing actions, self-evolution proposals (PART K),
   and any file modification whatsoever.
5. FREEDOMS PRESERVED: nothing here grants new authority. The forbidden list (real money,
   LIVE trading, credential changes, Lane-A freeze, paid providers, irreversible deletion)
   remains exactly as bound by the Master Operating Contract, the laws, and owner orders.
