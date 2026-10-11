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

---

### 2026-10-09 21:40 — step 5: M34 coherence audit, the three judgement calls

**Q: The queue row says six axes; INV-31 names seven (it adds the design
system). Which set does the audit map?**
**A:** Seven, and the discrepancy itself becomes a finding (M-AXIS-7).
**Reason:** INV-31 is the law ("her concern has one canonical source"), and the
queue row is a one-line summary of it. Mapping six would have silently dropped
an axis that has a live deliverable (`docs/design/`, `app/` tokens, Persian RTL)
and no declared owner, test or lint -- precisely the thing the audit exists to
expose. Recording the count conflict as a finding keeps the owner as the one who
decides whether the mandate covers design.

**Q: The registry had grown to 43 but nine live docs still stated 25 as present
fact, including `config/agent_registry.yaml`'s own header and
`AHOS_REALITY_MAP_v1.md` -- the file whose entire purpose is stopping census
overclaims. Fix them in an audit, or leave them for a doc mission?**
**A:** Fix them. This is M34's job, and M12 should have caught them.
**Reason:** leaving a live doc stating a superseded census is the exact
incoherence M34 exists to remove, and the source-of-truth file contradicting its
own `totals` is the defect that propagated the drift in the first place. All
nine are doc/config-only, no code semantics, no test pinned them. Archives and
dated historical statements were left untouched: editing them would falsify the
record. Then `tests/test_m34_coherence.py` pins the three relations that broke,
so the next registration cannot update the rows and leave the census behind.

**Q: Vision §14.9.1 calls `slills/` a misspelled duplicate of the skills folder
"with same-sized files". Treat it as an M34 duplicate?**
**A:** No -- the claim does not survive re-checking, and saying so is part of
the audit.
**Reason:** `slills/` holds 16 third-party `SKILL (1..15).md` files; the
canonical `.cursor/skills/` has 11 curated AHOS skill directories. Neither the
sizes nor the names correspond, nothing references it outside the archive, and
`docs/archive/.../DOC_TRUTH_MAP.md:22` already records it as uploaded
third-party material. An audit that confirmed a duplication it could not see
would be exactly the fabricated-positive the `UNKNOWN > fabricated` rule
forbids. It is recorded as unmanaged untrusted material and routed to M53, and
the correction is written into the audit so the vision line does not send a
future pass looking for a duplication that is not there. Same discipline applied
to two other inherited claims: `data/mission_ledger/` is lazy-by-design
(`mkdir` at first write), not a defect; and the `architecture_registry.sqlite`
absence is a builder with no production caller, which is a real gap but a
different one.

## 2026-10-10 (M13, gold track) — source pair deviation from the approved map

**Question.** AHOS_TRADING_SKILLS_v2 §0 names the gold pair as "FRED (fredapi) /
EIA free key | Stooq via pandas-datareader / yfinance futures (GC=F)", and
README_FOR_CLAUDE rule 2 says to use the approved sources and not reinvent
them. The two-source witness needs two fresh independent feeds. Which sources
does M13 actually wire?

**Choice.** Source B exactly as approved: Yahoo `GC=F` COMEX gold futures (the
same upstream tape yfinance reads). Source A as a **recorded deviation**:
gold-api.com XAU spot, instead of Stooq or FRED.

**Reason.** Both approved Source A options were measured and neither can serve
a fresh keyless witness. Stooq now serves a JavaScript browser-verification
wall and returns HTTP 404 for every CSV endpoint tried (`/q/l/?s=xauusd`,
`/q/l/?s=gc.f`, `/q/d/l/?s=xauusd`, plus CL=F, ^SPX, BTCUSD) — a plain HTTP
client cannot read it at all. FRED's gold series is the daily London bullion
fix (once-a-day settlement, a day behind) behind an API key, so it fails the
freshness window even with the sanctioned Credential Manager key wired, and a
keyed source cannot be part of a keyless unattended pair. gold-api.com XAU is
free, keyless, live-verified (16 s old at probe, $4195.60) and is a different
vendor from the COMEX tape, so it satisfies the law's independence clause
("different providers with different upstream data"). FRED's daily fix remains
the obvious *third*, corroborating source once its key is wired — corroborating
only, because a daily fix is not a fresh feed.

## 2026-10-10 (M13, gold track) — disagreement tolerance set to 1.0%

**Question.** What disagreement tolerance does the gold two-source witness use?

**Choice.** `GOLD_TOLERANCE_PCT = 1.0` — the **top** of the owner-approved
0.5–1% band (DEDUP_MERGE_MAP v1.20: "same 0.5-1% agreement rule"; TRADING_SKILLS
v2 §0: disagreement past tolerance is CONFLICT and gets no signal), replacing
my earlier 2.0%.

**Reason.** 2.0% was my own number and was 2–4× looser than the approved band;
the approved band is the rule to follow. The top rather than the bottom of the
band, because the gold pair is spot-vs-futures: it carries a basis and the two
tapes tick at different instants, so the tolerance must absorb both. Measured
live: spot 4196.90 vs futures 4220.30 = 0.56%, comfortably inside 1.0%. The
boundary is tested at both sides of the constant so the number is code, not
judgement. Not loosened to make a trade pass — the measured spread sits near
the middle of the band either way.

## 2026-10-10 (M13, gold track) — futures freshness gate left at one hour

**Question.** The COMEX front-month print ticks far less often than the spot
tape (measured 2026-10-10: Yahoo `regularMarketTime` 7862 s old at every
interval 1m/2m/1d, while gold-api spot was 16 s old). Should the futures feed
get a wider freshness window than the spot feed?

**Choice.** No. One uniform `GOLD_MAX_AGE_SEC = 3600` for both feeds.

