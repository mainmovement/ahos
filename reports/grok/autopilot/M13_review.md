# M13 — Paper trading, gold first (PAPER_ONLY), T0→T1 machinery per vision §11.0

Mission statement (queue row 19): *Paper trading, gold first (PAPER_ONLY),
T0->T1 machinery per vision 11.0*.

This review was written **before** any code, per the owner's CH-05 rule. The
three sign-offs (قاسم QA / رضا red team / عرفان evidence) are appended at the
end, after the work.

---

## 0. What a previous attempt left on disk

`git log` and `git status` were read before anything was written. M13 is not a
fresh mission — two prior attempts built most of it, and the honest first move
is to finish their uncommitted work rather than redo it.

Committed already:

| Gate | Where | Commit |
|---|---|---|
| two-source XAU price witness | `architecture/providers/gold.py` | `95d4618` |
| exit rules (frozen Lane A, import-only) | `paper_trading/exit_rules.py` `check_exits`, `EXIT_V1` | reused |
| risk: §5 sizing + §12 breaker | `architecture/markets/risk.py` | `5988620` |
| M42 independent judge | `architecture/markets/judge.py` | `5988620` |
| M39 breaker, paper half — entry gate | wired in `gold_paper.py:run_cycle` | `5988620` |
| T0→T1 gate evaluator | `architecture/markets/tier_gate.py` | `5988620` |
| 7-day soak cadence + README | `scripts/m13_gold_soak.py` | `a258fa0`, `1a64b4a` |

The five-gate acceptance set named by `DEDUP_MERGE_MAP` v1.20 line 183 —
two-source price witness, exit rules, risk, M42 judge, M39 breaker — is
therefore **already complete and committed**. Step 6 of
`NIGHT_RUN_CHECKPOINT.md` records it, with the judge's own bug-catch
(`J-CYCLE` ×2, from `_track_from_ledger` reading raw rows) and the verbatim
archive of the pre-correction ledger.

Uncommitted, and the actual object of this session:

1. `tests/test_tier_gate.py` — **untracked**. 20 tests, passing, pinning the
   T0→T1 evaluator's fail-closed posture and the one structural
   unmeasurability. The previous attempt wrote the test and never committed it.
2. The soak's live outputs (`soak_status.json`, `soak_runlog.jsonl`, the daily
   judge + digest), produced by a running process, PID 12616, started
   2026-10-11T22:09Z, healthy at session start.
3. The queue row itself: `M13 | PENDING → RUNNING`.

---

## 1. آرش — architecture review

**The one real gap: the T0→T1 machinery has no caller.**

`tier_gate.py` is the vision-§11.0 machinery — it measures a track against the
ten T1 exit criteria and reports which are met, unmet, and *unmeasurable as
specified*. It is committed and tested. Nothing runs it. The soak's daily step
(`scripts/m13_gold_soak.py:_daily_report`) runs the M42 judge and writes the
digest, then stops. A promotion-gate evaluator that never evaluates is VISION,
not IMPLEMENTED — and the queue row names the T0→T1 machinery explicitly, so
this is the row's own unfinished half.

The fix is a wiring job, not a build: evaluate the gate once per UTC day over
the same ledger the judge already reads, and write
`reports/grok/M13_SOAK/<day>_tier_gate.md`. Three constraints shape it:

- **The evaluator stays pure.** `tier_gate.py` takes plain dicts and numbers and
  imports nothing from the track. That separation is the same
  independent-reviewer principle the judge already follows
  (`judge.py` never imports `gold_paper`): the gate must measure the record, not
  ask the track how it did. So the bridge — ledger rows → the evaluator's
  arguments — lives in the track module, which already owns the record's shape.
- **No second replay.** `_track_from_ledger` already walks the mission history
  to rebuild the closed-trade blotter. The bridge reuses the same selection rule
  (settled closes only — a close with no corroborated price has no PnL, and
  counting it would let the track buy the trade-count threshold with trades that
  never happened) and says so in its docstring, so the two cannot drift.
- **The cadence runner stays an alarm clock.** It already owns `_latest_state`,
  a read-only ledger read for the status file; a tier-gate report is the same
  class of work — reporting over recorded bytes, no trading logic, no network.

**One defect found in the evaluator itself, while reviewing it as a caller.**
`max_drawdown_pct` is computed as `max(t.get("drawdown_pct") or 0.0 for t in
trades)`. A caller that supplies trades *without* a drawdown field — the
realistic case for any track that has not attached them — gets a 0.00% reading,
which **passes** the ≤15% criterion on missing evidence. That is exactly the
vacuous-pass hazard the module's own docstring warns about for the empty-track
case, and it is the opposite of the fail-closed posture the rest of the module
takes ("missing numbers make a criterion UNMET, never passed"). The fix belongs
in the evaluator, not in every future caller: no recorded drawdown ⇒ the
criterion is UNMEASURABLE, which blocks readiness harder than a FAIL. This is a
strengthening, not a weakening, and it is the reason this session touches
`tier_gate.py` at all.

**What is deliberately NOT done.** M13.1–M13.6 (oil, crypto majors, equities,
EU, Asia, long-tail tokens) are gated by `DEDUP_MERGE_MAP` v1.20 on M13 gold
passing its acceptance first, and the owner's 00:01 note puts the soak in the
background — no new adapter is started here. The learning-loop rows (NS-01,
OWN-AV-37) point at `paper_trading/lessons.py`, which is frozen Lane A and
token-shaped (it reads `paper_trade_v2` rows); the gold track records into the
mission ledger by INV-31, so a gold lesson builder would be a second
implementation of a concept that already has a home, and it is not begun.

