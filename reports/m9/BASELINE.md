# M9 Part A — Truth Baseline (exact counts)

Recorded 2026-10-02. Every number below is from an actual run in this session,
not from documentation. Method: the `tests/` suite was partitioned into 11
batches and run one batch at a time (the Windows pytest suite cannot be run in
one go — one O(n^2) defect made that physically impossible, see below).

## Python — 2647 passed, 0 failed, 2 skipped, 1 xfailed

| batch | result |
|---|---|
| 00 | 193 passed, 1 skipped |
| 01 | 327 passed |
| 02 | 180 passed, 1 xfailed |
| 03 | 274 passed |
| 04 | 254 passed, 1 skipped |
| 05 | 327 passed |
| 06 | 269 passed |
| 07 | 179 passed |
| 08 | 220 passed |
| 09 | 318 passed |
| 10 | 106 passed |

Coverage: 184 test modules on disk, 184 run (the M9 module
`tests/test_m9_import_side_effects.py` was written after the batches were cut
and was run separately — 3 passed). Zero test files were skipped to make a
number look good.

### The one defect this exposed (fixed, with regression tests)

`architecture/scheduling/engine.py::audit_and_register_missed_windows` ran one
dedup probe per (token, snapshot slot) against `gap_register`, which carries no
index on `(token_id, kind)`. Against the real discovery DB that is ~30,000 full
table scans of a 56k-row table — roughly 1.6 billion row comparisons per
scheduler cycle. `execute_scheduled_cycle` never returned. The entire batch-00
run was killed at the 1500s pytest timeout.

Two defects, both fixed in commit `3710288`:

1. **O(n^2) dedup.** `gap_register` is Lane A-owned and frozen, so no index was
   added. The `(token_id, kind)` keys are read once and membership is tested in
   memory — O(rows) total. Verified against the production discovery DB that
   exposed the bug: **0.59s** where it previously hung indefinitely.
2. **A unit test was reading production state.** `test_production_scheduler_cycle`
   never injected `discovery_db_path`, so the scheduler audited the real
   discovery DB instead of a temp one. That is why a unit test stalled — and
   why it would have passed or failed depending on machine state, which is not a
   test at all. The test is now hermetic.

`tests/test_audit_and_register_missed_windows_is_not_on2` pins the complexity
bound (200 tokens x 8 slots, all overdue, asserts < 10s and correct counts) plus
idempotency on a second pass.

### skip / xfail reasons (verified, not guessed)

- `batch_00: 1 skipped` — `tests/test_ai_provider_status.py:224`: **"non-Windows
  behaviour"**. A guard for the other platform; correct on this host.
- `batch_04: 1 skipped` — `tests/test_gemini_phraser.py:136`: **"on Windows the
  real credential may exist; the live smoke covers that path"**. Deliberately
  avoids touching the owner's real Windows Credential Manager entry; the same
  path is covered by the live smoke test. Correct.
- Neither skip hides a defect. Both are host guards, not silences.
- `batch_02: 1 xfailed` — `tests/test_engine_import_safety.py` previously held a
  *strict* xfail documenting that `engine/run_validation.py` ran its whole
  backtest at module scope. M9 part B fixed the defect; the xfail was removed
  and the test now asserts the invariant directly. This xfail is gone from the
  tree as of `3710288` — it appears above only because batch_02 was run before
  that commit landed. **The current tree has 0 xfail.**

## TypeScript — 377 tests, 0 fail

All 11 `npm run test:*` selftest suites green:

| suite | tests | pass | fail |
|---|---|---|---|
| test:web-api-auth | 9 | 9 | 0 |
| test:canonical-read-model | 13 | 13 | 0 |
| test:canonical-security | 19 | 19 | 0 |
| test:alert-banner | 8 | 8 | 0 |
| test:dashboard-truth | 34 | 34 | 0 |
| test:chat-control-gate | 126 | 126 | 0 |
| test:chat-reply-format | 40 | 40 | 0 |
| test:chat-intent | 72 | 72 | 0 |
| test:chat-agent | 30 | 30 | 0 |
| test:dev-missions | 14 | 14 | 0 |
| test:gemini-phraser | 12 | 12 | 0 |

## Static gates

| gate | exit | note |
|---|---|---|
| `npx tsc --noEmit` | 0 | clean |
| `npx eslint .` | 0 | clean |
| `npm run audit:control-verify` | 0 | `CHAIN_OK`, 9 lines |

## What this baseline is NOT

These are self-tests. Per owner directive §76, passing self-tests support a
rung of `TESTED` at most — never `VERIFIED` or `OPERATIONAL`. Independent
verification against real data, on the owner's machine, is what separates
`TESTED` from `VERIFIED`. See the register (Part C) for where each capability
actually sits.
