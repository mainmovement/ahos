# Identity Resolver — Live Receipt (2026-10-09)

Executed from the instruction at
`حافظه_ادامه/2026-10-09_03-00_دستور_اجرای_زنده_resolver.md`. Records the
restart, the test result, and what the live daemon actually decided.

**Timestamp (Asia/Tehran):** 2026-10-09 ~04:35 +03:30 (log timestamps are UTC).
**Outcome: VERIFIED** — one real identity resolved `VERIFIED` from two distinct
providers on a real address, live, on the restarted daemon. Details and the
honest limits below.

## 1. The restart

| | old daemon | new daemon |
|---|---|---|
| pid | 12036 | **12820** |
| started | 2026-10-08 14:46:38 (before commit `373516e`) | 2026-10-09 **04:31:56 +03:30** (after) |
| run_id | `run_1791458210_7f79ba16` | `run_1791507717_6810cfbd` |

The old daemon provably ran pre-commit code. It was restarted through
`scripts/restart_engine_only.py`, which drives the launcher's own
single-component path — `processkit.terminate()` on the recorded pid (gentle
first, force last; the old pid needed force, 0.8s), then the same
`_start_process("engine")` the launcher's start loop calls, with the same
command, env, log path, and pid record:

```
G:\robat\ahos\.venv\Scripts/python.exe -m architecture.runtime \
  --daemon --interval-sec 60 --observation-cycle --evidence-source local
```

Only the engine was touched. `launcher restart` was deliberately **not** used —
it stops and starts the gateway and the Telegram bot too, and
`launcher start --skip ...` persists a skip record that changes the launcher's
durable state for later status/stop runs. The gateway, the Telegram bot
(PID 1028), `claude.exe` (PID 9580) and the autopilot runner (PID 4516) were all
left running. No `.env` edit, no `DATABASE_URL` change, no Lane A change.

Two restarts happened. The first (PID 11220, 04:11:14) picked up the resolver
but its `identity_probe` audit lines never reached the log, because
`ahos.identity` had no handler — `get_logger` only installs one on the logger it
is named for, and the daemon named only `ahos.main`. The daemon now calls
`get_logger("ahos.identity", run_id=...)` alongside `ahos.main`; the resolver
itself stays free of any runtime import. The second restart (04:31:56) picked
that up, and the evidence below is from it. Both old pids are stopped; exactly
one engine daemon is running.

## 2. Test result

As instructed, only the targeted file — not the full suite.

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_multi_source_identity.py -q
.....................                      [100%]
21 passed in 0.35s
EXIT=0
```

## 3. The comment/code mismatch (instruction step 2)

Resolved by making the **code** match the comment, with a real fail-closed check:

- `BaseHttpProviderAdapter.requires_credentials` defaults to `True` — a provider
  that forgets to declare itself keyless is never treated as a free unattended
  source.
- `DexScreenerAdapter` and `GeckoTerminalAdapter` declare it `False` (both are
  genuinely keyless public APIs).
- `build_production_resolver()` returns `None` unless **every** provider in
  `DEFAULT_MARKET_PROVIDER_IDS` is present *and* keyless. The daemon then keeps
  the fail-closed single-source default (`identity_from_candidate`) and logs a
  WARNING naming the reason, instead of silently running on one source.
- Two new tests pin this, including that the production resolver refuses to
  build when the default set is not fully keyless.

The two-source rule is not weakened anywhere; if anything it is now enforced at
one more point.

## 4. What the live daemon decided

First opportunity cycle of `run_1791507717_6810cfbd`, 12 candidates, each probed
at both providers. Verbatim `identity_probe` lines from
`logs/launcher/engine.log`:

```
identity_probe chain=base symbol=SOL address=0x311935Cd80B76769bF2ecC9D8Ab7635b2139cf82 \
  asked=dexscreener,geckoterminal answered=dexscreener,geckoterminal \
  state=VERIFIED reason=min_sources_met conflicts=-

identity_probe chain=robinhood symbol=SOL address=0x208092689248d96Aa7F30aab09FF6A7E05b41E18 \
  asked=dexscreener,geckoterminal answered=dexscreener,geckoterminal \
  state=CONFLICT reason=source_disagreement conflicts=provider_address_mismatch:geckoterminal

