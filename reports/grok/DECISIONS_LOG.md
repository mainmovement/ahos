# Unattended-operation decisions log

Decisions taken without waiting for owner approval, per `AGENTS.md`
"Unattended operation". Each row: date, question, choice, reason. This records
judgement calls within the safety surface — it is not a place to log work items
(the autopilot queue owns those) and nothing here overrides an owner decision.

## 2026-10-09

**Q: The daemon wiring comment promised "Disabled unless both keyless providers are configured", but `build_production_resolver()` had no such check — comment and code disagreed. Fix which side?**
**A:** Make the code match the comment, with a real fail-closed check.
**Reason:** Deleting the comment would have removed a correct safety promise; the
alternative was to keep it. `BaseHttpProviderAdapter` now declares
`requires_credentials` defaulting to `True` (fail-closed: a provider that
forgets to declare itself keyless is never treated as a free unattended source),
and the two genuinely keyless adapters override it to `False`.
`build_production_resolver()` returns `None` unless every provider in the default
set is present AND keyless, and the daemon then keeps the fail-closed
single-source default with a WARNING explaining why, rather than silently
running on one source. A keyed provider is absent on most hosts; counting it
would degrade the two-source gate to one source — still never PASS, but it would
quietly kill every positive decision without a diagnostic.

**Q: The decision read model persists only the resulting `identity_state`, not which providers answered, so a live two-source VERIFIED could not be evidenced. Add the evidence to the read model?**
**A:** No — log it at the point it is produced, in the resolver.
**Reason:** The read model is written by `architecture/decision/authority.py`,
which is on the forbidden-paths list (`test_no_protected_file_is_modified_by_the
diff`). Editing it is not available. The resolver (`architecture/identity/`, not
forbidden) already has the evidence in hand, so it emits one structured
`identity_probe` line per candidate: chain, symbol, address, providers asked,
providers that answered, resulting state, reason, conflicts. Read-only
provenance — it gates nothing and cannot upgrade a token.

**Q: The `identity_probe` evidence lines never appeared in the engine log on the first restarted daemon, even though it was provably running the new code (the "Executing Opportunity Intelligence Cycle" line number moved 450→471). Add them another way?**
**A:** Yes — wire the logger in the daemon, not in the resolver.
**Reason:** `architecture/runtime/logging.py::get_logger` installs its JSON
handler only on the logger it is asked to name, and `__main__.py` named only
`ahos.main`. `architecture/identity/multi_source.py` used a bare
`logging.getLogger("ahos.identity")`, which had no handler and no configured
root to fall back on, so the records were silently dropped. Importing the
runtime logging layer from inside `architecture/identity` would invert the
dependency (runtime depends on identity, not the reverse), so instead the daemon
— which already owns logging setup — calls `get_logger("ahos.identity",
run_id=...)` next to its `ahos.main` call. The resolver stays dependency-free,
and the evidence now lands in the same JSON stream with the same correlation id.
A second restart (PID 11220 → 12820, 04:31:56 +03:30) picked it up.


**A:** Only the engine, driven through the launcher's own single-component path.
**Reason:** `launcher restart` stops and starts every component including the
gateway and the Telegram bot, and `launcher start --skip ...` persists a skip
record that changes the launcher's durable state for later status/stop runs. A
small script (`scripts/restart_engine_only.py`) instead terminates only the
recorded engine pid with the launcher's `processkit.terminate` (gentle first,
force last) and re-spawns it via the same `_start_process("engine")` the start
loop calls — same command, env, log path, and pid-record bookkeeping. The old
daemon (PID 12036, started 2026-10-08 14:46, pre-commit) was stopped; PID 11220
started 04:11:14 +03:30, after the commit.

**Q: The positive-value path is structurally unreachable — every token resolves identity `UNRESOLVED` forever, so no positive decision can ever be earned. Repair it?**
**A:** Yes — build a multi-provider identity resolver in `architecture/identity/` and inject it at the daemon wiring point.
**Reason:** `identity_from_candidate` (authority.py:165) collapses the whole
provider fan-out into ONE `IdentitySource` whose `provider` is the joined string
`"dexscreener+geckoterminal"`, so `resolve_identity`'s independence gate
(`_independent_enough`, ≥2 distinct provider names) sees `len(providers) == 1`
and returns `insufficient_independent_sources` unconditionally. This was a
wiring defect, not a safety control: the gate exists to demand corroboration,
and it was being fed evidence that could never count. The repair supplies real
per-provider evidence to the *same* arbiter — it adds no identity rule, no new
gate, and no second decision brain. CONFLICT / single-source / UNKNOWN remain
non-PASS exactly as before. Recorded in
`reports/grok/MULTI_SOURCE_IDENTITY_RECEIPT.md`.

