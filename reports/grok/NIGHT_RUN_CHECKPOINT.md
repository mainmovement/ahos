# AHOS night run — live checkpoint

Owner asleep. Order: `حافظه_ادامه/2026-10-09_04-20_دستور_شبانه_ادامه_کار.md`
(steps 1–8 + LOCKED list). Two-source rule:
`حافظه_ادامه/2026-10-09_04-46_قانون_شاهد_دو_منبعی_همه_بازارها.md`.
All times Asia/Tehran. Local commits only, branch `ahos`, never push.

If you are restarted, read this file first and continue from the next step.

## Step 1 — make the identity resolver live — DONE, committed `b5929a7`

- `build_production_resolver()` is now fail-closed: returns `None` unless every
  provider in the default set is present AND declares `requires_credentials =
  False`. `BaseHttpProviderAdapter.requires_credentials` defaults `True`, so a
  provider that forgets to declare itself keyless is never a free unattended
  source. The daemon keeps the single-source UNRESOLVED default and logs a
  WARNING naming the reason instead of silently degrading the two-source gate.
- Live evidence, daemon restarted engine-only (`scripts/restart_engine_only.py`,
  PID 12036 -> 12820, started 04:31:56, run_id `run_1791507717_6810cfbd`).
  First cycle, 12 candidates: 1 VERIFIED (`base` SOL `0x3119…9cf82`, both
  dexscreener+geckoterminal answered, `min_sources_met`), 1 CONFLICT
  (`provider_address_mismatch:geckoterminal` -> REJECT), 10 UNRESOLVED
  (`insufficient_independent_sources`).
- The VERIFIED token's decision is still `paper_allowed=False`, correctly: the
  identity gate passes and the SECURITY gate stops it (INCOMPLETE /
  unknown_critical_security). The blocker moved one gate down the chain;
  nothing was loosened.
- Audit: per-candidate `identity_probe` lines on the `ahos.identity` logger,
  wired in the daemon next to `ahos.main`.
- Tests: `tests/test_multi_source_identity.py` 21 passed. Receipt:
  `reports/grok/IDENTITY_RESOLVER_LIVE_RECEIPT.md`.

## Step 2 — fix the .env-writing test leak — FIX DONE, FULL SUITE IN PROGRESS

The leak (2026-10-09 01:44): `main()` in `scripts/operator_validation_gate.py`
force-loads the checkout's `.env` into `os.environ` and, when
`AHOS_GATEWAY_URL` is empty and `_resolve_gateway()` reports `source ==
"DEFAULT"`, calls
`_persist_env_key(ROOT / ".env", "AHOS_GATEWAY_URL", "http://127.0.0.1:3000/api/chat")`
— a real write into the operator's live `.env` from a pytest run.

Fix (uncommitted, in working tree):

1. `scripts/operator_validation_gate.py` — new module attribute
   `ENV_FILE = ROOT / ".env"`; both `.env` touches inside `main()`
   (`load_dotenv` and `_persist_env_key`) now go through it. Grep confirms
   those are the only two `.env` references in the module. Prevent-by-redirect,
   not restore-after: a crashed or interrupted run leaves no write behind,
   which the old restore-in-a-finally fixture could not guarantee.
2. `tests/test_operator_validation_gate.py` — the autouse fixture is now
   `_sandbox_env_file`, which monkeypatches `ovg.ENV_FILE` to `tmp_path /
   "sandbox.env"` for every test in the file and restores `os.environ` in a
   `finally`.
3. Two regression tests pin it, and both reproduce the *exact* triggering
   condition (no `AHOS_GATEWAY_URL`, `_resolve_gateway` monkeypatched to yield
   `source="DEFAULT"`, so the persist path really executes):
   - `test_main_persists_gateway_url_to_the_sandbox_not_the_repo_env`
     (agent-host, the generic path);
   - `test_windows_runner_never_writes_the_real_env` (the platform that
     actually leaked at 01:44).
   Each asserts the write landed in the sandbox AND that the real repo `.env`
   is byte-identical before/after (via a `_real_env_snapshot` fixture, so the
   assertion holds whether or not a `.env` exists).

