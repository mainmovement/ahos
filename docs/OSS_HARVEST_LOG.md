# OSS Harvest Log

Record of open-source projects surveyed for reusable capability, what was
taken, and why. Maintained so that every borrowed idea has a traceable origin
and a defensible licensing position.

**Standing rule.** Techniques and public mathematics may be reimplemented
freely. Source code is only copied when its licence permits it *and* the code
survives our constraints ($0/month, works under sanctions and filtering,
no paid API dependency, auditable offline). When those conflict, we
reimplement from first principles and say so here.

---

## Survey 1 — Solana rug / honeypot detection (Wave-26, 2026-08-17)

### Projects reviewed

| Project | Language | Licence | Verdict |
|---|---|---|---|
| `kukapay/rug-check-mcp` | Python | MIT | **Rejected** — thin wrapper around the paid Solsniffer API. |
| `ccan23/rugcheck` | Python | — | **Rejected as a dependency**; RugCheck is already covered by our own `RugCheckSecurityAdapter`. |
| `degenfrends/solana-rugchecker` | TypeScript | MIT | **Rejected** — wrong language; requires Helius + Metaplex SDKs. |
| `nothingdao/solana-bundler-detector` | TypeScript | — | **Techniques harvested** (see below). Code not usable: TS, Helius-dependent. |
| `drixindustries/Rug-Killer-On-Solana` | TypeScript | MIT | **Rejected** — front-end platform, not a library. |
| `faradaysage/Solana-Transaction-Analyzer` | Python | — | **Rejected** — requires a Helius API key. |
| `NBAFrigge/SolanaTokenHolderAnalyzer` | Python | — | **Rejected** — depends on the unofficial gmgn.ai endpoint. |

### Why almost everything was rejected

The ecosystem overwhelmingly solves the holder-data problem by **paying for
it** — Helius, Solsniffer, Birdeye, gmgn.ai. That is a reasonable choice for
most projects and an impossible one here: it breaks the $0 cost floor, and
those endpoints are not dependably reachable from the deployment target. A
dependency we cannot pay for or reach is not a capability, it is a future
outage.

### What was harvested

Three statistical techniques, reimplemented from first principles in
`architecture/intel/forensics.py`:

1. **Gini coefficient over holder balances.** Used by
   `solana-bundler-detector` as a concentration metric. The statistic itself
   is standard welfare economics (Gini, 1912) and belongs to nobody.

2. **Coefficient of variation across wallet behaviour.** Same project's
   "wallet similarity" heuristic. The insight worth keeping: automated buyers
   produce suspiciously *uniform* transaction counts, while humans produce
   ragged ones. Low variance across many wallets is evidence of one actor
   operating many wallets.

3. **Round-number clustering.** A widely used bot signature — scripts buy
   1.0 / 0.5 / 0.1 SOL; humans buy 0.3271.

**No code was copied**, so no licence obligation is inherited. This was the
right call on the merits, not just the legal ones: reimplementation forced us
to understand each statistic well enough to test it against hand-checkable
values (`tests/test_forensics.py` verifies perfect equality ⇒ Gini 0, uniform
behaviour ⇒ CV 0, organic amounts ⇒ ~0% round) and to apply our own UNKNOWN
discipline, which none of the surveyed projects have.

### The discipline the originals lack

Every surveyed project treats missing holder data as a low score. Ours returns
`UNKNOWN` and says why. A concentration score of zero for a token nobody could
measure is not a neutral default — it reads as safety, and it is the exact
failure this system exists to prevent.

---

## Already-reused prior art (pre-existing, recorded for completeness)

| Source | Where it lives | Notes |
|---|---|---|
| DexScreener public API | `DexScreenerAdapter`, `DexScreenerBoostsAdapter` | Free, keyless, 300 req/min. |
| GeckoTerminal public API | `GeckoTerminalAdapter` | Free, keyless. |
| GoPlus Security API | `GoPlusSecurityAdapter` | Free tier, keyless. |
| RugCheck API | `RugCheckSecurityAdapter` | Free tier; Solana LP lock / mint authority. |
| Ollama | `architecture/ai/clients.py` | Local models: free, offline, unfilterable. |
| n8n | `n8n/workflows/*.json` | Agent orchestration, self-hosted. |

---

## How to extend this log

`engine/oss_audit.py` collects read-only GitHub metadata (stars, licence,
last push) for candidate repositories and refuses to clone, install or execute
anything. Run it before adding a row here, and record the verdict with a
reason — including the rejections. The rejections are the more useful half of
this document: they stop the same dead end being explored twice.
