# M42 — Hash-chained single ledger + nightly reconcile
## Agent reviews and sign-offs

Mission statement (OWNER_DIRECTIVE_MISSION_PLAN.md:407):
> **M42 Hash-chained ledger + nightly reconcile:** extend
> `architecture/mission/ledger.py` + `paper_trading/ledger.py` into ONE
> append-only, hash-chained ledger. Nightly reconcile against the broker; a
> mismatch → HALT. Each broker ≤40%; USDT depeg monitoring.
>
> Acceptance: tampering breaks the chain; paper reconcile has 0 differences;
> the per-broker concentration test passes.

Status at hand-off: a previous session had written the machinery
(`architecture/mission/ledger.py` evidence surface, `architecture/treasury/`,
`architecture/markets/paper_anchor.py`, `config/broker_registry.yaml`,
`scripts/m42_nightly_reconcile.py`) but had **committed nothing and tested
nothing** — every dry run it made used `--dry-run`, so the recording path had
never once executed. This session finished it, tested it, and fixed the bugs
the tests found.

**This session (2026-10-13) finished delivery.** The hand-off state was:
machinery written, 68 tests green, reviews written — and still nothing
committed, so none of it existed in history. What this session did:

1. **Verified the live state it inherited.** The live chain was `CHAIN_INTACT`
   at 100 entries (`97 STATE, 2 RECONCILE, 1 ANCHOR`), not halted; a dry run
   reproduced the recorded verdict without writing.
2. **Hardened the counterparty leg.** It was the one leg unwrapped by a
   `try/except`, so a statement that could not be read — a row that does not
   parse, an adapter whose `statement()` raises — killed the reconcile with a
   traceback. Vision §11.0 lists a broker API anomaly among the halt triggers,
   so it now reports `R-COUNTERPARTY` and records a `m42:counterparty` HALT
   instead of dying. Two tests pin it (70 targeted tests, up from 68).
3. **Ran the nightly reconcile live for a second night** while the M13 soak
   was appending to the same chain — see عرفان below.
4. **Ran the full suite** as four shards and pasted the counts into قاسم's
   sign-off, rather than summarising them.
5. **Committed the work** — every prior M42 artifact was uncommitted, which
   meant the reviews referenced files that existed only in the working tree.

---

## آرش — architecture review

**The one-ledger question.** The spec says "extend `architecture/mission/ledger.py`
+ `paper_trading/ledger.py` into ONE ledger". Lane A is FROZEN
(`AGENTS.md`), so `paper_trading.sqlite` cannot gain a `prev_hash` column — a
chain column on the frozen store is not a legal implementation of this spec.
The design that satisfies both constraints is the **anchor**: the store is
fingerprinted read-only (`open_store_ro`, `mode=ro` uri, same idiom the lab
itself uses for the discovery store) and the fingerprint is recorded on the
mission ledger as `KIND_ANCHOR`. There is one chain; the store is a branch of
it. `tests/test_m42_single_ledger.py::TestAuthorityLaws::test_there_is_one_chain_not_two`
asserts the other half of that law — `paper_trading/ledger.py` must not grow a
second chain of its own.

**The evidence surface is evidence, not authority.** `record()` writes
`authority: "NONE"` on every row. A HALT grants nobody anything; the callers
that gate new risk on `halted()` give the record its effect. This is the
correct separation for a PAPER_ONLY system, and it is the same separation
`AGENTS.md` draws for the whole Lane B.

**Prefix-stable anchoring is the right asymmetry.** The anchor binds the first
*n* rows per table in rowid order. Append-only growth leaves the prefix
untouched and stays `ANCHORED_CLEAN`; an edit, delete, reorder or dropped table
breaks it. I corrected the `AnchorVerdict` docstring, which described new
tables as "growth" — row growth is silent by design, `extensions` reports new
tables.

**Verdict ordering is sound:** `BROKEN_CHAIN` > `HALTED` > `DISCREPANCY` >
`UNKNOWN` > `CLEAN`. A rewritten ledger is not evidence at all, so it outranks
a discrepancy. An existing unreleased HALT governs the run and the reconcile
reports it without clearing it — `clear_halt()` is an owner act.