Teeth: the tests assert `sandbox.is_file()`. If `main()` ever returns to an
inlined `ROOT / ".env"`, `monkeypatch.setattr(ovg, "ENV_FILE", …)` becomes
inert, no sandbox is created, and the tests fail. They cannot pass against the
vulnerable code. (I attempted an empirical revert-and-rerun to prove this but
the safety classifier timed out on the `git stash` repeatedly; the argument
above is complete without it and the tree was left clean.)

`pytest tests/test_operator_validation_gate.py` — **24 passed**.

**Full suite result (started 09:35, finished ~10:35 UTC): 2961 passed,
4 skipped, 1 failed.**

The one failure is `tests/test_execution_state.py::test_missing_store_reads_no_data_never_ok`
(`assert status["exists"] is False` → `True`). It is **pre-existing and
unrelated**: proven earlier in this session by stashing every change of mine
and parking the two new files outside the tree — the test fails identically on
a pristine checkout. No test was weakened and no failure was hidden to make a
number move. It is left for the owner to decide about (see the morning report).

Step 2 is DONE. Commit `c0c145f`.

## Step 3 — fix the autopilot so it can actually run — DONE

**Root cause, found by probing the real CLI:** the model name was not the
problem. `run_mission.ps1:4` copies the User env `ANTHROPIC_MODEL` (the Atria
gateway serves exactly one id, `Atria-Dawn-Preview`, confirmed by an
authenticated `GET /v1/models` in `M10_1_MODEL_BLOCKER.md`), and `claude -p`
runs on it fine — a live probe returned a real reply. But Claude Code's local
catalog does not describe that id, so it prints an `unrecognized_model` notice
to **stderr on every run, successful or not**, and `run_mission.ps1` merged
stderr into the result file with `*>`. The runner's `Test-InfraFailure`
matches `unrecognized_model` as a substring, so a mission that had completed
was classified INFRA and its work was discarded. The `429 Token quota
exhausted` was a separate, genuine, transient quota outage at the time; the
`unrecognized_model` half is why completed work never counted.

Fix, two coupled parts (both needed):

1. `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` in
   `run_mission.ps1` — the CLI's own documented escape hatch for a model the
   catalog does not know; restores wait-for-the-API instead of catalog-based
   window enforcement.
2. stdout and stderr are now captured separately. stderr is folded into the
   classified text **only when stdout carries no verdict**, so a genuine
   quota/auth failure (stderr, no reply) still reaches `IsInfraFailure` and is
   still classified INFRA, while a successful run's stderr notices cannot
   poison the verdict. Diagnostics are never lost: stderr always lands in
   `_claude_<n>_stderr.txt`.

`tests/test_autopilot_runner.py` — **29 passed** (12 dynamic PS 5.1 harness
cases A–L + static pins).

**Restart:** PID 4516 (runner, started 2026-10-07 08:25, pre-`7ab2fa4`) and
PID 14408 (watchdog) stopped; restarted hidden with
`-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File …` —
watchdog now PID 5904, runner PID 15288, both started 14:51:26 +03:30. The new
runner ran startup reconciliation (every existing gate preserved:
`OWNER_GATE_PRESERVED`), then yielded: heartbeat reads
`phase=INTERACTIVE_CLAUDE note="interactive Claude active"`, "interactive
Claude active -> not launching". `claude.exe` (interactive) untouched.

`autopilot/state.json` M12 counter reset 3 -> 0: the 3 measured quota death,
not work quality (already recorded as the intent in `DECISIONS_LOG.md`; the
stale runner had overwritten the earlier reset). It turned out HEAD already had
`M12: 0` committed, so the edit restored the committed value and is not in the
diff. M12 stays at `NEEDS_REVIEW` while step 4 works it interactively, so the
runner holds the queue and cannot launch a duplicate headless M12 against my
own session.

