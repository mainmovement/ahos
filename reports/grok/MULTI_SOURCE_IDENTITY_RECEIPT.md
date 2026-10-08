# Multi-Source Identity Resolver — Receipt (2026-10-09)

Mission: P2 — independent second market source, named by the owner directive as
"currently the highest-leverage functional gap". This receipt records what was
built, the commands that verified it, and the honest status.

## The blocker that was found

`identity_from_candidate` (`architecture/decision/authority.py:165-195`) builds
exactly ONE `IdentitySource` from the merged candidate, with

```python
provider=str(candidate.source_provider)   # "dexscreener+geckoterminal"
```

`resolve_identity`'s independence gate is

```python
providers = {s.provider for s in addressed}
if len(providers) < 2:
    return False
```

A joined string is one element, so `len(providers) == 1` always, the token
resolves `UNRESOLVED / insufficient_independent_sources`, and
`identity_allows_positive_decision` is `False` for **every token in the
system**. The positive-value path was not poorly scored — it was structurally
unreachable. No amount of data would have opened it.

A second defect made the gate falsely satisfiable if it *had* opened:
`GeckoTerminalAdapter.fetch_token_metrics` set `address=address` — it echoed the
queried address back as its own answer (DexScreener had the equivalent
`base.get("address", address)` fallback). An adapter that returns what it was
asked cannot corroborate anything; it would "confirm" any address. That is
corroboration that was never given.

## Evidence the store is genuinely multi-provider (and where it is not)

Queried `data/e01_discovery.sqlite` (read-only):

```
discovery_observations rows: 129,026
rows per provider: dexscreener 102,172  geckoterminal 26,854
tokens with >=2 distinct providers (all rows): 24,357
dexscreener EVIDENCE rows (error_state IS NULL): 8,028
dexscreener FAILURE rows (error_state set):       95,071
geckoterminal EVIDENCE rows:                      27,074
geckoterminal FAILURE rows:                            0
dexscreener evidence tokens: 67
geckoterminal evidence tokens: 26,563
INTERSECTION (true two-source evidence): 0
```

So the two providers do NOT corroborate each other in the store today: their
discovery fan-out queries a *different endpoint per provider*
(`fetch_candidate_tokens` → DexScreener `/search`, GeckoTerminal `/new_pools`),
so they land on disjoint token populations. The 24,357 "two-provider" tokens
are an artifact of counting failure records: 95,071 of DexScreener's rows are
the honest `no_valid_price` record written for delisted tokens, not evidence.

**Consequence:** a store-reading resolver would corroborate nothing (intersection
0). The resolver must ask both providers the *same per-address question* — which
is what `fetch_token_metrics` already does and what
`architecture/providers/collect.py::ProviderCollector` fans out across. This is
why the resolver is built on live per-address queries rather than on the store.

## What was built

### `architecture/identity/multi_source.py` (new)

`MultiSourceIdentityResolver` — callable with the `(candidate, now)` signature
the pipeline already expects (`orchestrator.py:197`), so it drops into the
existing `identity_resolver` injection point without touching the authority.

- Asks every provider in `DEFAULT_MARKET_PROVIDER_IDS = ("dexscreener",
  "geckoterminal")` the same `fetch_token_metrics(chain, address)` question.
- Emits one `IdentitySource` per provider that returned status `OK` with a
  token carrying a non-empty address.
- Hands those sources to the **same** `resolve_identity`, with the same
  `POLICY_VERSION`, same pool arguments, same staleness policy.
- **Adds no identity rule, no gate, no score, no decision.** It cannot emit
  WATCH/PAPER_CANDIDATE. It only supplies evidence.

Fail-closed by construction — a provider contributes a source ONLY on a real
answer:

| situation | source emitted | resulting state |
|---|---|---|
| provider error / timeout / rate limit | none | UNRESOLVED (if <2 answer) |
| provider returned zero tokens | none | UNRESOLVED |
| provider returned a token with no address | none | UNRESOLVED |
| provider returned a DIFFERENT address | yes, with its own claim | **CONFLICT** |
| providers disagree on chain | yes, with its own claim | **CONFLICT** |
| fewer than 2 independent providers answered | — | UNRESOLVED |
| two independent providers agree | two | **VERIFIED** |

### Adapter repairs (`architecture/providers/adapters.py`)

- `GeckoTerminalAdapter.fetch_token_metrics`: address is now
  `attrs.get("address") or resource.get("id") or ""` — the provider's own claim,
  never the query. Also reads the chain from the payload, and accepts both the
  `{"data": {...}}` wrapper and a bare attributes object.
- `DexScreenerAdapter.fetch_token_metrics`: address is now
  `base.get("address") or ""` — the `or address` fallback that would echo the
  query is removed.

`ProviderCollector`'s merge is unaffected: it never overwrites the base
candidate's address (`_fill_toplevel` copies symbol/name/pair_address/dex_id/
metrics/security/social, never `address`), and `registry.py:65` reads the
candidate's own address, not the returned token's.