**Two structural defects I found and fixed this session:**

1. **The recording path had never run.** `run_reconcile` reassigned `anchor` to
   the bare `StoreFingerprint` returned by `anchor_paper_store`, which both
   `_anchor_payload` and `_short_anchor` then treated as an `AnchorVerdict`,
   raising `AttributeError`. The `record()` call swallowed that into an
   `R-RECORD` finding, so **the verdict was silently never recorded** — the
   anchor bound and the reconcile verdict was lost. Fixed by re-witnessing after
   binding, and pinned by
   `TestReconcileDriver::test_the_binding_path_binds_and_stays_renderable`,
   which asserts the verdict is recorded and that no `R-RECORD` finding appears.
2. **`halted()` could never see a release.** It processed rows in chain order
   and tested each HALT against a `released` set that the matching clear had not
   been reached yet. Two passes now: collect every clear first, then test. This
   was a live control failure — a HALT the owner had released would have read as
   standing forever.

**Open gap, honestly stated:** the counterparty leg is `UNMEASURED`, not `CLEAN`.
The broker registry is empty by owner gate (§11.0.3). This is the correct
honest output and it is why the live verdict is `UNKNOWN`, not `CLEAN`.

## پروانه — prompt / spec clarity review

The spec is short and testable: three acceptance criteria, all three now named
tests in `TestM42Acceptance`. Two ambiguities in the spec needed resolving
before code could satisfy it:

- **"extend … into ONE ledger"** vs **"Lane A frozen"**. These conflict at the
  letter and agree at the intent: the intent is one chain binding every check
  that can stop the system, and the anchor is how that is achieved without
  editing frozen code. I recorded this reading in the module docstrings so the
  next reader does not re-litigate it.
- **"≤ 40%"** — inclusive or exclusive? `concentration_check` uses a strict
  `>`, so a broker at exactly 40.00% is inside the limit.
  `test_exactly_40_is_allowed` pins the choice; if the owner meant strictly
  below, that one comparison is the whole change.

The vision's halt list (§7.0) names exactly three stop conditions — ledger
mismatch, broker concentration, USDT depeg — and the code halts on exactly
those. It does **not** halt on an unmeasured leg. That is the honest reading:
an unmeasured limit is neither satisfied nor an emergency. The verdict says
`UNKNOWN` so it can never be mistaken for a green light, and
`ConcentrationVerdict.allowed` / `DepegVerdict.allowed` are `False` for
`UNMEASURED`, so a caller gating new risk stops rather than passes.

One spec-adjacent correction I made: an unreachable price feed used to raise
`R-DEPEG`. That made a network blip indistinguishable from a broken peg. The
gap now carries `R-DEPEG-UNMEASURED`, so a watchdog keying on `R-DEPEG` pages
only on a peg that actually broke. Same for `R-CONCENTRATION-UNMEASURED`.

## گیتی — governance review

- **PAPER_ONLY:** intact. No funds, keys, broker APIs or withdrawal surfaces
  are touched. The treasury never holds a key. `test_every_reconcile_row_declares_paper_only`
  asserts the recorded payload carries `paper_only: true` and `authority: "NONE"`.
- **Lane A:** untouched. Nothing under `discovery/` or `paper_trading/` was
  modified. The store is opened read-only; `TestPaperStoreAnchor::test_the_store_is_opened_read_only`
  asserts an INSERT and an UPDATE both raise through the anchor's own handle.
- **Authority boundaries:** intact. `test_no_authority_code_is_imported` asserts
  the M42 surface imports none of `architecture.decision` / `risk` / `positions`
  / `scoring`, and none of `discovery` / `engine` / `telegram_ai`. The
  OpportunityScorer is not consulted; the treasury decides nothing.
- **No new authority created:** `architecture/treasury/` is an observer. Its
  only outputs are evidence rows on a chain whose every row says
  `authority: NONE`, and a report. It promotes nothing.
- **Gates not weakened:** `hygiene.py`, `gate.py`, `policy.py`,
  `freeze_lane_a.py`, the authority registry and the risk caps were not opened.