Step 3 is DONE. Commit `bd93360`.

### Judgement calls (also in `reports/grok/DECISIONS_LOG.md`)
- Prevent-by-redirect over restore-after: restore-in-`finally` still leaves the
  write behind on a crash/interrupt; redirecting the path means the write is
  physically impossible.
- The regression tests trigger the write deliberately rather than trusting the
  fixture — a test that never exercises the leak cannot prove it is closed.
- Module attribute, not a function parameter, so every existing caller of
  `main()` is unchanged and the patch point is one line.

## Step 4 — M12, agent organisation — DONE, commit `a2715ba`

The queue row: "37+ agents in `config/agent_registry.yaml` using the owner
charter template, authority NONE by default, no auto-creation."

The 18 owner-approved agents of `reports/grok/AHOS_AUTONOMOUS_VISION.md` §2.3
(charter set approved 2026-10-03 20:43, #20–#37) are registered as
**AG-26..AG-43**, one per charter, in vision order. The registry now holds 43;
`validate_registry()` returns `{}`.

Key encodings (so nothing is re-derived on a restart):
- **authority NONE by default = `allowed_authority: []`** — omitting the field
  fails the contract's required check; `[]` is the only encoding that both
  validates and is assertable.
- **status `PLANNED`, not the vision's `REGISTERED`** — the registry enum has no
  REGISTERED member; that is the P1§14 *lifecycle* vocabulary. PLANNED keeps the
  EXISTS-needs-real-evidence lint honest: not one of the 18 has an artifact, and
  all 18 have operability all-false.
- **مریم (AG-39) holds VETO in neither list** — her charter grants an
  uncancellable veto, so forbidding it would deny an owner fact, and granting it
  is a governance promotion. Recorded in `ops.notes`.
- **Cross-taxonomy reporting lines are notes, not dependencies** — an AG↔agent.*
  edge would be a silent piece of the OWN-AV-56 mapping (human gate).
- `form: service` everywhere (M10 retired n8n); `lane: B` everywhere.

Deliverables:
- `config/agent_registry.yaml` — 18 entries, `totals` recomputed
  (agents 43, PLANNED 21, boot CRITICAL 16 / ADVISORY 18; operability unchanged).
- `docs/architecture/agent_matrix_v2.md` — regenerated via the generator, FRESH.
- `docs/agents/M12_REGISTERED_AGENTS.md` — the owner-charter index (the vision
  §2.3.3 stays the charter authority; this is an index, never a second source).
- `tests/test_m12_agent_registration.py` — 18 new invariants: the vision#→AG
  mapping table, empty allowed authority, no DECIDE/PROMOTE, charter
  traceability, no Slice-1 auto-creation, acyclic AG-only dependencies,
  non-duplication vs the 19, totals truthfulness.
- `docs/governance/agent_taxonomy_map.json` — stale census corrected
  (25→43, PLANNED 3→21), version 0.1.0 → 0.1.1 with a dated delta note.
- Five docs' census quotes corrected to 43 (incl. `AHOS_REALITY_MAP_v1.md`, whose
  purpose is preventing census overclaims).
- Count pins 25→43 in `tests/test_agent_matrix_v2.py:37` and
  `tests/test_architecture_p1.py:69,72,73,108,110` — the invariants they check
  (doc == generator output, no duplicate ids, totals computed) are unchanged.

Two defects fixed along the way:
1. `engine/agent_matrix_v2.py` wrote the generated doc in the platform codepage
   instead of UTF-8 — the regeneration crashed on Windows (reads were already
   UTF-8). Now the write is too.
2. The census drift in (5) above — the suite does not catch doc census quotes;
   grep is the only check.

Evidence: `reports/grok/autopilot/M12_review.md` — four pre-coding reviews
(آرش / domain specialist / پروانه / گیتی) recorded BEFORE any edit, then the
three sign-offs. **Full suite 2971 passed, 4 skipped, 0 failed** (57:22),
`tests/test_execution_state.py` excluded; its single pre-existing failure is
unchanged and left for the owner. Targeted set: 100 passed.

