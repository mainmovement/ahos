# AHOS Supervision Architecture v2

**Effective:** 2026-09-12  
**Council:** Independent AHOS Oversight Council  
**Build agent:** Ahos cursor configuration (`bc-2773f4bf-6ae2-459f-82f0-44baa07d9500`)

## Core principle

```
EVENT-DRIVEN > SCHEDULE-DRIVEN
```

Scheduled cycles are for **operational pulse** and **strategic audit** only.  
Critical events trigger **immediate** review — no waiting for next timer.

---

## Four-layer model

```
┌─────────────────────────────────────────────────────────┐
│ L1  IMMEDIATE EVENT     │ PR/commit/security/Lane A/…   │
│     (event-driven)      │ → cycle on critical events    │
├─────────────────────────────────────────────────────────┤
│ L2  OPERATIONAL 30min   │ delta since last cycle        │
│     (scheduled)         │ STATUS: ALLOW|MONITOR|FIX|BLOCK│
├─────────────────────────────────────────────────────────┤
│ L3  STRATEGIC 4h        │ vision drift, debt, launch path│
│     (scheduled)         │ → BEST PATH correction        │
├─────────────────────────────────────────────────────────┤
│ L4  MILESTONE GATES     │ G0–G6 before major milestones │
│     (on-demand)         │ never "green tests = pass"    │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Immediate event supervision

### Critical events (review immediately)

| Category | Events |
|----------|--------|
| **Code** | new commit, branch, PR, PR update, merge attempt |
| **Architecture** | schema/DB, security, dependency, authority conflict |
| **Frozen** | Lane A or frozen-area modification |
| **Claims** | AGI/ACI, readiness, production/operational |
| **Quality** | test regression, significant failure, unexpected behavior |
| **Agent** | stop, stall, loop, repeated failed approach, scope expansion |
| **Integration** | provider/external-system change |
| **Noise guard** | file explosion, doc-only churn without trigger |

### Event sources

| Source | Mechanism |
|--------|-----------|
| GitHub PR activity | `cursor-subscriptions-subscribe_github_pr` scope `repo` |
| GitHub CI failure | `subscribe_github_ci` on active build branches |
| Timer miss | L2/L3 catches gaps |

### L1 cycle type

`CYCLE_EVENT_YYYYMMDD_HHMM.md` — short, focused, references delta only.

---

## Layer 2 — Operational supervision (30 minutes)

**Timer:** `ahos-oversight-operational-30m` (1800s)

### Scope (delta-first — never full rescan without cause)

1. Changes since previous cycle
2. Build agent state (RUNNING/IDLE/ERROR)
3. Active branch + open PRs
4. Recent commits (build agent branches)
5. Test signal (only if changed or triggered)
6. Current directive + blockers
7. Stall detection (no progress N cycles)

### Output STATUS

| Status | Meaning |
|--------|---------|
| `ALLOW` | Proceed as directed |
| `MONITOR` | Watch, no intervention |
| `FIX_BEFORE_CONTINUE` | Build agent must fix before more work |
| `BLOCK` | Stop specific action |
| `STOP` | Halt build agent until resolved |

### Noise reduction rules

- Do **not** re-read entire repo each cycle
- Do **not** repeat unchanged findings verbatim
- Deep inspection only when L1 event or STATUS escalation requires it
- Skip specialist full council unless material change detected

---

## Layer 3 — Strategic audit (4 hours)

**Timer:** `ahos-oversight-strategic-4h` (14400s)

### Questions

- Still aligned with Vision/Intent?
- Architecture drift?
- Implementation vs Intent gap growing?
- Technical debt vs capability growth?
- PR structure complexity?
- Tests → real confidence?
- Docs ↔ implementation sync?
- Readiness inflation?
- AGI/ACI claims ahead of evidence?
- Current path = best path to Launch?

### Output

`CYCLE_STRATEGIC_YYYYMMDD.md` + truth model delta + BEST PATH update if needed.

---

## Layer 4 — Milestone gates

Before major milestones, run gate review. **Tests green alone ≠ pass.**

| Gate | Focus |
|------|-------|
| **G0** | Vision / Truth alignment |
| **G1** | Architecture integrity (One Brain, Lane A, authority) |
| **G2** | Core engineering (pytest, freeze, imports) |
| **G3** | Integration (Py↔TS, Telegram gateway, providers) |
| **G4** | Operational readiness (soak, Windows gates, live edges) |
| **G5** | Security / reliability (S-01, overlay, fail-closed) |
| **G6** | Launch readiness (all gap artifacts, no inflation) |

Artifact: `docs/supervision/gates/GATE_GN_YYYYMMDD.md`

---

## Vision alignment (3 levels)

Every material change reviewed at:

1. **Technical correctness** — does code work?
2. **Architectural correctness** — right place in system?
3. **Project correctness** — should AHOS have this at all?

Level 3 blocks "correct but wrong capability."

---

## Build agent control

### PRE-FLIGHT (before material change)

- intended change, authority surface, reason
- expected behavior, risks, test plan

### POST-FLIGHT (after material change)

- actual diff, tests run, evidence artifacts
- unexpected behavior, unknowns, new risks

Missing POST-FLIGHT on material change → `FIX_BEFORE_CONTINUE`

---

## Readiness model (8 states)

```
DESIGNED → IMPLEMENTED → TESTED → VALIDATED → INTEGRATED → OPERATIONAL → PRODUCTION_READY → LAUNCH_READY
```

Each upgrade requires **specific evidence** — see `AHOS_PROJECT_TRUTH_MODEL.md`.

Fail-closed: insufficient evidence = `UNKNOWN`, never upgrade.

---

## Directive vocabulary

`ALLOW` · `MONITOR` · `DO` · `DO_NOT` · `FIX_BEFORE_CONTINUE` · `FIX_BEFORE_MERGE` · `BLOCK` · `STOP` · `ESCALATE_TO_HUMAN`

---

## Human authority required

- Irreversible / financial / live trading / destructive migration
- Security-sensitive authorization
- Launch declaration
- Frozen authority change
- Fundamental intent change

Council: `RECOMMEND → HUMAN AUTHORIZATION`

---

## Anti-overengineering filter

Every recommendation must pass:

- Necessary? Proportionate? Maintainable?
- Reduces risk? Materially improves AHOS?
- Can defer? Avoids architecture churn?

---

## Stall detection

Flag as `STALL / LOOP / DRIFT` when build agent:

- No meaningful progress ≥2 operational cycles
- Repeats same failure
- Similar PRs without convergence
- Fixture-only greening
- Scope expansion without directive

---

## Record schema (every cycle)

```
Timestamp | Trigger | Agent State | Branch | Changes | Tests | Evidence
Specialist Findings | Meta-Critique | Decision | Directive | Risk | Next Review
```

Path: `docs/supervision/cycles/`

---

## Subscriptions (active)

| Name | Interval | Layer |
|------|----------|-------|
| `ahos-oversight-operational-30m` | 1800s | L2 |
| `ahos-oversight-strategic-4h` | 14400s | L3 |
| `ahos-oversight-github-pr` | event | L1 |
| ~~`ahos-agent-supervision-hourly`~~ | retired | — |

---

## Launch question (final filter)

> Does this decision move AHOS one real step toward **trustworthy Launch**?

Not: prettier PR, more tests, more complex code.

Yes: real, executable, provable, vision-aligned capability.
