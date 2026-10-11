# M13 gold 7-day paper soak

Started 2026-10-12 (Tehran), owner decision 00:01: gold first on the paper track,
running on its own as a background scheduled job while the dashboard work
continues in the foreground. Seven days, one paper cycle every 15 minutes, one
M42 judge report per UTC day.

**PAPER_ONLY.** This is not a trading bot. The runner (`scripts/m13_gold_soak.py`)
owns no trading logic at all — it is an alarm clock. Every cycle is
`architecture.markets.gold_paper.run_gold_paper_cycle`, which trades a fictional
$10 000 bankroll against real two-source-corroborated XAU prices and records into
the one canonical mission ledger. There is no live path, no key, no exchange, and
no funds to reach. PAPER_ONLY is structural in the modules the runner calls, not
a flag it sets.

## What to read, in what order

1. **`<UTC-day>_judge.md`** — the day's M42 judge report. The judge replays the
   ledger's recorded bytes and never asks the track what happened, so its numbers
   are derived from evidence rather than from the process's memory. `CLEAN` means
   every closed trade re-derives from the position and the corroborated price the
   ledger records; anything else is a finding worth reading.
2. **`<UTC-day>_digest.json`** — the same day as a machine-readable digest.
   `signed` is `false` by design: this is paper, and nothing here is an attestation.
3. **`soak_status.json`** — the runner's live state: cycle counts, the last cycle,
   the ledger's checkpoint. Written after every cycle.
4. **`soak_runlog.jsonl`** — one JSON line per cycle and per daily report, failure
   included. This is the record to grep when something looks wrong.
5. **`soak_stdout.log` / `soak_stderr.log`** — the process's own output.
   `soak_pid.txt` is its PID.

## What this soak will actually produce

The exit card the track uses is the token card, `PT-X1-v1`: take-profit **+50%**,
stop **−35%**, hard exit at 48 hours. Gold does not move 50% in a week, so the
soak's exits will almost all be `TIME_EXIT` at 48 hours, not profit or stop.
That is the honest expectation — a soak that "found" a profit exit would mean the
card was wrong or the prices were.

Because the witness law requires **two** independent corroborating sources, a
cycle with only one fresh source records `UNRESOLVED` and no position is taken or
closed. Expect that over weekends: `yahoo_gc_futures` tracks `GC=F`, which stops
trading Friday evening New York and reopens Sunday evening, while
`goldapi_spot` stays live. On a Saturday the soak legitimately sees one fresh
source and one two-days-stale one. That is market structure, not a broken feed,
and the track correctly holds any open position as `UNPRICED` rather than pricing
it on one source.

## What a failure looks like, and what it is not

A cycle that raises — a down feed, a network blip, a ledger hiccup — is logged
and the cadence continues. A soak that died on its first transient would soak
nothing, so the one thing the runner guarantees is that it survives a bad cycle.
The line for a failed cycle has `"ok": false` with the error and a short
traceback in `soak_runlog.jsonl`; the status file's `cycles_failed` counts them.

The daily judge is written after a failure as well as after a success, because a
day with no report is worse than a report over a thin day.

If the process is gone, it is safe to restart it — nothing about the soak lives
in memory. The runner rebuilds the track from the ledger each cycle, so a restart
loses at most the elapsed time:

```powershell
$py = 'G:\robat\ahos\.venv\Scripts\python.exe'
$p = Start-Process -FilePath $py -ArgumentList 'scripts\m13_gold_soak.py','--days','7','--interval-sec','900' `
  -WorkingDirectory 'G:\robat\ahos' -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput 'reports\grok\M13_SOAK\soak_stdout.log' `
  -RedirectStandardError  'reports\grok\M13_SOAK\soak_stderr.log'
Set-Content 'reports\grok\M13_SOAK\soak_pid.txt' -Value $p.Id -Encoding ASCII
```

A single advance, or today's report alone, without touching the cadence:

```bash
.venv/Scripts/python.exe scripts/m13_gold_soak.py --once
.venv/Scripts/python.exe scripts/m13_gold_soak.py --report-only
```

## Related

- `scripts/m13_gold_soak.py` — the runner. Its docstring is the contract.
- `tests/test_m13_gold_soak.py` — pins the two properties that make it a soak:
  a failing cycle is recorded rather than raised, and `--report-only`
  reconciles the ledger with no network of its own.
- `architecture/markets/gold_paper.py` — the track and the witness law.
- `architecture/markets/judge.py` — the M42 judge the daily report runs.
- `reports/PRE_SOAK_STATUS.txt` — the host's pre-soak gates (G1–G10 PASS as of
  2026-10-12).