LISTED for the owner, not decided: the OWN-AV-06 conflict (register via
`ahos_org/registry.py` vs the charter template's prohibition — M34 should carry
it); §2.7 open seats (GH-2, second Guardian, three more AGI/ACI team seats);
OWN-AV-04 (veto matrix, still not encoded); OWN-AV-56 and OWN-AV-62 untouched.

Queue row M12 flipped to DONE with the evidence appended; `state.json` M12
already reads 0. The runner now sees DONE (not launchable), so no duplicate
headless M12.

## Step 4.5 — the owner's model-name report, resolved — commit `59b2548`

The owner asked (interactively, after the queue went quiet) that the autopilot
runner stop hard-coding the preview model name and use whatever this interactive
session uses. Investigated before editing, because step 3 had already concluded
the name was not the blocker — and the live M34 runlog confirms it again:

- `_claude_ap_M34_result.txt` (19:55 and 20:11 attempts) = `API Error: Request
  rejected (429), Token quota exhausted` on stdout, **no verdict**.
- `_claude_ap_M34_stderr.txt` = only the `unrecognized_model` catalog notice.
- Direct dry-run: `claude -p --model <derived>` → the notice on stderr and a
  correct reply on stdout, in one process. The notice is cosmetic and prints on
  every run against this gateway; the run-killer is transient account quota.

So the letter of the ask (change the name) would have changed nothing, and the
spirit is now enforced structurally: `run_mission.ps1` derives the model from
the same source this session uses (User `ANTHROPIC_MODEL`, then the User
`settings.json` `model` field), passes it as an explicit `--model` on both
invocations, and **aborts loudly** if it cannot be derived — a silent fallback
would 400 against a gateway that serves one id. No code or config names the
model now; the only two literals left are test fixtures reproducing the CLI's
real wording. `M10_1_MODEL_BLOCKER.md` — whose title steered two investigations
at the name — gets a dated correction appended (not a rewrite; it is evidence),
retracting its owner-facing "set a model string" items.

`HOLD.flag` refreshed for M34 the same way it was used for M10/M12: M34 is now
the first launchable queue row, so without a hold the headless runner relaunches
it between my turns, duplicating the mission against the same tree. Runner
heartbeat confirms `phase=HOLD note="Grok review hold active"`.
`tests/test_autopilot_runner.py` — 29 passed.

## Step 5 — M34 coherence audit — DONE

Deliverable: `reports/grok/M34_COHERENCE_AUDIT.md` — the seven-axis
canonical-source map, the measured ledger census, the number-mapping table, the
stale-doc corrections, and the deprecate-with-shim merge plan.

Findings in brief:
- **Mandate-level:** INV-31 names **seven** canonical sources; the queue row
  names six and drops the design system. Mapped seven; the count conflict is
  itself a finding (**M-AXIS-7**), listed for the owner.
- **One genuine duplicate implementation:** `engine/bot_skeleton.py` — no live
  caller, its stated consumer (n8n) retired by M10. Merge plan row 1,
  owner-gated. The five agent namespaces are separated **by law** (P2§63); no
  merge proposed. The two cores are a documented, test-pinned boundary.
- **Event bus: zero implementations.** The contradiction is between three ops
  docs saying NOT_JUSTIFIED and the vision's INV-31 law with 11 topics M33.17
  consumes. An owner act, not a code one (**M-BUS-1**).
- **Ledger fragmentation measured** (fresh, `mode=ro`): 6 stores, only
  `paper_trading` (34 triggers/19 tables) and `control_plane_ledger` (6/4)
  fully guarded. `config/control_plane.yaml:60`'s "3 governed sqlite stores"
  was the 2026-08-13 W10A-02 census scope; fixed to carry provenance + the
  current measurement.
