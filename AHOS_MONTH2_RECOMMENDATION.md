# AHOS Month 2 Recommendation

**Date:** 2026-08-18 · **Basis:** Month 1 gate status = PENDING (pilot accruing; see
`AHOS_MONTH1_OPERATIONAL_GATE.md`). Per directive: operational evidence takes priority over
unit-test passes — therefore this is a **conditional** plan, sequenced behind gate evidence.

## Recommendation (priority order)

| # | Item | Enter Month 2? | Rationale |
|---|---|---|---|
| 1 | **Complete the soak first** (VPS migration + 168h window + §6 deliberate events + backup drill M-GAP-010 + off-box watchdog alert M-GAP-012) | **Mandatory pre-condition** | The gate is PENDING; expanding features before operational proof repeats the Phase-XX pattern the audit flagged (claims before evidence). |
| 2 | **Provider availability work ON the VPS**: live probes of existing adapters (DexScreener/GeckoTerminal/GoPlus/RugCheck + CoinGecko/ChainExplorer from Phase 7) | **Yes — first Month-2 workstream** | M-GAP-007: success paths unproven from sandbox; a live host closes the largest provider-reliability unknown. Cheap, high-evidence. |
| 3 | **CoinMarketCap + Launchpad adapters** | Yes (second workstream) | M-GAP-011; CMC free tier needs a key → follow the DEXTools inert-until-configured pattern (never blocked, never fabricated). |
| 4 | **Multi-chain E2E beyond solana** (ethereum, bsc, base, arbitrum, polygon, avalanche) | Yes, gated on #2 | Chain maps exist (Phase 7); need live collection coverage reports per chain. |
| 5 | Telegram operationalization | **No — keep Month 4** | Blocked on user token rotation (M-GAP-009); pulling it earlier adds risk without evidence value. |
| 6 | Local AI lane / research intelligence / additional agent capabilities | **No** | Roadmap v3 places these Months 3–5; no operational evidence yet justifies re-sequencing. |
| 7 | Postgres migration | **No — Month 6** | SQLite is intact and honest; migration is deployment hardening, correctly last. |
| 8 | Production deployment hardening | Month 6 (final) | Sequence preserved from Roadmap v3. |

## Trigger Rule

Month-2 feature work (#3, #4) starts only when the pilot-to-VPS soak has produced ≥ 48h of
clean snapshots AND no new Severity-1/2 gap is open. If the gate ultimately classifies FAIL,
Month 2 becomes a remediation month instead — feature expansion is cancelled, not deferred.

## Scheduler framework question — closed with evidence

Directive constraint #11 (no new scheduler framework unless evidence proves necessity):
28 failure-matrix scenarios + pilot hours show the in-house scheduler correctly refusing
overlaps, recovering leases, measuring drift, and failing closed. **No evidence supports
adding Temporal/Celery/APScheduler/Redis.** Question stays closed unless a soak incident
contradicts the acceptance criteria.