**Reason.** A wider futures window would be tuning the freshness gate to make
the trade happen — exactly the gate-loosening the locked list forbids. The
honest consequence is accepted and recorded: between COMEX sessions the witness
reports UNRESOLVED and the paper track records NO_DATA rather than trading on
spot alone. The live run confirmed this is what actually happens (ledger cycle
2: `insufficient_independent_sources (only ['goldapi_spot'] answered fresh;
stale: ['yahoo_gc_futures'])`, no position opened).

## 2026-10-10 (M13, ledger hygiene) — archived the pre-correction gold ledger

**Question.** The canonical `M13-GOLD-PAPER` ledger held six rows: a correct
START and cycles 1-2, then two rows written by a defect of mine
(`_track_from_ledger` read `CHECKPOINT` off the raw `history()` record, where
it is nested under `state` and only `ledger.latest()` flattens it), so the
runner rebuilt a fresh track and wrote `cycle 1` twice more. Zero trades were
ever closed. Should those rows be removed?

**Choice.** Not removed — archived verbatim, then the ledger restarted.

**Reason.** The ledger's whole purpose is tamper-evidence, so rewriting it in
place is not available, and the duplicate rows are not a defect of the paper
track: they are a defect of the writer I had just written and already fixed.
Left in place they would make the M42 reconcile permanently DISCREPANCY for a
reason unrelated to the system's own behaviour, which would teach the wrong
lesson (that the judge's verdict is noise). The archived copy keeps its intact
hash chain and remains verifiable, so nothing is lost; the fresh ledger is the
one the corrected writer produces. Recorded here rather than in the ledger
itself because the ledger is the audited object, not the audit log. The judge
reported the duplicates as `J-CYCLE` before the archive, which is the
behaviour the tests pin.

## 2026-10-10 (M13, acceptance) — risk and breaker wired as an entry gate

**Question.** `architecture/markets/risk.py` implements §5 sizing and §12
limits, but a breaker that nothing consults is not a gate. Where does it bind?

**Choice.** It gates *new risk only*, and it is evaluated on every cycle.

**Reason.** Evaluating it only on entries would let it sit silently ARMED
while the limits drift past; evaluating it always keeps its state on the
record. It does not flatten an open position: flattening within 60 s is M39's
live-trading action, there is no live trading here, and the frozen exit card
has no breaker reason — inventing one would extend Lane A's vocabulary through
the back door. The §12 history (closed-trade blotter, equity curve) is replayed
from the ledger by `_track_from_ledger`, so a restart cannot reset the limits.
Only settled closes enter the blotter: an invalidated trade has no price and
therefore no PnL distribution to bootstrap from, so counting it would let the
track buy the 30-trade threshold with trades that never happened.

## 2026-10-10 — the watchdog's `claude -c -p` restart, made reliable

**Question.** The ad-hoc watchdog restart (`claude -c -p`) exits silently, hangs,
and once returned `401 Invalid API key` although both keys work. Fix how?

**Choice.** Replace it with `reports/grok/claude_resume.ps1`, which names the
session instead of continuing "the newest conversation", and which normalises the
four `ANTHROPIC_*` vars from the User scope the same way `run_mission.ps1` does.

**Reason.** Both failure modes had a concrete cause, and neither was the key.
`claude -c` means *the most recent conversation in this directory* — it does not
name the stalled session, so it can latch onto a different transcript and exit
with nothing to say (the silent exit) or block on one that cannot continue (the
hang). On this machine the newest transcript is the *interactive* session, which
a headless resume would write turns into. The 401 was the same shadowing bug
`run_mission.ps1:4` already solved: a process-scoped `ANTHROPIC_API_KEY` left in
the launching shell's environment shadows the working `ANTHROPIC_AUTH_TOKEN`, so
the gateway rejects a key that is individually valid. The fix is to copy from the
User scope and *remove* the process value when the User one is absent — never to
pick a key.

**Tested once, live:** mission 10's session resolved from its own runlog, the
model derived without a literal, and the reply came back `429 Token quota
exhausted` — a real account limit, not an auth failure. The `unrecognized_model`
notice on stderr did not poison the verdict, because stderr is folded into the
classified text only when stdout carries no reply. The same classifier regexes as
`run_mission.ps1` are reused, so a quota outage stays a non-chargeable INFRA and
is never escalated to an owner gate as though the mission had failed.

**Four defects the test exposed, all fixed:** the `claude.ps1` shim writes
UTF-16LE, so the log read mojibake (now decoded by BOM); `Stop-Job -Force` is not
a PS 5.1 parameter and crashed the timeout path (now `Stop-Job` plus a CIM sweep
that kills the orphaned `claude.exe`, which `Stop-Job` alone leaves running —
that orphan *is* the hang); `Get-Process` has no `CommandLine` in PS 5.1, so the
first kill filter matched nothing (now `Get-CimInstance`); and a logging failure
under `$ErrorActionPreference='Stop'` would have aborted the script before it
could report (now `try`/`catch` around every `Log`).

## 2026-10-10 — step 7: CC-3 / CC-4 / CC-1 assessed, none blocking

**Question.** The overnight order lists three defects to fix "along the way if
they block" (CC-3 NameError, CC-4 cycle_duration_ms outliers, CC-1 daemon not
using ControlPlane). Fix any?

**Choice.** None. CC-3 is a latent typo, corrected only in the sense of being
recorded; CC-4 and CC-1 are not defects.

**Reason.**
- **CC-3** — `architecture/ai/debate_council.py:107` annotates `-> Tuple[...]`
  without importing `Tuple`. It is annotation-only (`from __future__ import
  annotations` makes it a string, never evaluated), the module imports cleanly,
  and `Tuple` is absent from its namespace at runtime. It cannot fire. It was
  not fixed because it does not block anything tonight, and an out-of-scope edit
  to an AI-layer file during a gold mission would be scope creep against the
  same codebase that just passed 124 M13 tests. Left for a dedicated cleanup.