- **Nine stale 25-census docs corrected** — M12 fixed five and missed these,
  including `config/agent_registry.yaml`'s own header contradicting its
  `totals`, and `AHOS_REALITY_MAP_v1.md`, whose purpose is stopping census
  overclaims. New `tests/test_m34_coherence.py` pins the three relations that
  broke (204 passed; negative paths verified to fire).
- **Three inherited claims corrected on re-check:** `slills/` is uploaded
  third-party material, **not** a `.cursor/skills` duplicate (routed to M53);
  `data/mission_ledger/` is lazy-by-design, not a defect; the model name was
  never the run-killer (the `M10_1_MODEL_BLOCKER.md` correction, step 4.5).
- **Vision internal defect recorded, not fixed:** its header says 18 new agents
  (20–37) while its own §2.3 table lists 20 through #39 — so **#38 سروش and
  #39 کیان are unregistered**. The vision is the owner's approved charter and
  counts as evidence; it was not edited.

LISTED for the owner (not decided): M-DB-1, M-TRADE-1, M-TAX-1, M-TAX-2,
M-WIN-1, M-AXIS-7, M-BUS-1, M-LEDGER-3, M-MEM-1, M-LAUNCH-1, plus OWN-AV-04/06/
56/62 and the §2.7 seats carried from M12.

NOT done, by design: no merge executed (M34.3 is the *plan*; rows are gated to
M42 / M30 / M53 / owner); M34.5 coherence score not attempted — scoring before
the merges land would measure the fragmentation, not the fix.

## Step 6 — M13 gold-first paper cycle — DONE, commit `5988620`

The M13 acceptance set named by DEDUP_MERGE_MAP v1.20 line 183 — *"only after
M13 gold passes its acceptance (two-source price witness, exit rules, risk,
M42 judge, M39 breaker)"* — is complete, all five on Lane B:

| Gate | Where | Evidence |
|---|---|---|
| two-source price witness | `architecture/providers/gold.py` | commit `95d4618` |
| exit rules | frozen `paper_trading.exit_rules` (import-only) | `check_exits`, EXIT_V1 |
| risk | `architecture/markets/risk.py` | §5 sizing + §12 ruin bootstrap |
| M42 judge | `architecture/markets/judge.py` | independent reconcile, CLEAN |
| M39 breaker | wired into `GoldPaperTrack.run_cycle` | paper half — entry gate |

**The breaker is an entry gate, evaluated every cycle.** A breaker nobody
consults is not a gate, so `PaperBreaker.check` runs before every entry; it
holds *new risk only* and never flattens an open position — flattening within
60 s is M39's live-trading action, there is no live trading here, and the frozen
exit card has no breaker reason, so extending the vocabulary would be a Lane A
edit through the back door. The §12 history (closed-trade blotter, equity curve)
is replayed from the ledger by `_track_from_ledger`, so a restart cannot reset
the loss limits. Only settled closes enter the blotter: an invalidated trade has
no price and therefore no PnL to bootstrap from, so counting it would let the
track buy the 30-trade threshold with trades that never happened.

**The judge never imports the track it audits** (DEDUP:141's independent-reviewer
principle). It replays the ledger and re-derives every number from the recorded
bytes, so a track that wrote a flattering equity claim is *checked*, not
believed. It verifies the chain, the paper form (`paper_only is not True` is a
finding), position continuity, the §49 double-entry on every settled close, the
money identity, that an unpriceable close carries zero PnL, and the track's own
counters against its own claims. One finding is a `DISCREPANCY` — there is no
verdict that means "mostly fine", which is the HALT the vision specifies.

**The judge caught my own bug.** The first `_track_from_ledger` read `history()`
raw rows, where the checkpoint is nested under `state`, so the rebuilt track
always started at cycle 1 and wrote duplicate cycle 1s into the canonical
ledger. The judge reported `J-CYCLE` x2 — evidence the judge works. The
pre-correction ledger was **archived verbatim** at
`data/mission_ledger/archived/M13-GOLD-PAPER_pre_correct_cycles_20261010.jsonl`
(chain verified `CHAIN_INTACT`, head `416c6d6b…`) rather than rewritten in
place, because the ledger's purpose is tamper-evidence; a fresh ledger under
the corrected writer now reconciles **CLEAN**.

