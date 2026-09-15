# Slice 2B — Deferred Semantics Requiring a Human/Council Decision

**Status:** OPEN decision gate · **Created:** 2026-09-15 (Remediation-03)
**Gate class:** semantic policy. Neither item is implementable unilaterally
without changing governance-visible behavior; both change *which commands
succeed*, which is owner-visible authority behavior.

---

## Decision 1 — D-08: how `ContradictionCase.affects_candidate_ids` is derived

**Today:** caller-chosen, length-1 (Slice-2B bound). A contradiction that
logically also affects sibling candidates sharing the same claims/evidence
silently spares them: they can promote while the named sibling is blocked.

| Option | Meaning | Risk |
|---|---|---|
| **A. Keep explicit caller-chosen lists** (status quo) | Challenger names every affected candidate | Silent spare of siblings (today's defect) |
| **B. Auto-derive candidates sharing any claim/evidence with `left/right`** | TCB computes and stores the full set | Over-blocking: a stylistic "contradiction" annotates unrelated knowledge and freezes it; derivation semantics need a rigor bar (what counts as sharing) |
| **C. Explicit list + TCB warning surface** | List stays caller-chosen; projections expose "potentially affected siblings" for human review without blocking | No automatic blocking change; review load on humans; warnings can be ignored |

**Recommendation:** Option C now (no blocking-behavior change; adds the
visibility the defect actually lacks), revisit Option B only with a defined
similarity bar. **Owner decision required before any blocking-semantics
change.**

---

## Decision 2 — D-19: delegation narrowing for `task_required=False` commands

**Today:** some commands (`REGISTER_AGENT`, `REVOKE_*`, `DELEGATE_AUTHORITY`,
`CREATE_TASK`) do not scope to a task. Because child grants must narrow to a
task, the operator's root grants for these commands are effectively
undelegatable — any future agent principal could never receive them.

| Option | Meaning | Risk |
|---|---|---|
| **A. Keep root-only** (status quo) | Suite of identity/authority operations stays operator-only | Future agent-principal automation needs new grant semantics (Slice 2C concern anyway) |
| **B. Add a second narrowing axis** (`task_id=None` children for explicitly allow-listed command types) | Delegation can cover task-less commands where policy says so | Widens authority algebra; an allow-list mistake mints undelegatable-by-design into delegatable — irreversible-looking behavior change |

**Recommendation:** Option A for Slice 2B. Task-less authority operations are
control-plane-meta and belong to the operator in this slice; redesign with the
multi-principal session model in Slice 2C. **Owner decision required before
any delegation-algebra change.**

---

## Standing rule

An agent may implement neither option silently. These two decisions change
governance-visible outcomes and are therefore surfaced, not executed.