---

## 2. پروانه — spec / prompt clarity review

The spec has three sources that must be reconciled, newest-first:

1. **Vision §11.0** (v1.6, `AHOS_AUTONOMOUS_VISION.md:1086`): the T0–T4 ladder.
   T0 today, every market. The T1 exit gate is ten criteria (≥6 months real
   data, ≥200 trades, ≥3-of-4 regimes with ≥30 each, net of fees/funding with
   2× slippage, MaxDD ≤15% and ≤1.5× backtest, Sharpe ≥1, DSR/PSR ≥0.95,
   PF ≥1.3, no month >40% of total profit, WF + OOS). **Promotion is an owner
   act plus three gate agents** (قاسم AG-16, رضا AG-19, سپهر AG-03); §11.0 also
   says **only automatic downgrade, never automatic promotion** (INV-35).
2. **`DEDUP_MERGE_MAP` v1.20**: M13.x adapters come *only after* M13 gold passes
   the five-gate acceptance. That is the scope cap.
3. **The queue row**: "T0->T1 machinery per vision 11.0" — the machinery, not
   the promotion.

The prompt's acceptance criterion is therefore **not** "reach T1" — no code can
reach T1, by law, and the ladder needs ≥6 months of real data which no session
can produce. Read as written, the deliverable is: **the machinery exists, is
wired into the evidence cadence, runs daily, and reports honestly that it is not
ready.** A daily report that says `0/200 trades, 0.07/6 months, NOT READY` is
the successful outcome here; a report that said "ready" would be proof the gate
is broken.

One ambiguity I am resolving explicitly rather than silently: the ladder's
"≥3 of 4 regimes" has a four-regime denominator, but
`architecture/intel/regimes.py` defines **three** regimes, and
`MarketRegimeClassifier(n_regimes=4)` silently relabels the fourth to
`NEUTRAL_CHOP` via a `.get` fallback. The previous attempt recorded this as
`M-REGIME-4` and left it as an owner question rather than inventing a fourth
label. That is the correct call — inventing one here would be gate-loosening by
another name — and this session keeps it visible in every report instead of
resolving it.

---

## 3. گیتی — governance review

Checked against the hard rules before writing any code:

- **PAPER_ONLY / Lane A frozen.** The change touches `tier_gate.py` (Lane B),
  `gold_paper.py` (Lane B), `scripts/m13_gold_soak.py` (a runner with no trading
  logic) and tests. No Lane A file is edited; `paper_trading/exit_rules.py` is
  imported, as `gold_paper.py` already does. No risk cap, gate, hygiene rule,
  policy, registry, or authority surface changes.
- **No promotion.** `evaluate_tier_gate` returns `promoted=False` by
  construction and `TierGateReport.ready_for_owner_review` is a *reporting*
  property. AG-28 (Zarrin, the gold track's agent of record) has
  `allowed_authority: []` with DECIDE and PROMOTE forbidden. INV-35 (downgrade
  only, never upgrade) is untouched: this module upgrades nothing.
- **Fail-closed direction.** The evaluator's missing-number semantics go
   UNMEASURABLE, and UNMEASURABLE *blocks* readiness rather than being waived
   (`ready_for_owner_review` requires `not self.unmeasurable`). The drawdown fix
   in §1 preserves and extends exactly this direction.
- **No weakening of tests.** No skip/xfail, no removed assert, no loosened
   tolerance. The one behavioural change makes a previously-vacuous PASS an
   UNMEASURABLE, which is stricter. Existing `test_tier_gate.py` cases all
   supply `drawdown_pct`, so none of them are affected; new cases pin the new
   behaviour.
- **No new store, no duplicate module.** The bridge is one function in an
   existing module; the report is one function in an existing script; the output
   is a markdown file in the existing soak directory. INV-31 (one ledger) holds:
   the gate reads the same canonical ledger the judge reads.
- **Process hygiene.** The running soak (PID 12616) was started by a previous
   attempt of this mission. Upgrading the runner requires a restart, which the
   soak's own README documents as safe — the runner rebuilds the track from the
   ledger each cycle, so a restart costs at most elapsed time. The restart is
   scheduled with `--days` set to the *remaining* time on the original deadline
   so the soak's planned end does not silently move. Its stdout/stderr logs are
   rotated, not overwritten, so the earlier process output survives.
- **Local commits only, files staged by name.** No push, no remote change, no
   `.env`, no secrets. Soak outputs are committed as evidence, not rewritten.

---

## 4. The change set, before it is written

1. `architecture/markets/tier_gate.py` — a missing drawdown becomes UNMEASURABLE
   instead of a vacuous 0.00% PASS; one new test pins it.
2. `architecture/markets/gold_paper.py` — `paper_history(ledger)`: one pass over
   the mission history producing the gate's arguments (settled trades, each
   carrying the drawdown at its exit; the data span in months), reusing the
   settled-close selection rule the risk replay already uses.
3. `scripts/m13_gold_soak.py` — `_tier_report(...)`, called on the UTC-day
   rollover beside the judge and from `--report-only`; its record joins the
   runlog (`kind: "tier_gate"`) and the status file.
4. `tests/test_tier_gate.py` (untracked → committed) + new cases in
   `tests/test_m13_gold_soak.py` for the wiring.
5. `reports/grok/M13_SOAK/README.md` — the tier report joins the reading order.
6. The soak is restarted onto the new runner, deadline preserved.
7. Queue row + continuation guide + this review's sign-offs.