Tests: 124 passed across the four M13 modules
(`test_gold_two_source`, `test_gold_paper_cycle`, `test_gold_risk`,
`test_gold_judge`). The judge suite's negative paths were rewritten around
*chain-intact crafted lies* — the first draft used `assert … or True`, which
was vacuous and I flagged it myself. A crafted ledger is the dishonest-track
case the judge exists for; editing a real ledger only ever produces
`BROKEN_CHAIN`.

**Remaining for M13's *target***: 30 closed paper trades. No position has
opened yet — the live feeds have been UNRESOLVED between COMEX sessions. The
gate is honest about that rather than trading a single source.

### The watchdog resume — DONE, tested live

`reports/grok/claude_resume.ps1` replaces the ad-hoc `claude -c -p` restart.
Both failure modes had concrete causes and neither was the key:

- **`claude -c` continues "the most recent conversation in this directory"** —
  it does not name the stalled session, so it can exit with nothing to say
  (the silent exit) or block on one that cannot continue (the hang). On this
  machine the newest transcript is the *interactive* session, which a headless
  resume would write turns into. The script resolves the session from the
  runner's own runlog instead, and refuses to guess — the first dry-run proved
  the point by resolving to this very interactive session.
- **The 401** was a stale process-scoped `ANTHROPIC_API_KEY` shadowing the
  working `ANTHROPIC_AUTH_TOKEN`, so the gateway rejected a key that is
  individually valid. Fixed by normalising the four `ANTHROPIC_*` vars from
  the User scope and *removing* the process value when the User one is absent
  — never by picking a key.

**Tested once, live.** Mission 10's session resolved from its runlog, the model
derived without a literal, and the reply came back `429 Token quota exhausted`
— a real account limit, not an auth failure. The `unrecognized_model` stderr
notice did not poison the verdict, because stderr is folded into the classified
text only when stdout carries no reply. Four defects the test exposed, all
fixed: the `claude.ps1` shim writes UTF-16LE (now decoded by BOM); `Stop-Job
-Force` is not a PS 5.1 parameter (now `Stop-Job` plus a CIM sweep that kills
the orphaned `claude.exe` — that orphan *is* the hang); `Get-Process` has no
`CommandLine` in PS 5.1 (now `Get-CimInstance`); and a logging failure would
have aborted the script before it could report.

## Step 8a — M-D1 app window — DONE, commit `e9d2ddf`

The owner's double-click now opens a dedicated window, not a browser tab.
`launcher/appwindow.py` builds the Chromium `--app=<url>` command line: an
isolated profile at `%LOCALAPPDATA%\AHOS\app-window-profile` (never the user's
Chrome Default), a fixed window size, and a host-resolver rule
`MAP * ~NOTFOUND , EXCLUDE 127.0.0.1` that blocks every non-loopback DNS lookup
at the browser itself. Nine switches keep it a closed loop — no extensions, no
sync, no background networking, no component update, no pings, no proxy. The
argv is a list, never a shell string, so the URL is never visible to other
processes through `cmd.exe`.

The URL carries a one-time boot token, so `open_app_window` never logs it: the
log line names only the browser, the `profile_marker` used to find the process is
the profile switch and never the URL, and an error describing an argv describes it
without the value. Every failure degrades to the legacy `open_url` rather than
failing a launch — no browser installed, a spawn refusal, an unwritable profile
directory — and the fallback prints the Persian line the mission specifies.
`tests/test_launcher_appwindow.py` (24 tests) pins the argv order, the resolver
rule, the profile isolation and the token-reaches-no-log-line property.

## Step 8b — M-D3 design tokens and the truth-badge contract — DONE

The precedence that makes an honest state impossible to style as success,
implemented as data:

    REJECTED > CONFLICT > UNKNOWN > STALE > VERIFIED

