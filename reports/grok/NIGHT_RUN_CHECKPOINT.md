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

Step 2 is DONE. Commit follows this checkpoint.

### Judgement calls (also in `reports/grok/DECISIONS_LOG.md`)
- Prevent-by-redirect over restore-after: restore-in-`finally` still leaves the
  write behind on a crash/interrupt; redirecting the path means the write is
  physically impossible.
- The regression tests trigger the write deliberately rather than trusting the
  fixture — a test that never exercises the leak cannot prove it is closed.
- Module attribute, not a function parameter, so every existing caller of
  `main()` is unchanged and the patch point is one line.

## Next steps (in order)

3. Autopilot fix: `claude_autopilot.ps1` sets the model name
   `Atria-Dawn-Preview`, which M12 failed on (`unrecognized_model`) alongside
   `429 Token quota exhausted`. Use a valid model or the CLI default, then
   restart the runner (PID 4516) and watchdog (PID 14408) hidden, the same way
   they were started. Keep yielding while an interactive Claude session is
   active. Do NOT kill `claude.exe` (PID 9580).
4. M12 from `reports/grok/CLAUDE_AUTOPILOT_QUEUE.md`.
5. M34 coherence audit + merge plan (list owner-gated contradictions).
6. M13 gold-first paper cycle (Lane B only; write the exact blocker if Lane A
   is needed).
7. CC-3 / CC-4 / CC-1 if blocking; CC-5 prepare migration only, never apply.
8. Dashboard missions M-D1..M-D4 (`OWNER_DECISIONS_Q1-Q10.md` wins over the
   missions file). No M-D5+ tonight.

Morning report by 10:00 Tehran: `reports/grok/NIGHT_RUN_REPORT.md`.
