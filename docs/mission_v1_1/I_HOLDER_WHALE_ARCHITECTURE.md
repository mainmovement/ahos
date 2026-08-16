# I. HOLDER / WHALE INTELLIGENCE ARCHITECTURE — Wave-6 (Part V) — 2026-08-11
# Marks per component below. Feasibility is probe-driven: nothing claimed that free RPCs can't serve.

## 1. Feasibility ground truth (probes)
| Capability | RPC method | Free-public feasibility | State |
|---|---|---|---|
| Top token accounts (SOL) | getTokenLargestAccounts | **NO — probe 2026-08-11: mainnet-beta 429 ×3, onfinality 429, publicnode 403+timeout, api.mainnet.solana.com 429, helius-public-key 401 (5/5 rejections). Shared free RPCs throttle/forbid this method.** | **BLOCKED-at-source (evidence-backed)**; adapter+schema shipped; features emit only from real rows |
| Top-account balances change | repeats of above | blocked with it | same |
| Total holder count | getProgramAccounts (token accounts) | NO on public RPCs (disabled/prohibitive) | MISSING → UNKNOWN, documented |
| Deployer funding path | getSignaturesForAddress + getTransaction | YES-ish but slow/partial (rate-budgeted; getSlot/getBlock OK on public RPC = LIVE VERIFIED wave-5) | PARTIAL design (Phase-3) |
| Wallet age (first activity) | idem | partial | PARTIAL |
| EVM holders | Transfer-log scanning w/ block budget | feasible in principle on publicnode (blockNumber OK) | DESIGNED (Phase-3) |
| Smart-money labels | cross-token outcome-joined wallet P&L | needs ≥ weeks of E-01 outcomes | ARCHITECTURE only (§4) |
| Possibly-viable alternative | Helius/QuickNode free-tier API keys | signup required; IR signup risk | UNKNOWN — user-dependent |

**Standing correction:** an earlier draft of this doc claimed getTokenLargestAccounts was LIVE VERIFIED.
The 2026-08-11 probe battery refuted it (Part XXIV: failure preserved, not hidden).

## 2. Data model (additive v1.3)
holder_snapshot(token_id, ts, source, top_accounts_json, top10_share, top20_share, raw_ref)
wallet_observation(address, chain, first_seen_ts, last_seen_ts, evidence_json)   — accumulated across tokens
(Concentration computed at ingest; row payloads archived; NULL discipline unchanged.)

## 3. Collector (Phase-3 path; SOL first — LIVE-probed)
discovery/holders.py: for top-liquidity OBSERVING SOL tokens (budget: ≤30/day, rpm-respecting):
getTokenLargestAccounts → snapshot row. Features (fs_v0.2, E-doc): top_holder_concentration,
top20_net_flow_1h (signed delta vs prior snapshot ≥1h old), whale_exit_event (top-acct balance −50%+,
observation-derived, not "label").

## 4. Smart-money = evidence-based (Part V law)
WalletReputation is DERIVED, never manual:
reputation(address) := f( realized outcomes of EARLY entries across E-01-tracked tokens, batch-sealed )
- An address joins the reputation pool only after ≥3 entry-observations with RESOLVED outcomes.
- One profitable trade ⇒ NOT smart money (explicit test in fixtures).
- Sybil/clustering heuristics (common funding source, same-block entries) = v2 architecture; heuristic
  flags only, confidence LOW until validated.

## 5. Adversarial notes (Council 14)
Top-N snapshots are manipulable (dust-splitting). Concentration features carry reliability=MED, plus a
planned bundling-suspicion feature later. Snapshot cadence ≤ token budget; RPC cost ceiling $0.