- **Honest labels:** the live verdict is `UNKNOWN` and the report says why in
  its findings section. No `CLEAN` claim rests on an unmeasured leg, and after
  the renderer fix the findings section never claims "no discrepancy" under a
  non-CLEAN verdict.
- **Secrets:** none added. `record()` routes evidence payloads through the same
  `redact_secrets` law as checkpoints; `test_secrets_never_reach_the_chain`
  asserts a key-looking string is rejected and nothing is written.

---

## رضا — red team (attempts to break it)

Attacks tried, and what each produced:

1. **Edit a recorded checkpoint's equity** to a flattering number →
   `LedgerTamperError` from `verify()` (entry_hash mismatch), verdict
   `BROKEN_CHAIN`.
2. **Edit a checkpoint but recompute its own hash** so only the *claim* moves,
   not the chain → chain stays `CHAIN_INTACT`, the paper judge fires
   `DISCREPANCY` (double-entry / money identity), reconcile records a halt
   source. This is the attack the judge exists for, and it is the one a
   chain-only check would miss.
3. **Release a halt, then sound a second one, then clear the first's hash** →
   the later halt still stands (a clear cannot be replayed against a different
   halt).
4. **Clear a halt twice** → still released; a clear is not itself cleared.
5. **Tamper the chain and read `halted()`** → fail-closed: reads as halted with
   "chain unverifiable" as the reason.
6. **Edit, delete, reorder, and drop a table** in the anchored store →
   `ANCHORED_MISMATCH` in all four cases.
7. **Write through the anchor's own connection** → `sqlite3.OperationalError`
   on both INSERT and UPDATE.
8. **Forge an anchor's `root_hash`** on the chain → `ANCHORED_MISMATCH`.
9. **Claim a fill's PnL that does not re-derive** from its own exec prices and
   costs → `R-ARITHMETIC` finding, verdict `DISCREPANCY`.
10. **One broker at 100%, 60/40, 50/50, 40.01/59.99** → `BREACH` each time;
    exactly 40/40/20 passes.
11. **Feed one quote, or two quotes 5% apart, or a zero price** → `UNMEASURED`,
    no halt recorded. The two-source law cannot be satisfied by one feed.
12. **Try to make the reconcile lift its own halt** → it cannot; the second run
    leaves the halt standing.
13. **Try to record a secret** → `SecretRejectedError`, nothing written.
14. **Try to bind the live store from a throwaway test ledger** → cannot; the
    driver's paper leg is repointed at a tmp store in the fixture, and
    `data/` is never opened for write.

**Not attacked, and why:** the hash chain is keyless, so an attacker who
rewrites the *entire* file can recompute every hash — `verify()`'s docstring
says so and requires `head_hash` to be recorded outside the file. The chain
head is now in the committed reconcile report (`reports/grok/M42/`), and
`MissionLedger.verify(anchor_hash=...)` checks it. That is the designed
residual risk, and it is documented rather than hidden.

## عرفان — evidence (every claim points at a file, test or commit)

| Claim | Evidence |
|---|---|
| Ledger is one chain over state + evidence | `architecture/mission/ledger.py:512-604` (`record`, `evidence`, `halt`, `clear_halt`, `halted`, `head_hash`); `tests/test_m42_single_ledger.py::TestLedgerEvidenceSurface` |
| Tampering breaks the chain | `TestM42Acceptance::test_acceptance_tampering_breaks_the_chain`; `TestHaltProtocol::test_tamper_reads_as_halted_fail_closed` |
| Paper reconcile has 0 differences | `TestM42Acceptance::test_acceptance_paper_reconcile_has_zero_differences`; live receipt `reports/grok/M42/2026-10-12_reconcile.md` ("paper judge: CLEAN over 77 cycles, 0 finding(s)") |
| Per-broker ≤ 40% passes | `TestM42Acceptance::test_acceptance_per_broker_concentration`; `TestBrokerConcentration` |
| Store bound to the chain, read-only | `architecture/markets/paper_anchor.py`; `TestPaperStoreAnchor` |
| Depeg two-source law | `architecture/treasury/surveillance.py:197-249`; `TestUsdtDepeg` |
| A mismatch is a HALT on the chain | `TestReconcileDriver::test_concentration_breach_halts`, `test_depeg_breach_halts` |
| The recording path works end to end | live run: 81 ledger entries (`78 STATE, 2 RECONCILE, 1 ANCHOR`), chain head `3e20a93e34e7185f`, verdict recorded |
| No authority imported | `TestAuthorityLaws::test_no_authority_code_is_imported` |
| No second chain in the paper lab | `TestAuthorityLaws::test_there_is_one_chain_not_two` |