A display may only downgrade along that chain. `dashboard_truth_badge.ts` maps
the **real** enum values of the authority chain — `CanonicalReadStatus`,
`IdentityState`, `SecurityState`, `CanonicalOutcome` and the council's
`DISAGREEMENT` — onto badge states, and an unrecognised value falls through to
UNKNOWN. `dashboard_tokens.ts` holds the two owner-approved themes at the spec's
exact hexes (§2.1 Imperial, §2.2 Neon), and `globals.css` is the only place the
theme switches.

Verification — `npm run test:truth-badge` **44/44**, covering every acceptance
criterion the mission names: UNKNOWN and CONFLICT never get the VERIFIED colour,
the ✓ glyph, the glow class or the success sound id; a stale VERIFIED becomes
STALE; `UNAVAILABLE` gives UNKNOWN; a disagreement beats a VERIFIED; an
unrecognised enum gives UNKNOWN. `npm run test:dashboard-truth` 34/34
regression, `npx tsc --noEmit` clean, `npx eslint` clean.

The selftest also guards its own honesty: it re-reads the four Python enum
declarations and `canonical_read_model.ts` and asserts every key in the mapping
table is a value one of them actually declares. My first draft of the table
contained seven invented enum names (`PAPER_CANDIDATE`, `SECURITY_REJECT`,
`SINGLE_SOURCE`, `INSUFFICIENT_SOURCES`, `SOURCE_DISAGREEMENT`,
`PROVIDER_ADDRESS_MISMATCH`, `INSUFFICIENT_LIQUIDITY`) — plausible names for
things no module declares. That is fixed and now mechanically impossible to
reintroduce. See `reports/grok/DECISIONS_LOG.md` for the full account.

The badge is wired into the two truth-bearing surfaces of `CommandCenter.tsx`:
the opportunity dossier (canonical status, identity, security) and the canonical
decisions card (identity, security), replacing the old tone-mapped `StatusPill`
there. The decision and confidence pills stay as `StatusPill` — the display score
is non-authoritative analysis and must not borrow the badge's contract.

**Verified in a real browser, not only in assertions.** A dev server rendered the
spec'd dev-only badge sheet at `app/badge_sheet/page.tsx` (watermarked FIXTURE,
names no token): 25 badges SSR'd with the correct modifier classes, a DOM check
that exactly the five VERIFIED badges read `--ahos-status-verified` while zero
non-VERIFIED badges do, and inspection of the compiled CSS confirming both
`[data-theme]` blocks and all five status variables ship at the spec hexes. That
pass caught a bug the unit tests structurally could not: the badge `fill` strings
named the CSS variable without `var()`, producing plausible-looking invalid CSS
that renders nothing. Fixed, and now asserted.

**Two open items, recorded as UNKNOWN rather than guessed:** whether Vazirmatn's
binary carries the `tnum` feature (Google's CSS enables nothing; the direct
`.ttf` download returned an error page — settled by M-D2's owner-gated font
package), and the two screenshot deliverables, which were not taken because the
repo has no screenshot capability and no tooling may be installed. The badge
sheet renders at `/badge_sheet` in the M-D1 app window for the owner to capture.

## Next steps (in order)

7. CC-3 / CC-4 / CC-1 if blocking; CC-5 prepare migration only, never apply.
   CC-3 assessed NOT blocking — a latent `Tuple` NameError in
   `architecture/ai/debate_council.py`, unreachable from the live path.
8. Dashboard missions M-D1..M-D4 (`OWNER_DECISIONS_Q1-Q10.md` wins over the
   missions file). No M-D5+ tonight.
   - M-D1 app window — **DONE**, `e9d2ddf`.
   - M-D3 tokens + truth badge — **DONE** (this step).
   - M-D2 fonts — **OWNER_GATE**: `npm i vazirmatn@33.0.3` /
     `@fontsource/vazirmatn@5.3.0` + `@fontsource/lalezar@5.3.0`, or vendor the
     woff2 with the OFL text. Skip until the owner opens the gate; the `tnum`
     question is recorded UNKNOWN for it to settle.
   - M-D4 RTL 2D shell refactor — next, no new dependencies needed.

