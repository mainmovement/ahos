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

## Next steps (in order)

5. M34 coherence audit + merge plan (list owner-gated contradictions).
6. M13 gold-first paper cycle (Lane B only; write the exact blocker if Lane A
   is needed).
7. CC-3 / CC-4 / CC-1 if blocking; CC-5 prepare migration only, never apply.
8. Dashboard missions M-D1..M-D4 (`OWNER_DECISIONS_Q1-Q10.md` wins over the
   missions file). No M-D5+ tonight.


Morning report by 10:00 Tehran: `reports/grok/NIGHT_RUN_REPORT.md`.
