# QUEUE DECISION — M12 returned to PENDING (2026-10-08)

## Question

M12 sits at `NEEDS_REVIEW`, which `Select-NextMission` honours as an owner gate and
which has therefore held every row below it (M34 and 43 others) since 10:10. Is this
a genuine human-review need, or a runner defect?

## Evidence

`autopilot/consumed/ap_M12.json` records the escalation:

```
verdict:      MALFORMED
exit_code:    0
waited_sec:   3243
source:       live
ts:           2026-10-08T10:10:00
```

`autopilot/state.json` records `M12: 3` — the attempt cap.

`reports/grok/_claude_ap_M12_result.txt` (the output those three attempts produced)
contains exactly two substantive lines and no verdict:

```
claude.exe : [claude-code:unrecognized_model] {"model":"Atria-Dawn-Preview","query_source":"sdk"}
API Error: Request rejected (429) . Token quota exhausted.
```

There is no `AUTOPILOT_RESULT` line, because the mission never ran. The account quota
was exhausted before the model could start.

## Root cause

A wording mismatch in the runner's failure classifier. The guard matched
`usage limit|quota exceeded|credit balance`; the CLI actually emits
`Token quota exhausted`, `Request rejected (429)` and `unrecognized_model`. None of
the real strings matched, so every attempt fell through to `MALFORMED`. After three
such attempts `Apply-Verdict` escalated the row to `NEEDS_REVIEW`, and
`Select-NextMission` then treated a dead token quota as an unresolved human review.

This is the same defect class proven for M10 on 2026-10-07 (resolved in `c7fbfc5`).
A platform outage was being represented as an AHOS mission failure.

## Repair applied (this session)

`claude_autopilot.ps1` and `run_mission.ps1` now classify quota/model/auth/rate
failures as **infrastructure**, not mission, failures:

- new `Test-InfraFailure` matching the CLI's real wording, verified against the
  committed M12 artifact;
- new `INFRA` verdict branch in `Apply-Verdict`: the row returns to `PENDING`, the
  attempt budget is **not** charged, and the queue is **not** frozen;
- a bounded, monotonic, saturating backoff (`Get-InfraBackoffSec`) so a dead quota is
  retried with growing delay rather than hammered, while the row stays launchable;
- the same classification in `Reconcile-ActiveState`, so a runner generation that dies
  during an outage cannot leave a `RUNNING` row that the main loop would hand to the
  owner;
- `run_mission.ps1` now stops retrying immediately on an infra failure instead of
  burning all its attempts against an unavailable platform.

Pinned by TEST L in `autopilot/test_runner.ps1` (executed under real PowerShell 5.1)
and by static pins in `tests/test_autopilot_runner.py`. Full harness: 12/12 pass.

## Decision

**M12: `NEEDS_REVIEW` -> `PENDING`**, and `state.json` `M12: 3 -> 0`.

Rationale: the three attempts were all infrastructure deaths, and the repaired
classifier would not have charged any of them. The `NEEDS_REVIEW` status was produced
by a runner defect, not by a human reviewing the work, so returning the row to the
launchable set restores the state the queue would have had. This is not a judgement
that M12 is complete — it is the correction of a false escalation.

**M12 is NOT marked DONE.** The work has not been re-evaluated on its merits. The
runner will re-execute it and deliver its own verdict. Note that the current registry
holds 25 agents with explicit per-agent `allowed_authority`/`forbidden_authority`,
whereas the queue row describes "37+ agents ... authority NONE by default" — so the
re-run may well find the row describes work that is not yet done as specified.

## Queue integrity

Only the STATUS column changed. BLOCKED_OWNER and DONE rows are untouched. The
owner-gate semantics of `NEEDS_REVIEW` are preserved — a genuine human review still
holds the queue; a platform outage no longer does.
