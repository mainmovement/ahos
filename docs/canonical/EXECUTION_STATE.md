# AHOS CANONICAL — EXECUTION STATE (M5)

**What this file is:** the canonical pointer to the record that mechanises the Master
Directive's wave-opening verification. It is *not* a state report itself — the
machine-readable record under `reports/` is the report. This file says where to find it,
what it means, and what it must never be used for.

**Status: stable pointer.** The file does not carry state and therefore cannot go stale.
The dated, timestamped artifact it points at is the thing that goes stale — by design,
which is why a new one is written each run rather than this file being edited.

---

## Why this exists

`MASTER_DIRECTIVE_v1.md` (R-42, sha-pinned, CI-enforced by `tests/test_master_directive.py`)
mandates a **12-step wave protocol** at every session/wave start, and its OPERATIONAL
REGISTRATION §3 states the verification facts "are logged in the wave's ledger entry
(`PHASE_STATE.md` + register)".

That logging had never been mechanised. The five verification steps existed only in
doctrine prose and in a hand-written paragraph of the R-series entry, so every session
re-derived them by reading documents — the exact chat-prompt dependency M5 was created to
remove. `scripts/execution_state.py` composes them from facts the repository already holds.

## How to use it

At session start, before other work:

```bash
python scripts/execution_state.py
```

This prints a summary and writes a timestamped record to
`reports/execution_state_<UTC>.json` (append-only; never overwritten). Read that record
for steps 1–5, then continue the protocol from step 6 yourself.

## What the record contains

Directive steps 1–5, as computed facts:

| Step | Facts |
|---|---|
| 1 VERIFY WORKSPACE | branch, HEAD sha, working-tree cleanliness |
| 2 VERIFY MASTER VERSION | the five doctrine-registry laws — single ACTIVE/highest, no orphan files, sha matches disk, sha present in the issue register |
| 3 VERIFY EXPERIMENT STATE | persistence stores (integrity + row counts), Lane-A freeze integrity |
| 4 VERIFY GOVERNANCE | registry OK, Lane-A intact, both registers present |
| 5 VERIFY OPEN RISKS | open/resolved gap counts, owner-blocked list, implementable-now list |

Verdict vocabulary is deliberately `VERIFIED` / `DEGRADED` / `NOT_VERIFIED`. There is no
`PASS`: the gap register's own law forbids PASS without an artifact, and a description of
state is not an artifact of the thing described. `DEGRADED` means the record is complete
but the repository has a condition a session should notice (dirty tree, Lane-A drift,
store integrity). `NOT_VERIFIED` means a step could not be computed at all.

## What this record is NOT

This is binding, and `tests/test_execution_state.py` pins it:

- **Not authority.** It grants nothing, unlocks nothing, changes no maturity, permission,
  or trading control. It carries no field capable of authorising anything.
- **Not a mission selector.** Directive step 6 — SELECT HIGHEST-VALUE SAFE NEXT ACTION —
  remains a human choice. The `implementable_now` list repeats the gap register's own
  words; it never assesses or ranks.
- **Not a readiness claim.** It is not `OPERATOR_READY`, `PRODUCTION_READY`, or any
  readiness classification. Those live in `docs/FINAL_TRUTH_AUDIT.md` and require the
  evidence this record explicitly does not constitute.
- **Not a substitute for the registers.** It summarises them. `AHOS_GAP_REGISTER.md` and
  `AHOS_ISSUE_REGISTER.md` remain the authorities; if the record disagrees with either,
  the register is correct and the record has a bug.

## Honesty laws

- `UNKNOWN` beats invented. A fact that cannot be verified is recorded as not verified,
  never smoothed into a plausible-looking value.
- Missing persistence stores read `NO_DATA` — the honest state of a host that has never
  run the daemon — and are **not** scored as integrity failures.
- Artifacts are append-only. Reusing an explicit `--out` is refused without `--force`,
  so a new record cannot silently destroy a committed one (the M-GAP-036 lesson).
- Written as pinned UTF-8, because the record carries the repository's non-ASCII and
  cp1252 would corrupt it on a Windows host (the M-GAP-033 class).
- The gap-register parse reads the summary table only. Addendum prose is not counted, so
  `open_total` is a floor, not a census.

## Related

- Doctrine: `docs/canonical/MASTER_DIRECTIVE_v1.md` · registry: `docs/canonical/master_directive_registry.json`
- Implementation: `scripts/execution_state.py` · pins: `tests/test_execution_state.py`
- Gap record: `AHOS_GAP_REGISTER.md` M-GAP-040 (Addendum 2026-09-28 (9))
- Adjacent recorders (same discipline): `scripts/system_state_snapshot.py` (runtime state),
  `scripts/record_test_run.py` (command-run evidence)