---

## Sign-offs

### قاسم — QA (targeted **and** full suite, counts pasted)

Targeted, `.venv/Scripts/python.exe -m pytest tests/test_m42_single_ledger.py`:

```
70 passed in 14.14s
```

The two tests added above the baseline of 68 pin the new counterparty-leg law.

Regression surface for the modules M42 touched — the ledger, the two judges, and
the gold paper track the halt gate now reads:

```
tests/test_mission_ledger.py + tests/test_gold_judge.py  ->  104 passed
tests/test_gold_paper_cycle.py + tests/test_m13_gold_soak.py  ->  42 passed
```

Full suite, run as four shards over `tests/` (this host's suite is too slow for
one pass; one shard per background slot, `--timeout=1500` per test):

```
shard aa:  738 passed, 1 skipped   (exit 0)
shard ab: 1252 passed, 3 skipped, 1 FAILED  (exit 1)
shard ac:  846 passed               (exit 0)
shard ad:  599 passed               (exit 0)
------------------------------------------------------------------
total:   3435 passed, 4 skipped, 1 failed
```

The one failure is `tests/test_execution_state.py::test_missing_store_reads_no_data_never_ok`
(`assert status["exists"] is False` → `True`). It is a **known pre-existing
test-isolation defect on this host**, not a regression from M42: the test
monkeypatches `es.ROOT` while its own comment admits the path getter resolves
against the real config, so it asserts an absent cognitive memory store on a
host where that store genuinely exists. It was proven pre-existing on
2026-10-09 by stashing the change under review and removing the new files —
the test failed identically on the pristine checkout. I did not relax it.

Verdict: **the targeted suite and every M42-adjacent suite pass; the full
suite is on its documented 1-failed baseline.** Sign-off granted on the
targeted evidence, with the full-suite baseline recorded honestly rather than
repeated as a pass.

### رضا — red team

The attack list above stands. This session added one more, against the leg I
changed:

15. **Hand the reconcile a statement row it cannot parse** (`qty: "not-a-number"`)
    and an adapter whose `statement()` raises `ConnectionError` → both now
    produce `DISCREPANCY` with an `R-COUNTERPARTY` finding and a recorded
    `m42:counterparty` HALT, instead of a traceback. Before the fix, a malformed
    statement from a broker killed the process, which a watchdog would have read
    as a crash rather than the stop vision §11.0 requires.

No attack reversed a verdict, cleared a halt, or passed an unmeasured limit off
as satisfied.

### عرفان — evidence

Every claim in the table above points at a file, a test, or a commit. Added
this session:

| Claim | Evidence |
|---|---|
| The recording path works on a second night | live run `reports/grok/M42/2026-10-13_reconcile.md` — paper judge `CLEAN` over **102 cycles, 0 findings**; depeg `ARMED` at 0.0799%; verdict `UNKNOWN` (counterparty leg unmeasured) |
| The chain survives concurrent writers | `data/mission_ledger/mission_ledger.jsonl` verified `CHAIN_INTACT` at 107 entries (`103 STATE, 3 RECONCILE, 1 ANCHOR`) while the M13 soak was appending its own `STATE` rows between my writes — the shared-append design held across two live nights |
| A broker API anomaly halts | `TestReconcileDriver::test_an_unreadable_statement_halts_rather_than_crashing`, `test_a_statement_object_that_raises_halts_too` |
| No authority imported | `TestAuthorityLaws::test_no_authority_code_is_imported` (the file list includes `scripts/m42_nightly_reconcile.py`) |

**All three sign-offs granted.** The one honest gap is the counterparty leg,
which is `UNMEASURED` by owner gate, and which is exactly why the live verdict
is `UNKNOWN` rather than `CLEAN`.