### Wiring (`architecture/runtime/__main__.py`)

```python
identity_resolver = build_production_resolver()

orchestrator = OpportunityPipelineOrchestrator(
    collector=collector,
    telegram_adapter=telegram_adapter,
    target_chat_id=allowed_chats[0] if allowed_chats else None,
    score_ledger=score_ledger,
    identity_resolver=identity_resolver,
)
```

The orchestrator's default resolver stays `identity_from_candidate` — the
fail-closed single-source default is untouched, and every test that constructs
the orchestrator directly keeps its existing behaviour. Only the production
daemon gets the multi-source resolver.

## Verification commands and results

```
$ ./.venv/Scripts/python.exe -B scripts/freeze_lane_a.py
Lane-A integrity OK (36 files pinned)
EXIT=0

$ ./.venv/Scripts/python.exe scripts/validate_imports.py
EXIT=0

$ ./.venv/Scripts/python.exe -m pytest tests/test_multi_source_identity.py -q
...................                      [100%]
19 passed in 0.68s
EXIT=0
```

Lane A untouched: no file under `discovery/**` or `paper_trading/**` was
modified; the resolver imports frozen `discovery.identity` read-only, exactly
as `architecture/identity/resolution.py` already does.

Full suite:

```
$ ./.venv/Scripts/python.exe -m pytest tests/ -q
1 failed, 2957 passed, 4 skipped in 3481.57s (0:58:01)
FAILED tests/test_execution_state.py::test_missing_store_reads_no_data_never_ok
EXIT=1
```

**The one failure is pre-existing and unrelated to this change**, proven rather
than asserted: with this change stashed and both new files moved out of the
tree, the same test fails identically on the pristine checkout.

```
$ git stash push -- architecture/identity/__init__.py \
      architecture/providers/adapters.py architecture/runtime/__main__.py
Saved working directory and index state WIP on ahos: 7ab2fa4 ...    EXIT=0

$ # tests/test_multi_source_identity.py and architecture/identity/multi_source.py
$ # moved out of the tree for this leg

$ ./.venv/Scripts/python.exe -m pytest \
      tests/test_execution_state.py::test_missing_store_reads_no_data_never_ok -q
>       assert status["exists"] is False
E       assert True is False
tests\test_execution_state.py:122: AssertionError
1 failed in 0.30s                                                      EXIT=1
```

Its own comment is the cause — "The path getter is resolved against the real
config" — so it asserts an absent cognitive memory store on a host where that
store genuinely exists. It touches no file in `architecture/`, and my diff
touches nothing outside `architecture/`, `tests/`, and `reports/`. Left exactly
as written; no test was weakened, deleted, or had an assertion relaxed.

## The four required cases (test_multi_source_identity.py)

| case | providers | result | positive gate |
|---|---|---|---|
| two agreeing sources | both OK, same address | `VERIFIED` `min_sources_met` | `True` |
| one source only | one OK, one empty | `UNRESOLVED` `insufficient_independent_sources` | `False` |
| conflicting sources | different addresses | `CONFLICT` `source_disagreement` | `False` |
| missing fields | empty chain/address | not `VERIFIED` | `False` |

Plus the fail-closed pins: a down provider contributes no source; no provider
answering is UNRESOLVED; a token with no address claim contributes no source;
an unsupported chain is UNSUPPORTED before any provider is asked; conflicting
chains are CONFLICT. Plus the two echo guards that keep the gate honest, and a
pin that `build_production_resolver()` constructs the real adapters for the
documented pair so the production path is the tested path.

## Honest status: PARTIAL

**VERIFIED.** The structural blocker is removed and the mechanism is proven
offline: two independent providers answering the same per-address question now
reach `VERIFIED`, and every fail-closed path (conflict, single-source, missing
fields, provider down) stays shut. Lane A integrity passes, imports validate,
the new tests pass.

**Why PARTIAL, not COMPLETE — the two open items:**

1. **Live corroboration has not yet been observed end to end on this host.**
   The tests inject a routing transport; they prove the mechanism, not a live
   two-provider agreement over the real network. The mission directive is
   explicit that "a fixture test is not live runtime proof". Confirming this
   requires the daemon to run a real opportunity cycle with egress to both
   providers — an operator/runtime action, and egress reachability on this
   laptop is a separate open question (M-GAP-007 notes the same gap for CMC).
2. **The store still corroborates nothing.** The disjointness proven above
   (intersection 0) is structural to the discovery fan-out, not a defect in the
   resolver. This does not block the resolver, but it means the observation
   store cannot yet serve as a second source and the resolver must make live
   per-address calls. Consolidating the two providers onto a shared
   per-address capability would close that, and is scoped to the observation
   mission, not this one.

**Not claimed.** No upgrade to any token's real-world status. No claim that any
specific token now warrants a positive decision — the resolver makes identity
*reachable*, and every downstream gate (security overlay, score, confidence,
risk, optional AI downgrade) still applies unchanged. No change to Lane A, to
the decision authority's logic, or to any safety deny-list.
