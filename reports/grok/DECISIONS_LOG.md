# Unattended-operation decisions log

Decisions taken without waiting for owner approval, per `AGENTS.md`
"Unattended operation". Each row: date, question, choice, reason. This records
judgement calls within the safety surface — it is not a place to log work items
(the autopilot queue owns those) and nothing here overrides an owner decision.

## 2026-10-08

**Q: The autopilot runner escalates a dead token quota to `NEEDS_REVIEW`, which freezes all 43 rows below it. Repair the orchestration, or leave it?**
**A:** Repair it — classify quota/model/auth failures as `INFRA`, not mission failures.
**Reason:** The escalation was provably a category error: the CLI emits `Token quota
exhausted` / `Request rejected (429)` / `unrecognized_model`, none of which the
runner's `quota exceeded` pattern matched, so a platform outage fell through to
`MALFORMED` and then to an owner gate. A non-product infrastructure failure was being
represented as an AHOS mission failure. The repair charges no attempt, freezes no
queue, and backs off instead — the queue stays launchable for the whole outage.

**Q: Reset M12's escalation, or leave it for the owner?**
**A:** Return it to `PENDING` and zero its attempt counter. Do **not** mark it DONE.
**Reason:** All three attempts were quota deaths with no `AUTOPILOT_RESULT` line, so
the `NEEDS_REVIEW` was produced by the runner defect above, not by a human reviewing
the work. Restoring the launchable state is the correction of a false escalation. It
is explicitly not a completeness claim — the runner will re-execute M12 and deliver
its own verdict, and the row's "37+ agents, authority NONE by default" description does
not match the current 25-agent registry, so the re-run may find real work remaining.
Recorded in `autopilot/QUEUE_DECISION_M12_infra_false_escalation.md`.

## 2026-10-07

**Q: M10 Stage 4 — execute the live `.env` `DATABASE_URL` flip, or only prepare it?**
**A:** Prepare + document, do **not** flip.
**Reason:** The owner had already gated this explicitly (2026-10-07). Everything
around the flip is built, tested, and receipted — the probe branch, the
rewritten `windows_ensure_database_url.ps1`, the scratch-store gateway smoke,
and the one-line flip + rollback runbook. The remaining act changes which store
a live PAPER_ONLY gateway reads; that is the owner's call, and the rollback path
stays exactly as documented while it is unexecuted.

**Q: The Stage 4c smoke found a `ReferenceError` in `db/index.ts` — fix it now?**
**A:** Yes; fix, add a regression test, re-run the smoke.
**Reason:** A re-export without a local value binding is a plain bug — invisible
to `tsc`, and it would have made the owner's flip fail closed on every request.
Fixing it changes no safety surface and no authority boundary; leaving it would
have shipped a known-broken flip path.

**Q: The smoke receipt v1 claimed the `/api/chat` retry-then-500 contract fires on a DB failure. It does not.**
**A:** Correct the receipt and the runbook to describe the real contract.
**Reason:** `chat.ts` swallows store failures, so the route's 500 branch is a
*provider*-failure path. Recording the mechanism as it actually is beats a
cleaner-sounding claim that no leg exercised. `REALITY > DOCUMENTATION`.

**Q: `config/.env.template` needs a comment touch for Stage 5, but `config/` is permission-denied in this session.**
**A:** Skip it; note the gap in the migration doc and the archive README.
**Reason:** The template's *keys* stay either way (the plan says keys kept for
compat). Only a comment changes. Fighting a permission boundary for a comment is
not worth it, and `.env.template` is not a live runtime path.

**Q: `engine/run_all_checks.sh` calls bare `python3`, which is the Windows Store stub here.**
**A:** Run it through a venv shim outside the repo; do not edit the script.
**Reason:** The script is CI-authored and runs correctly on the Linux CI host.
Rewriting it for this Windows shell would diverge the local and CI paths for
every future run. The shim is host-local, uncommitted, and leaves the artifact
untouched.