Then M13.1–M13.6 per README v1.20: one adapter at a time on the same gold
pipeline (oil, crypto majors, US, EU, Asia, tokens), each gated by unit tests +
a 7-day paper soak + honest M42 judge numbers.


Morning report by 10:00 Tehran: `reports/grok/NIGHT_RUN_REPORT.md`.

---

## Step 9 — the owner's pivot to the new Dashi main screen

The owner rejected the current dashboard look ("it is the 4-month-old UI") and
directed: stop polishing `CommandCenter`, build the new Dashi design from scratch
as the main screen, pulling M-D5..M-D8 forward. `TEAM_QUEUE_2026-10-11.md` is the
authoritative order; `README_FOR_CLAUDE.md` v1.22+ and the 2026-10-11 02:17 note
remove the M-D5.0 package gate ("install the listed free packages … without
asking").

Done this step:

- **M-D4 committed as-is** — `e73ff7b`, the snapshot vocabulary extracted.
- **M-D1 regression fixed** — `37977a2`. The full suite after M-D3 came back
  `2 failed, 3350 passed, 4 skipped`; one was the known pre-existing
  `test_execution_state` isolation defect, the other was
  `launcher/appwindow.py:291` (the POSIX branch had no console-suppressing flag).
  Baseline for future full runs is now **1 known failure**.
- **M-D5.1 prototype review** — committed `73a03e4`. One real R3F prototype out
  of five; its `<Environment preset>` is the raw.githack.com fetch the reference
  board forbids. Patterns carried forward rewritten, three defects rejected.
- **M-D5.0 package manifest** — `docs/dashboard/PACKAGES.md`, pinned and
  licence-checked, including the one non-MIT row (postprocessing is **Zlib**).
- **M-D5.3 quality probe** — written, **39/39** in
  `npm run test:stage-quality`. `resolveTier` is pure, so the T0..T3 ladder is
  proven without a GPU. See DECISIONS_LOG for the four judgement calls.
- **M-D5.2 stage + shell** — written. Empty gold-lit observatory floor with a
  procedural shamseh engraving, a procedural PMREM environment (the replacement
  for the banned HDR fetch), a 56px RTL top bar with the PAPER ONLY pill bound to
  real `executionMode`, the measured tier chip, and the M-D5.4 context-loss
  fallback. `/command_center` keeps the old real-data surface alive.

### BLOCKED — the install

`npm install` for the pre-approved set was **denied by the Claude Code auto-mode
safety classifier**, after repeated classifier timeouts. Recorded as
`BLOCKED_TOOL_PERMISSION` per OWNER_DECISIONS Q3 — not routed around, not
retried through another tool. Exact command, pins and licences are in
`docs/dashboard/PACKAGES.md`.

**State:** `npx tsc --noEmit` reports 46 errors, all missing-module resolution
(`three`, `@react-three/fiber`, `zustand`, `detect-gpu`) plus the R3F JSX
intrinsics those types provide. **The stage has never rendered and no M-D5.2
screenshot exists.** I committed only what compiles (docs + the
`/command_center` route) and held the stage, shell, store, probe and the
modified `app/page.tsx`, `package.json`, `globals.css` in the working tree — so
the committed main route still renders the old Command Center and no half-built
main screen ships.

Working signals while blocked: `npm run test:stage-quality` 39/39,
`npm run test:truth-badge` 44/44.

**Next, the moment the install clears:** one commit lands M-D5.2/M-D5.3 and
flips `app/page.tsx` to the Dashi shell; then `next dev` on a loopback port to
SSR-verify the shell and take the `reports/dashboard/screens/M-D5.2/` screenshot
the owner's step process asks for; then M-D5.5's TierPanel reading
`config/idea_shelf.json`, and M-D6's globe.