- **CC-4** — `cycle_duration_ms` is computed and recorded correctly
  (`observation_loop.py:281` rounds to 2 dp; `record_metric` never raises). An
  "outlier" is a genuinely slow cycle being measured. Clamping or filtering it
  would make operational telemetry report a number that is not the observation —
  the UNKNOWN > fabricated law, applied to metrics. If slow cycles matter, the
  fix is to investigate them, not to unsee them.
- **CC-1** — the daemon does not use ControlPlane because it is not supposed to.
  `launcher/__init__.py:14` names `architecture.control_plane.ControlPlane` as
  the ONE operator surface, and `launcher/control_plane_bridge.py` is the wiring
  the launcher uses to start the engine. Having the daemon reach into ControlPlane
  directly would create a second operator surface, which is the fragmentation
  M34 measured and the plan consolidates away.

---

## 2026-10-10 — M-D3 truth badge and design tokens (dashboard mission 3)

**Question.** The M-D3 spec (`reports/grok/dashboard/CLAUDE_BUILD_MISSIONS.md`)
asks for a token table, a badge contract with precedence
`REJECTED > CONFLICT > UNKNOWN > STALE > VERIFIED`, and a selftest proving
UNKNOWN and CONFLICT cannot be styled as success. Four judgement calls arose.

**Choices and reasons.**

1. **The token hexes had to be corrected against the spec, not authored.** My
   first `dashboard_tokens.ts` wrote plausible-looking values (Imperial
   `#0A0608`, crimson `#C8102E`, gold `#D4AF37`). Reading
   `DASHBOARD_DESIGN_SPEC.md` §2.1 showed every one of them was wrong: Imperial
   `bg` is `#0B0709`, `gold` is `#D4AF5A`, and there is no `surfaceRaised` token
   at all. The mission says "the tokens exactly match the spec hex values", so
   the table was rewritten from §2.1/§2.2 and now declares only the tokens those
   tables declare — `panelEdge`, `goldHi`, `crimson`, `crimsonHi` and `ember` are
   `null` in Neon, because §2.2 does not give Neon those rows. Chosen because a
   token table that invents a value is exactly the fabrication the module exists
   to prevent, and because the two themes genuinely have different token sets.

2. **Neon's hairline is derived, and the derivation is stated and checked.** Neon
   has no `panel-edge` row, but a hairline is needed. `deriveEdge(panel, text)`
   blends the panel 15% toward the theme's own body text. Validated by applying
   the same rule to Imperial, where the spec *does* give both values: it produces
   `#372E2E` against the spec's `#3A2A1C` — the same luminance family, so the
   rule is faithful rather than tuned. The spec value always wins where it exists;
   the derivation is marked `DERIVED` in `globals.css` and asserted in the
   selftest.

3. **The enum map was carrying vocabulary no Python module declares.** My first
   `STATE_TO_BADGE` contained `PAPER_CANDIDATE`, `SECURITY_REJECT`,
   `SINGLE_SOURCE`, `INSUFFICIENT_SOURCES`, `SOURCE_DISAGREEMENT`,
   `PROVIDER_ADDRESS_MISMATCH`, `INSUFFICIENT_LIQUIDITY` and `NOT_FOUND`. None of
   these is a value the authority chain declares — I had inferred plausible names
   instead of reading the enums. The real sets are `IdentityState`
   (VERIFIED/CONFLICT/UNRESOLVED/INVALID/STALE/UNSUPPORTED), `SecurityState`
   (PASS/REJECT/INCOMPLETE/STALE), `CanonicalReadStatus`
   (AVAILABLE/UNAVAILABLE/STALE), `CanonicalOutcome`
   (BUY/WATCH/SKIP/REJECT/INSUFFICIENT_EVIDENCE/HIGH_RISK/MONITOR_ONLY/NO_TRADE)
   and the council's `DISAGREEMENT`. The table now contains only those, and the
   selftest re-reads the four Python files plus `canonical_read_model.ts` and
   asserts every key is among the declarations — so a future invented key fails
   the build instead of passing as a mapping of something real.
   `CanonicalOutcome`'s SKIP/HIGH_RISK/MONITOR_ONLY/NO_TRADE are deliberately
   *absent*: an abstention is not a measurement, and the fall-through to UNKNOWN
   is the honest rendering of it.

4. **Only VERIFIED gets the success treatment; UNKNOWN is the only silent state.**
   CONFLICT and REJECTED keep *alert* sound ids. They are results — the council
   says "DISAGREEMENT IS A RESULT" — and an alarm is not a celebration. UNKNOWN
   alone has no sound at all, because an unmeasured state has nothing to announce.
   The selftest asserts what the mission actually forbids: that no non-VERIFIED
   state carries the *success* sound, the turquoise variable, the ✓ glyph, or the
   glow class.

5. **`TruthBadge.tsx` lives at the repo root, not `components/`.** The spec names
   `components/TruthBadge.tsx` but flags the folder as TO-CONFIRM; the repo keeps
   its TS modules at the root (`CommandCenter.tsx`, `dashboard_truth.ts`) and has
   no `components/` directory. Chosen to match the existing convention, and
   because `@/TruthBadge` then resolves exactly like the `@/dashboard_truth`
   import it sits beside.

6. **REJECTED's glyph is ✕, not the spec's octagon.** No monochrome octagon has
   reliable coverage in the bundled font stack, and an emoji-presentation octagon
   would inherit platform colour, undermining "colour is never the only cue". The
   octagon's stop-sign meaning is carried instead by §2.3's other cue for that
   row, the solid red bar (`border: "bar"`, rendered as a thick left edge).