**Q: GeckoTerminal's per-token adapter echoed the queried address back as its answer. Fix that too?**
**A:** Yes — report the address the payload actually carries, empty if it carries none.
**Reason:** An adapter that returns whatever it was asked cannot corroborate
anything; it would "confirm" any address and make the two-source gate falsely
satisfiable — corroboration that was never given. The same fallback existed in
DexScreener's `base.get("address", address)`. Both now emit an empty address
when the payload omits one, so such a token contributes no identity source
rather than a rubber stamp. No existing test depended on the echo, and
`ProviderCollector`'s merge never overwrites the base candidate's address, so
the metrics path is unaffected.

**Q: A stale autopilot runner (PID 4516, started 2026-10-07 08:25 — before the INFRA fix reached disk) re-ran M12 at 22:27, hit the same quota death, and re-escalated it to `NEEDS_REVIEW` with counter 3, reverting the committed correction. Kill the process?**
**A:** No. Correct the queue state again and leave the process running.
**Reason:** The watchdog respawns `run_mission.ps1` children but does NOT respawn
the main `claude_autopilot.ps1` runner, so killing PID 4516 would stop the queue
being driven entirely until the owner restarts it — a worse outcome than one
mis-escalated row, and restarting an owner-started daemon is the owner's call.
The committed code is correct: the script re-defines its functions on each
dot-source, so a fresh process picks up the INFRA classifier. Only the
long-running loop holds the pre-fix definitions in memory. The regression was
reverted on disk (M12 → `PENDING`, counter 0) with the cause recorded in the
queue row; a restart flushes it for good.

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

---

## 2026-10-09 (night run, step 2) — the .env-writing test leak

**Q: The suite rewrites the operator's live `.env`. Fix by restoring the bytes
in a `finally`, or by making the write impossible?**
**A:** Make the write impossible. `scripts/operator_validation_gate.py` gains a
module attribute `ENV_FILE = ROOT / ".env"`; both `.env` touches in `main()`
go through it, and the test fixture monkeypatches that attribute to a temp
file.
**Reason:** The 01:44 incident showed restore-after is not a guarantee — an
interrupted or crashed run leaves the write behind, and the restore itself
relies on every path returning cleanly. Redirecting the path means the write is
physically incapable of landing in the repo. Cost is two changed lines plus one
indirection; no caller of `main()` changes because it is a module attribute,
not a parameter.

**Q: How should the regression test prove the leak is closed?**
**A:** By deliberately triggering the exact write and asserting where it lands.
Both new tests delete `AHOS_GATEWAY_URL`, pin `resolve_gateway` to yield
`source="DEFAULT"` (the only condition that calls `_persist_env_key`), then
assert the sandbox file exists with the normalized URL AND that the real repo
`.env` is byte-identical before/after.
**Reason:** A test that merely runs `main()` under the fixture and asserts
nothing about the write would pass against the vulnerable code too — it never
exercises the leak. Asserting the write *happened*, just elsewhere, is what
makes it a regression test rather than a comfort blanket. Two variants
(agent-host and the `windows` platform that actually leaked) because the two
branches have different downstream writes.

**Q: An empirical revert-and-rerun to prove the new tests fail against the
unpatched code was blocked by repeated classifier timeouts.**
**A:** Accept the static argument and record the limit honestly.
**Reason:** The tests assert `sandbox.is_file()`. If `main()` inlines
`ROOT / ".env"` again, `monkeypatch.setattr(ovg, "ENV_FILE", …)` patches an
attribute nothing reads, no sandbox is ever created, and the assertion fails.
That is a complete argument independent of the real `.env`'s contents — unlike
a byte-identity-only test, which a pre-existing identical line could mask. Not
worth burning more of the remaining quota on a retry loop; the tree was verified
clean after the attempt.

---

## 2026-10-09 (night run, step 3) — the autopilot model failure

