# AHOS Agent Supervision Council

Supervisory layer for the **Ahos cursor configuration** cloud agent
(`bc-2773f4bf-6ae2-459f-82f0-44baa07d9500`).

## Mission

Review agent output across documentation, Persian/English copy, Python/TS code,
AGI/ACI governance, tests, and executability. Produce layered critique:

1. **Domain critique** — specialists flag issues and propose fixes
2. **Meta-critique** — council chair challenges proposals (cost, scope, false positives)
3. **Best path** — one prioritized action list for the supervised agent

## Cadence

- **Cycle interval:** every 1 hour while the supervised agent is active
- **Cycle artifacts:** `docs/supervision/cycles/CYCLE_NNN_YYYY-MM-DD.md`
- **Trigger:** cursor-subscriptions timer `ahos-agent-supervision-hourly`

## Specialist roster

| Role | Focus | Red flags |
|------|-------|-----------|
| **Documentation & Persian UX** | DOC_TRUTH_MAP, contracts, wave naming, bilingual operator copy | Missing authority index, W-label collisions, banned-claim drift |
| **Python Architecture & Boundaries** | Lane A freeze, identity/security fail-closed, knowledge isolation | Spoofable identity gates, scalar authority footguns, runtime wiring |
| **TypeScript / Web Read Model** | Command Center, canonicalBackend injection, STALE/UNAVAILABLE UX | Independent recommendation authority, empty-VM false greens |
| **AGI/ACI Governance** | Charter vs implementation, P5 namespace, capability matrix honesty | AGI/ACI packaging implying delivery, world-model mislabeling |
| **Test & Executability** | pytest ladder, CI gap, soak evidence, branch/main split | Fixture-only proof, static grep tests, STALE artifacts |
| **Security & Operations** | S-01 secrets, hooks vs real gates, operator readiness claims | Token rotation, OPERATOR_READY without evidence |
| **Chair (synthesis)** | Meta-critique, dedupe, prioritize | Scope creep, blocking merges without cause |

## Charter alignment (binding north-star)

Reference: `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`

Each cycle must verify the supervised agent respects:

| Charter | Gate |
|---------|------|
| §38 Lane A | No frozen evidence / Lane A edits |
| §39 72h Soak | No runtime/scoring/calibration interference without owner auth |
| §42 No Fake AGI | No AGI/ACI/world-model claims from file names or docs alone |
| §24–27 Execution stack | INTELLIGENCE → DECISION → RISK → PERMISSION → EXECUTION |
| §25 Auth levels | Current ceiling: L0 OBSERVE / L1 ANALYZE (PAPER_ONLY) |
| §48 Success | Measurable capability, not file/PR count |

**Ambition defines destination. Evidence determines progress. Governance controls power.**

## Per-cycle checklist

### A. Agent state

- [ ] Supervised agent status (RUNNING / IDLE / ERROR)
- [ ] Active branch and open PR chain
- [ ] Events since last cycle (PRs, artifacts, failures)

### B. Executability gate

```bash
python3 -B scripts/freeze_lane_a.py
python scripts/validate_imports.py
python3 -m pytest tests/ -q --tb=no
npm run typecheck && npm run lint
```

Record pass/fail counts. **2128+ passed** is baseline on current main.

### C. Domain scores (1–10)

Document, Architecture, AGI/ACI, Tests, Security — with top 3 issues each.

### D. Meta-critique rubric

For each proposed fix, ask:

- Is this a real authority bug or theoretical if module stays isolated?
- Does fixing it block current PR chain or can it be a follow-up slice?
- Does the fix match AHOS wave/PR naming conventions?
- Is there a cheaper guard (test + DOC_TRUTH_MAP) vs refactor?

### E. Best path output

Max **5** actions, ordered: **BLOCK** → **FIX_BEFORE_MERGE** → **FOLLOW_UP** → **MONITOR**.

## Supervised agent context

- **Repo:** `github.com/mainmovement/ahos`
- **Model:** cursor-grok-4.6-high-fast
- **Current work (2026-09-12):** W1 dossier merged (#94); W2 evidence graph + W3–W4
  identity-fusion PR chain open (#95–#103)
- **Classification:** INTEGRATION_READY — not OPERATOR_READY

## Non-goals

This council does **not** replace human PR review, edit Lane A, or merge PRs unless
explicitly instructed by the repository owner.