**Also recorded — two findings that came back UNKNOWN rather than verified.**

- **Vazirmatn `tnum` is unverified.** The Google-served CSS for the family
  declares no `font-feature-settings` at all, so nothing currently enables
  tabular numerals in the dashboard. Determining whether the font *binary*
  contains the feature requires the M-D2 font package (owner-gated `npm i`); the
  attempted direct download of the `.ttf` returned an error page. Recorded as
  UNKNOWN for M-D2 to settle, not guessed either way.
- **The two M-D3 screenshot deliverables were not taken.** The repo has no
  screenshot capability and no new tooling may be installed, so
  `M-D3/01_badge_sheet_imperial.png` and `02_badge_sheet_neon.png` do not exist.
  Instead the spec'd dev-only badge sheet was built at `app/badge_sheet/page.tsx`
  (watermarked FIXTURE, names no token, renders only the contract) and verified
  by rendering it in a real browser: 25 badges SSR'd with the correct modifier
  classes, and a DOM check that exactly the five VERIFIED badges read
  `--ahos-status-verified` while zero non-VERIFIED badges do. The compiled CSS
  was inspected to confirm both `[data-theme]` blocks and all five status
  variables ship at the spec hexes.

**Bug caught by the browser pass, not by the unit tests.** The badge `fill`
strings embedded the custom property *name* without `var()` —
`color-mix(in srgb, --ahos-status-verified 16%, …)` looks plausible, is invalid
CSS, and renders nothing. A unit test comparing strings cannot see this; the SSR
markup did. Fixed, and the selftest now asserts every fill wraps its variable in
`var()` so the class recurs.

**Status.** M-D3 COMPLETE: `npm run test:truth-badge` 44/44,
`npm run test:dashboard-truth` 34/34 regression, `npx tsc --noEmit` clean,
`npx eslint` clean on all touched files, badge sheet verified rendered. Committed
as the M-D3 commit. Screenshots remain open for the owner to take from
`/badge_sheet` in the app window M-D1 built.

---

## 2026-10-11 — M-D4, and the M-D5 Dashi pivot

**M-D4 committed as-is** (`e73ff7b`), per the owner's instruction. The snapshot
vocabulary moved out of `CommandCenter.tsx` into `dashboard_snapshot.ts`
(−207/+15 in CommandCenter), `tsc --noEmit` clean. Polishing of the old Command
Center stops here.

**A regression I introduced in M-D1 was caught by the full suite.**
`test_phase18_launchers.py::TestNoVisibleConsole` statically scans every
`subprocess.Popen` for a console-suppressing flag, and
`launcher/appwindow.py:291` — the POSIX branch of M-D1's window launcher — had
neither `creationflags` nor `windowsHide`. The Windows branch did, which is why
it slipped past the targeted launcher tests. Fixed with `windowsHide=True`,
which is the correct default for a GUI launcher on any platform and a no-op off
Windows; 77/77 in the two launcher files. Committed as `37977a2`.