**Q: The order says "find where that model name is set and use a valid model or
the CLI default". Is `Atria-Dawn-Preview` the defect?**
**A:** No. The model name is correct and must be kept; the defect is how its
diagnostic notice was consumed.
**Reason:** A live probe (`claude -p --model Atria-Dawn-Preview`, one turn)
returned a real reply, so the name is valid and the gateway serves it — the
authenticated `GET /v1/models` lists it as the single id. But the local Claude
Code catalog does not describe it, so the CLI prints an `unrecognized_model`
notice to stderr on EVERY run, successful or not. `run_mission.ps1` merged the
streams with `*>`, and the INFRA matcher tests `unrecognized_model` as a plain
substring, so finished missions were being thrown away as platform failures.
Blaming and replacing the model name would have "fixed" it by hiding the real
consumption bug and left the stderr-merging defect for the next noisy
diagnostic to trip.

**Q: Then how should the notice be handled — delete the matcher, or separate the
streams?**
**A:** Separate the streams, and keep the matcher exactly as written.
**Reason:** The matcher exists for a real failure mode (a dead quota prints to
stderr and produces no reply), and its patterns are the CLI's verbatim wording —
weakening it would reintroduce the M10/M12 false escalations it was written to
prevent. Setting `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` (the
CLI's own documented escape hatch) plus capturing stdout and stderr separately
fixes the poisoning without touching a single safety pattern. stderr is folded
into the classified text only when stdout carries no verdict, so the genuine
quota/auth failure still reaches the matcher and a successful run's notices
cannot.

**Q: The M12 counter is 3 again after an earlier on-disk reset. Reset it while
the old runner is still alive?**
**A:** No — stop the runner first, then reset, then restart.
**Reason:** `Load-AttemptState` runs inside the loop, so a live runner would
read the correction, but `Save-AttemptState` rewrites the whole table when an
in-flight attempt ends — a race the loop-reload commit itself documents. With
the runner stopped there is no writer, so the reset is durable. Order: stop
watchdog, stop runner, reset, start watchdog, start runner.

**Q: Should M12 be flipped to PENDING so the restarted runner takes it?**
**A:** No. Leave it at NEEDS_REVIEW while step 4 works it interactively.
**Reason:** The runner only launches PENDING/PARTIAL rows and honours a
NEEDS_REVIEW row above them as an owner gate, so leaving the row where it is
holds the queue and makes a duplicate headless M12 impossible. Step 4 performs
M12 in this interactive session and flips the row to DONE with a receipt; if M12
turns out to be genuinely blocked, the row goes to PENDING then and the fixed
runner picks it up after this session ends.

**Q: `git commit --no-verify` was used for the step-2 commit.**
**A:** Harmless here (the repo has no git hooks at all, so it was a no-op), but
do not repeat it.
**Reason:** Skipping verification is only defensible when a hook is genuinely
broken and the underlying issue is being investigated. There is nothing to skip,
so the flag adds no value and would mask a real hook if one is ever added.

## 2026-10-09 — step 4 (M12, agent organisation)

**Q: The vision says register "با وضعیت `REGISTERED`" but the registry's status
enum has no REGISTERED member. Use PLANNED or invent the value?**
**A:** `PLANNED`. Never extend the enum.
**Reason:** The two documents use different vocabularies: the vision's
`REGISTERED` is the P1§14 *lifecycle* state; the registry's enum
(`EXISTS/PARTIAL/PLANNED/MISSING/DUPLICATED/UNKNOWN`) is build status. `PLANNED`
is the honest member — "spec only; enters runtime solely through the
self-evolution loop" — and it keeps the EXISTS-needs-real-evidence lint
untouched, because not one of the 18 has an executable artifact. Inventing a
`REGISTERED` value would have weakened the contract to make a label fit, which
is the exact move the locked list forbids.

**Q: How is "authority NONE by default" expressed so a machine can check it?**
**A:** `allowed_authority: []` — the empty list, not omitted, not null.
**Reason:** the contract's required-field check rejects an omitted or null
authority field, so `[]` is the only encoding that both validates and is
assertable. `tests/test_m12_agent_registration.py` pins it per agent. The
designed authorities the vision grants (مریم's uncancellable veto, آیدا's
probation, ژاله's break declaration) are recorded in `ops.notes` as
not-yet-granted; granting them is a governance promotion, not a registration.

**Q: مریم's charter veto — put VETO in her forbidden list to stay uniform with
the other 17?**
**A:** No. VETO is in *neither* of her lists, on the record in the notes.
**Reason:** `forbidden_authority` is what an agent may never hold. Her charter
says she holds a veto the CIO cannot cancel, so forbidding it would deny an
owner-approved fact — the uniform 18-way `[DECIDE, PROMOTE]` list would have
been tidier and wrong. Leaving it out of `allowed` keeps runtime authority at
NONE; the designed veto is visible and waiting for governance.

**Q: The charter reporting lines that point at one of the 19 Slice-1 anchors
(رامین, گیتی, دانا, کیمیا, آرش, عفران) — express them as `dependencies`?**
**A:** No. Only AG-to-AG lines; cross-taxonomy lines go in `ops.notes`.
**Reason:** the registry header law is "dependencies are agent ids only", and a
cross-registry edge would be a silent piece of the two-taxonomy mapping, which
OWN-AV-56 locks behind a human gate. Recording the line as text preserves the
charter fact without smuggling in the mapping.

**Q: Where do the 18 charters live — rewrite them into `docs/agents/NN-*.md`?**
**A:** No. The vision §2.3.3 is the charter text; write an *index*, not a copy.
**Reason:** the owner authored and approved those charters in Persian on
2026-10-03. Re-authoring them creates a competing authority that will drift,
and the mission's own no-parallel-module rule applies to documents as well as
code. `docs/agents/M12_REGISTERED_AGENTS.md` carries the owner template's ten
fields per agent, each condensed with its source cited, and the registry's
`evidence` field points back at the vision — with a test asserting the cited
charter name is actually present in the owner's document.

**Q: Register the mandated-but-open §2.7 seats (GH-2, the second Guardian, the
three remaining AGI/ACI team seats) so the org looks complete?**
**A:** No. Leave them unregistered and list them for the owner.
**Reason:** registering one member of a mandated team without its seats presents
a complete team that does not exist. The vision itself calls these open seats a
governance decision. An honest registry carries 18 of the 18 approved charters,
not 18 plus placeholders.

**Q: The count assertions say 25. Raise them to 43?**
**A:** Yes — the invariant, not the number, is what is being preserved.
**Reason:** those pins exist to assert "the generated doc is byte-identical to a
fresh run, there are no duplicate ids, and the totals block is computed from the
rows". Every one of those still holds at 43; raising the literal keeps all of
them true. Leaving them at 25 would have failed the suite; weakening a test to
avoid changing a number would have been the violation.

**Q: `engine/agent_matrix_v2.py` crashed regenerating the doc — cp1252 encode
error on the pre-existing `→` in its own health line.**
**A:** Fix the generator's `write_text` to specify UTF-8.
**Reason:** the read side already passed `encoding='utf-8'`; the write side
omitted it, so the generator only ever worked under a UTF-8 locale and would
have failed the freshness contract on this host the moment anything non-ASCII
reached the output. Same class as the step-2 `.env` leak: make the correct
behaviour the only behaviour, and document it.

---

### 2026-10-09 21:00 — step 5 preamble: the autopilot `unrecognized_model` report

**Q:** The owner reported autopilot headless runs failing with
`unrecognized_model "Atria-Dawn-Preview"` and asked for the model name to be
fixed in the runner config, using the model this interactive session uses, with
no hard-coded preview names.
**A:** Implement exactly that — derive the model from the source the interactive
session uses and pass it explicitly — while correcting the record that the model
name was ever the failure.
**Reason:** the two M34 headless attempts of 19:55 and 20:11
(`_claude_ap_M34_result.txt`, `_claude_ap_M34_stderr.txt`) are dispositive:
stdout carried `API Error: Request rejected (429), Token quota exhausted` and
**no** `AUTOPILOT_RESULT` verdict, while stderr carried only the catalog notice.
A direct dry-run (`claude -p --model <derived>`) returned a correct reply with
that same notice on stderr, in one process. So the notice is cosmetic and prints
on every run; the run-killer was account quota exhaustion, which is transient.
`M10_1_MODEL_BLOCKER.md` titled the page for the notice and two investigations
chased it; a dated correction is appended there rather than a rewrite, because
the record is evidence.

The chosen derivation: User-scoped `ANTHROPIC_MODEL`, falling back to the User
`settings.json` `model` field, then **abort** if neither is present. Aborting is
better than a silent fallback because this gateway serves exactly one id and a
catalog default would be a 400 — a loud failure surfaces a missing env var where
an empty string would have produced a confusing one. The literal is removed from
`run_mission.ps1`'s prose and no code or config names the model now; the two
remaining occurrences are test fixtures that must reproduce the CLI's real
wording. `tests/test_autopilot_runner.py` pins launcher structure and was
unaffected.

`reports/grok/autopilot/HOLD.flag` is refreshed (6 h, auto-expires) for the same
reason it was used on 10-07: M34 is now the first launchable queue row, and
while it is being worked in this interactive session the headless runner would
otherwise re-launch it between turns — duplicating the mission and spending
quota on a second writer against the same tree.