(10 further candidates, all chain=solana memecoins) \
  asked=dexscreener,geckoterminal answered=- \
  state=UNRESOLVED reason=insufficient_independent_sources conflicts=-
```

### The verified example

| field | value |
|---|---|
| decision id (token_key) | `base:0x311935cd80b76769bf2ecc9d8ab7635b2139cf82` |
| identity_token_id | `a2c040aa0443254d4e17033a6fe4deac` |
| chain / symbol / address | base / SOL / `0x311935Cd80B76769bF2ecC9D8Ab7635b2139cf82` |
| provider 1 | **DexScreener** (`dexscreener`) |
| provider 2 | **GeckoTerminal** (`geckoterminal`) |
| identity_state | **VERIFIED** — `min_sources_met`, policy `identity-resolution-v1` |

This is the instruction's success criterion: one real identity `VERIFIED` from
two distinct providers on a real address, with the decision id and both provider
names.

### The gate advanced exactly once, and stopped honestly

The corresponding decision in `reports/canonical_decision_read_model.json`:

```
identity_state : VERIFIED
outcome        : INSUFFICIENT_EVIDENCE
advisor_action : AVOID
paper_allowed  : False
primary_reason : "Security gate: INCOMPLETE (unknown_critical_security)."
security_state : INCOMPLETE   (security_reason: unknown_critical_security)
```

The identity gate — the structural blocker this work removed — now passes on
live evidence. The token is still not paper-allowed, because the **security**
gate has no enrichment for it and correctly refuses to pass it. That is the
intended behaviour, not a failure: PAPER_ONLY means each gate must be earned
independently, and this token earned the first and not the second.

### All three fail-closed paths, live

| identity_state | count | outcome | paper_allowed | why |
|---|---|---|---|---|
| `VERIFIED` | 1 | INSUFFICIENT_EVIDENCE | False | passed identity, stopped at security |
| `CONFLICT` | 1 | **REJECT** | False | "Identity gate: token state CONFLICT cannot produce ENTER." |
| `UNRESOLVED` | 10 | INSUFFICIENT_EVIDENCE | False | "Identity gate: token state UNRESOLVED cannot produce ENTER." |

Nothing became PASS that should not have. `CONFLICT` and `UNRESOLVED` still hard
-veto ENTER exactly as before. The 10 `UNRESOLVED` rows are solana memecoin
addresses on which **neither** provider answered (`answered=-`), which is the
honest single-source-or-less outcome, not a regression.

## 5. Honest limits of this result

- **The full positive path is still unexercised end to end.** No token reached
  `paper_allowed: True`. The identity blocker is gone; the binding gate is now
  security enrichment. Closing that is a separate mission (the observation
  cycles remain `DEGRADED`, ~39/40 live calls failing for the Lane-A poller),
  and the instruction explicitly forbade loosening anything to force a PASS.
- **Two of the 12 candidates carry `chain=base` / `chain=robinhood`** while the
  daemon runs `--chain solana`. The collector returns candidates carrying their
  own chain, so the resolver asked about the chain the candidate claimed. Both
  providers agreeing on `base:0x3119…` is genuine agreement; the resolver makes
  no judgement about whether that token is interesting — that is downstream.
- **One cycle of 12 candidates is a complete observation, not a statistical
  one.** The mechanism is proven live; the population of tokens that will pass
  is unknown and no claim is made about it.
- **The `identity_probe` evidence is logged, not persisted in the read model.**
  The read model is written by `architecture/decision/authority.py`, which is on
  the forbidden-paths list, so the evidence is audited in the engine log at the
  point it is produced instead.

## 6. Files changed this session

- `architecture/identity/multi_source.py` — keyless gate in
  `build_production_resolver()`; `identity_probe` audit logging.
- `architecture/providers/adapters.py` — `requires_credentials` declared on the
  base (True) and on the two keyless adapters (False).
- `architecture/runtime/__main__.py` — comment now matches the real check, with
  a WARNING on fallback; `ahos.identity` wired into the structured logger.
- `tests/test_multi_source_identity.py` — 19 → 21 tests (the keyless gate).
- `scripts/restart_engine_only.py` — new, engine-only restart via the launcher's
  own primitives.
- `reports/grok/DECISIONS_LOG.md` — the four decisions quoted above.

No file under `discovery/` or `paper_trading/` was modified. The decision
authority and the security overlay were not touched.