**Full suite result after M-D3: 2 failed, 3350 passed, 4 skipped** (62 min).
One failure is the known pre-existing `test_execution_state` isolation defect
(this host's baseline; not a regression). The other was the appwindow one above,
now fixed. Baseline for future runs is therefore 1 known failure.

**The owner's pivot: build the new Dashi main screen from scratch.** The old UI
is rejected. The queue is authoritative: `TEAM_QUEUE_2026-10-11.md` M-D5.1..M-D5.6,
and the owner removed the M-D5.0 package gate at 02:17 ("install the listed free
packages … without asking"). I followed it.

**M-D5.1 — prototype review** (`docs/dashboard/PROTOTYPE_REVIEW.md`, committed
`73a03e4`). The headline: of the "five three.js prototypes" exactly one contains
real R3F, and it uses `<Environment preset="night">` — the exact
raw.githack.com fetch REFERENCE_BOARD ref 9 forbids. Its `Math.random()`
placement breaks spec §1's "deterministic hash of tokenKey so it stays stable
between refreshes", and its cyan/violet/pink decoration lands on top of
VERIFIED's and CONFLICT's status hexes, which §2.3 forbids as decoration. Six
patterns are carried forward *rewritten*; three are rejected with reasons.

**M-D5.3 — the quality probe is written and proven** (uncommitted, see below).
`components/stage/quality.ts` splits measurement (impure) from decision (pure):
`resolveTier` is a pure function of a plain record, so the whole T0..T3 ladder is
assertable on a machine with no GPU. `scripts/quality_selftest.ts` is 39/39.
The decisions worth recording:

- **An unavailable measurement is never a low one.** A null `fps` or null `ramGb`
  does not demote — null is "we could not measure", and reading it as "slow"
  would turn UNKNOWN into a fabrication, the exact thing the badge law forbids.
  This is asserted explicitly.
- **The override may raise but the limits still win.** A user can wish for T3 on
  an 8-core machine; they cannot wish for a backend that does not exist. When a
  cap bites an override, the reason becomes `override-capped` and the Persian
  line says the wish was lowered, so the chip never implies the user got what
  they asked for.
- **`prefers-reduced-motion` is not an input to `resolveTier`.** Spec §11 says it
  is combinable with any tier; it changes the motion budget, not the renderer.
  Putting it here would have made it demote the tier, which is wrong.
- **The frame test is documented as synthetic.** 2000 scissored clears per frame
  for 2 s on a 512² context, shader-free so it measures the same on every driver.
  Its number is *not* the scene's fps — that is M-D5.6's overlay — and the
  docstring says so, because presenting a synthetic number as the app's
  performance would be a fabrication.
- **The "never from the machine name" rule is asserted mechanically, not in
  prose.** The selftest strips comments and then asserts no `userAgent` /
  `platform` / `vendor` / `hostname` / `oscpu` identifier reaches code, and that
  `navigator` is touched only through the three measured properties. It scans
  property *names* rather than `navigator.` chains, because a chain can be hidden
  behind a local alias — that distinction cost two iterations to get right.

**M-D5.2 — the stage and shell are written** (uncommitted). `Stage.tsx` is the
empty gold-lit observatory floor: lacquer disc with clearcoat, a gold edge ring
at §14's metalness 1 / roughness 0.28, and a 10-fold shamseh engraving generated
by index arithmetic (no copied art). The metal reflects a PMREM environment built
from two emissive quads in code, so gold reads as gold with zero fetches — that
is the direct replacement for the prototype's banned `<Environment preset>`.
`DashiShell.tsx` is the 56px RTL top bar with the PAPER ONLY pill bound to
`/api/command`'s `executionMode` (a missing mode renders UNKNOWN, never "paper"),
the measured tier chip, and the M-D5.4 context-loss fallback to a Persian notice
with a retry. `/command_center` keeps the old surface alive and reachable.

### BLOCKED_TOOL_PERMISSION — the M-D5.0 install

`npm install` was **denied by the Claude Code auto-mode safety classifier**
("Stage 2 classifier error — blocking based on stage 1 assessment"), after
several classifier timeouts on the same command. Per OWNER_DECISIONS Q3 this is
recorded rather than routed around: the exact command, the pins and the licence
table are in `docs/dashboard/PACKAGES.md`, and I did not retry it through another
tool, shell or interpreter.

Consequence, stated plainly: `npx tsc --noEmit` has **46 errors**, all of them
missing-module resolution for `three`, `@react-three/fiber`, `zustand` and
`detect-gpu` (plus the JSX intrinsic elements R3F's types provide). Not one is a
logic error in the new code; `quality.ts` has exactly one, the `detect-gpu`
import. **The stage has never rendered and no M-D5.2 screenshot exists.**
`npm run test:stage-quality` (39/39) and `npm run test:truth-badge` are the
regression signals that still work, since they need none of the blocked packages.

I therefore committed only what compiles — the two docs and the
`/command_center` route — and left the stage, the shell, the store, the probe and
the modified `app/page.tsx`, `package.json` and `globals.css` in the working
tree. The committed main route still renders the old Command Center, which is
the safe state: no half-built main screen ships while the gate is closed. When
the install clears, one commit lands M-D5.2/M-D5.3 and flips the main route.

### 2026-10-11 — M-D5.0 install cleared; the detect-gpu API was wrong in two ways

Soltan ran the pinned install on the laptop (2026-10-11 10:04, exact
`PACKAGES.md` command, 99 packages added). All 11 pins verified at their exact
versions. `npx tsc --noEmit` went 46 errors → 1 → 0; `test:stage-quality` 39/39.

**Q: the one remaining tsc error was `getGpuDevice` — how should detect-gpu be
called?**
**A:** `getGPUTier`, not `getGpuDevice`. The package exports only `getGPUTier`
and returns `{ tier, type, isMobile, fps, gpu, device }`.
**Why:** the name I had written does not exist in 5.0.70. README_FOR_CLAUDE
v1.38 flagged it.

**Q: `benchmarksURL` — file or directory?**
**A:** **Directory.** detect-gpu fetches `${benchmarksURL}/${model}.json` per GPU
family (`d-intel.json`, `d-nvidia.json`, …), so the `/benchmarks/benchmarks.json`
I had wired would have 404'd every lookup.
**Why:** read from `detect-gpu/dist/detect-gpu.esm.js` and its `.d.ts` rather
than guessing. **How to apply:** the 16 JSONs (713 KB) are now vendored at
`public/benchmarks/` and `BENCHMARKS_URL = "/benchmarks"`, which closes PACKAGES
"Open" item 1 and keeps the M-D2 zero-external-request contract real rather than
documented.

**Q: detect-gpu's `tier` means discrete GPU — yes?**
**A:** **No.** Its ladder is framerate, not card class: tier 1 ≥ 15 fps,
tier 2 ≥ 30 fps, tier 3 ≥ 60 fps in its benchmark scene. My comment claiming
"tier ≥ 2 is a dedicated-class card" conflated the two.
**Why:** the library's own README, line 44. **How to apply:** the probe now
treats tier ≥ 2 as "sustained 30 fps in the benchmark", documents that as what
it is, and — the load-bearing part — accepts **only** `type: "BENCHMARK"` as a
measurement. `FALLBACK` (no renderer string) and `SSR` (no window) are the
library guessing, and a guess handing back `false` would read "we don't know" as
"it is slow", the exact fabrication AHOS law forbids. They hand back `null`
instead, which `resolveTier` never reads as a low value.

**Q: is `hardwareTierSync`'s "GPU" promotion still honest?**
**A:** Yes, with the wording fixed. The `true` arm no longer says "a dedicated
card is the stronger signal"; it points at `probeQuality` for what was actually
measured. The spec's T3 wording ("WebGPU + discrete GPU") is unchanged — that is
the design's vocabulary for the rung.

### 2026-10-11 — M-D5.2 renders; two probe defects that were fabricating the tier

The stage rendered for the first time. Capturing it required a CDP-driven
screenshot harness (`scripts/screenshot_dashi.mjs`) because `chrome --screenshot`
fires at the load event, before the `ssr:false` dynamic import resolves — every
plain screenshot was byte-identical to the loading placeholder. The harness polls
the tier chip and captures only after the probe lands.

**Q: the chip said T0 / "بدون WebGL" on a machine that has WebGL2 and 60 fps.**
**A:** The probe was racing the bundle parse. `StageLazy` mounted on the store's
T1 *default*, so `three.js`/R3F was being parsed on the main thread while
`frameProbe` counted `requestAnimationFrame` ticks. The fill-rate test therefore
measured bundle-load contention, reported < 24 fps, and `resolveTier` honestly
demoted to T0 from a dishonest number — the stage then never mounted, so the bug
was self-confirming.
**Why it matters:** the defect was invisible from inside the code. `resolveTier`
is pure and 44/44 correct; the wrong verdict came entirely from *when* the
measurement was taken. Honest logic fed a contaminated input still fabricates.
**How I found it:** the CDP harness traced every `getContext` call from boot —
all succeeded, which ruled out a missing backend and left timing as the only
explanation.
**Fix:** `DashiShell` no longer loads the stage until `verdict !== null`, and a
third render state ("در حال سنجشِ توانِ گرافیکی") covers the measuring period
instead of the T0 fallback — nothing has failed while the probe is in flight, so
the fallback notice would have been a false claim. After the fix the same machine
probes **T1** with a real `<canvas>` mounted.

**Q: an Intel HD integrated part was labelled "گرافیک مجزا" (discrete GPU).**
**A:** `probeQuality` read detect-gpu's `tier >= 2` as a dedicated-class flag.
detect-gpu's tier is a **framerate** ladder (1 ≥ 15, 2 ≥ 30, 3 ≥ 60 fps), not a
card class, so an integrated part clearing 30 fps introduced itself as discrete —
and the chip stated that as a hardware fact.
**Why it matters:** this is the exact fabrication `UNKNOWN > fabricated` exists to
prevent. The chip is presentation, but the label asserts a hardware class the
measurement never established.
**Fix:** new `dedicatedClass(renderer)` reads the renderer *string* instead, and
only excludes known-integrated families — `null` for anything unreadable or
unrecognised, so absence of a match is never read as evidence of integration.
`probeQuality` also now accepts only `type: "BENCHMARK"` as a measurement, since
`FALLBACK`/`SSR` are detect-gpu guessing. Covered by five new selftest cases
(44/44 total), including the laptop's literal renderer string and an
Intel-Arc-substring ordering trap.

---

### 2026-10-11 16:00 — the tier chip claimed 8 cores on a 4-core machine

**Q:** the production capture (`05-prod-build-t1.json`) reported
`navigator.hardwareConcurrency = 4`, but the chip's hardware span read
«۸ هسته» — "8 cores".
**A:** the chip rendered `HARDWARE_LABELS[verdict.hardware]`, and
`hardwareTierSync` clamps **every** count below 12 into the `T8` band. The band's
label was being stated as a point measurement. The T8/T16/T32 ladder is not in
the spec — CLAUDE_DASHBOARD_2050 rule 3 defines a two-valued hardware axis
(discrete vs integrated); the core ladder is M-D5.3's own addition, and its names
were never measurements.
**Why it matters:** the third fabrication of a hardware fact in this probe, and
the same class as the other two: a classification presented as a measurement.
The chip is the surface the owner reads to trust the tier, and "8 cores" on a
4-core machine is a false hardware claim, not a rounding.
**Fix:** the verdict now carries the measured count (`verdict.cores`, from a new
`measuredCores()` impure getter) *alongside* the band, and the chip states the
count — «۴ هستهٔ منطقی», with "logical" because `hardwareConcurrency` counts
hyperthreads, not physical cores. `HARDWARE_LABELS` now name the **edges** each
band covers ("under 12 cores" / "12–23 cores" / "24 cores or more", mirroring
`hardwareTierSync`'s clamp boundaries) and appear only in the title, introduced
as a band. A null count is unknown, never a low one — the same law as a null fps.
Covered by a new selftest suite (48/48 total). Verified live: chip text
«۴ هستهٔ منطقی», title ending «دستهٔ کمتر از ۱۲ هسته».

---

### 2026-10-11 16:35 — M-D5.4 verified by provoking a real context loss

**Q:** the fallback path (`StageLifecycle` → `FallbackNotice` → `retryStage`)
was written in M-D5.2 but nothing had ever forced a WebGL context loss, so the
listener was unverified code.
**A:** `scripts/screenshot_contextloss.mjs` calls `WEBGL_lose_context.loseContext()`
on the stage's own context — the driver then raises a **real** `webglcontextlost`,
the exact event the listener must survive. Dispatching a synthetic Event would
have tested only the `addEventListener` call.
**Why it matters:** the acceptance criteria ("fallback to 2D with a Persian
notice; no data loss on a live tier switch") are not reachable from the app on
its own; without provoking them, "it works" would have been an assumption about
error-path code that had never run.
**Result:** canvas 1→0 with the `role="alert"` notice, retry re-probes and
restores it, and a down-then-up tier switch (T1→T0→T1) keeps the shell's pill and
caption data intact. `overrideAfter: null` confirms the floor click clears the
override rather than stranding the machine at T0. Two polling bugs in the first
draft of the test would have passed a switch that had not happened — the chip
never returns to `pending` during a re-probe, and a second consecutive switch
needs its own reference class. Both are documented in the step README.

---

### 2026-10-11 17:10 — M-D5.5 the shelf registry is served by one route, and a missing registry is never an empty list

**Q:** the panel must list ideas «منتظر ارتقا» from `config/idea_shelf.json`,
which does not exist yet (M59.S has not shipped). Serve it from `public/`, or
through an API route? And what does a missing file render as?
**A:** one server-side route (`app/api/idea_shelf/route.ts`) reads the file from
`config/`; the registry is deliberately **not** copied into `public/`. A missing
or unparseable file renders a grey `TruthBadge` UNKNOWN, never an empty list, and
there is no fallback list of idea names anywhere in the panel.
**Why it matters:** a file in `public/` would put a second, browser-fetchable copy
of the registry beside the one M59.S reads as its single source — the two could
drift, and the dashboard would be showing a roadmap the owner's registry never
issued. The route keeps the read through one place. And `parseShelf(null)` →
`UNAVAILABLE`, because an empty list is a *claim* ("everything fits on this
machine") that a missing file cannot support; this is `UNKNOWN > fabricated` at
the layer where a corrupted registry would otherwise look like good news. The
same law governs the edges: an idea with an unrecognised tier tag is neither
runnable nor blocked, and an unknown *machine* tier means the panel says unknown
rather than "everything is waiting".
**Result:** 22/22 in the new selftest; the capture records `/idea_shelf.json` →
404 (the decision showing up in the browser) and `/api/idea_shelf` → 401 in the
headless browser, which is the auth gate every dashboard route sits behind — so
the capture's UNKNOWN badge is the required presentation, and the script logs the
raw 401 body so it is not mistaken for the missing-file branch.

---

## 2026-10-11 — M-D5.F: §2.3's fill is a swatch, never a text background

**Question.** The owner's 19:42 QA list (item 1) reports the top-left chip's text
as *still* hatched and unreadable after M-D5.F was believed done. Where does the
hatch come from, and may §2.3's hatch be removed to fix it?

**Choice.** Keep the hatch; move it off the text. The cause was not the pattern
but where it was painted: `globals.css` set `background: var(--badge-fill, …)` on
the `.truth-badge` span itself, so UNKNOWN's 45° gradient ran *behind the label*
and its 1px lines crossed the Persian glyphs at 0.75rem. The fix renders the fill
on a `0.7em` swatch beside the glyph and makes the badge root and the label span
transparent. The top-left chip is that UNKNOWN badge — the PAPER ONLY pill holds
`TruthBadge state="UNAVAILABLE"` whenever `/api/command` reports no known mode,
which is the state the owner's screenshot and the headless capture both show.

**Reason.** §2.3 mandates the hatch as UNKNOWN's non-colour cue, and the
selftest asserts the fill uses its own colour variable; deleting it would weaken
the contract the badge exists to enforce. The illegibility was a presentation
bug, not a spec defect, so the honest fix changes the surface, not the cue. The
same reasoning declined two larger changes: no font binary was vendored, because
Vazirmatn is already wired through `next/font/google` under `--font-vazir`
(self-hosted at build, no runtime fetch) and the illegibility was never the
typeface; and the 4.5:1 floor is now a WCAG-luminance assertion over every
state on both themes' `bg` and `panel` rather than a judgement call.

**Result.** `test:truth-badge` 47/47 (44 + 3 new, including the tightest case —
UNKNOWN's `#9AA3B2` on Imperial's `#160E12` panel at 7.46:1). The capture harness
now reports the badge's computed backgrounds, so the fix is proven in DOM state
(root `none`, label `none`, swatch `PATTERN`) and not by eye. Its new
`overrideTier` arg seeds the app's own override before boot, so the required T3
capture goes through `resolveTier` and the chip's title still names the pick as
manual — no hardware claim is fabricated by the preview.

---

## 2026-10-11 — the capture harness waits for the stage, not the chip

**Question.** `screenshot_dashi.mjs` reported `canvas: 0` on a T1 verdict that
should mount the stage. Capture anyway?

**Choice.** No. The poll broke the moment the tier chip left `pending`, which
fires when `probeQuality` lands (~6s), while `StageLazy` was still fetching and
parsing the three.js chunk — exactly the bundle-parse contention `DashiShell`
documents as the reason the probe runs first. The poll now waits for the canvas
the verdict allows, or for the 2D `dashi-fallback` when it does not allow one,
within the same settle budget.

**Reason.** A capture taken on the stage's loading line would show an empty
stage, and the queue forbids a step ending there; a screenshot that looks empty
would read as a defect in work that is correct. The change is to the harness's
wait condition only — the verdict and the scene are untouched, so it cannot make
a capture more flattering than the truth, only more patient.

**Result.** `canvas: 1` in both the measured-T1 and forced-T3 captures, with the
chip text and the badge computed styles reported alongside.

---

## 2026-10-11 — the idea-shelf seed: tags only where the vetting assigned them

**Question.** Item 2 of the owner's 19:42 list asks for a seed
`config/idea_shelf.json` from the real approved items, "with tiers from Asi's
vetting". Laya and Kev are approved but their hardware fit was never vetted. Tag
them anyway, since a 421M model and a 0.8B one obviously fit in 8 GB?

**Choice.** No. Ship them with `tier: null`. The registry carries the nine tools
the owner named plus the two later same-day approvals (light-ocr, BitNet b1.58),
with a tag only where a vetting line actually assigned one: T16 for Vane,
OpenSandbox, Browser Use and AnythingLLM; T8 for Uptime Kuma, light-ocr and
BitNet's 2B4T helper. `est_ram_mb` is absent everywhere, because no vetting line
gave a number and the panel only renders a RAM count when one exists.

**Reason.** The shelf's own contract is that an untagged idea is neither runnable
nor awaiting — listing Laya as awaiting would claim a requirement the registry
never recorded, and tagging it T8 would claim the opposite, that this machine is
known-good for it. Either is a hardware fact manufactured from a guess, and the
DEDUP notes are explicit that both are open ("RAM unverified", "verify Windows CPU
fit") — their «Kev-0.8B likely T8» is a hunch in a vetting whose whole point is to
convert hunches into measurements. Obviousness is not the test; `UNKNOWN >
fabricated` is. The selftest pins the choice: the `null` set must be exactly
Laya and Kev, so a future edit that tags them fails the suite unless the
expectation moves with it — which is the prompt to update the vetting record the
file is seeded from.

**Result.** `test:idea-shelf` 26/26 (22 + 4 new, all four reading the committed
file rather than a fixture). On a T8 machine the panel now lists exactly the four
T16 tools under «منتظر ارتقا». One judgement call recorded against the grain: the
14:33 AJI note says «AnythingLLM/Hermes3D/GitBot SKIP» while 06:48 says «AnythingLLM
shelf T16» and the owner's 19:26 list names it; the most recent explicit
instruction wins and it is seeded at T16, with the contradiction noted here rather
than silently resolved.

---

## 2026-10-11 — declined to open the Web API gate for a capture

**Question.** The panel's OK branch cannot be photographed headlessly:
`/api/idea_shelf` answers 401 RESTRICTED without a dashboard session, which only
the launcher establishes. Start a second dev server with
`AHOS_WEB_API_ALLOW_OPEN_ACCESS=1` on a free port to capture it?

**Choice.** No. Ship the selftest as the proof and capture the branch the
headless browser can actually reach.

**Reason.** The flag is documented as local/mock-only, so the choice is legal, but
it weakens an enforcing control to produce a screenshot, and the control is one
AGENTS.md names explicitly — the gate is what keeps a headless browser, and
anything else without a session, off the dashboard routes. Two dev servers in one
tree would also contend over `.next`. The unproven link is thin: the route is
unchanged since M-D5.5, the panel is unchanged, and the only new artifact is the
registry, which four new assertions read from disk through the same `parseShelf`
and `awaitingUpgrade` the route uses. The capture that *was* taken proves the
other half of item 2 — the 401 branch renders grey UNKNOWN text with no hatch,
because item 1 moved the fill off the label.

**Result.** The receipt names the gap instead of papering over it: the owner's own
window shows the OK branch, the suite proves its contents, and no auth gate was
loosened for a picture.

---

## 2026-10-11 — the globe renders no data, and gold is its only light

**Question.** The owner's item 3 asks for a globe and item 4 asks for it now. Does
the stage get to show anything about the market on it — a lit region, a marker, a
colour shift?

**Choice.** No. The globe is ornament: no geography, no markers, no verdict
colours. Its only emissive surface is the brand gold.

**Reason.** Two rules converge. The TS lane is presentation-only and must not
become a recommendation authority, and a marker on the globe *is* a recommendation
if it is not labelled data. And spec §2.3 forbids status colours as decoration —
lighting a hemisphere in VERIFIED's turquoise would tell the owner something the
truth badge in the DOM is the only permitted voice for. So the globe's contract is
written into its receipt, not just its code: if a marker ever appears it has to
come from `/api/command` and be labelled, and nothing in `Globe.tsx` is wired for
it. This also keeps M-D6 honest — the data rings are a separate artifact with
their own authority questions, and bolting them onto a decorative globe now would
blur the line.

**Result.** The stage gained a centrepiece and gained zero authority surface.
`test:stage-quality` stays 48/48 because nothing it asserts moved.

---

## 2026-10-11 — a fresnel shell instead of a bloom pass, at every tier

**Question.** Item 3 asks for "a gold rim light and soft bloom done in a shader or
CSS" but also "no heavy postprocessing on T1". Give T1 the rim only and T2/T3 the
real bloom chain?

**Choice.** Ship one overdrawn fresnel shell on a BackSide sphere for all tiers.
Do not bring the bloom chain in this step at all.

**Reason.** The item's own wording allows the shader route, and the shell is it:
additive, one extra draw call, no render targets, no cost worth measuring
separately — the capture's scene fps is 56 at T1 and 60 at T3 *with* it. Adding a
second, tier-gated implementation of the same visual idea would mean two code
paths for one silhouette and a T1/T3 look that diverges for no owner-visible
reason. The bloom chain is M-D5.6's pipeline; when it lands it can replace the
shell where the tier pays for it, and the shell remains the T1 answer.

**Result.** One rim implementation, four tiers, `test:globe` 8/8 and no
postprocessing dependency added to the T1 bundle.

## 2026-10-12

**Q: The G2 gateway gate FAILed while a Next.js dev server was plainly running —
which side moves, the server or `.env`?**
**A:** Move `.env`'s `AHOS_GATEWAY_URL` to the live server, not the server to
the configured port.
**Reason:** The running gateway was launched deliberately as
`next dev --hostname 127.0.0.1 --port 3199`, and M-D5.5 already recorded that
this process is not an agent session's to stop. Nothing at all was listening on
`:3000`, so every consumer pointed at `:3000` was already broken — the config
was stale relative to the host, not the other way round. Retargeting one loopback
URL changes no credential, touches no Lane A, and is reversible in one line; it
is also the change the gate's own remediation text asks for when it says "ensure
npm run dev is up **and** `AHOS_GATEWAY_URL=...`". The force-load in
`operator_validation_gate.py:798` exists to stop a *stale shell export* from
beating `.env`, so exporting `AHOS_GATEWAY_PORT=3199` could not win and editing
the file was the only route that actually closes the gate. After the retarget,
G2 reads `http_200 from http://127.0.0.1:3199/api/chat` and G1-G10 are all PASS,
`pre_soak_entry_ok=true` — the entry condition the owner's 00:01 note asked for.
The one-line rewrite printed only that one line, never the file, and `.env`
stays gitignored.
**Result:** `VERDICT: PRE_SOAK entry OK on this Windows host`; G11 stays
NOT_VERIFIED because it is OPERATOR_READY-only and the owner holds the Telegram
E2E artifact.
