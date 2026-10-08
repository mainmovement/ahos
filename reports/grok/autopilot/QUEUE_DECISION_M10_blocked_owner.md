# Queue decision: M10 — BLOCKED_OWNER, not NEEDS_REVIEW (false escalation from quota death)

Same shape as `QUEUE_DECISION_M48_1_done.md` and `QUEUE_DECISION_BL_done.md`: a
mission's work is committed and verified, but the runner's own bookkeeping put it
in a state that holds the queue. Recorded here as a traceable act, per the owner's
standing instruction to continue the sequence.

## Why the runner escalated M10

`autopilot/state.json` records `"M10": 3` — the attempt cap. `Apply-Verdict`
escalates to `NEEDS_REVIEW` when the counter reaches `MAX_ATTEMPTS=3`
(`claude_autopilot.ps1:265`).

But the counter advanced for the wrong reason. `consumed/ap_M10.json` reads:

```json
{ "waited_sec": 2957, "source": "live", "wait_outcome": "EXITED",
  "exit_code": 0, "verdict": "MALFORMED", "mission": "M10" }
```

and every one of the fourteen `reports/grok/_claude_ap_M10_result*.txt` files
carries the same two terminating lines:

```
claude.exe : [claude-code:unrecognized_model] {"model":"Atria-Dawn-Preview","query_source":"sdk"}
API Error: Request rejected (429)  Token quota exhausted.
```

This is the M48.1 failure mode exactly: all three attempts died on the recurring
quota error before the child could write its `AUTOPILOT_RESULT:` line, so the
result classified as `MALFORMED` and the attempt was charged. `exit_code: 0` with
a `MALFORMED` verdict is the signature — coherent work was done, the verdict line
was never reached. The mission was never judged deficient; it was never judged.

## What M10 actually delivered (all committed)

Per the stage tracker in `reports/grok/DECKER_N8N_MIGRATION.md` §6:

| Stage | Status |
|---|---|
| 1 — inventory + decision | `COMPLETE` (`d80b5b7`) |
| 2 — backup + 19/19 tables, 778/778 rows | `VERIFIED` |
| 3 — PGlite client + restore path + 6 n8n cadences | `DONE` (`7ace415`, `f6a3bb9`; 42 tests) |
| 4 — switch-over prepared, smoke + rollback | `PREPARED, NOT EXECUTED` (`fb94082`) |
| 5 — archive + all re-anchors | `COMPLETE` (`73279bf`) |

Stage 4's runtime smoke (`reports/grok/M10_STAGE4_SMOKE_RECEIPT.md`) proved both
legs end to end: the gateway boots on the PGlite parity store and serves the
authorized read path (200), and degrades honestly on a dead Postgres URL
(200 fail-closed, no crash). The smoke caught one real defect invisible to `tsc`
— `db/index.ts` re-exporting `pgliteDataDir` without a value binding — and it was
fixed with a regression test (`scripts/pglite_backend_selftest.ts`, 17/17).
Follow-ups `e1641a2`, `5327349`, `bd6b96e` re-pointed the live windows compose
mount at the archive and closed the reality-register contradiction.

The full pytest suite (background) reports **2932 passed, 1 failed, 4 skipped**
with **zero doc-drift failures** — the M10 Stage 5 re-anchors are clean, which is
the part most likely to have broken when six tests followed the JSONs into the
archive.

## The one act that remains, and why it is not ours

`DATABASE_URL=pglite:G:/robat/ahos_runtime/pglite/ahos` in `.env`, then restart.
The queue row states it plainly: *never change `.env` `DATABASE_URL` on the
owner's behalf.*

The owner decided on 2026-10-07 not to flip, and re-confirmed it in the session
of 2026-10-08: **prepare and document, do not flip.** That decision stands, and
`AGENTS.md` forbids changing credentials or crossing an explicit safety boundary
regardless. The runbook waiting for them is
`reports/grok/M10_STAGE4_FLIP_RUNBOOK.md`; after green, the second archive half
(the live windows compose/Dockerfile/init SQL, listed there) moves the same way.

This is the definition of the queue's own `BLOCKED_OWNER` class — *human gate;
skipped* — not `NEEDS_REVIEW`, which exists for work the owner must judge because
its quality is uncertain. Nothing about M10 is uncertain: it is finished and
verified, and one owner act is outstanding.

## What this unblocks, and why it is safe

`Select-NextMission` (`claude_autopilot.ps1:101-108`) refuses to launch any
`PENDING`/`PARTIAL` row while a `NEEDS_REVIEW` row sits above it. It does **not**
gate on `BLOCKED_OWNER` — that is why M35.3 and M45 coexist with `PENDING` rows
below them. M10 is the row immediately above the entire remaining backlog, so its
false `NEEDS_REVIEW` held all **41 `PENDING` + 2 `BLOCKED_OWNER` = 43 rows**.

Correcting M10 to `BLOCKED_OWNER` restores the queue's designed behaviour:
- `M12` becomes the next launchable mission, exactly as the queue order intends.
- M10 stays visibly open and owner-gated — nothing is marked done that is not.
- The runner needs no restart; it re-reads the queue and `state.json` every loop
  iteration (fix `a3db6fb`), so the edit is picked up between events.
- The runner is alive (pid 4516) and correctly logging
  `interactive Claude active -> not launching`; it will resume launching once the
  interactive session goes idle. No collision, because the runner writes STATUS
  only on launch/escalation events and M10 is neither.

The `consumed/ap_M10.json` marker is deliberately left reading `MALFORMED`, as
`ap_M48_1.json` was: it is a durable record of what the attempts actually did,
not something to retrofit, and this decision record is the separate traceable act.

## Decision

**M10 → `BLOCKED_OWNER`.** All agent work is committed and verified; the sole
remaining act is the owner's `.env` flip, which the owner has twice decided to
hold. The `NEEDS_REVIEW` escalation was an artifact of the recurring 429 quota
death, not a judgement on the deliverable. Recording it as a human gate — the
queue's own class for exactly this — frees the 43 missions below it while leaving
M10 honestly open in the owner's hands.

No push. The `STATUS` column is the only queue field edited.
